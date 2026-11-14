"""C-A on 19 other equity markets (registered in research/MARKETS_HYPOTHESES.md).

Run: python run_markets.py       (writes results/markets.json, results/markets.csv, results/figures/markets_*.png)

The data end is frozen at the research run (2026-11-06). Every period is in-sample in time; the
markets are out-of-sample only in the cross-section.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats as st  # noqa: E402
from scipy.optimize import brentq  # noqa: E402

from strategy.data import daily_cash  # noqa: E402
from strategy.evaluate import paired_sharpe, sharpe, summary  # noqa: E402
from strategy.markets import MARKETS, build_market, dip_trade_stats, n_eff  # noqa: E402

END = "2026-11-06"
PERIODS = {"full": slice(None, None), "2007_2015": slice(None, "2015-12-31"), "2016_2026": slice("2016-01-01", None)}
COMPARISONS = {"ca_vs_market": ("strategy", "market"), "book1_vs_market": ("book1", "market"),
               "book2_vs_drift": ("book2", "drift"),
               "ca_vs_book2_unregistered": ("strategy", "book2")}
COST_CHECK_BP = 5.0
LABEL_OFFSET = {"EWW": (-26, 3), "EWA": (5, -10), "OEF": (5, -10), "SPY": (-24, 3), "EZU": (5, -10)}
FIG = Path("results/figures")

BLUE, ORANGE, AQUA, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984"
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
GROUP_COLOR = {"Reference": INK, "US segments": BLUE, "Developed ex-US": AQUA, "Emerging": ORANGE}
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False,
    "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 11,
    "axes.titlecolor": INK, "axes.titlelocation": "left", "font.size": 9.5, "lines.linewidth": 2,
    "legend.frameon": False, "legend.fontsize": 9})


def ca_minus_market(ticker: str, cost_bp: float) -> float:
    """Full-period Sharpe of C-A minus buy & hold at a given cost per side."""
    s = build_market(ticker, END, cost_per_side=cost_bp / 1e4)
    return sharpe(s["strategy"]) - sharpe(s["market"])


def break_even_bp(ticker: str) -> float | None:
    """Cost per side at which C-A's Sharpe advantage over buy & hold vanishes (None if never within 200 bp)."""
    lo, hi = ca_minus_market(ticker, 0.0), ca_minus_market(ticker, 200.0)
    if lo <= 0:
        return 0.0
    if hi > 0:
        return None
    return round(brentq(lambda c: ca_minus_market(ticker, c), 0.0, 200.0, xtol=0.25), 1)


def pooled(z: pd.Series, diffs: pd.DataFrame) -> dict:
    """Mean z-statistic scaled by sqrt(n_eff) (equicorrelated z-statistics)."""
    ne, rho = n_eff(diffs)
    zp = float(z.mean() * math.sqrt(ne))
    return {"n": int(len(z)), "n_eff": round(ne, 2), "mean_rho": round(rho, 3), "mean_z": round(float(z.mean()), 3),
            "pooled_z": round(zp, 2), "p_value": round(float(2 * (1 - st.norm.cdf(abs(zp)))), 4)}


def save(fig, name: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=150)
    plt.close(fig)


