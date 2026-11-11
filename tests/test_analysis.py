"""Self-checks for the diagnostics layer: simulator equivalence, costs, leverage, no look-ahead."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from strategy import analysis as A
from strategy.books import connors_states, crp_weights, dip_exposure, weights_book


def _synthetic(n: int = 900, seed: int = 1) -> dict:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2012-01-02", periods=n)
    R = pd.DataFrame(rng.normal(0.0003, [0.012, 0.009, 0.010], (n, 3)), index=idx, columns=["SPY", "TLT", "GLD"])
    spy = 100 * (1 + R["SPY"]).cumprod()
    st = connors_states(spy)
    return {"R": R, "cash": pd.Series(0.02 / 252, index=idx), "spy_close": spy,
            "exposure": dip_exposure(spy), "dip": st["dip"], "overbought": st["overbought"], "w2": crp_weights(R)}


def test_simulator_matches_weights_book():
    c = _synthetic()
    W = A.book_weights(c)
    a = A.simulate(W, c["R"], c["cash"])["excess"]
    b = weights_book(W, c["R"], c["cash"])
    pd.testing.assert_series_equal(a.iloc[1:-1], b.iloc[1:-1], check_names=False)


def test_trading_cost_enters_linearly():
    c = _synthetic()
    W = A.book_weights(c)
    s0 = A.simulate(W, c["R"], c["cash"], cost_per_side=0.0)
    s5 = A.simulate(W, c["R"], c["cash"], cost_per_side=5e-4)
    pd.testing.assert_series_equal(s5["excess"], s0["excess"] - 5e-4 * s0["turnover"], check_names=False)


def test_leverage_scales_excess_returns_without_frictions():
    c = _synthetic()
    W = A.book_weights(c)
    one = A.simulate(W, c["R"], c["cash"], cost_per_side=0.0, margin_spread_pa=0.0)["excess"]
    two = A.simulate(2 * W, c["R"], c["cash"], cost_per_side=0.0, margin_spread_pa=0.0)["excess"]
    np.testing.assert_allclose(two.to_numpy(), 2 * one.to_numpy(), atol=1e-12)


def test_financing_is_charged_on_net_borrowing_only():
    idx = pd.bdate_range("2020-01-01", periods=3)
    R = pd.DataFrame({"A": [0.0, 0.0, 0.0]}, index=idx)
    zero = pd.Series(0.0, index=idx)
    x = A.simulate(pd.DataFrame({"A": [1.5, 1.5, 1.5]}, index=idx), R, zero, cost_per_side=0.0)
    assert x["excess"].iloc[1] == pytest.approx(-0.5 * 0.015 / 252)
    y = A.simulate(pd.DataFrame({"A": [0.8, 0.8, 0.8]}, index=idx), R, zero, cost_per_side=0.0)
    assert y["excess"].iloc[1] == pytest.approx(0.0)


def test_regimes_have_no_lookahead():
    c = _synthetic()
    cut = c["R"].index[700]
    trunc = {k: (v.loc[:cut] if hasattr(v, "loc") else v) for k, v in c.items()}
    full, part = A.regimes(c), A.regimes(trunc)
    for k in full:
        pd.testing.assert_series_equal(full[k].loc[:cut], part[k], check_names=False)


def test_conditional_uses_the_regime_of_the_previous_close():
    idx = pd.bdate_range("2020-01-01", periods=4)
    ret = pd.DataFrame({"x": [0.0, 0.01, -0.02, 0.03]}, index=idx)
    reg = pd.Series(["a", "b", "a", "b"], index=idx)
    out = A.conditional(ret, reg).set_index("regime")
    assert out.loc["a", "days"] == 2 and out.loc["b", "days"] == 1   # day 0 has no previous close


def test_episodes_and_holm():
    idx = pd.bdate_range("2020-01-01", periods=8)
    state = pd.Series([0, 1, 1, 0, 0, 1, 0, 0], index=idx)
    pnl = pd.Series(0.01, index=idx)
    ep = A.episodes(state, pnl)
    assert ep["days"].tolist() == [2, 1] and ep["start"].iloc[0] == idx[2]
    assert A.holm({"a": 0.01, "b": 0.04, "c": 0.03}) == {"a": 0.03, "c": 0.06, "b": 0.06}


@pytest.mark.network
def test_simulator_reproduces_the_strategy():
    from strategy.books import build
    end = "2026-11-06"
    s = build(end)["strategy"]
    c = A.components(end)
    x = A.simulate(A.book_weights(c), c["R"], c["cash"])["excess"].loc[s.index]
    assert (x - s).abs().max() < 2e-4                      # only the inter-book rebalancing cost differs
    sr = lambda v: v.mean() / v.std() * np.sqrt(252)      # noqa: E731
    assert sr(x.loc["2023-11-01":]) == pytest.approx(sr(s.loc["2023-11-01":]), abs=0.005)
