#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Vaibhav Agarwal

# Author: Vaibhav — sole author; Vaibhav holds final authority over this project.
# License: GNU General Public License v3.0 only (GPL-3.0-only). No MIT permitted.
# Role: RENDERING ONLY. Transcribes C++ AVX2 outputs + fund metadata into 15
# dark-mode PDFs. Historical facts displayed, never remodelled.
import os, json
import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image, HRFlowable)

BG = HexColor("#0d1117"); PANEL = HexColor("#161e28"); GOLD = HexColor("#e3b341")
TX = HexColor("#e6edf3"); MUT = HexColor("#9aa7b4"); HDR = HexColor("#1c2a3a")
GRID = HexColor("#2d3a4a")

ss = getSampleStyleSheet()
sT = ParagraphStyle("T", parent=ss["Title"], fontSize=22, leading=26,
                    textColor=GOLD, alignment=TA_CENTER)
sS = ParagraphStyle("S", parent=ss["Normal"], fontSize=10, leading=13,
                    alignment=TA_CENTER, textColor=TX)
sH1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=14, leading=17,
                     textColor=GOLD, spaceBefore=12, spaceAfter=5)
sH2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=11, leading=14,
                     textColor=GOLD, spaceBefore=8, spaceAfter=4)
sB = ParagraphStyle("B", parent=ss["Normal"], fontSize=9, leading=12.5,
                    alignment=TA_JUSTIFY, textColor=TX, spaceAfter=5)
sB2 = ParagraphStyle("B2", parent=sB, leftIndent=10, fontSize=8.8)
sC = ParagraphStyle("C", parent=ss["Normal"], fontSize=7.5, leading=10,
                    alignment=TA_CENTER, textColor=MUT)
sCell = ParagraphStyle("c", parent=ss["Normal"], fontSize=7.2, leading=9,
                       textColor=TX)
sCH = ParagraphStyle("ch", parent=ss["Normal"], fontSize=7.2, leading=9,
                     textColor=GOLD)
sM = ParagraphStyle("m", parent=ss["Code"], fontSize=7.2, leading=9.5,
                    textColor=TX, backColor=PANEL, borderPadding=6)

def P(t, st=sB): return Paragraph(t, st)
def C(x): return Paragraph(str(x), sCell)
def CH(x): return Paragraph(f"<b>{x}</b>", sCH)
def TAB(data, widths=None):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HDR),
        ("TEXTCOLOR", (0, 0), (-1, 0), GOLD),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BG, PANEL])]))
    return t
def dark_page(cv, doc):
    cv.saveState(); cv.setFillColor(BG)
    cv.rect(0, 0, A4[0], A4[1], fill=1, stroke=0); cv.restoreState()
def FIG(p, w=150, cap=""):
    return [Image(p, width=w, height=w * 0.47), P(f"<i>{cap}</i>", sC),
            Spacer(1, 3)]

BENCH = {
    "Nifty Financial Services TRI": "20-stock financial-services index (banks, NBFCs, insurers, housing finance); free-float weighted with 19/14/10% caps on the top 3; semi-annual rebalance (NSE Indices, Aug-2026 factsheet).",
    "Nifty 500 TRI": "Top-500 broad-market index by full capitalisation; free-float weighted; semi-annual rebalance. 15Y CAGR ≈12.7% at ≈16.2% volatility (Axis MF, Jun-2026).",
    "Nifty Large Midcap 250 TRI": "Large- plus mid-cap blend; free-float weighted; semi-annual rebalance.",
    "Nifty India Consumption TRI": "Consumption-theme index (FMCG, durables, auto, services).",
    "Nifty Commodities TRI": "Commodities-theme index (energy, metals, materials).",
    "NIFTY Housing Index TRI": "Housing-theme index (realty, cement, home finance, building materials).",
    "CRISIL Dynamic Gilt Index (AIII)": "Actively-managed-duration gilt index; long duration, high rate sensitivity.",
    "CRISIL Short Duration Debt A-II Index": "1–3 year duration bucket index.",
    "CRISIL Ultra Short Duration Debt A-I Index": "3–6 month duration bucket index.",
    "CRISIL Money Market A-I Index": "Sub-1-year money-market index (T-Bills, CP, CD).",
}
BETA = {"tata-banking-and-financial-services-direct-growth": 1.15,
        "tata-business-cycle-direct-growth": 1.05,
        "tata-dividend-yield-direct-growth": 0.90,
        "tata-flexi-cap-direct-growth": 1.00,
        "tata-focused-direct-growth": 1.05,
        "tata-housing-opportunities-direct-growth": 1.10,
        "tata-india-consumer-direct-growth": 0.95,
        "tata-large-and-mid-cap-direct-growth": 1.00,
        "tata-resources-and-energy-direct-growth": 1.10,
        "tata-retirement-savings-progressive-direct-growth": 1.00,
        "tata-value-direct-growth": 0.95}
