# TraderLion Trade Management

## Overview

Systematic trade management methodology combining precise entry tactics with edge-based position sizing, disciplined stop placement, and staged sell rules. The framework prioritizes capital preservation through "tight and logical" risk control, progressive exposure scaling, and continuous post-analysis feedback loops.

> "Ninety per cent of any great trader is going to be the risk control." — Paul Tudor Jones

> "You want to be trading your largest when you are trading your best and your smallest when conditions/your trading is at its worst." — Mark Minervini

---

## Entry Tactics

Entry tactics are short-term processes and patterns used to build a position as a larger setup is being completed. Each tactic has a well-defined pivot point (entry trigger) and a risk management level (stop placement). The pipeline detects actionable entry patterns (MA pullbacks, consolidation pivots, inside days, tight days, gap reversals, support reclaims) with trigger/stop prices; the agent selects the appropriate tactic and interprets context.

### Setup-to-Tactic Pairing

| Setup | Available Entry Tactics |
|-------|------------------------|
| Launchpad / Base Breakout | Key Support Level Reclaim, Consolidation Pivot Breakout, Key MA Pullback, Oops Reversal, Key Support Level Pullback |
| Gapper | Opening Range Breakout, Intraday Base Entry, High Volume Close Pivot |
| Post-Breakout (any setup) | 10 SMA Retest, 21 EMA Catch-Up, First 50 SMA Touch |

### Launchpad / Base Breakout Tactics

1. **Key Support Level Reclaim**: Undercut prior support (base low or 50 SMA) then surge back above. Stop below relevant higher low, target < 5% ideally < 3%. Often one of the first tradable spots in a base.
2. **Consolidation Pivot Breakout**: Tightens within consolidation → breakout above shorter-term resistance. Stop at nearest higher low or respected MA. Build position up the right side before the traditional base breakout.
3. **Key MA Pullback**: Gradual pullback on below-avg volume to a respected MA. Trigger when demand appears at the MA. Stop just below the MA (< 1-2% risk). Also valid on sudden gap downs to the MA that close strong.
4. **Oops Reversal**: Gap down below prior day's low → price reclaims the prior low (Larry Williams pattern). Best up the right side into a support area. Stop at low of day.
5. **Key Support Level Pullback**: Gradual pullback on lower volume to a prior consolidation/base pivot. Stop just below the pivot and forming higher low.

### Post-Breakout Tactics

6. **10 SMA Retest**: Quick retest of 10 SMA after breakout. Stop below the 10 SMA. Often occurs in the first few days.
7. **21 EMA Catch-Up**: 1-3 week rest as 21 EMA catches up. Stop below the 21 EMA. Opportunity to add or start new position.
8. **First 50 SMA Touch**: Longer-term pullback to 50 SMA after base breakout. First touch is often excellent; quality diminishes on subsequent tests.

### Gapper Tactics

9. **Opening Range Breakout (ORB)**: Day 1 gap up → breakout above 3/5/15-min opening range. Best gappers trend above VWAP all day.
10. **Intraday Base Entry**: Day 1 gap up → intraday base pullback to anchored VWAP. Breakout from the intraday base.
11. **High Volume Close (HVC) Pivot**: Day 2 continuation through prior day's close. Can also serve as U-turn entry after pullback.

### General Entry Principles

- **Entry precision**: Get in within 1.5% of the pivot. Further above degrades risk/reward.
- **Position building**: String together entry tactics (20%, 10%, 20%) as successive pivots trigger. Goal: full position with profit cushion before the larger pattern breakout.
- **Context matters**: Different market periods favor certain setups and tactics. Lean into what produces follow-through.

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

**"Earn the Right to Size Up" Principle**: Larger positions lead to bigger performance ONLY if you can manage risk correctly. Do not increase position size because of conviction alone — increase because the process is working, the market is cooperating, and recent trades confirm the edge.

