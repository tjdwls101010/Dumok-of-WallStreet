# SidneyKim0 Quantitative Models

## Overview

Statistical and quantitative tools forming the analytical backbone of the SidneyKim0 methodology. Each model produces a specific output that feeds into the overall market assessment. Models are used together — convergence across multiple models increases signal reliability.

---

## Model 1: Macro Regression Residual Z-Score

### Purpose
Estimate the "macro-implied fair value" of a target asset based on multiple macro input variables. The residual (actual minus predicted) Z-score identifies how far the asset has deviated from what macro conditions suggest.

### Methodology
1. Build multi-factor OLS regression: `target_price = β₁×input₁ + β₂×input₂ + ... + const`
2. Generate predicted values (macro-implied fair value) over the historical period
3. Compute residuals: `residual = actual - predicted`
4. Calculate rolling Z-score of residuals over a 252-day lookback window
5. The current residual Z-score indicates statistical extension vs. macro fundamentals

### Default Inputs
- Target: `^GSPC` (S&P 500) or `QQQ` (NASDAQ 100)
- Macro inputs: `DX-Y.NYB` (DXY), `^TNX` (US10Y), `GC=F` (Gold), `^VIX` (VIX)
- Period: 5 years
- Method: Rolling OLS (252-day window)

### Interpretation Thresholds
| Z-score | Interpretation |
|---------|---------------|
| 0 to ±1σ | Within normal range; macro-justified |
| ±1σ to ±2σ | Moderate deviation; monitoring zone |
| ±2σ | Significant deviation; mean reversion signal |
| ±3σ | Extreme deviation; high-confidence mean reversion signal |
| ±4σ | Historical anomaly; regime reassessment required |

**Key insight**: When residual Z-score exceeds +2σ, the asset is priced ABOVE what macro conditions justify. This is SidneyKim0's primary overvaluation signal. When below -2σ, the asset is statistically cheap relative to macro fundamentals.

### Script Reference
See `SKILL.md` → Macro category for multi-factor regression and residual analysis tools.

---

## Model 2: Pattern Similarity (Historical Analog Matching)

### Purpose
Find historical periods with the highest multi-dimensional similarity to the current market pattern. Use the historical forward returns from those periods to construct a probabilistic fan chart for the next N days.

### Methodology
1. Define a lookback window (typically 100-150 trading days)
2. Extract a multi-feature vector for each day: price (normalized), RSI, price slope/velocity, volatility, distance-to-high (D2H)
3. For every historical starting point, compute DTW (Dynamic Time Warping) distance or Pearson correlation between the current N-day window and each historical N-day window
4. Select the top 10 most similar historical periods (ranked by correlation score)
5. Plot the subsequent 60-day forward returns for each analog
6. Construct fan chart: 10th-90th percentile (extreme range), 25th-75th percentile (likely range), and average path

### Key Parameters
- Window size: 150 days (standard)
- Forward projection: 60 trading days
- Features: price + RSI + slope + volatility + D2H
- Top-N analogs: 10

### Interpretation
- Average path direction and slope = base case
- 25-75% probability band = likely outcome range
- 10-90% probability band = tail risk range
- Historical analog correlation scores rank confidence:
  - corr > 0.90: Very high similarity (strong analog)
  - corr 0.70-0.90: High similarity (good analog)
  - corr < 0.70: Moderate similarity (use with caution)

### Use Case
When the top-3 analogs all share a similar macro context (same regime type, similar rate environment), their forward return profiles are more credible than when analogs span multiple regime types.

### Script Reference
See `SKILL.md` → Pattern category for DTW pattern matching, similarity analysis, and fan chart projection tools.

---

## Model 3: RSI Percentile Distribution Analysis

### Purpose
Determine how extreme the current RSI reading is in historical context, using beta-fitted distribution analysis to assign precise probability estimates.

