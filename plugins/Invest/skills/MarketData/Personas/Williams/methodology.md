# Larry Williams Short-Term Trading Methodology

## Overview

Volatility-breakout-driven short-term trading methodology that identifies trend-setting price explosions, enters using range-expansion entry formulas, and captures two-to-five-day swings while holding profits through the close. Rooted in the principle that market structure is mechanical and readable, with prices moving from swing point to swing point in identifiable patterns. Combines volatility breakout entries with Trading Day of Week (TDW) filters, intermarket trend confirmation, and rigorous money management.

> "It was never my thinking that did it for me, it was my sitting that made the big money. My sitting!" -- Jesse Livermore, as quoted by Williams

> "I believe the current trade I am in will be a loser ... a big loser at that. This continues to be my most important market mantra. Winners we can handle, it's the losses that kill you."

---

## Core Philosophy

### Money Management Is the Highest Priority

Every wipeout comes from placing too large a bet or holding a losing position too long. Knowing how to deal with your resources has the highest priority over market direction or timing. God does not deny, He just delays -- the market will eventually do what you expect, but only if you survive long enough. Master your defeats first; the wealth follows.

### Believe the Current Trade Will Lose

Adopt the belief that the current trade will most likely not work out. This is not pessimism -- it is the most powerful risk management mindset available. It forces you to: (1) set stops on every trade, (2) never oversize a position, (3) take the first lifeboat rather than going down with the ship. Positive beliefs about winning lead to holding losers too long and oversizing positions.

### Time Is Your Ally

The shorter the time frame, the less money you make. This is absolute, unequivocal investment truth. Profits need time to grow. Day traders limit their profit potential by definition. The optimal trading window is two-to-five-day swings. Hold winners to the close at minimum -- never exit intraday on a winning position unless stopped out.

### Speculation = Observation + Preservation

The word "speculate" comes from the Latin "specular" (to observe). We observe, place our bets with edges, and protect positions with stops to preserve capital. Develop strategies with winning advantages, work the odds, and stay alert to changes.

### Adapt to Change

Fundamentals are permanent; application changes. Markets evolve -- pit sessions gave way to electronic trading, opening price dynamics shifted, new instruments emerge. Great traders notice changes and react. Losers follow black boxes blindly. Stay on your toes.

---

## Market Structure Framework

### Swing Point Identification

Market structure is mechanical and can be read like a language. The alphabet consists of each day's open, high, low, and close. All market movement can be identified through nested swing points.

**Short-Term Low**: Any day with higher lows on BOTH sides. Confirmed when price rallies above the high of the day that made the low.

**Short-Term High**: Any day with lower highs on BOTH sides. Confirmed when price falls below the low of the day that made the high.

**Intermediate-Term Low**: A short-term low with higher short-term lows on both sides.

**Intermediate-Term High**: A short-term high with lower short-term highs on both sides.

**Long-Term Low**: An intermediate-term low with higher intermediate-term lows on both sides.

**Long-Term High**: An intermediate-term high with lower intermediate-term highs on both sides.

### Special Day Types

- **Inside Days** (~7.6% of all days): Lower daily high AND higher daily low than previous day. Ignore for swing point identification -- market is in congestion.
- **Outside Days** (~7% of all days): Higher high AND lower low than previous day. Study the flow from open to close to determine swing direction.

### Trading Signals from Market Structure

**Buy Signal**: An intermediate-term low forms higher than the prior intermediate-term low. Enter when a new short-term low is confirmed (price rallies above the high of the low day). The intermediate uptrend momentum carries the trade.

**Sell Signal**: An intermediate-term high forms lower than the prior intermediate-term high. Enter when a new short-term high is confirmed (price falls below the low of the high day).

### Targets and Trailing Stops

**Target Calculation**: Measure the distance from the intermediate-term high to the intermediate-term low. Add that distance to the intermediate-term high for upside targets (or subtract from the low for downside targets).

**Trailing Stops** (four options, ranked by tightness):
1. Below the most recent short-term low (tightest)
2. Below the second short-term low back in time (more room)
3. Formation of a subsequent intermediate-term high/low (signal exit)
4. Target reached (fullest run)

### The Market Is Not Random

After one down close, prices close higher 55.8% of the time (vs. the 53.2% base rate). After two consecutive down closes, the up-close rate is 55.2%. After three consecutive down closes in a row, profitability increases significantly. Down closes set up better rallies than up closes.

