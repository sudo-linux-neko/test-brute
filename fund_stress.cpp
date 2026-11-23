// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Vaibhav Agarwal

/*
 * Fund Stress-Test Engine (generic) — pure C++ with AVX2, OpenMP
 * Covers all 15 Tata Direct-Growth funds: debt multi-factor mode
 * (rate/spread/redemption, Rule 2a-7 + ESMA lens) and equity GBM mode
 * (market-shock x vol-regime x horizon, DFAST-style severely adverse).
 *
 * Author: Vaibhav — sole author; Vaibhav holds final authority over this project.
 * License: GNU General Public License v3.0 only (GPL-3.0-only). Never MIT.
 *
 * Hyper-optimized for: i5-1335U (AVX2+FMA, 12T), 7.6 GiB RAM.
 * Flags: -O3 -march=native -mtune=native -mavx2 -mfma -funroll-loops
 *        -flto -fopenmp -DNDEBUG -ffast-math -fno-math-errno
 * Usage:
 *   fund_stress debt   <nav.csv> <outdir> <paths> <threads> <ytm> <modDur> <sprDur> <beta>
 *   fund_stress equity <nav.csv> <outdir> <paths> <threads> <beta>
 */
#include <immintrin.h>
#include <omp.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

struct Rng {
  uint64_t s;
  explicit Rng(uint64_t seed) : s(seed ? seed : 0x9E3779B97F4A7C15ULL) {}
  inline uint64_t next(void) {
    s ^= s >> 12; s ^= s << 25; s ^= s >> 27;
    return s * 2685821657736338717ULL;
  }
  inline double uniform(void) {
    return (double)(next() >> 11) * (1.0 / 9007199254740992.0);
  }
};

static bool read_nav(const char *path, std::vector<double> &nav,
                     std::vector<std::string> &dates) {
  std::ifstream f(path);
  if (!f) return false;
  std::string line;
  std::getline(f, line);
  while (std::getline(f, line)) {
    if (line.size() < 8) continue;
    size_t c = line.find(',');
    if (c == std::string::npos) continue;
    size_t c2 = line.find(',', c + 1);
    std::string ds = line.substr(0, c);
    std::string ns = (c2 == std::string::npos) ? line.substr(c + 1)
                                               : line.substr(c + 1, c2 - c - 1);
    char *e = nullptr;
    double v = std::strtod(ns.c_str(), &e);
    if (e != ns.c_str() && v > 0) { nav.push_back(v); dates.push_back(ds); }
  }
  return nav.size() > 100;
}

// ---------------- DEBT MODE ----------------
struct DScen { int rate_bp, spr_bp; double red; double twist_bp; char name[64]; };
struct alignas(64) DAcc {
  double mean = 0, m2 = 0, mn = 1e9, mx = -1e9;
  uint64_t n = 0, b9995 = 0, b9990 = 0, b9975 = 0, b9950 = 0, fee = 0;
  uint64_t hist[120] = {0};
};
static constexpr double DH_LO = -0.06, DH_HI = 0.02;
static constexpr int DH_N = 120, DBLOCK = 4096;

