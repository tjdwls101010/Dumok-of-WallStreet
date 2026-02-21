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

---

## Script Output Interpretation Guide

### williams_r Interpretation

#### What %R Measures

Williams %R measures where today's close falls within the highest high and lowest low of the lookback period. The scale runs from -100 (close at the period low) to 0 (close at the period high). It is a measure of buying and selling pressure: which side -- buyers or sellers -- currently has the upper hand.

Williams describes this as the core question of market dynamics: "The reason price fluctuates is that one side, the buyer or the seller, blinks ... the side that wants it and wants it now, is the side that pushes prices higher or lower." %R quantifies this imbalance.

#### Zone Interpretation

| Zone | %R Range | Meaning | Williams' Guidance |
|---|---|---|---|
| Overbought | > -20 | Close is near the lookback-period high. Buyers have dominated recently. | This is a **setup condition** for potential selling, NOT a standalone sell signal. Treat as "close greater than the close X days ago" -- price is extended. |
| Neutral | -20 to -80 | Close is in the middle of the range. Neither side has decisive control. | No setup present. Wait for price to move into an extreme zone before considering action. |
| Oversold | < -80 | Close is near the lookback-period low. Sellers have dominated recently. | This is a **setup condition** for potential buying, NOT a standalone buy signal. Treat as "close lower than the close X days ago, suggesting Yin may turn into Yang." |

#### Critical Rule: %R Zones Are Setups, Not Signals

Williams is explicit that overbought/oversold conditions are only the first half of the equation. From the text: "My first step is to create a setup for the trade, as I don't want to trade on just one technical goody all by itself." The setup (oversold %R reading) must be combined with a confirmed entry trigger (volatility breakout, pattern confirmation, or GSV threshold).

- **Oversold %R reading** establishes the condition: "prices have been declining, so a rally of some sort should be in the future."
- **Entry trigger** comes separately: a volatility breakout above a threshold, a swing point confirmation, or a pattern signal.
- **Never act on %R alone.** The reading tells you the market is overextended; the entry technique tells you the reversal has begun.

#### Combining %R with Other Filters

Williams' documented approach layers %R setups with these additional filters:

1. **TDW (Trading Day of Week)**: After an oversold setup, "limit buying to only one of three days of the week: Tuesday, Wednesday, and Friday." For sell setups from overbought readings, sell days are subject to separate TDW confirmation.
2. **Trend Direction**: After an oversold reading, confirm the broader trend supports the reversal. Williams uses a 20-day moving average (rising = uptrend confirmation for buys) and intermarket data (bonds closing higher than 5-15 days ago for bullish stock entries).
3. **Volatility Breakout Confirmation**: The entry price must exceed a threshold (typically 180% of the average failure swing value or a percentage of ATR) before committing capital.

#### When to Act vs. When to Wait

| %R Condition | Action |
|---|---|
| Entering oversold zone (crossing below -80) | **Wait.** Setup is forming but not complete. Do not buy yet. |
| Sustained in oversold zone (days_in_current_zone rising) | **Prepare.** The longer the oversold condition persists, the stronger the eventual rally setup -- but still require entry trigger. |
| Exiting oversold zone (crossing back above -80) | **Evaluate entry trigger.** If volatility breakout or pattern confirmation fires on a favorable TDW, this is the signal. |
| Entering overbought zone (crossing above -20) | **Wait.** Sell setup forming. Monitor for confirmation. |
| Sustained in overbought zone | **Prepare.** Market may be in a strong trend. Do not fade strength without confirming reversal. |
| Exiting overbought zone (crossing below -20) | **Evaluate sell trigger.** If conditions align (TDW, trend, breakout), consider short or exit long. |

#### What Constitutes a Valid %R Signal vs. Noise

- **Valid signal**: %R in an extreme zone (overbought or oversold) + at least one confirming filter (TDW favorable, trend aligned, breakout level triggered). Williams achieved 75-86% accuracy only when combining setup + entry + filter.
- **Noise**: %R oscillating near zone boundaries without committing to an extreme, or %R in an extreme zone but no confirming entry trigger fires. "Exceeding the average of these [swings] means something out of the average has just taken place" -- the %R extreme alone is not "out of the average" enough.

#### Caveats from Williams

- "It is a 'dumb' technique: It knows not when a big trade will come or even when a winning trade will be delivered on a silver platter. That is why you cannot pick and choose these trades, you must simply take them, one at a time, as they come out of the hopper."
- "If you pick and choose, you will invariably pick the losers and walk away from the winners. It is nothing personal, we all do, and the way to beat this devil is to take 'em all."
- The previous 1-4 days produce the best calculation values. Longer lookback periods (10+ days) do not improve stability as expected.
- Electronic markets have diminished the reliability of open-based reference points. The close-based approach is now preferred.

