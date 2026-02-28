# Williams Core Trading Framework

## Overview

Larry Williams' methodology is built on the premise that markets have definite structure -- prices move from point to point in identifiable swings driven by volatility cycles and the relationship between open, high, low, and close. The framework is designed for short-term position trading with a 2-5 day holding period, capitalizing on explosive range expansion days while managing risk through precise entry mechanics and money management. The electronic era adaptation shifts reference points from the opening price to the prior day's low/close, using Average True Range (ATR) as the volatility measure.

---

## Volatility Breakout System

### Classical Formula (Pit Trading Era)

The original system adds a percentage of the previous day's range to the next day's opening price:

- **Buy Signal**: Open + (Pct x Yesterday's Range)
- **Sell Signal**: Open - (Pct x Yesterday's Range)

This was the most consistently profitable mechanical entry technique Williams ever discovered. Across 11 major commodity markets, it produced profits in every single one when tested from the 1970s through 1998. Accuracy ranged from 44% to 60% depending on the market and percentage used, with average profits per trade varying from $73 (Cotton at 60%) to $2,157 (Coffee at 130%).

### Electronic Era Adaptation

The transition from pit to electronic trading fundamentally changed market structure. The opening price lost its explosive character because electronic markets close only hours before reopening, eliminating the 18-hour gap that once made the open a critical reference point. Williams' research on post-2000 data identified new reference points:

**Primary Reference: Prior Day's Low**
- **Buy Entry**: Low + (20% of 3-day ATR)
- **Condition**: Prior day must have a down close AND close < open (double confirmation of selling pressure)
- **Best TDW**: Monday and Tuesday showed the strongest results; Wednesday was the worst day and should be excluded

**Secondary Reference: Prior Day's Open/Close**
- **Buy Entry**: Open + (60% of 3-day ATR)
- **Condition**: Same down close + close < open requirement
- **Characteristic**: Higher net profits ($70,000 in testing) but inconsistent equity curve until 2007

### Key Principle

The percentage of range added determines a critical trade-off: lower percentages generate more trades with lower accuracy; higher percentages generate fewer trades with higher accuracy and larger average profits. In Bonds, using 100% of range produced 80% accuracy on 651 trades; restricting to the best TDW days boosted accuracy to 84% while cutting trades in half and reducing drawdown from $10,031 to $3,500.

---

## Swing Point Hierarchy

Williams defines market structure through a fractal hierarchy of swing points that mechanically identifies trend at all timeframes:

### Short-Term Swing Points
- **Short-Term Low**: Any daily low with higher lows on both sides of it
- **Short-Term High**: Any daily high with lower highs on both sides of it
- Inside days (lower high + higher low, ~7.6% of all days) are ignored in swing identification
- Outside days (~7% of all days) are resolved by examining the open-to-close direction

### Intermediate-Term Swing Points
- **Intermediate Low**: Any short-term low with higher short-term lows on both sides
- **Intermediate High**: Any short-term high with lower short-term highs on both sides

### Long-Term Swing Points
- **Long-Term Low**: Any intermediate low with higher intermediate lows on both sides
- **Long-Term High**: Any intermediate high with lower intermediate highs on both sides

### Practical Application

Once you understand this nesting structure, you can identify trend changes in real-time. When price rallies above the high of a day that formed a short-term low, that low is confirmed. If this new short-term low is higher than the prior short-term low, it may confirm an intermediate low, which in turn may confirm a long-term low. This enables entry at the very start of a new up-leg.

**Price Target**: Intermediate High + (High - Low of the intermediate swing range). This projection uses the amplitude of the prior swing to estimate the next move's reach.

These swing points are the only valid support and resistance levels Williams has found. Their violation provides actionable information about trend change and serves as the basis for stop-loss placement.

---

## Range Expansion/Contraction Axiom

This is the most fundamental cycle Williams identifies -- and it is not a time cycle but a price cycle:

**Small ranges beget large ranges. Large ranges beget small ranges.**

This axiom holds across all markets, all countries, and all timeframes (5-minute bars through monthly bars). It is driven by the natural cycle of human attention: investors lose interest (small ranges), then gain interest (large ranges), and the cycle repeats.

### Quantitative Rules

1. **Position during small ranges**: When a market that normally has large daily ranges enters a period of compressed, small-range days, an explosive move is imminent. This is when to establish positions.
2. **Exit during large ranges**: After a cluster of large-range days, expect range contraction. Do not enter new positions during large-range periods -- this is the classic sucker play that traps the public.
3. **Measurement**: Compare current range to a moving average of recent ranges. When the ratio drops significantly below 1.0, the market is coiled for a move.

### The Public's Error

The public is attracted to markets showing large price changes, incorrectly believing the current large change will continue. Knowledgeable traders do the opposite: they look for historically volatile markets that have recently produced small ranges, knowing a large-range day is approaching.

---

## Open-to-Low/High Relationship

Large-range days have a statistically provable structure in how they trade from open to close:

### Quantitative Evidence (T-Bonds, 1970-1998)

- If the dip from Open to Low is < 20% of yesterday's range: **87% probability** the day closes above the open
- If Open-to-Low dip < 10%: **42% probability** of closing $500+ above open; **15% probability** of closing $1,000+ above open
- If Open-to-Low dip > 70%: **near-zero probability** of a large-range up close

### Trading Rules

1. Do NOT try to buy far below the open on expected large up days -- large-range up days rarely trade much below the opening
2. If long and price falls significantly below the open, exit -- the probability of a large-range up close has collapsed
3. Mirror logic applies for shorts: do not sell far above the open on expected down days
4. If short and price rallies significantly above the open, exit

These rules are universal across freely traded markets and represent the "laws of gravity" of intraday price movement.

---

## Close-as-Trend-Indicator

Williams decomposes each day's price action into buying power and selling pressure relative to the close:

- **Buying Power** = Close - Low (how far buyers pushed price up from the day's worst level)
- **Selling Pressure** = High - Close (how far sellers pushed price down from the day's best level)

### Interpretation Framework

When Buying Power consistently exceeds Selling Pressure across recent days, the market is under accumulation. When Selling Pressure dominates, distribution is occurring. The close's position within the day's range is the single most important piece of information about who won the daily battle.

### The Real Secret to Short-Term Trading

Large-range up days close at or near the high. Large-range down days close at or near the low. This means the optimal strategy for short-term traders is to hold to the close -- not to dance in and out. Williams proved this with the same S&P Monday-buy system:
- Exit at $500 target: LOST $8,150 (59% accuracy but average profit too small)
- Exit at $1,000 target: Made $13,737 ($35/trade average)
- Exit at close: Made $39,075 ($100/trade average, drawdown cut to $6,650)
- Hold to next day's close: Made $68,312 ($172/trade average)
- Hold 6 days: Made $71,600 ($251/trade average)

The 2-5 day optimal holding period balances the need for time to create profits against the risk of overstaying.

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
