# SidneyKim0 Analysis Methodology

## Overview

SidneyKim0 is a statistical nomadist who prioritizes quantitative evidence over market narratives. His core philosophy: "통계적으로 전 자신이 있습니다" (Statistically, I am confident). He follows a rigorous 6-step analysis process that ensures every conclusion is cross-validated across multiple independent data sources.

---

## Step 1: Macro Data Collection & Regime Classification

### Starting Point: US10Y as the Anchor

Every analysis begins with US 10-Year Treasury yield. Everything else derives from where US long rates sit.

### Data Cascade Order

1. **Rates & Spreads**: US10Y level, US10Y-2Y spread, US10Y-3M spread, KR10Y-2Y spread, US-KR 10Y spread
2. **FX**: DXY (Dollar Index), USD/KRW, USD/JPY, USDKRW-DXY rolling correlation
3. **Safe Haven Assets**: Gold, Silver, Gold/Silver ratio, US Treasury demand direction
4. **Commodity Indicators**: WTI, Naphtha (demand proxy), BDI (global trade), DRAM contract prices, LME, CRB
5. **Liquidity Plumbing**: TGA (Treasury General Account), RRP (Reverse Repo), Reserve Balances, Central bank balance sheets
6. **Credit Conditions**: HY spread, ERP (Equity Risk Premium vs US10Y)
7. **Activity/Real Economy**: ISM manufacturing, employment, CPI (Cleveland Fed nowcasting for real-time)
8. **Valuation**: CAPE (Shiller PE), GBM model outputs for KOSPI and USDKRW
9. **Technical/Statistical**: RSI (14-period, weekly, monthly), Z-scores from proprietary models, put/call ratio, 20-day rolling slope
10. **CME FedWatch**: Rate cut count tracked as continuous variable (e.g., "1.95회", "2.3회")
11. **Sentiment**: Michigan consumer survey, VIX, crypto dominance (BTC vs altcoin)
12. **Flow Data**: Foreign/institutional/individual positioning, credit balance percentile

### Market Regime Framework (4 Cycles)

- **Financial Cycle (금융장세)**: Rate cuts / easing -> liquidity-driven rally
- **Earnings Cycle (실적장세)**: Corporate profits drive equities independent of rates
- **Reverse Financial Cycle (역금융장세)**: Sudden rate increases kill the rally even if earnings are fine
- **Reverse Earnings Cycle (역실적장세)**: Earnings deteriorate, forcing policy response

The regime determines the entire positioning logic. Transition signals must be detected early.

---

## Step 2: Divergence Detection

### Cross-Asset Feedback Loop

After each data point, check whether the "feedback" (피드백) from other asset classes is consistent or contradictory. Divergence = signal.

### Core Cross-Validation Checks

- **Rate vs Dollar**: If rates spike but dollar does NOT follow proportionally -> dollar ceiling signal
- **Rate vs FX (Korea)**: If KR10Y-2Y spread widens but USD/KRW does not fall -> danger signal
- **Gold vs Dollar**: If gold rises much more than dollar falls -> safe haven escalation (금>>>달러>>>DM ordering)
- **Equity vs Commodity**: If equities surge but commodities lag -> rally lacks fundamental backing
- **EM vs DM**: If EM massively outperforms DM -> historically precedes liquidity reversal (양털깎기)
- **Safe Haven Decomposition**: Where safe haven flows go matters more than magnitude (Gold vs Bonds vs BTC vs altcoins)

### Commodity Demand-Supply Decomposition

Split commodities into categories:
- **Demand-driven**: Copper, Naphtha, WTI (when naphtha confirms)
- **Supply-driven**: Iron ore, Coal
- **Semiconductor**: DRAM contract prices (DDR4 8Gb as benchmark)
- **Global trade**: BDI (Baltic Dry Index)

If demand-driven commodities fall while DXY also falls -> genuine demand destruction (contradictory danger).

---

## Step 3: Statistical Significance Validation

### Quantitative Models

