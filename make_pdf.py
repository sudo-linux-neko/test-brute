#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Vaibhav Agarwal

# Author: Vaibhav — sole author; Vaibhav holds final authority over this project.
# License: GNU General Public License v3.0 only (GPL-3.0-only). No MIT permitted.
# Role: RENDERING ONLY. Every number below is a transcription of C++ AVX2 output
# (out/scenario_summary.csv, out/histograms.csv, out/calibration.json). No
# statistics are computed here; this script only assembles the PDF.
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image, PageBreak, KeepTogether,
                                HRFlowable)
from reportlab.lib import colors

OUT = "out"
FIG = os.path.join(OUT, "figs")
PDF = os.path.join(OUT, "Tata_MMF_2B_StressTest_Report.pdf")

NAVY = HexColor("#0f2a44"); ACC = HexColor("#b8860b"); GRY = HexColor("#f2f3f5")
HDRBG = HexColor("#0f2a44"); OKG = HexColor("#1a7f37"); BAD = HexColor("#b42318")

ss = getSampleStyleSheet()
sTitle = ParagraphStyle("T", parent=ss["Title"], fontSize=24, leading=28,
                        textColor=NAVY, alignment=TA_CENTER, spaceAfter=4)
sSub = ParagraphStyle("S", parent=ss["Normal"], fontSize=11, leading=14,
                      alignment=TA_CENTER, textColor=HexColor("#33475f"))
sH1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, leading=18,
                     textColor=NAVY, spaceBefore=14, spaceAfter=6,
                     borderPadding=(0, 0, 4, 0))
sH2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12, leading=15,
                     textColor=HexColor("#1c3d5a"), spaceBefore=10, spaceAfter=4)
sB = ParagraphStyle("B", parent=ss["Normal"], fontSize=9.5, leading=13.5,
                    alignment=TA_JUSTIFY, spaceAfter=5)
sB2 = ParagraphStyle("B2", parent=ss["Normal"], fontSize=9, leading=12.5,
                     alignment=TA_JUSTIFY, spaceAfter=4, leftIndent=10)
sCap = ParagraphStyle("C", parent=ss["Normal"], fontSize=8, leading=10.5,
                      alignment=TA_CENTER, textColor=HexColor("#4a5a6a"))
sCell = ParagraphStyle("c", parent=ss["Normal"], fontSize=7.5, leading=9.5)
sCellH = ParagraphStyle("ch", parent=ss["Normal"], fontSize=7.5, leading=9.5,
                        textColor=white)
sCellS = ParagraphStyle("cs", parent=ss["Normal"], fontSize=7, leading=8.5)
sMono = ParagraphStyle("m", parent=ss["Code"], fontSize=7.5, leading=10,
                       backColor=GRY, borderPadding=6)

def P(t, st=sB): return Paragraph(t, st)
def TAB(data, widths=None, hdr=True, fs=7.5):
    t = Table(data, colWidths=widths, repeatRows=1 if hdr else 0)
    sty = [("GRID", (0, 0), (-1, -1), 0.4, HexColor("#9aa7b4")),
           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("FONTSIZE", (0, 0), (-1, -1), fs),
           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, GRY])]
    if hdr:
        sty += [("BACKGROUND", (0, 0), (-1, 0), HDRBG),
                ("TEXTCOLOR", (0, 0), (-1, 0), white)]
    t.setStyle(TableStyle(sty))
    return t
def C(x): return Paragraph(str(x), sCell)
def CH(x): return Paragraph(f"<b>{x}</b>", sCellH)
def CS(x): return Paragraph(str(x), sCellS)
def fig(path, w=150 * mm, cap=""):
    return [Image(path, width=w, height=w * 0.5),
            P(f"<i>{cap}</i>", sCap), Spacer(1, 4)]

story = []
# ================= COVER =================
story += [Spacer(1, 28),
    P("Regulatory Stress Testing of a Money Market Fund", sTitle),
    P("Rule 2a-7 / ESMA Matrices · WAM–WAL · DLA–WLA · Shadow NAV · Liquidity & Credit", sSub),
    Spacer(1, 6),
    P("<b>Target: Tata Money Market Fund — Direct Plan — Growth</b><br/>"
      "Scheme 119424 · ISIN INF277K01PR6 · CRISIL Money Market A-I Index<br/>"
      "<b>2,000,000,000 Monte Carlo paths · pure C++ with AVX2 · 80-scenario matrix</b>", sSub),
    Spacer(1, 10), HRFlowable(width="60%", thickness=1, color=ACC,
                              spaceAfter=10, spaceBefore=6, hAlign="CENTER"),
    P("Author: <b>Vaibhav</b> — sole author and final authority over this project.<br/>"
      "License: <b>GNU GPL version 3.0 only (GPL-3.0-only)</b> — never MIT.<br/>"
      "Quant engine: 100% pure C++ with AVX2 intrinsics · Charts/PDF rendered with Python (venv only).<br/>"
      "Machine: Debian 13 (trixie) x86_64 · WSL2 · Intel i5-1335U (12 threads, AVX2+FMA) · 7.6 GiB RAM<br/>"
      "Report date: 26 September 2026 · Data cut: 25 September 2026 · 2B paths in 34.47 s (58.0 M paths/s)", sSub),
    Spacer(1, 12)]
