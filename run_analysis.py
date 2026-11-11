"""Gross vs net, cost sensitivity, win rates, leverage and the registered leverage diagnostics.

Run: python run_analysis.py      (writes results/analysis.json and results/figures/*.png)

The data end is frozen at the research run (2026-11-06) so that every number matches
results/backtest.json. Nothing here is out-of-sample: see research/LEVERAGE_HYPOTHESES.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.optimize import brentq  # noqa: E402

from strategy import analysis as A  # noqa: E402
from strategy.books import COST_PER_SIDE, MARGIN_SPREAD_PA, build  # noqa: E402
from strategy.data import daily_cash  # noqa: E402
from strategy.evaluate import paired_sharpe  # noqa: E402

END = "2026-11-06"
HOLDOUT = "2023-11-01"
PERIODS = {"full_2007_2026": slice(None, None), "2007_2015": slice(None, "2015-12-31"),
           "2016_2026": slice("2016-01-01", None), "holdout_2023_11": slice(HOLDOUT, None)}
COST_GRID_BP = [0, 0.5, 1, 2, 3, 5, 7.5, 10, 15, 20, 30, 40, 50]
SPREAD_GRID = [0.0, 0.005, 0.01, 0.015, 0.025, 0.04]
LEVERAGE_GRID = [0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
FIG = Path("results/figures")

# chart tokens (validated categorical order: blue, orange, aqua; neutral grey for the benchmark)
BLUE, ORANGE, AQUA, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984"
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False,
    "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 11,
    "axes.titlecolor": INK, "axes.titlelocation": "left", "font.size": 9.5, "lines.linewidth": 2,
    "legend.frameon": False, "legend.fontsize": 9})


def sr(x: pd.Series) -> float:
    return float(x.mean() / x.std() * np.sqrt(252))


def equity(excess: pd.Series, cash: pd.Series) -> pd.Series:
    return (1 + excess + cash.reindex(excess.index)).cumprod()


def shade_holdout(ax) -> None:
    ax.axvspan(pd.Timestamp(HOLDOUT), pd.Timestamp(END), color=GRID, alpha=0.6, lw=0, zorder=0)
    ax.text(pd.Timestamp(HOLDOUT), 1.0, " holdout", transform=ax.get_xaxis_transform(), va="top",
            ha="left", color=INK2, fontsize=8.5)


def save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=150)
    plt.close(fig)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    out: dict = {"data_end": END, "note": "in-sample diagnostics; see research/LEVERAGE_HYPOTHESES.md"}

    net = build(END)
    gross = build(END, cost_per_side=0.0, margin_spread_pa=0.0)
    idx = net["strategy"].index
    cash = daily_cash(idx)
    spy = net["spy"]

    c = A.components(END)
    W_ca = A.book_weights(c)
    sim0 = A.simulate(W_ca, c["R"], c["cash"], cost_per_side=0.0).loc[idx]
    turnover = sim0["turnover"]

    # ------------------------------------------------------------------ 1. gross vs net
    out["gross_vs_net"] = {}
    for p, sl in PERIODS.items():
        out["gross_vs_net"][p] = {
            "gross": A.stats(gross["strategy"].loc[sl], cash), "net": A.stats(net["strategy"].loc[sl], cash),
            "spy": A.stats(spy.loc[sl], cash),
            "cost_drag_pa": round(float((gross["strategy"] - net["strategy"]).loc[sl].mean() * 252), 5),
            "trading_cost_drag_pa": round(float(COST_PER_SIDE * turnover.loc[sl].mean() * 252), 5),
            "turnover_pa": round(float(turnover.loc[sl].mean() * 252), 2)}

    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(9, 6.2), sharex=True, gridspec_kw={"height_ratios": [3, 1.2]})
    eg, en, es = equity(gross["strategy"], cash), equity(net["strategy"], cash), equity(spy, cash)
    ax.plot(eg, color=ORANGE, label=f"Strategy gross  (CAGR {out['gross_vs_net']['full_2007_2026']['gross']['cagr_total']:.1%})")
    ax.plot(en, color=BLUE, label=f"Strategy net  (CAGR {out['gross_vs_net']['full_2007_2026']['net']['cagr_total']:.1%})")
    ax.plot(es, color=GREY, lw=1.5, label=f"SPY  (CAGR {out['gross_vs_net']['full_2007_2026']['spy']['cagr_total']:.1%})")
    ax.set_yscale("log")
    ax.set_ylabel("Growth of $1 (log)")
    ax.set_title("Strategy before and after costs, 2007-02 to 2026-11")
    shade_holdout(ax)
    ax.legend(loc="upper left")
    ax2.plot((eg / en - 1) * 100, color=INK2, lw=1.5)
    ax2.set_ylabel("Gross ahead of net, %")
    ax2.set_title("Cumulative cost drag (trading 1 bp/side + margin T-bill+1.5 %)", fontsize=10)
    save(fig, "gross_vs_net.png")

    # ------------------------------------------------------------------ 2. cost sensitivity
    sens = {"trading_cost_bp": [], "margin_spread": []}
    for bp in COST_GRID_BP:
        x = sim0["excess"] - bp * 1e-4 * turnover
        row = {"cost_bp_per_side": bp}
        for p in ("full_2007_2026", "holdout_2023_11"):
            row[p] = A.stats(x.loc[PERIODS[p]], cash)
        sens["trading_cost_bp"].append(row)
    for spread in SPREAD_GRID:
        x = A.simulate(W_ca, c["R"], c["cash"], margin_spread_pa=spread)["excess"].loc[idx]
        row = {"margin_spread_pa": spread}
        for p in ("full_2007_2026", "holdout_2023_11"):
            row[p] = A.stats(x.loc[PERIODS[p]], cash)
        sens["margin_spread"].append(row)
    be = {}
    for p in ("full_2007_2026", "holdout_2023_11"):
        sl = PERIODS[p]
        x0, to = sim0["excess"].loc[sl], turnover.loc[sl]
        be[p] = {"bp_where_sharpe_equals_spy": round(brentq(lambda b: sr(x0 - b * 1e-4 * to) - sr(spy.loc[sl]), 0, 2000), 1),
                 "bp_where_excess_return_is_zero": round(float(x0.mean() / to.mean() / 1e-4), 1)}
    sens["break_even"] = be
    out["cost_sensitivity"] = sens

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.9))
    for p, col, lab in (("full_2007_2026", BLUE, "2007–2026"), ("holdout_2023_11", ORANGE, "Holdout 2023-11+")):
        a1.plot(COST_GRID_BP, [r[p]["sharpe"] for r in sens["trading_cost_bp"]], color=col, marker="o", ms=4, label=f"Strategy {lab}")
        a1.axhline(sr(spy.loc[PERIODS[p]]), color=col, ls="--", lw=1.2, label=f"SPY {lab}")
        a1.axvline(be[p]["bp_where_sharpe_equals_spy"], color=col, ls=":", lw=1)
        a2.plot([s * 100 for s in SPREAD_GRID], [r[p]["sharpe"] for r in sens["margin_spread"]], color=col, marker="o", ms=4)
        a2.axhline(sr(spy.loc[PERIODS[p]]), color=col, ls="--", lw=1.2)
    a1.axvline(COST_PER_SIDE * 1e4, color=INK2, lw=1)
    a1.text(COST_PER_SIDE * 1e4, 0.55, " model: 1 bp", transform=a1.get_xaxis_transform(), color=INK2, fontsize=8.5, va="top")
    a1.set_xlabel("Trading cost per side, bp of notional")
    a1.set_ylabel("Sharpe ratio (net)")
    a1.set_title("Trading costs (dotted = break-even vs SPY)")
    a1.legend(fontsize=8, loc="center right")
    a2.axvline(MARGIN_SPREAD_PA * 100, color=INK2, lw=1)
    a2.text(MARGIN_SPREAD_PA * 100, 0.55, " model: 1.5 %", transform=a2.get_xaxis_transform(), color=INK2, fontsize=8.5, va="top")
    a2.set_xlabel("Margin spread over T-bill, % p.a.")
    a2.set_title("Financing cost of the dip leverage")
    save(fig, "cost_sensitivity.png")

    # ------------------------------------------------------------------ 3. win rates
    r_spy_ex = (c["R"]["SPY"] - c["cash"]).loc[idx]
    dip_pnl = r_spy_ex - MARGIN_SPREAD_PA / 252             # one extra unit of SPY, borrowed
    ob_pnl = -0.5 * r_spy_ex                                  # half a unit of SPY moved to cash
    dip_ep = A.episodes(c["dip"].loc[idx], dip_pnl)
    ob_ep = A.episodes(c["overbought"].loc[idx], ob_pnl)
    out["win_rates"] = {}
    for p, sl in PERIODS.items():
        a, b = (sl.start or idx[0]), (sl.stop or idx[-1])
        sel = lambda ep: ep[(ep["start"] >= pd.Timestamp(a)) & (ep["start"] <= pd.Timestamp(b))] if not ep.empty else ep  # noqa: E731
        out["win_rates"][p] = {
            "strategy": A.hit_rates(net["strategy"].loc[sl], cash, spy),
            "spy": A.hit_rates(spy.loc[sl], cash),
            "book1_dip_trades": A.episode_stats(sel(dip_ep), 2 * COST_PER_SIDE),
            "book1_overbought_trades": A.episode_stats(sel(ob_ep), 2 * 0.5 * COST_PER_SIDE)}
    dip_ep.assign(start=dip_ep["start"].dt.date, end=dip_ep["end"].dt.date).to_csv("results/dip_trades.csv", index=False)

    # ------------------------------------------------------------------ 4. static leverage
    lev = {}
    lev_series = {}
    for L in LEVERAGE_GRID:
        s = A.simulate(W_ca * L, c["R"], c["cash"]).loc[idx]
        lev_series[L] = s["excess"]
        lev[str(L)] = {p: A.stats(s["excess"].loc[sl], cash) for p, sl in PERIODS.items()}
        lev[str(L)]["max_gross_exposure"] = round(float(s["gross_exposure"].max()), 2)
        lev[str(L)]["avg_gross_exposure"] = round(float(s["gross_exposure"].mean()), 2)
    grid = np.round(np.arange(0.0, 10.01, 0.05), 2)
    growth_opt = {}
    sims = {L: A.simulate(W_ca * L, c["R"], c["cash"]).loc[idx]["excess"] for L in grid}
    for p, sl in PERIODS.items():
        g = [np.log1p(sims[L].loc[sl] + cash.loc[sl]).mean() for L in grid]
        growth_opt[p] = float(grid[int(np.argmax(g))])
    vol_ratio = float(spy.std() / net["strategy"].std())
    eq_vol = A.simulate(W_ca * vol_ratio, c["R"], c["cash"]).loc[idx]["excess"]
    out["leverage"] = {"static": lev, "growth_optimal_leverage": growth_opt,
                       "equal_vol_to_spy": {"leverage": round(vol_ratio, 2),
                                            **{p: {"strategy": A.stats(eq_vol.loc[sl], cash), "spy": A.stats(spy.loc[sl], cash)}
                                               for p, sl in PERIODS.items()}}}

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
    for p, col, lab in (("full_2007_2026", BLUE, "2007–2026"), ("holdout_2023_11", ORANGE, "Holdout")):
        for ax, key, scale in ((axes[0], "cagr_total", 100), (axes[1], "max_drawdown_total", 100), (axes[2], "sharpe", 1)):
            ax.plot(LEVERAGE_GRID, [lev[str(L)][p][key] * scale for L in LEVERAGE_GRID], color=col, marker="o", ms=4, label=lab)
            ax.axhline(A.stats(spy.loc[PERIODS[p]], cash)[key] * scale, color=col, ls="--", lw=1.1)
    for ax, t in zip(axes, ("CAGR, %", "Max drawdown, %", "Sharpe ratio")):
        ax.set_title(t)
        ax.set_xlabel("Leverage on the whole strategy")
        ax.axvline(1.0, color=INK2, lw=1)
    axes[0].legend(loc="upper left", title="dashed = SPY", title_fontsize=8)
    save(fig, "leverage.png")

    fig, ax = plt.subplots(figsize=(9, 4.4))
    for L, col in ((1.0, BLUE), (1.5, ORANGE), (2.0, AQUA)):
        st = lev[str(L)]["full_2007_2026"]
        ax.plot(equity(lev_series[L], cash), color=col, label=f"Strategy ×{L:g}  (CAGR {st['cagr_total']:.1%}, max DD {st['max_drawdown_total']:.0%})")
    st = A.stats(spy, cash)
    ax.plot(es, color=GREY, lw=1.5, label=f"SPY  (CAGR {st['cagr_total']:.1%}, max DD {st['max_drawdown_total']:.0%})")
    ax.set_yscale("log")
    ax.set_ylabel("Growth of $1 (log)")
    ax.set_title("Static leverage on the whole strategy (net of costs and financing)")
    shade_holdout(ax)
    ax.legend(loc="upper left")
    save(fig, "leverage_equity.png")

    # ------------------------------------------------------------------ 5. conditional moments
    reg = A.regimes(c)
    rets = pd.DataFrame({"strategy": net["strategy"], "book1": net["book1"], "book2": net["book2"],
                         "SPY": r_spy_ex, "TLT": (c["R"]["TLT"] - c["cash"]).loc[idx],
                         "GLD": (c["R"]["GLD"] - c["cash"]).loc[idx]})
    out["conditional"] = {k: A.conditional(rets, v.loc[idx]).to_dict(orient="records") for k, v in reg.items()}
    out["component_hurdle"] = {p: A.hurdle(rets.drop(columns="strategy").loc[sl], rets["strategy"].loc[sl]).to_dict(orient="records")
                               for p, sl in (("2007_2015", PERIODS["2007_2015"]), ("2016_2026", PERIODS["2016_2026"]))}

    fams = [("book1_state", ["dip", "neutral", "overbought"], "Book-1 state"),
            ("spy_trend", ["above_sma200", "below_sma200"], "SPY vs SMA200"),
            ("spy_volatility", ["low", "high"], "SPY 20d vol vs 1y median"),
            ("stock_bond_corr", ["negative", "positive"], "SPY–TLT 63d correlation")]
    fig, axes = plt.subplots(1, 4, figsize=(12, 3.8), sharey=True)
    for ax, (k, labels, title) in zip(axes, fams):
        df = pd.DataFrame(out["conditional"][k])
        xs = np.arange(len(labels))
        for j, (ser, col) in enumerate((("strategy", BLUE), ("book1", ORANGE), ("book2", AQUA))):
            v = [df[(df.series == ser) & (df.regime == lab)]["sharpe"].iloc[0] for lab in labels]
            ax.bar(xs + (j - 1) * 0.27, v, width=0.25, color=col, label=ser if k == "book1_state" else None)
        ax.set_xticks(xs, [f"{lab}\n{df[(df.series == 'strategy') & (df.regime == lab)]['share_of_days'].iloc[0]:.0%} of days" for lab in labels], fontsize=8.5)
        ax.axhline(0, color=INK2, lw=0.8)
        ax.set_title(title, fontsize=10)
    axes[0].set_ylabel("Sharpe on day t+1 (annualised)")
    axes[0].legend(fontsize=8, loc="upper right")
    fig.suptitle("Where the strategy earns per unit of risk, 2007–2026 (regime decided at close t)", x=0.01, ha="left",
                 fontweight="bold", color=INK, fontsize=11)
    save(fig, "conditional_sharpe.png")

    # ------------------------------------------------------------------ 6. registered timing variants
    R, cs = c["R"], c["cash"]
    ca_full = A.simulate(W_ca, R, cs)["excess"]
    vol_hat = (ca_full.rolling(20).std() * np.sqrt(252))
    lev_v1 = (0.10 / vol_hat).clip(upper=2.0).fillna(1.0)
    trend_on = (reg["spy_trend"] == "above_sma200").astype(float)
    corr_neg = (reg["stock_bond_corr"] == "negative").astype(float)
    vol_high = (reg["spy_volatility"] == "high").astype(float)
    dip, ob = c["dip"], c["overbought"]

    makers = {
        "V1_vol_target_10pct": (lambda ind: A.simulate(W_ca.mul(ind, axis=0), R, cs)["excess"], lev_v1),
        "V2_trend_1.5x": (lambda ind: A.simulate(W_ca.mul(1 + 0.5 * ind, axis=0), R, cs)["excess"], trend_on),
        "V3_book2_1.5x": (lambda ind: A.simulate(A.book_weights(c, book2_scale=1.5), R, cs)["excess"], None),
        "V4_book2_1.5x_if_corr_neg": (lambda ind: A.simulate(A.book_weights(c, book2_scale=1 + 0.5 * ind), R, cs)["excess"], corr_neg),
        "V5_dip_3x": (lambda ind: A.simulate(A.book_weights(c, exposure=(1 + 2 * dip - 0.5 * ob).clip(0.5, 3.0)), R, cs)["excess"], None),
        "V6_dip_3x_if_vol_high": (lambda ind: A.simulate(A.book_weights(c, exposure=(1 + dip + dip * ind - 0.5 * ob).clip(0.5, 3.0)), R, cs)["excess"], vol_high),
    }
    ca = ca_full.loc[idx]
    variants, pvals = {}, {}
    for name, (make, ind) in makers.items():
        x = make(ind).loc[idx]
        res = {p: {"stats": A.stats(x.loc[sl], cash), "paired_vs_CA": paired_sharpe(x.loc[sl], ca.loc[sl])}
               for p, sl in PERIODS.items()}
        if ind is not None:
            null = A.rotation_null(lambda i, m=make: m(i), ind, slice(idx[0], idx[-1]))
            obs = sr(x)
            res["rotation_null"] = {"observed_sharpe": round(obs, 3), "null_median": round(float(np.median(null)), 3),
                                    "null_95pct": round(float(np.percentile(null, 95)), 3),
                                    "p_value": round(float((1 + (null >= obs).sum()) / (1 + len(null))), 4)}
            pvals[name] = res["rotation_null"]["p_value"]
        else:
            pvals[name] = res["full_2007_2026"]["paired_vs_CA"]["p_value"]
        res["vol_ratio_vs_CA"] = round(float(x.std() / ca.std()), 2)
        variants[name] = res
    adj = A.holm(pvals)
    for name, res in variants.items():
        res["p_raw"], res["p_holm"] = pvals[name], adj[name]
        res["passes_registered_condition"] = bool(
            res["2007_2015"]["stats"]["sharpe"] > A.stats(ca.loc[PERIODS["2007_2015"]], cash)["sharpe"]
            and res["2016_2026"]["stats"]["sharpe"] > A.stats(ca.loc[PERIODS["2016_2026"]], cash)["sharpe"]
            and adj[name] < 0.10)
    out["leverage_variants"] = {"baseline_CA": {p: A.stats(ca.loc[sl], cash) for p, sl in PERIODS.items()},
                                "trials": len(makers), "variants": variants}

    names = list(variants)
    fig, ax = plt.subplots(figsize=(9, 3.9))
    ys = np.arange(len(names))[::-1]
    for p, col, off, lab in (("2007_2015", BLUE, 0.17, "2007–2015"), ("2016_2026", ORANGE, -0.17, "2016–2026-11")):
        base = out["leverage_variants"]["baseline_CA"][p]["sharpe"]
        ax.barh(ys + off, [variants[n][p]["stats"]["sharpe"] - base for n in names], height=0.32, color=col, label=lab)
    ax.axvline(0, color=INK2, lw=1)
    ax.set_yticks(ys, [f"{n}  (p_holm {variants[n]['p_holm']:.2f})" for n in names], fontsize=8.5)
    ax.set_xlabel("Sharpe difference vs C-A (net)")
    ax.set_title("Registered leverage variants: Sharpe gain over C-A in both halves")
    ax.legend(loc="lower right")
    save(fig, "leverage_variants.png")

    Path("results/analysis.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    g = out["gross_vs_net"]["full_2007_2026"]
    print(f"gross Sharpe {g['gross']['sharpe']:.3f} net {g['net']['sharpe']:.3f} SPY {g['spy']['sharpe']:.3f} "
          f"turnover {g['turnover_pa']}x  break-even {be}")
    print("win rates full:", out["win_rates"]["full_2007_2026"])
    print("growth-optimal leverage:", growth_opt)
    for n, v in variants.items():
        print(f"{n:28s} SR 07-15 {v['2007_2015']['stats']['sharpe']:.3f} 16-26 {v['2016_2026']['stats']['sharpe']:.3f} "
              f"p_raw {v['p_raw']:.3f} p_holm {v['p_holm']:.3f} pass {v['passes_registered_condition']}")


if __name__ == "__main__":
    main()
