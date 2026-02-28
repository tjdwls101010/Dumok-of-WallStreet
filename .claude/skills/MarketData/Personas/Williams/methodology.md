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

### Key Principle: Accuracy-to-Volume Trade-Off

The percentage of range added determines a critical trade-off: **range % increases → fewer trades, higher accuracy, larger average profit**. This is one of the most important optimization levers in the system.

**Bond Market Evidence** (1990-1998):
- 100% of range: 80% accuracy on 651 trades, $173 avg profit/trade
- Restricting to best TDW days: **84% accuracy**, trades cut in half, drawdown reduced from $10,031 to **$3,500**

**S&P 500 Optimization Evidence** (1982-1998):
- Using 50% volatility expansion on all days: $227,822 profit, 74% accuracy, 1,333 trades, $170 avg/trade
- Optimized 40% buy / 200% sell with TDW filter: $213,560 profit, **83% accuracy**, 850 trades, **$251 avg/trade** -- reducing trades by 46% while increasing avg profit by 47%

### Entry Point Comparison Framework (Electronic Era)

Williams tested five reference points for the volatility expansion value post-2000 on the S&P 500 E-Mini, each with its optimal ATR percentage:

| Reference Point | Best ATR % | Net Profit | Characteristic |
|----------------|-----------|-----------|----------------|
| Tomorrow's Open | 60% | ~$70,000 | Highest net profits but inconsistent equity until 2007 |
| Prior Day's Close | 60% | ~$30,000 | Worked then fell apart from 2008 |
| Prior Day's Low | 20% | ~$60,000 | Most consistent equity line; best fit overall |
| Prior Day's High | 30% | ~$15,000 | Worked well until 2008 bear market |
| Mid-price (H+L)/2 | Various | Mixed | Less reliable than extremes |

**Williams' conclusion**: The prior day's low with a 20% ATR expansion and the next day's opening with a 60% ATR expansion are the two most productive reference points. The low-based reference produces the most consistently rising equity line across market regimes. The critical insight is that **what reference point you use matters enormously** -- each requires a different optimal volatility expansion percentage.

**TDW confirmation** (Electronic era, Low + 20% ATR): Monday and Tuesday are the strongest buy days; **Wednesday should be excluded** entirely. Dropping Wednesday improved profits substantially and reduced drawdown by approximately 65%.

---

## Swing Point Hierarchy

Williams defines market structure through a fractal hierarchy of swing points that mechanically identifies trend at all timeframes:

### Short-Term Swing Points
- **Short-Term Low**: Any daily low with higher lows on both sides of it
- **Short-Term High**: Any daily high with lower highs on both sides of it

#### Inside Day Rules
Inside days (lower high + higher low) appear approximately 7.6% of the time (3,892 occurrences in a study of 50,692 trading sessions across nine major commodities). They are **ignored** in swing identification because they represent congestion -- the current swing did not go further, but it did not reverse either. The correct response to an inside day is: **wait, don't trade**. Do not use inside days to generate short-term swing points until the congestion resolves.

#### Outside Day Interpretation
Outside days (higher high AND lower low than the prior day) occur approximately 7% of the time (3,487 out of 50,692 sessions). When an outside day appears, resolve the ambiguity by examining the **open-to-close direction** of that day: if the close is above the open, treat the day as an up day for swing purposes; if below, treat as a down day. This directional resolution is necessary because the bar's range engulfed both sides, creating conflicting swing signals.

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

### Specific Implementation Rules

- **Consecutive small-range count**: Track the number of consecutive days where the daily range is below its recent moving average. The longer the compression sequence, the more explosive the potential breakout. This is not a time cycle but a price cycle -- the coiling can last different durations each time.
- **Direction bias combination**: Combine range analysis with close position (upper or lower portion of the daily range) to determine likely breakout direction. A string of small-range days with closes consistently in the upper portion of the range biases the expected expansion to the upside.
- **Volatility expansion as entry trigger**: The breakout from compression is captured by the volatility breakout system. Add a percentage of recent range (or ATR) to a reference point. The percentage chosen interacts with the range state: during extreme compression, even a small percentage expansion represents a significant move relative to recent ranges, producing higher-probability signals.
- **TDW overlay**: Not all breakout days from compression are equal. Apply the TDW filter to time your entry to the most favorable day. In the S&P, Monday-Tuesday breakouts from compression produce the strongest follow-through.

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