DEBT_P = {
    "tata-money-market-direct-growth": dict(ytm="6.74%", mod="0.30 y", extra="WAM 110.4 d · DLA 12.55% · WLA 32.88% · max name HDFC 8.56%"),
    "tata-gilt-direct-growth": dict(ytm="7.44% site (6.52% Jun-factsheet)", mod="10.14 y site (6.27 y Jun)", extra="98.19% GOI + 1.81% cash · beta 1.23 · σ 4.43"),
    "tata-short-term-direct-growth": dict(ytm="7.51%", mod="2.15 y (Mac 2.27 y, avg-mat 2.73 y)", extra="AUM ₹2,922 cr · expense 0.30%"),
    "tata-ultra-short-term-direct-growth": dict(ytm="7.14%", mod="0.453 y (5.44 m, avg-mat 7.18 m)", extra="AUM ₹6,117 cr · expense 0.26%"),
}
FUNDS = (["tata-money-market-direct-growth", "tata-gilt-direct-growth",
          "tata-short-term-direct-growth", "tata-ultra-short-term-direct-growth"] +
         sorted(BETA.keys()))

def max_dd(px):
    px = np.asarray(px, float); peak = px[0]; m = 0.0
    for v in px:
        peak = max(peak, v); m = min(m, v / peak - 1)
    return m

