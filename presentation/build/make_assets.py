"""Data bundle and decorative images for the deck.

Run from the repo root after run_markets.py:
    python presentation/build/make_assets.py presentation/build
    cd presentation/build && npm install pptxgenjs@3.12.0
    PPTX_SKILL=<path to the pptx skill> node build.js ../regime_mr_other_markets.pptx
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from strategy.data import daily_cash  # noqa: E402
from strategy.markets import MARKETS, build_market  # noqa: E402

OUT = Path(sys.argv[1])
END = "2026-11-06"
rows = pd.read_csv("results/markets.csv", index_col=0)
js = json.loads(Path("results/markets.json").read_text(encoding="utf-8"))

curves = {}
for t in MARKETS:
    s = build_market(t, END)
    cash = daily_cash(s["strategy"].index)
    eq = {k: (1 + s[k] + cash).cumprod() for k in ["strategy", "market"]}
    curves[t] = {k: v.resample("ME").last() for k, v in eq.items()}

groups = ["US segments", "Developed ex-US", "Emerging"]
w = rows[rows.group != "Reference"]
period_avg = {g: {"2007_2015": round(float(w[w.group == g].overlay_diff_2007_2015.mean()), 3),
                  "2016_2026": round(float(w[w.group == g].overlay_diff_2016_2026.mean()), 3)} for g in groups}
period_avg["All 19"] = {"2007_2015": round(float(w.overlay_diff_2007_2015.mean()), 3),
                        "2016_2026": round(float(w.overlay_diff_2016_2026.mean()), 3)}

bundle = {
    "rows": rows.reset_index().replace({np.nan: None}).to_dict(orient="records"),
    "pooled": js["pooled"], "M": {k: js[k] for k in ["M1", "M2", "M3"]},
    "M4": {k: v for k, v in js["M4"].items() if k != "break_even_bp"},
    "period_avg": period_avg,
    "curves": {t: {"dates": [d.strftime("%Y-%m") for d in curves[t]["strategy"].index],
                   "strategy": [round(float(x), 4) for x in curves[t]["strategy"]],
                   "market": [round(float(x), 4) for x in curves[t]["market"]]} for t in ["IWM", "EFA", "EEM"]},
}
(OUT / "data.json").write_text(json.dumps(bundle), encoding="utf-8")

# concentric arcs, partly off-canvas, as in the reference decks
fig = plt.figure(figsize=(13.333, 7.5), dpi=150)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 13.333)
ax.set_ylim(0, 7.5)
ax.axis("off")
for cx, cy in [(-0.6, -0.4), (13.9, 7.9)]:
    for r in np.arange(0.5, 3.6, 0.14):
        ax.add_patch(plt.Circle((cx, cy), r, fill=False, lw=0.7, color="#d9c7cc", alpha=0.55))
fig.savefig(OUT / "bg_arcs.png", transparent=True)
plt.close(fig)

# title header: burgundy field with every market's C-A curve
fig = plt.figure(figsize=(13.333, 4.1), dpi=150)
ax = fig.add_axes([0, 0, 1, 1])
fig.patch.set_facecolor("#5f021f")
ax.set_facecolor("#5f021f")
for t in MARKETS:
    c = curves[t]["strategy"]
    ax.plot(np.arange(len(c)), np.log(c.to_numpy()), color="white", alpha=0.10 if t != "SPY" else 0.35, lw=1.4)
ax.set_xlim(-5, len(c) + 5)
ax.axis("off")
fig.savefig(OUT / "title_header.png", facecolor="#5f021f")
plt.close(fig)
print("assets written")
