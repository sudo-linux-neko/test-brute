#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Vaibhav Agarwal

# Author: Vaibhav — sole author; Vaibhav holds final authority over this project.
# License: GNU General Public License v3.0 only (GPL-3.0-only). No MIT permitted.
# Role: RENDERING ONLY. Plots C++-produced CSVs in dark mode. No statistics
# recomputed beyond direct display of C++ output values.
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.style.use("dark_background")
BG = "#0d1117"; GOLD = "#e3b341"; CY = "#56d4dd"; MG = "#ff7eb6"
GN = "#7ee787"; OR = "#ffa657"; TX = "#e6edf3"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG,
                     "savefig.facecolor": BG, "figure.dpi": 150,
                     "font.size": 9, "axes.grid": True, "grid.alpha": 0.18,
                     "text.color": TX, "axes.labelcolor": TX,
                     "xtick.color": TX, "ytick.color": TX})

DEBT = ["tata-money-market-direct-growth", "tata-gilt-direct-growth",
        "tata-short-term-direct-growth", "tata-ultra-short-term-direct-growth"]
EQ = ["tata-banking-and-financial-services-direct-growth",
      "tata-business-cycle-direct-growth", "tata-dividend-yield-direct-growth",
      "tata-flexi-cap-direct-growth", "tata-focused-direct-growth",
      "tata-housing-opportunities-direct-growth",
      "tata-india-consumer-direct-growth",
      "tata-large-and-mid-cap-direct-growth",
      "tata-resources-and-energy-direct-growth",
      "tata-retirement-savings-progressive-direct-growth",
      "tata-value-direct-growth"]

def short(slug):
    return slug.replace("tata-", "").replace("-direct-growth", "")