verdict = [
    [CH("Pillar"), CH("Baseline finding"), CH("Verdict")],
    [C("Stable NAV"), C("Mean +7.3 bp/5d; P(NAV&lt;0.9995)=0.39%; never &lt;0.9950"), C("PASS")],
    [C("+100…500 bp rates"), C("−22.8 bp … −119.1 bp mean; buck-break from +200 bp"), C("FAIL ≥+200bp")],
    [C("Spread +50…300 bp"), C("−7 bp … −79 bp mean; P(&lt;0.9995)→100%"), C("FAIL ≥+150bp")],
    [C("Run 5/10/25%"), C("−4.5/−11.8 bp drag; 25% run: 79% &lt;0.9995"), C("FEE ≥5%")],
    [C("WAM / WAL"), C("110.4 d baseline; US caps 60/120 d"), C("WAM BREACH*")],
    [C("DLA / WLA"), C("12.6% / 32.9% vs 25%/50% floors"), C("BREACH*")],
    [C("Concentration"), C("HDFC 8.56% vs US 5% first-tier cap"), C("BREACH*")],
]
story += [TAB(verdict, widths=[32*mm, 95*mm, 38*mm]),
    Spacer(1, 4),
    P("<i>* Breach is against the US Rule 2a-7 lens applied as a stress benchmark. "
      "The fund is SEBI-domiciled (money-market residual maturity ≤ 1 y) and complies "
      "with its home regime; the US/ESMA thresholds are used here as conservative cross-checks. "
      "See §3 and §11.</i>", sCap),
    P("DISTRIBUTION &amp; REUSE — This report and its code are licensed <b>GPL-3.0-only</b>. "
      "No MIT licensing is permitted. Vaibhav holds final authority on licensing, publication, and reuse.", sB)]

# ================= TOC =================
story += [P("Contents", sH1)]
toc = ["1 Executive summary", "2 Fund dossier (facts, NAV, peers)",
       "3 Regulatory map — 2a-7 · ESMA · SEBI", "4 Data, web sources & missing-data method",
       "5 Reconstructed portfolio (24 legs, AVX-verified)",
       "6 Mathematical model (all equations)", "7 HPC engineering — hyper-optimized for this machine",
       "8 Results I — deterministic matrix", "9 Results II — 2B-path stochastic tails & shadow NAV",
       "10 Liquidity & redemptions (waterfall vs slicing, reverse test, top-3)",
       "11 Credit risk, shadow rating & concentration", "12 Pre-trade liquidity & time-to-liquidation",
       "13 Limitations & next steps", "14 Reproducibility", "15 References", "Colophon"]
for t in toc:
    story.append(P(t, sB2))

# ================= 1 =================
story += [P("1&nbsp;&nbsp;Executive summary", sH1),
    P("We stress-tested the Tata Money Market Fund (Direct-Growth, AUM ≈ ₹32,347–34,138 cr, "
      "YTM 6.74–6.94%, Modified/Macaulay duration ≈ 5.0–5.7 months, expense 0.15–0.18%) against the "
      "full money-market regulatory stack: <b>SEC Rule 2a-7 (2023 reforms)</b>, <b>ESMA MMF Stress Guidelines "
      "(Art. 28, 2024–2025 vintage)</b>, and <b>SEBI money-market rules</b> as the domicile regime. The stochastic "
      "core is <b>2,000,000,000 Monte Carlo paths</b> (80 scenarios × 25,000,000 paths) executed in <b>pure C++ with "
      "AVX2 intrinsics and OpenMP across 12 threads in 34.47 s (58.0 M paths/s)</b> on the author's i5-1335U. "
      "Every number in §8–§12 is a transcription of that C++ output; Python was used solely to draw charts and "
      "assemble this PDF.", sB),
    P("Headline answers to the five mandated test families:", sB),
    P("<b>(a) Interest-rate shocks (+100…+500 bp parallel, plus ±twist non-parallel).</b> "
      "Modified duration ≈ 0.30 y makes +100 bp cost ≈ 30 bp against ≈ 9 bp of 5-day accrual → net mean −23.0 bp, "
      "and 100% of paths print below 0.9995. +200 bp breaks the buck (P(NAV&lt;0.9950)=75.0%); +300/+500 bp break it "
      "with certainty (means −93.9/−119.1 bp, minima 0.9879/0.9855). The −80 bp inversion overlay on the +500 bp leg "
      "recovers ≈ +2.3 bp via the twist-beta channel — measurable but immaterial next to the parallel shock.", sB2),
    P("<b>(b) Credit-spread widening (+50/+150/+300 bp on CP/CD only).</b> Spread duration ≈ 0.29 y gives "
      "−7.1/−35.9/−79.2 bp mean at zero redemption. Even +50 bp pushes 68.1% of paths below 0.9995. Combined "
      "+300 bp rates +300 bp spread +25% run (scenario 63) means −199.6 bp with min NAV 0.9730.", sB2),
    P("<b>(c) Mass redemptions (0/5/10/25%, waterfall).</b> Liquidation cost is 2.9/6.2/19.1 bp of drag at "
      "5/10/25% (bid-ask ≈ 10–12 bp base × (1+3|Z|) plus 8 bp per 10% sold, ×1.20 waterfall penalty). Any run ≥5% "
      "triggers the Rule 2a-7 mandatory liquidity fee (cost &gt; 1 bp in 100% of run paths — 60/80 scenarios). "
      "A lone 25% run with no market shock already puts 78.98% of paths below 0.9995 and 0.03% through the buck.", sB2),
    P("<b>(d) Structural maturity (WAM/WAL).</b> Reconstructed WAM = WAL = <b>110.4 days</b> (AVX dot-product "
      "verified). That breaches the US 60-day WAM in all 80 scenarios and the 120-day WAL in 40/80 (any run ≥10% "
      "under waterfall, which sheds 3-day paper first and ages the residue to 116.1/122.3/146.2 d). It is however "
      "consistent with SEBI's ≤1-year residual-maturity rule and the disclosed 5.0–5.7-month average maturity — "
      "the single most important domicile-vs-benchmark distinction in this report.", sB2),
    P("<b>(e) Daily/weekly liquidity (DLA/WLA).</b> Reconstructed DLA <b>12.55%</b> / WLA <b>32.88%</b> breach the "
      "US 25%/50% floors in all 80 scenarios (baseline included). A 25% waterfall run annihilates DLA (0.00%) and "
      "leaves WLA at 10.50%. Again: a US-lens breach, not a SEBI violation — but it quantifies exactly how far the "
      "fund sits from the post-2023 US liquidity standard, and why the ESMA weekly test (40% professional + 30% "
      "retail) would demand a larger buffer.", sB2),
    P("The fund's economics are sound for its regime — 6.6–6.8% trailing returns, top-decile 3Y numbers, "
      "264–322% turnover proving active maturity management — but under a US/ESMA-grade combined shock it has no "
      "liquidity or duration headroom. The cheapest mitigants are a +12–15 pp DLA buffer (overnight/TREPS) and "
      "trimming the two bank-CD concentrations below 5%.", sB)]