### Methodology
1. Collect N-year RSI time series (14-day RSI, daily)
2. Fit a beta distribution to the historical RSI data
3. Compute the current RSI percentile within the fitted distribution
4. Identify how many times historically the RSI reached the current level or higher
5. Compute the historical mean reversion target (e.g., where RSI typically falls after reaching extreme levels)

### Key Historical Thresholds
| RSI Level | Historical Interpretation |
|-----------|--------------------------|
| > 80 | ~5-year frequency event; historically ~80% probability of mean reversion to RSI ~49 within 1 month |
| > 70 | Overbought; above 75th percentile historically |
| 50-70 | Normal trending zone |
| 30-50 | Oversold territory; elevated mean reversion probability |
| < 30 | Extreme oversold; historically high mean reversion probability |

**When to escalate**: When RSI simultaneously exceeds 80 AND the ascent slope is historically extreme (top decile of all observed RSI climbs), treat this as a compound confirmation — both the level and the velocity are anomalous. Each dimension independently signals overextension; together they represent a higher-confidence reversion setup.

### Slope/Derivative Analysis
Beyond the RSI level, the rate-of-change (slope) carries independent information:
- Normalize the current N-day price slope against the full historical slope distribution
- Slopes in the top 5-10% historically (fastest ascents) are associated with elevated reversion probability regardless of absolute RSI level
- Combine slope percentile + RSI percentile for a compound overbought signal: when both exceed the 90th percentile simultaneously, treat it as a compound overextension condition

### Script Reference
See `SKILL.md` → Statistics category for percentile, distribution, and extremes tools.
See `SKILL.md` → Technical category for RSI oscillator and slope/derivative tools.

---

## Model 4: Rolling Correlation Regime Analysis

### Purpose
Detect breakdown and recovery of historically stable correlations between asset pairs. Extreme negative deviations from historical mean correlation signal regime transitions or mispricing opportunities.

### Methodology
1. Compute rolling N-day correlation between two assets (typically 45-day window)
2. Compute the long-run mean correlation over the full historical period
3. Compute the Z-score of the current correlation vs. the long-run mean
4. Identify "extreme negative start" events (correlation drops sharply below mean)
5. Track "turning point" events (correlation recovers from extreme negative)

### Key Asset Pairs
| Pair | Normal Correlation | Alert Condition |
|------|-------------------|-----------------|
| NASDAQ — KOSPI | Positive (0.6-0.9) | Drop to 3σ below mean = regime signal |
| Gold — DXY | Negative | Simultaneous rise = safe-haven stress |
| US Equity — EM Equity | Positive | Sharp divergence = liquidity flow shift |
| US10Y — Equity | Variable | Correlation regime determines "good is good" vs. "bad is good" |

### Interpretation
- **Extreme decoupling** (3σ negative): Historically precedes regime transition or snapback
- **Simultaneous divergence across multiple pairs**: Higher confidence signal than single-pair
- "나스닥-코스피 상관관계가 3시그마 초입을 노크하고 있습니다" = approaching 3-sigma decoupling threshold

### Script Reference
See `SKILL.md` → Statistics category for correlation and multi-asset extreme detection tools.
See `SKILL.md` → Convergence and Divergence categories for multi-model signal assessment tools.

---

## Model 5: Yield Spread and Curve Analysis

### Purpose
Characterize the yield curve regime and identify historically anomalous spread conditions that precede macro regime transitions.

### Methodology
1. Compute current spreads: US10Y-2Y, US10Y-3M, KR10Y-US10Y (cross-country)
2. Calculate the Z-score of each spread relative to its historical distribution
3. Classify the yield curve regime: bear steepening, bull steepening, bear flattening, inverted
4. Find historical periods with the same spread combination