**Market-Condition Adjustment**:
- Weak markets: 5% starting positions
- Normal markets: 10% starting positions
- Strong markets: 15% starting positions

**Maximum Position Calculation**: Max position = Allowable additional risk (%) / Stop loss (%)

*Example*: 3% additional risk allowable, 4.1% stop loss = 73% max. Constrained by stage max (20% for Stage 2).

---

## Stop Loss System

### The "Tight and Logical" Principle

Every stop must satisfy both criteria simultaneously:

- **Tight**: Loss on the position limited to a few percent (1-4% for swing, up to 6% for volatile names)
- **Logical**: Violation of the stop level invalidates the thesis and suggests the entry tactic has failed

A tight stop alone is useless if normal fluctuations trigger it. A logical stop alone is useless if too far from entry. If you cannot place a tight AND logical stop, wait for a better setup.

**Rule of Three**: Average gain over 6 months / 3 = target maximum stop %
- Day traders: ~3% avg gain → < 1% stops
- Swing traders: ~10% avg gain → < 3% stops
- Position traders: ~30% avg gain → < 10% stops

### Stop Placement Guidelines

- Place a few cents below key levels (obvious stops get shaken out). Always ready to re-enter if the stock reclaims.
- After being stopped out: re-enter if setup still valid; best trades sometimes take multiple attempts. But if the bar suggests significant distribution, wait for the chart to heal.
- **Intraday vs End-of-Day**: In a strong bull market, define two stop levels in advance (e.g., 4% EOD, 7% intraday absolute). In a choppy market, act immediately.

### Stop Adjustment Progression

**Breakeven Adjustment**: Move stop to cost basis once profit reaches 2-3x the initial stop loss. In weak markets, move faster.

**Trailing Stop Methods**:
1. **MA Trail**: 21 EMA (swing) or 50 SMA (position). Sell on two closes below.
2. **Swing Low Trail**: Raise stop below each new swing low.
3. **Character-Based**: If accelerated/extended → shorter MA. If distribution → tighten to 21 EMA.

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

All three factors are entirely within the trader's control. "Managing risk" means adjusting at least one factor to keep total risk acceptable.

### Risk Dial Concept

Risk is a dial that turns in response to market feedback:
- Uptrending market + winning trades: increase total risk allowance
- Weakening market + losing trades: decrease total risk allowance

---

## Risk Downgrade Strategy

When the market weakens or recent trades are losing, reduce risk systematically through three levers:

1. **Reduce Number of Positions**: Sort existing positions by performance (Grade A-D). Eliminate D-grade first, consider trimming C-grade. Preserve A and B.
2. **Decrease Position Sizes**: Sell portions to bring sizes back to comfortable levels. Adjust starting sizes: 5% (weak) / 10% (normal) / 15% (strong).
3. **Adjust Stop Losses**: Tighten initial stops in weak markets. Be quicker to raise stops to breakeven. Each stock must prove itself worth the risk.

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

### Stage 3: Performance Phase (Adaptive Selling)

- Less proactive selling early in each cycle; sell more aggressively into strength later
- Divide sales between two different key MAs to hold part of position for larger moves
- Market leaders in leading themes: hold core for larger move. Secondary names: quicker to sell into strength.
- **Average winner monitoring**: If average winner increasing → extend holding periods. If declining → lean into swing trading.

### Selling Into Strength Methods

**At Average Gain / R-Multiples**: Sell portions at rolling average gain and at R-multiples (profit / initial stop).

**At Base Extensions**: Stocks typically pause around 20-25% above the top of the base.

**Using MA Extensions**: Note the stock's typical extension from key MAs. Early extensions from a base are shows of power; later extensions are more likely exhaustion.

**On Key Reversals** (sell when 4+ criteria align — pipeline detects automatically):
Extension from MAs, gap fill reversal, trendline breach, abnormal volume, widest range, reversal below prior low with low CR.