def figures(rows: pd.DataFrame, series: dict[str, dict], out: dict) -> None:
    order = rows.sort_values(["group_rank", "ca_sharpe"]).index.tolist()
    y = np.arange(len(order))

    fig, ax = plt.subplots(figsize=(8, 7.2))
    ax.barh(y + 0.2, rows.loc[order, "market_sharpe"], 0.4, color=GREY, label="Buy & hold")
    ax.barh(y - 0.2, rows.loc[order, "ca_sharpe"], 0.4, color=BLUE, label="C-A on that market")
    ax.set_yticks(y, [f"{t}  {MARKETS[t][0]}" for t in order])
    for lab, t in zip(ax.get_yticklabels(), order):
        lab.set_color(GROUP_COLOR[MARKETS[t][1]])
    ax.axvline(0, color=INK2, lw=0.8)
    ax.invert_yaxis()
    ax.set_xlabel("Sharpe ratio 2007-02 – 2026-11 (excess over T-bill, USD)")
    ax.set_title("C-A beats buy & hold in all 19 markets (and on SPY)")
    ax.legend(loc="lower right")
    ax.grid(axis="y", visible=False)
    save(fig, "markets_sharpe.png")

    fig, ax = plt.subplots(figsize=(8, 7.2))
    d = rows.loc[order, "overlay_diff"]
    se = (d / rows.loc[order, "overlay_z"]).abs()
    colors = [GROUP_COLOR[MARKETS[t][1]] for t in order]
    ax.errorbar(d, y, xerr=1.96 * se, fmt="none", ecolor=GRID, elinewidth=3)
    ax.scatter(d, y, color=colors, zorder=3, s=36)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(y, [f"{t}  {MARKETS[t][0]}" for t in order])
    for lab, t in zip(ax.get_yticklabels(), order):
        lab.set_color(GROUP_COLOR[MARKETS[t][1]])
    ax.invert_yaxis()
    ax.set_xlabel("Sharpe of book 1 (dip overlay) minus buy & hold, with 95 % interval")
    ax.set_title("The dip overlay adds Sharpe in all 19 markets, but is significant in few")
    ax.grid(axis="y", visible=False)
    save(fig, "markets_overlay.png")

    fig, ax = plt.subplots(figsize=(7, 4.6))
    for t in rows.index:
        g = MARKETS[t][1]
        ax.scatter(rows.loc[t, "market_vol"] * 100, rows.loc[t, "rebal_return_diff"] * 100, color=GROUP_COLOR[g], s=36,
                   zorder=3)
        ax.annotate(t, (rows.loc[t, "market_vol"] * 100, rows.loc[t, "rebal_return_diff"] * 100),
                    textcoords="offset points", xytext=LABEL_OFFSET.get(t, (5, 3)), fontsize=8, color=INK2)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xlabel("Volatility of the equity market p.a. (%)")
    ax.set_ylabel("Book 2 minus never-rebalanced, % p.a.")
    ax.set_title(f"Rebalancing premium vs equity volatility (Spearman {out['M3']['spearman_vol_vs_premium']:+.2f})")
    save(fig, "markets_rebalancing.png")

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=False)
    for ax, t in zip(axes, ["IWM", "EFA", "EEM"]):
        s = series[t]
        cash = daily_cash(s["strategy"].index)
        for k, c, lab in [("market", GREY, "Buy & hold"), ("strategy", BLUE, "C-A")]:
            ax.plot((1 + s[k] + cash).cumprod(), color=c, lw=1.6, label=lab)
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(matplotlib.ticker.FixedLocator([0.5, 1, 2, 4, 8]))
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
        ax.set_title(f"{t} — {MARKETS[t][0]}")
    axes[0].legend(loc="upper left")
    axes[0].set_ylabel("Growth of 1 USD (log)")
    save(fig, "markets_equity.png")