### Key Spread Thresholds
| Spread | Interpretation |
|--------|---------------|
| US10Y-2Y > 0, rising | Normal steepening — typically bullish for equities long-term |
| US10Y-2Y > 0, US10Y-3M < 0 | Partial inversion anomaly — dotcom-era signal (1998 Oct) |
| US10Y-2Y fully inverted | Recession signal; historical precursor to risk-off |
| KR10Y spread vs. US10Y | At 2019/2023 levels = boundary condition |
| KR10Y-2Y at 46bp while FX diverges | 2007 analog pattern (historically very rare) |

### Regime Characterization
- **Bear Steepening**: Long rates rise faster than short rates. Equity headwind when driven by inflation fears rather than growth expectations. Commodity and real asset tailwind.
- **Bull Steepening**: Short rates fall faster than long rates. Typically follows aggressive easing. Equity and EM tailwind.
- **Bear Flattening**: Short rates rise faster. Typical of early tightening cycle. Mixed equity signal.
- **Inverted**: Growth risk dominant. Historical recession precursor.

### Script Reference
See `SKILL.md` → Macro category for spread analysis tools.
See `SKILL.md` → FRED category for interest rate and yield curve data.

---

## Model 6: ERP (Equity Risk Premium) Valuation Model

### Purpose
Compare the earnings yield (inverse of CAPE) to US10Y to assess whether equities are offering adequate risk premium over risk-free rates. Near-zero or negative ERP historically precedes multiple compression.

### Formula
```
ERP = (1 / CAPE) - US10Y
```

### Interpretation
| ERP | Historical Assessment |
|-----|----------------------|
| > 3% | Equities clearly attractive vs. bonds |
| 1-3% | Normal range; equities moderately attractive |
| 0-1% | Equities barely compensating for risk |
| < 0% | Bonds yield more than equities; historical multiple compression signal |

### Key Historical Context
- CAPE 36-37 + US10Y 4.4% → ERP effectively near zero or negative
- "US10Y 4.4% 의미: PE 22배 (듀레이션 무시) vs. PE 8배 (복리 가정)" — illustrates how rate level destroys equity valuation case
- At US10Y 4.4%, equities must grow earnings 9%+ annually for 10 years to justify current prices

### Script Reference
See `SKILL.md` → Macro category for ERP calculation tools.
See `SKILL.md` → Valuation category for CAPE ratio data tools.

---

## Model 7: Conditional Probability / Event Study Analysis

### Purpose
Compute the historical probability of a specific outcome given a triggering condition. Used to assign base-rate probabilities to scenarios rather than making directional calls without statistical foundation.

### Standard Event Study Format
1. Define the triggering condition (e.g., "RSI > 80 on ATH with 4Q new high and no Santa Rally")
2. Search 25-40 year historical database for matching conditions
3. Count occurrences
4. Measure forward returns at 20, 60, 120 trading days
5. Report: occurrence count, win rate, average forward return, distribution range

### Example Output Format
```
Trigger: [Defined condition]
Historical occurrences: 11 (over 25 years)
Forward 20d mean return: +0.43%
Probability of prior low breach (20d): 80%
```

**Key principle**: Sample size matters. When historical occurrences are fewer than 5, explicitly flag low confidence. When occurrences are 10+, treat as statistically meaningful.

### Script Reference
See `SKILL.md` → Backtest category for conditional probability, event return statistics, and extreme reversal tools.

---

## Model Convergence Framework

No single model is sufficient. Signal strength increases when multiple models agree:

| Convergence Level | Models Agreement | Confidence |
|-------------------|-----------------|------------|
| HIGH | 3+ models point same direction | Act with high conviction |
| MEDIUM | 2 models agree, 1 neutral | Act with moderate conviction |
| LOW | Mixed signals | Wait for convergence; reduce position size |
| CONTRADICTORY | Models disagree | Investigate the discrepancy — potential regime transition |

**Application**: When macro regression residual Z-score, pattern similarity fan chart, and RSI percentile all point to the same direction, this is a HIGH-confidence setup. When they diverge, the divergence itself is information — typically signals a regime transition in progress.

See `SKILL.md` → Convergence category for automated multi-model signal assessment tools.
