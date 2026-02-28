# TraderLion Market Environment Analysis

## Overview

Market environment analysis methodology combining market cycle identification, institutional gauge assessment, and breadth analysis. Determines when to be aggressive and when to protect capital by reading cyclical behavior and institutional participation.

> "At least 50% of the whole game is the general market." — William O'Neil. Three out of four stocks follow the trend of the general market.

---

## Market Cycle Framework

The market alternates between uptrends and downtrends driven by two layers: technical/liquidity (longer-term bull/bear) and human psychology (shorter-term fear/greed).

### Stage 1: Downcycle
- Market in sustained decline or choppy sideways. Leadership failing, trends short-lived.
- Limit exposure or take select shorts. Stage 1-2 traders: primarily cash.
- Watch for RS stocks holding up well; build watchlists for the next cycle.
- "Trying to trade long in a downcycle is like sailing upwind."

### Stage 2: Bottoming / Cycle Transition
- **Index support holding**: Rounded bottom or capitulatory drop that recovers quickly
- **Decoupling / RS divergence**: Key stocks begin ignoring general weakness — institutions stepping in
- Be on high alert. Prepare focus list of strongest RS stocks. Do NOT go full exposure — test the waters.

### Stage 3: Upcycle
- **Start signal**: Close above 21 EMA (QQQ reference)
- **End signal**: Two closes below 21 EMA, second close below prior day's low
- **Days 1-3** (Best R/R): Add exposure via ETFs or best setup stocks. Stage 1-2: half size, build after traction.
- **Days 4-6** (First Stress Test): Natural profit-taking creates a sudden negative day. How leaders respond provides critical info. Goal: portfolio positioned so even if all stop out, equity curve makes higher low.
- **Later in Cycle**: Continue fresh trades but become stricter. Late-cycle breakouts are laggards, more prone to failure. Keep cost basis low enough for swing-to-position transitions.
- **False Starts**: Every sensitive system produces them. Differentiator is follow-through: leading stocks confirm with strong action, gap ups, breakouts.
- **Cycle Strength**: Strongest cycles follow significant corrections or extended bear markets. Calibrate initial aggression based on prior correction depth.

### Group Base Formation Signal
When 3+ stocks in the same theme simultaneously form similar bases, this indicates sector-level accumulation. When the first breaks out, remaining stocks become higher-probability candidates. During Stage 2 transitions, this is one of the strongest confirmation signals.

### Progression Principle
Progress from interpretation (reacting to confirmed signals) to anticipation (positioning before confirmation). Stage 1-2 traders: interpret accurately. Stage 3-4 traders: anticipate cycle transitions and position earlier.

---

## Market Gauge System

Key stocks that institutions currently support, serving as leading indicators of risk appetite.

- **Stalwarts** (permanent): 2-3 large-cap stocks with heavy index weighting and high institutional ownership. Reflect risk-on/risk-off regardless of cycle.
- **Cycle Leaders** (rotational): 1-2 stocks from current dominant theme. Rotate as leadership shifts. Strongest RS stock in leading group is primary candidate.
- **Theme Type Context**: Transformative themes (AI, semis) produce stronger, longer-lasting leadership than Cyclical themes (energy, banks).

| Gauge Signal | Market Reading |
|---|---|
| Above key MAs, holding psychological levels | Positive — other trades will work well |
| Breaking below key levels | Deteriorating — increase caution |
| Showing RS during market weakness | Potential cycle turn — prepare for uptrend |

- Add a point to cycle score if gauge stocks are above a relevant MA
- Update gauge stocks as market leadership rotates

---

## Breadth and Cycle Confirmation

### Point System: Composite Cycle Score

→ pipeline의 `cycle_score` 참조

| Component | Signal | Points |
|---|---|---|
| **Index Trend** | QQQ above rising 21 EMA | +1 |
| **Index Trend** | QQQ above rising 50 SMA | +1 |
| **Index Trend** | QQQ above rising 200 SMA | +1 |
| **Breadth** | Market breadth expanding | +1 |
| **Breadth** | Leadership breadth healthy | +1 |
| **Gauge** | Gauge stocks above key MAs | +1 |
| **Gauge** | Gauge stocks holding psychological levels | +1 |
| **Feedback** | Recent trades working (positive win rate) | +1 |

**Score Interpretation**:
- 6-8 points: Strong upcycle — aggressive exposure
- 4-5 points: Normal conditions — standard sizing
- 2-3 points: Choppy/transitional — reduced sizing, tighter stops
- 0-1 points: Downcycle — minimal exposure, cash preservation

### Trend Definitions by Timeframe

Using QQQ as reference:
- **Short-term uptrend**: Above a rising 10 SMA
- **Intermediate-term uptrend**: Above a rising 21 EMA
- **Long-term uptrend**: Above a rising 200 SMA

| Market State | Action |
|---|---|
| Uptrends on all timeframes, strong leadership | Maximum exposure, full sizing |
| Long-term uptrend, short-term downtrend, leaders weakening | Reduce to 40% exposure, 5% positions |
| Long-term downtrend, lack of leadership | Minimal exposure, cash |
| Long-term downtrend, short-term uptrends, developing leadership | Test waters cautiously |
| Choppy short/medium trends, mixed leadership | Reduce position count and size |

### Breadth Interpretation

Breadth metrics confirm cycle stage. Pipeline quantifies these — use output for scoring:
- **Expanding breadth** during upcycle confirms broad institutional participation
- **Narrowing breadth** late in cycle warns of distribution beneath the surface
- **Breadth divergence** (indexes at highs, fewer stocks participating) is a late-cycle topping signal
- Track screen result counts over time as an independent breadth confirmation signal

### Stage 4: Topping / Cycle End

- **Trigger**: Two closes below 21 EMA with second close below prior day's low
- Leading stocks showing distribution (key reversals, failed breakouts) → pipeline의 `sell_signal_audit` 참조
- Breadth narrowing while indexes may still hold; gauge stocks breaking key levels
- Reduce exposure systematically (Grade D positions first), tighten stops, shift to capital preservation

---

## Breakout Pattern Recognition

### Successful Breakout Characteristics
- Volume 25%+ above average at breakout
- Immediate follow-through: strong close (high CR), trends above VWAP on breakout day
- Subsequent bars remain constructive (up on volume, tight on low volume)
- MAs aligned and rising (21 EMA > 50 SMA > 200 SMA)
- Part of a leading theme with institutional sponsorship
- Early cycle timing: higher probability, stronger follow-through

### Failed Breakout Characteristics
- Volume average or below at breakout — lack of conviction
- Breakout bar closes in lower half of range (low CR, distribution signal)
- Quick reversal below pivot within 1-3 days
- Non-constructive bars follow: up on low volume, down on high volume
- Choppy stock character (gaps up and down, no MA respect) → pipeline의 `stock_profile.character_grade` 참조
- Late cycle timing with narrowing breadth

→ pipeline의 `constructive_ratio`, `volume_edge`, `stock_profile` 참조

See SKILL.md → Macro, Data Sources
