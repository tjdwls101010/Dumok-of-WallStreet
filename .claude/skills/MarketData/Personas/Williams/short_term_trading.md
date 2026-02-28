# Williams Short-Term Trading: Patterns & Setups

## Overview

Williams' short-term trading approach combines structural bar patterns, calendar biases (TDW/TDM), and volatility-based entries to identify explosive 2-5 day moves. Every pattern is based on the same underlying principle: the public gets trapped by emotional reactions to apparent breakouts or breakdowns, and the immediate reversal of those moves creates high-probability entries for informed traders. No pattern should be traded in isolation -- each requires confirmation from setup criteria including TDW, intermarket relationships, overbought/oversold conditions, and trend context.

---

## Five Chart Patterns

### 1. Outside Day Reversal

**Definition**: A day whose range completely engulfs the prior day's range (higher high AND lower low) that closes lower than the prior day's close.

**Bar-by-bar construction**:
- Day 0: Normal trading day establishing a range
- Day 1 (Outside Day): High > Day 0 High, Low < Day 0 Low, Close < Day 0 Close
- The market explored both directions but sellers won decisively

**Trading Rule**: Buy on the next day's open. In Bonds (1990-1998), trading outside day buy signals on any day except Thursday produced **90% accuracy** on 41 trades, with an average profit of $420/trade and profit factor of 3.77. In the S&P 500 (1986-1998), outside days with down closes that occurred on Tuesday set up 25 Wednesday sell signals, of which 19 were winners (76%) netting $21,487.

**Backtested Accuracy**: ~85% when combined with TDW filter (average across Bond and S&P tests). The pattern's strength increases significantly when Thursday is excluded (Bond market) or when aligned with favorable TDW days.

**Pattern Combination**: Outside Day + TDW(Tuesday→Wednesday) is one of the strongest stacking combinations -- the S&P sell signal on this combination achieved 76% accuracy with $859 average profit per trade.

**Electronic Era Status**: Outside days remain bullish even in electronic markets. Testing on the S&P E-Mini from 1998 forward confirmed similar results.

### 2. Smash Day (Naked Close)

**Definition**: A day that closes below the prior day's low (naked down close) or above the prior day's high (naked up close). This violent price action draws the public into the fray at exactly the wrong moment.

**Buy Setup**:
- Day 1: Close < Prior day's Low (naked down close). May also take out 3-8 days of lows
- Day 2: If price trades ABOVE Day 1's High, buy immediately
- The immediate reversal means the public's breakout has failed -- they swallowed the hook

**Sell Setup**:
- Day 1: Close > Prior day's High (naked up close)
- Day 2: If price trades BELOW Day 1's Low, sell immediately

**Key Requirement**: The reversal must occur the VERY NEXT DAY. The pattern's power comes from the immediacy of the failure. If several days pass without reversal, the original breakout may be valid.

