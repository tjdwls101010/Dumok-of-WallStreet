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

### Trade Application
- **Entry**: 3σ extension — enter counter-trend position with conservative sizing
- **Exit target**: Mean reversion to 0σ (or ±1σ for partial exit)
- **Stop**: 4σ breach — mandatory regime reassessment and position review
- Duration governed by statistical condition, not elapsed time

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

**Cycle exhaustion rules**:
- RSI 80+ reached after sustained multi-month rally: treat as a cycle exhaustion signal, not just a short-term overbought
- Monthly RSI reaching extreme levels across multiple assets simultaneously (e.g., Gold, Silver, S&P 500 all with monthly RSI > 75): compound signal indicating cycle peak across asset classes

**When to escalate**: When RSI simultaneously exceeds 80 AND the ascent slope is historically extreme (top decile of all observed RSI climbs), treat this as a compound confirmation — both the level and the velocity are anomalous. Each dimension independently signals overextension; together they represent a higher-confidence reversion setup.

### Slope/Derivative Analysis
Beyond the RSI level, the rate-of-change (slope) carries independent information:
- Normalize the current N-day price slope against the full historical slope distribution
- Slopes in the top 5-10% historically (fastest ascents) are associated with elevated reversion probability regardless of absolute RSI level
- Combine slope percentile + RSI percentile for a compound overbought signal: when both exceed the 90th percentile simultaneously, treat it as a compound overextension condition
- "기울기 교정" (stiffness correction): An abnormally steep price slope will correct even if the underlying trend is still intact. The correction mechanism is slope normalization, not necessarily trend reversal

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

### Key Asset Pairs for US Macro
| Pair | Normal Correlation | Alert Condition |
|------|-------------------|-----------------|
| S&P 500 — Gold | Variable | Simultaneous new highs = anomaly (both risk-on and risk-off rallying) |
| Gold — DXY | Negative | Simultaneous rise = safe-haven stress |
| US Equity — EM Equity | Positive | Sharp divergence = liquidity flow shift |
| US10Y — Equity | Variable | Correlation regime determines "good is good" vs. "bad is good" |
| Gold — Silver | Positive | Gold/Silver ratio surging = deleveraging signal |

### Interpretation
- **Extreme decoupling** (3σ negative): Historically precedes regime transition or snapback
- **Simultaneous divergence across multiple pairs**: Higher confidence signal than single-pair
- **Gold-Nasdaq simultaneous rise**: Historically unstable — one must eventually yield. If Gold continues rising while Nasdaq reverses, risk-off wins. If Nasdaq holds while Gold corrects, risk-on continues.

---

## Model 5: Yield Spread and Curve Analysis

### Purpose
Characterize the yield curve regime and identify historically anomalous spread conditions that precede macro regime transitions.

### Methodology
1. Compute current spreads: US10Y-2Y, US10Y-3M, cross-country spreads
2. Calculate the Z-score of each spread relative to its historical distribution
3. Classify the yield curve regime: bear steepening, bull steepening, bear flattening, inverted
4. Find historical periods with the same spread combination

### Key Spread Thresholds
| Spread | Interpretation |
|--------|---------------|
| US10Y-2Y > 0, rising | Normal steepening — typically bullish for equities long-term |
| US10Y-2Y > 0, US10Y-3M < 0 | Partial inversion anomaly — dotcom-era signal (1998 Oct) |
| US10Y-2Y fully inverted | Recession signal; historical precursor to risk-off |
| US10Y-3M persistent inversion | Strong recession predictor; more reliable than 10Y-2Y |

### Regime Characterization
- **Bear Steepening**: Long rates rise faster than short rates. Equity headwind when driven by inflation fears rather than growth expectations. Commodity and real asset tailwind. Most dangerous regime for EM and growth equities.
- **Bull Steepening**: Short rates fall faster than long rates. Typically follows aggressive easing. Equity and EM tailwind.
- **Bear Flattening**: Short rates rise faster. Typical of early tightening cycle. Mixed equity signal.
- **Inverted**: Growth risk dominant. Historical recession precursor.

