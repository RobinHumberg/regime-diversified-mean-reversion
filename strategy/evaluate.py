"""Performance statistics on daily excess returns."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import stats

DAYS = 252


def sharpe(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(DAYS))


def sortino(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x[x < 0].std(ddof=1) * np.sqrt(DAYS))


def summary(excess: pd.Series, cash: pd.Series) -> dict:
    """Sharpe/Sortino on excess returns; CAGR and max drawdown on TOTAL returns (excess + cash)."""
    total = (excess + cash.reindex(excess.index)).dropna()
    eq = (1 + total).cumprod()
    return {"sharpe": round(sharpe(excess), 3), "sortino": round(sortino(excess), 3),
            "excess_return_pa": round(float(excess.mean() * DAYS), 4),
            "volatility_pa": round(float(excess.std() * np.sqrt(DAYS)), 4),
            "cagr_total": round(float(eq.iloc[-1] ** (DAYS / len(total)) - 1), 4),
            "max_drawdown_total": round(float((eq / eq.cummax() - 1).min()), 4),
            "days": int(len(excess))}


def paired_sharpe(a: pd.Series, b: pd.Series) -> dict:
    """Jobson-Korkie test with the Memmel (2003) correction for two DEPENDENT Sharpe ratios."""
    x, y = pd.concat([a, b], axis=1).dropna().T.to_numpy()
    n = len(x)
    sa, sb = x.mean() / x.std(ddof=1), y.mean() / y.std(ddof=1)
    rho = float(np.corrcoef(x, y)[0, 1])
    var = (2 * (1 - rho) + 0.5 * (sa ** 2 + sb ** 2 - 2 * rho ** 2 * sa * sb)) / n
    z = (sa - sb) / math.sqrt(var)
    k = math.sqrt(DAYS)
    return {"sharpe_a": round(sa * k, 3), "sharpe_b": round(sb * k, 3), "diff": round((sa - sb) * k, 3),
            "rho": round(rho, 3), "z": round(float(z), 2), "p_value": round(float(2 * (1 - stats.norm.cdf(abs(z)))), 4)}


def bootstrap_sharpe(x: pd.Series, n_boot: int = 2000, seed: int = 42) -> dict:
    """Percentile bootstrap (i.i.d. resampling) of the annualised Sharpe ratio."""
    r = x.dropna().to_numpy()
    rng = np.random.default_rng(seed)
    s = np.array([(lambda v: v.mean() / v.std(ddof=1))(rng.choice(r, len(r))) for _ in range(n_boot)]) * np.sqrt(DAYS)
    return {"ci_low": round(float(np.percentile(s, 2.5)), 3), "ci_high": round(float(np.percentile(s, 97.5)), 3)}
