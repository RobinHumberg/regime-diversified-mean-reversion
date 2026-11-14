"""C-A with the equity asset swapped for another market (registered in research/MARKETS_HYPOTHESES.md).

Only the equity ETF changes, in book 1 and in book 2. Every rule, cost and the cash accounting are
those of `books.py`, so ``build_market("SPY")`` reproduces ``books.build()``.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .books import (COST_PER_SIDE, CRP_START, MARGIN_SPREAD_PA, VOL_WINDOW, WARMUP_DAYS, connors_states,
                    crp_weights, dip_exposure, exposure_book, weights_book)
from .data import closes, daily_cash

DIVERSIFIERS = ["TLT", "GLD"]

MARKETS: dict[str, tuple[str, str]] = {
    "SPY": ("S&P 500", "Reference"),
    "QQQ": ("Nasdaq-100", "US segments"),
    "IWM": ("Russell 2000", "US segments"),
    "MDY": ("S&P MidCap 400", "US segments"),
    "DIA": ("Dow Jones 30", "US segments"),
    "OEF": ("S&P 100", "US segments"),
    "EFA": ("MSCI EAFE", "Developed ex-US"),
    "EZU": ("Eurozone", "Developed ex-US"),
    "EWG": ("Germany", "Developed ex-US"),
    "EWU": ("United Kingdom", "Developed ex-US"),
    "EWJ": ("Japan", "Developed ex-US"),
    "EWA": ("Australia", "Developed ex-US"),
    "EWC": ("Canada", "Developed ex-US"),
    "EEM": ("MSCI Emerging", "Emerging"),
    "EWZ": ("Brazil", "Emerging"),
    "FXI": ("China large caps", "Emerging"),
    "EWY": ("South Korea", "Emerging"),
    "EWT": ("Taiwan", "Emerging"),
    "EWW": ("Mexico", "Emerging"),
    "EZA": ("South Africa", "Emerging"),
}


def drift_weights(R: pd.DataFrame) -> pd.DataFrame:
    """Equal thirds bought at the first close of ``R`` and never rebalanced."""
    g = (1 + R.fillna(0.0)).cumprod()
    g = g / g.iloc[0]
    return g.div(g.sum(axis=1), axis=0)


def build_market(equity: str, end: str | None = None, cost_per_side: float = COST_PER_SIDE,
                 margin_spread_pa: float = MARGIN_SPREAD_PA) -> dict[str, pd.Series]:
    """Daily excess returns of book 1, book 2, C-A, buy & hold and the never-rebalanced drift book.

    Also returns ``dip`` (dip state decided at each close) for trade statistics.
    """
    px_eq = closes([equity], end)[equity].dropna()
    r_eq = px_eq.pct_change().iloc[1:]
    px_eq = px_eq.loc[r_eq.index]
    cash_eq = daily_cash(r_eq.index)
    book1 = exposure_book(dip_exposure(px_eq), r_eq, cash_eq, cost_per_side, margin_spread_pa)

    px = closes([equity] + DIVERSIFIERS, end).loc[CRP_START:].dropna()
    R = px.pct_change().iloc[1:]
    cash = daily_cash(R.index)
    first = R.rolling(VOL_WINDOW).std().dropna().index[0]
    start = first + pd.Timedelta(days=WARMUP_DAYS)
    book2 = weights_book(crp_weights(R), R, cash, cost_per_side, margin_spread_pa).loc[start:]
    Rs = R.loc[start:]
    drift = weights_book(drift_weights(Rs), Rs, cash.loc[Rs.index], cost_per_side, margin_spread_pa)

    both = pd.concat([book1.rename("book1"), book2.rename("book2")], axis=1).dropna()
    idx = both.index
    return {"book1": both["book1"], "book2": both["book2"], "strategy": both.mean(axis=1),
            "market": (r_eq - cash_eq).loc[idx], "drift": drift.reindex(idx),
            "dip": connors_states(px_eq)["dip"].reindex(idx)}


def dip_trade_stats(dip: pd.Series, market_excess: pd.Series) -> dict:
    """Count and win rate of dip episodes, judged by the market's excess return while held."""
    held = dip.shift(1).fillna(0.0)
    run_id = (held.diff().fillna(held) == 1).cumsum().where(held == 1)
    pnl = market_excess.groupby(run_id).apply(lambda x: float(np.prod(1 + x) - 1))
    return {"trades": int(len(pnl)), "win_rate": round(float((pnl > 0).mean()), 3) if len(pnl) else None,
            "avg_trade": round(float(pnl.mean()), 4) if len(pnl) else None}


def n_eff(diffs: pd.DataFrame) -> tuple[float, float]:
    """Effective number of independent markets and the mean pairwise correlation of the columns."""
    c = diffs.dropna().corr().to_numpy()
    n = c.shape[0]
    rho = float(c[np.triu_indices(n, 1)].mean())
    return n / (1 + (n - 1) * rho), rho