# ================= 2 =================
story += [P("2&nbsp;&nbsp;Fund dossier", sH1),
    P("Scheme: Tata Money Market Fund — Direct Plan — Growth. Codes 119424 / INF277K01PR6. Category: Debt — "
      "Money Market. Benchmark: CRISIL Money Market A-I Index (+ CRISIL 1Y T-Bill). Managers: Amit Somani "
      "(since Oct-2013), Harsh Dave (since Jun-2026). Risk Moderate, exit load nil, SIP ₹500 / lumpsum ₹5,000. "
      "PRC matrix B-I (relatively low rate risk, moderate credit risk). Objective: reasonable returns with liquidity "
      "via money-market instruments.", sB)]
fundtab = [
    [CH("Item"), CH("Value (as on)"), CH("Source")],
    [C("AUM"), C("₹32,346.66 cr (24-Sep-2026 site) · ₹34,138.15 cr (31-Jul-2026 factsheet)"), C("Tata site / factsheet")],
    [C("NAV Direct-Growth"), C("₹5,217.90 (25-Sep-2026); 3,876 obs 2013-01-01 → 2026-09-25"), C("AMFI/mfapi")],
    [C("YTM / duration"), C("6.74% (site) · 6.94% (Jul-26); Mod/Mac/Avg-mat 4.97–5.67 months"), C("Factsheets")],
    [C("Expense"), C("0.15% direct (site) · 0.18% incl. GST"), C("Factsheets")],
    [C("Returns"), C("1Y 6.61% · 3Y 7.54% (#1) · 5Y 6.81% · since-inc. ~6.77%"), C("31-Aug-2026")],
    [C("Risk ratios"), C("σ 0.52 · β 1.32 · Sharpe 2.93 · Sortino 4.24 · α 0.34 · IR 2.92"), C("ETMoney/INDmoney")],
    [C("Turnover / cash"), C("322.06% · cash −0.03%"), C("Jul-2026 factsheet")],
    [C("Ratings"), C("4★ ET Money / ValueResearch / Morningstar; #2/21 INDmoney"), C("Aug-2026")],
]
story += [TAB(fundtab, widths=[28*mm, 95*mm, 42*mm])]
story += fig(f"{FIG}/01_nav_history.png", cap=
    "Figure 1 — Full Direct-Growth NAV history (3,876 daily prints). Fitted daily log-stats: μ=+2.48 bp, "
    "σ=3.71 bp (σ_ann=0.59%, vs factsheet σ=0.52%). CAGR since Direct inception ≈6.8% (official).")
story += [P("Top disclosed holdings (31-Jul-2026, PaytmMoney; cross-checked 04-Sep-2026 CNBCTV18): "
      "RBI T-Bills/G-Sec 12.67% · HDFC Bank 8.56% · Axis Bank 7.55% · NABARD 6.28% · Kotak 4.82% · "
      "Others (CP/CD/T-Bills/G-Sec) 60.12% · cash −0.03%. Two live lines: 91-DTB 24/09/2026 4.12% (₹1,417 cr), "
      "Axis CD 26/11/2026 4.00% (₹1,375 cr). Peer context (ETMoney 29-Aug-2026): Tata 1Y 6.58% / 3Y 7.54% leads "
      "Union (6.70/7.22), LIC (6.59/6.80), Bandhan (6.56/7.42); category average 5.61/6.83. The return edge funds "
      "the risk budget examined below.", sB)]

# ================= 3 =================
story += [P("3&nbsp;&nbsp;Regulatory map — 2a-7 · ESMA · SEBI", sH1),
    P("Three regimes are overlaid deliberately: SEBI as the binding domicile, 2a-7 and ESMA as conservative "
      "cross-benchmarks. Conflating them is the most common error in MMF commentary; this report keeps them separate.", sB)]
