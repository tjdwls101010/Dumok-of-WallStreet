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

**Trading Rule**: Buy on the next day's open. The pattern's strength increases significantly when aligned with favorable TDW days.

**Pattern Combination**: Outside Day + TDW is one of the strongest stacking combinations.

**Electronic Era Status**: Outside days remain bullish even in electronic markets.

### 2. Smash Day (Naked Close)

**Definition**: A day that closes below the prior day's low (naked down close) or above the prior day's high (naked up close). This violent price action draws the public into the fray at exactly the wrong moment.

**Buy Setup**:
- Day 1: Close < Prior day's Low (naked down close). May also take out 3-8 days of lows
- Day 2: If price trades ABOVE Day 1's High, buy immediately
- The immediate reversal means the public's breakout has failed

**Sell Setup**:
- Day 1: Close > Prior day's High (naked up close)
- Day 2: If price trades BELOW Day 1's Low, sell immediately

**Key Requirement**: The reversal must occur the VERY NEXT DAY. The pattern's power comes from the immediacy of the failure. If several days pass without reversal, the original breakout may be valid.

**Trading Rule**: Use this pattern in two contexts:
1. **Trend continuation**: In a strong trend, a smash day against the trend is a pullback entry
2. **Range breakout failure**: In a 5-10 day choppy range, a smash day followed by immediate reversal suggests a breakout in the opposite direction

### 3. Hidden Smash Day

**Definition**: A day that closes UP for the day but in the bottom 25% of its range (and ideally below the open). The up close masks the fact that buyers got smashed.

**Buy Setup**:
- Day 1: Close > Prior Close (up day), but Close is in the **lower 25%** of the day's range. Best patterns also have **Close < Open**
- Day 2: If price rallies above Day 1's High, buy

**Hidden Smash Day Refinement**: The lower 25% threshold is the key discriminator. The additional confirmation of Close < Open significantly increases reliability, because it confirms that buyers were truly smashed.

**Pattern Combination**: Hidden Smash Day + trading range context produces the strongest signals.

### 4. Specialists' Trap (Wyckoff Trap)

**Definition**: Derived from Richard Wyckoff's 1930s work on market manipulation. A false breakout from a 5-10 day congestion zone that reverses within 1-3 days.

**Buy Trap Setup**:
- Down-trending market stabilizes sideways for 5-10 days
- Price breaks below with a naked close lower than all daily lows of the range
- Within **1-3 days**, price snaps back above the **"true high of the breakdown day"**

**Critical Point**: The "true low/high of the breakout/breakdown day" becomes the **trigger level**. Its violation within the strict 1-3 day time window is the entry signal. If more than 3 days pass, the setup is invalidated.

### 5. Oops! Pattern

**Definition**: The most reliable short-term pattern Williams ever traded in the pit era, based on an overemotional gap response that immediately reverses.

**Buy Setup**:
- Market gaps down, opening below the prior day's low
- During the same session, price recovers back up to the prior day's low
- Buy at the prior day's low -- the gap down was an emotional overreaction

**Electronic Era Limitation**: This pattern has been **greatly diminished** by electronic trading. The 16-18 hour gap that once created explosive openings no longer exists. Retains value on Sunday evening opens and after major news events.

---

## Trading Day of the Week (TDW) Framework

Not all days of the week are created equal. This is one of Williams' most enduring discoveries, holding from the 1960s through 2011 and beyond.

### S&P 500 TDW Bias

- **Monday**: Strongest buy day. Mon-Tue combined = most reliable
- **Tuesday**: Second-best buy day. Strengthened in electronic era
- **Wednesday**: **Weakest day; exclude from buy systems.** Excluding Wed reduced drawdown by ~65%
- **Thursday**: Best sell day for short signals
- **Friday**: Strongest absolute performance; ~57% close above open

### TDW Application

TDW is used as a setup filter, not a standalone system. The best trades combine TDW bias with volatility breakouts and intermarket confirmation.

---

## Trading Day of the Month (TDM) Framework

TDM measures the trading day number within each month (not calendar date). A month typically has 20-22 trading days.

### S&P 500 TDM Bias

- **Month Start Bullish Zone (TDM 1-4)**: Strong bullish bias
- **Midmonth Weakness (TDM 5-7, 12-13)**: Negative expected returns. Avoid initiating new longs
- **End-of-Month Rally (TDM 19-22)**: The strongest and most reliable seasonal pattern
- **Best TDMs for buying**: 8, 18, 19, 20, 21, 22

### TDM Application

Like TDW, TDM is used as a setup -- a leading indicator of when to take action. Williams does not blindly trade TDM signals; he waits until TDM aligns with his other tools.

### TDW/TDM Interaction Rules

The interplay between TDW and TDM creates a two-dimensional filter that is the cornerstone of Williams' calendar-based trade qualification:

- **Convergence (both bullish)**: This is the **highest-conviction** setup. When a bullish TDW coincides with a bullish TDM, the combined probability significantly exceeds either signal alone. Williams calls this "stacking the deck."
- **Divergence (conflicting signals)**: When TDW is bullish but TDM is bearish (or vice versa), **reduce position size or pass entirely**. The conflicting calendar signals dilute the edge.
- **Practical application**: The more confirming biases present (TDW + TDM + intermarket + volatility breakout), the larger the position warranted.

---

## Electronic Era Pattern Status

The transition from pit trading to electronic markets fundamentally changed some patterns while leaving others intact:

### Patterns Diminished by Electronic Trading
- **Oops! pattern**: Greatly diminished. Retains limited value on Sunday evening opens and post-major-news events only.
- **GSV (Greatest Swing Value)**: Opening-based reference has lost predictive power. The underlying concept may work with alternative reference points.

### Patterns That Have Held Up
- **TDW/TDM**: Held from the 1960s through 2011 and beyond
- **Outside Day**: Confirmed working on S&P E-Mini from 1998 forward
- **Smash Day / Hidden Smash Day**: Based on fundamental human psychology and remain valid
- **Specialists' Trap**: Structural false-breakout concept persists regardless of execution venue
- **Willspread**: Worked consistently from the mid-1980s through 2011

---

## Script Output Interpretation Guide

### Pattern Scan Output

When reviewing pattern scan results:
- **Pattern type**: Identify which of the 5 patterns was detected. Outside days and Smash days are the most frequent; Specialists' Traps and Oops! are rarer but higher-conviction
- **Reversal confirmation**: Has the immediate reversal (next day) already occurred? Williams' patterns require NEXT-DAY confirmation
- **Context**: A pattern in a strong trend (continuation) is higher probability than the same pattern in a choppy range. Check the swing point hierarchy for trend alignment
- **TDW filter**: Reject pattern signals that occur on historically unfavorable days

### TDW/TDM Analysis Output

When interpreting calendar bias output:
- **Convergence**: The strongest signal occurs when both TDW and TDM point bullish simultaneously
- **Divergence**: When TDW is bullish but TDM is bearish (or vice versa), reduce position size or pass
- **Historical consistency**: TDW patterns have held for 40+ years across regime changes
- **Integration with other signals**: TDW/TDM are SETUP conditions, not entry triggers. Use them to determine WHEN to look for volatility breakout or pattern entries, not as standalone buy/sell signals
