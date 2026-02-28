# Williams Core Trading Framework

## Overview

Larry Williams' methodology is built on the premise that markets have definite structure -- prices move from point to point in identifiable swings driven by volatility cycles and the relationship between open, high, low, and close. The framework is designed for short-term position trading with a 2-5 day holding period, capitalizing on explosive range expansion days while managing risk through precise entry mechanics and money management. The electronic era adaptation shifts reference points from the opening price to the prior day's low/close, using Average True Range (ATR) as the volatility measure.

---

## Volatility Breakout System

The volatility breakout adds a percentage of recent volatility (ATR) to a reference point. In the pit era, the reference was the opening price; in the electronic era, the prior day's low is the most reliable reference.

### Key Principle: Accuracy-to-Volume Trade-Off

The percentage of range added determines a critical trade-off: **range % increases → fewer trades, higher accuracy, larger average profit**. This is one of the most important optimization levers in the system.

### Electronic Era Adaptation

The transition from pit to electronic trading fundamentally changed market structure. The opening price lost its explosive character because electronic markets close only hours before reopening. Williams' research on post-2000 data identified the prior day's low as the most consistent reference point, producing the most steadily rising equity line across market regimes. The critical insight is that **what reference point you use matters enormously** -- each requires a different optimal volatility expansion percentage.

**TDW confirmation**: Monday and Tuesday are the strongest buy days; **Wednesday should be excluded** entirely.

---

## Swing Point Hierarchy

Williams defines market structure through a fractal hierarchy of swing points that mechanically identifies trend at all timeframes:

### Short-Term Swing Points
- **Short-Term Low**: Any daily low with higher lows on both sides of it
- **Short-Term High**: Any daily high with lower highs on both sides of it

**Inside Day Rules**: Inside days are **ignored** in swing identification because they represent congestion -- the current swing did not go further, but it did not reverse either.

**Outside Day Interpretation**: When an outside day appears, resolve the ambiguity by examining the **open-to-close direction** of that day: if the close is above the open, treat the day as an up day; if below, treat as a down day.

### Intermediate-Term Swing Points
- **Intermediate Low**: Any short-term low with higher short-term lows on both sides
- **Intermediate High**: Any short-term high with lower short-term highs on both sides

### Long-Term Swing Points
- **Long-Term Low**: Any intermediate low with higher intermediate lows on both sides
- **Long-Term High**: Any intermediate high with lower intermediate highs on both sides

### Practical Application

Once you understand this nesting structure, you can identify trend changes in real-time. When price rallies above the high of a day that formed a short-term low, that low is confirmed. If this new short-term low is higher than the prior short-term low, it may confirm an intermediate low, which in turn may confirm a long-term low. This enables entry at the very start of a new up-leg.

These swing points are the only valid support and resistance levels Williams has found. Their violation provides actionable information about trend change and serves as the basis for stop-loss placement.

---

## Range Expansion/Contraction Axiom

This is the most fundamental cycle Williams identifies -- and it is not a time cycle but a price cycle:

**Small ranges beget large ranges. Large ranges beget small ranges.**

This axiom holds across all markets, all countries, and all timeframes (5-minute bars through monthly bars). It is driven by the natural cycle of human attention: investors lose interest (small ranges), then gain interest (large ranges), and the cycle repeats.

### Interpretation Rules

1. **Position during small ranges**: When a market enters compressed, small-range days, an explosive move is imminent
2. **Exit during large ranges**: After a cluster of large-range days, expect contraction. Do not enter new positions during large-range periods
3. **Direction bias**: Combine range analysis with close position (upper or lower portion of the daily range) to determine likely breakout direction
4. **TDW overlay**: In the S&P, Monday-Tuesday breakouts from compression produce the strongest follow-through

### The Public's Error

The public is attracted to markets showing large price changes, incorrectly believing the current large change will continue. Knowledgeable traders do the opposite: they look for historically volatile markets that have recently produced small ranges, knowing a large-range day is approaching.

---

## Close-as-Trend-Indicator

Williams decomposes each day's price action into buying power and selling pressure relative to the close:

- **Buying Power** = Close - Low (how far buyers pushed price up from the day's worst level)
- **Selling Pressure** = High - Close (how far sellers pushed price down from the day's best level)

### Interpretation Framework

When Buying Power consistently exceeds Selling Pressure across recent days, the market is under accumulation. When Selling Pressure dominates, distribution is occurring. The close's position within the day's range is the single most important piece of information about who won the daily battle.

### The Real Secret to Short-Term Trading

Large-range up days close at or near the high. Large-range down days close at or near the low. This means the optimal strategy for short-term traders is to hold to the close -- not to dance in and out. The 2-5 day optimal holding period balances the need for time to create profits against the risk of overstaying.

---

## Five Elements of Market Analysis

Williams identifies five data sources for identifying short-term explosions:

1. **Price Patterns**: Short-term bar patterns that trap the public into wrong-side positions
2. **Price Indicators**: Mathematical tools derived from price (oscillators, moving averages) -- useful but self-referential
3. **Trend/Momentum**: The direction and force of price movement
4. **Intermarket Relationships**: How one market predicts another (e.g., Bonds predict S&P)
5. **Sentiment/COT Data**: Tracking the crowd that is usually wrong (public) vs. the crowd usually right (Commercials)

The strongest trades occur when multiple elements align -- Williams calls this "stacking the deck."

---

## Script Output Interpretation Guide

### Volatility Breakout Analysis

When reviewing volatility breakout output, focus on:
- **ATR context**: Is the current ATR compressed relative to recent history? Compressed ATR means the market is coiled for expansion
- **Entry level distance**: How far is the breakout level from the current price? Closer levels mean higher probability of triggering but lower confirmation of genuine momentum
- **TDW alignment**: Does the signal day match historically favorable trading days for the instrument?

### Swing Point Analysis

When interpreting swing point output:
- **Hierarchy level**: A short-term swing point is a weak signal alone; an intermediate swing confirming a long-term trend change is the strongest signal
- **Trend direction**: Are short-term lows making higher lows (bullish) or lower lows (bearish)?
- **Proximity to confirmed points**: A trade near a confirmed intermediate low with upward nesting is the ideal Williams entry

### Range Analysis

When interpreting range analysis output:
- **Range ratio**: Current range vs. average range. Ratios well below 1.0 signal imminent expansion
- **Range sequence**: Count consecutive small-range days. The longer the compression, the more explosive the potential breakout
- **Direction bias**: Combine range analysis with close position (upper/lower portion of range) to determine likely breakout direction

### Williams %R

Williams %R measures where the current close sits relative to the recent high-low range:
- **Values near 0 (overbought)**: Price is near the top of its recent range. In trending markets, this is a sign of strength, not a sell signal
- **Values near -100 (oversold)**: Price is near the bottom of its recent range. Combined with other setup conditions, this identifies potential reversal zones
- **Divergence**: %R making higher lows while price makes lower lows signals weakening downside momentum