def debt_figs(slug):
    d = f"out/funds/{slug}"; fd = f"{d}/figs"; os.makedirs(fd, exist_ok=True)
    s = pd.read_csv(f"{d}/scenario_summary.csv")
    h = pd.read_csv(f"{d}/histograms.csv")
    nav = pd.read_csv(f"data/{slug}/nav_daily.csv", usecols=["Date", "NAV_Rs"],
                      parse_dates=["Date"])
    nm = short(slug)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.semilogy(nav["Date"], nav["NAV_Rs"], lw=1.0, color=GOLD)
    ax.set_title(f"{nm} — Daily NAV (log)", color="white")
    ax.set_xlabel("Date"); ax.set_ylabel("NAV Rs")
    fig.tight_layout(); fig.savefig(f"{fd}/d1_nav.png"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    base = s[s.red_frac == 0].sort_values(["spread_bp", "rate_bp"])
    for sp, g in base.groupby("spread_bp"):
        g = g.sort_values("rate_bp")
        ax.plot(g.rate_bp, g.mean_ret_5d * 1e4, marker="o", ms=3,
                label=f"spr +{int(sp)}bp")
    ax.set_title(f"{nm} — Mean 5d return vs rate shock (red=0%)", color="white")
    ax.set_xlabel("Rate shock (bp)"); ax.set_ylabel("Mean 5d (bp)")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(f"{fd}/d2_rate.png"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    sl = s[s.rate_bp == 200].sort_values(["spread_bp", "red_frac"])
    if sl.empty:
        sl = s[s.rate_bp == s.rate_bp.max()].sort_values(["spread_bp", "red_frac"])
    for sp, g in sl.groupby("spread_bp"):
        g = g.sort_values("red_frac")
        ax.plot(g.red_frac * 100, g.mean_ret_5d * 1e4, marker="s", ms=4,
                label=f"spr +{int(sp)}bp")
    ax.set_title(f"{nm} — Redemption cost (rate +{int(sl.rate_bp.iloc[0])}bp)",
                 color="white")
    ax.set_xlabel("Redemption (% NAV)"); ax.set_ylabel("Mean 5d (bp)")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(f"{fd}/d3_red.png"); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(8, 3.4))
    picks = [("Baseline", 0), ("Max combined", int(s.scen.max()))]
    for ax, (t, sc) in zip(axes, picks):
        g = h[h.scen == sc].sort_values("bin_lo_ret")
        mid = (g.bin_lo_ret + g.bin_hi_ret) / 2 * 1e4
        ax.bar(mid, g["count"], width=(mid.iloc[1] - mid.iloc[0]) * 0.95,
               color=CY if t == "Baseline" else MG)
        ax.set_title(t, color="white"); ax.set_xlabel("5d ret (bp)")
    fig.suptitle(f"{nm} — Shadow-return distributions", color="white")
    fig.tight_layout(); fig.savefig(f"{fd}/d4_hist.png"); plt.close(fig)
    return 4

def eq_figs(slug):
    d = f"out/funds/{slug}"; fd = f"{d}/figs"; os.makedirs(fd, exist_ok=True)
    s = pd.read_csv(f"{d}/scenario_summary.csv")
    h = pd.read_csv(f"{d}/histograms.csv")
    nav = pd.read_csv(f"data/{slug}/nav_daily.csv", usecols=["Date", "NAV_Rs"],
                      parse_dates=["Date"])
    nm = short(slug)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.semilogy(nav["Date"], nav["NAV_Rs"], lw=1.0, color=GOLD)
    ax.set_title(f"{nm} — Daily NAV (log)", color="white")
    ax.set_xlabel("Date"); ax.set_ylabel("NAV Rs")
    fig.tight_layout(); fig.savefig(f"{fd}/e1_nav.png"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    b = s[s.vol_mult == 1.0].sort_values(["horizon_d", "shock_pct"])
    for hd, g in b.groupby("horizon_d"):
        g = g.sort_values("shock_pct")
        ax.plot(g.shock_pct, g.mean_ret * 100, marker="o", ms=4,
                label=f"{int(hd)}d horizon")
    ax.set_title(f"{nm} — Expected return vs systematic shock (vol x1)",
                 color="white")
    ax.set_xlabel("Market shock (%)"); ax.set_ylabel("Mean return (%)")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(f"{fd}/e2_shock.png"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    b0 = s[(s.shock_pct == 0) & (s.vol_mult == 1.0)].sort_values("horizon_d")
    x = np.arange(len(b0)); w = 0.2
    for i, col in enumerate(["var95", "var99", "var999", "cvar99"]):
        ax.bar(x + (i - 1.5) * w, b0[col].values * 100, width=w, label=col)
    ax.set_xticks(x, [f"{int(v)}d" for v in b0.horizon_d])
    ax.set_title(f"{nm} — VaR / CVaR by horizon (no shock, vol x1)",
                 color="white")
    ax.set_ylabel("Loss (%)"); ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(f"{fd}/e3_var.png"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    sc_base = int(s[(s.shock_pct == 0) & (s.vol_mult == 1.0) &
                    (s.horizon_d == 252)].iloc[0].scen)
    sc_adv = int(s[(s.shock_pct == -20) & (s.vol_mult == 2.0) &
                   (s.horizon_d == 63)].iloc[0].scen)
    for sc, col, lab in [(sc_base, CY, "Base 1Y"), (sc_adv, MG, "-20% x2 1Q")]:
        g = h[h.scen == sc].sort_values("bin_lo_ret")
        mid = (g.bin_lo_ret + g.bin_hi_ret) / 2 * 100
        m = (mid > -60) & (mid < 80)
        ax.step(mid[m], g["count"][m], where="mid", color=col, label=lab)
    ax.set_title(f"{nm} — Return tails: base vs severely adverse",
                 color="white")
    ax.set_xlabel("Return (%)"); ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(f"{fd}/e4_tails.png"); plt.close(fig)
    return 4

n = 0
for slug in DEBT:
    n += debt_figs(slug); print("debt figs ok:", slug)
for slug in EQ:
    n += eq_figs(slug); print("eq figs ok:", slug)
print("TOTAL_FIGS", n)
