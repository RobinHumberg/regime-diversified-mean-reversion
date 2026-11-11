# CLAUDE.md — Handoff for an AI agent continuing this work

You are picking up a finished research result. Read this whole file before changing anything.

## What this repository is

One frozen trading strategy, "C-A", and nothing else: 50 % SPY with a Connors RSI(2) dip overlay
(book 1) plus 50 % of an equal-weight SPY/TLT/GLD portfolio rebalanced at month ends (book 2). The
exact rules are in `README.md` → "Exact rules" and in `strategy/books.py`. The README is the
human-facing description; this file tells you how to work on it without destroying its evidence.

## Status of the evidence (do not overstate it)

- Holdout 2023-11-01 – 2026-11-06, evaluated ONCE after the selection was frozen: Sharpe 1.417 vs
  SPY 1.092, paired p = 0.165. "Beats SPY" yes; "clearly beats" (pre-defined as ≥ +0.25 AND p < 0.10) NO.
- Chosen from 34 pre-registered candidates over seven rounds; Deflated Sharpe 0.78.
- The 50/50 combination was formed after seeing both books' validation segments, so validation
  (2016-01 – 2023-10) is in-sample for the combination.
- The model that did the research knew market history until about mid-2026, including the gold
  rally, so the holdout is not perfectly blind. No-gold diagnostic: 1.22. Truly unseen data begins
  around 2026-07.
- **The holdout is spent.** Every period up to 2026-11-06 has been looked at. Any new idea tested on
  that data is in-sample, whatever you call it.

## Rules for working here

1. **The rules are frozen.** Do not tune thresholds (10/90 RSI, SMA 200/5, 0.5/2.0 bounds, 1/3
   weights, 50/50, month-end timing). A change makes a *new* strategy that has no out-of-sample
   evidence at all. If you want to test a change, write it down first (what, why, the economic cause,
   the success condition), keep C-A unchanged next to it, and evaluate the change only on data after
   its registration date.
2. **Decision at close t, held on t+1.** Never use a same-day price in a signal. `tests/
   test_strategy.py::test_no_lookahead_in_signals` must keep passing; add such a test for every new
   signal.
3. **Report Sharpe on excess returns** over the FRED DTB3 T-bill. Credit cash and charge financing
   exactly as `strategy/books.py` does. Report CAGR and drawdown on TOTAL returns (excess + cash).
4. **Compare dependent Sharpes with the paired test** (`evaluate.paired_sharpe`), never by eyeballing.
5. **Several correlated markets are not several witnesses.** If you replicate on other indices,
   compute n_eff = n / (1 + (n−1)·mean pairwise correlation) of the return differences.
6. **Costs stay modelled** (1 bp per side). If a variant only works without costs, it does not work.

## Reproduce before you do anything else

`python run_backtest.py` must print (data until 2026-11-06; later downloads may differ by ±0.01
because Yahoo revises adjusted prices):

| period | strategy | SPY | p |
|---|---:|---:|---:|
| 2007–2015 | 0.626 | 0.352 | 0.026 |
| 2016–2019 | 1.133 | 1.003 | 0.563 |
| 2020–2023-10 | 0.516 | 0.405 | 0.550 |
| holdout from 2023-11 | 1.417 | 1.092 | 0.165 |

If your numbers differ by more than about 0.03, find out why (stale cache, changed yfinance
behaviour, a calendar change) before you trust anything else. `results/backtest.json` is the
reference.

## The open task: a forward test

The only way to reach a statistically clear verdict is new data. Suggested protocol:

1. After each US close, run `python signal_today.py` and append its JSON plus the date to a ledger
   (e.g. `forward/ledger.jsonl`). Never edit past ledger rows.
2. Each month, compute the forward Sharpe of C-A vs SPY from the first ledger date, using the same
   accounting as `strategy/books.py` (or recompute with `build()` and slice from the start date; the
   rules are causal, so this is equivalent, provided the code did not change).
3. Pre-register the evaluation point now: for example, after 24 months of forward data, combined with
   the holdout, run `paired_sharpe` on 2023-11 → today. Do not peek-and-stop earlier because it looks good.
4. Track the regime risks: rolling 252-day SPY–TLT correlation (book 2 weakens when it turns
   positive, as in 2022) and the number of dip signals per year (book 1 does nothing without them).

## Diagnostics layer (costs, win rates, leverage)

`run_analysis.py` + `strategy/analysis.py` add gross/net, cost sensitivity, win rates, static
leverage and six leverage-timing variants. They do not change C-A.

- `analysis.simulate` rebuilds C-A from its target weights (daily rebalancing, same cost and
  financing accounting as `books.py`). It matches `build()` to within 0.6 bp p.a.; the test
  `tests/test_analysis.py::test_simulator_reproduces_the_strategy` guards this. Use it whenever
  you scale positions (leverage, per-book weights) instead of multiplying return series, which
  would skip financing and turnover costs.
- The data end is frozen at 2026-11-06 in `run_analysis.py`, so its numbers match
  `results/backtest.json`.
- The leverage variants V1–V6 were registered in `research/LEVERAGE_HYPOTHESES.md` before they
  were computed. All are in-sample; none met its registered condition. V2 (1.5 × when SPY > SMA200)
  is the only one with a raw rotation-null p < 0.05 (Holm 0.25). If you want to pursue it, register
  it as a forward test next to C-A — do not adopt it on the backtest.
- Reference values: net Sharpe 2007–2026 0.776 (gross 0.788), turnover 10 × p.a., break-even
  trading cost vs SPY 35.6 bp per side, dip-trade win rate 72.3 % (159 trades).

## Known pitfalls

- `month_ends` must not treat the last close of a running month as a month end. Otherwise the live
  signal rebalances every day. This is fixed and tested (`test_running_month_is_not_a_month_end`).
- yfinance caches can silently stop updating. `strategy/data.py` re-downloads when the cached series
  ends more than 5 business days ago. Check the last date of every series when results look odd.
- GLD starts in 2004-11 and TLT in 2002-07. Book 2 therefore starts in 2007 (252-day warm-up plus
  400 days, aligned with the research run). Do not backfill with other assets.
- Daily Sharpe ratios of 2+ on a 3-year window are noise-heavy. The bootstrap CI is [0.34, 2.47].

## Background you may need

- Rebalancing premium: Booth & Fama (1992); Erb & Harvey (2006); diversification return
  ½(Σ wᵢσᵢ² − σ_p²).
- Index reversal as liquidity provision: Lehmann (1990); Nagel (2012).
- Connors RSI(2): Connors & Alvarez, "Short Term Trading Strategies That Work" (2008).
- Stock–bond correlation regimes: Campbell, Sunderam & Viceira (2017).
- What failed and why: see README → "Research provenance".
