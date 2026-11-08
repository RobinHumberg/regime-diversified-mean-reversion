"""Reproduce every reported number: pre-validation, validation, holdout, by year.

Run: python run_backtest.py            (writes results/backtest.json)
"""
from __future__ import annotations

import json
from pathlib import Path

from strategy.books import build
from strategy.data import daily_cash
from strategy.evaluate import bootstrap_sharpe, paired_sharpe, summary

PERIODS = {
    "pre_validation_2007_2015": ("2007-01-01", "2015-12-31"),
    "validation_2016_2019": ("2016-01-01", "2019-12-31"),
    "validation_2020_2023_10": ("2020-01-01", "2023-10-31"),
    "validation_full": ("2016-01-01", "2023-10-31"),
    "holdout_2023_11_onwards": ("2023-11-01", None),
}


def main() -> None:
    s = build()
    cash = daily_cash(s["strategy"].index)
    out = {"data_end": str(s["strategy"].index[-1].date()), "periods": {}, "holdout_by_year": {}}
    for name, (a, b) in PERIODS.items():
        st, spy = s["strategy"].loc[a:b], s["spy"].loc[a:b]
        out["periods"][name] = {"strategy": summary(st, cash), "spy": summary(spy, cash),
                                "paired_test": paired_sharpe(st, spy)}
    ho = s["strategy"].loc["2023-11-01":]
    out["holdout_bootstrap_ci"] = bootstrap_sharpe(ho)
    out["holdout_aged_one_day_note"] = "see tests/test_strategy.py::test_one_day_delay"
    for y in sorted(set(ho.index.year)):
        out["holdout_by_year"][str(y)] = {"strategy": summary(s["strategy"].loc[str(y)], cash)["sharpe"],
                                          "spy": summary(s["spy"].loc[str(y)], cash)["sharpe"]}
    Path("results").mkdir(exist_ok=True)
    Path("results/backtest.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    for name, v in out["periods"].items():
        p = v["paired_test"]
        print(f"{name:26s} strategy {v['strategy']['sharpe']:+.3f}  SPY {v['spy']['sharpe']:+.3f}  "
              f"diff {p['diff']:+.3f}  p {p['p_value']:.3f}")
    print("holdout by year:", out["holdout_by_year"])


if __name__ == "__main__":
    main()
