# SidneyKim0 Historical Analogies Framework

## Overview

Historical analogs are not predictions — they are probability-weighted scenario templates. Each analog provides a reference for (1) the macro conditions that preceded a market event, (2) the sequence of asset behavior during the event, and (3) the resolution pathway. When multiple features of the current environment match a historical period, the historical outcome distribution informs probabilistic positioning.

> "정답은 나와 있습니다. 역사의 패턴이 모두 해당되는 수준이기에" — The answer is already there in history; this level of pattern match is unmistakable

---

## Analog Selection Methodology

### Step 1: Pattern Similarity Screening
Use the quantitative pattern similarity model (see `quantitative_models.md`) to identify the top-10 historical periods with the highest multi-feature correlation to the current N-day window.

- Features: Price pattern, RSI trajectory, slope (rate of change), volatility, distance-to-52-week-high
- Window: Typically 100-150 trading days
- Output: Correlation scores for each historical match

### Step 2: Macro Condition Matching
From the top-10 pattern matches, filter for those where macro conditions were also similar:
- Comparable yield curve shape (steepening/flat/inverted)
- Comparable CAPE level (within ±5 of current)
- Comparable rate environment (absolute level and direction)
- Comparable EM vs. DM relative performance regime

### Step 3: Analog Weighting
Weight surviving analogs by:
1. Pattern correlation score (higher = more weight)
2. Macro condition match count (more matching conditions = more weight)
3. Exclude analogs where the macro regime fundamentally differs (even if pattern matches)

### Step 4: Forward Return Distribution
Construct a fan chart from weighted historical forward returns:
- Average path (weighted mean)
- 25-75 percentile band (likely range)
- 10-90 percentile band (extreme range)
- Report the 60-day forward mean return and range

### Step 5: Scenario Construction and Invalidation
For the top 2-3 analogs, construct explicit scenarios:
- Scenario A: [Analog 1] plays out — what macro signal confirms this?
- Scenario B: [Analog 2] plays out — what macro signal confirms this?
- Invalidation: What data point would reject each scenario?

---

## Core Historical Reference Points

### 1993 — Rate Constraint, Limited Advance

**Macro Context**:
- Fed raised rates in 1994 more aggressively than market expected
- S&P 500 ended 1994 effectively flat YoY (+1%)
- Yield curve normalized after early-1990s bull flattening
- Fourth quarter 1993 saw S&P 500 make new highs without the anticipated Santa Rally

**Pattern Match Conditions**:
- 4Q new high in equity markets without strong December follow-through
- Fed policy tightening ahead of consensus expectation
- Rate environment remained solid (not crisis, not easing)

**Key Lesson for US Markets**:
When the 4Q has established new highs but December closes weakly, and the rate environment is restrictive, the base case is sideways-to-modestly-lower for 12 months — not a crash, but meaningful "time cost" while fundamentals catch up to valuation.

**Analog Probability Usage**: Weight this scenario when the Fed is committed to higher-for-longer without imminent crisis trigger. Outcome: 0-2% S&P 500 return over the next 12 months, high volatility, no clear trend.

---

### 1997-1998 — EM Outperform, Structural Crisis, US Rebound

**The Two-Phase Pattern**:

**Phase 1 (1997 start)**: EM (especially Asia) dramatically outperformed DM.
- High-yield flows into emerging markets; carry trade funded in USD
- US market strong but EM stronger on absolute and relative basis
- Commodity prices still firm; "everything rally" in EM

**Phase 2 (1997 H2 - 1998)**: Asian financial crisis trigger.
- Thai baht crisis → contagion across EM
- EM equities collapsed (40-60% drawdowns)
- USD surged as EM devalued
- US absorbed global liquidity; domestic consumption drove continued US strength
- Russia default (1998) and LTCM near-collapse created brief US equity panic (-20%)
- Fed cut rates 75bp quickly → US equity recovered; EM did not for 5 years

