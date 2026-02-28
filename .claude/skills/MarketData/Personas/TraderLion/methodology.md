# TraderLion Analysis Methodology

## Overview

Momentum-based growth stock methodology combining systematic stock selection (TIGERS), structured workflow (S.N.I.P.E.), and disciplined risk management to identify and ride institutional-driven trends. Rooted in William O'Neil's CANSLIM tradition but evolved with proprietary edges, setups, and entry tactics.

> "The goal with edges and setups is to define frameworks for identifying and entering high potential stocks at a point where if you are right, you will quickly be at a profit, and where if you are wrong, you will quickly be stopped out for a negligible loss."

---

## Core Philosophy

- **Ride Institutional Waves** — Sustained trends are created by the largest funds. Identify and ride these waves. Retail size is an advantage — nimble entry/exit at points where institutions build over weeks.
- **Simplicity and Specialization** — Fewer cogs, more polish. Focus on price action; one style, one strategy mastered deeply. A handful of setups, strict criteria for the top 1%.
- **Plan for Failure** — Build failure into the system. The system and psyche must survive drawdowns so performance compounds during favorable periods.
- **Manage Risk Tightly** — Losses must be papercuts. Every entry needs a tight and logical stop at an important technical level. "If you can master this skill — the ability to always enter with both a tight and logical stop loss in a high potential stock and setup — you will succeed in the market."
- **Think in Cycles** — Market and stocks rise/fall in cycles. Trade in the right direction relative to the current trend. Become aggressive at the right points.

---

## The S.N.I.P.E. Workflow

Five-step systematic workflow progressively narrowing from the total market to a focused, actionable trade.

### Step 1: Search and Scan
- Cast the widest net — broad liquidity, dollar volume, basic fundamental filters
- Target ~400-500 names; general screens (75-400 results) + specialist screens (<50 results)
- Track result counts over time — fluctuations reveal breadth changes

### Step 2: Narrow
- Filter for TIGERS criteria — theme, fundamentals, momentum, trend
- Scan for price/volume signatures (HV edges, RS characteristics)
- Reduce to ~75 weekly candidates

### Step 3: Identify
- Cross-reference each candidate against edge checklist → pipeline의 `edge_count`, `snipe_composite` 참조
- Confirm setup type matches current market conditions
- Build weekly focus list of max ~15 names

### Step 4: Plan
- Define exact entry level and failure level → pipeline의 `entry_readiness` 참조
- Calculate position size based on edge count → pipeline의 `position_tier` 참조
- Set alerts, prepare gap contingency plans, document plan before execution

### Step 5: Execute
- Execute plan as designed; no emotion-based deviation
- Monitor closing range and volume post-entry → pipeline의 `constructive_ratio`, `volume_edge` 참조
- Apply sell rules for both strength and weakness → pipeline의 `sell_signal_audit` 참조
- Track profit cushion for overnight hold decisions

### Climax Top Recognition

After a major move, a stock accelerates upward in a euphoric last push. This climax top often marks the end of a model stock's rise. Decision rule: sell. Institutional investors are now net selling to the crowd. No fundamental story overrides this signal. Benchmark: SCHW — 400% in 24 weeks, then fell 65% in 6 months.

### Sell Philosophy: Technicals Override Fundamentals

"Although we buy based on both technicals and fundamentals, we must look to the charts to determine exactly when we should sell." Fundamentals often deteriorate only after the stock has already fallen significantly. Never fall in love with a stock. Previously great stocks that rose tenfold can lose momentum and tumble 75%+.

### Undercut and Rally

A stock undercuts a prior established low then immediately rallies back above within 1-3 days. The undercut stops out weak holders and triggers shorts; the rally forces covering and attracts new buyers. Recovery volume exceeds undercut volume. Frequently marks the final low before a breakout. → pipeline의 `special_pattern_flags.undercut_and_rally` 참조

---

## TIGERS Stock Selection Criteria

Six dimensions evaluated when selecting stocks. A stock meeting multiple TIGERS criteria simultaneously presents the highest probability opportunity. → pipeline의 `tigers_summary` 참조

### T — Theme
- Two types: **Transformative** (new tech changing how we live) and **Cyclical** (economic cycle-driven)
- **Three-Wave Alignment**: healthy market + disruptive theme + best-positioned company = maximum potential
- **PLGs**: Stocks move in groups. Even average stocks in strong groups outperform strongest stocks in weak groups

