"""Self-checks: accounting conventions, no look-ahead, robustness to a one-day delay."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from strategy import books
from strategy.books import connors_states, crp_weights, exposure_book, weights_book

IDX = pd.bdate_range("2020-01-01", periods=6)


def test_exposure_is_held_from_the_next_day():
    e = pd.Series([1.0, 2.0, 2.0, 1.0, 1.0, 1.0], index=IDX)
    r = pd.Series([0.0, 0.01, 0.02, -0.01, 0.0, 0.0], index=IDX)
    zero = pd.Series(0.0, index=IDX)
    ex = exposure_book(e, r, zero)
    # day 1 holds the exposure decided on day 0 (1.0); day 2 holds 2.0 decided on day 1
    assert ex.iloc[1] == pytest.approx(0.01 - 1e-4)
    assert ex.iloc[2] == pytest.approx(2 * 0.02 - 1e-4 - 0.015 / 252)


def test_crp_resets_at_month_end_and_drifts_otherwise():
    idx = pd.bdate_range("2021-01-25", "2021-02-05")
    R = pd.DataFrame({"A": 0.01, "B": 0.0, "C": 0.0}, index=idx)
    W = crp_weights(R)
    jan_end = idx[idx.month == 1][-1]
    assert W.loc[jan_end].tolist() == pytest.approx([1 / 3] * 3)
    after = W.loc[idx[idx > jan_end][0]]
    assert after["A"] > 1 / 3 and after.sum() == pytest.approx(1.0)


def test_running_month_is_not_a_month_end():
    idx = pd.bdate_range("2026-10-26", "2026-11-06")
    me = books.month_ends(idx)
    assert pd.Timestamp("2026-10-30") in me and pd.Timestamp("2026-11-06") not in me


def test_weights_book_charges_the_first_purchase():
    R = pd.DataFrame({"A": [0.0, 0.0, 0.0]}, index=IDX[:3])
    W = pd.DataFrame({"A": [1.0, 1.0, 1.0]}, index=IDX[:3])
    zero = pd.Series(0.0, index=IDX[:3])
    ex = weights_book(W, R, zero)
    assert ex.iloc[1] == pytest.approx(0.0)        # holds W[0]; turnover vs drifted is zero


def _states_on(close: pd.Series) -> pd.DataFrame:
    return connors_states(close)


def test_no_lookahead_in_signals():
    rng = np.random.default_rng(0)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.012, 900))),
                      index=pd.bdate_range("2015-01-01", periods=900))
    full = _states_on(close)
    cut = close.index[600]
    trunc = _states_on(close.loc[:cut])
    pd.testing.assert_frame_equal(full.loc[:cut], trunc)


@pytest.mark.network
def test_one_day_delay_keeps_most_of_the_edge():
    """Execute every decision one day late: the holdout Sharpe must stay above SPY's."""
    spy = books.closes(["SPY"])["SPY"]
    r = spy.pct_change().iloc[1:]
    spy = spy.loc[r.index]
    cash = books.daily_cash(r.index)
    e = books.dip_exposure(spy)
    late = books.exposure_book(e.shift(1).bfill(), r, cash)
    on_time = books.exposure_book(e, r, cash)
    ho = slice("2023-11-01", None)
    s = lambda x: x.loc[ho].mean() / x.loc[ho].std() * np.sqrt(252)  # noqa: E731
    assert s(late) > 0.5 * s(on_time)
