# TraderLion Trade Management

## Overview

Systematic trade management methodology combining precise entry tactics with edge-based position sizing, disciplined stop placement, and staged sell rules. The framework prioritizes capital preservation through "tight and logical" risk control, progressive exposure scaling, and continuous post-analysis feedback loops.

> "Ninety per cent of any great trader is going to be the risk control." — Paul Tudor Jones

> "You want to be trading your largest when you are trading your best and your smallest when conditions/your trading is at its worst." — Mark Minervini

---

## Entry Tactics

Entry tactics are short-term processes and patterns used to build a position as a larger setup is being completed. Each tactic has two components: a well-defined pivot point (entry trigger) and a risk management level (stop placement). The goal is to size enough to make a difference if the trade works, while keeping losses small if it fails.

### Launchpad / Base Breakout Entry Tactics

#### 1. Key Support Level Reclaim

- **Condition**: Stock has undercut a prior support level (base low or 50 SMA) and surges back above it
- **Trigger**: Price reclaims the key level after the undercut
- **Stop**: Below the relevant higher low or key technical area; target < 5%, ideally < 3%
- **Notes**: Often one of the first tradable spots in a base. The more powerful the reclaim, the more likely the stock continues higher. Can occur on multiple timeframes (minutes to days)

#### 2. Consolidation Pivot Breakout

- **Condition**: Stock tightens within a consolidation, forming defined shorter-term resistance areas and swing highs
- **Trigger**: Breakout above the consolidation pivot (shorter-term resistance)
- **Stop**: Nearest relevant higher low or key moving average the stock has previously respected; target < 5%, ideally < 3%
- **Notes**: Allows building positions up the right side of a consolidation before the traditional base breakout. Goal is to have a full position with a profit cushion before the stock breaches the traditional base pivot

#### 3. Key Moving Average Pullback

- **Condition**: Stock pulls back gradually on below-average volume to a key moving average it has previously respected, showing Relative Strength
- **Trigger**: Demand comes in at the moving average; stock holds and pushes higher. Also valid on sudden gap downs to the MA that close strong
- **Stop**: Just below the moving average; if the stock undercuts and fails to reclaim, the tactic has failed. Risk can be very small (< 1-2%)
- **Notes**: Build position as close to the MA as possible. Be ready to give the stock multiple shots at working

#### 4. Oops Reversal

- **Condition**: Stock gaps down below prior day's low (Larry Williams pattern). Best when occurring up the right side of the base and into a potential support area (MA or consolidation pivot)
- **Trigger**: Price pushes back up through the prior day's low
- **Stop**: Low of the day or nearby key support level
- **Notes**: Strongest oops reversals immediately rebound with high daily closing ranges and ideally outside days. The "oops" is when sellers who exited on the gap down have to buy back

#### 5. Key Support Level Pullback

- **Condition**: Stock pulls back gradually on lower than average volume to a prior consolidation pivot or base pivot
- **Trigger**: Stock rebounds from and shows respect for the key level
- **Stop**: Just below the pivot and the higher low that is forming

### Post-Breakout Entry Tactics

After the initial base breakout, add to positions or start swing trades using these tactics. Earlier additions after the first base breakout carry higher quality; second and third tests of MAs further from the base are lower quality.

#### 6. 10 SMA Retest

- **Condition**: After a breakout, stock makes a quick retest of the 10-day SMA
- **Trigger**: Stock holds and bounces from the 10 SMA area
- **Stop**: Below the 10 SMA
- **Notes**: Often occurs in the first few days after a breakout

#### 7. 21 EMA Catch-Up

- **Condition**: After trending, stock rests for one to three weeks as the 21 EMA catches up
- **Trigger**: Stock holds the 21 EMA area and resumes upward
- **Stop**: Below the 21 EMA
- **Notes**: Opportunity to add to a position or start a new one if prior entries were missed

#### 8. First 50 SMA Touch