---

## Volatility Breakout System (Core Entry Method)

### The Fundamental Principle

Trends are set in motion by "explosions of price activity." When price has an explosive move up or down, the market continues in that direction until an equal or greater explosive move occurs in the opposite direction. This expansion in volatility is the single most consistently profitable mechanical entry technique Williams has found.

### The Formulas

**Basic Volatility Breakout (Open-Based)**:
```
Buy Signal  = Tomorrow's Open + (Multiplier x Today's Range)
Sell Signal = Tomorrow's Open - (Multiplier x Today's Range)
```

Where Range = High - Low of the current day, and Multiplier is typically between 0.2 and 1.5 depending on the instrument and conditions.

**True Range Variant** (more accurate):
```
True Range = max(High - Low, |High - Previous Close|, |Low - Previous Close|)
Average True Range = mean(True Range over past N days)

Buy Signal  = Reference Point + (Multiplier x Average True Range of past 3 days)
Sell Signal = Reference Point - (Multiplier x Average True Range of past 3 days)
```

### Reference Point Selection

Williams tested five reference points extensively. Ranked by profitability:

1. **Tomorrow's Open** (best overall) -- Average profit per trade $389, highest accuracy (five commodities >50% win rate)
2. **Today's Close** -- Average profit per trade $327
3. **Today's High/Low** -- Average profit per trade $313
4. **Today's Mid-Price** -- Usable but inconsistent
5. **Today's Low** (for buys) -- Effective with 20% ATR multiplier after down-close days

For modern electronic markets (where close and next open are nearly identical), the close can serve as a practical substitute for the opening.

### Optimal Multiplier Ranges

The best multiplier varies by instrument and market condition. Typical tested values:
- **After Down-Close Days**: 20-60% of ATR(3) from the low or open
- **After Up-Close Days**: 40-90% of ATR(3) from the close
- **General Use**: 50-100% of yesterday's range from the open

Smaller multipliers (20-40%) capture more moves but with lower quality. Larger multipliers (100-200%) catch only the strongest explosions with higher accuracy but fewer trades.

### Protective Stops

- Dollar-based stop: Fixed dollar amount (e.g., $1,500 for S&P futures)
- Range-based stop: 50% of the previous day's range subtracted from entry price
- Use whichever is hit first

### Exit Strategies

1. **Hold to Close** (minimum) -- Capture large-range days that close at their extremes
2. **First Profitable Opening** -- Exit on the first open that shows a profit (bailout)
3. **Hold N Days** -- Hold for 2-6 days with trailing stops (more profit, more risk)
4. **Time-Based Exit** -- Exit after a fixed number of bars if target not reached

Holding longer = more profit. Results from S&P testing: exit on close = $39K profit; hold to next close = $68K; hold 6 days = $71.6K.

---

## Trading Day of Week (TDW) Filter

### The Discovery

Not all days of the week are equal for trading. TDW effects are persistent across decades and instruments, making this one of the most robust filters available.

### Historical Patterns (US Stock Indices)

**Best Buy Days**: Monday, Tuesday (consistently bullish bias)
**Worst Buy Days**: Wednesday (often loses money on long entries)
**Best Sell Days**: Thursday (strong short-side bias)
**Mixed**: Friday (varies by system and period)

### Application Rules

- Only take buy signals on the strongest buy days
- Only take sell signals on the strongest sell days
- Eliminating weak days reduces trades by ~40-50% but dramatically improves average profit per trade and reduces drawdown
- TDW filtering alone can cut drawdowns by 60%+ while boosting profit per trade

### TDW Combined with Volatility Breakout

After an up-close day: Best buy days are Monday, Wednesday, Thursday (avoid Tuesday and Friday).
After a down-close day: Best buy days are Monday, Tuesday, Thursday, Friday (avoid Wednesday).

---

## Trend Filters

### Moving Average Trend Definition

**Uptrend**: The 20-day moving average of closing prices is higher today than yesterday.
**Downtrend**: The 20-day moving average is lower today than yesterday.

Only take buy volatility breakout signals during uptrends. This single filter eliminated the 2008 bear market losses in testing while preserving the majority of bull market gains.

### Intermarket Trend Filter (Bond-Stock Relationship)

Higher bond prices are bullish for stocks; lower bond prices are bearish. Apply as:
- **Buy stocks only if**: Bond closing price is greater today than 5 days ago
- **Sell stocks only if**: Bond closing price is lower than 35 days ago

