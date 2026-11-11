"""The strategy: two mean-reversion books combined 50/50.

Book 1 (dip overlay): SPY exposure 1.0, raised to 2.0 after an oversold close in an uptrend
(Connors RSI(2) rule) and cut to 0.5 after an overbought close in a downtrend.
Book 2 (rebalancing premium): SPY / TLT / GLD in equal thirds, rebalanced at each month end.
Strategy C-A: 50 % of capital in each book.

Every decision uses data up to the close of day t and is held from day t+1. All returns
are EXCESS returns over the 3-month T-bill.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import closes, daily_cash

COST_PER_SIDE = 1e-4          # 1 bp of traded notional
MARGIN_SPREAD_PA = 0.015      # extra exposure above 1.0 is financed at T-bill + 1.5 %
CRP_ASSETS = ["SPY", "TLT", "GLD"]
CRP_START = "2005-01-01"
VOL_WINDOW = 252              # only used to align the start date with the research run
WARMUP_DAYS = 400


def rsi(close: pd.Series, n: int = 2) -> pd.Series:
    """Wilder RSI."""
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def connors_states(close: pd.Series) -> pd.DataFrame:
    """Dip and overbought states, decided at each close.

    dip:        enter when RSI(2) < 10 and close > SMA200; leave when close > SMA5
    overbought: enter when RSI(2) > 90 and close < SMA200; leave when close < SMA5
    """
    r2, s200, s5 = rsi(close), close.rolling(200).mean(), close.rolling(5).mean()
    dip, ob = np.zeros(len(close)), np.zeros(len(close))
    d = o = 0
    for t in range(len(close)):
        c, m200, m5, r = close.iloc[t], s200.iloc[t], s5.iloc[t], r2.iloc[t]
        if np.isnan(m200):
            d = o = 0
        else:
            d = 1 if (d == 0 and r < 10 and c > m200) else (0 if (d == 1 and c > m5) else d)
            o = 1 if (o == 0 and r > 90 and c < m200) else (0 if (o == 1 and c < m5) else o)
        dip[t], ob[t] = d, o
    return pd.DataFrame({"dip": dip, "overbought": ob}, index=close.index)


def dip_exposure(close: pd.Series) -> pd.Series:
    """Book-1 SPY exposure decided at each close: 1 + dip - 0.5 * overbought, within [0.5, 2]."""
    st = connors_states(close)
    return (1.0 + st["dip"] - 0.5 * st["overbought"]).clip(0.5, 2.0)


def exposure_book(exposure: pd.Series, ret: pd.Series, cash: pd.Series,
                  cost_per_side: float = COST_PER_SIDE, margin_spread_pa: float = MARGIN_SPREAD_PA) -> pd.Series:
    """Excess return of holding ``exposure`` x the asset (decided at close t, held on day t+1).

    total = held * r - cost + (1 - held) * cash - max(held - 1, 0) * spread; excess = total - cash.
    """
    held = exposure.shift(1).fillna(0.0)
    cost = held.diff().abs().fillna(held.abs()) * cost_per_side
    total = held * ret.fillna(0.0) - cost + (1 - held) * cash - (held - 1).clip(lower=0) * margin_spread_pa / 252
    return total - cash


def month_ends(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Last trading day of each month. The final day of the data counts only if the month is over.

    Without this rule the latest close of a running month would look like a month end and the
    live signal would rebalance every day.
    """
    s = pd.Series(idx, index=idx)
    me = pd.DatetimeIndex(s.groupby(idx.to_period("M")).max().to_numpy())
    last = idx[-1]
    if (last + pd.offsets.BDay(1)).month == last.month:
        me = me[me != last]
    return me