- **Rolling Pearson Correlation**: 45-day and 100-day windows across 25+ years of data, translated into sigma-based probability
- **Z-Score Residual Model**: KOSPI vs macro parameters (USD/KRW, gold, DXY, NASDAQ, yield spreads), R-squared = 0.9878 (smoothed)
- **GBM (Gradient Boosting Machine) + OLS**: For KOSPI and USDKRW fair value prediction
- **US Macro Fair Value Model (OLS)**: S&P 500 vs macro factors (DXY, GC=F, ^TNX, HYG). Run via `macro/macro.py fairvalue SPY --inputs DX-Y.NYB,GC=F,^TNX,HYG --period 10y`. R-squared typically 0.98+. Residual Z-score indicates over/undervaluation.
- **US Macro Residual Monitor**: Rolling residual Z-score from macro fair value model. Run via `macro/macro.py residual SPY --inputs DX-Y.NYB,GC=F,^TNX --period 10y`. Detects extreme deviations (3sigma+) and tracks residual trend direction.
- **US Spread Regime Classifier**: Yield curve regime classification (bull/bear steepening/flattening). Run via `macro/macro.py spread ^TNX ^IRX --period 5y`. Provides percentile ranking and regime label.
- **Multi-Model Signal Convergence**: Aggregates Z-score, RSI, and macro model signals for convergence detection. Run via `macro/macro.py convergence SPY --symbols DX-Y.NYB,GC=F,^TNX --period 10y`.
- **DTW (Dynamic Time Warping)**: Subsequence matching for pattern similarity (60-150 day window). Run via `technical/pattern dtw-similarity SYMBOL --window 60 --period 15y`.
- **RSI Distribution Analysis**: Robust Z + ECDF across weekly/monthly timeframes
- **20-Day Relative Slope Normalization**: Momentum regime detection
- **Fan Chart Projection**: Based on top 10 similar historical patterns, projects 60-day forward returns

### US Market Data Cascade (for SPY/QQQ/NVDA Analysis)

When analyzing US equities, follow this US-specific cascade in order:

1. **Macro Fair Value**: `macro/macro.py fairvalue SPY --inputs DX-Y.NYB,GC=F,^TNX,HYG --period 10y` -- Is SPY above/below macro-implied fair value? What is the residual Z-score?
2. **Residual Trend**: `macro/macro.py residual SPY --inputs DX-Y.NYB,GC=F,^TNX --period 10y` -- How many extreme events detected? What is the residual direction (expanding or mean-reverting)?
3. **Yield Curve Regime**: `macro/macro.py spread ^TNX ^IRX --period 5y` -- Bull/bear steepening/flattening? What percentile is the current spread?
4. **RSI Multi-Timeframe + Slope**: `technical rsi-mtf SPY` then `technical slope SPY` then `technical rsi-derivative SPY` then `technical momentum-regime SPY` -- RSI divergence + slope normalization + momentum regime
5. **Z-Score Cascade**: `statistics/zscore.py SPY --periods 63,126,252` -- Short/medium/long-term Z-scores for statistical positioning
6. **Cross-Asset Divergence**: `analysis/divergence.py SPY,GC=F,DX-Y.NYB,^TNX` -- Automatic divergence detection
7. **FRED Policy Data + Net Liquidity**: `data_advanced/fred yield-curve`, `data_advanced/fred tga`, `data_advanced/fred credit-spreads`, `macro/net_liquidity.py net-liquidity` -- TGA balance, yield curve shape, credit conditions, aggregate liquidity trajectory
8. **Market Regime**: `technical/pattern regime ^GSPC,GC=F,DX-Y.NYB --lookback 20` -- Current regime classification
9. **Valuation + ERP**: `valuation/cape.py` + `macro/erp.py erp` -- CAPE percentile vs historical + Equity Risk Premium danger signal
10. **Sentiment**: WebSearch for CNN Fear & Greed, CME FedWatch

### FRED Series ID Quick Reference (for `fred series --series-id`)

