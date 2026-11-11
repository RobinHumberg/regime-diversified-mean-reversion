"""Dip-trade risk controls: drawdown decomposition and the 7 registered variants D1-D7.

Run: python run_dip_risk.py      (writes results/dip_risk.json and results/figures/dip_*.png)

In-sample diagnostics only, see research/DIP_RISK_HYPOTHESES.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from run_analysis import AQUA, BLUE, END, FIG, GREY, INK2, ORANGE, PERIODS, plt, save  # noqa: F401
from strategy import analysis as A
from strategy import dip_risk as D
from strategy.books import COST_PER_SIDE, MARGIN_SPREAD_PA, build, exposure_book
from strategy.data import closes, daily_cash
from strategy.evaluate import paired_sharpe

def cvar(x: pd.Series, q: float) -> float:
    """Mean of the worst q share of observations."""
    v = np.sort(x.dropna().to_numpy())
    return round(float(v[: max(1, int(np.ceil(q * len(v))))].mean()), 4)


HALVES = {"2007_2015": PERIODS["2007_2015"], "2016_2026": PERIODS["2016_2026"]}


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    s = build(END)
    idx = s["strategy"].index
    cash = daily_cash(idx)
    spy = closes(["SPY"], END)["SPY"].dropna()
    r_spy = spy.pct_change()
    cash_spy = daily_cash(spy.index)
    c = A.components(END)
    out: dict = {"data_end": END, "note": "in-sample diagnostics; see research/DIP_RISK_HYPOTHESES.md"}

    # ------------------------------------------------------------- step 0: drawdown decomposition
    overlay = 0.5 * (s["book1"] - s["spy"])
    parts = {"SPY half of book 1": 0.5 * s["spy"], "dip/overbought overlay": overlay, "book 2": 0.5 * s["book2"]}
    dd_rows = []
    for peak, trough, depth in D.drawdowns(s["strategy"] + cash, k=5):
        w = slice(peak + pd.Timedelta(days=1), trough)  # the peak day itself is not a loss
        row = {"peak": str(peak.date()), "trough": str(trough.date()), "depth": round(depth, 4),
               "sum_excess": round(float(s["strategy"].loc[w].sum()), 4)}
        row.update({k: round(float(v.loc[w].sum()), 4) for k, v in parts.items()})
        row["dip_days_in_window"] = int(c["dip"].shift(1).reindex(s["strategy"].loc[w].index).sum())
        dd_rows.append(row)
    out["drawdown_decomposition"] = dd_rows

    # ------------------------------------------------------------- variants
    vix = closes(["^VIX", "^VIX3M"], END)
    contango = (vix["^VIX"] < vix["^VIX3M"]).reindex(spy.index)          # NaN before 2006-07 -> allowed
    s200 = spy.rolling(200).mean()
    rising = s200 > s200.shift(20)
    inv_vol = (0.15 / (r_spy.rolling(20).std() * np.sqrt(252))).clip(upper=1.0)
    specs = {
        "C-A": {},
        "D1_time_stop_5d": {"max_hold": 5},
        "D2_trend_break_exit": {"trend_exit": True},
        "D3_price_stop_3sigma": {"stop_sigma": 3.0},
        "D4_inverse_vol_size": {"size": inv_vol},
        "D5_vix_backwardation_veto": {"entry_ok": contango.where(contango.notna(), True).astype(bool)},
        "D6_rising_sma200": {"entry_ok": rising},
        "D7_D1+D2_dip_3x": {"max_hold": 5, "trend_exit": True, "size": 2.0, "max_exposure": 3.0},
    }
    res, series = {}, {}
    for name, kw in specs.items():
        ex = D.dip_exposure_variant(spy, **kw)
        book1 = exposure_book(ex["exposure"], r_spy.reindex(spy.index), cash_spy)
        ov = (book1 - (r_spy - cash_spy)).reindex(idx)
        W = A.book_weights(c, exposure=ex["exposure"].reindex(c["R"].index))
        strat = A.simulate(W, c["R"], c["cash"])["excess"]
        series[name] = strat.loc[idx]
        trades = D.dip_trades(ex["extra"], r_spy, cash_spy, COST_PER_SIDE, MARGIN_SPREAD_PA)
        trades = trades[trades["start"] >= idx[0]]
        r = {"trade_level": {}, "overlay_sharpe": {}, "strategy": {}}
        for p, sl in {**HALVES, "full_2007_2026": PERIODS["full_2007_2026"], "holdout_2023_11": PERIODS["holdout_2023_11"]}.items():
            a, b = pd.Timestamp(sl.start or idx[0]), pd.Timestamp(sl.stop or idx[-1])
            r["trade_level"][p] = D.trade_stats(trades[(trades["start"] >= a) & (trades["start"] <= b)])
            o = ov.loc[sl]
            r["overlay_sharpe"][p] = round(float(o.mean() / o.std() * np.sqrt(252)), 3)
            st = A.stats(series[name].loc[sl], cash)
            st["cvar1_daily"] = cvar(series[name].loc[sl] + cash.loc[sl], 0.01)
            r["strategy"][p] = st
        r["leverage_at_minus_40pct_dd"] = D.leverage_at_drawdown(
            lambda L, W=W: A.simulate(W * L, c["R"], c["cash"])["excess"].loc[idx], cash)
        res[name] = r

    base = res["C-A"]
    pvals = {}
    for name in specs:
        if name == "C-A":
            continue
        r = res[name]
        r["paired_vs_CA"] = {p: paired_sharpe(series[name].loc[sl], series["C-A"].loc[sl])
                             for p, sl in {**HALVES, "full_2007_2026": PERIODS["full_2007_2026"]}.items()}
        pvals[name] = r["paired_vs_CA"]["full_2007_2026"]["p_value"]
    adj = A.holm(pvals)
    for name, p in adj.items():
        r = res[name]
        r["p_holm"] = p
        cond = []
        for h in HALVES:
            t, tb = r["trade_level"][h], base["trade_level"][h]
            cond.append(t["worst_trade"] > tb["worst_trade"] and t["cvar5_trade"] > tb["cvar5_trade"]
                        and r["overlay_sharpe"][h] >= base["overlay_sharpe"][h] - 0.05)
        sig_worse = r["paired_vs_CA"]["full_2007_2026"]["diff"] < 0 and p < 0.10
        r["passes_registered_condition"] = bool(all(cond) and not sig_worse)
    out["variants"] = res

    # ------------------------------------------------------------- robustness of D5 (not a new trial)
    # VIX settles at 16:15 ET, SPY at 16:00: a same-day VIX reading is 15 minutes late. Age it.
    def d5_overlay(entry_ok: pd.Series) -> dict:
        ex = D.dip_exposure_variant(spy, entry_ok=entry_ok)
        ov = (exposure_book(ex["exposure"], r_spy, cash_spy) - (r_spy - cash_spy)).loc[idx[0]:idx[-1]]
        tr = D.dip_trades(ex["extra"], r_spy, cash_spy, COST_PER_SIDE, MARGIN_SPREAD_PA)
        tr = tr[tr["start"] >= idx[0]]
        st = D.trade_stats(tr)
        return {"overlay_sharpe": round(float(ov.mean() / ov.std() * np.sqrt(252)), 3),
                "worst_trade": st["worst_trade"], "cvar5_trade": st["cvar5_trade"], "trades": st["trades"]}

    allowed = contango.where(contango.notna(), True).astype(bool)
    aging = {f"lag_{k}d": d5_overlay(contango.shift(k).where(contango.shift(k).notna(), True).astype(bool))
             for k in (0, 1, 2)}
    aging["C-A"] = d5_overlay(pd.Series(True, index=spy.index))
    rng = np.random.default_rng(7)
    v = allowed.to_numpy()
    null = [d5_overlay(pd.Series(np.roll(v, int(rng.integers(252, len(v) - 252))), index=spy.index))
            for _ in range(300)]
    obs = aging["lag_0d"]
    out["d5_robustness"] = {
        "aging": aging,
        "rotation_null": {
            "overlay_sharpe_p": round((1 + sum(n["overlay_sharpe"] >= obs["overlay_sharpe"] for n in null)) / 301, 4),
            "cvar5_p": round((1 + sum(n["cvar5_trade"] >= obs["cvar5_trade"] for n in null)) / 301, 4),
            "null_median_overlay_sharpe": float(np.median([n["overlay_sharpe"] for n in null]))},
        "share_of_days_backwardated": round(float((~allowed).loc[idx[0]:].mean()), 3)}
    base_tr = D.dip_trades(D.dip_exposure_variant(spy)["extra"], r_spy, cash_spy, COST_PER_SIDE, MARGIN_SPREAD_PA)
    d5_tr = D.dip_trades(D.dip_exposure_variant(spy, entry_ok=allowed)["extra"], r_spy, cash_spy, COST_PER_SIDE, MARGIN_SPREAD_PA)
    base_tr, d5_tr = base_tr[base_tr["start"] >= idx[0]], d5_tr[d5_tr["start"] >= idx[0]]
    gone = base_tr[~base_tr["start"].isin(d5_tr["start"])]
    out["d5_robustness"]["vetoed_trades"] = {"n": int(len(gone)), "win_rate": round(float((gone["pnl"] > 0).mean()), 3),
                                             "mean_pnl": round(float(gone["pnl"].mean()), 4),
                                             "sum_pnl": round(float(gone["pnl"].sum()), 4)}
    # How far from the 1.0 threshold were the vetoes? A 15-minute VIX move cannot flip a clear
    # backwardation, but it can flip a borderline one. No intraday VIX/VIX3M history is available.
    ratio = (vix["^VIX"] / vix["^VIX3M"]).reindex(spy.index)
    entry_close = gone["start"].map(lambda d: spy.index[spy.index.get_loc(d) - 1])
    out["d5_robustness"]["vetoed_entry_ratio"] = [
        {"entry_close": str(e.date()), "vix_vix3m": round(float(ratio.loc[e]), 3), "pnl": round(float(p), 4)}
        for e, p in sorted(zip(entry_close, gone["pnl"]), key=lambda t: t[1])]
    sens = {}
    for m in (-0.05, -0.02, 0.0, 0.02, 0.05):
        okm = (ratio < 1 + m).where(ratio.notna(), True).astype(bool)
        tr = D.dip_trades(D.dip_exposure_variant(spy, entry_ok=okm)["extra"], r_spy, cash_spy, COST_PER_SIDE, MARGIN_SPREAD_PA)
        sens[f"veto_if_ratio_ge_{1 + m:.2f}"] = D.trade_stats(tr[tr["start"] >= idx[0]])
    out["d5_robustness"]["threshold_sensitivity"] = sens
    Path("results/dip_risk.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")

    # ------------------------------------------------------------- figures
    names = list(specs)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2), sharey=True)
    ys = np.arange(len(names))[::-1]
    for ax, (key, title, scale) in zip(axes, (("worst_trade", "Worst dip trade, %", 100),
                                              ("cvar5_trade", "Mean of worst 5 % of dip trades, %", 100),
                                              ("overlay", "Overlay Sharpe (book 1 − SPY)", 1))):
        for h, col, off, lab in (("2007_2015", BLUE, 0.18, "2007–2015"), ("2016_2026", ORANGE, -0.18, "2016–2026-11")):
            v = [res[n]["overlay_sharpe"][h] if key == "overlay" else res[n]["trade_level"][h][key] * scale for n in names]
            ax.barh(ys + off, v, height=0.34, color=col, label=lab)
        ax.axvline(0, color=INK2, lw=0.8)
        ax.set_title(title, fontsize=10)
    axes[0].set_yticks(ys, names, fontsize=8.5)
    handles, labels = axes[2].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", ncol=2, fontsize=8.5)
    fig.suptitle("Dip-trade risk controls (per unit of book-1 capital, after costs)", x=0.01, ha="left",
                 fontweight="bold", fontsize=11)
    save(fig, "dip_risk_trades.png")

    fig, ax = plt.subplots(figsize=(9, 4.0))
    xs = np.arange(len(dd_rows))
    for j, (part, col) in enumerate((("SPY half of book 1", GREY), ("dip/overbought overlay", ORANGE), ("book 2", AQUA))):
        ax.bar(xs + (j - 1) * 0.27, [row[part] * 100 for row in dd_rows], width=0.25, color=col, label=part)
    ax.set_xticks(xs, [f"{row['peak'][:7]} → {row['trough'][:7]}\nDD {row['depth']:.0%}" for row in dd_rows], fontsize=8.5)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_ylabel("Contribution, % of capital (sum of excess returns)")
    ax.set_title("What caused the five largest drawdowns of C-A")
    ax.legend(loc="lower right", fontsize=8.5)
    save(fig, "dip_risk_drawdown.png")

    for row in dd_rows:
        print(row)
    print("D5 robustness:", out["d5_robustness"])
    for n, r in res.items():
        t = r["trade_level"]
        print(f"{n:28s} trades {t['full_2007_2026']['trades']:3d} win {t['full_2007_2026']['win_rate']:.2f} "
              f"worst {t['2007_2015']['worst_trade']:+.3f}/{t['2016_2026']['worst_trade']:+.3f} "
              f"cvar5 {t['2007_2015']['cvar5_trade']:+.3f}/{t['2016_2026']['cvar5_trade']:+.3f} "
              f"ovSR {r['overlay_sharpe']['2007_2015']:.2f}/{r['overlay_sharpe']['2016_2026']:.2f} "
              f"SR {r['strategy']['full_2007_2026']['sharpe']:.3f} DD {r['strategy']['full_2007_2026']['max_drawdown_total']:.3f} "
              f"L@-40 {r['leverage_at_minus_40pct_dd']} p_holm {r.get('p_holm', '-')} pass {r.get('passes_registered_condition', '-')}")


if __name__ == "__main__":
    main()