**On Vertical Acceleration** (sell when 3+ criteria align — pipeline detects automatically):
Rate of advance steepened, >25% above 21 EMA, expanding ranges, erratic volume, 8+ week uptrend. Sell at least 1/3 into the strength.

### Selling Style Choice

Selling into strength vs. weakness are both valid approaches — a deliberate personal style decision. Swing traders lean toward selling into strength. Position traders lean toward selling into weakness. Inconsistency between the two is where most selling mistakes originate.

*Apply this framework independently to the current analysis target.*

---

## Trade Execution Process

1. **Daily focus list**: Maximum 5 ideas (ideally 1-3). Tighter list = better execution.
2. **Pre-trade plan**: Define buy point, stop loss, share count before market open.
3. **Set alerts** at the buy point and slightly below.
4. **Verification**: As alerts trigger, double-check all setup/tactic requirements.
5. **Order execution**: Place order AND enter pre-planned stop loss immediately.
6. **Near the close**: Check executed trades. In choppy markets, take off trades with no follow-through.
7. **End of day review**: Journal thoughts and improvements.

---

## Post Analysis

### Core Metrics

Track regularly: Batting Average, Average Gain/Loss, Risk/Reward Ratio (target 2:1+), Max Gain, Max Loss, Avg Trade Length (winners vs losers).

### Trade Log & 6-Step Chart Analysis

For each trade: Record symbol, dates, edges, setup/tactic, position size, risk management, execution rating (out of 10), and key takeaways.

**6-Step Process**: (1) Gather trade log info → (2) Mark up chart at decision points → (3) Grade each action → (4) Overall observations → (5) Look 2-3 weeks past exit → (6) Derive system-level rules (not personal resolutions).

**Selecting Trades**: Sort by % return. Analyze top 5 winners and bottom 10 losers. Depth over breadth.

### Equity Curve Analysis

Plot account value over time. Ideal shape: staircase from bottom-left to top-right. Study "difference-maker periods" — replicate those conditions and decisions. If drawdowns exceed the market's, tighten risk management.

See SKILL.md → Analysis, Statistics

---

## Post-Entry Behavior Interpretation

The pipeline provides post-breakout monitoring data and closing range analysis. Use these to classify stock behavior within the first 5-10 trading days:

- **Tennis Ball**: Pulls back briefly, bounces sharply. Strongest behavior — hold/add, trail stop below pullback low.
- **Egg**: Breaks and does not recover. Failed breakout — sell immediately at stop. Do not rationalize holding.
- **Squat**: Consolidates sideways near breakout level. Constructive squat (declining volume, tight range, holding MAs) likely resolves up. Non-constructive squat (erratic volume, wide swings) — sell 2/3.
- **Extension Down with Strong Close**: Sharp decline but closes in upper 60% of range near support. Do not enter same day; monitor 1-3 days for confirmation (higher low, constructive close, no follow-through down).

When pipeline reports constructive bar ratio <0.35, treat as distribution warning regardless of other factors.

---

## Disposition Effect Check Protocol

The disposition effect — holding losers too long and selling winners too early — is the most common bias among growth traders. This protocol activates automatically on every sell/hold query.

### Pipeline-Integrated Audit

The pipeline automatically detects 6 sell signals (21 EMA breach, 50 SMA breach, high-volume reversal, vertical acceleration, key reversal, distribution cluster) and provides signal count with severity grading.

### Trigger Counting Interpretation

- **0-1 signals**: Position healthy. Continue holding per current sell rule stage.
- **2 signals**: Position under stress. Tighten stop to nearest MA. Consider reducing by 1/3.
- **3+ signals**: **Mandatory warning** — display disposition effect alert with triggered signals and specific action. "프로세스가 예측보다 우선한다."

### Adding-to-a-Loser Refusal

If the user requests adding to a position below cost basis AND 2+ sell signals triggered, the agent MUST refuse. "사랑에 빠지지 마라." Wait for a new constructive base, then re-evaluate as a fresh entry. Only overridden by explicit user acknowledgment of risk.