**Backtested Accuracy**: ~76%. In the S&P 500 (1986-1998), smash day sell setups on Tuesday (close above prior day's high, preceded by 2 consecutive up closes) produced 25 trades setting up Wednesday sells with 19 winners (76%), netting $21,487. In Bonds (1989-1998), the same pattern on Thursday set up Friday sells: 28 trades, **89% accuracy**, $13,303 profit, profit factor 3.83.

**Trading Rule**: Use this pattern in two contexts:
1. **Trend continuation**: In a strong trend, a smash day against the trend is a pullback entry. The trend is intact and ready for another push. This is the higher-probability use case.
2. **Range breakout failure**: In a 5-10 day choppy range, a smash day followed by immediate reversal suggests a breakout in the opposite direction, as all the stops were triggered and the "breakout babies" were trapped.

**Pattern Combination**: Smash Day + trend context is the preferred stacking. Williams particularly values smash days that occur during strong trends as re-entry opportunities.

### 3. Hidden Smash Day

**Definition**: A day that closes UP for the day but in the bottom 25% of its range (and ideally below the open). The up close masks the fact that buyers got smashed -- price rallied and then collapsed, but the chartist sees only "up close" and misses the failure.

**Buy Setup**:
- Day 1: Close > Prior Close (up day), but Close is in the **lower 25%** of the day's range (High - Low). Best patterns also have **Close < Open** (additional confirmation)
- Day 2: If price rallies above Day 1's High, buy -- the failed selling is being reversed

**Sell Setup** (mirror image):
- Day 1: Close < Prior Close (down day), but Close is in the **upper 25%** of the range and **above the Open**
- Day 2: If price drops below Day 1's Low, sell

**Hidden Smash Day Refinement**: The lower 25% threshold is the key discriminator. The additional confirmation of Close < Open (on a nominally "up" day) significantly increases the pattern's reliability, because it confirms that buyers were truly smashed -- price opened higher or rallied sharply, then collapsed to close below its own opening despite still being "up" compared to the prior close. This dual condition filters out weaker setups.

**Backtested Accuracy**: ~89% in the highest-conviction setups. The hidden smash day outperforms the regular smash day because the trap is more subtle -- chartists see only "up close" and miss the failure embedded in the range structure.

**Pattern Combination**: Hidden Smash Day + trading range context produces the strongest signals. When a hidden smash occurs at the boundary of a 5-10 day congestion zone, the immediate reversal is particularly powerful.

**Rationale**: What happened is that price either gapped up and then sold off to close barely above the prior close, or rallied sharply intraday and then gave back nearly all gains. The buyers were "hidden smashed." If the next day immediately reverses and takes out the smash day's high, the trapped sellers are in trouble.

### 4. Specialists' Trap (Wyckoff Trap)

**Definition**: Derived from Richard Wyckoff's 1930s work on market manipulation. A false breakout from a 5-10 day congestion zone that reverses within 1-3 days.

**Sell Trap Setup**:
- Market is in an uptrend and enters a 5-10 day sideways box/congestion
- Price breaks out to the upside with a naked close above the entire trading range
- Within **1-3 days**, price falls below the **"true low of the breakout day"**
- This signals the upside breakout was false -- distributors unloaded to the public on strength

**Buy Trap Setup** (mirror image):
- Down-trending market stabilizes sideways for 5-10 days
- Price breaks below with a naked close lower than all daily lows of the range
- Within **1-3 days**, price snaps back above the **"true high of the breakdown day"**
- All sell stops below the range were triggered; the public is now afraid to buy the reversal

**Critical Point**: The "true low of the breakout day" (for sell traps) or "true high of the breakdown day" (for buy traps) becomes the **trigger level**. Its violation within the strict 1-3 day time window is the entry signal. If more than 3 days pass without the trigger level being violated, the original breakout may have been valid and the trap setup is invalidated.

**Backtested Accuracy**: ~80%. The pattern derives from Richard Wyckoff's 1930s work on market manipulation. While not the most frequent pattern, it is among the highest-conviction setups when all conditions are met. Williams found this pattern works across all markets including individual stocks (tested on Exxon and others).

### 5. Oops! Pattern

**Definition**: The most reliable short-term pattern Williams ever traded, based on an overemotional gap response that immediately reverses.

**Buy Setup**:
- Market gaps down, opening below the prior day's low
- During the same session, price recovers back up to the prior day's low
- Buy at the prior day's low -- the gap down was an emotional overreaction that trapped sellers

**Sell Setup** (mirror image):
- Market gaps up, opening above the prior day's high
- Price falls back to the prior day's high
- Sell at the prior day's high

**Backtested Accuracy**: ~82% in the pit trading era. Williams estimates he made over $1,000,000 trading this pattern during the pit era. It was the most reliable of all short-term patterns he researched and traded.

**Electronic Era Limitation**: This pattern has been **greatly diminished** by electronic trading. In the pit era, markets were closed for 16-18 hours, allowing orders and emotions to build up and causing torrents of buy/sell orders that forced markets to gap open. Now there are only a few minutes or hours between electronic close and open, so the "blow-off" effect of pent-up orders is largely gone. The pattern retains value on Sunday evening opens and after major news events, but it is no longer the workhorse it was in the pit era.

---

## Trading Day of the Week (TDW) Framework

Not all days of the week are created equal. This is one of Williams' most enduring discoveries, holding from the 1960s through 2011 and beyond. The random walk theory says there should be no day-of-week bias, but the data proves otherwise decisively.

### S&P 500 TDW Bias

| Day | Open-to-Close Bias (1982-1998) | Updated (1998-2011) | Historical Character |
|-----|-------------------------------|---------------------|---------------------|
| Monday | +$91/trade, 52% | +$45/trade, 50% | Strongest buy day. Mon-Tue combined = most reliable |
| Tuesday | +$59/trade, 52% | +$56/trade, 55% | Second-best buy day. Strengthened in electronic era |
| Wednesday | -$27/trade, 52% | -$27/trade, 51% | **Weakest day; exclude from buy systems.** Excluding Wed reduced drawdown by ~65% |
| Thursday | -$10/trade, 50% | -$37/trade, 50% | Best sell day for short signals |
| Friday | +$134/trade, 57% | +$109/trade, 57% | Strongest absolute performance; 57% close above open |

**S&P Cumulative TDW Performance** (volatility breakout system, Low + 20% ATR, 2000-2011): Monday = **$50,000** profit, Tuesday = **$30,000**, Wednesday = **-$22,000** (loss), Thursday = $12,000, Friday = $8,000. The Mon-Tue dominance is striking: these two days account for the vast majority of the system's profits.

### Bond Market TDW Bias

| Day | Open-to-Close Bias (1977-1998) | Updated (1998-2011) | Historical Character |
|-----|-------------------------------|---------------------|---------------------|
| Monday | +$59/trade, 54% | +$53/trade, 55% | Solid buy day |
| Tuesday | -$18/trade, 49% | -$35/trade, 47% | **Weakened in electronic era** |
| Wednesday | +$16/trade, 54% | +$4/trade, 52% | Moderate; acceptable for longs |
| Thursday | +$30/trade, 53% | +$8/trade, 50% | Neutral |
| Friday | -$35/trade, 50% | -$14/trade, 51% | **Largest daily range** -- volatility for breakout entries |

### Grain Markets TDW Bias

All grain markets show a pronounced tendency to rally more on Wednesdays than any other day. Soybeans on Wednesdays: $117 average profit per trade vs. $14 on Thursdays. This has persisted since the 1960s.

### TDW Application

TDW is used as a setup filter, not a standalone system. The best trades combine TDW bias with volatility breakouts and intermarket confirmation. For example, a Bond volatility breakout system restricted to buy on Tuesday/Thursday and sell on Wednesday/Thursday produced 84% accuracy with a profit factor of 1.85, compared to 80% accuracy trading all days.

---

## Trading Day of the Month (TDM) Framework

TDM measures the trading day number within each month (not calendar date). A month typically has 20-22 trading days. Holidays and weekends mean the trading day number differs from the calendar date.

### S&P 500 TDM Bias

- **Month Start Bullish Zone (TDM 1-4)**: Strong bullish bias. Four consecutive profitable trading days at the start of each month
- **Midmonth Weakness (TDM 5-7, 12-13)**: Negative expected returns. Avoid initiating new longs
- **End-of-Month Rally (TDM 19-22)**: The strongest and most reliable seasonal pattern. Three consecutive bullish days with strong profits
- **Best TDMs for buying**: 8, 18, 19, 20, 21, 22

**S&P TDM Performance Data** (1982-1998, buy on open of TDM, exit close of same day):

| TDM | $ Profit | # Trades | % Wins | Avg $/Trade |
|-----|---------|---------|--------|------------|
| 8 | $51,312 | 175 | 68% | $293 |
| 19 | $64,162 | 145 | 57% | $442 |
| 20 | $55,600 | 110 | 54% | $505 |
| **21** | **$70,875** | **75** | **64%** | **$945** |
| 22 | $42,375 | 61 | 65% | $694 |

**TDM 21 stands out**: $945 average profit per trade is the highest of any TDM -- nearly double the next best. The reduced number of trades (75) reflects that not all months have a TDM 21, but when they do, the edge is substantial. Updated results (1998-2011) confirm the pattern held: TDM 21 produced $31,562 on 106 trades (55% accuracy, $297 avg/trade).

### Bond Market TDM Bias

- **Best Buy Days**: TDM 10, 11, 12, 16, 20 (midmonth and end-of-month strength)
- **Worst Buy Days**: TDM 2, 14, 18 (avoid longs on these days without additional filters)
- **TDM 18 and 22**: Traditional Bond buy signals. Bond TDM 18 or 22 buy signals historically produced strong results when combined with trend confirmation

**Bond TDM Performance Data** (1998-2011, buy on open, exit close same day):
- **TDM 20 = $33,000 profit** -- the single strongest TDM for Bonds, confirming the end-of-month rally bias
- TDM 11 = $25,000 profit -- midmonth strength anchor
- TDM 16 = $13,000 profit -- secondary midmonth strength

**Bond TDM 18/22 Detailed Performance** (1986-1998):
- TDM 18 unfiltered: 139 trades, 71% accuracy, $250 avg/trade, $8,625 drawdown
- TDM 22 unfiltered: 50 trades, 76% accuracy, $496 avg/trade, $4,500 drawdown
- **TDM 22 + Gold filter (Gold in downtrend)**: 28 trades, **89% accuracy**, **$719 avg/trade**, drawdown only **$1,500**, profit factor 5.47, 17 consecutive winners

### Gold TDM Bias

- **Sweet Spot**: TDM 11 through 16 (midmonth rally tendency)
- **Also Strong**: TDM 3 and 4
- **Worst Day**: TDM 7 (strong sell bias) and TDM 17

### TDM Application

Like TDW, TDM is used as a setup -- a leading indicator of when to take action. Williams does not blindly trade TDM signals; he waits until TDM aligns with his other tools. The strongest trades occur when TDW and TDM point in the same direction simultaneously.

### TDW/TDM Interaction Rules

The interplay between TDW and TDM creates a two-dimensional filter that is the cornerstone of Williams' calendar-based trade qualification:

- **Convergence (both bullish)**: This is the **highest-conviction** setup. When a bullish TDW (e.g., Monday for S&P) coincides with a bullish TDM (e.g., TDM 20-21), the combined probability significantly exceeds either signal alone. A Monday that falls on TDM 20 is a high-conviction buy setup for the S&P. Williams calls this "stacking the deck."
- **Divergence (conflicting signals)**: When TDW is bullish but TDM is bearish (or vice versa), **reduce position size or pass entirely**. The conflicting calendar signals dilute the edge, and the expected value of the trade drops below Williams' threshold for action.
- **Practical application**: Williams' strategy is to find a bias (TDW, TDM) and then couple it with another bias to load the deck. The more confirming biases present (TDW + TDM + intermarket + volatility breakout), the larger the position warranted.

---

## Greatest Swing Value (GSV)

### Concept

GSV separates buying swings from selling swings by measuring:
- **Buy Swing**: Distance from Open to High on DOWN close days (the market could rally that much but failed to hold, closing down)
- **Sell Swing**: Distance from Open to Low on UP close days (the market could decline that much but failed to hold, closing up)

These are "failure swings" -- the market swung that far but could not follow through. Exceeding the average failure swing means something out of the ordinary is occurring.

### Formula

1. Calculate the buy swing (Open to High) for each of the past **4 days** that had down closes
2. Average these 4 values -- this is the "4-day average failure swing"
3. Multiply by **180%** to get the entry threshold
4. Buy above the opening at this 180% value

Mirror logic for sells: average the sell swings (Open to Low) on up close days for 4 days, multiply by 180%, subtract from opening for sell entry.

### GSV Stop Placement

Use **225%** of the 4-day average swing value as the stop distance. If price returns to this level after triggering entry, the momentum move has failed. The 225% threshold represents a swing significantly beyond the normal failure range -- its violation means the expected momentum move has been definitively rejected.

### GSV Setup Conditions

GSV is not traded in isolation. Williams requires additional conditions for the highest-probability trades:
- **Oversold condition**: The market should be in an oversold state (e.g., Williams %R near -100) before the GSV buy triggers. This ensures the momentum explosion occurs from a depressed level, not from an already-extended move.
- **TDW filter**: Apply the trading day of the week bias. For Bonds, Fridays have been the strongest GSV trigger day. For the S&P, Mondays and Tuesdays.
- **Performance data**: Bond GSV combined with the TDW filter produced 90% accuracy in pit-era testing. S&P GSV was profitable across multiple market regimes when filtered by oversold conditions and favorable TDW days.

### Electronic Era Status

The GSV concept using the opening as reference has been **greatly diminished** by electronic trading. The opening is now essentially the prior close, so the Open-to-High/Low swing measure has lost its predictive power. The 16-18 hour gap between close and open that once created the explosive opening dynamics no longer exists. However, the TDW data within the GSV framework still holds -- Fridays remain strong for Bonds, Tuesdays for stocks. Williams suggests future research using the prior day's high, low, or close as alternative reference points to recapture the pattern's edge.

---

## Three-Bar High/Low Channel Pullback

A simple pullback buy system that uses a **3-bar moving average** channel. Williams once had over 30 consecutive winning trades using this strategy.

### Construction
- Calculate a **3-bar moving average of the lows** (lower channel)
- Calculate a **3-bar moving average of the highs** (upper channel)
- Each bar represents the timeframe of your chart (5-minute, 15-minute, daily)

### Trading Rules
- **Buy**: When price pulls back to the **3-bar MA of lows** during an uptrend (as defined by swing point trend identification). Enter at the MA of lows level.
- **Take profit**: At the **3-bar MA of highs** level. This captures the channel-width move.
- **Sell short**: When price rallies to the **3-bar MA of highs** during a confirmed downtrend. Exit at the 3-bar MA of lows.

### Critical Conditions
- **Do NOT** buy at the 3-bar MA of lows if doing so would create a swing point that triggers a trend reversal to the downside. The buy requires the larger trend to be intact.
- **Do NOT** sell at the 3-bar MA of highs unless the swing point reversal system has confirmed the trend is down.
- The system works best combined with **Willspread** confirmation: when Willspread is positive, buy the 3-bar MA of lows; when negative, sell the 3-bar MA of highs.
- Works on 5-minute to 60-minute bar charts and daily charts. The 15-minute timeframe provides a good balance of signal frequency and reliability.

---

## Month-End Trading Systems

### S&P First-of-Month Buy

Based on the consistent tendency for stock prices to rally around the first of the month. This is one of the most enduring trading patterns Williams has identified, known since the 1960s and confirmed through 2011.

**Original Results** (1987-1998): Buy on open of first trading day, $1,500 stop (not on entry day), exit at first profitable opening. 129 trades, **85% accuracy**, $569 avg/trade, $3,325 drawdown, profit factor 3.46.

**Updated Results** (1998-2011, $3,500 stop): $106,000 net profits, 66% accuracy on the large S&P contract. E-Mini contract: **81% accuracy**, $29,650 net, $426 avg/trade.

**Optimization -- Skip January and March**: These are the worst-performing months historically. Excluding them: 270 trades, **80% accuracy**, $546 avg/trade. Further improvement by requiring Bonds to have closed higher the day prior to entry (Bond uptrend = supportive for stocks).

### S&P Month-End Buy Timing

- Enter long near TDM 19-22
- Exit after TDM 1-4 of the following month
- This captures the end-of-month/beginning-of-month bullish seasonal
- **Do not take on Mondays** in the E-Mini for best results. Best stop: $1,600 for E-Mini.

### Bond TDM 18/22 Buy

Bonds show midmonth-to-end-of-month strength with remarkable consistency (tested 1980s through 2011):

**TDM 18 Buy** (1986-1998): $1,500 stop, exit at close three days after entry. 139 trades, 71% accuracy, $250 avg/trade. Filtered with **Gold in downtrend** (Gold close < 24 days ago): accuracy rises to 75%, avg/trade jumps to $356, drawdown cut nearly in half to $4,500.

**TDM 22 Buy** (1986-1998): 50 trades, 76% accuracy, $496 avg/trade. With **Gold filter**: only 28 trades, but **89% accuracy**, $719 avg/trade, $1,500 drawdown, **17 consecutive winners**, profit factor 5.47. This is an exceptional opportunity -- the problem is that not many months have a TDM 22.

**Long-term persistence**: From the 1980s through May 2011, buying on the opening of the 5th trading day prior to month-end generated over $32,000 of profits on 119 trades, $275 avg/trade, worst drawdown less than $3,700.

---

## Willspread Indicator

### Concept

Willspread measures the relative relationship between a primary market and a secondary (related) market. It detects causative shifts in intermarket dynamics rather than using price to predict price.

### Formula

1. **Calculate the spread ratio**: (Primary Market Price ÷ Secondary Market Price) × 100
2. **Apply exponential moving averages**: Calculate a fast EMA (5-period for intraday, 14-period for daily) and slow EMA (20-period for intraday, 19-period for daily) of the spread ratio
3. **Willspread value** = Fast EMA - Slow EMA

### Market Pairings
- **Bonds**: Primary = Bonds, Secondary = Gold (Gold exerts major impact on Bonds)
- **S&P 500**: Primary = S&P 500, Secondary = T-Bills or Bonds (interest rates drive stocks)

### Trading Rules

- **Buy signal**: Willspread crosses from **negative to positive** territory (below zero line to above). This means the primary market is strengthening relative to its secondary market.
- **Next-bar confirmation** (critical): After the zero-line crossing, Williams **almost always waits** for the very next bar to rally above the high of the bar that produced the crossing. This confirmation step filters false signals.
- **Sell signal**: Willspread crosses from **positive to negative**. Wait for the next bar to trade below the low of the crossing bar for confirmation.
- **Exception**: Confirmation can be skipped if other technical gauges (trendlines, positive oscillator readings) corroborate the signal.

### Performance

Willspread has worked consistently from the mid-1980s through 2011. It correctly signaled the 1987 crash (negative crossing on October 14 at 311.50, stayed short through the debacle to exit at 219.50 on October 20 for $46,000/contract profit). On daily charts, a 14/19-day Willspread measurement remains effective for determining longer-term Bond trend.

### Application

When Willspread is positive and rising, the primary market is strengthening relative to its secondary market -- bullish for the primary. When negative and falling, the primary is weakening -- bearish. This provides an intermarket confirmation filter that avoids the trap of using price to predict price. Willspread is best combined with the 3-bar high/low channel: when Willspread is positive, buy pullbacks to the 3-bar MA of lows; when negative, sell rallies to the 3-bar MA of highs.

---

## Electronic Era Pattern Status

The transition from pit trading to electronic markets fundamentally changed some patterns while leaving others intact. Williams' assessment (2011 update):

### Patterns Diminished by Electronic Trading
- **Oops! pattern**: Greatly diminished. The 16-18 hour gap that created explosive openings no longer exists. Markets now close only a few hours before reopening, eliminating the pent-up order flow that drove gap reversals. Retains limited value on Sunday evening opens and post-major-news events only.
- **GSV (Greatest Swing Value)**: The opening price as reference point has lost its predictive power. The open is now essentially the prior close, so the Open-to-High/Low failure swing measurement no longer captures meaningful data. The underlying concept may work with alternative reference points (prior day's low, close, or high), but this remains an area for future research.

### Patterns That Have Held Up
- **TDW (Trading Day of Week)**: Held up from the 1960s through 2011 and beyond. Monday-Tuesday bullish bias in S&P, Wednesday weakness, and Friday strength have persisted across the pit-to-electronic transition. This is one of Williams' most enduring discoveries.
- **TDM (Trading Day of Month)**: Month-end strength and first-of-month rallies have been remarkably consistent. Bond TDM 18/22 patterns from the 1980s continued working through 2011. S&P first-of-month with 80%+ accuracy spans three decades.
- **Outside Day**: Confirmed working on S&P E-Mini from 1998 forward with similar results to pit-era testing.
- **Smash Day / Hidden Smash Day**: These patterns are based on fundamental human psychology (public getting trapped at wrong moments) and remain valid in electronic markets.
- **Specialists' Trap**: The concept of false breakouts from congestion zones is structural and persists regardless of execution venue.
- **Willspread**: Worked consistently from the mid-1980s through 2011 across market regimes, including correctly signaling the 1987 crash and 1997/1998 selloffs.

---

## Script Output Interpretation Guide

### Pattern Scan Output

When reviewing pattern scan results:
- **Pattern type**: Identify which of the 5 patterns was detected. Outside days and Smash days are the most frequent; Specialists' Traps and Oops! are rarer but higher-conviction
- **Reversal confirmation**: Has the immediate reversal (next day) already occurred? If so, the entry may have been missed. Williams' patterns require NEXT-DAY confirmation
- **Context**: A pattern in a strong trend (continuation) is higher probability than the same pattern in a choppy range. Check the swing point hierarchy for trend alignment
- **TDW filter**: Reject pattern signals that occur on historically unfavorable days for the instrument

### TDW/TDM Analysis Output

When interpreting calendar bias output:
- **Convergence**: The strongest signal occurs when both TDW and TDM point bullish simultaneously. A Monday (bullish TDW for S&P) that falls on TDM 20 (bullish TDM) is a high-conviction setup
- **Divergence**: When TDW is bullish but TDM is bearish (or vice versa), reduce position size or pass on the trade
- **Historical consistency**: TDW patterns have held for 40+ years across regime changes. If a TDW pattern appears broken in recent data, it may be a temporary anomaly rather than a regime shift
- **Integration with other signals**: TDW/TDM are SETUP conditions, not entry triggers. Use them to determine WHEN to look for volatility breakout or pattern entries, not as standalone buy/sell signals
