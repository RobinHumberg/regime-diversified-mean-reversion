"""Diagnostics around the frozen strategy: costs, win rates, leverage and conditional regimes.

Nothing here changes C-A. The portfolio-level simulator below reproduces C-A from its target
weights (see ``tests/test_analysis.py``) so that the same weights can be scaled by a leverage
factor, per book or over time, under identical cost and financing accounting.

Every regime indicator is decided at the close of day t and applied to the return of day t+1.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .books import (COST_PER_SIDE, CRP_ASSETS, CRP_START, MARGIN_SPREAD_PA, VOL_WINDOW,
                    WARMUP_DAYS, connors_states, crp_weights, dip_exposure)
from .data import closes, daily_cash

DAYS = 252


# --------------------------------------------------------------------------- inputs

def components(end: str | None = None) -> dict:
    """Asset returns, cash and both books' target weights on the book-2 calendar."""
    spy_all = closes(["SPY"], end)["SPY"].dropna()
    px = closes(CRP_ASSETS, end).loc[CRP_START:].dropna()
    R = px.pct_change().iloc[1:]
    cash = daily_cash(R.index)
    first = R.rolling(VOL_WINDOW).std().dropna().index[0]
    start = R.index[R.index >= first + pd.Timedelta(days=WARMUP_DAYS)][0]
    st = connors_states(spy_all).reindex(R.index)
    return {"R": R, "cash": cash, "start": start, "spy_close": spy_all.reindex(R.index),
            "exposure": dip_exposure(spy_all).reindex(R.index), "dip": st["dip"],
            "overbought": st["overbought"], "w2": crp_weights(R)}


def book_weights(c: dict, book1_scale=1.0, book2_scale=1.0, exposure: pd.Series | None = None) -> pd.DataFrame:
    """C-A target weights 0.5 * book 1 + 0.5 * book 2, each optionally scaled (scalar or series)."""
    e = c["exposure"] if exposure is None else exposure
    W = 0.5 * c["w2"].mul(book2_scale, axis=0)
    W["SPY"] = W["SPY"] + 0.5 * e * book1_scale
    return W


# --------------------------------------------------------------------------- simulator

def simulate(W: pd.DataFrame, R: pd.DataFrame, cash: pd.Series, cost_per_side: float = COST_PER_SIDE,
             margin_spread_pa: float = MARGIN_SPREAD_PA) -> pd.DataFrame:
    """Daily rebalancing to target weights W (decided at close t, held on t+1).

    Same accounting as ``books.weights_book``: cash earns the T-bill, net borrowing pays
    T-bill + spread, cost is charged on the exact turnover against the drifted holdings.
    Returns columns ``excess`` (over the T-bill), ``turnover`` and ``gross_exposure``.
    """
    Wv, Rv, cv = W.to_numpy(), R.fillna(0.0).to_numpy(), cash.to_numpy()
    held = np.vstack([np.zeros(Wv.shape[1]), Wv[:-1]])
    c = 1.0 - held.sum(axis=1)
    port = (held * Rv).sum(axis=1) + c * cv - np.maximum(-c, 0.0) * margin_spread_pa / DAYS
    drifted = held * (1 + Rv) / (1 + port)[:, None]
    turnover = np.abs(Wv - drifted).sum(axis=1)
    turnover[0] = turnover[-1] = 0.0
    return pd.DataFrame({"excess": port - cost_per_side * turnover - cv, "turnover": turnover,
                         "gross_exposure": np.abs(held).sum(axis=1)}, index=W.index)


# --------------------------------------------------------------------------- statistics

def stats(excess: pd.Series, cash: pd.Series) -> dict:
    """Sharpe on excess returns; CAGR, drawdown, worst day/month on TOTAL returns."""
    x = excess.dropna()
    total = x + cash.reindex(x.index)
    eq = (1 + total).cumprod()
    monthly = (1 + total).groupby(total.index.to_period("M")).prod() - 1
    cagr = eq.iloc[-1] ** (DAYS / len(total)) - 1
    mdd = (eq / eq.cummax() - 1).min()
    return {"sharpe": round(float(x.mean() / x.std() * np.sqrt(DAYS)), 3),
            "excess_return_pa": round(float(x.mean() * DAYS), 4),
            "volatility_pa": round(float(x.std() * np.sqrt(DAYS)), 4),
            "cagr_total": round(float(cagr), 4), "max_drawdown_total": round(float(mdd), 4),
            "calmar": round(float(cagr / -mdd), 3) if mdd < 0 else None,
            "worst_day": round(float(total.min()), 4), "worst_month": round(float(monthly.min()), 4),
            "days": int(len(x))}


def hit_rates(excess: pd.Series, cash: pd.Series, benchmark: pd.Series | None = None) -> dict:
    """Share of positive days / months / years (total return), optionally share beating a benchmark."""
    total = excess + cash.reindex(excess.index)
    out = {}
    for name, freq in (("daily", None), ("monthly", "M"), ("yearly", "Y")):
        r = total if freq is None else (1 + total).groupby(total.index.to_period(freq)).prod() - 1
        out[f"{name}_win_rate"] = round(float((r > 0).mean()), 4)
        if benchmark is not None:
            bt = benchmark.reindex(excess.index) + cash.reindex(excess.index)
            b = bt if freq is None else (1 + bt).groupby(bt.index.to_period(freq)).prod() - 1
            out[f"{name}_beats_benchmark"] = round(float((r > b).mean()), 4)
    return out