**Key Structural Mechanism**:
The yield differential between US and EM compressed too much during the EM rally phase. When the carry trade unwound, dollar funding was withdrawn. Countries with high USD-denominated debt faced solvency crises. EM entered multi-year underperformance relative to DM.

**Pattern Match Conditions**:
- EM dramatically outperforming DM for an extended period (5+ months)
- Yield spread (US vs. EM) near historical boundary levels
- FX volatility in EM starting to rise
- Gold remaining firm while EM commodity prices peak

**Key Lesson for US Markets**:
When EM outperformance is driven by yield differential compression rather than fundamental improvement, the reversion is structural. US becomes the liquidity safe haven. After the crisis resolution, US equities recover first and fastest.

---

### 1998 October — Dotcom Pre-Bubble (Partial Inversion Analog)

**Macro Context**:
- CAPE at 35-36 (identical to 2025 levels)
- S&P 500 dividend yield at 1.28% (identical to 2025)
- Yield curve in partial inversion: US10Y-2Y positive, US10Y-3M negative (identical pattern observed only in 1998 Oct and March 2025)
- Russia default + LTCM crisis → Fed cut 75bp in rapid succession
- This liquidity injection fueled the final parabolic phase of the dotcom bubble

**The Resolution**: S&P 500 fell -33% from July to October 1998, then rallied +200% before the final bubble peak in March 2000.

**Pattern Match Conditions**:
- CAPE 35-37
- Dividend yield near 1.3%
- Partial inversion (10Y-2Y positive, 10Y-3M negative)
- Market leadership concentrated in a narrow, high-multiple sector

**Key Lesson for US Markets**:
This analog does NOT predict immediate crash — it predicts a final speculative extension driven by emergency liquidity injection. The current period matches many features, but differs in: (1) debt/GDP ratio is 2.3x higher than 1998, (2) active fiscal policy is constrained by TGA dynamics, (3) no geopolitical shock has yet triggered the Fed rescue.

The 1998 analog suggests: if a macro shock (credit event, EM crisis) forces the Fed to cut rates even with elevated inflation, a blow-off rally in growth equities becomes possible before the structural correction.

---

### 2007 — Bear Steepening Analog

**Macro Context**:
- Yield curve bear steepening (10Y-2Y spread widening while both rose)
- USD/EM FX anomaly: yield spread compressed but FX didn't respond as expected
- Credit spreads began widening in H2 2007 while equities held near highs
- Housing credit stress visible in credit market months before equity top

**Pattern Match Conditions**:
- Long-end rates rising faster than short-end (bear steepening)
- Credit spreads beginning to widen while equities hold
- EM-DM yield spread at boundary levels while EM FX weakening
- Gold and equities both at elevated levels simultaneously ("금주식 동시 버블")

**2007 Resolution Sequence**:
1. Gold and stocks made simultaneous highs (2007 mid-year)
2. Credit spreads widened first (HY before IG)
3. Equity market held for months after credit signal
4. Eventually equities followed credit down
5. Gold initially fell with equities, then recovered as safe haven
6. The lag between credit signal and equity top was ~6 months

**Key Lesson for US Markets**:
The 2007 analog is the most dangerous because the equity market maintained its highs for months after credit began signaling stress. Key tell: credit spreads widening while equity options market remains complacent (low VIX, low put/call).

---

### 2011 — Global Everything Rally → US Liquidity Absorption

**The Sequence**:
1. Post-2008 QE created a global "everything rally" from 2009-2011
2. Gold hit new highs in 2011 (~$1,900)
3. EM equities dramatically outperformed DM throughout 2010-2011
4. Commodities (oil, metals) at multi-year highs
5. S&P 500 recovered from 2008 lows and approached pre-crisis highs

**The Inflection (2011 H2)**:
- European sovereign debt crisis triggered risk-off
- Gold remained elevated (safe-haven transition)
- All other commodities (silver, copper, oil) collapsed
- EM equities fell sharply
- S&P 500 corrected but recovered quickly
- US absorbed all global liquidity; DXY bottomed and began multi-year uptrend
- EM equities entered a 5-year relative underperformance vs. US

