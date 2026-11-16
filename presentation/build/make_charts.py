"""Chart images for the deck, drawn from data.json.

Keynote drops the native charts pptxgenjs writes, so the deck embeds these PNGs instead.
Run after make_assets.py:
    python presentation/build/make_charts.py presentation/build
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

OUT = Path(sys.argv[1])
D = json.loads((OUT / "data.json").read_text(encoding="utf-8"))
rows = D["rows"]

BURG, ROSE, OCHRE, GREY, MUTED, GRID = "#5F021F", "#B5838F", "#C08A2E", "#8C8C8C", "#5E5E5E", "#E6E0E2"
GROUP_COLOR = {"Reference": "#2E2E2E", "US segments": BURG, "Developed ex-US": ROSE, "Emerging": OCHRE}
GROUPS = list(GROUP_COLOR)
RANK = {g: i for i, g in enumerate(GROUPS)}

installed = {f.name for f in font_manager.fontManager.ttflist}
FONT = next((f for f in ["Calibri", "Carlito", "Helvetica Neue", "Arial"] if f in installed), "DejaVu Sans")
plt.rcParams.update({
    "font.family": FONT, "font.size": 11, "text.color": MUTED, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": GRID, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.75, "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False, "legend.frameon": False,
    "xtick.major.size": 0, "ytick.major.size": 0, "axes.axisbelow": True, "axes.facecolor": "none", "figure.facecolor": "none",
})


def label(r):
    return f"{r['ticker']}  {r['name']}"


def ordered(key):
    return sorted(rows, key=lambda r: (RANK[r["group"]], -r[key]))


def save(fig, name):
    fig.savefig(OUT / name, dpi=200, transparent=True)
    plt.close(fig)


def signed(x, d=2):
    return ("+" if x > 0 else "−" if x < 0 else "") + f"{abs(x):.{d}f}"


def barh_axes(w, h, n):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.grid(axis="y", visible=False)
    ax.set_ylim(n - 0.5, -0.5)
    return fig, ax


def legend_below(ax, handles, labels, ncol):
    ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=ncol, fontsize=12,
              handlelength=1.0, columnspacing=1.6)


# headline: C-A vs buy & hold
o = ordered("ca_sharpe")
fig, ax = barh_axes(8.3, 5.15, len(o))
y = range(len(o))
bh = ax.barh([i + 0.19 for i in y], [r["market_sharpe"] for r in o], height=0.36, color=GREY)
ca = ax.barh([i - 0.19 for i in y], [r["ca_sharpe"] for r in o], height=0.36, color=BURG)
ax.set_yticks(list(y), [label(r) for r in o], fontsize=10)
ax.set_xlim(0, 0.9)
ax.xaxis.set_major_formatter(lambda v, _: f"{v:.1f}")
legend_below(ax, [bh, ca], ["Buy & hold", "C-A"], 2)
fig.tight_layout()
save(fig, "chart_headline.png")

# dip overlay by market
o = ordered("overlay_diff")
fig, ax = barh_axes(8.3, 5.15, len(o))
ax.barh(range(len(o)), [r["overlay_diff"] for r in o], height=0.6, color=[GROUP_COLOR[r["group"]] for r in o])
ax.set_yticks(range(len(o)), [label(r) for r in o], fontsize=10)
ax.set_xlim(0, 0.2)
ax.set_xticks([0, 0.05, 0.1, 0.15, 0.2])
ax.xaxis.set_major_formatter(lambda v, _: signed(v))
legend_below(ax, [plt.Rectangle((0, 0), 1, 1, color=GROUP_COLOR[g]) for g in GROUPS], GROUPS, 4)
fig.tight_layout()
save(fig, "chart_overlay.png")

# overlay by period
cats = ["US segments", "Developed ex-US", "Emerging", "All 19"]
a = [D["period_avg"][c]["2007_2015"] for c in cats]
b = [D["period_avg"][c]["2016_2026"] for c in cats]
fig, ax = plt.subplots(figsize=(7.2, 4.9))
ax.grid(axis="x", visible=False)
x = range(len(cats))
b1 = ax.bar([i - 0.19 for i in x], a, width=0.36, color=BURG)
b2 = ax.bar([i + 0.19 for i in x], b, width=0.36, color=ROSE)
for bars in (b1, b2):
    for r in bars:
        ax.annotate(signed(r.get_height()), (r.get_x() + r.get_width() / 2, r.get_height()), xytext=(0, 3),
                    textcoords="offset points", ha="center", fontsize=10)
ax.set_xticks(list(x), cats, fontsize=12)
ax.set_ylim(0, 0.16)
ax.set_yticks([0, 0.04, 0.08, 0.12, 0.16])
ax.yaxis.set_major_formatter(lambda v, _: signed(v))
legend_below(ax, [b1, b2], ["2007–2015", "2016–2026"], 2)
fig.tight_layout()
save(fig, "chart_periods.png")

# rebalancing premium vs volatility
fig, ax = plt.subplots(figsize=(7.6, 5.1))
for g in GROUPS:
    rs = [r for r in rows if r["group"] == g]
    ax.scatter([r["market_vol"] * 100 for r in rs], [r["rebal_return_diff"] * 100 for r in rs], s=55,
               color=GROUP_COLOR[g], label=g, zorder=3)
ax.axhline(0, color=MUTED, lw=0.8, zorder=2)
ax.set_xlim(15, 40)
ax.set_ylim(-1.5, 1.0)
ax.yaxis.set_major_formatter(lambda v, _: signed(v, 1))
ax.set_xlabel("Equity volatility, % p.a.")
ax.set_ylabel("Book 2 minus drift, % p.a.")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=4, fontsize=12, handletextpad=0.3,
          columnspacing=1.6)
fig.tight_layout()
save(fig, "chart_rebal.png")

# C-A minus book 2 alone
o = sorted(rows, key=lambda r: -r["ca_minus_book2"])
fig, ax = barh_axes(7.6, 5.15, len(o))
vals = [r["ca_minus_book2"] for r in o]
ax.barh(range(len(o)), vals, height=0.6, color=[BURG if v > 0 else ROSE for v in vals])
ax.axvline(0, color=MUTED, lw=0.8)
ax.set_yticks(range(len(o)), [label(r) for r in o], fontsize=10)
ax.set_xlim(-0.1, 0.1)
ax.set_xticks([-0.1, -0.05, 0, 0.05, 0.1])
ax.xaxis.set_major_formatter(lambda v, _: signed(v))
legend_below(ax, [plt.Rectangle((0, 0), 1, 1, color=c) for c in (BURG, ROSE)], ["C-A ahead", "Book 2 alone ahead"], 2)
fig.tight_layout()
save(fig, "chart_book2.png")

# break-even costs
o = ordered("break_even_bp")
fig, ax = barh_axes(8.3, 5.15, len(o))
bars = ax.barh(range(len(o)), [r["break_even_bp"] for r in o], height=0.6, color=BURG)
for r, v in zip(bars, o):
    ax.annotate(f"{v['break_even_bp']:.0f}", (r.get_width(), r.get_y() + r.get_height() / 2), xytext=(4, 0),
                textcoords="offset points", va="center", fontsize=10)
ax.set_yticks(range(len(o)), [label(r) for r in o], fontsize=10)
ax.set_xlim(0, 55)
fig.tight_layout()
save(fig, "chart_costs.png")

# growth of 1 USD, log scale
for t, c in D["curves"].items():
    fig, ax = plt.subplots(figsize=(4.0, 4.4))
    n = len(c["strategy"])
    ax.plot(range(n), c["market"], color=GREY, lw=1.75)
    ax.plot(range(n), c["strategy"], color=BURG, lw=1.75)
    ax.set_yscale("log", base=2)
    ax.set_ylim(0.5, 8)
    ax.set_yticks([0.5, 1, 2, 4, 8], ["0.5", "1", "2", "4", "8"])
    ticks = [i for i, d in enumerate(c["dates"]) if d.startswith(("2008", "2012", "2016", "2020", "2024"))]
    first = {}
    for i in ticks:
        first.setdefault(c["dates"][i][:4], i)
    ax.set_xticks(list(first.values()), list(first.keys()))
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    save(fig, f"chart_equity_{t}.png")

print("charts written with font", FONT)