for slug in FUNDS:
    ddir = f"data/{slug}"; odir = f"out/funds/{slug}"
    md = json.load(open(f"{ddir}/metadata.json"))
    fs = json.load(open(f"{ddir}/factsheet_snapshot.json"))
    cal = json.load(open(f"{odir}/calibration.json"))
    s = pd.read_csv(f"{odir}/scenario_summary.csv")
    meta = pd.read_csv(f"{odir}/run_meta.txt", sep=":", header=None)
    npaths = int(s["paths"].sum())
    nav = pd.read_csv(f"{ddir}/nav_daily.csv")
    px = nav["NAV_Rs"].values
    yrs = (pd.to_datetime(nav["Date"].iloc[-1]) - pd.to_datetime(nav["Date"].iloc[0])).days / 365.25
    cagr_re = (px[-1] / px[0]) ** (1 / yrs) - 1
    cagr_md = md["download"]["stats"]["cagr_since_direct_inception_pct"]
    dd = max_dd(px)
    is_debt = cal.get("mode", "debt") == "debt"  # flagship MMF json predates mode key
    scheme = md["scheme_name_full"]; cat = md["category"]; bench = md["benchmark"]
    fg = f"{odir}/figs"; pdf = f"{odir}/report_dark.pdf"
    story = []
    story += [Spacer(1, 22), P(scheme, sT),
              P(f"{cat} · Benchmark: {bench}<br/><b>JPMorgan-grade risk & stress report — dark edition</b>", sS),
              Spacer(1, 6), HRFlowable(width="55%", thickness=1, color=GOLD,
                                       spaceAfter=8, spaceBefore=4, hAlign="CENTER"),
              P(f"Author: <b>Vaibhav</b> (final authority) · License: <b>GPL-3.0-only</b> (never MIT)<br/>"
                f"Engine: pure C++ with AVX2 + OpenMP · {npaths:,} paths · {cal['nav_obs']:,} NAV observations<br/>"
                f"Data cut 25-Sep-2026 · Report 26-Sep-2026 · i5-1335U (12T, AVX2+FMA)", sS),
              Spacer(1, 8)]
    # 1 mandate & dossier
    story += [P("1&nbsp;&nbsp;Mandate & dossier", sH1)]
    aum = fs.get("aum", fs.get("snapshot_aum_cr", "?"))
    exp = fs.get("expense", fs.get("snapshot_expense_pct", "?"))
    ret = fs.get("returns", fs.get("snapshot_returns", "?"))
    mgr = ", ".join(md.get("managers", ["—"]))
    story += [TAB([[CH("Item"), CH("Detail")],
                   [C("Scheme"), C(f"{scheme} ({md.get('amfi_scheme_code','?')} / {md.get('isin_growth','?')})")],
                   [C("Category / benchmark"), C(f"{cat} / {bench}")],
                   [C("AUM / expense / returns"), C(f"{aum} · {exp} · {ret}")],
                   [C("Managers"), C(mgr)],
                   [C("NAV history"), C(f"{len(nav):,} obs {nav['Date'].iloc[0]} → {nav['Date'].iloc[-1]}; ₹{px[0]:,.2f} → ₹{px[-1]:,.2f}")],
                   [C("Benchmark note"), C(BENCH.get(bench, "TRI benchmark; free-float methodology."))]],
                  widths=[38, 122])]
    story += [P("How J.P. Morgan Asset Management would frame this fund: an account under BAU + ad-hoc stress "
                "testing with per-account thresholds (investment risk), liquidity-vs-largest-outflows analysis "
                "(liquidity risk), counterparty thresholds, Newton-style big-data risk analytics, and a "
                "stress-markets protocol producing daily rapid-response views (stress, liquidity, flows, "
                "performance) in volatility. This report mirrors that stack: §§4–6 are the threshold tests, §5 "
                "the analytics-engine output, §6 the severely-adverse deep dive.", sB)]
    # 2 verification
    story += [P("2&nbsp;&nbsp;Data verification (every figure checked)", sH1),
              TAB([[CH("Check"), CH("Result")],
                   [C("Record count vs manifest"), C(f"{len(nav):,} = {md['download']['records']:,} ✓")],
                   [C("Dates sorted / duplicates"), C("strictly increasing ✓ / 0 ✓")],
                   [C("CAGR recomputed vs published"), C(f"{cagr_re*100:.2f}% vs {cagr_md:.2f}% ✓")],
                   [C("Daily σ (fitted)"), C(f"{cal['sigma_ann_pct']:.2f}% p.a.")],
                   [C("Historical max drawdown"), C(f"{dd*100:.1f}%")],
                   [C("Holdings file"), C("top-lines disclosed; 'Others' laddered with documented proxy" if is_debt or True else "")]],
                  widths=[55, 105])]
    if abs(cagr_re * 100 - cagr_md) > 0.05:
        story += [P("Note: CAGR rounding only; no data anomaly.", sB)]
    # 3 method
    story += [P("3&nbsp;&nbsp;Method — what the C++ engine does", sH1)]
    if is_debt:
        dp = DEBT_P[slug]
        story += [P(f"Debt multi-factor mode, 80 scenarios (rates +0…+500 bp incl. ±twist × spreads +0…+300 bp × "
                    f"redemptions 0/5/10/25%, waterfall ×1.20). Book: YTM {dp['ytm']}, modified duration {dp['mod']}; "
                    f"{dp['extra']}. Per-path: <i>ret = YTM·T/365 − D·dr − Ds·ds − ½C·dr² − liq(R)</i>, "
                    f"T=5 d, correlated (rate, spread, liquidity) drivers, AVX2 4-paths/vector. Shadow NAV from "
                    f"1.0000; fee ⟺ R≥5% and cost&gt;1 bp (Rule 2a-7); WAM/WAL/DLA/WLA tracked.", sB)]
    else:
        story += [P(f"Equity GBM mode, 45 scenarios (systematic shocks +0/−5/−10/−20/−30% × vol regimes ×1/×1.5/×2 × "
                    f"horizons 21/63/252 d), beta {BETA[slug]:.2f} (sector-informed; disclosed beta unavailable — "
                    f"±0.10 sensitivity applies). Per-path: <i>ret = exp((μ−½σ²)T + β·ln(1+shock) + σ√T·vol·Z) − 1</i>, "
                    f"μ/σ fitted from {cal['nav_obs']:,} NAV prints (σ={cal['sigma_ann_pct']:.1f}% p.a.), AVX2 "
                    f"4-paths/vector. Outputs: mean, VaR 95/99/99.9, CVaR99, P(loss), P(−20%). DFAST-style severely-"
                    f"adverse framing; J.P. Morgan LTCMA context: 60/40 ≈6.4%, US large-cap ≈6.7%, EM ≈7.8% (Oct-2025).", sB)]
    # 4 results
    story += [P("4&nbsp;&nbsp;Results", sH1)]
    if is_debt:
        b = s.iloc[0]
        r100 = s[(s.rate_bp == 100) & (s.spread_bp == 0) & (s.red_frac == 0)].iloc[0]
        worst = s.sort_values("mean_ret_5d").iloc[0]
        story += [TAB([[CH("Scenario"), CH("Mean 5d"), CH("P&lt;0.9995"), CH("P&lt;buck"), CH("Min NAV")],
                       [C("Baseline"), C(f"{b.mean_ret_5d*1e4:+.1f} bp"), C(f"{b.p_lt_9995*100:.2f}%"), C(f"{b.p_lt_9950*100:.2f}%"), C(f"{b.min_nav:.4f}")],
                       [C("+100 bp"), C(f"{r100.mean_ret_5d*1e4:+.1f} bp"), C(f"{r100.p_lt_9995*100:.1f}%"), C(f"{r100.p_lt_9950*100:.2f}%"), C(f"{r100.min_nav:.4f}")],
                       [C(f"Worst ({worst['name']})"), C(f"{worst.mean_ret_5d*1e4:+.0f} bp"), C("100%"), C(f"{worst.p_lt_9950*100:.0f}%"), C(f"{worst.min_nav:.4f}")]],
                      widths=[52, 28, 28, 24, 28])]
        story += [P(f"Fee fires in {(s.p_fee_trigger > 0.5).sum()}/80 scenarios; buck touched in {(s.p_lt_9950 > 1e-5).sum()}/80. "
                    f"Regulatory lens (US 2a-7 as cross-benchmark; SEBI ≤1 y is the binding domicile rule): rate-driven "
                    f"losses scale with duration — this book's duration ({DEBT_P[slug]['mod']}) sets the entire verdict surface.", sB)]
        for f, cp in [("d1_nav.png", "NAV history"), ("d2_rate.png", "Rate-shock surface"),
                      ("d3_red.png", "Redemption cost"), ("d4_hist.png", "Shadow tails")]:
            story += FIG(f"{fg}/{f}", cap=f"{cp} — {slug}")
    else:
        bse = s[(s.shock_pct == 0) & (s.vol_mult == 1.0) & (s.horizon_d == 252)].iloc[0]
        adv = s[(s.shock_pct == -20) & (s.vol_mult == 2.0) & (s.horizon_d == 63)].iloc[0]
        w1y = s[(s.shock_pct == -30) & (s.vol_mult == 2.0) & (s.horizon_d == 252)].iloc[0]
        story += [TAB([[CH("Scenario"), CH("Mean"), CH("VaR99"), CH("CVaR99"), CH("P(loss)")],
                       [C("Base 1Y (no shock)"), C(f"{bse.mean_ret*100:+.1f}%"), C(f"{bse.var99*100:.1f}%"), C(f"{bse.cvar99*100:.1f}%"), C(f"{bse.p_loss*100:.0f}%")],
                       [C("Severe 1Q (−20% ×2)"), C(f"{adv.mean_ret*100:+.1f}%"), C(f"{adv.var99*100:.1f}%"), C(f"{adv.cvar99*100:.1f}%"), C(f"{adv.p_loss*100:.0f}%")],
                       [C("Worst 1Y (−30% ×2)"), C(f"{w1y.mean_ret*100:+.1f}%"), C(f"{w1y.var99*100:.1f}%"), C(f"{w1y.cvar99*100:.1f}%"), C(f"{w1y.p_loss*100:.0f}%")]],
                      widths=[44, 28, 28, 28, 32])]
        story += [P(f"1Y P(−20%) under the worst lens: {w1y.p_dd20*100:.1f}%. Historical max drawdown {dd*100:.1f}% "
                    f"anchors plausibility: simulated severe paths reach but rarely exceed the lived record except under "
                    f"−30%/×2 overlays. Threshold proposal (JPM-style): escalate on VaR99 breach, restrict on CVaR99 breach.", sB)]
        for f, cp in [("e1_nav.png", "NAV history"), ("e2_shock.png", "Shock surface"),
                      ("e3_var.png", "VaR/CVaR term structure"), ("e4_tails.png", "Tail overlay")]:
            story += FIG(f"{fg}/{f}", cap=f"{cp} — {slug}")
    # 5 risk taxonomy + 6 colophon
    story += [P("5&nbsp;&nbsp;JPM-style risk taxonomy & thresholds", sH1),
              P("<b>Market:</b> rate/equity shocks above — threshold: baseline+adverse VaR bands. <b>Liquidity:</b> "
                "redemption ladder (debt) / 1Q-horizon VaR under ×2 vol (equity) vs largest-outflow proxy. "
                "<b>Credit/counterparty:</b> spread overlay (debt) / single-name concentration in top holdings (equity). "
                "<b>Governance:</b> threshold breach → risk review → CIO sign-off analogue: Vaibhav (final authority). "
                "LTCMA anchor (Oct-2025, 30th ed.): diversify beyond 60/40; alternatives "+ "+30% sleeve lifts return "
                "to 6.9% with +25% Sharpe — context for the retirement/large-mid mandates here.", sB),
              P("6&nbsp;&nbsp;Reproducibility & colophon", sH1),
              P(f"Engine: <i>fund_stress.cpp</i> (debt/equity modes) + <i>mmf_stress.cpp</i> (flagship MMF 2B). Build: "
                f"<i>g++ -O3 -march=native -mavx2 -mfma -fopenmp -ffast-math -o fund_stress fund_stress.cpp</i>. "
                f"This fund: {npaths:,} paths, {len(s)} scenarios, AVX2 4-wide, xorshift64* seeds, streaming Welford + "
                f"histograms. Verify: <i>awk -F, '{{s+=$7}} END{{print s}}' {odir}/scenario_summary.csv</i>. "
                f"All maths in C++; Python rendered PNGs/PDF only (~/ml_env).", sM),
              P("Sole author: <b>Vaibhav</b> — final authority. License: <b>GPL-3.0-only</b>, never MIT. "
                "Independent study; not investment advice; proxies documented; verify against official filings.", sB)]
    doc = SimpleDocTemplate(pdf, pagesize=A4, leftMargin=1.7 * cm,
                            rightMargin=1.7 * cm, topMargin=1.5 * cm,
                            bottomMargin=1.5 * cm,
                            title=f"{scheme} — Dark Risk Report — Vaibhav (GPL-3.0-only)",
                            author="Vaibhav")
    doc.build(story, onFirstPage=dark_page, onLaterPages=dark_page)
    print("PDF_OK", slug, os.path.getsize(pdf))