## Down-Close Bias (Non-Random Market Evidence)

Williams provides statistical evidence that markets are not random. In a truly random market, the probability of an up close following a down close should remain at the baseline ~53.2%. Instead, the data shows a significant bias:

| Condition | Average Up Close Probability | Sample Size |
|-----------|------------------------------|-------------|
| After 1 down close | **55.8%** | ~22,970 observations across 10 major markets |
| After 2 consecutive down closes | **55.2%** | ~10,683 observations |
| After 3 consecutive down closes | **~55%** (varies by market) | Further filtered |

The bias is consistent across Bellies (55%), Cotton (53%/55%), Soybeans (56%/56%), Wheat (53%/55%), British Pound (57%/56%), Gold (58%/55%), Nikkei (56%/60%), Eurodollar (59%/56%), Bonds (54%/52%), and S&P 500 (55%/53%). This is not a trading system in itself, but it is proof that price action contains exploitable non-random dependencies -- the foundation upon which all subsequent pattern work is built.

**Practical application**: The Dax index (1998-2011) demonstrated this escalating: buying after every down close lost $60,558; after 2 down closes, loss narrowed to $1,568; after 3 down closes, 334 trades produced $25,295 at 55% accuracy. Restricting to Tuesdays, Thursdays, and Fridays after 3 consecutive down closes: 204 trades, 58% accuracy, $44,795 profit.

---

## Close-as-Trend-Indicator

Williams decomposes each day's price action into buying power and selling pressure relative to the close:

- **Buying Power** = Close - Low (how far buyers pushed price up from the day's worst level)
- **Selling Pressure** = High - Close (how far sellers pushed price down from the day's best level)

### Interpretation Framework

When Buying Power consistently exceeds Selling Pressure across recent days, the market is under accumulation. When Selling Pressure dominates, distribution is occurring. The close's position within the day's range is the single most important piece of information about who won the daily battle.

### The Real Secret to Short-Term Trading

Large-range up days close at or near the high. Large-range down days close at or near the low. This means the optimal strategy for short-term traders is to hold to the close -- not to dance in and out.

#### Large-Range Day Characteristics

On large-range days, approximately **87% of the time** the open occurs at one extreme of the day's range and the close at the opposite extreme. Specifically (T-Bonds, 1970-1998): if the dip from Open to Low is less than 20% of yesterday's range, there is an 87% probability the day closes above the open. This is the "law of gravity" for intraday price movement -- large-range up days open near the low and close near the high; large-range down days open near the high and close near the low. Do NOT try to buy far below the open on expected large up days, because they rarely trade much below the opening.

#### Holding Period Optimization Evidence

Williams proved the holding period effect with a simple S&P 500 system (buy on Monday open if below Friday's close, 389 trades, 1982-1998):

| Exit Strategy | Net Profit | Avg Profit/Trade | Accuracy | Drawdown |
|--------------|-----------|-----------------|----------|----------|
| $500 target | **-$8,150** | -$21 | 59% | $12,837 |
| $1,000 target | $13,737 | $35 | 55% | $8,887 |
| Exit at close | $39,075 | $100 | 53% | $6,550 |
| Hold to next day's close | $68,312 | $172 | 55% | $11,000 |
| Hold 6 days | **$71,600** | **$251** | 52% | $19,725 |

The lesson is unambiguous: the shorter the holding period, the less opportunity for profits. The $500 target trader had the highest accuracy (59%) yet lost money because the average profit was too small to overcome the average loss. The 6-day hold produced the highest net profit with the best average per trade ($251), nearly doubling the close-exit results. As Jesse Livermore stated: "It was never my thinking that did it for me, it was my sitting that made the big money."

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
