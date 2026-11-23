#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Vaibhav Agarwal

# Author: Vaibhav — sole author; Vaibhav holds final authority over this project.
# License: GNU General Public License v3.0 only (GPL-3.0-only). No MIT permitted.
# Role: RENDERING ONLY. All Monte Carlo maths/statistics were computed in pure
# C++ with AVX2 (mmf_stress.cpp). This script only rasterizes PNG charts from
# the C++ CSV outputs and assembles the PDF. No numerics are recomputed here
# beyond direct plotting of C++-produced values.
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "out"
FIG = os.path.join(OUT, "figs")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"figure.dpi": 150, "font.size": 9, "axes.grid": True,
                     "grid.alpha": 0.3})

s = pd.read_csv(os.path.join(OUT, "scenario_summary.csv"))
h = pd.read_csv(os.path.join(OUT, "histograms.csv"))
nav = pd.read_csv("data/tata-money-market-direct-growth/nav_daily.csv",
                  usecols=["Date", "NAV_Rs"], parse_dates=["Date"])

# 1. NAV history (log) -------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 3.4))
ax.semilogy(nav["Date"], nav["NAV_Rs"], lw=1.0)
ax.set_title("Tata Money Market Direct-Growth — Daily NAV 2013-01-01 → 2026-09-25 (3,876 obs)")
ax.set_xlabel("Date"); ax.set_ylabel("NAV Rs (log scale)")
fig.tight_layout(); fig.savefig(f"{FIG}/01_nav_history.png"); plt.close(fig)

# 2. Rate-shock sensitivity (red=0, four spread lines) ------------------------
fig, ax = plt.subplots(figsize=(7.5, 3.8))
base = s[s.red_frac == 0].sort_values(["spread_bp", "rate_bp"])
for sp, g in base.groupby("spread_bp"):
    g = g.sort_values("rate_bp")
    ax.plot(g.rate_bp, g.mean_ret_5d * 1e4, marker="o", ms=3,
            label=f"spread +{int(sp)}bp")
ax.set_title("Mean 5-day shadow return vs parallel rate shock (redemption = 0%)")
ax.set_xlabel("Rate shock (bp)"); ax.set_ylabel("Mean 5d return (bp)")
ax.legend(fontsize=8); fig.tight_layout()
fig.savefig(f"{FIG}/02_rate_shock.png"); plt.close(fig)

# 3. Spread-shock grouped bars (red=0) ----------------------------------------
piv = base.pivot(index="rate_bp", columns="spread_bp", values="mean_ret_5d") * 1e4
fig, ax = plt.subplots(figsize=(7.5, 3.8))
x = np.arange(len(piv.index)); w = 0.18
for i, col in enumerate(piv.columns):
    ax.bar(x + (i - 1.5) * w, piv[col].values, width=w, label=f"+{int(col)}bp spr")
ax.set_xticks(x, [f"{int(v)}" for v in piv.index])
ax.set_title("Credit-spread widening: mean 5d return (bp) by rate shock, red=0%")
ax.set_xlabel("Rate shock (bp)"); ax.set_ylabel("bp"); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(f"{FIG}/03_spread.png"); plt.close(fig)

# 4. Redemption cost waterfall (rate +200bp slice) ----------------------------
fig, ax = plt.subplots(figsize=(7.5, 3.8))
sl = s[(s.rate_bp == 200)].sort_values(["spread_bp", "red_frac"])
for sp, g in sl.groupby("spread_bp"):
    g = g.sort_values("red_frac")
    ax.plot(g.red_frac * 100, g.mean_ret_5d * 1e4, marker="s", ms=4,
            label=f"spr +{int(sp)}bp")
ax.set_title("Mass-redemption cost at +200bp rates: mean 5d return vs outflow")
ax.set_xlabel("Redemption (% NAV)"); ax.set_ylabel("Mean 5d return (bp)")
ax.legend(fontsize=8); fig.tight_layout()
fig.savefig(f"{FIG}/04_redemption.png"); plt.close(fig)