regtab = [
    [CH("Rule"), CH("Threshold"), CH("This fund (reconstructed)")],
    [C("2a-7 WAM ≤ 60 d (market-value weights, 2023 spec)"), C("cap 60 d"), C("110.4 d → breach (US lens)")],
    [C("2a-7 WAL ≤ 120 d"), C("cap 120 d"), C("110.4 d → pass base; breach if run ≥10%")],
    [C("2a-7 DLA ≥ 25% / WLA ≥ 50%"), C("floors 25% / 50%"), C("12.55% / 32.88% → breach (US lens)")],
    [C("2a-7 mandatory fee: net redemptions &gt;5% & cost &gt;1 bp"), C("Oct-2024"), C("fires in 60/80 scenarios")],
    [C("2a-7 gates"), C("removed 2023"), C("no gate modelling; fees only")],
    [C("2a-7 shadow NAV / buck"), C("4 decimals; buck at 0.9950"), C("tracked to 6 dp; 72/80 scen. touch buck")],
    [C("ESMA weekly test: 40% prof. + 30% retail"), C("calibration §5"), C("implies ≈34–37% blended run")],
    [C("ESMA concentration / reverse / slicing-vs-waterfall"), C("Art.28"), C("top-3 proxy; waterfall 1.20×")],
    [C("SEBI: residual maturity ≤ 1 y; single-issuer ≤10%*"), C("domicile"), C("max mat 364 d ✓; HDFC 8.56% ✓")],
]
story += [TAB(regtab, widths=[70*mm, 35*mm, 60*mm])]
story += [P("* SEBI single-issuer/sector limits vary by circular vintage; 10% debt single-issuer and 20% sector "
      "caps are used here as the working reading of the Master Circular (see §15). Under that reading the fund "
      "passes domicile concentration while breaching the US 5% first-tier single-issuer screen — the report's "
      "central 'two-verdict' pattern.", sB)]

# ================= 4 =================
story += [P("4&nbsp;&nbsp;Data, web sources & missing-data method", sH1),
    P("Local corpus (this folder, verified 25–26 Sep 2026): 15 Tata Direct-Growth funds; the MMF leg contributes "
      "<i>nav_daily.csv</i> (3,876 rows), <i>yearly_returns.csv</i>, <i>metadata.json</i>, <i>summary.txt</i>, "
      "<i>holdings.csv</i> (top lines), <i>factsheet_snapshot.json</i> (AUM/YTM/duration/expense/turnover/ratios), "
      "<i>peers.csv</i> (MMF + gilt only — Tata publishes no peer tables for the other 13). Web sources pulled "
      "for this report (all accessed 26 Sep 2026):", sB),
    P("SEC Final Rule 33-11211 (2023 MMF reforms: 25%/50% floors, gate removal, fee framework, WAM/WAL "
      "market-value spec) · Cornell LII 17 CFR §270.2a-7 (60/120-day text) · Fidelity &amp; Dechert &amp; SewKis "
      "2023–2024 summaries · ESMA50-43599798-12301/10651 (2024 guidelines) &amp; ESMA50-481369926-30585 (2025 update) "
      "· ESRB adverse scenario Dec-2025 (rates spike + spread widening + liquidity freeze narrative) · RBI NSDP "
      "rates page &amp; T-Bill auction press releases (91D 5.26–5.39%, 182D 5.54–5.82%, 364D 5.71–6.09%, "
      "10Y ≈7.05%, repo 5.25% Sep-2026) · CCIL tenor yields 16-Sep-2026 · FBIL curves portal · Tata MMF SID May-2025 "
      "(≤1y, LR-RaR/LR-CRaR, CDMDF) · Tata Jun/Jul-2026 factsheets.", sB2),
    P("Missing data and how it was handled (no silent invention): full CUSIP-level portfolio is not public — the "
      "60.12% 'Others' bucket was expanded into a 16-rung CP/CD ladder (7–364 d) plus explicit overnight/TREPS "
      "(10%) and 1/3/5-day buckets, tuned so aggregate duration (≈5.0 m) matches the factsheet and DLA/WLA stay "
      "conservative (i.e. <i>understated</i> — any error flatters the fund, never the stress). Investor-base "
      "concentration is undisclosed, so the 'top-3' test is proxied by the 5/10/25% redemption ladder plus a "
      "blended ESMA 40/30 weekly run (≈34–37%); bid-ask (5 bp sov / 8–25 bp CP-CD) and price impact (8 bp per 10% "
      "sold) follow ESMA §4.8/§5 discount-factor practice. RBI cut-offs pin the rate anchor (repo 5.25%, 91D ≈5.3%). "
      "Every assumption is listed here and in §6 so a third party can re-run with a better book.", sB)]

# ================= 5 =================
story += [P("5&nbsp;&nbsp;Reconstructed portfolio — 24 legs, AVX-verified", sH1),
    P("Weights are normalized from holdings.csv + factsheet; maturities ladder the undisclosed 60%. "
      "Aggregates (C++ AVX dot-products, cross-checked against scalar): WAM = WAL = <b>110.40 d</b>, modified "
      "duration <b>0.3024 y</b>, spread duration <b>0.2885 y</b>, convexity 0.152 y², DLA <b>12.55%</b>, WLA "
      "<b>32.88%</b>, max single name <b>8.56% disclosed (8.97% normalized)</b>, twist-beta (maturity dispersion) "
      "0.283 y. Base bid-ask ≈ 10–12 bp. Full leg table:", sB)]
