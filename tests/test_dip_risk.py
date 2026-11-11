"""Self-checks for the dip risk controls."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from strategy import dip_risk as D
from strategy.books import dip_exposure


def _close(n: int = 1500, seed: int = 3) -> pd.Series:
    rng = np.random.default_rng(seed)
    return pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0004, 0.013, n))), index=pd.bdate_range("2010-01-01", periods=n))


def test_defaults_reproduce_the_frozen_rule():
    close = _close()
    pd.testing.assert_series_equal(D.dip_exposure_variant(close)["exposure"], dip_exposure(close), check_names=False)


def test_no_lookahead_for_every_control():
    close = _close()
    gate = close.pct_change().rolling(10).mean() > 0
    cut = close.index[1100]
    for kw in ({"max_hold": 5}, {"trend_exit": True}, {"stop_sigma": 3.0}, {"entry_ok": gate},
               {"size": 0.5 + close.pct_change().abs().rolling(20).mean() * 20}):
        full = D.dip_exposure_variant(close, **kw)
        trunc = D.dip_exposure_variant(close.loc[:cut], **{k: (v.loc[:cut] if isinstance(v, pd.Series) else v) for k, v in kw.items()})
        pd.testing.assert_frame_equal(full.loc[:cut], trunc)


def test_time_stop_holds_at_most_n_days_and_blocks_reentry():
    close = _close()
    ex = D.dip_exposure_variant(close, max_hold=2)
    runs = (ex["dip"] != ex["dip"].shift()).cumsum()
    assert ex["dip"].groupby(runs).sum().max() <= 2          # state set on <= 2 closes = <= 2 held days
    base = D.dip_exposure_variant(close)
    assert ex["dip"].sum() <= base["dip"].sum()


def test_dip_trades_charge_size_and_financing():
    idx = pd.bdate_range("2020-01-01", periods=5)
    extra = pd.Series([0, 2.0, 2.0, 0, 0], index=idx)
    r = pd.Series([0, 0, 0.01, 0.01, 0], index=idx)
    zero = pd.Series(0.0, index=idx)
    tr = D.dip_trades(extra, r, zero, cost_per_side=1e-4, margin_spread_pa=0.0)
    assert len(tr) == 1 and tr["days"].iloc[0] == 2
    assert tr["pnl"].iloc[0] == pytest.approx(2 * 0.01 + 2 * 0.01 - 2 * 1e-4 * 2)


def test_drawdowns_are_non_overlapping():
    total = pd.Series([0.0, -0.1, 0.2, -0.05, -0.05, 0.3, -0.2, 0.0], index=pd.bdate_range("2020-01-01", periods=8))
    dds = D.drawdowns(total, k=3)
    assert dds[0][2] < -0.19 and all(a[1] < b[0] or b[1] < a[0] for i, a in enumerate(dds) for b in dds[i + 1:])