### Rate-Dollar Decoupling Signal
Under normal conditions, rising US10Y accompanies DXY strength. When US10Y rises 15+ BP but DXY falls simultaneously, this is a sovereign credibility signal — the yield rise is driven by risk premium (term premium, credit concern) rather than growth/inflation expectations. Different implications than a normal rate rise.

---

## Model 6: ERP (Equity Risk Premium) Valuation Model

### Purpose
Compare the earnings yield (inverse of CAPE) to US10Y to assess whether equities are offering adequate risk premium over risk-free rates.

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
- At US10Y 4.4%, equities must grow earnings 9%+ annually for 10 years to justify current prices
- ERP decomposition: Track dividend yield vs. US10Y as a cleaner spread measure. When dividend yield falls to 1.28% while US10Y is at 4.4%, the gap itself is a valuation signal regardless of CAPE

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

---

## Model 8: CAPE Linear Regression Upper Bound

### Purpose
Determine whether the current CAPE ratio is at a statistically extreme level relative to its own long-term trend, independent of rate environment.

### Methodology
1. Fit a linear regression to the CAPE ratio over the full historical period (Shiller dataset, 100+ years)
2. Compute the regression residual and its standard deviation
3. Calculate the current CAPE's Z-score relative to the trend line
4. Identify historical episodes when CAPE exceeded current σ-level

### Interpretation
- CAPE at 2σ+ above trend: Market is in the historical overvaluation zone. Not an immediate sell signal, but constrains the probability of further multiple expansion.
- CAPE at 35-37 (2025 level): Matches 1998 October level exactly. The only higher reading was 2000 March. This itself carries forward return distribution information.

---

## Model 9: Cleveland Fed CPI Nowcast

### Purpose
Use the Cleveland Fed's real-time CPI nowcast as a leading indicator for rate expectations, rather than waiting for the official CPI release.

### Methodology
1. Compare the Cleveland Fed CPI nowcast (released daily, 30 days ahead of official CPI) against consensus
2. Track the nowcast-consensus spread: positive = inflation hotter than expected, negative = cooler
3. When the nowcast consistently runs above consensus for 2+ weeks, pre-position for hawkish rate reaction on CPI release day
4. Combine with shelter CPI leading indicators (mortgage market index) for housing component prediction

### Application
This model provides a 2-4 week edge on rate-sensitive positioning. When the nowcast diverges from consensus by more than 0.1%, the CPI surprise probability is elevated.

---

## Model 10: Gold/Silver Ratio as Risk-Off Barometer

### Purpose
Track the XAU/XAG ratio as a leading indicator for global deleveraging and risk-off phases.

### Methodology
1. Compute the Gold/Silver ratio (XAU/XAG) daily
2. Calculate the ratio's rate-of-change (ROC) over 5, 20, 60 trading days
3. Compare current ROC against historical distribution
4. A sharp surge (30%+ in a short period) signals broad deleveraging across asset classes

### Historical Benchmark Events
| Event | Gold/Silver Ratio Spike | Context |
|-------|------------------------|---------|
| Lehman 2008 | Extreme | Global deleveraging |
| 2011 EM Peak | Large | EM → DM liquidity rotation |
| COVID 2020 | Extreme | Pandemic deleveraging |

### Interpretation
- After extreme Gold/Silver ratio spike: if Gold holds while Silver rebounds → equities tend to bounce
- If Gold itself subsequently declines after the ratio spike → deeper crash follows
- As a short-entry signal: Gold/Silver ratio at extreme levels with silver lagging gold aggressively → silver short has positive expectancy

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

**VIX + Yield Curve + Commodity coherence check**: When VIX, yield curve dynamics, and commodity prices all tell a consistent story, the macro signal is strong. When they diverge (e.g., VIX low but yield curve inverting and commodities falling), investigate — one of them is wrong, and identifying which provides the edge.
