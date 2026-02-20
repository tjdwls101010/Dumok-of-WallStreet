# SidneyKim0 Analysis Methodology

## Overview

Macro-statistical analysis methodology combining top-down macro regime identification with quantitative pattern detection and probabilistic scenario analysis. Explicitly NOT narrative-driven, NOT sentiment-following, NOT bottom-up fundamental analysis. Statistical data and macro regime context drive conclusions, not stories.

> "숫자가 말하게 하라" — Let the numbers speak

> "데이터 보다 내러티브에 집중되면, 틀린다" — When focus shifts to narrative over data, you get it wrong

---

## Core Philosophy

### Data Over Narrative

Every thesis must be backed by specific quantitative data. When market consensus is narrative-driven and data diverges, the data wins eventually. The analyst's job is to find the divergence early.

Key distinction: narrative changes fast; macro structure changes slowly. Short-term price action follows narratives, but macro structure determines the final resolution.

### Macro Regime First

Individual asset analysis without macro regime context is incomplete. The market cycle phase determines which signals are reliable, which assets benefit, and which risk factors dominate. Determine the regime before analyzing individual positions.

### Statistical Edge Over Conviction

Probability-based positioning over high-conviction bets. State the probability, the historical base rate, and the scenario count — not just the direction. "통계 10번 중 8번" (8 out of 10 historically) is more useful than "I'm confident it will fall."

---

## Market Regime Classification

Four primary market regimes, each with distinct asset behavior and analysis priorities:

### 1. 실적장세 (Earnings Cycle)

**Definition**: Fundamentals drive asset prices. Rates are neutral or declining. Economic growth is translating directly into earnings growth.

**Signals**:
- "Good is good" feedback loop: strong economic data → stock rally
- High-yield and growth stocks outperform
- Correlations between risk assets are high and positive
- Market breadth expanding

**Analysis priority**: Earnings acceleration, sector rotation, forward P/E relative to growth

**US analog**: 2017, 2023 H2, 2024 H1

---

### 2. 역금융장세 (Reverse Financial Cycle)

**Definition**: Inflation prevents monetary easing despite economic weakness. Rates stay "higher for longer" even as growth decelerates. The market's multiple compression exceeds earnings growth.

**Signals**:
- "Bad is bad" — weak data triggers both equity and bond selling
- Safe-haven assets (gold, USD) rally simultaneously with high-yield weakness
- CAPE/ERP divergence: CAPE elevated while ERP compresses to near zero
- FedWatch pricing fewer cuts than consensus expected
- High-yield bonds underperform investment grade

**Analysis priority**: US10Y trajectory, FedWatch probability shifts, ERP level, CAPE multiple sustainability

**US analog**: 2018 Q4, 2022, 2025 H1

---

### 3. 역실적장세 (Reverse Earnings Cycle)

**Definition**: Both rates AND earnings disappoint simultaneously. The market faces double compression — multiple contraction plus earnings revision downward.

**Signals**:
- Earnings guidance cuts across sectors
- Credit spreads widening sharply
- Volume/breadth deterioration
- Leadership breakdown in former cycle leaders
- TGA/RRP liquidity indicators deteriorating

**Analysis priority**: Credit spread trajectory, earnings revision trends, liquidity metrics

**US analog**: 2007-2008, 2022 H2

---

### 4. 유동성 쏠림 / 양털깎기 (Liquidity Flow / Wool-Shearing Cycle)

**Definition**: Global liquidity flows unilaterally into the US dollar system. EM assets correct first and harder. Yield spread differentials between US and other markets drive FX, which drives capital flows.

**Signals**:
- EM dramatically underperforming DM (after a period of EM outperformance)
- Dollar strengthening while US rates stable or rising
- Gold/commodity softness except gold which retains safe-haven premium
- US10Y-2Y spread widening while EM rates diverge from US
- "약한 고리부터 깨진다" — weaker link assets (HY bonds, EM equities, speculative commodities) crack first

**Historical pattern**: EM outperforms → peak in relative EM strength → DXY pivot → EM corrects → US absorbs global liquidity → EM enters multi-year underperformance

**US analog**: 1997-1998 (Asia crisis), 2011 H2, 2022

---

## Data Cascade Hierarchy

Analyze in this exact order. Higher-order signals constrain lower-order ones.

### Level 1: Rate Regime (Interest Rate Architecture)
- US10Y level and direction (absolute anchor for all valuation)
- Yield curve shape: bear steepening / bull steepening / bear flattening / inverted
- FedWatch cut probability and timeline (CME futures-based)
- ERP = Earnings Yield (1/CAPE) minus US10Y: the equity valuation danger signal