**Pattern Match Conditions**:
- Extended period of EM >>> DM outperformance
- Gold at multi-year highs, other precious metals also rallying
- Q4 long-term rates pivoting higher (bear steepening)
- Commodity prices at extended levels

**The Resolution Pattern**:
- Phase 1: Non-gold commodities collapse first
- Phase 2: EM equities fall (harder and earlier than DM)
- Phase 3: Gold remains elevated as the sole commodity store of value
- Phase 4: US equities dip but recover on US liquidity absorption
- Phase 5: EM enters multi-year underperformance; US dollar multi-year uptrend

**Key Lesson for US Markets**:
When positioned anticipating the 2011 analog:
1. Short or reduce EM exposure during the outperformance phase
2. Long USD (wait for the pivot)
3. After the EM crisis trigger, rotate aggressively into US large-cap
4. Maintain gold exposure longer than non-precious commodities
5. EM underperformance vs. US persists for years, not months

**Gold Lag Signal**: After gold peaks and begins declining, equities may have 3-12 months before the broader correction materializes. Gold declining while equities hold is a *leading* signal of the final leg before the correction.

---

### 2013 / 2023 — Bear Steepener Historical Precedent

**Context**: Periods when the yield curve bear-steepened (long rates rising faster) without an immediate crisis.

**2013**: "Taper Tantrum" — Fed signaled QE tapering, long rates spiked, but the economy was stable enough to absorb higher rates. S&P 500 continued higher after initial volatility.

**2023 Oct**: US10Y hit 5% — Dimon "sell" call at the peak. Market corrected briefly, then recovered as rate peak was confirmed.

**Pattern Match Conditions**:
- Bear steepening without credit crisis
- Economy still growing (not in recession)
- Market participants questioning whether rates will break the economy

**Key Lesson**: Bear steepening without credit crisis = volatility but not necessarily crash. The 5% US10Y level has been a historical rejection zone — rates reach it but cannot sustain above it. Hawkish extreme statements (Dimon "8% possible") at rate peaks are contrarian buy signals for bonds.

---

### 2018-2019 — Protective Rate Cut → Inflation Chain

**Context**: Fed raised rates through 2018 Q4, causing a sharp equity correction (-20%). Fed then pivoted to "insurance cuts" (3 cuts in 2019) despite no recession.

**The Chain**:
1. Aggressive tightening → equity correction → Fed pivot
2. Insurance cuts without recession = liquidity injection into a still-growing economy
3. Excess liquidity contributed to asset price inflation (2019-2020)
4. COVID stimulus layered on top → inflation breakout in 2021-2022

**Key Lesson**: Protective rate cuts without a genuine recession create future inflation. If the Fed cuts in 2025-2026 in response to market stress rather than economic recession, the same chain may repeat. The cut itself becomes the next problem.

---

### 2022 Q3 / 2024 H2 — Reversal from EM/HY Leadership

**Context**: Policy-driven EM or high-beta outperformance that reversed sharply:
- Policy catalysts (government intervention, special programs) drove equity rallies
- Fundamentals (yield differential, FX) were unfavorable throughout
- The rally was "borrowed" — running ahead of fundamentals
- Trigger: carry trade unwind (yen carry in August 2024) or rate shock → EM collapsed

**Pattern Match Conditions**:
- Government policy driving equity rally independent of macro fundamentals
- Yield spread remains unfavorable (US rates still higher)
- RSI reaching 80 during the policy-driven rally
- Institutional buyers concentrated (artificial support visible)

---

### 2023 Summer Goldilocks vs. 2024 Reverse Goldilocks

**2023 Summer "Goldilocks"**: Economy growing + inflation falling + rates stable = perfect environment for risk assets. S&P 500 rallied ~15% in 4 months.

