// Deck: "Does C-A travel?" — styled after the club's PM session decks (no logo).
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");
const D = require("./data.json");

const OUT = process.argv[2] || "deck.pptx";
const W = 13.333;

const BURG = "5F021F", SUBC = "7F354C", ROSE = "B5838F", OCHRE = "C08A2E", GREY = "8C8C8C",
  INK = "1A1A1A", MUTED = "5E5E5E", TINT = "F6EEF0", CALLOUT = "FCF3D2", LINE = "D9C7CC";
const GROUP_COLOR = { "Reference": "2E2E2E", "US segments": BURG, "Developed ex-US": ROSE, "Emerging": OCHRE };

const THEME = {
  name: "Burgundy Research", headFontFace: "Garamond", bodyFontFace: "Calibri",
  colors: { dk1: INK, lt1: "FFFFFF", dk2: BURG, lt2: TINT, accent1: BURG, accent2: GREY, accent3: ROSE,
    accent4: OCHRE, accent5: SUBC, accent6: "2E2E2E", hlink: BURG, folHlink: SUBC },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Regime-Diversified Mean Reversion — other markets";

const ARCS = path.join(__dirname, "bg_arcs.png");

pres.defineSlideMaster({
  title: "TITLE",
  background: { color: "FFFFFF" },
  objects: [
    { image: { x: 0, y: 0, w: W, h: 4.1, path: path.join(__dirname, "title_header.png") } },
    { line: { x: 0.32, y: 0, w: 0, h: 6.95, line: { color: BURG, width: 2.25 } } },
    { line: { x: W - 0.32, y: 0, w: 0, h: 6.95, line: { color: BURG, width: 2.25 } } },
    { placeholder: { options: { name: "title", type: "title", x: 0.75, y: 4.4, w: 11.8, h: 1.05, fontFace: "Garamond",
      fontSize: 44, bold: true, color: BURG, align: "left", valign: "middle", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "sub", type: "body", x: 0.75, y: 5.5, w: 11.8, h: 0.9, fontSize: 16, bold: true,
      color: SUBC, charSpacing: 1.5, valign: "top", margin: 0 }, text: "" } },
  ],
});

pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: "FFFFFF" },
  objects: [
    { image: { x: 0, y: 0, w: W, h: 7.5, path: ARCS } },
    { rect: { x: 10.75, y: 7.0, w: 2.05, h: 0.07, fill: { color: BURG }, line: { color: BURG, width: 0 } } },
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.3, w: 11.6, h: 0.85, fontFace: "Garamond",
      fontSize: 38, bold: true, color: BURG, align: "left", valign: "bottom", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "sub", type: "body", x: 0.6, y: 1.17, w: 11.6, h: 0.4, fontSize: 15, bold: true,
      color: SUBC, charSpacing: 2, valign: "top", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 0.6, y: 6.95, w: 0.6, h: 0.3, fontSize: 10, color: GREY },
});

pres.defineSlideMaster({
  title: "SECTION",
  background: { color: "FFFFFF" },
  objects: [
    { image: { x: 0, y: 0, w: W, h: 7.5, path: ARCS } },
    { rect: { x: 0.75, y: 0.62, w: 2.05, h: 0.07, fill: { color: BURG }, line: { color: BURG, width: 0 } } },
    { rect: { x: 10.75, y: 6.85, w: 2.05, h: 0.07, fill: { color: BURG }, line: { color: BURG, width: 0 } } },
    { placeholder: { options: { name: "title", type: "title", x: 1.0, y: 2.55, w: 11.3, h: 1.4, fontFace: "Garamond",
      fontSize: 54, bold: false, color: BURG, align: "center", valign: "middle", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "sub", type: "body", x: 1.0, y: 4.0, w: 11.3, h: 0.6, fontSize: 16, bold: true,
      color: SUBC, charSpacing: 2, align: "center", valign: "top", margin: 0 }, text: "" } },
  ],
});