*Apply this framework independently to the current analysis target.*

### volatility_breakout Interpretation

#### The Fundamental Principle

"Trends are set in motion by 'explosions of price activity.' If price, in one hour, day, week, or month has an explosive move up or down, the market will continue in that direction until there is an equal or greater explosive move in the opposite direction." A volatility breakout is the detection of this explosion. When it fires, you are wagering that the new trend leg has begun.

#### Field-by-Field Interpretation

**buy_level / sell_level**

| Condition | Meaning |
|---|---|
| Price reaches buy_level | A buy breakout has fired. "A clear indication price has had a new impetus driving it in a direction, and price, like any object once set in motion, tends to stay in the direction of that motion." |
| Price reaches sell_level | The downside equivalent: sellers have exerted enough force to overcome recent containment. A sell breakout has fired. |
| Price stays between buy_level and sell_level | No explosion occurred. The market is range-bound. No trade. "I will not trade just because of such an entry, but will use this as my entry technique when the time and conditions are correct." |
| buy_level and sell_level are very close to reference_close | Volatility has contracted (small ATR). The next expansion could be significant. Prepare for a breakout but require additional confirmation. |
| buy_level and sell_level are very far from reference_close | Volatility is already elevated. Only a truly exceptional explosion triggers a signal. Higher conviction when triggered, but fewer signals. |

**reference_close**

The reference point from which breakout levels are calculated. Williams tested five reference points and concluded: "The best point to add or subtract a volatility expansion value to is tomorrow's open." In electronic markets where the close and next open are nearly identical, the close serves as the practical substitute.

**true_range / atr_3**

| Metric | Interpretation |
|---|---|
| true_range (latest day) | The single-day volatility measure. True Range = max(High-Low, abs(High-prevClose), abs(Low-prevClose)). Accounts for gaps. |
| atr_3 (3-day average) | Williams' preferred averaging period. "In almost all cases, the previous one to four days produce the best value in trading or developing systems." The 3-day ATR captures the most recent volatility regime. |
| atr_3 is small relative to price | Low-volatility environment. Breakout levels are tight. Signals fire more frequently but the "explosion" threshold is lower. More likely to produce false starts. |
| atr_3 is large relative to price | High-volatility environment. Breakout levels are wide. Signals are rarer but represent genuinely exceptional moves. Higher quality. |
| current_range_vs_avg > 1.5 | Range expansion phase. "When this volatility increases beyond recent proportion, trends change." This is the condition Williams identifies as trend-setting. |
| current_range_vs_avg < 0.5 | Range contraction. The market is compressing. Expect an eventual expansion -- but direction is unknown until the breakout fires. |

**multiplier**

The multiplier scales the ATR to set the breakout threshold. Williams tested multipliers from 0.2 to 2.0 across dozens of instruments.

| Multiplier Range | Characteristics | Williams' Context |
|---|---|---|
| 0.2-0.4 | Tight threshold. Captures many moves. Lower accuracy but higher trade frequency. | "Smaller multipliers capture more moves but with lower quality." Best after down-close days from the low reference. |
| 0.5-1.0 | Standard range. Balanced trade frequency and quality. | "50 percent volatility expansion" is the baseline test. "100 percent of the previous day's range added to the open" is the simple daily range breakout. |
| 1.0-2.0 | Wide threshold. Catches only the strongest explosions. Fewer trades, higher accuracy. | "200 percent of the range subtracted from the open" for sell entry. "180 percent of the four-day swing value average" for GSV entries. "Proof the market is tracking in fresh ground, new territory." |

#### Entry Confirmation Requirements

A valid volatility breakout signal requires more than price touching the level. Williams' layered filter approach:

1. **Price must reach the breakout level during the trading session.** If the high of the day touches or exceeds buy_level, the buy signal fires. If the low touches or goes below sell_level, the sell signal fires.
2. **TDW filter must be favorable.** Restricting trades to favorable days "reduced trades by ~40-50% but dramatically improved average profit per trade and reduced drawdown." Best buy days for stock indices after down closes: Monday, Tuesday, Thursday, Friday (avoid Wednesday). After up closes: Monday, Wednesday, Thursday (avoid Tuesday, Friday).
3. **Trend must confirm.** Use the 20-day moving average: if it is rising today vs. yesterday, the uptrend is confirmed for buys. "Down closes set up better rallies."
4. **Intermarket filter (bonds) should align.** "Buy stocks only if bond closing price is greater today than 5 days ago." Adding this filter "reduced the largest single loss from $8,150 to $2,075 and cut drawdown from $13,025 to $5,250."
5. **Combined result.** The fully filtered system achieved 90% accuracy with $444 average profit per trade.

#### Relationship to Large-Range Days

The volatility breakout is Williams' mechanism for boarding large-range days:

- "The most profitable strategy for short-term traders is to catch large-range days. These days close at or near their extremes."
- Three day types will develop after entry: (1) small-range day -- small loss or gain, (2) reversal day -- loss, (3) large-range day in your favor -- big win. "Only large-range days generate meaningful profit. You MUST be in the trade to catch them."
- "Exiting early (with $500 targets) LOSES money. Holding to close makes money."

#### Reference Point Selection Priorities

| Priority | Reference Point | Avg Profit/Trade | Notes |
|---|---|---|---|
| 1 | Tomorrow's Open | $389 | Best overall. Highest accuracy. In electronic markets, use the close as proxy. |
| 2 | Today's Close | $327 | More practical for modern markets since close ≈ next open. |
| 3 | Today's High (buy) / Low (sell) | $313 | "Using the low as our reference point" with 20% ATR works well after down-close days. |
| 4 | Today's Mid-Price | -- | "Usable but inconsistent." |
| 5 | Today's Low (for buys only) | -- | Effective with 20% ATR multiplier specifically after down-close days. |

#### Stop Placement

- **Dollar-based stop**: Fixed amount (e.g., $1,500 for bond futures, $2,500 for S&P futures).
- **Range-based stop**: 50% of the previous day's range subtracted from entry price. Alternatively, 225% of the average swing value (for GSV-based entries).
- **Open-based stop (practical)**: "In real-time trading, I will use a stop at or slightly above or below the open, once I am filled on a long or short."
- **Day's low/high stop (absolute)**: "In absence of this stop, you certainly must have one taking out the low of the day -- this would be a sure sign of failure."

For the script's output: the sell_level serves as the initial stop reference for long entries. Verify that the distance between current_price and sell_level represents an acceptable loss relative to your position size and account risk percentage.

#### Caveats from Williams

- "I will not trade just because of such an entry, but will use this as my entry technique when the time and conditions are correct." The volatility breakout is the entry mechanism, not the decision mechanism.
- "Active traders are usually losing traders. Those of us who pick and choose our spots to speculate are more inclined to come out winners as we have tipped the scales in our favor."
- "There is not a 100 percent correct mechanical approach to trading." Expect losses. The edge comes from the cumulative result of many trades taken with consistent filters.

*Apply this framework independently to the current analysis target.*

### swing_points Interpretation

#### Confirmation Rules for Valid Swing Points

| Point Type | Definition | Confirmation Trigger |
|---|---|---|
| Short-Term Low | A day with higher lows on BOTH sides | Price rallies above the HIGH of that low day |
| Short-Term High | A day with lower highs on BOTH sides | Price falls below the LOW of that high day |
| Intermediate-Term Low | A short-term low with higher short-term lows on both sides | Same as above, applied at the short-term level |
| Intermediate-Term High | A short-term high with lower short-term highs on both sides | Same as above, applied at the short-term level |

**Inside days** (~7.6% of sessions): Ignore for swing identification. The market is in congestion.

**Outside days** (~7% of sessions): Study the direction from open to close to determine which swing direction the day belongs to.

#### Interpreting the Nested Swing Structure

All market movement is hierarchical. Short-term points build intermediate-term points, which build long-term points.

- **`level: short_term`** points define the smallest identifiable swings -- the building blocks.
- **`level: intermediate`** points represent confirmed structural turns at a higher time frame. These are the primary trading signals.
- The absence of intermediate-term points means the market has not yet produced enough nested structure to confirm a higher-order trend.

#### Trend Direction from swing_points Output

| `short_term` trend | `intermediate` trend | Interpretation | Trading Posture |
|---|---|---|---|
| up | up | Full structural alignment upward | Strongest buy setup. Enter on confirmed intermediate-term low higher than prior |
| up | neutral | Short-term rallying but intermediate not yet confirmed | Tentative. Wait for intermediate-term low confirmation |
| up | down | Short-term bounce within intermediate downtrend | Counter-trend rally. Do not buy |
| down | up | Short-term pullback within intermediate uptrend | Potential buying opportunity if pullback forms a higher short-term low |
| down | down | Full structural alignment downward | Strongest sell/short setup |
| down | neutral | Short-term declining, intermediate not yet resolved | Wait |

#### Entry Signals from Swing Point Patterns

**Buy Signal**: Most recent intermediate-term low is HIGHER than the prior intermediate-term low. Enter when the short-term low is confirmed (price exceeds the high of the day that formed the low).

**Sell Signal**: Most recent intermediate-term high is LOWER than the prior intermediate-term high. Enter when price falls below the low of the day that formed the high.

**Reversal Signal**: If the initial stop is hit, Williams instructs reversing the position entirely, because the structure has now confirmed the opposite trend.

#### Target Calculation Method

