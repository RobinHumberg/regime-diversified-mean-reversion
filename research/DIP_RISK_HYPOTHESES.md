# Dip-trade risk hypotheses — written down before the first number

Registered 2026-11-11, after `LEVERAGE_HYPOTHESES.md` and before any of the rules below was computed.

**Goal.** Make the losing dip trades of book 1 smaller, so that the dip overlay (or the whole
strategy) can carry more leverage for the same tail risk.

**What the analyst already knew when writing this.** `results/dip_trades.csv` (159 trades) and its
five worst trades: 2011-07-28 (11 days, −10.1 %), 2020-02-25 (5 days, −4.0 %), 2007-02-26
(7 days, −4.0 %), 2012-05-07 (11 days, −3.8 %), 2018-02-05 (6 days, −3.6 %). The average holding
period is 3.4 days. Long holding periods among the worst trades motivated D1. Nothing else about the
variants below has been computed. All data up to 2026-11-06 has been seen, so every result is
in-sample.

## Step 0 — descriptive, not a trial

Decompose the five largest drawdowns of C-A into the dip overlay (0.5 × (book 1 − SPY)) and the
rest. If the overlay contributes little to them, cutting dip-trade losses cannot buy much extra
leverage for the whole strategy, only for the overlay.

## Variants (7 trials, parameters fixed here)

Book 1 keeps its entry rule (RSI(2) < 10 and close > SMA200), its normal exit (close > SMA5)
and its overbought leg unchanged, except where stated. Book 2 and the 50/50 split are unchanged.
Every rule is decided at the close of t and held on t+1.

| ID | Change to the dip leg | Economic cause | Prediction |
|---|---|---|---|
| D1 | **Time stop:** leave the dip after 5 held days | Liquidity shocks revert within days (Nagel 2012). A dip that has not bounced after a week is more likely news than forced selling | Smaller worst trades, small cost in Sharpe |
| D2 | **Trend-break exit:** leave when close < SMA200 | The trade's premise (a dip inside a bull market) is gone | Cuts crash-type trades |
| D3 | **Price stop:** leave when close < entry close × (1 − 3 σ₂₀), σ₂₀ = 20-day daily SPY vol at entry | Classic stop-loss | **Hurts**: under mean reversion a stop sells at the worst moment (Kaminski & Lo 2014) |
| D4 | **Inverse-vol sizing:** extra exposure = min(1, 15 % / σ₂₀ annualised) instead of 1 | Equal risk per trade; the crash-type dips arrive with high volatility | Lower overlay volatility and tail, similar Sharpe |
| D5 | **VIX term-structure veto:** no new dip entry when VIX ≥ VIX3M at the close | Backwardation marks acute stress, where liquidity spirals continue (Brunnermeier & Pedersen 2009) | Avoids the worst entries, loses some of the best ones |
| D6 | **Rising-trend filter:** additionally require SMA200 today > SMA200 20 days ago | Dips in a flattening trend are closer to a regime break | Fewer, safer trades |
| D7 | **D1 + D2 with dip exposure 3.0** | The user's actual question: cut the tails, then lever the dip | Higher overlay return with a tail no worse than C-A |

## Metrics

- **Trade level (dip trades):** number, win rate, average, worst trade, mean of the worst 5 % of
  trades (CVaR 5 %), all per unit of book-1 capital, after costs and financing.
- **Overlay level:** Sharpe of book 1 − SPY.
- **Strategy level:** Sharpe, max drawdown, worst month, daily CVaR 1 %, and the leverage at
  which the strategy's max drawdown reaches −40 % together with the CAGR at that leverage.

## Success condition

A variant counts as a candidate for a forward registration if, in *both* 2007–2015 and
2016–2026-11, (a) its worst dip trade and its trade CVaR 5 % are better than C-A's and (b) its
overlay Sharpe is not lower than C-A's by more than 0.05; and the strategy Sharpe difference
against C-A is not significantly negative (paired test, Holm over 7 trials). Max drawdown is
reported, but it is a single-path statistic and is not part of the condition.