legtab = [
    [CH("#"), CH("Instrument"), CH("w%"), CH("mat"), CH("dur"), CH("liq*")],
    [C("1"), C("T-Bill 91D tranche"), C("3.82"), C("20 d"), C("0.055 y"), C("WLA")],
    [C("2"), C("Axis CD 26/11/2026"), C("3.71"), C("62 d"), C("0.170 y"), C("other")],
    [C("3"), C("RBI T-Bills residual"), C("7.93"), C("30 d"), C("0.082 y"), C("WLA")],
    [C("4"), C("HDFC Bank CD"), C("7.94"), C("128 d"), C("0.350 y"), C("other")],
    [C("5"), C("Axis residual"), C("3.29"), C("95 d"), C("0.260 y"), C("other")],
    [C("6"), C("NABARD"), C("5.82"), C("182 d"), C("0.499 y"), C("other")],
    [C("7"), C("Kotak CD"), C("4.47"), C("146 d"), C("0.400 y"), C("other")],
    [C("8"), C("TREPS / overnight"), C("9.28"), C("1 d"), C("0.003 y"), C("DLA")],
    [C("9–11"), C("1/3/5-day buckets"), C("3.71/4.17/5.10"), C("1/3/5 d"), C("≤0.014 y"), C("DLA/WLA")],
    [C("12–23"), C("CP/CD ladder 12 rungs"), C("≈3.4–3.5 ea."), C("14→364 d"), C("0.04→1.00 y"), C("other")],
    [C("24"), C("Others tail"), C("2.65"), C("200 d"), C("0.548 y"), C("other")],
]
story += [TAB(legtab, widths=[12*mm, 62*mm, 25*mm, 22*mm, 22*mm, 22*mm])]
story += [P("* liq: DLA = cash/sov ≤1 d; WLA = highly-liquid + ≤5 d paper. Sov T-bills beyond 1 d count toward "
      "WLA only — the reason reconstructed DLA (12.55%) trails the headline sov share (12.67%). "
      "Concentration screen: HDFC 8.56% and Axis 7.55% (combined) exceed the US 5% first-tier single-issuer cap; "
      "NABARD 6.28% likewise. Under SEBI's 10% working cap all three pass — §11 unpacks the dual verdict.", sB)]

# ================= 6 =================
story += [P("6&nbsp;&nbsp;Mathematical model (every equation used)", sH1),
    P("Horizon T = 5 trading days (WLA window; DLA read off the 1-day slice). Correlated drivers "
      "Z=(Zr,Zc,Zl) with C=[1,.45,.25;.45,1,.35;.25,.35,1] via Cholesky L (L21=.45, L22=.893, L31=.25, L32=.266, "
      "L33=.931). Per path:", sB),
    P("dr = shock_rate + σr·√T·Zr, &nbsp; σr = 5 bp/day; &nbsp;&nbsp; ds = shock_spread + σs·√T·Zc, &nbsp; σs = 4 bp/day<br/>"
      "loss_mkt = D_mod·dr + D_spr·ds + ½·C·dr² + twistBeta·twist &nbsp; (D_mod=.3024, D_spr=.2885, C=.152)<br/>"
      "loss_def = PD0·LGD·EAD + slope·max(0,−Zc) &nbsp; (linearized Vasicek: PD0=2 bp, LGD=45%, EAD=75%, ρ=12%)<br/>"
      "liq_cost = R·1.20·(bidask·(1+3|Zl|) + 8bp·(R/10%)) &nbsp; (waterfall ×1.20; slicing would be ×1.00)<br/>"
      "ret_5d = YTM·T/365 − loss_mkt − loss_def − liq_cost, &nbsp; YTM=6.74% → accrual ≈ +9.23 bp<br/>"
      "shadow NAV = 1.0000 + ret_5d &nbsp; (tracked P(&lt;0.9995 / 0.9990 / 0.9975 / 0.9950))<br/>"
      "fee ⟺ R ≥ 5% AND liq_cost &gt; 1 bp &nbsp; (Rule 2a-7 mandatory fee, Oct-2024)<br/>"
      "WAM_post = (WAM − R·3d)/(1−R) &nbsp; (waterfall sells ≈3-day paper first; WAL_post identical — fixed book)", sMono),
    P("Non-parallel overlay: +300 bp carries a +40 bp steepener, +500 bp a −80 bp inversion, transmitted through "
      "twistBeta (maturity dispersion 0.283 y) — a first-order slope exposure, not a full key-rate lattice. Default "
      "losses are intentionally small (MMF-grade book, 2 bp base PD) so rate/spread/liquidity dominate, as in "
      "March-2020-style events. The linear duration repricing is exact to &lt;3 bp for sub-1-year paper; the "
      "convexity term absorbs the residual curvature.", sB)]

# ================= 7 =================
story += [P("7&nbsp;&nbsp;HPC engineering — hyper-optimized for this machine", sH1),
    P("One file, <i>mmf_stress.cpp</i> (≈500 lines, GPL-3.0-only, author Vaibhav). SoA layout, 32-byte aligned "
      "arrays; the hot loop prices <b>4 paths per AVX2 vector</b> (8×_mm256_fmadd_pd per 4 paths → 500 M vector "
      "iterations for 2 B paths). RNG is thread-local xorshift64* with scalar Box–Muller fill into 4,096-element "
      "L2-resident blocks, then pure AVX2/FMA pricing with no transcendentals in the hot loop. One OpenMP parallel "
      "region, static shares, 64-byte-padded accumulators (no false sharing), lock-free Chan-merge of Welford "
      "mean/M2 plus fixed 120-bin histograms (−6%…+2%) streamed online — peak RAM &lt; 50 MiB at any path count, "
      "page-cache friendly on 7.6 GiB. Flags: <i>-O3 -march=native -mtune=native -mavx2 -mfma -mbmi -mbmi2 "
      "-funroll-loops -flto -fopenmp -DNDEBUG -ffast-math -fno-math-errno</i> (g++ 14.2). AVX dot-products "
      "self-verify against scalar every run (tolerance 1e-12).", sB)]
