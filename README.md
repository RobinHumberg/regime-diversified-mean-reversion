# Regime-Diversified Mean Reversion

A long-only, daily-rebalanced US portfolio that combines two **mean-reversion** mechanisms with opposite regimes:

1. **Index dip overlay (book 1).** Hold SPY. After an oversold close in an uptrend, double the exposure until the bounce. After an overbought close in a downtrend, halve it.
2. **Cross-asset rebalancing premium (book 2).** Hold SPY, long Treasuries (TLT) and gold (GLD) in equal thirds and rebalance back at every month end. Rebalancing sells relative winners and buys relative losers, which is the most robust mean-reversion rule we found.

The strategy puts **50 % of capital in each book**.

In a holdout period that was not touched until the strategy was selected and frozen (**2023-11-01 to 2026-11-06**), it beat the S&P 500 on a risk-adjusted basis. The difference is not statistically significant. Read the caveats below before relying on it.

| Holdout 2023-11-01 – 2026-11-06 (757 trading days) | Strategy | SPY (S&P 500) |
|---|---:|---:|
| Sharpe ratio (excess over 3-month T-bill) | **1.42** | 1.09 |
| Sortino ratio | 2.01 | 1.42 |
| Volatility p.a. | 13.1 % | 15.4 % |
| CAGR (total return) | 24.6 % | 22.1 % |
| Max drawdown (total return) | −12.9 % | −18.8 % |
| Paired Sharpe test (Jobson-Korkie / Memmel) | diff +0.33, ρ 0.92, **p = 0.165** | |
| Bootstrap 95 % CI of the Sharpe | [0.34, 2.47] | |

## Results in every period

| Period | Role | Strategy Sharpe | SPY Sharpe | Strategy max DD | SPY max DD |
|---|---|---:|---:|---:|---:|
| 2007 – 2015 | pre-validation check | 0.63 | 0.35 | −32.4 % | −55.2 % |
| 2016 – 2019 | validation, segment 1 | 1.13 | 1.00 | −14.9 % | −19.4 % |
| 2020 – 2023-10 | validation, segment 2 | 0.52 | 0.41 | −23.6 % | −33.7 % |
| **2023-11 – 2026-11** | **holdout (one run)** | **1.42** | **1.09** | −12.9 % | −18.8 % |

Holdout Sharpe by calendar year: 2024 1.79 vs 1.44, 2025 1.33 vs 0.73, 2026 (to Nov 6) 0.43 vs 0.51.

The strategy has lower volatility and smaller drawdowns than SPY in every period. In the calm bull market of 2016–2019 its *return* was lower than SPY's (12.8 % vs 14.3 % CAGR), but its risk was lower by more.

## Honest caveats

- **Not statistically significant.** Before the holdout, "clearly beats" was defined as a Sharpe at least SPY + 0.25 *and* p < 0.10. The difference (+0.33) qualifies, the p-value (0.165) does not. The strategy is 92 % correlated with SPY, so a 0.3 Sharpe difference needs roughly 4–5 years of data to reach p < 0.10. Three years cannot settle it.
- **Selected from 34 registered candidates in seven rounds.** The Deflated Sharpe Ratio over the holdout with 34 trials is 0.78. The 50/50 combination was formed *after* both books' validation segments were known: the dip overlay was strong in 2020–23, the rebalancing book in 2016–19. The validation period is therefore in-sample for the combination. Only the holdout is out-of-sample.
- **The holdout is not perfectly blind to the analyst.** The research was done by an AI model whose training data covers markets until about mid-2026, including the 2024–25 gold rally. The design was motivated by measurements on 2005–2015, but this cannot be fully excluded. Diagnostics:
  - Without gold (book 2 = SPY/TLT only), the holdout Sharpe is **1.22** against 1.09.
  - On the 91 days after the knowledge cutoff (2026-07-01 → 11-06), the strategy returned +0.4 % excess, SPY −2.7 %. That is too short for any conclusion.
- **International replication is weaker than it looks.** The frozen rule was applied to eight MSCI country ETFs: EAFE, Japan, Germany, UK, Canada, Australia, Switzerland and France.
  - It beats the local index in 8/8 markets (mean +0.16 Sharpe).
  - But the markets are 74 % correlated, so they count as ~1.3 independent witnesses, not 8.
  - Abroad, the gain came from the diversification book. The dip overlay *reduced* the Sharpe there compared with book 2 alone.
- **Regime risk in the bond leg.** The rebalancing premium needs low or negative stock–bond correlation. In 2022 both fell together. That is why the second validation segment is weak.
- **Survivorship and data.** All instruments are ETFs that exist today. yfinance adjusted prices can be revised slightly over time.

**The only honest next step is a forward test with the rules frozen** (see `CLAUDE.md`).

## Exact rules

All signals are computed from the **close of day t** and held during **day t+1**. Signals use only data up to and including t, as tested in `tests/`.