```
Upside Target = last_intermediate_high + (last_intermediate_high - last_intermediate_low)
Downside Target = last_intermediate_low - (last_intermediate_high - last_intermediate_low)
```

Markets have "a strong tendency to rally above the last intermediate-term high by the same amount it moved from the intermediate-term high to the lowest point prior to advancing."

Note: "Markets don't always go to targets, which is why it is critical you also learn to have a trailing stop."

#### Trailing Stop Options (Ranked by Tightness)

| Rank | Method | When to Use |
|---|---|---|
| 1 (tightest) | Below the most recent short-term low | When uncertain or wanting to lock in quick profit |
| 2 | Below the second short-term low back in time | When moderately bullish and willing to give the trade room |
| 3 | Formation of a subsequent intermediate-term high/low | When the trade is working and you want structural confirmation of a turn |
| 4 (widest) | Target reached | When full confidence in the setup |

#### Consecutive Down/Up Close Reliability Context

- After **one** down close: prices close higher 55.8% of the time (vs. 53.2% base rate)
- After **two** consecutive down closes: 55.2% up-close rate
- After **three** consecutive down closes: profitability increases significantly

A swing low forming after multiple consecutive down closes carries higher statistical reliability.

*Apply this framework independently to the current analysis target.*

### range_analysis Interpretation

#### The Real Secret: Large-Range Days

Williams states: "We make money only on large-range days." When the output shows `phase: expansion` (range_ratio >= 1.5), you are looking at the type of day that generates the vast majority of short-term trading profits.

"Large-range days usually close at or near the high, if an up day, or the low, if a down day."

#### Three Types of Days and Their Profit Implications

| Williams' Day Type | range_analysis Mapping | Profit Implication | Action |
|---|---|---|---|
| Small-range day | `phase: contraction` or `phase: normal` with low range_ratio | Small loss or small gain -- essentially a wash | Hold position with stops in place. This day is not your payday |
| Reversal day | Any phase where price moves against your position | Loss | Stop-loss absorbs the damage. Accept it as the cost of staying in the game |
| Large-range day in your favor | `phase: expansion` with close near the extreme | The payoff | Hold to the close. Do NOT exit early |

#### Interpreting the phase Field

| Phase | range_ratio | Meaning | Trading Response |
|---|---|---|---|
| `expansion` | >= 1.5 | Today's range is 1.5x or more the average true range. Large-range day | If positioned correctly, hold to the close. If not positioned, a volatility "explosion" has occurred and a new trend leg may be underway |
| `normal` | 0.5 - 1.5 | Range is within the ordinary band | Maintain existing positions. No special action required |
| `contraction` | <= 0.5 | Range is half or less of the average. Tight, quiet day | Contraction precedes expansion. A string of contraction days is a setup for the next large-range day. Prepare entries |

#### Range Expansion vs. Contraction Sequences

- **Multiple contraction days followed by expansion**: Classic Williams volatility breakout setup. "Trends are set in motion by explosions of price activity."
- **Expansion followed by more expansion**: Trend is accelerating. Hold positions.
- **Expansion followed by contraction**: Trend leg may be exhausting. Consider tightening trailing stops.
- **Sustained normal phase**: Sideways chop. Williams makes his living catching large-range breakouts out of these periods.

#### Why Holding to the Close Matters (Performance Data)

Same system (buy Monday open if below Friday close), S&P 500 1982-1998:

| Exit Strategy | Net Profit | Avg Profit/Trade | Win Rate |
|---|---|---|---|
| $500 profit target (quick exit) | -$8,150 | -$20.95 | 59% |
| $1,000 profit target | +$13,737 | +$35.31 | 55% |
| Exit on same-day close | +$39,075 | +$100.45 | 53% |
| Hold to next day's close | +$68,312 | +$172.07 | 55% |
| Hold 6 days with stop | +$71,600 | +$251.23 | 52% |

The $500-target approach had the HIGHEST accuracy (59%) yet LOST money. "The facts speak for themselves."

"I hold to the close, at least, for an exit point. Until someone can do the impossible, that is, call all short-term fluctuations, there will be no better strategy for a short-term trader."

#### Using range_analysis for Position Management

| Scenario | current_percentile | phase | Decision |
|---|---|---|---|
| Very high (>80th) + expansion | High | expansion | Hold to close. "Enter the trade, place my protective stop, then shut my eyes, hold my breath, quit looking at the market, and wait to get out on the close. Or later!" |
| High (60-80th) + normal | Elevated | normal | Standard hold with existing stops |
| Low (<20th) + contraction | Low | contraction | Market is compressed. Coiling setup. Prepare for the next expansion day |
| Moderate + expansion | Moderate | expansion | Modest expansion -- hold but with standard trailing stop |

*Apply this framework independently to the current analysis target.*