- **Condition**: Stock experiences a longer-term pullback to the 50 SMA / 10-week MA after a base breakout
- **Trigger**: First touch of the 50 SMA shows demand and support
- **Stop**: Below the 50 SMA
- **Notes**: The first touch after a longer-term base breakout is often excellent. Quality diminishes on subsequent tests as the stock may need to form another base

### Gapper Setup Entry Tactics

#### 9. Opening Range Breakout (ORB)

- **Condition**: Day 1 of a gap up. Stock forms a short range in the opening prints (3-min, 5-min, or 15-min)
- **Trigger**: Breakout above the opening range high
- **Stop**: Recent intraday low or higher low within the range
- **Notes**: Best gappers open and trend above daily VWAP all day. Shorter timeframes carry more noise and failures

#### 10. Intraday Base Entry

- **Condition**: Day 1 of a strong gap up. Stock forms intraday bases and pulls back, often coinciding with pullbacks to intraday anchored VWAP
- **Trigger**: Breakout from the intraday base
- **Stop**: Recent higher low within the intraday base

#### 11. High Volume Close (HVC) Pivot

- **Condition**: Day 2 pattern looking for continuation through the close of the gap-up day. Allows judging the quality of the gapper setup by volume and closing range
- **Trigger**: Continuation move through the prior day's close (HVC confirmation)
- **Stop**: Low of the breakout day or relevant intraday higher low; target < 3%
- **Notes**: Can also be used as a U-turn entry after a pullback and consolidation. Often used as the last addition when building a position through ORB + intraday base + HVC

*Apply this framework independently to the current analysis target.*

---

## Position Sizing

### Edge-Based Sizing System

Position sizing is determined by the number of edges present in a setup, combined with market conditions, recent trading performance, and conviction.

**Base Position**: 10% of portfolio (Stage 1-2 traders)

**Edge Adjustment**: +2.5% per additional edge identified, up to a maximum of 4 edges

| Edges Present | Position Size |
|---|---|
| 0 (base) | 10% |
| 1 edge | 12.5% |
| 2 edges | 15% |
| 3 edges | 17.5% |
| 4 edges (max) | 20% |

**Stage-Dependent Guidelines**:
- Stage 1: Stay consistent at base 10% while building process
- Stage 2: Adjust up to 20% maximum based on edges, market, and feedback
- Stage 3: Customize parameters after proving risk management across multiple market cycles

**Market-Condition Adjustment**:
- Weak markets: 5% starting positions
- Normal markets: 10% starting positions
- Strong markets: 15% starting positions

**Pre-Trade Sizing Checklist**:
1. What is current total open risk? How much can be added?
2. What is the expected stop loss level and % loss on position?
3. What is conviction level and how many edges are present?
4. What is the health of the current market (weak / normal / strong)?
5. How have recent trades performed? Is feedback positive?

**Maximum Position Calculation**: Max position = Allowable additional risk (%) / Stop loss (%)

*Example*: 3% additional risk allowable, 4.1% stop loss = 73% max. Constrained by stage max (20% for Stage 2).

---

## Stop Loss System

### The "Tight and Logical" Principle

Every stop must satisfy both criteria simultaneously:

- **Tight**: Loss on the position limited to a few percent (1-4% for swing, up to 6% for volatile names)
- **Logical**: Violation of the stop level invalidates the thesis and suggests the entry tactic has failed

A tight stop alone is useless if normal fluctuations trigger it. A logical stop alone is useless if it is too far from the entry to keep the loss small. If you cannot place a tight AND logical stop, wait for a better setup.

**Rule of Three**: Average gain over 6 months divided by 3 = target maximum stop percentage
- Day traders: ~3% avg gain -> < 1% stops
- Swing traders: ~10% avg gain -> < 3% stops
- Position traders: ~30% avg gain -> < 10% stops

### Stop Placement Guidelines

- Place a few cents below key levels (obvious stops get shaken out)
- Strong bull markets: give benefit of the doubt; can use wider intraday stop as worst case (decide in advance)
- Weak/choppy markets: act immediately, cut early if stock does not act well
- Hard stops for those who cannot watch the market constantly
- After being stopped out: re-enter if setup and story are still valid; best trades sometimes take multiple attempts