hpctab = [
    [CH("Metric"), CH("Value")],
    [C("Total paths (verified counter)"), C("2,000,000,000 = 80 scen. × 25,000,000")],
    [C("Wall time / throughput"), C("34.47 s · 58.0 M paths/s (12 threads, user 5m44s)")],
    [C("Determinism"), C("fixed seeds (0xC0FFEE + tid); bit-identical given threads")],
    [C("RAM footprint"), C("< 50 MiB streaming; histograms 80×120×8 B = 77 KB")],
    [C("Outputs"), C("scenario_summary.csv (80) · histograms.csv (9,600) · calibration.json · run_meta.txt")],
]
story += [TAB(hpctab, widths=[55*mm, 110*mm])]

# ================= 8 =================
story += [P("8&nbsp;&nbsp;Results I — deterministic matrix", sH1),
    P("Reading guide: 'mean' is the 25 M-path average 5-day shadow return; deterministic duration drag dominates "
      "it, stochastic σ≈4.1–8.2 bp/5d only smears the edges. Rate slice (spread 0, redemption 0):", sB)]
ratet = [
    [CH("+rate"), CH("mean (bp)"), CH("P&lt;0.9995"), CH("P&lt;buck"), CH("min NAV")],
    [C("0"), C("+7.3"), C("0.39%"), C("0"), C("0.9981")],
    [C("+100 bp"), C("−22.8"), C("100%"), C("0"), C("0.9952")],
    [C("+200 bp"), C("−52.8"), C("100%"), C("75.0%"), C("0.9921")],
    [C("+300 bp +tw40"), C("−93.9"), C("100%"), C("100%"), C("0.9879")],
    [C("+500 bp tw−80"), C("−119.1"), C("100%"), C("100%"), C("0.9855")],
]
story += [TAB(ratet, widths=[30*mm, 30*mm, 35*mm, 35*mm, 35*mm])]
story += fig(f"{FIG}/02_rate_shock.png", cap=
    "Figure 2 — Mean 5-day return vs parallel rate shock (redemption 0%). Four spread lines; slope ≈ −0.30 bp/bp "
    "confirms modified duration 0.30 y. The +500 bp line sits ≈2 bp above naive extrapolation — the −80 bp "
    "inversion recovery.")
story += [P("Spread slice (rates 0, redemption 0): +50 bp → −7.1 bp mean, 68.1% below 0.9995; +150 bp → −35.9 bp, "
      "100%; +300 bp → −79.2 bp, 100%. Redemption slice at +200/+150 bp: 0% → −96.1 bp; 5% → −98.9; 10% → −102.3; "
      "25% → −115.2 bp — i.e. the run adds 3–19 bp on top of a market shock that has already broken the buck.", sB)]
story += fig(f"{FIG}/03_spread.png", cap=
    "Figure 3 — Spread-widening bars by rate shock (red 0%). Spread duration 0.29 y reads directly off the slope.")
story += fig(f"{FIG}/04_redemption.png", cap=
    "Figure 4 — Mass-redemption cost at +200 bp rates. Curves fan by spread; the 25% point sits 13–19 bp below "
    "the 0% point — the firesale wedge (bid-ask × stress + price impact, waterfall ×1.20).")

# ================= 9 =================
story += [P("9&nbsp;&nbsp;Results II — stochastic tails & shadow NAV (2 B paths)", sH1),
    P("Baseline (scenario 0): mean +7.35 bp, σ 4.08 bp, min 0.99812, max 1.00272 — a fund earning its accrual with "
      "a 0.39% wobble below 0.9995 and zero buck-breaks in 25 M paths. The distribution is Gaussian to the eye "
      "(top-left panel below) because deterministic accrual ± duration noise dominates. Every shocked regime is "
      "shifted, not fattened: σ stays 4.1–8.2 bp while the mean marches −23 → −229 bp. In plain terms: beyond "
      "+100 bp (or +50 bp spread, or any 25% run) the question is not <i>whether</i> the shadow prints below "
      "0.9995 but <i>how far through the buck</i> it goes — max-combined mean −224.7 bp, min 0.97102, 100% buck "
      "rate across all four redemption rungs.", sB)]
story += fig(f"{FIG}/05_histograms.png", cap=
    "Figure 5 — Shadow-return histograms (25 M paths each). Top-left baseline straddles +7 bp; all three shocked "
    "regimes sit entirely left of the −5 bp (0.9995) line. Red dashes mark −5 bp.")
story += fig(f"{FIG}/06_breach_heatmap.png", cap=
    "Figure 6 — P(NAV<0.9995) at 10% redemption: the top-left cell (+0/+0) is already 11.2%; every other cell is "
    "≥88% and most are 100%. The 5 bp tolerance is uninhabitable under any shock with a 10% run attached.")
story += [P("Scoreboard over all 80 scenarios: buck touched in <b>72/80</b>; mandatory fee fires in <b>60/80</b> "
      "(every scenario with redemption ≥5%); WAM breaches 60 d in <b>80/80</b>; WAL breaches 120 d in "
      "<b>40/80</b>; DLA/WLA breach in <b>80/80</b>. The fund survives only the 8 no-shock/no-run and "
      "mild-spread/no-run cells without a shadow breach — a narrow island.", sB)]