def main() -> None:
    series = {t: build_market(t, END) for t in MARKETS}
    rank = {"Reference": 0, "US segments": 1, "Developed ex-US": 2, "Emerging": 3}
    out: dict = {"data_end": END, "markets": {}, "pooled": {}}
    rows = []
    for t, s in series.items():
        cash = daily_cash(s["strategy"].index)
        m = {"name": MARKETS[t][0], "group": MARKETS[t][1], "start": str(s["strategy"].index[0].date()),
             "summary": {k: summary(s[k], cash) for k in ["strategy", "market", "book1", "book2", "drift"]},
             "tests": {p: {c: paired_sharpe(s[a].loc[sl], s[b].loc[sl]) for c, (a, b) in COMPARISONS.items()}
                       for p, sl in PERIODS.items()},
             "dip_trades": dip_trade_stats(s["dip"], s["market"])}
        out["markets"][t] = m
        ft = m["tests"]["full"]
        rows.append({"ticker": t, "name": m["name"], "group": m["group"], "group_rank": rank[m["group"]],
                     "ca_sharpe": ft["ca_vs_market"]["sharpe_a"], "market_sharpe": ft["ca_vs_market"]["sharpe_b"],
                     "ca_diff": ft["ca_vs_market"]["diff"], "ca_p": ft["ca_vs_market"]["p_value"],
                     "book1_sharpe": ft["book1_vs_market"]["sharpe_a"],
                     "overlay_diff": ft["book1_vs_market"]["diff"], "overlay_z": ft["book1_vs_market"]["z"],
                     "overlay_p": ft["book1_vs_market"]["p_value"],
                     "overlay_diff_2007_2015": m["tests"]["2007_2015"]["book1_vs_market"]["diff"],
                     "overlay_diff_2016_2026": m["tests"]["2016_2026"]["book1_vs_market"]["diff"],
                     "book2_sharpe": ft["book2_vs_drift"]["sharpe_a"], "drift_sharpe": ft["book2_vs_drift"]["sharpe_b"],
                     "ca_minus_book2": ft["ca_vs_book2_unregistered"]["diff"],
                     "ca_vs_book2_p": ft["ca_vs_book2_unregistered"]["p_value"],
                     "rebal_diff": ft["book2_vs_drift"]["diff"], "rebal_p": ft["book2_vs_drift"]["p_value"],
                     "no_overlay_sharpe": round(sharpe(0.5 * s["market"] + 0.5 * s["book2"]), 3),
                     "rebal_return_diff": float((s["book2"] - s["drift"]).mean() * 252),
                     "market_vol": m["summary"]["market"]["volatility_pa"],
                     "ca_cagr": m["summary"]["strategy"]["cagr_total"], "market_cagr": m["summary"]["market"]["cagr_total"],
                     "ca_maxdd": m["summary"]["strategy"]["max_drawdown_total"],
                     "market_maxdd": m["summary"]["market"]["max_drawdown_total"],
                     "dip_trades": m["dip_trades"]["trades"], "dip_win_rate": m["dip_trades"]["win_rate"]})
    rows = pd.DataFrame(rows).set_index("ticker")
    rows["overlay_share"] = ((rows["ca_sharpe"] - rows["no_overlay_sharpe"]) / rows["ca_diff"]).round(3)
    wit = [t for t in MARKETS if MARKETS[t][1] != "Reference"]

    for p, sl in PERIODS.items():
        out["pooled"][p] = {}
        for c, (a, b) in COMPARISONS.items():
            z = pd.Series({t: out["markets"][t]["tests"][p][c]["z"] for t in wit})
            diffs = pd.DataFrame({t: (series[t][a] - series[t][b]).loc[sl] for t in wit})
            wins = int(sum(out["markets"][t]["tests"][p][c]["diff"] > 0 for t in wit))
            out["pooled"][p][c] = {"wins": wins, **pooled(z, diffs)}
            for g in ["US segments", "Developed ex-US", "Emerging"]:
                gt = [t for t in wit if MARKETS[t][1] == g]
                out["pooled"][p][f"{c}__{g}"] = {
                    "wins": int(sum(out["markets"][t]["tests"][p][c]["diff"] > 0 for t in gt)),
                    **pooled(z[gt], diffs[gt])}

    be = {t: break_even_bp(t) for t in MARKETS}
    at5 = {t: ca_minus_market(t, COST_CHECK_BP) for t in wit}
    rows["break_even_bp"] = pd.Series(be)
    rows["ca_diff_at_5bp"] = pd.Series(at5).round(3)

    pf = out["pooled"]
    m1 = pf["full"]["ca_vs_market"]
    m2 = {p: pf[p]["book1_vs_market"] for p in PERIODS}
    m3 = pf["full"]["book2_vs_drift"]
    rho_m3 = float(st.spearmanr(rows.loc[wit, "market_vol"], rows.loc[wit, "rebal_return_diff"])[0])
    wins_5 = int(sum(v > 0 for v in at5.values()))
    out["M1"] = {"wins": m1["wins"], "p_value": m1["p_value"], "pass": m1["wins"] >= 15 and m1["p_value"] < 0.10}
    out["M2"] = {p: {"wins": v["wins"], "p_value": v["p_value"]} for p, v in m2.items()}
    out["M2"]["pass"] = all(m2[p]["wins"] >= 13 and m2[p]["p_value"] < 0.10 for p in ["full", "2007_2015", "2016_2026"])
    out["M3"] = {"wins": m3["wins"], "spearman_vol_vs_premium": round(rho_m3, 3),
                 "pass": m3["wins"] >= 13 and rho_m3 > 0}
    out["M4"] = {"wins_at_1bp": m1["wins"], "wins_at_5bp": wins_5, "pass": wins_5 >= m1["wins"] - 2,
                 "break_even_bp": be}
    out["generalises"] = bool(out["M1"]["pass"] and out["M2"]["pass"])

    Path("results").mkdir(exist_ok=True)
    Path("results/markets.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    rows.drop(columns="group_rank").to_csv("results/markets.csv", float_format="%.4f")
    figures(rows, series, out)

    pd.set_option("display.width", 220)
    print(rows[["group", "ca_sharpe", "market_sharpe", "ca_p", "no_overlay_sharpe", "overlay_share", "book1_sharpe", "overlay_diff", "overlay_p",
                "overlay_diff_2007_2015", "overlay_diff_2016_2026", "rebal_diff", "market_vol", "dip_trades",
                "dip_win_rate", "break_even_bp", "ca_diff_at_5bp", "ca_minus_book2", "ca_vs_book2_p"]].to_string())
    for p in PERIODS:
        for c in COMPARISONS:
            print(p, c, pf[p][c])
            for g in ["US segments", "Developed ex-US", "Emerging"]:
                print("   ", g, pf[p][f"{c}__{g}"])
    print({k: out[k] for k in ["M1", "M2", "M3"]}, "M4", {k: v for k, v in out["M4"].items() if k != "break_even_bp"})
    print("generalises:", out["generalises"])


if __name__ == "__main__":
    main()