// ---------- helpers ----------
let n = 0;
function content(title, sub, section) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  s.addText(sub, { placeholder: "sub" });
  n += 1;
  return s;
}
function txt(s, text, o) {
  s.addText(text, { isTextBox: true, margin: 0, color: INK, fontSize: 16, valign: "top", ...o });
}
function bullets(s, items, o) {
  const runs = items.map((it, i) => {
    const parts = Array.isArray(it) ? it : [{ text: it }];
    return parts.map((p, j) => ({ text: p.text, options: { ...(p.options || {}),
      ...(j === 0 ? { bullet: { indent: 16 } } : {}),
      ...(j === parts.length - 1 && i < items.length - 1 ? { breakLine: true } : {}) } }));
  }).flat();
  s.addText(runs, { isTextBox: true, margin: 0, color: INK, fontSize: 16, valign: "top", paraSpaceAfter: 8, ...o });
}
function callout(s, x, y, w, h, runs, icon = "💡") {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: CALLOUT }, line: { color: CALLOUT, width: 0 },
    objectName: "callout" });
  s.addText(icon, { isTextBox: true, x: x + 0.15, y: y + 0.12, w: 0.45, h: 0.45, fontFace: "Segoe UI Emoji", fontSize: 18,
    margin: 0, valign: "top" });
  s.addText(runs, { isTextBox: true, x: x + 0.65, y: y + 0.12, w: w - 0.85, h: h - 0.24, margin: 0, fontSize: 15,
    color: INK, valign: "middle" });
}
function stat(s, x, y, w, big, label, color = BURG) {
  s.addText(big, { isTextBox: true, x, y, w, h: 0.75, fontFace: "Garamond", fontSize: 40, bold: true, color, margin: 0,
    valign: "bottom" });
  s.addText(label, { isTextBox: true, x, y: y + 0.78, w, h: 0.62, fontSize: 14, color: MUTED, margin: 0, valign: "top" });
}
function source(s, text) {
  s.addText(text, { isTextBox: true, x: 1.3, y: 6.9, w: 9.2, h: 0.35, fontSize: 10, color: GREY, margin: 0,
    valign: "middle" });
}
const CHART_BASE = () => ({
  catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontSize: 11, valAxisLabelFontSize: 11,
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt", legendFontSize: 12,
  dataLabelFontFace: "+mn-lt", dataLabelFontSize: 10, dataLabelColor: MUTED,
  valGridLine: { color: "E6E0E2", size: 0.75 }, catGridLine: { style: "none" },
  catAxisLineShow: false, valAxisLineShow: false,
});
const fmt = (x, d = 2) => (x >= 0 ? "+" : "−") + Math.abs(x).toFixed(d);
const rows = D.rows;
const rank = { "Reference": 0, "US segments": 1, "Developed ex-US": 2, "Emerging": 3 };
const ordered = (key) => [...rows].sort((a, b) => rank[a.group] - rank[b.group] || b[key] - a[key]);
const label = (r) => `${r.ticker}  ${r.name}`;
const tableHead = (cells) => cells.map((c) => ({ text: c, options: { bold: true, color: "FFFFFF", fill: { color: BURG },
  fontSize: 13, valign: "middle" } }));

// ---------- 1 title ----------
pres.addSection({ title: "Introduction" });
{
  const s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Introduction" });
  s.addText("Regime-Diversified Mean Reversion", { placeholder: "title" });
  s.addText([
    { text: "DOES THE STRATEGY TRAVEL? C-A ON 19 OTHER EQUITY MARKETS", options: { breakLine: true } },
    { text: "Public Markets Research · November 2026", options: { bold: false, color: MUTED, charSpacing: 0, fontSize: 14 } },
  ], { placeholder: "sub" });
  s.addNotes("Title. One frozen strategy (C-A), replicated on US segments, developed markets outside the US and emerging markets.");
}

// ---------- 2 disclaimer ----------
{
  const s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Introduction" });
  s.addText("These slides are for educational purposes only. All results are backtests on historical data from 2007 to 2026 and are in-sample in time. They do not constitute financial, legal or investment advice, and no guarantee is made regarding their accuracy or completeness. Past performance does not predict future returns.",
    { isTextBox: true, x: 2.0, y: 2.3, w: 9.33, h: 2.6, fontFace: "Garamond", fontSize: 20, color: INK, align: "center",
      valign: "middle", margin: 0 });
  s.addNotes("Disclaimer.");
}

// ---------- 3 agenda ----------
{
  const s = content("Overview of Today's Session", "AGENDA", "Introduction");
  const items = ["Recap: the C-A strategy on the S&P 500", "Why the two mechanisms should work elsewhere",
    "Research design and four registered hypotheses", "Results: headline, dip overlay, rebalancing, costs",
    "Verdict and honest caveats", "Q&A"];
  items.forEach((t, i) => {
    const y = 1.95 + i * 0.75;
    s.addShape(pres.shapes.OVAL, { x: 0.65, y, w: 0.5, h: 0.5, fill: { color: i === 3 ? BURG : "FFFFFF" },
      line: { color: BURG, width: 1.5 }, objectName: `agenda-dot-${i + 1}` });
    s.addText(String(i + 1), { isTextBox: true, x: 0.65, y, w: 0.5, h: 0.5, align: "center", valign: "middle", margin: 0,
      fontFace: "Garamond", fontSize: 18, bold: true, color: i === 3 ? "FFFFFF" : BURG });
    txt(s, t, { x: 1.4, y, w: 6.2, h: 0.5, valign: "middle", fontSize: 18 });
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 8.3, y: 1.95, w: 4.4, h: 4.25, fill: { color: TINT }, line: { color: TINT, width: 0 },
    objectName: "scope-card" });
  [["19", "equity markets besides the S&P 500"], ["3", "regions: US segments, developed ex-US, emerging"],
    ["20 yrs", "of daily data, 2007-02 to 2026-11"]].forEach(([b, l], i) => stat(s, 8.65, 2.1 + i * 1.35, 3.8, b, l));
  s.addNotes("Agenda. The results section is the core of the talk.");
}