static int run_debt(const char *navPath, const char *outDir, int64_t totalPaths,
                    int nthreads, double ytm, double modDur, double sprDur,
                    double H_LO = -0.06, double H_HI = 0.02) {
  char mk[512]; snprintf(mk, sizeof mk, "mkdir -p %s", outDir); (void)system(mk);
  std::vector<double> nav; std::vector<std::string> dates;
  if (!read_nav(navPath, nav, dates)) { std::fprintf(stderr, "FATAL nav\n"); return 2; }
  double s1 = 0, s2 = 0; int nr = 0;
  for (size_t i = 1; i < nav.size(); ++i) {
    double r = log(nav[i] / nav[i - 1]);
    if (!std::isfinite(r) || fabs(r) > 0.05) continue;
    s1 += r; s2 += r * r; ++nr;
  }
  double mu = s1 / nr, var = std::max(1e-18, s2 / nr - mu * mu);
  double sig_d = sqrt(var);
  const int rates[5] = {0, 100, 200, 300, 500};
  const int sprs[4] = {0, 50, 150, 300};
  const double reds[4] = {0, 0.05, 0.10, 0.25};
  std::vector<DScen> sc; sc.reserve(80);
  for (int r : rates) for (int s : sprs) for (double d : reds) {
    DScen x; x.rate_bp = r; x.spr_bp = s; x.red = d;
    x.twist_bp = (r == 300) ? 40 : (r == 500 ? -80 : 0);
    snprintf(x.name, sizeof x.name, "r%+dbp_s%+dbp_tw%+d_red%02d", r, s,
             (int)x.twist_bp, (int)(d * 100));
    sc.push_back(x);
  }
  int64_t perScen = totalPaths / (int64_t)sc.size();
  const double T = 5.0, sigR = 0.0005, sigS = 0.0004;
  const double c12 = 0.45, c13 = 0.25, c23 = 0.35;
  const double L21 = c12, L22 = sqrt(1 - c12 * c12), L31 = c13;
  const double L32 = (c23 - c13 * c12) / L22;
  const double L33 = sqrt(std::max(1e-9, 1 - L31 * L31 - L32 * L32));
  const double accrual = ytm * (T / 365.0), conv = modDur * modDur;
  const double baseBA = 0.0011, pImp = 0.0008;
  std::vector<DAcc> gacc(sc.size());
  double t0 = omp_get_wtime(); int64_t grand = 0;
#pragma omp parallel shared(sc, gacc) reduction(+ : grand)
  {
    int tid = omp_get_thread_num();
    Rng rng(0xDEB7ULL + (uint64_t)tid * 0x9E3779B1ULL);
    std::vector<double> b0(DBLOCK), b1(DBLOCK), b2(DBLOCK);
    for (size_t si = 0; si < sc.size(); ++si) {
      const DScen &c = sc[si];
      double drP = c.rate_bp * 1e-4, dsS = c.spr_bp * 1e-4;
      DAcc t; t.mn = 1e9; t.mx = -1e9;
      const __m256d vSigR = _mm256_set1_pd(sigR * sqrt(T));
      const __m256d vSigS = _mm256_set1_pd(sigS * sqrt(T));
      const __m256d vDrP = _mm256_set1_pd(drP), vDsS = _mm256_set1_pd(dsS);
      const __m256d vMod = _mm256_set1_pd(modDur), vSpr = _mm256_set1_pd(sprDur);
      const __m256d vCvx = _mm256_set1_pd(0.5 * conv);
      const __m256d vAcc = _mm256_set1_pd(accrual);
      const __m256d vL21 = _mm256_set1_pd(L21), vL22 = _mm256_set1_pd(L22);
      const __m256d vL31 = _mm256_set1_pd(L31), vL32 = _mm256_set1_pd(L32),
                    vL33 = _mm256_set1_pd(L33);
      const __m256d vBa = _mm256_set1_pd(baseBA);
      const __m256d vPI = _mm256_set1_pd(pImp * (c.red / 0.10));
      const __m256d vRed = _mm256_set1_pd(c.red * 1.20);
      const __m256d vZero = _mm256_setzero_pd(), vOne = _mm256_set1_pd(1.0);
      const __m256d v9995 = _mm256_set1_pd(0.9995), v9990 = _mm256_set1_pd(0.9990),
                    v9975 = _mm256_set1_pd(0.9975), v9950 = _mm256_set1_pd(0.9950);
      int64_t share = (perScen + omp_get_num_threads() - 1) / omp_get_num_threads();
      int64_t a = (int64_t)tid * share, b = std::min<int64_t>(perScen, a + share);
      int64_t myN = (b > a) ? (b - a) : 0, done = 0;
      grand += myN;
      double mean = 0, m2 = 0, mn = 1e9, mx = -1e9; uint64_t n = 0;
      uint64_t l1 = 0, l2 = 0, l3 = 0, l4 = 0, lf = 0;
      while (done < myN) {
        int cur = (int)std::min<int64_t>(DBLOCK, myN - done);
        for (int i = 0; i < cur; i += 2) {
          double u1 = rng.uniform(), u2 = rng.uniform(), u3 = rng.uniform(),
                 u4 = rng.uniform();
          if (u1 < 1e-12) u1 = 1e-12; if (u3 < 1e-12) u3 = 1e-12;
          double r1 = sqrt(-2.0 * log(u1)), r2 = sqrt(-2.0 * log(u3));
          b0[i] = r1 * cos(6.283185307179586 * u2); b1[i] = r1 * sin(6.283185307179586 * u2);
          if (i + 1 < cur) { b0[i+1] = r2 * cos(6.283185307179586 * u4); b1[i+1] = r2 * sin(6.283185307179586 * u4); }
          double u5 = rng.uniform(), u6 = rng.uniform(), u7 = rng.uniform(), u8 = rng.uniform();
          if (u5 < 1e-12) u5 = 1e-12; if (u7 < 1e-12) u7 = 1e-12;
          b2[i] = sqrt(-2.0 * log(u5)) * cos(6.283185307179586 * u6);
          if (i + 1 < cur) b2[i+1] = sqrt(-2.0 * log(u7)) * cos(6.283185307179586 * u8);
        }
        int i = 0;
        for (; i + 4 <= cur; i += 4) {
          __m256d e0 = _mm256_loadu_pd(&b0[i]), e1 = _mm256_loadu_pd(&b1[i]),
                   e2 = _mm256_loadu_pd(&b2[i]);
          __m256d zr = e0;
          __m256d zc = _mm256_fmadd_pd(vL22, e1, _mm256_mul_pd(vL21, e0));
          __m256d zl = _mm256_fmadd_pd(vL33, e2, _mm256_fmadd_pd(vL32, e1, _mm256_mul_pd(vL31, e0)));
          __m256d dr = _mm256_fmadd_pd(vSigR, zr, vDrP);
          __m256d ds = _mm256_fmadd_pd(vSigS, zc, vDsS);
          __m256d ab; { __m256d nz = _mm256_sub_pd(vZero, zl);
            ab = _mm256_blendv_pd(zl, nz, _mm256_cmp_pd(zl, vZero, _CMP_LT_OQ)); }
          __m256d liq = _mm256_mul_pd(vRed, _mm256_add_pd(
              _mm256_mul_pd(vBa, _mm256_fmadd_pd(_mm256_set1_pd(3.0), ab, vOne)), vPI));
          __m256d loss = _mm256_fmadd_pd(vMod, dr, _mm256_fmadd_pd(vSpr, ds, liq));
          loss = _mm256_fnmadd_pd(vCvx, _mm256_mul_pd(dr, dr), loss);
          __m256d ret = _mm256_sub_pd(vAcc, loss);
          __m256d nv = _mm256_add_pd(vOne, ret);
          l1 += __builtin_popcount(_mm256_movemask_pd(_mm256_cmp_pd(nv, v9995, _CMP_LT_OQ)));
          l2 += __builtin_popcount(_mm256_movemask_pd(_mm256_cmp_pd(nv, v9990, _CMP_LT_OQ)));
          l3 += __builtin_popcount(_mm256_movemask_pd(_mm256_cmp_pd(nv, v9975, _CMP_LT_OQ)));
          l4 += __builtin_popcount(_mm256_movemask_pd(_mm256_cmp_pd(nv, v9950, _CMP_LT_OQ)));
          alignas(32) double ln[4], rn[4], lq[4];
          _mm256_store_pd(ln, nv); _mm256_store_pd(rn, ret); _mm256_store_pd(lq, liq);
          if (c.red >= 0.05) for (int k = 0; k < 4; ++k) if (lq[k] > 0.0001) ++lf;
          for (int k = 0; k < 4; ++k) {
            double x = rn[k]; ++n;
            double d = x - mean; mean += d / (double)n; m2 += d * (x - mean);
            if (ln[k] < mn) mn = ln[k]; if (ln[k] > mx) mx = ln[k];
            int bb = (int)((x - H_LO) * ((double)DH_N / (H_HI - H_LO)));
            if ((unsigned)bb < (unsigned)DH_N) t.hist[bb]++;
          }
        }
        for (; i < cur; ++i) {
          double zr = b0[i], zc = L21 * b0[i] + L22 * b1[i];
          double zl = L31 * b0[i] + L32 * b1[i] + L33 * b2[i];
          double dr = drP + sigR * sqrt(T) * zr, ds = dsS + sigS * sqrt(T) * zc;
          double liq = c.red * 1.20 * (baseBA * (1 + 3 * fabs(zl)) + pImp * (c.red / 0.10));
          double ret = accrual - (modDur * dr + sprDur * ds + liq - 0.5 * conv * dr * dr);
          double nv = 1.0 + ret; ++n;
          double d = ret - mean; mean += d / (double)n; m2 += d * (ret - mean);
          if (nv < mn) mn = nv; if (nv > mx) mx = nv;
          if (nv < 0.9995) ++l1; if (nv < 0.9990) ++l2;
          if (nv < 0.9975) ++l3; if (nv < 0.9950) ++l4;
          if (c.red >= 0.05 && liq > 0.0001) ++lf;
          int bb = (int)((ret - H_LO) * ((double)DH_N / (H_HI - H_LO)));
          if ((unsigned)bb < (unsigned)DH_N) t.hist[bb]++;
        }
        done += cur;
      }
      t.mean = mean; t.m2 = m2; t.mn = mn; t.mx = mx; t.n = n;
      t.b9995 = l1; t.b9990 = l2; t.b9975 = l3; t.b9950 = l4; t.fee = lf;
#pragma omp critical
      { DAcc &g = gacc[si];
        if (g.n == 0) { g.mn = t.mn; g.mx = t.mx; }
        else { if (t.mn < g.mn) g.mn = t.mn; if (t.mx > g.mx) g.mx = t.mx; }
        if (t.n) { if (g.n == 0) { g.mean = t.mean; g.m2 = t.m2; }
          else { double d = t.mean - g.mean; uint64_t s = g.n + t.n;
            g.m2 += t.m2 + d * d * (double)g.n * (double)t.n / (double)s;
            g.mean += d * (double)t.n / (double)s; }
          g.n += t.n; }
        g.b9995 += t.b9995; g.b9990 += t.b9990; g.b9975 += t.b9975;
        g.b9950 += t.b9950; g.fee += t.fee;
        for (int q = 0; q < DH_N; ++q) g.hist[q] += t.hist[q]; } }
  }
  double t1 = omp_get_wtime();
  { std::string p = std::string(outDir) + "/scenario_summary.csv";
    std::FILE *f = std::fopen(p.c_str(), "w");
    std::fprintf(f, "scen,name,rate_bp,spread_bp,twist_bp,red_frac,paths,mean_ret_5d,sd_ret_5d,min_nav,max_nav,p_lt_9995,p_lt_9990,p_lt_9975,p_lt_9950,p_fee_trigger\n");
    for (size_t i = 0; i < sc.size(); ++i) { DAcc &g = gacc[i];
      double sd = (g.n > 1) ? sqrt(g.m2 / (double)(g.n - 1)) : 0;
      double dn = (double)std::max<uint64_t>(1, g.n);
      std::fprintf(f, "%zu,%s,%d,%d,%d,%.2f,%llu,%.8f,%.8f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f\n",
        i, sc[i].name, sc[i].rate_bp, sc[i].spr_bp, (int)sc[i].twist_bp, sc[i].red,
        (unsigned long long)g.n, g.mean, sd, g.mn, g.mx,
        g.b9995 / dn, g.b9990 / dn, g.b9975 / dn, g.b9950 / dn, g.fee / dn); }
    std::fclose(f); }
  { std::string p = std::string(outDir) + "/histograms.csv";
    std::FILE *f = std::fopen(p.c_str(), "w");
    std::fprintf(f, "scen,bin_lo_ret,bin_hi_ret,count\n");
    double w = (H_HI - H_LO) / DH_N;
    for (size_t i = 0; i < sc.size(); ++i) for (int b = 0; b < DH_N; ++b)
      std::fprintf(f, "%zu,%.8f,%.8f,%llu\n", i, H_LO + b * w, H_LO + (b + 1) * w,
                   (unsigned long long)gacc[i].hist[b]);
    std::fclose(f); }
  { std::string p = std::string(outDir) + "/calibration.json";
    std::FILE *f = std::fopen(p.c_str(), "w");
    std::fprintf(f, "{\"mode\":\"debt\",\"nav_obs\":%zu,\"mu_daily\":%.10f,"
      "\"sigma_daily\":%.10f,\"sigma_ann_pct\":%.4f,\"ytm\":%.4f,"
      "\"mod_dur\":%.4f,\"spr_dur\":%.4f,\"first_nav\":%.4f,\"last_nav\":%.4f}\n",
      nav.size(), mu, sig_d, sig_d * sqrt(252.0) * 100.0, ytm, modDur, sprDur,
      nav.front(), nav.back());
    std::fclose(f); }
  { std::string p = std::string(outDir) + "/run_meta.txt";
    std::FILE *f = std::fopen(p.c_str(), "w");
    std::fprintf(f, "author: Vaibhav (final authority)\nlicense: GPL-3.0-only\n"
      "mode: debt\ntotal_paths_simulated: %lld\nscenarios: %zu\nthreads: %d\n"
      "seconds: %.2f\nmpaths_per_sec: %.2f\navx2: yes\n", (long long)grand,
      sc.size(), nthreads, t1 - t0, (double)grand / 1e6 / std::max(1e-9, t1 - t0));
    std::fclose(f); }
  std::printf("DEBT PATHS=%lld SCEN=%zu SEC=%.2f MP/S=%.2f\n", (long long)grand,
    sc.size(), t1 - t0, (double)grand / 1e6 / std::max(1e-9, t1 - t0));
  return 0;
}

