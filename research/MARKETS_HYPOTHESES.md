# Other-markets hypotheses — written down before the first number

Registered 2026-11-14, before any return of the markets below was downloaded or computed.

**Question.** Is C-A an artefact of the US stock market of 2007–2026, or do its two mechanisms
(index dip reversal, cross-asset rebalancing) also pay in other equity markets — other US
segments, developed markets outside the US and emerging markets?

**What changes.** Only the equity asset. In each market m, SPY is replaced by a US-listed ETF on
that market *in book 1 and in book 2*. Everything else is C-A exactly as frozen: RSI(2) 10/90,
SMA 200/5, exposure in [0.5, 2.0], TLT and GLD as the other two thirds of book 2, month-end
rebalancing, 50/50 books, 1 bp per side, financing at T-bill + 1.5 %, Sharpe on excess returns over
the FRED 3-month T-bill. The investor is a US-dollar investor; all returns are in USD. Decision at
the US close of t, held on t+1 (the ETFs trade on the US calendar, so the rule stays causal).

**What the analyst already knew when writing this.** General market history to mid-2026: the US
outperformed most other markets after 2009, emerging markets had a weak decade (2011–2020),
China and Brazil had deep drawdowns, Japan and Europe recovered from 2023. No backtest of any of the
rules below on any of these ETFs has been computed in this repository. The period 2007–2026 is
not out-of-sample in time; it is out-of-sample only in the cross-section (these series played no
role in selecting C-A).

## Universe (19 markets, fixed here; SPY is the reference, not a witness)

ETFs with data since 2005 at the latest, so that every market covers the same window as C-A
(2007-02 – 2026-11-06, book-2 warm-up as in `books.build`).

| Group | ETFs |
|---|---|
| US segments | QQQ (Nasdaq-100), IWM (Russell 2000), MDY (S&P MidCap 400), DIA (Dow Jones 30), OEF (S&P 100) |
| Developed ex-US | EFA (MSCI EAFE), EZU (Eurozone), EWG (Germany), EWU (UK), EWJ (Japan), EWA (Australia), EWC (Canada) |
| Emerging | EEM (MSCI EM), EWZ (Brazil), FXI (China large caps), EWY (Korea), EWT (Taiwan), EWW (Mexico), EZA (South Africa) |

India (INDA 2012, EPI 2008) is excluded because it does not cover the window.

## Comparisons per market

- **C-A(m)** vs **buy & hold of m** (headline).
- **Book 1(m)** vs **buy & hold of m**: the dip overlay in isolation. C-A − "no overlay" (book 1
  replaced by buy & hold) equals 0.5 × (book 1 − buy & hold), so this is the overlay's contribution.
- **Book 2(m)** vs **drift(m)**: the same three assets bought in equal thirds at the book-2 start
  and never rebalanced. The difference is the rebalancing premium.

Paired Jobson-Korkie/Memmel test for each comparison. Pooled across markets: mean z-statistic
× √n_eff, with n_eff = n / (1 + (n − 1) · ρ̄), ρ̄ = mean pairwise correlation of the daily return
differences (CLAUDE.md rule 5). Sub-periods 2007–2015 and 2016–2026-11.

## Hypotheses and success conditions

| ID | Hypothesis | Economic cause | Prediction | Success condition |
|---|---|---|---|---|
| M1 | C-A beats buy & hold of the local market | Book 2 adds two assets with low equity correlation; this alone lowers volatility | Holds almost everywhere, strongest where the equity market had a low Sharpe (EM, Europe) | C-A Sharpe > buy & hold in ≥ 15 of 19 markets **and** pooled p < 0.10 |
| M2 | The dip overlay adds Sharpe outside SPY | Short-term index reversal is a liquidity-provision premium (Nagel 2012) that should exist wherever liquidity providers absorb selling pressure | **Weaker outside US large caps.** Emerging-market index returns have more positive short-horizon autocorrelation (non-synchronous trading of local constituents, slower information diffusion), which works against reversal; US-listed EM ETFs also mix currency moves into their dips | Book 1 Sharpe > buy & hold in ≥ 13 of 19 markets **and** pooled p < 0.10, in both sub-periods |
| M3 | Rebalancing adds Sharpe in every market | The diversification return ½(Σ wᵢσᵢ² − σ_p²) is mechanical and grows with asset volatility | Positive almost everywhere; larger for high-volatility equity (EM) | Book 2 Sharpe > drift in ≥ 13 of 19 markets; rank correlation between equity volatility and the book-2 − drift return difference > 0 |
| M4 | The result survives realistic costs | Turnover of C-A is about 10 × p.a.; EM ETFs have wider spreads (2–5 bp) | Break-even cost against buy & hold far above 5 bp for most markets | M1 count at 5 bp per side not lower than at 1 bp by more than 2 markets |

## What would count as "C-A generalises"

M1 and M2 both pass. M1 alone passing says only that a 1/3-bond, 1/3-gold portfolio diversifies an
equity market, which is not news. M2 is the test of the strategy-specific idea.

## What is reported regardless of outcome

Per-market table (Sharpe, CAGR, max drawdown, p-values, number of dip trades and their win rate),
group averages, n_eff, cost break-even, and figures. Failing markets are reported, not dropped. No
parameter is changed per market.