**Book 1: SPY exposure in [0.5, 2.0]**
- RSI(2) is Wilder's RSI over 2 days. SMA(n) is the simple moving average of closes.
- *Dip state:* entered when RSI(2) < 10 **and** close > SMA(200). Left when close > SMA(5).
- *Overbought state:* entered when RSI(2) > 90 **and** close < SMA(200). Left when close < SMA(5).
- Exposure = clip(1 + dip − 0.5 · overbought, 0.5, 2.0).
- Exposure above 1.0 is financed at T-bill + 1.5 % p.a. Unused capital earns the T-bill rate.

**Book 2: SPY / TLT / GLD**
- Reset to 1/3 each at the close of the last trading day of every month. In between, the weights drift with prices (no trading).

**Strategy:** 50 % of capital in book 1, 50 % in book 2.

| Example: holdings for 1.0 of capital | No signal | Dip | Overbought |
|---|---:|---:|---:|
| SPY | 0.50 + 0.5·w_SPY ≈ 0.67 | 1.00 + 0.5·w_SPY ≈ 1.17 | 0.25 + 0.5·w_SPY ≈ 0.42 |
| TLT | 0.5·w_TLT ≈ 0.17 | ≈ 0.17 | ≈ 0.17 |
| GLD | 0.5·w_GLD ≈ 0.17 | ≈ 0.17 | ≈ 0.17 |

**Costs and cash:** 1 bp of traded notional per side, with exact turnover against the drifted holdings. Cash and all Sharpe ratios use the FRED 3-month T-bill rate (DTB3).

## Why it should work (the economics)

- **Index mean reversion is a liquidity-provision premium.** After forced or hedging-driven selling, buyers who supply liquidity are paid by the rebound (Lehmann 1990; Nagel 2012, "Evaporating Liquidity"). The premium is largest when volatility is high. In our measurements, most of the rebound arrives in the first night after the oversold close.
- **The rebalancing premium is a diversification return.** A constantly rebalanced portfolio grows faster than the weighted average of its parts by ½(Σ wᵢσᵢ² − σ_p²) (Booth & Fama 1992; Erb & Harvey 2006). Across stocks, long bonds and gold (2005–2015 correlation −0.10), this is 1.2 % p.a., three times the 0.4 % available among US sectors (correlation 0.75). It pays best in calm regimes with a stable negative stock–bond correlation.
- **The two books pay in different regimes.** In validation, book 1 earned in 2020–23 (0.64 vs 0.41) and book 2 in 2016–19 (1.28 vs 1.00). Their combination diversifies regime risk. A pure overlay on SPY cannot do this. It raises the Sharpe only if its own Sharpe exceeds ρ × Sharpe(SPY), which is almost impossible in a calm bull market.

## How to run

```bash
pip install -r requirements.txt
python run_backtest.py     # reproduces every number above, writes results/backtest.json
python signal_today.py     # portfolio to hold from the next session (run after the US close)
pytest -q                  # accounting, no-look-ahead and one-day-delay checks
```

Data comes from Yahoo Finance via `yfinance` (adjusted closes) and from FRED (DTB3, no API key). It is cached in `data_cache/`, and a cache that ends more than 5 business days ago is re-downloaded. `results/backtest.json` is the reference output of the research run (data until 2026-11-06).

## Repository layout

```
strategy/data.py       price and T-bill loaders (cached)
strategy/books.py      the two books, the combination, today's target portfolio
strategy/evaluate.py   Sharpe, Sortino, drawdown, paired Sharpe test, bootstrap
run_backtest.py        all reported periods
signal_today.py        live/paper signal
tests/                 self-checks
results/backtest.json  reference numbers
CLAUDE.md              handoff document for an AI agent continuing this work
```

## Research provenance (what did NOT work)

The strategy came out of a pre-registered programme. Each round reproduced a paper, analysed where its returns came from and tested economically motivated variants, with one fixed selection rule: beat SPY in *both* validation halves, survive a one-day execution delay, and make at least 30 trades. Rejected along the way:

- **Neural-network mean reversion with a spectral-entropy loss** (Nassar & Ephrem 2020). The paper's own trading rule never triggers.
- **PAMR / OLMAR online portfolio selection** (Li et al. 2012). Its benchmark results are dataset and survivorship artefacts. On ETFs it adds nothing over plain rebalancing.
- **TSI index dip rules** (Requejo 2024). The paper's Sharpe of 1.43 is not reproducible from the disclosed rules.
- **Market making under mean reversion** (Chakraborty & Kearns 2011). The theory is correct: profit ∝ 1 − variance ratio. But the variance ratio drifted towards 1 after 2016.
- **Overnight-only holding.** The overnight drift no longer carries index returns after 2016.

## Disclaimer

Research code. It is not investment advice. Past and backtested performance does not guarantee future results. Use at your own risk.