**Key thresholds**:
- US10Y 4.0-4.5%: High-hurdle zone; requires 9%+ earnings growth to justify current multiples
- US10Y 5%+: Historical rejection zone for equity multiples
- ERP near zero or negative: Historically precedes multiple compression

### Level 2: Dollar and FX Architecture
- DXY direction (USD strengthening = EM headwind)
- Yield spread: US10Y vs. key EM 10Y (Korea, Japan, EUR)
- Spread direction and rate of change

**Key interpretation**:
- When US rates are HIGHER than peer: dollar strengthens, EM equity underperforms
- When US rates are LOWER than peer: dollar weakens, EM may outperform temporarily
- Both conditions ultimately resolve with liquidity flowing to the US (양털깎기 dynamic)

### Level 3: Cross-Asset Sentiment Architecture
- Gold price direction (safe-haven or risk-asset behavior)
- Gold-Dollar relationship: Both rising simultaneously = anomaly signal, potential regime shift
- Put/Call ratio on US equities: below 0.6 = extreme bullishness (watch for reversal)
- VIX term structure: contango vs. backwardation
- CAPE ratio: current vs. historical average

**Key thresholds**:
- Put/Call ratio < 0.6: Historically unsustainable bullish sentiment
- CAPE > 35: "Rejection zone" — equity multiple expansion unlikely
- Gold rising while dollar also rising: Safe-haven stress signal, not equity positive

### Level 4: Real Economy and Liquidity Pulse
- BDI (Baltic Dry Index): Real-time global trade volume
- Commodity price indices: GSCI, LME index, CRB index
- Semiconductor spot prices (DRAM, NAND): Forward demand signal
- TGA + RRP → Fed Net Liquidity: Systemic liquidity tracker
- Credit spreads (high-yield vs. investment-grade)

### Level 5: Individual Asset/Sector Context
Only after Levels 1-4 are assessed. Individual asset analysis is constrained by macro regime.

---

## Analysis Workflow

### Step 1: Macro Regime Identification
Determine which of the 4 regimes currently applies. This is not always clean — markets can be transitioning between regimes. When in transition, state the probability of each regime.

### Step 2: Rate Architecture Assessment
- Current US10Y level and trajectory (up/flat/down)
- Yield curve shape and dynamics
- FedWatch: current vs. consensus expectation divergence
- ERP calculation and historical context

### Step 3: Cross-Asset Signal Mapping
- Map signals from Level 3 instruments
- Flag anomalies: assets that are NOT behaving as the regime would predict
- Anomalies are the highest-alpha signals — they indicate regime transition or mispricing

### Step 4: Historical Analog Selection
- Use pattern similarity to find the top 3-5 historical periods matching:
  (a) current price pattern (N-day window)
  (b) macro regime characteristics
  (c) quantitative indicators (CAPE, ERP, spread levels)
- Weight analogs by match quality (correlation score)

### Step 5: Probabilistic Scenario Construction
- Build 2-3 scenarios based on historical analog base rates
- Assign probabilities from historical outcome distribution
- State invalidation conditions: what would falsify each scenario

### Step 6: Statistical Signal Assessment
- Run relevant quantitative models (see `quantitative_models.md`)
- Cross-validate with historical analog fan chart projections
- Identify any σ-level extremes that historically precede mean reversion

### Step 7: Positioning
- State current regime conviction
- Translate scenario probabilities to risk/reward
- State what changes would shift conviction (duration management)

---

## Consensus vs. Data Divergence Principle

When sell-side consensus and statistical data diverge, the data wins eventually. Key diagnostic questions:

1. **Is the narrative already priced in?** If an asset has moved significantly on a narrative, and data doesn't confirm it, the narrative is borrowed from the future.
2. **Are "weak links" holding up?** High-yield bonds, EM equities, and speculative commodities are the canaries. If they weaken while leading assets still hold, regime transition is underway.
3. **What does the distribution say?** Instead of debating direction, compute the historical probability distribution. "RSI 80에 도달한 이후 1달 내 되돌림 확률 80%" is more actionable than "I think it will fall."

---

## Risk Management and Duration Philosophy

- Position duration is macro-regime dependent: in 실적장세, hold longer; in 역금융장세, reduce duration
- σ-level extremes (±3σ, ±4σ) trigger position review, not automatic action — context determines response
- "4시그마의 벽이 무너지면 예상 밖의 이동" — when 4σ walls break, regime reassessment mandatory
- When positioned against consensus, track the RSI/σ level and define the exit criteria before entering

> "이미 통계를 근거로 포지션을 유지할 계획입니다" — The position duration is governed by statistics, not by conviction alone