// ---------- 4 strategy recap ----------
pres.addSection({ title: "Strategy and design" });
{
  const s = content("The Strategy: C-A", "RECAP OF THE FROZEN RULES", "Strategy and design");
  const card = (x, head, sub, items) => {
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.9, w: 5.55, h: 3.2, fill: { color: TINT }, line: { color: TINT, width: 0 },
      objectName: `card-${head}` });
    txt(s, head, { x: x + 0.3, y: 2.05, w: 5.0, h: 0.5, fontFace: "Garamond", fontSize: 24, bold: true, color: BURG });
    txt(s, sub, { x: x + 0.3, y: 2.55, w: 5.0, h: 0.35, fontSize: 13, bold: true, color: SUBC, charSpacing: 1.5 });
    bullets(s, items, { x: x + 0.3, y: 3.05, w: 4.95, h: 1.95, fontSize: 15 });
  };
  card(0.6, "Book 1 · Index Dip Overlay", "50 % OF CAPITAL", [
    "Hold the index at exposure 1.0",
    [{ text: "Dip: ", options: { bold: true } }, { text: "RSI(2) < 10 and close > SMA200 → exposure 2.0 until close > SMA5" }],
    [{ text: "Overbought: ", options: { bold: true } }, { text: "RSI(2) > 90 and close < SMA200 → exposure 0.5 until close < SMA5" }],
  ]);
  card(7.15, "Book 2 · Rebalancing Premium", "50 % OF CAPITAL", [
    "Index, long Treasuries (TLT) and gold (GLD) in equal thirds",
    "Reset to 1/3 each at every month end",
    "Weights drift with prices in between",
  ]);
  s.addShape(pres.shapes.OVAL, { x: 6.07, y: 2.9, w: 1.2, h: 1.2, fill: { color: BURG }, line: { color: "FFFFFF", width: 3 },
    objectName: "split-badge" });
  s.addText("50/50", { isTextBox: true, x: 6.07, y: 2.9, w: 1.2, h: 1.2, align: "center", valign: "middle", margin: 0,
    fontFace: "Garamond", fontSize: 20, bold: true, color: "FFFFFF" });
  txt(s, [{ text: "On SPY, 2007–2026: ", options: { bold: true } },
    { text: "Sharpe 0.78 vs 0.53 for buy & hold. Holdout 2023-11 to 2026-11: 1.42 vs 1.09, paired p = 0.165." }],
  { x: 0.6, y: 5.45, w: 12.1, h: 0.4, fontSize: 16 });
  txt(s, "Decision at the close of day t, held on day t+1 · 1 bp per side · Sharpe on excess returns over the 3-month T-bill",
    { x: 0.6, y: 5.95, w: 12.1, h: 0.35, fontSize: 14, color: MUTED });
  s.addNotes("Nothing about these rules changes in this study. Only the equity asset is swapped.");
}

// ---------- 5 theory ----------
{
  const s = content("Why It Should Travel", "ECONOMIC THEORY", "Strategy and design");
  const col = (x, head, body, formula) => {
    txt(s, head, { x, y: 1.95, w: 5.6, h: 0.45, fontSize: 18, bold: true });
    txt(s, body, { x, y: 2.45, w: 5.6, h: 1.6, fontSize: 16 });
    if (formula) txt(s, formula, { x, y: 4.0, w: 5.6, h: 0.6, fontFace: "Cambria Math", fontSize: 22, color: BURG });
  };
  col(0.6, "Book 1: liquidity provision",
    "Forced or hurried selling pushes the index below fair value. Whoever buys the dip is paid for providing liquidity when the reversal comes. This should happen in any market where investors sometimes sell in a hurry.");
  col(6.95, "Book 2: diversification return",
    "Rebalancing sells relative winners and buys relative losers. The gain is mechanical and grows with the volatility of the assets:",
    "DR ≈ ½ (Σ wᵢσᵢ² − σₚ²)");
  s.addShape(pres.shapes.LINE, { x: 6.67, y: 2.0, w: 0, h: 2.6, line: { color: LINE, width: 1.25 } });
  callout(s, 0.6, 4.95, 12.1, 1.15, [
    { text: "Registered prediction: ", options: { bold: true } },
    { text: "the dip overlay should be weaker in emerging markets, because their indices show more short-horizon momentum and USD-listed ETFs mix currency moves into their dips." }]);
  source(s, "Lehmann (1990); Nagel (2012); Booth & Fama (1992); Erb & Harvey (2006)");
  s.addNotes("The two books rest on different premia. If C-A is more than a US artefact, both should show up abroad.");
}

// ---------- 6 design ----------
{
  const s = content("Research Design", "ONE CHANGE, EVERYTHING ELSE FROZEN", "Strategy and design");
  bullets(s, [
    [{ text: "Only the equity asset changes, ", options: { bold: true } }, { text: "in book 1 and in book 2" }],
    "TLT, GLD, every threshold, costs and cash accounting stay as they are",
    "US-dollar investor, US-listed ETFs, 4,970 trading days",
    "Hypotheses committed to git before the first number was computed",
    "Pooled tests use the effective number of independent markets, n_eff",
  ], { x: 0.6, y: 1.95, w: 4.2, h: 4.6, fontSize: 16, paraSpaceAfter: 12 });
  const groups = [["US SEGMENTS", "US segments"], ["DEVELOPED EX-US", "Developed ex-US"], ["EMERGING", "Emerging"]];
  groups.forEach(([head, g], i) => {
    const x = 5.2 + i * 2.55;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.95, w: 2.35, h: 3.15, fill: { color: TINT }, line: { color: TINT, width: 0 },
      objectName: `universe-${g}` });
    txt(s, head, { x: x + 0.2, y: 2.1, w: 2.0, h: 0.35, fontSize: 12, bold: true, color: GROUP_COLOR[g] === ROSE ? SUBC : GROUP_COLOR[g] === OCHRE ? "8A6100" : BURG, charSpacing: 1.5 });
    const rs = rows.filter((r) => r.group === g);
    s.addText(rs.map((r, k) => [{ text: r.ticker, options: { bold: true, color: INK } },
      { text: "  " + r.name, options: { color: MUTED, breakLine: k < rs.length - 1 } }]).flat(),
    { isTextBox: true, x: x + 0.2, y: 2.55, w: 2.05, h: 2.45, fontSize: 14, margin: 0, valign: "top", paraSpaceAfter: 9 });
  });
  callout(s, 5.2, 5.35, 7.45, 1.2, [{ text: "Same window everywhere: ", options: { bold: true } },
    { text: "all 20 series share the same 4,970 trading days without gaps. India is excluded because no ETF covers the full window." }]);
  s.addNotes("India is excluded because no ETF covers the full window.");
}