# 5. Shadow-NAV histograms, 4 regimes -----------------------------------------
scen_pick = {
    "Baseline (r0/s0/red0)": 0,
    "+200bp, no redemption": int(s[(s.rate_bp == 200) & (s.spread_bp == 0) & (s.red_frac == 0)].iloc[0].scen),
    "25% run, no market shock": int(s[(s.rate_bp == 0) & (s.spread_bp == 0) & (s.red_frac == 0.25)].iloc[0].scen),
    "Max combined (+500/+300/25%)": int(s.scen.max()),
}
fig, axes = plt.subplots(2, 2, figsize=(8, 5), sharex=True, sharey=False)
for ax, (title, sc) in zip(axes.ravel(), scen_pick.items()):
    g = h[h.scen == sc].sort_values("bin_lo_ret")
    mid = (g.bin_lo_ret + g.bin_hi_ret) / 2 * 1e4
    ax.bar(mid, g["count"], width=(mid.iloc[1] - mid.iloc[0]) * 0.95)
    ax.axvline(1.0 - 0.9995, color="r", ls="--", lw=1)
    ax.set_title(f"{title}  [n=25M]")
    ax.set_xlabel("5d return (bp)"); ax.set_ylabel("paths")
fig.suptitle("Shadow-NAV return distributions (25M paths each, C++ AVX2)")
fig.tight_layout(); fig.savefig(f"{FIG}/05_histograms.png"); plt.close(fig)

# 6. Breach-probability heatmap P(NAV<0.9995), red=10% -------------------------
sub = s[s.red_frac == 0.10].pivot(index="spread_bp", columns="rate_bp",
                                  values="p_lt_9995")
fig, ax = plt.subplots(figsize=(6.5, 3.8))
im = ax.imshow(sub.values, origin="lower", aspect="auto", vmin=0, vmax=1)
ax.set_xticks(range(len(sub.columns)), [f"{int(c)}" for c in sub.columns])
ax.set_yticks(range(len(sub.index)), [f"{int(i)}" for i in sub.index])
ax.set_xlabel("Rate shock (bp)"); ax.set_ylabel("Spread shock (bp)")
ax.set_title("P(shadow NAV < 0.9995) — 10% redemption, 25M paths/cell")
for i in range(sub.shape[0]):
    for j in range(sub.shape[1]):
        ax.text(j, i, f"{sub.values[i, j]:.2f}", ha="center", va="center",
                fontsize=7, color="white" if sub.values[i, j] > 0.5 else "black")
fig.colorbar(im, ax=ax, label="probability")
fig.tight_layout(); fig.savefig(f"{FIG}/06_breach_heatmap.png"); plt.close(fig)

# 7. Liquidity funnel DLA/WLA vs redemption -----------------------------------
liq = s[(s.rate_bp == 0) & (s.spread_bp == 0)].sort_values("red_frac")
fig, ax = plt.subplots(figsize=(7.5, 3.8))
x = liq.red_frac * 100
ax.plot(x, liq.dla_post_pct, marker="o", label="DLA post (waterfall)")
ax.plot(x, liq.wla_post_pct, marker="o", label="WLA post (waterfall)")
ax.axhline(25, color="r", ls="--", lw=1, label="2a-7 DLA floor 25%")
ax.axhline(50, color="darkred", ls="--", lw=1, label="2a-7 WLA floor 50%")
ax.set_title("Daily / Weekly liquid assets after redemption (waterfall liquidation)")
ax.set_xlabel("Redemption (% NAV)"); ax.set_ylabel("% of remaining NAV")
ax.legend(fontsize=8); fig.tight_layout()
fig.savefig(f"{FIG}/07_liquidity.png"); plt.close(fig)

# 8. WAM/WAL vs redemption -----------------------------------------------------
fig, ax = plt.subplots(figsize=(7.5, 3.8))
ax.plot(x, liq.wam_post_d, marker="o", label="WAM post")
ax.plot(x, liq.wal_post_d, marker="s", label="WAL post")
ax.axhline(60, color="r", ls="--", lw=1, label="2a-7 WAM cap 60d")
ax.axhline(120, color="darkred", ls="--", lw=1, label="2a-7 WAL cap 120d")
ax.set_title("WAM / WAL after waterfall redemptions (baseline 110.4d)")
ax.set_xlabel("Redemption (% NAV)"); ax.set_ylabel("days")
ax.legend(fontsize=8); fig.tight_layout()
fig.savefig(f"{FIG}/08_wam_wal.png"); plt.close(fig)

print("FIGURES_OK", sorted(os.listdir(FIG)))