### Stop Adjustment Progression

**Breakeven Adjustment**: Move stop to cost basis once profit reaches 2-3x the initial stop loss
- Strong market: standard 2-3x rule
- Weak market: move faster, even at just a few % profit

**Trailing Stop Methods**:
1. **Moving Average Trail**: Use 21 EMA (swing) or 50 SMA (position). Sell on two closes below the MA once it rises above cost basis
2. **Swing Low Trail**: Raise stop below each new swing low as the stock continues higher
3. **Character-Based Adjustment**: If stock starts an accelerated move when already extended, switch to shorter MA (e.g., low of 2 days ago). If stock shows distribution (downside reversals, failed breakouts), tighten to 21 EMA or low of the week

---

## Total Open Risk Management

### Formula

```
Total Risk ($) = Position_1 × Stop_1% + Position_2 × Stop_2% + ... + Position_n × Stop_n%

Total Risk (%) = [Total Risk ($) / Portfolio Value ($)] × 100
```

### Three Control Factors

1. **Number of positions** open
2. **Size of each position** in dollars
3. **Stop loss location** on each position

All three factors are entirely within the trader's control. "Managing risk" means adjusting at least one factor to keep total risk acceptable given risk tolerance, style, market conditions, extensions from MAs, volatility, and YTD profits.

### Risk Dial Concept

Risk is not on/off — it is a dial that turns in response to market feedback:
- Uptrending market + winning trades: increase total risk allowance
- Weakening market + losing trades: decrease total risk allowance
- Progressive exposure: raise sizing in response to positive feedback, lower in response to negative feedback

---

## Risk Downgrade Strategy

When the market weakens or recent trades are losing, reduce risk systematically:

### 1. Reduce Number of Positions (Grade A-D)

Sort existing positions by profit/performance over the past month and forward potential:
- **Grade A**: Strongest performers, strongest outlook — keep
- **Grade B**: Solid, but not the best — hold if possible
- **Grade C**: Mediocre — consider trimming
- **Grade D**: Weakest performers — eliminate first

### 2. Decrease Position Sizes

- Sell portions of positions to bring sizes back to comfortable levels
- Preserve strongest stocks first
- If a winner is extended and showing weakening signs: sell half, re-enter when conditions firm
- Adjust starting sizes: 5% (weak market), 10% (normal), 15% (strong market)

### 3. Adjust Stop Losses

- Tighten initial stops in weak markets
- Be quicker to raise stops to breakeven
- Each stock must prove itself worth the risk
- Strong markets are forgiving; weak markets are not

---

## Sell Rules

### Stage 1-2: Consistency Phase (Rigid Rules)

**Initial Sell**: At 5% profit, immediately sell half the position and raise stop on the balance to breakeven

**Trailing**: If stock continues without hitting stops, trail using relevant key moving averages:
- Swing traders: 21 EMA — sell on two closes below
- Position traders: 50 SMA — sell on two closes below

**Maximum Stop**: If stock ever breaches maximum stop loss, sell immediately — no exceptions

### Progressive Sell Rules (Stage 2 Advancement)

Advance through these progressions only after demonstrating consistent process:

1. Sell 1/3 at 5%, sell 1/3 at rolling average gain of last 20 trades, sell 1/3 on MA weakness
2. Sell 1/3 at 5%, sell 1/3 into strength when visually extended from MA, sell 1/3 on MA weakness
3. Same as #2 but allow adding back 1/3 if stock forms another low-risk entry tactic
4. Sell 1/3 at average gain, sell 1/3 into strength, sell 1/3 on MA weakness; allow adding back up to 2/3 on new low-risk buy points

### Stage 3: Performance Phase (Aggressive Selling)