**2024 "Reverse Goldilocks"**: Economy still growing BUT inflation re-accelerating + rates rising again. The same strong economy that supports earnings is also supporting inflation, which prevents rate cuts.

**Transition Signal**: Cleveland Fed CPI nowcast running above consensus + PMI rising + wage growth stable = the Goldilocks window is closing. Position for the transition before the market confirms it.

---

## Analog Validation and Invalidation

### Validation Signals
An analog is validated when:
1. The macro trigger event occurs (Fed rate cut, EM credit event, credit spread blowout)
2. The sequence of asset moves matches the historical pattern (phase by phase)
3. The pattern similarity correlation score remains high as time passes

### Invalidation Signals
Abandon an analog when:
1. A key macro condition diverges from the historical period (e.g., Fed does the opposite of what happened in the analog)
2. The "weak link" assets (EM, HY) fail to crack despite the conditions predicting they should
3. A new structural factor emerges with no historical precedent (e.g., unprecedented fiscal policy tool)

### "Dead Cat Bounce" vs. Structural Reversal Classification
After a major decline, distinguish between a dead cat bounce and a structural reversal by checking:
1. **Volume profile**: Reversal has expanding volume on up-days; dead cat has declining volume
2. **Credit confirmation**: HY spreads tightening = structural; HY spreads flat = dead cat
3. **Breadth**: Advancing stocks broadly increasing = structural; narrow leadership = dead cat
4. **Rate response**: If the rally coincides with rate decline = structural; if rates are still rising = dead cat

### "이번엔 다르다" (This Time is Different) Bias vs. Genuine Structural Difference

The discipline:
- Acknowledge structural differences explicitly and state their impact on the analog's relevance
- "1998년과 다른 점: GDP 대비 부채비율이 2.3배 높고, TGA가 active policy를 제약" — structural differences explicitly stated
- But do NOT abandon the analog just because of differences. Ask: do these differences change the DIRECTION of the outcome, or just the MAGNITUDE and TIMING?
- Most "this time is different" arguments are wrong. But some structural changes ARE genuine. The discipline is: quantify the difference, assign a probability adjustment, maintain the analog with reduced weight rather than abandoning it entirely.

---

## Multiple Analog Scenario Framework

When the market matches multiple analogs simultaneously, construct weighted scenarios:

**Example: 2025-2026 Assessment (from methodology)**
- Analog 1: 1993 (probability: lower) — Fed restraint, sideways market, no crisis trigger
- Analog 2: 1997 (probability: higher) — EM outperform peak → structural EM crisis → US absorbs liquidity
- Analog 3: 1998 Oct (partial) — partial curve inversion precedes final speculative push

Probability weighting:
- 1993 analog: ~30% (requires smooth soft landing, Fed pivots gently)
- 1997 analog: ~50% (EM structural stress is already visible; yield differential mechanism active)
- 1998 analog: ~20% (crisis triggers emergency Fed cut → speculative blow-off)

**Position implications from this weighted scenario**:
- Maintain US equity exposure but reduce EM exposure
- Wait for EM crisis trigger before aggressive US long positioning
- If Fed cuts aggressively: look for blow-off in growth equities (1998 phase)
- Long-term: position for dollar strength and US dominance (1997 outcome)

> "저는 개인적으로 93년보다 97년에 더 가깝다고 생각하는 입장입니다" — base case is the 1997 analog, not the softer 1993 analog

---

## US Credit Downgrade Response Pattern

Historical precedent: S&P US credit downgrade (2011) and Fitch downgrade (2023).
- Initial reaction: Sharp equity selloff, VIX spike
- Resolution: Both times the market recovered within weeks
- Mechanism: US Treasuries still function as global reserve asset despite the downgrade; "약한 고리" EM assets sell off harder than US because the downgrade triggers global risk-off but the dollar strengthens anyway

**Key insight**: A US credit downgrade is paradoxically positive for the dollar in the short term because it triggers global risk-off that drives capital into dollar assets.