// ---------------- EQUITY MODE ----------------
struct EScen { double shock; double volm; int hor; char name[48]; };
struct alignas(64) EAcc {
  double mean = 0, m2 = 0, mn = 1e9, mx = -1e9;
  uint64_t n = 0;
  uint64_t hist[400] = {0};
};
static constexpr double EH_LO = -1.0, EH_HI = 1.5;
static constexpr int EH_N = 400, EBLOCK = 4096;

static int run_equity(const char *navPath, const char *outDir, int64_t totalPaths,
                      int nthreads, double beta) {
  char mk[512]; snprintf(mk, sizeof mk, "mkdir -p %s", outDir); (void)system(mk);
  std::vector<double> nav; std::vector<std::string> dates;
  if (!read_nav(navPath, nav, dates)) { std::fprintf(stderr, "FATAL nav\n"); return 2; }
  double s1 = 0, s2 = 0; int nr = 0;
  double mdd = 0, peak = nav[0];
  for (size_t i = 1; i < nav.size(); ++i) {
    double r = log(nav[i] / nav[i - 1]);
    if (std::isfinite(r) && fabs(r) < 0.35) { s1 += r; s2 += r * r; ++nr; }
    if (nav[i] > peak) peak = nav[i];
    mdd = std::min(mdd, nav[i] / peak - 1.0);
  }
  double mu = s1 / nr, sig = sqrt(std::max(1e-18, s2 / nr - mu * mu));
  const double shocks[5] = {0, -0.05, -0.10, -0.20, -0.30};
  const double vols[3] = {1.0, 1.5, 2.0};
  const int hors[3] = {21, 63, 252};
  std::vector<EScen> sc; sc.reserve(45);
  for (double sh : shocks) for (double v : vols) for (int h : hors) {
    EScen x; x.shock = sh; x.volm = v; x.hor = h;
    snprintf(x.name, sizeof x.name, "m%+d_vol%.1f_h%d", (int)(sh * 100), v, h);
    sc.push_back(x);
  }
  int64_t perScen = totalPaths / (int64_t)sc.size();
  std::vector<EAcc> gacc(sc.size());
  double t0 = omp_get_wtime(); int64_t grand = 0;
#pragma omp parallel shared(sc, gacc) reduction(+ : grand)
  {
    int tid = omp_get_thread_num();
    Rng rng(0xE9177ULL + (uint64_t)tid * 0x9E3779B1ULL);
    std::vector<double> zb(EBLOCK);
    for (size_t si = 0; si < sc.size(); ++si) {
      const EScen &c = sc[si];
      double T = (double)c.hor;
      double jump = beta * log1p(c.shock); // beta-scaled systematic shock
      double drift = (mu - 0.5 * sig * sig) * T + jump;
      double diff = sig * sqrt(T) * c.volm;
      EAcc t; t.mn = 1e9; t.mx = -1e9;
      const __m256d vDr = _mm256_set1_pd(drift), vDf = _mm256_set1_pd(diff);
      const __m256d vOne = _mm256_set1_pd(1.0);
      int64_t share = (perScen + omp_get_num_threads() - 1) / omp_get_num_threads();
      int64_t a = (int64_t)tid * share, b = std::min<int64_t>(perScen, a + share);
      int64_t myN = (b > a) ? (b - a) : 0, done = 0;
      grand += myN;
      double mean = 0, m2 = 0, mn = 1e9, mx = -1e9; uint64_t n = 0;
      while (done < myN) {
        int cur = (int)std::min<int64_t>(EBLOCK, myN - done);
        // Box-Muller fill (scalar; AVX hot loop follows)
        for (int i = 0; i < cur; i += 2) {
          double u1 = rng.uniform(), u2 = rng.uniform();
          if (u1 < 1e-12) u1 = 1e-12;
          double rr = sqrt(-2.0 * log(u1)), tt = 6.283185307179586 * u2;
          zb[i] = rr * cos(tt);
          if (i + 1 < cur) zb[i + 1] = rr * sin(tt);
        }
        int i = 0;
        for (; i + 4 <= cur; i += 4) {
          __m256d z = _mm256_loadu_pd(&zb[i]);
          __m256d lr = _mm256_fmadd_pd(vDf, z, vDr); // log-return
          // simple ret = exp(lr)-1 via scalarized exp (4 exps; memory-bound loop)
          alignas(32) double lra[4]; _mm256_store_pd(lra, lr);
          alignas(32) double rta[4];
          rta[0] = exp(lra[0]) - 1.0; rta[1] = exp(lra[1]) - 1.0;
          rta[2] = exp(lra[2]) - 1.0; rta[3] = exp(lra[3]) - 1.0;
          __m256d rt = _mm256_load_pd(rta);
          (void)rt; (void)vOne;
          for (int k = 0; k < 4; ++k) {
            double x = rta[k]; ++n;
            double d = x - mean; mean += d / (double)n; m2 += d * (x - mean);
            if (x < mn) mn = x; if (x > mx) mx = x;
            int bb = (int)((x - EH_LO) * ((double)EH_N / (EH_HI - EH_LO)));
            if ((unsigned)bb < (unsigned)EH_N) t.hist[bb]++;
          }
        }
        for (; i < cur; ++i) {
          double x = exp(drift + diff * zb[i]) - 1.0; ++n;
          double d = x - mean; mean += d / (double)n; m2 += d * (x - mean);
          if (x < mn) mn = x; if (x > mx) mx = x;
          int bb = (int)((x - EH_LO) * ((double)EH_N / (EH_HI - EH_LO)));
          if ((unsigned)bb < (unsigned)EH_N) t.hist[bb]++;
        }
        done += cur;
      }
      t.mean = mean; t.m2 = m2; t.mn = mn; t.mx = mx; t.n = n;
#pragma omp critical
      { EAcc &g = gacc[si];
        if (g.n == 0) { g.mn = t.mn; g.mx = t.mx; }
        else { if (t.mn < g.mn) g.mn = t.mn; if (t.mx > g.mx) g.mx = t.mx; }
        if (t.n) { if (g.n == 0) { g.mean = t.mean; g.m2 = t.m2; }
          else { double d = t.mean - g.mean; uint64_t s = g.n + t.n;
            g.m2 += t.m2 + d * d * (double)g.n * (double)t.n / (double)s;
            g.mean += d * (double)t.n / (double)s; }
          g.n += t.n; }
        for (int q = 0; q < EH_N; ++q) g.hist[q] += t.hist[q]; } }
  }
  double t1 = omp_get_wtime();
  { std::string p = std::string(outDir) + "/scenario_summary.csv";
    std::FILE *f = std::fopen(p.c_str(), "w");
    std::fprintf(f, "scen,name,shock_pct,vol_mult,horizon_d,paths,mean_ret,sd_ret,min_ret,max_ret,var95,var99,var999,cvar99,p_loss,p_dd20\n");
    double bw = (EH_HI - EH_LO) / EH_N;
    for (size_t i = 0; i < sc.size(); ++i) { EAcc &g = gacc[i];
      double sd = (g.n > 1) ? sqrt(g.m2 / (double)(g.n - 1)) : 0;
      // quantiles from histogram (losses positive convention for VaR)
      auto q = [&](double tail) { uint64_t tgt = (uint64_t)(tail * (double)g.n);
        uint64_t c = 0; for (int b = 0; b < EH_N; ++b) { c += g.hist[b];
          if (c >= tgt) return -(EH_LO + (b + 1) * bw); } return -(EH_LO + EH_N * bw); };
      double v95 = q(0.05), v99 = q(0.01), v999 = q(0.001);
      // CVaR99: mean loss beyond VaR99
      uint64_t tgt = (uint64_t)(0.01 * (double)g.n), c = 0; double sl = 0; uint64_t nl = 0;
      for (int b = 0; b < EH_N; ++b) { uint64_t take = g.hist[b];
        if (c + take <= tgt) { sl += take * (EH_LO + (b + 0.5) * bw); nl += take; c += take; }
        else if (c < tgt) { uint64_t need = tgt - c;
          sl += need * (EH_LO + (b + 0.5) * bw); nl += need; break; } }
      double cvar = (nl ? -(sl / (double)nl) : v99);
      uint64_t nloss = 0, ndd = 0;
      for (int b = 0; b < EH_N; ++b) { double mid = EH_LO + (b + 0.5) * bw;
        if (mid < 0) nloss += g.hist[b]; if (mid < -0.20) ndd += g.hist[b]; }
      double dn = (double)std::max<uint64_t>(1, g.n);
      std::fprintf(f, "%zu,%s,%.1f,%.1f,%d,%llu,%.8f,%.8f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f\n",
        i, sc[i].name, sc[i].shock * 100, sc[i].volm, sc[i].hor,
        (unsigned long long)g.n, g.mean, sd, g.mn, g.mx, v95, v99, v999, cvar,
        nloss / dn, ndd / dn); }
    std::fclose(f); }
  { std::string p = std::string(outDir) + "/histograms.csv";
    std::FILE *f = std::fopen(p.c_str(), "w");
    std::fprintf(f, "scen,bin_lo_ret,bin_hi_ret,count\n");
    double w = (EH_HI - EH_LO) / EH_N;
    for (size_t i = 0; i < sc.size(); ++i) for (int b = 0; b < EH_N; ++b)
      std::fprintf(f, "%zu,%.8f,%.8f,%llu\n", i, EH_LO + b * w, EH_LO + (b + 1) * w,
                   (unsigned long long)gacc[i].hist[b]);
    std::fclose(f); }
  { std::string p = std::string(outDir) + "/calibration.json";
    std::FILE *f = std::fopen(p.c_str(), "w");
    std::fprintf(f, "{\"mode\":\"equity\",\"nav_obs\":%zu,\"mu_daily\":%.10f,"
      "\"sigma_daily\":%.10f,\"sigma_ann_pct\":%.4f,\"beta\":%.3f,"
      "\"hist_max_drawdown\":%.4f,\"first_nav\":%.4f,\"last_nav\":%.4f}\n",
      nav.size(), mu, sig, sig * sqrt(252.0) * 100.0, beta, mdd,
      nav.front(), nav.back());
    std::fclose(f); }
  { std::string p = std::string(outDir) + "/run_meta.txt";
    std::FILE *f = std::fopen(p.c_str(), "w");
    std::fprintf(f, "author: Vaibhav (final authority)\nlicense: GPL-3.0-only\n"
      "mode: equity\ntotal_paths_simulated: %lld\nscenarios: %zu\nthreads: %d\n"
      "seconds: %.2f\nmpaths_per_sec: %.2f\navx2: yes\n", (long long)grand,
      sc.size(), nthreads, t1 - t0, (double)grand / 1e6 / std::max(1e-9, t1 - t0));
    std::fclose(f); }
  std::printf("EQUITY PATHS=%lld SCEN=%zu SEC=%.2f MP/S=%.2f\n", (long long)grand,
    sc.size(), t1 - t0, (double)grand / 1e6 / std::max(1e-9, t1 - t0));
  return 0;
}

int main(int argc, char **argv) {
  if (argc < 6) {
    std::fprintf(stderr, "usage: fund_stress <debt|equity> nav.csv outdir paths threads [params...]\n");
    return 1;
  }
  std::string mode = argv[1];
  const char *nav = argv[2], *out = argv[3];
  int64_t paths = atoll(argv[4]);
  int nth = atoi(argv[5]);
  if (nth < 1) nth = 1; if (nth > 64) nth = 64;
  omp_set_num_threads(nth);
  if (mode == "debt") {
    if (argc < 9) { std::fprintf(stderr, "debt needs ytm modDur sprDur\n"); return 1; }
    double hlo = (argc >= 10) ? atof(argv[9]) : -0.06;
    double hhi = (argc >= 11) ? atof(argv[10]) : 0.02;
    return run_debt(nav, out, paths, nth, atof(argv[6]), atof(argv[7]), atof(argv[8]), hlo, hhi);
  } else if (mode == "equity") {
    double beta = (argc >= 7) ? atof(argv[6]) : 1.0;
    return run_equity(nav, out, paths, nth, beta);
  }
  std::fprintf(stderr, "unknown mode\n");
  return 1;
}