- Less proactive selling early in each cycle; wait until later to sell more aggressively into strength
- Divide sales between two different key MAs to hold part of position for larger moves
- Judgment calls on MA closes: Are they sharp and definitive, or merely drifting? Is the second close higher than the first?
- Market leaders in leading themes: hold core for larger move
- Secondary/performance enhancer names: quicker to sell into strength

### Selling Into Strength Methods

**At Average Gain / R-Multiples**: Sell portions at rolling average gain and at R-multiples (profit / initial stop). Ensures winners pay for stop-outs.

**At Base Extensions**: Stocks typically pause around 20-25% above the top of the base. Swing traders can sell some or all at this level.

**Using MA Extensions**: Note the stock's typical extension from key MAs (%, ATR, or visual). Sell a portion when extension approaches historical limits. Early extensions from a base are shows of power; later extensions are more likely exhaustion.

**On Key Reversals** (sell when 4+ of these criteria align):
- Stock was visually extended from MAs at the high
- Gap up that fills and reverses downward
- Breach of a trend line of highs
- Volume abnormally high or highest since breakout
- Widest range bar since breakout
- Reversal below prior day's low with low closing range

*Apply this framework independently to the current analysis target.*

---

## Post Analysis

### Trade Log Template

For each trade, record in real time:

| Field | Detail |
|---|---|
| Symbol | Ticker |
| Date | Entry/exit dates |
| Why | Specific edges present |
| Setup & Entry Tactic | Which pattern and tactic used |
| Position Size | % of portfolio and how arrived at |
| Initial Risk Management | Stop location and rationale |
| Position Management | Actions taken after entry |
| Execution Rating | Out of 10, with rationale |
| Key Takeaways | Lessons for future trades |

### 6-Step Chart Analysis Process

1. **Gather trade log information**: Notes, screenshots at key actions (buys/sells)
2. **Mark up the chart**: Label buys, sells, stops, MAs on the chart at the time of entry
3. **Grade action by action**: Entry execution, stop management, sell decisions — each graded out of 10
4. **Overall trade observations**: What went well, what went poorly, what could improve
5. **Look forward past exit**: Did the stock set up again? Was timing or market cycle the issue?
6. **Derive system-level rules**: Not "I need to buy closer to the pivot" but implement a specific routine change (set alerts below pivot)

### Key Trade Analytics

Track these metrics regularly (every few months):

- **Batting Average**: Winners / Total trades (eliminate +-1% scratch trades)
- **Average Gain**: $ amount, % on position, equity contribution (% gain x position size)
- **Average Loss**: $ amount, % on position, equity contribution
- **Risk/Reward Ratio**: Average gain / Average loss — target 2:1 or better
- **Max Gain**: Maximum gain over the period
- **Max Loss**: Should be nearly equal to average loss; any outlier loss requires root cause analysis
- **Avg Trade Length (Winners)**: Should be much longer than losers
- **Avg Trade Length (Losers)**: Minimize to cut losses fast

### The 1% Improvement Philosophy

> "Consistent 1% improvements over time can lead to dramatic changes in your performance and process."

Post analysis is the single most impactful exercise for improving performance. Approach losses objectively — each series of trades is impacted by the market. Do not change rules too fast based on data from one market cycle. Iterate, analyze, adjust, repeat.

See SKILL.md -> Analysis, Statistics

---

## Trading Rules Framework

A complete rule set should address these seven sections:

1. **Market Analysis**: How to define trends, assess market health
2. **Stock Selection & Routines**: Screening criteria, watchlist management
3. **Edges, Setups & Entry Tactics**: Specific patterns with chart examples
4. **Risk Management & Position Sizing**: Stops, total risk, sizing rules
5. **Sell Rules & Position Management**: Selling into weakness/strength, trailing
6. **Post Analysis & Journaling**: Frequency, metrics, rule updates
7. **Contingency Planning**: Gap downs, system failures, emergency contacts

Rules must be written with enough clarity and specificity that a trader of similar experience could follow them. Rules in your head don't count. They are a living document — revisit and revise as you evolve.