def episodes(state: pd.Series, pnl: pd.Series) -> pd.DataFrame:
    """Contiguous runs where ``state`` (decided at close t) is held on t+1, with summed P&L."""
    held = state.shift(1).fillna(0).astype(int)
    run_id = (held.diff().fillna(held) != 0).cumsum()
    rows = []
    for _, g in held[held == 1].groupby(run_id[held == 1]):
        rows.append({"start": g.index[0], "end": g.index[-1], "days": len(g),
                     "pnl": float(pnl.loc[g.index].sum())})
    return pd.DataFrame(rows)


def episode_stats(ep: pd.DataFrame, round_trip_cost: float) -> dict:
    if ep.empty:
        return {"trades": 0}
    p = ep["pnl"] - round_trip_cost
    wins, losses = p[p > 0], p[p <= 0]
    return {"trades": int(len(p)), "win_rate": round(float((p > 0).mean()), 4),
            "avg_pnl": round(float(p.mean()), 5), "median_pnl": round(float(p.median()), 5),
            "avg_win": round(float(wins.mean()), 5) if len(wins) else None,
            "avg_loss": round(float(losses.mean()), 5) if len(losses) else None,
            "profit_factor": round(float(wins.sum() / -losses.sum()), 3) if losses.sum() < 0 else None,
            "avg_holding_days": round(float(ep["days"].mean()), 2)}


def conditional(returns: pd.DataFrame, regime: pd.Series) -> pd.DataFrame:
    """Moments of each return column on day t+1, grouped by the regime decided at close t."""
    lab = regime.shift(1).reindex(returns.index)
    rows = []
    for col in returns.columns:
        for key, x in returns[col].groupby(lab):
            mu, sd = x.mean() * DAYS, x.std() * np.sqrt(DAYS)
            rows.append({"series": col, "regime": key, "share_of_days": round(len(x) / lab.notna().sum(), 4),
                         "days": int(len(x)), "excess_return_pa": round(float(mu), 4),
                         "volatility_pa": round(float(sd), 4), "sharpe": round(float(mu / sd), 3),
                         "kelly_fraction": round(float(mu / sd ** 2), 2)})
    return pd.DataFrame(rows)


def hurdle(components_: pd.DataFrame, portfolio: pd.Series) -> pd.DataFrame:
    """Adding weight to component k raises the portfolio Sharpe iff SR_k > rho(k, p) * SR_p."""
    sr = lambda x: x.mean() / x.std() * np.sqrt(DAYS)  # noqa: E731
    sp = sr(portfolio)
    rows = []
    for col in components_.columns:
        rho = components_[col].corr(portfolio)
        rows.append({"component": col, "sharpe": round(float(sr(components_[col])), 3),
                     "rho_with_strategy": round(float(rho), 3), "required_sharpe": round(float(rho * sp), 3),
                     "margin": round(float(sr(components_[col]) - rho * sp), 3)})
    return pd.DataFrame(rows)


def rotation_null(make_excess, indicator: pd.Series, period: slice, n: int = 500, seed: int = 7,
                  min_shift: int = 252) -> np.ndarray:
    """Sharpe distribution when the timing indicator is rotated circularly by a random offset.

    Keeps the share of active days and the persistence of the regime, destroys only its timing.
    """
    rng = np.random.default_rng(seed)
    v = indicator.to_numpy()
    out = np.empty(n)
    for i in range(n):
        k = int(rng.integers(min_shift, len(v) - min_shift))
        x = make_excess(pd.Series(np.roll(v, k), index=indicator.index)).loc[period]
        out[i] = x.mean() / x.std() * np.sqrt(DAYS)
    return out


def holm(pvals: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni adjusted p-values."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, run, out = len(items), 0.0, {}
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = round(run, 4)
    return out


# --------------------------------------------------------------------------- regimes

def regimes(c: dict) -> dict[str, pd.Series]:
    """Causal regime labels at each close (registered in research/LEVERAGE_HYPOTHESES.md)."""
    spy = c["spy_close"]
    r = c["R"]
    vol20 = r["SPY"].rolling(20).std() * np.sqrt(DAYS)
    vol_med = vol20.rolling(252).median()
    corr63 = r["SPY"].rolling(63).corr(r["TLT"])
    state = pd.Series("neutral", index=r.index)
    state[c["dip"] == 1] = "dip"
    state[c["overbought"] == 1] = "overbought"
    return {"book1_state": state,
            "spy_trend": pd.Series(np.where(spy > spy.rolling(200).mean(), "above_sma200", "below_sma200"),
                                   index=r.index).where(spy.rolling(200).mean().notna()),
            "spy_volatility": pd.Series(np.where(vol20 > vol_med, "high", "low"), index=r.index).where(vol_med.notna()),
            "stock_bond_corr": pd.Series(np.where(corr63 < 0, "negative", "positive"), index=r.index).where(corr63.notna())}