// ---------- 7 hypotheses ----------
{
  const s = content("Four Registered Hypotheses", "SUCCESS CONDITIONS FIXED IN ADVANCE", "Strategy and design");
  const H = [
    ["M1", "C-A beats buy & hold of the local market", "Treasuries and gold diversify any equity market", "≥ 15 of 19 markets and pooled p < 0.10"],
    ["M2", "The dip overlay (book 1) beats buy & hold", "Liquidity-provision premium exists everywhere", "≥ 13 of 19 and pooled p < 0.10, in both 2007–15 and 2016–26"],
    ["M3", "Monthly rebalancing beats never rebalancing", "Diversification return is mechanical", "≥ 13 of 19 and rank correlation with volatility > 0"],
    ["M4", "The result survives realistic costs", "Turnover is only ~10× per year", "At 5 bp per side, at most 2 markets fewer than at 1 bp"],
  ];
  const body = H.map((r) => r.map((c, j) => ({ text: c, options: { fontSize: 14, bold: j === 0, color: j === 0 ? BURG : INK,
    valign: "middle" } })));
  s.addTable([tableHead(["", "Hypothesis", "Economic cause", "Success condition"]), ...body], {
    x: 0.6, y: 1.95, w: 12.1, colW: [0.7, 3.9, 3.6, 3.9], rowH: [0.45, 0.75, 0.75, 0.75, 0.75],
    border: { type: "solid", pt: 0.75, color: LINE }, margin: [4, 8, 4, 8] });
  callout(s, 0.6, 5.65, 12.1, 0.85, [{ text: "“C-A generalises” = M1 and M2. ", options: { bold: true } },
    { text: "M1 alone would only say that bonds and gold diversify equities, which is not news." }], "🔑");
  s.addNotes("M2 is the strategy-specific test.");
}

// ---------- 8 section ----------
pres.addSection({ title: "Results" });
{
  const s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Results" });
  s.addText("Results", { placeholder: "title" });
  s.addText("19 MARKETS · 2007-02 TO 2026-11", { placeholder: "sub" });
}

// ---------- 9 headline chart ----------
{
  const s = content("C-A vs Buy & Hold", "SHARPE RATIO 2007–2026, EXCESS OVER T-BILL, USD", "Results");
  const o = ordered("ca_sharpe");
  s.addChart(pres.charts.BAR, [
    { name: "Buy & hold", labels: o.map(label), values: o.map((r) => r.market_sharpe) },
    { name: "C-A", labels: o.map(label), values: o.map((r) => r.ca_sharpe) },
  ], { x: 0.45, y: 1.7, w: 8.3, h: 5.15, barDir: "bar", barGapWidthPct: 45, chartColors: [GREY, BURG],
    catAxisOrientation: "maxMin", valAxisMinVal: 0, valAxisMaxVal: 0.9, valAxisMajorUnit: 0.2, valAxisLabelFormatCode: "0.0",
    showLegend: true, legendPos: "b", catAxisLabelFontSize: 10, ...CHART_BASE(), objectName: "chart-headline" });
  stat(s, 9.2, 1.9, 3.6, "19 / 19", "markets: C-A has the higher Sharpe");
  stat(s, 9.2, 3.35, 3.6, "p = 0.011", "pooled across markets");
  stat(s, 9.2, 4.8, 3.6, "n_eff = 1.3", "differences are 73 % correlated: one common cause");
  s.addNotes("C-A beats buy & hold everywhere. But the 19 wins share one cause, the bond and gold half, so they count as about 1.3 independent markets.");
}