### I — Innovation
- Proprietary technology or unique approach separating the company from peers
- Assess via subject matter experts; experience product firsthand if possible
- Institutional behavior must confirm the thesis in price action

### G — Growth
- Minimum 25% YoY quarterly EPS/sales growth; triple-digit preferred
- **Acceleration** is a powerful signal (25% → 40% → 80% sequential quarters)
- Revenue growth matters — many companies prioritize growth over immediate profit

### E — Edges
- Chart displays recognized technical edges indicating institutional accumulation → pipeline의 `edge_count`, `winning_characteristics` 참조
- Trending orderly, fighting downtrends, gapping up on earnings, breaking out from bases
- See `stock_identification.md` for detailed edge definitions

### R — Relative Strength
- RS line in uptrend, ideally making new highs; near top of 3-month RS leaderboards → pipeline의 `rs_ranking` 참조
- Consistently above key MAs; leading the market in current cycle

### S — Setup
- Actionable, studied setup with clearly defined entry and failure levels
- Must allow tight and logical risk management → pipeline의 `entry_readiness` 참조
- See `stock_identification.md` for setup definitions

---

## The Four Stages of Trader Development

Every trader passes through four stages. Progression requires brutal self-honesty, identified through the equity curve.

### Stage 1: Unprofitable
- **Equity curve**: Volatile, downtrending. Random entries/exits, no system, no risk management.
- **Risk level**: Minimal real capital. Paper trading or very small positions.
- **Path forward**: Commit to learning. Write first rules. Implement stop losses and sell rules.

### Stage 2: Boom and Bust
- **Equity curve**: Volatile, non-trending. Tracks with the market — up when good, gives back when it turns.
- **Risk level**: Conservative sizing. Focus on learning over performance.
- **Path forward**: Focus on ONE time frame and ONE strategy. The transition to Stage 3 generally occurs when traders limit noise and master one setup. This is the critical turning point.

### Stage 3: Profitable and Consistent
- **Equity curve**: Generally upward, forming higher lows cycle to cycle.
- **Risk level**: Normal sizing. Begin pushing on highest-quality setups with tight entries.
- **Path forward**: Master a handful of edges deeply. Trade in sync with medium-term cycles. Tighter entries enable larger size with same risk.

### Stage 4: Performance
- **Equity curve**: Sharp upward trend with shallow drawdowns.
- **Risk level**: Full concentration on best opportunities. Aggressive sizing at correct cycle moments.
- **Path forward**: Fully master entry nuances. Anticipate shorter-term cycles. "Wait, stalk, and pounce when the time is right."

### Equity Curve Diagnostic
Plot portfolio value over at least one year. Each stage has a characteristic shape. Most top traders take approximately two full bull-to-bear cycles to reach Stage 3. Rushing typically results in regression.

---

## New Edge Discovery

### Trading Studies
Structured process for investigating market observations and discovering new edges:
- **Generate Ideas** — Study setups, read trading books, analyze model book stocks. Ask: What is my weakness? What do past winners share?
- **Define the Study** — Scope completable in ~1 month. Phrase as: "I will study ______ with the goal of ______."
- **Collect Examples** — Define exact data points. Collect from different time periods and market environments.
- **Analyze Results** — Write hypotheses, create plots, group by similar data points, analyze outliers.
- **Draw Conclusions** — Organize findings with key takeaways, statistics, and conditional probabilities.

### Model Book Construction
Compilation of highest-quality stocks over a cycle, with fundamental/technical data annotated.
- Determine scope → Build larger list → Finalize selectively → Research fundamentals → Annotate charts → Build reference document
- **Key Insight**: The consolidation pivot entry — begin positions at low-risk entry points up the right side of a base, earlier than traditional breakout. True leaders almost always present another low-risk entry point.

---

## Screening Framework

- **Design Process**: Define purpose (general 75-400 results vs. specialist <50) → identify model stock → define characteristics → prototype → analyze → iterate
- **Fundamental Data Points**: Dollar volume, EPS/sales growth, EPS surprise, growth acceleration
- **Technical Data Points**: RS ratings (1w/1m/3m/6m/12m), price vs. 50/150/200 SMA, % off highs/lows, Weinstein Stage
- **Two Goals**: (1) Consistently find actionable trade ideas; (2) Gauge market health via result count trends
- See SKILL.md → Screening, Technical
