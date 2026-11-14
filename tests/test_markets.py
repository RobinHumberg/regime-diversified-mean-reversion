"""Other-markets layer: SPY equivalence, drift book, dip-trade counting and n_eff."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from strategy.books import weights_book
from strategy.markets import MARKETS, build_market, dip_trade_stats, drift_weights, n_eff


def test_drift_book_never_trades_after_the_start():
    idx = pd.bdate_range("2021-01-01", periods=60)
    rng = np.random.default_rng(3)
    R = pd.DataFrame(rng.normal(0, 0.01, (60, 3)), index=idx, columns=list("ABC"))
    W = drift_weights(R)
    assert W.iloc[0].tolist() == pytest.approx([1 / 3] * 3)
    assert W.sum(axis=1).to_numpy() == pytest.approx(np.ones(60))
    zero = pd.Series(0.0, index=idx)
    gross = weights_book(W, R, zero, cost_per_side=0.0)
    net = weights_book(W, R, zero)
    assert (gross - net).abs().max() < 1e-12


def test_dip_trades_are_counted_per_episode_and_held_from_the_next_day():
    idx = pd.bdate_range("2022-01-03", periods=8)
    dip = pd.Series([0, 1, 1, 0, 0, 1, 0, 0], index=idx, dtype=float)
    r = pd.Series([0.0, 0.5, 0.01, 0.02, 0.5, 0.5, -0.03, 0.5], index=idx)
    s = dip_trade_stats(dip, r)
    assert s["trades"] == 2
    assert s["win_rate"] == pytest.approx(0.5)
    assert s["avg_trade"] == pytest.approx(((1.01 * 1.02 - 1) + (-0.03)) / 2, abs=1e-4)


def test_n_eff_bounds():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(5000, 1))
    same = pd.DataFrame(np.repeat(x, 4, axis=1))
    indep = pd.DataFrame(rng.normal(size=(5000, 4)))
    assert n_eff(same)[0] == pytest.approx(1.0)
    assert n_eff(indep)[0] == pytest.approx(4.0, abs=0.1)


def test_universe_is_the_registered_one():
    witnesses = [t for t, (_, g) in MARKETS.items() if g != "Reference"]
    assert len(witnesses) == 19 and MARKETS["SPY"][1] == "Reference"


@pytest.mark.network
def test_spy_reproduces_the_strategy():
    from strategy.books import build

    a, b = build("2026-11-06"), build_market("SPY", "2026-11-06")
    for k, j in [("book1", "book1"), ("book2", "book2"), ("strategy", "strategy"), ("spy", "market")]:
        assert (a[k] - b[j]).abs().max() < 1e-12