// ---------- 10 group table ----------
{
  const s = content("The Same Pattern in Every Region", "AVERAGES BY GROUP", "Results");
  const G = [["Reference (SPY)", "0.78", "0.53", "+0.15", "−32 %", "−55 %", "38 bp"],
    ["US segments (5)", "0.70", "0.51", "+0.09", "−34 %", "−55 %", "32 bp"],
    ["Developed ex-US (7)", "0.42", "0.25", "+0.09", "−41 %", "−62 %", "33 bp"],
    ["Emerging (7)", "0.42", "0.27", "+0.10", "−50 %", "−69 %", "37 bp"]];
  const body = G.map((r) => r.map((c, j) => ({ text: c, options: { fontSize: 15, align: j === 0 ? "left" : "center",
    bold: j === 0 || j === 1, color: j === 1 ? BURG : INK, valign: "middle" } })));
  s.addTable([tableHead(["Group", "C-A Sharpe", "Buy & hold", "Book 1 − B&H", "C-A max DD", "B&H max DD", "Break-even"])
    .map((c, j) => ({ ...c, options: { ...c.options, align: j === 0 ? "left" : "center" } })), ...body], {
    x: 0.6, y: 1.95, w: 12.1, colW: [2.8, 1.55, 1.55, 1.6, 1.55, 1.55, 1.5], rowH: 0.55,
    border: { type: "solid", pt: 0.75, color: LINE }, margin: [4, 8, 4, 8] });
  stat(s, 0.6, 4.95, 3.7, "~20 pp", "smaller maximum drawdown than buy & hold, in every group");
  stat(s, 4.75, 4.95, 3.7, "18 / 19", "markets with a higher CAGR too (exception: QQQ, 15.3 % vs 15.6 %)");
  stat(s, 8.9, 4.95, 3.8, "0.42 vs 0.78", "C-A abroad stays far below C-A on SPY: the market's own Sharpe matters most");
  s.addNotes("Group values are simple averages. The level of the local equity Sharpe dominates; the strategy adds a similar amount everywhere.");
}

// ---------- 11 overlay ----------
{
  const s = content("The Dip Overlay", "BOOK 1 MINUS BUY & HOLD, SHARPE 2007–2026", "Results");
  const o = ordered("overlay_diff");
  const gs = ["Reference", "US segments", "Developed ex-US", "Emerging"];
  s.addChart(pres.charts.BAR, gs.map((g) => ({ name: g, labels: o.map(label),
    values: o.map((r) => (r.group === g ? r.overlay_diff : 0)) })), {
    x: 0.45, y: 1.7, w: 8.3, h: 5.15, barDir: "bar", barGrouping: "stacked", barGapWidthPct: 40,
    chartColors: gs.map((g) => GROUP_COLOR[g]), catAxisOrientation: "maxMin", valAxisMinVal: 0, valAxisMaxVal: 0.2,
    valAxisMajorUnit: 0.05, valAxisLabelFormatCode: "+0.00;-0.00;0", showLegend: true, legendPos: "b",
    catAxisLabelFontSize: 10, ...CHART_BASE(), objectName: "chart-overlay" });
  stat(s, 9.2, 1.9, 3.6, "19 / 19", "markets: the overlay adds Sharpe");
  stat(s, 9.2, 3.35, 3.6, "2 of 19", "significant on their own (OEF, EEM)");
  stat(s, 9.2, 4.8, 3.6, "p = 0.024", "pooled, n_eff = 2.6 (differences only 35 % correlated)");
  s.addNotes("The overlay is the strategy-specific part. It is positive everywhere and explains 14 to 62 percent of C-A's edge; book 2 explains the rest.");
}

// ---------- 12 overlay faded ----------
{
  const s = content("The Overlay Faded After 2016", "AVERAGE SHARPE GAIN OF BOOK 1 OVER BUY & HOLD", "Results");
  const cats = ["US segments", "Developed ex-US", "Emerging", "All 19"];
  s.addChart(pres.charts.BAR, [
    { name: "2007–2015", labels: cats, values: cats.map((c) => D.period_avg[c]["2007_2015"]) },
    { name: "2016–2026", labels: cats, values: cats.map((c) => D.period_avg[c]["2016_2026"]) },
  ], { x: 0.45, y: 1.75, w: 7.2, h: 4.9, barDir: "col", barGapWidthPct: 60, chartColors: [BURG, ROSE],
    valAxisMinVal: 0, valAxisMaxVal: 0.16, valAxisMajorUnit: 0.04, valAxisLabelFormatCode: "+0.00;-0.00;0",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "+0.00", showLegend: true, legendPos: "b",
    catAxisLabelFontSize: 12, ...CHART_BASE(), objectName: "chart-periods" });
  const P = D.pooled;
  const rowsP = [["2007–2015", `${P["2007_2015"].book1_vs_market.wins} / 19`, P["2007_2015"].book1_vs_market.p_value.toFixed(3)],
    ["2016–2026", `${P["2016_2026"].book1_vs_market.wins} / 19`, P["2016_2026"].book1_vs_market.p_value.toFixed(2)]];
  s.addTable([tableHead(["Period", "Positive", "Pooled p"]),
    ...rowsP.map((r, i) => r.map((c, j) => ({ text: c, options: { fontSize: 15, align: j ? "center" : "left",
      bold: i === 1 && j === 2, color: i === 1 && j === 2 ? BURG : INK } })))], {
    x: 8.1, y: 1.95, w: 4.6, colW: [1.7, 1.45, 1.45], rowH: 0.5, border: { type: "solid", pt: 0.75, color: LINE },
    margin: [4, 8, 4, 8] });
  txt(s, [{ text: "M2 fails: ", options: { bold: true, color: BURG } },
    { text: "it needs pooled p < 0.10 in both halves. After 2016 the gain halves and is no longer distinguishable from noise." }],
  { x: 8.1, y: 3.7, w: 4.6, h: 1.3, fontSize: 15 });
  callout(s, 8.1, 5.25, 4.6, 1.35, [{ text: "Same decay as on SPY: ", options: { bold: true } },
    { text: "index reversal was stronger before 2016." }]);
  s.addNotes("Emerging markets show the biggest drop: from +0.15 to +0.04.");
}