Adding the bond filter reduced the largest single loss from $8,150 to $2,075 and cut drawdown from $13,025 to $5,250 in S&P testing.

### The Layered Filter Approach

The optimal system combines ALL three filters:
1. Volatility breakout entry formula
2. TDW filter (trade only on favorable days)
3. Trend confirmation (20-day MA + bond trend)

Combined result: 90% accuracy, average profit per trade $444, dramatically reduced drawdown. Fewer trades, but each one is backed by multiple confirming factors.

---

## The "Real Secret": Large-Range Days

### The Discovery

The most profitable strategy for short-term traders is to catch large-range days. These days close at or near their extremes: up days close near the high; down days close near the low.

### Implications

- There is NO need to try to call intraday swings. Large-range days do the work.
- Enter the trade, place the protective stop, and hold to the close.
- Three types of days will develop: (1) small-range day (small loss or gain), (2) reversal day (loss), (3) large-range day in your favor (big win).
- Only large-range days generate meaningful profit. You MUST be in the trade to catch them.
- Exiting early (with $500 targets) LOSES money. Holding to close makes money. The facts settle the argument.

### Proof by Holding Period

Same system (buy Monday open if below Friday close), S&P 500 1982-1998:
- Exit at $500 target: -$8,150 (net loss despite 59% accuracy)
- Exit at $1,000 target: +$13,737 (marginal profit)
- Exit on same-day close: +$39,075 (3x better, $100 avg profit/trade)
- Hold to next day's close: +$68,312 ($172 avg profit/trade)
- Hold 6 days: +$71,600 ($251 avg profit/trade)

---

## Five Tools for Short-Term Trading

### 1. Price Patterns (Market Structure)

Swing points, intermediate-term highs and lows, trend identification. This is the structural backbone. See Market Structure Framework above.

### 2. Momentum / Volatility Breakouts

The entry mechanism. See Volatility Breakout System above. Volatility expansion signals the start of a new trend leg.

### 3. Trading Day of Week (TDW)

Persistent day-of-week biases that filter out weak-probability trades. See TDW Filter above.

### 4. Intermarket Relationships

Bond prices affect stock prices. The relationship between markets provides a powerful setup and filter. See Trend Filters above.

### 5. Sentiment

When advisors are extremely bearish, expect rallies. When extremely bullish, expect declines. The public is a net loser 80% of the time -- copper their wagers. COT (Commitment of Traders) report tracks smart money (Commercials) but is longer-term in nature.

---

## Adaptation to US Stock Trading

### Key Adjustments from Futures/Commodities

1. **Range Calculation**: Use True Range (accounts for gaps) instead of simple High-Low when stocks gap frequently
2. **Reference Point**: For stocks with significant overnight gaps, use the previous close as the reference point; for highly liquid ETFs/indices that trade near-continuously, the close and next open are nearly identical
3. **TDW Patterns**: Apply the same day-of-week analysis but verify patterns with recent data for the specific instrument
4. **Trend Filter**: Use the 20-day MA filter on the stock itself plus SPY/QQQ as the broad market trend proxy instead of bonds
5. **Volatility Multiplier**: Start with 0.5-1.0x of ATR(3) and optimize for the specific stock's volatility profile
6. **Position Sizing**: Apply Williams' money management rules (covered in later chapters) -- never risk more than a fixed percentage of capital per trade
7. **Stops**: Use ATR-based stops rather than fixed dollar amounts (e.g., 1.5x ATR below entry)

---

## Williams' Rules Summary

1. **Never argue with the market.** Price is what is. Value is ephemeral.
2. **Money management is everything.** Master defeats before chasing victories.
3. **Believe each trade will lose.** This keeps stops tight and positions small.
4. **Time creates profits.** Hold winners. Let them run. Two-to-five-day swings are optimal.
5. **Large-range days are your payday.** Enter, set stops, hold to close. No fancy dancing.
6. **Volatility breakouts set trends.** An explosive range expansion signals continuation.
7. **Filter relentlessly.** Combine TDW + trend + intermarket relationships. Fewer trades = better trades.
8. **Losses are papercuts.** Never let a single loss destroy you. E.H. Harriman's rule: kill your losses.
9. **Down closes set up rallies.** Consecutive down closes increase rally probability.
10. **Stay awake and adapt.** What works today may not work tomorrow. Fundamentals are permanent; specifics change.
