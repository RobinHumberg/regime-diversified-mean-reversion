"""Risk controls for the dip leg of book 1 (registered in research/DIP_RISK_HYPOTHESES.md).

``dip_exposure_variant`` is a generalisation of ``books.dip_exposure``: with every option at its
default it reproduces C-A exactly (tested). The overbought leg is never changed.

A forced exit (time stop, trend break, price stop) blocks re-entry until the normal exit
condition (close > SMA5) is met, so a stopped dip cannot re-enter on the next close.
Every decision uses data up to the close of t and is held on t+1.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .books import connors_states, rsi

DAYS = 252


def dip_exposure_variant(close: pd.Series, max_hold: int | None = None, trend_exit: bool = False,
                         stop_sigma: float | None = None, entry_ok: pd.Series | None = None,
                         size: pd.Series | float = 1.0, max_exposure: float = 2.0) -> pd.DataFrame:
    """Book-1 exposure with optional dip risk controls.

    max_hold:    leave the dip after this many held days
    trend_exit:  leave the dip when close < SMA200
    stop_sigma:  leave when close < entry close * (1 - stop_sigma * 20-day daily vol at entry)
    entry_ok:    boolean series; a new dip is entered only where it is True
    size:        extra exposure in a dip (scalar or series, frozen at the entry close)
    Returns columns ``exposure``, ``dip``, ``extra`` (extra exposure on dip days).
    """
    r2, s200, s5 = rsi(close), close.rolling(200).mean(), close.rolling(5).mean()
    vol20 = close.pct_change().rolling(20).std()
    ok = pd.Series(True, index=close.index) if entry_ok is None else entry_ok.reindex(close.index).fillna(True)
    sz = pd.Series(size, index=close.index) if np.isscalar(size) else size.reindex(close.index).fillna(1.0)
    ob = connors_states(close)["overbought"].to_numpy()
    n = len(close)
    dip, extra = np.zeros(n), np.zeros(n)
    d = blocked = held = 0
    entry_px = stop_px = x = 0.0
    for t in range(n):
        c, m200, m5, r = close.iloc[t], s200.iloc[t], s5.iloc[t], r2.iloc[t]
        if np.isnan(m200):
            d = blocked = 0
        elif d == 1:
            held += 1
            if c > m5:
                d = 0
            elif ((max_hold is not None and held >= max_hold) or (trend_exit and c < m200)
                  or (stop_sigma is not None and c < stop_px)):
                d, blocked = 0, 1
        else:
            if blocked and c > m5:
                blocked = 0
            if not blocked and r < 10 and c > m200 and ok.iloc[t]:
                d, held, entry_px, x = 1, 0, c, float(sz.iloc[t])
                stop_px = entry_px * (1 - stop_sigma * vol20.iloc[t]) if stop_sigma is not None else -np.inf
        dip[t], extra[t] = d, x * d
    exposure = np.clip(1.0 + extra - 0.5 * ob, 0.5, max_exposure)
    return pd.DataFrame({"exposure": exposure, "dip": dip, "extra": extra}, index=close.index)


def dip_trades(extra: pd.Series, r: pd.Series, cash: pd.Series, cost_per_side: float,
               margin_spread_pa: float) -> pd.DataFrame:
    """P&L of every dip episode per unit of book-1 capital (extra exposure, borrowed), after costs."""
    held = extra.shift(1).fillna(0.0)
    pnl = held * (r - cash - margin_spread_pa / DAYS)
    on = held > 0
    run_id = (on != on.shift()).cumsum()
    rows = []
    for _, g in held[on].groupby(run_id[on]):
        rows.append({"start": g.index[0], "end": g.index[-1], "days": len(g), "size": float(g.max()),
                     "pnl": float(pnl.loc[g.index].sum() - 2 * cost_per_side * g.max())})
    return pd.DataFrame(rows)


def trade_stats(tr: pd.DataFrame) -> dict:
    if tr.empty:
        return {"trades": 0}
    p = tr["pnl"].sort_values()
    k = max(1, int(np.ceil(0.05 * len(p))))
    return {"trades": int(len(p)), "win_rate": round(float((p > 0).mean()), 4),
            "avg_pnl": round(float(p.mean()), 5), "total_pnl": round(float(p.sum()), 4),
            "worst_trade": round(float(p.iloc[0]), 4), "cvar5_trade": round(float(p.iloc[:k].mean()), 4),
            "avg_holding_days": round(float(tr["days"].mean()), 2)}


def drawdowns(total: pd.Series, k: int = 5) -> list[tuple[pd.Timestamp, pd.Timestamp, float]]:
    """The k largest non-overlapping peak-to-trough drawdowns of a total-return series."""
    eq = (1 + total).cumprod()
    out, mask = [], pd.Series(True, index=eq.index)
    for _ in range(k):
        e = eq[mask]
        if len(e) < 2:
            break
        dd = e / e.cummax() - 1
        trough = dd.idxmin()
        peak = e.loc[:trough].idxmax()
        out.append((peak, trough, float(dd.min())))
        rec = eq.loc[trough:][eq.loc[trough:] >= eq.loc[peak]]
        end = rec.index[0] if len(rec) else eq.index[-1]
        mask.loc[peak:end] = False
    return out


def leverage_at_drawdown(make_excess, cash: pd.Series, budget: float = -0.40,
                         grid=np.round(np.arange(0.5, 4.01, 0.05), 2)) -> dict:
    """Highest leverage whose max drawdown stays within ``budget``, and the CAGR there."""
    best = None
    for L in grid:
        x = make_excess(L)
        eq = (1 + x + cash.reindex(x.index)).cumprod()
        if (eq / eq.cummax() - 1).min() < budget:
            break
        best = (float(L), float(eq.iloc[-1] ** (DAYS / len(eq)) - 1))
    return {"leverage": best[0], "cagr": round(best[1], 4)} if best else {"leverage": None, "cagr": None}