// ---------- 13 EM prediction ----------
{
  const s = content("Our Emerging-Market Prediction Was Wrong", "PREDICTION VS OUTCOME", "Results");
  const box = (x, head, big, body, fill, col) => {
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.95, w: 5.85, h: 2.75, fill: { color: fill }, line: { color: fill, width: 0 },
      objectName: `box-${head}` });
    txt(s, head, { x: x + 0.35, y: 2.1, w: 5.2, h: 0.4, fontSize: 13, bold: true, color: col, charSpacing: 1.5 });
    txt(s, big, { x: x + 0.35, y: 2.55, w: 5.2, h: 0.9, fontFace: "Garamond", fontSize: 34, bold: true, color: col });
    txt(s, body, { x: x + 0.35, y: 3.5, w: 5.2, h: 1.1, fontSize: 15, color: col === "FFFFFF" ? "FFFFFF" : INK });
  };
  box(0.6, "REGISTERED", "Weaker in EM", "More short-horizon momentum in EM indices and currency noise in USD-listed ETFs should work against reversal.", TINT, BURG);
  box(6.85, "OBSERVED", "EEM strongest of all", "+0.18 Sharpe from the overlay, p = 0.003. The emerging group has the strongest pooled evidence (p = 0.02).", BURG, "FFFFFF");
  txt(s, "A possible explanation (untested)", { x: 0.6, y: 5.0, w: 12, h: 0.4, fontSize: 18, bold: true });
  bullets(s, [
    "A US-listed EM ETF trades while its local markets are closed, so US-hours selling can push it below the value of its holdings",
    "That gap closes the next day: an ETF-microstructure effect, not the index reversal C-A is built on. Testing it needs NAV or local-index data",
  ], { x: 0.6, y: 5.45, w: 12.1, h: 1.3, fontSize: 15, paraSpaceAfter: 6 });
  s.addNotes("We report the failed prediction instead of hiding it. The explanation is a hypothesis for a new registered study.");
}

// ---------- 14 rebalancing ----------
{
  const s = content("Rebalancing Scales with Volatility", "BOOK 2 MINUS NEVER-REBALANCED, RETURN % P.A.", "Results");
  const o = [...rows].sort((a, b) => a.market_vol - b.market_vol);
  const gs = ["Reference", "US segments", "Developed ex-US", "Emerging"];
  const data = [{ name: "Volatility", values: o.map((r) => +(r.market_vol * 100).toFixed(2)) },
    ...gs.map((g) => ({ name: g, values: o.map((r) => (r.group === g ? +(r.rebal_return_diff * 100).toFixed(3) : null)) }))];
  s.addChart(pres.charts.SCATTER, data, { x: 0.45, y: 1.7, w: 7.6, h: 5.1, chartColors: gs.map((g) => GROUP_COLOR[g]),
    lineSize: 0, lineDataSymbol: "circle", lineDataSymbolSize: 10, valAxisMinVal: -1.5, valAxisMaxVal: 1.0,
    valAxisMajorUnit: 0.5, valAxisLabelFormatCode: "+0.0;-0.0;0", catAxisMinVal: 15, catAxisMaxVal: 40,
    catAxisMajorUnit: 5, catAxisCrossesAt: 15, valAxisCrossesAt: -1.5, showValAxisTitle: true, valAxisTitle: "Book 2 minus drift, % p.a.", valAxisTitleFontSize: 11,
    valAxisTitleColor: MUTED, showCatAxisTitle: true, catAxisTitle: "Equity volatility, % p.a.", catAxisTitleFontSize: 11,
    catAxisTitleColor: MUTED, showLegend: true, legendPos: "b", ...CHART_BASE(), objectName: "chart-rebal" });
  stat(s, 8.5, 1.9, 4.2, "19 / 19", "markets: higher Sharpe with monthly rebalancing");
  stat(s, 8.5, 3.3, 4.2, "ρ = +0.74", "rank correlation with equity volatility, as theory predicts");
  bullets(s, [
    [{ text: "Korea, Brazil, South Africa: ", options: { bold: true } }, { text: "+0.5 to +0.7 % p.a." }],
    [{ text: "QQQ (bottom): ", options: { bold: true } }, { text: "−1.3 % p.a., the Nasdaq rally rewarded letting it run" }],
    [{ text: "2016–2026: ", options: { bold: true } }, { text: "only 8 of 19, letting gold run paid" }],
  ], { x: 8.5, y: 4.75, w: 4.2, h: 1.95, fontSize: 14, paraSpaceAfter: 6 });
  s.addNotes("M3 passes. The rebalancing premium behaves exactly like the diversification-return formula says.");
}