- UNRATE: Unemployment Rate (monthly)
- PAYEMS: Nonfarm Payrolls (monthly)
- ICSA: Initial Jobless Claims (weekly)
- WRESBAL: Reserve Balances (weekly)
- GDP: Nominal GDP (quarterly)
- GDPC1: Real GDP (quarterly)
- WALCL: Fed Total Assets (weekly)
- WTREGEN: TGA Balance (weekly)
- RRPONTSYD: Reverse Repo (daily)
- BAMLH0A0HYM2: HY OAS Spread (daily)
- DGS10: 10-Year Treasury (daily)
- DGS2: 2-Year Treasury (daily)
- DGS3MO: 3-Month Treasury (daily)
- DTWEXBGS: Trade-Weighted Dollar Index (daily)

### Sigma-Based Decision Framework

- **2 sigma**: Notable anomaly, start monitoring
- **3 sigma**: Extreme event (top 0.3%), high-conviction entry zone begins
- **4 sigma**: Personal trading entry threshold for mean reversion
- **5 sigma**: 1 in 3.31 million -- "market dysfunction territory"
- **6+ sigma**: Off-the-charts -- comparable to WTI going negative during COVID

### "Non-Negotiable Price" (타협이 되지 않는 가격)

When BOTH fundamental analysis AND statistical mean-reversion analysis converge on a price being extreme, this is a high-conviction entry. Exit when statistical edge is consumed (mean reversion completes).

---

## Step 4: Historical Case Search

### Pattern Matching Process

1. Run multi-feature DTW model against 25-30 year database: `technical/pattern multi-dtw SYMBOL --window 60 --period 15y` (price+RSI+slope+vol+D2H). Fallback: `technical/pattern dtw-similarity SYMBOL` for price-only.
2. Identify top 3-5 matching periods by weighted DTW distance
3. For each match, verify "necessary conditions" (필요조건) are satisfied
4. If necessary conditions are violated, the analogy is rejected regardless of price pattern similarity
5. Examine what happened AFTER the matched period (60-day, 6-month, 1-year forward)

### Necessary Condition Framework

"필요조건 자체가 위반되었기에 결과를 주장할 수 없습니다" -- If the necessary precondition for a historical outcome is not present, that outcome cannot be claimed even if the price pattern looks similar.

Example: If KOSPI is rising at crisis-recovery speed WITHOUT a prior crisis, the necessary precondition (crisis) is violated, so the recovery analogy doesn't apply.

---

## Step 5: Probabilistic Scenario Presentation

### Scenario Forking

Present 2-3 clearly opposed scenarios with relative probability based on the data cascade:

- Scenario A (base case): Description + probability + conditions that confirm
- Scenario B (alternative): Description + probability + conditions that confirm
- Scenario C (tail risk): Description + probability + what to watch

### Rules

- NEVER present a single prediction
- Acknowledge uncertainty explicitly: "3σ+ means statistics break down"
- State falsification conditions for each scenario: what data would invalidate the thesis
- Use probabilistic language: "확률로 보면..." (looking at probability...)

---

## Step 6: Position Statement with Risk Acknowledgment

### Position Disclosure

Always end with concrete positioning:
- What is long/short
- At what levels (entry, TP, stop)
- What would falsify the view

### Position Management Rules

- **First wave rejection**: Band trade (횡보 밴드 트레이딩)
- **Second wave rejection**: Long-term directional position ("두 번째 상승의 반전에선 -> 장기 숏")
- **If position breaks against**: Exit immediately (not band trading)
- **If position works**: Hold until statistical target unconditionally
- **4-sigma entry rule**: Enter at 4-sigma with conviction, but remain suspicious even at 5-sigma (burned 3 times at 4-sigma historically)
- **Exit when statistical edge is consumed**: When mean reversion completes and the asset returns to average valuation, close position regardless of narrative

### Core Principle

"근거와 목표를 반드시 세워야 합니다" (You must establish evidence and targets before trading)
