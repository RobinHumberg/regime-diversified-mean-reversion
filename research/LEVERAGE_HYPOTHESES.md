# Leverage hypotheses — written down before the first number

Registered 2026-11-11, before `run_analysis.py` produced any leverage result.

**Status of the data.** Every day up to 2026-11-06 has already been looked at during the
research that produced C-A. Nothing below is out-of-sample. These are *diagnostics* that say
where leverage is economically plausible, not new strategies. A variant that looks good here
must be registered again and earn its evidence on data after its registration date, exactly as
`CLAUDE.md` demands for any change to C-A. C-A itself is not changed.

## What is measured, and why

1. **Static leverage L × C-A** for L ∈ {0.5, 1, 1.25, 1.5, 1.75, 2, 2.5, 3}. Static leverage
   does not change the Sharpe ratio (apart from financing and costs), only return, volatility
   and drawdown. Shows the price of leverage and the empirical growth-optimal (Kelly) level.
2. **Conditional "moments".** Excess return, volatility, Sharpe and the Kelly fraction μ/σ²
   of C-A, book 1, book 2, SPY, TLT and GLD inside causal regimes: book-1 state
   (dip / overbought / neutral), SPY trend (close vs SMA200), volatility (trailing 20-day SPY
   volatility above or below its trailing 252-day median) and stock–bond correlation (trailing
   63-day SPY–TLT correlation above or below 0). Descriptive only.
3. **Component hurdle.** Raising the weight of component k raises the portfolio Sharpe iff
   SR_k > ρ(k, C-A) · SR_C-A. Reported for each component, separately for 2007–2015 and
   2016–2026-11, so the stability of the answer is visible.

## Timing variants (6 trials, parameters fixed here, no tuning)

All variants start from the C-A target weights, are decided at the close of t, held on t+1,
rebalanced daily, pay 1 bp per side on exact turnover and T-bill + 1.5 % on borrowed money.

| ID | Rule | Economic cause |
|---|---|---|
| V1 | C-A × min(10 % / σ̂, 2), σ̂ = trailing 20-day realised vol of C-A | Volatility clusters but expected returns do not rise with it (Moreira & Muir 2017) |
| V2 | C-A × 1.5 when SPY > SMA200, else × 1.0 | Uptrends are low-vol, positive-drift regimes; drawdowns of levered equity cluster below the trend (Faber 2007) |
| V3 | Book 2 × 1.5 (book 1 unchanged) | Low-volatility, diversified assets earn more per unit of risk under leverage aversion (Frazzini & Pedersen 2014; Asness, Frazzini & Pedersen 2012) |
| V4 | Book 2 × 1.5 only when trailing 63-day SPY–TLT correlation < 0 | The diversification return needs a negative stock–bond correlation (Campbell, Sunderam & Viceira 2017) |
| V5 | Book-1 dip exposure 3.0 instead of 2.0 (always) | The reversal is a liquidity-provision premium; the overlay already levers there |
| V6 | Book-1 dip exposure 3.0 only when trailing 20-day SPY vol > its trailing 252-day median | The liquidity-provision premium rises with volatility (Nagel 2012) |

**Success condition (for a later forward registration, not for a decision now):** Sharpe above
C-A in *both* 2007–2015 and 2016–2026-11 and a rotation-null p < 0.10 after Holm correction
over the 6 trials. Static leverage is not a trial: it cannot change the Sharpe.

**Null.** For the regime-timed variants (V2, V4, V6) the regime indicator is rotated circularly
by a random offset (500 rotations). This keeps the share of levered days and the persistence of
the regime, and destroys only its timing. For V1 the leverage series is rotated the same way.
V3 and V5 have no timing component; they are judged by the paired Sharpe test against C-A.