// ---------- 15 equity curves ----------
{
  const s = content("Growth of 1 USD", "C-A VS BUY & HOLD, LOG SCALE", "Results");
  const names = { IWM: "Russell 2000 (IWM)", EFA: "MSCI EAFE (EFA)", EEM: "MSCI Emerging (EEM)" };
  ["IWM", "EFA", "EEM"].forEach((t, i) => {
    const c = D.curves[t];
    const x = 0.5 + i * 4.15;
    txt(s, names[t], { x: x + 0.15, y: 1.85, w: 3.8, h: 0.4, fontSize: 16, bold: true });
    s.addChart(pres.charts.LINE, [
      { name: "Buy & hold", labels: c.dates.map((d) => d.slice(0, 4)), values: c.market },
      { name: "C-A", labels: c.dates.map((d) => d.slice(0, 4)), values: c.strategy },
    ], { x, y: 2.3, w: 4.0, h: 4.4, chartColors: [GREY, BURG], lineSize: 1.75, lineDataSymbol: "none",
      valAxisLogScaleBase: 2, valAxisMinVal: 0.5, valAxisMaxVal: 8, valAxisLabelFormatCode: "General",
      catAxisLabelFrequency: 48, catAxisLabelPos: "low", showLegend: false, ...CHART_BASE(),
      objectName: `chart-equity-${t}` });
  });
  s.addText([{ text: "━  C-A", options: { color: BURG, bold: true } }, { text: "      ━  Buy & hold", options: { color: GREY, bold: true } }],
    { isTextBox: true, x: 8.7, y: 1.17, w: 4.0, h: 0.4, fontSize: 14, align: "right", margin: 0, valign: "top" });
  s.addNotes("Total-return growth including T-bill interest on cash.");
}

// ---------- 16 book 2 alone ----------
{
  const s = content("But: Book 2 Alone Was Often Better", "C-A MINUS BOOK 2 ALONE, SHARPE · NOT REGISTERED", "Results");
  const o = [...rows].sort((a, b) => b.ca_minus_book2 - a.ca_minus_book2);
  s.addChart(pres.charts.BAR, [
    { name: "C-A ahead", labels: o.map(label), values: o.map((r) => (r.ca_minus_book2 > 0 ? r.ca_minus_book2 : 0)) },
    { name: "Book 2 alone ahead", labels: o.map(label), values: o.map((r) => (r.ca_minus_book2 <= 0 ? r.ca_minus_book2 : 0)) },
  ], { x: 0.45, y: 1.7, w: 7.6, h: 5.15, barDir: "bar", barGrouping: "stacked", barGapWidthPct: 40,
    chartColors: [BURG, ROSE], catAxisOrientation: "maxMin", valAxisMinVal: -0.1, valAxisMaxVal: 0.1,
    valAxisMajorUnit: 0.05, valAxisLabelFormatCode: "+0.00;-0.00;0", catAxisLabelPos: "low", showLegend: true,
    legendPos: "b", catAxisLabelFontSize: 10, ...CHART_BASE(), objectName: "chart-book2" });
  stat(s, 8.5, 1.9, 4.2, "15 / 19", "markets where book 2 alone has the higher Sharpe");
  stat(s, 8.5, 3.3, 4.2, "p = 0.77", "pooled: none of the differences is significant");
  callout(s, 8.5, 4.85, 4.2, 1.8, [{ text: "No contradiction: ", options: { bold: true } },
    { text: "the overlay improves an equity position everywhere, but where equities had a low Sharpe, less equity was better." }]);
  s.addNotes("This check was added after seeing the registered results, because an earlier eight-country run had found the same. It answers whether the 50 % equity book belongs there at all.");
}

// ---------- 17 costs ----------
{
  const s = content("Costs Are Not the Problem", "BREAK-EVEN COST PER SIDE VS BUY & HOLD, BASIS POINTS", "Results");
  const o = ordered("break_even_bp");
  s.addChart(pres.charts.BAR, [{ name: "Break-even", labels: o.map(label), values: o.map((r) => r.break_even_bp) }], {
    x: 0.45, y: 1.7, w: 8.3, h: 5.15, barDir: "bar", barGapWidthPct: 40, chartColors: [BURG], catAxisOrientation: "maxMin",
    valAxisMinVal: 0, valAxisMaxVal: 55, valAxisMajorUnit: 10, valAxisLabelFormatCode: "0", showValue: true,
    dataLabelPosition: "outEnd", dataLabelFormatCode: "0", showLegend: false, catAxisLabelFontSize: 10, ...CHART_BASE(),
    objectName: "chart-costs" });
  stat(s, 9.2, 1.9, 3.6, "22–48 bp", "per side before the edge over buy & hold disappears");
  stat(s, 9.2, 3.35, 3.6, "1–5 bp", "realistic cost of trading these ETFs");
  stat(s, 9.2, 4.8, 3.6, "19 / 19", "markets still ahead at 5 bp per side (M4 passes)");
  s.addNotes("Turnover is about ten times per year, so even wide emerging-market spreads do not matter.");
}