---

## Earnings Event Protocol

Activated when the next earnings report is within 5 trading days for any active position or new entry candidate.

### Step 1: Edge Freshness Check

- **Volume edges**: Was the HVE/HVIPO/HV1 within the last 60 trading days? If older, edge is stale.
- **RS edge**: Is RS score still >=70? Has RS line broken its uptrend?
- **N-Factor**: Is the catalyst narrative still intact? Any negative pre-announcements?

If 2+ edges have gone stale, the position has lost its original thesis.

### Step 2: Position Health Assessment

| Factor | Healthy | Unhealthy |
|--------|---------|-----------|
| Profit cushion | >5% profit | Breakeven or loss |
| Constructive ratio | >0.5 | <0.35 |
| Trend template | >=6/8 passing | <5/8 passing |
| Recent sell signals | 0-1 triggered | 2+ triggered |

### Step 3: Three-Option Framework

**Option A — Full Exit** (edges stale OR position unhealthy):
Sell entire position before earnings. Re-evaluate after for potential fresh entry.

**Option B — Half Position** (edges mixed AND moderately healthy):
Sell 50% before earnings. On remaining 50%: set absolute stop at -8% from current price.

**Option C — Hold with Absolute Stop** (edges fresh AND healthy AND profit cushion >8%):
Hold full position. Set non-negotiable absolute stop at breakeven or -5% from current price, whichever is higher.

**Default**: If uncertain, default to Option B. "실패를 시스템에 내장하라."

---

## Four Contingency Plans

Every trade entry must include four pre-defined contingency plans, documented BEFORE execution.

### Plan 1: Initial Stop (What If Immediately Wrong?)

Define before every entry: specific stop price, stop type (hard vs mental), max loss in $ and %, action on trigger (full exit, no averaging down).

Template: "If {symbol} closes below ${stop_price} ({stop_pct}% below entry), sell entire position for a ${loss_amount} loss ({portfolio_pct}% of portfolio)."

### Plan 2: Re-Entry (What If Stopped Out But Setup Remains Valid?)

Best winning stocks across 2004-2024 frequently required 2-3 entry attempts. Being stopped out on a valid setup is NORMAL.

- **Waiting period**: Minimum 1 trading day after stop-out
- **Re-entry conditions**: Stock reclaims the stop level AND shows constructive action (CR >60%, volume expansion)
- **Size adjustment**: Re-entry at 50% of original position. Scale back to full after 2-3% profit.
- **Maximum attempts**: 2 re-entries on same setup. After 3 total attempts, monitor-only.
- **Shakeout re-entry**: Stop-out that clears weak holders then quickly reclaims with volume is often one of the best re-entry signals.

### Plan 3: Profit-Taking (What If Right And Running?)

- **First target**: Sell 1/3 at first target gain (Stage 1-2: 5%, Progressive: average gain of last 20 trades)
- **Second target**: Sell 1/3 at second target gain OR when visually extended from key MA
- **Final third**: Trail with 21 EMA (swing) or 50 SMA (position). Sell on two closes below.
- **Windfall rule**: If stock gaps up >10% in a single day after already being extended, sell at least 1/3 immediately.

### Plan 4: Disaster Scenario (What If Black Swan?)

- **Gap down >10%**: Sell at market open. Do not wait for recovery.
- **Market-wide crash (QQQ drops >5% in a day)**: Sell all positions below 21 EMA. Hold positions with >10% profit cushion above 21 EMA.
- **Individual stock halt**: Set GTC limit sell order at -8% from last traded price.

Template: "Worst case for {symbol}: gap down to ${disaster_price}. Action: sell at market. Maximum portfolio impact: {max_impact_pct}%."

### Contingency Plan Enforcement

The agent MUST verify all four plans exist before confirming any trade entry. Missing plan → warning: "실패를 시스템에 내장하라."