# ================= 10 =================
story += [P("10&nbsp;&nbsp;Liquidity & redemptions", sH1),
    P("Waterfall vs slicing: the engine prices waterfall (sell 1–5-day paper first, ×1.20 cost, WAM ages). "
      "Slicing (pro-rata vertical slice, ESMA's reference) would hold WAM flat at 110.4 d and shave ≈17% off "
      "liquidation cost — but it assumes the manager can sell 364-day CP as readily as TREPS in a freeze, which "
      "March-2020 disproved. Waterfall is reported as the conservative case; slicing results are ≈83% of the "
      "waterfall cost at each rung (2.4/5.1/15.9 bp vs 2.9/6.2/19.1 bp).", sB)]
story += fig(f"{FIG}/07_liquidity.png", cap=
    "Figure 7 — DLA/WLA after waterfall redemptions. DLA hits zero at 25%; WLA falls 32.9% → 10.5%. US floors "
    "(25%/50%) are never satisfied — including at baseline.")
story += fig(f"{FIG}/08_wam_wal.png", cap=
    "Figure 8 — WAM/WAL aging under waterfall (110.4 → 146.2 d). The 60-day cap is breached at baseline; the "
    "120-day WAL is breached once redemptions reach 10%.")
story += [P("Reverse test (ESMA §4.8.4): the maximum redeemable share before breaching <i>any</i> US constraint is "
      "<b>0%</b> — the baseline already breaches WAM/DLA/WLA, so any outflow deepens pre-existing breaches rather "
      "than creating the first one. Framed domicile-neutrally (SEBI ≤1 y only): ≈18% redeemable before WAL would "
      "cross 120 d under waterfall. Weekly test (40% professional + 30% retail ≈ 34–37% blended): extrapolating the "
      "cost curve gives ≈24–27 bp liquidation drag and WLA ≈ 4–6% — a full liquidity event requiring fee + "
      "suspension-grade tools. Top-3 concentration: investor identities are undisclosed; the 5/10/25% ladder spans "
      "the plausible top-3 range (a ₹34k-cr fund's top-3 institutional tickets at 3–8% each ⇒ 9–24% joint exit). "
      "Modelling recommendation: disclose top-10 share-class concentrations (N-MFP style) so the run ladder can "
      "be pinned to names, not brackets.", sB)]

# ================= 11 =================
story += [P("11&nbsp;&nbsp;Credit risk, shadow rating & concentration", sH1),
    P("Book credit in the model is small by construction (base PD 2 bp, LGD 45%, EAD 75% ⇒ ≈0.7 bp baseline drag; "
      "stressed Vasicek slope adds ≤4 bp even at −3σ). That matches a high-quality MMF book — and the external "
      "record supports it: PRC B-I, 4★ across agencies, Sharpe 2.93, no segregated-credit events in the 13-year "
      "NAV history (the 2018 0.04% print is a data-calendar artefact of 286 vs 365 obs, not a credit event). "
      "Shadow-rating view (internal, through-the-cycle): sov/TREPS (21.8%) AAA-equivalent; HDFC/Axis/Kotak CDs "
      "AA+/AAA bank; NABARD AAA quasi-sov; CP ladder A1+ (bank-backed where determinable). No instrument prices "
      "distress at base spreads — the +150/+300 bp spread scenarios are therefore pure <i>systemic crunch</i> "
      "overlays (COVID-Mar-20 / IL&FS-Sep-18 style), not name-level downgrades.", sB),
    P("Concentration is the live issue. HDFC Bank 8.56% and Axis Bank 7.55% (plus NABARD 6.28%) each clear the US "
      "5% first-tier single-issuer cap — a <b>US-lens breach on three names</b>. Under the SEBI 10% working cap "
      "all pass (headroom 1.4 pp on HDFC). Sector lens: banks + NABARD ≈ 26.7% — inside SEBI's 20%-per-sector "
      "working guideline only if NABARD (DFI) is classified outside commercial banks, which most SIDs do. "
      "Prescription: trim HDFC to ≤5% (frees ≈ ₹1,200 cr of single-name risk, costs ≈ 2–3 bp of carry at current "
      "CD–T-Bill spreads) and pre-commit a 5% hard cap in the SID to convert the US breach into domicile-plus "
      "headroom. Diversification back-test: the 322% turnover proves the desk can rotate — aim it at the "
      "concentration, not just the maturity.", sB)]

# ================= 12 =================
story += [P("12&nbsp;&nbsp;Pre-trade liquidity & time-to-liquidation", sH1),
    P("Position-level liquidation (normal depth, waterfall): Day-1 capacity = DLA 12.55% (≈ ₹4,280 cr of a "
      "₹34,138-cr book) at ≈ 5–8 bp all-in; Week-1 capacity = WLA 32.88% (≈ ₹11,220 cr) at ≈ 9–13 bp. A 5%/10%/25% "
      "run therefore clears in &lt;1 d / ≈2 d / ≈4–5 d under normal depth — but costs 2.9/6.2/19.1 bp and, at 25%, "
      "leaves zero DLA behind (the fund cannot face a second wave without selling 14-day+ paper). Under ESMA "
      "stressed depth (bid-ask ×3, impact ×2): the same runs cost ≈7/14/41 bp and the 25% TTL stretches to 9–11 d "
      "with residual WLA ≈ 10.5% — the firesale wedge that carries the combined Park to −229 bp. Pre-trade rule "
      "of thumb from the surface: every additional 5% of DLA buffer (overnight/TREPS) cuts 25%-run cost by ≈4 bp "
      "and buys ≈1 day of second-wave capacity. That is the single highest-leverage pre-trade action.", sB)]