// ---------- 18 verdict ----------
pres.addSection({ title: "Verdict" });
{
  const s = content("Verdict", "THE FOUR REGISTERED TESTS", "Verdict");
  const V = [["M1", "C-A beats buy & hold", "19 / 19, pooled p = 0.011", true],
    ["M2", "Dip overlay beats buy & hold, both halves", "2007–15: p = 0.043 · 2016–26: p = 0.27", false],
    ["M3", "Rebalancing beats never rebalancing", "19 / 19, ρ(volatility) = +0.74", true],
    ["M4", "Survives 5 bp per side", "19 / 19, break-even 22–48 bp", true]];
  V.forEach(([id, h, r, ok], i) => {
    const y = 1.95 + i * 0.85;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y, w: 12.1, h: 0.7, fill: { color: i % 2 ? "FFFFFF" : TINT },
      line: { color: TINT, width: 0 }, objectName: `verdict-row-${id}` });
    txt(s, id, { x: 0.8, y, w: 0.7, h: 0.7, valign: "middle", fontFace: "Garamond", fontSize: 24, bold: true, color: BURG });
    txt(s, h, { x: 1.6, y, w: 5.0, h: 0.7, valign: "middle", fontSize: 16, bold: true });
    txt(s, r, { x: 6.6, y, w: 4.2, h: 0.7, valign: "middle", fontSize: 15, color: MUTED });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 11.0, y: y + 0.14, w: 1.5, h: 0.42, rectRadius: 0.08,
      fill: { color: ok ? BURG : "FFFFFF" }, line: { color: ok ? BURG : OCHRE, width: 1.5 }, objectName: `badge-${id}` });
    s.addText(ok ? "PASSED" : "FAILED", { isTextBox: true, x: 11.0, y: y + 0.14, w: 1.5, h: 0.42, align: "center",
      valign: "middle", margin: 0, fontSize: 13, bold: true, charSpacing: 1.5, color: ok ? "FFFFFF" : "8A6100" });
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 5.5, w: 12.1, h: 1.05, fill: { color: BURG }, line: { color: BURG, width: 0 },
    objectName: "verdict-banner" });
  s.addText([{ text: "“C-A generalises” (M1 and M2): not met. ", options: { bold: true } },
    { text: "The rebalancing book travels; the dip overlay travels in sign, but not in strength." }],
  { isTextBox: true, x: 0.9, y: 5.5, w: 11.5, h: 1.05, valign: "middle", margin: 0, fontSize: 17, color: "FFFFFF" });
  s.addNotes("Three of four registered tests pass, but the one that tests the strategy-specific idea fails after 2016.");
}

// ---------- 19 caveats ----------
{
  const s = content("Honest Caveats", "WHAT THIS STUDY DOES NOT SHOW", "Verdict");
  const C4 = [
    ["In-sample in time", "Every day from 2007 to 2026 has been looked at. The markets are out-of-sample only in the cross-section."],
    ["Correlated witnesses", "The 19 headline wins count as 1.3 independent markets. They share one cause: the Treasury and gold half."],
    ["A prior partial run", "Six of the 19 markets overlap an earlier eight-country check. The registration missed it; an erratum is in the repository."],
    ["Survivorship and USD lens", "Only ETFs that exist today. Returns include currency moves. Yahoo revises adjusted prices slightly over time."],
  ];
  C4.forEach(([h, b], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.95 + Math.floor(i / 2) * 2.4;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 5.95, h: 2.15, fill: { color: TINT }, line: { color: TINT, width: 0 },
      objectName: `caveat-${i + 1}` });
    txt(s, h, { x: x + 0.3, y: y + 0.2, w: 5.35, h: 0.5, fontFace: "Garamond", fontSize: 24, bold: true, color: BURG });
    txt(s, b, { x: x + 0.3, y: y + 0.8, w: 5.35, h: 1.2, fontSize: 15 });
  });
  s.addNotes("These limits apply to every number in the deck.");
}

// ---------- 20 takeaways ----------
{
  const s = content("Takeaways", "WHAT FOLLOWS FROM THE STUDY", "Verdict");
  const T = [
    ["Rebalancing travels", "Its premium shows up in every market and grows with volatility. This half of C-A does not depend on the US."],
    ["The dip overlay travels in sign, not in strength", "Positive in all 19 markets, but the evidence sits before 2016. It is no reason to trade C-A abroad instead of on SPY."],
    ["C-A on SPY stays the strategy", "Nothing here changed its rules. Next: the forward test, and a newly registered study of the EEM gain with NAV data."],
  ];
  T.forEach(([h, b], i) => {
    const y = 1.95 + i * 1.5;
    s.addShape(pres.shapes.OVAL, { x: 0.6, y: y + 0.05, w: 0.75, h: 0.75, fill: { color: BURG }, line: { color: BURG, width: 0 },
      objectName: `takeaway-dot-${i + 1}` });
    s.addText(String(i + 1), { isTextBox: true, x: 0.6, y: y + 0.05, w: 0.75, h: 0.75, align: "center", valign: "middle",
      margin: 0, fontFace: "Garamond", fontSize: 24, bold: true, color: "FFFFFF" });
    txt(s, h, { x: 1.65, y, w: 11, h: 0.45, fontSize: 19, bold: true, color: BURG });
    txt(s, b, { x: 1.65, y: y + 0.5, w: 11, h: 0.8, fontSize: 16 });
  });
  source(s, "Code, data and the registration: github.com/RobinHumberg/regime-diversified-mean-reversion");
  s.addNotes("Close on the three takeaways, then open for questions.");
}

// ---------- 21 Q&A ----------
{
  const s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Verdict" });
  s.addText("Q&A", { isTextBox: true, x: 2.0, y: 2.4, w: 9.33, h: 2.2, fontFace: "Garamond", fontSize: 110, bold: true, color: BURG, align: "center", valign: "middle", margin: 0 });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT, n, "content slides");
})();