def crp_weights(R: pd.DataFrame) -> pd.DataFrame:
    """Book-2 weights at each close: reset to 1/3 each at month end, drifting with prices in between."""
    me = set(month_ends(R.index))
    Rv = R.fillna(0.0).to_numpy()
    W = np.zeros(R.shape)
    w = np.zeros(R.shape[1])
    for t, day in enumerate(R.index):
        if t > 0 and w.sum() > 0:
            w = w * (1 + Rv[t]) / (1 + w @ Rv[t])
        if day in me:
            w = np.full(R.shape[1], 1.0 / R.shape[1])
        W[t] = w
    return pd.DataFrame(W, index=R.index, columns=R.columns)


def weights_book(W: pd.DataFrame, R: pd.DataFrame, cash: pd.Series,
                 cost_per_side: float = COST_PER_SIDE, margin_spread_pa: float = MARGIN_SPREAD_PA) -> pd.Series:
    """Excess return of daily weights W (held from the next day), cost on exact drift turnover."""
    Wv, Rv, cv = W.to_numpy(), R.fillna(0.0).to_numpy(), cash.to_numpy()
    out = np.zeros(len(W))
    for t in range(1, len(W)):
        held = Wv[t - 1]
        c = 1.0 - held.sum()
        port = held @ Rv[t] + c * cv[t] - max(-c, 0.0) * margin_spread_pa / 252
        drifted = held * (1 + Rv[t]) / (1 + port)
        cost = cost_per_side * np.abs(Wv[t] - drifted).sum() if t < len(W) - 1 else 0.0
        out[t] = port - cost - cv[t]
    return pd.Series(out, index=W.index)


def build(end: str | None = None, crp_assets: list[str] | None = None,
          cost_per_side: float = COST_PER_SIDE, margin_spread_pa: float = MARGIN_SPREAD_PA) -> dict[str, pd.Series]:
    """Daily excess returns of book 1, book 2, the strategy (C-A) and SPY buy & hold.

    ``cost_per_side`` and ``margin_spread_pa`` exist for cost-sensitivity analysis only; the
    strategy is defined with the module defaults.
    """
    crp_assets = crp_assets or CRP_ASSETS
    spy = closes(["SPY"], end)["SPY"]
    r_spy = spy.pct_change().iloc[1:]
    spy = spy.loc[r_spy.index]
    cash_spy = daily_cash(r_spy.index)
    book1 = exposure_book(dip_exposure(spy), r_spy, cash_spy, cost_per_side, margin_spread_pa)

    px = closes(crp_assets, end).loc[CRP_START:].dropna()
    R = px.pct_change().iloc[1:]
    cash = daily_cash(R.index)
    first = R.rolling(VOL_WINDOW).std().dropna().index[0]
    book2 = weights_book(crp_weights(R), R, cash, cost_per_side, margin_spread_pa).loc[
        first + pd.Timedelta(days=WARMUP_DAYS):]

    both = pd.concat([book1.rename("book1"), book2.rename("book2")], axis=1).dropna()
    return {"book1": both["book1"], "book2": both["book2"], "strategy": both.mean(axis=1),
            "spy": (r_spy - cash_spy).loc[both.index]}


def target_portfolio(end: str | None = None) -> dict:
    """Weights to hold from the next session, per 1.0 of capital (for paper or live tracking)."""
    spy = closes(["SPY"], end)["SPY"].dropna()
    e = float(dip_exposure(spy).iloc[-1])
    st = connors_states(spy).iloc[-1]
    px = closes(CRP_ASSETS, end).loc[CRP_START:].dropna()
    w2 = crp_weights(px.pct_change().iloc[1:]).iloc[-1]
    total = {a: 0.5 * float(w2[a]) for a in CRP_ASSETS}
    total["SPY"] += 0.5 * e
    return {"as_of_close": str(spy.index[-1].date()), "book1_spy_exposure": e,
            "dip_state": int(st["dip"]), "overbought_state": int(st["overbought"]),
            "book2_weights": {a: round(float(w2[a]), 4) for a in CRP_ASSETS},
            "portfolio_weights": {a: round(v, 4) for a, v in total.items()},
            "cash_weight": round(1.0 - sum(total.values()), 4)}