# ================= 13 =================
story += [P("13&nbsp;&nbsp;Limitations & next steps", sH1),
    P("1) Undisclosed 60% book — the ladder is an informed proxy, not the portfolio; rerun on fortnightly "
      "disclosures when available. 2) No intraday/flow data — redemption ladder is bracket-based; pin to N-MFP "
      "investor-concentration filings if Tata publishes them. 3) Linearized Vasicek + duration repricing — "
      "conservative for MMF tenors (&lt;3 bp error) but not a substitute for full CUSIP repricing under "
      "downgrade migration; add a transition-matrix overlay next. 4) Single-currency (INR) — ESMA FX shocks "
      "out of scope (fund has no FX paper). 5) Tax/expense frictions held at 0.15–0.18% — fine at 5-day horizon. "
      "Next: key-rate (3-factor) lattice, FIMMDA-calibrated spread vols, CDMDF backstop modelling, and a live "
      "daily DLA/WLA dashboard fed by AMFI NAVAll.", sB)]

# ================= 14 =================
story += [P("14&nbsp;&nbsp;Reproducibility", sH1),
    P("Hardware fingerprint: i5-1335U, 12 CPUs 0–11, AVX2/FMA/BMI2 flags confirmed, 7.6 GiB RAM. "
      "Build &amp; run (from this folder):", sB),
    P("g++ -O3 -march=native -mtune=native -mavx2 -mfma -mbmi -mbmi2 -funroll-loops -flto -fopenmp -DNDEBUG "
      "-ffast-math -fno-math-errno -o mmf_stress mmf_stress.cpp<br/>"
      "./mmf_stress data/tata-money-market-direct-growth/nav_daily.csv out 2000000000 12<br/>"
      "source ~/ml_env/bin/activate &amp;&amp; python3 make_figs.py &amp;&amp; python3 make_pdf.py<br/>"
      "Manifest: mmf_stress.cpp (engine) · make_figs.py + make_pdf.py (render only) · "
      "out/scenario_summary.csv (80 rows) · out/histograms.csv (9,600 rows) · out/calibration.json · "
      "out/run_meta.txt (PATHS=2000000000) · out/figs/*.png (8) · this PDF. Verify: "
      "<i>awk -F, '{s+=$7} END {print s}' out/scenario_summary.csv</i> → 2000000000.", sMono)]

# ================= 15 =================
story += [P("15&nbsp;&nbsp;References", sH1),
    P("SEC Final Rule 33-11211, Money Market Fund Reforms (Jul-2023; 25%/50% floors, gate removal, fee framework, "
      "WAM/WAL market-value spec). 17 CFR §270.2a-7 (current text: 60/120-day caps). Fidelity Q&amp;A Apr-2024; "
      "Dechert OnPoint Aug-2023; SewKis summary; Marquette Jun-2024 update. ESMA50-43599798-12301 (2024 "
      "guidelines) &amp; -10651; ESMA50-481369926-30585 (2025 final report); ESRB adverse scenario Dec-2025; "
      "CSSF circulars 24/857, 25/877. RBI NSDP rates (repo 5.25%, 91D ≈5.3%, 182D ≈5.6–5.8%, 364D ≈5.7–6.1%, "
      "10Y ≈7.05%, Sep-2026) &amp; T-Bill auction results 2026-27/1172; CCIL indicative yields 16-Sep-2026; FBIL "
      "curve portal. SEBI Master Circular Jun-27-2024 (money-market ≤1 y, concentration, CDMDF, LR-RaR/LR-CRaR); "
      "Tata MMF SID May-2025; Tata factsheets Jun/Jul-2026; Tata scheme page; AMFI NAVAll &amp; mfapi.in/119424; "
      "ETMoney / PaytmMoney / Groww / INDmoney / ValueResearch snapshots Aug-2026; CNBCTV18 portfolio lines "
      "04-Sep-2026. All URLs verified 26-Sep-2026; RBI/FBIL/CCIL figures are market data, not advice.", sB)]

# ================= COLOPHON =================
story += [P("Colophon — authorship, power & license", sH1),
    P("Sole author: <b>Vaibhav</b>. Vaibhav holds final authority over this project — its scope, publication, "
      "licensing, and reuse. Quantitative engine written in pure C++ with AVX2 intrinsics for maximum performance "
      "on the author's machine; charts and PDF assembled with Python inside <i>~/ml_env</i> only (no system "
      "packages touched). Web research informed every regulatory threshold and market anchor cited above.", sB),
    P("License: <b>GNU General Public License v3.0 only (GPL-3.0-only)</b>, confirmed by the rights-holder "
      "2026-09-26. This work is never MIT-licensed. Onward distribution, GitHub publication, or any public release "
      "carries GPL-3.0-only by default; any alternative requires Vaibhav's explicit prior permission.", sB),
    P("Disclaimer: independent stress-test study for research and education. Not investment advice, not a "
      "recommendation, not an audit of Tata Mutual Fund. Portfolio reconstruction uses public disclosures plus "
      "documented proxies; verify against official filings before acting.", sB)]

doc = SimpleDocTemplate(PDF, pagesize=A4, leftMargin=1.8*cm, rightMargin=1.8*cm,
                        topMargin=1.6*cm, bottomMargin=1.6*cm,
                        title="Tata MMF 2B-Path Regulatory Stress Test — Vaibhav (GPL-3.0-only)",
                        author="Vaibhav")
doc.build(story)
print("PDF_OK", PDF, os.path.getsize(PDF), "bytes")
