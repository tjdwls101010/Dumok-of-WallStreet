# TraderLion Stock Identification

## Overview

Systematic framework for identifying high-potential growth stocks through volume edges, Relative Strength analysis, catalyst identification, and actionable setup recognition. The more edges a stock exhibits simultaneously, the stronger the evidence for institutional accumulation.

> "A proper setup is not necessarily special because of its ability to always produce strong returns consistently, but rather because it allows traders to manage risk tightly and logically."

---

## TIGERS Stock Selection Framework

TIGERS is TraderLion's adaptation of CANSLIM — six dimensions evaluated when selecting stocks. A stock meeting multiple TIGERS criteria simultaneously presents the highest probability opportunity.

### T — Theme

The stock rides a strong growth theme. **Transformative** themes (technology-driven, long-lasting — e.g. AI, semiconductors) produce longer, more meaningful opportunities than **Cyclical** ones (macro-driven, shorter-lived). Stocks move in groups; identify the top 1-3 stocks within the current transformative theme. Maximum potential requires three-wave alignment: healthy market + disruptive theme + best-positioned company.

### I — Innovation

The company has a standout product or service separating it from peers — unique value proposition leading to rapid growth and market share capture. Try to experience the product firsthand. **Critical rule**: if price action does not confirm the thesis, look elsewhere.

### G — Growth

Minimum quarterly growth: **>25% YoY** in earnings or sales. Preferred: triple-digit and/or **accelerating** across sequential quarters (e.g. 25% → 40% → 80%). Revenue growth is critical for growth-at-all-cost companies. Track the sequential trend of quarterly EPS and sales growth rates.

### E — Edges

Accumulation must show up in the charts. Stock should trend orderly when market is strong, fight downtrends, bounce quickly after corrections, gap up on earnings, and break out from base patterns. See Volume Edges, RS Edge, and N-Factor sections below.

### R — Relative Strength

Stock should be close to the top of 3-month RS leaderboards, continuing to trend and obey moving averages. See RS Edge section below.

### S — Setup

Wait until the stock develops a mastered setup (Launch Pad, Gapper, Base Breakout). Specialize in 1-3 setups rather than trying to learn everything.

---

## Volume Edges

Volume signatures indicate potential significant character change. The pipeline detects all HV edges; use these interpretation guides for analysis context.

### HVE — Highest Volume Ever

Volume exceeds the all-time maximum. The strongest HV edge. When paired with a game-changing catalyst, often marks the beginning of a new long-term trend. **Follow-through confirmation**: stock rises next day on even higher volume. **Caution**: Biotech HVEs on drug trial news often go nowhere — prefer stocks with catalysts that translate to sustained earnings growth.

### HVIPO — Highest Volume Since IPO Week

Volume exceeds the post-IPO-week maximum. Particularly meaningful for stocks public 6-12+ months, as it suggests fundamental re-evaluation. The longer since IPO, the more significant. **Follow-through confirmation**: next-day rise on even higher volume confirms character change.

### HV1 — Highest Volume in 1 Year

Volume exceeds the 250-day maximum. Most frequently occurring HV edge. Signals material change in institutional view. Most effective with a game-changing catalyst. Look for next-day follow-through on higher volume.

### Increasing Average Volume

Sustained step-function increase in average daily volume over weeks/months, typically coinciding with early stages of a major move. Indicates growing institutional participation and improving liquidity. **Key distinction from HV edges**: HV edges are single-day events; Increasing Average Volume is a multi-week trend providing context and confirmation.

See SKILL.md → Technical, Screening

---

## Relative Strength Edge

### RS Line Interpretation

The RS line plots stock price / index price ratio. The **trend** matters, not the absolute value. **Most powerful signal**: RS line making new highs before price makes new highs — a hallmark of future market leaders.

### RS Days

Days where the stock outperforms the market during corrections. **Threshold**: >60% RS days during a correction indicates strong institutional accumulation.

### Five Manifestations

1. **RS Line Uptrend**: Trending upward, ideally making new highs
2. **High RS Day %**: >60% outperformance days during corrections
3. **MA Maintenance**: Holds above key MAs (21 EMA, 50 SMA) while market undercuts them
4. **Divergent Higher Lows**: Forms higher lows while market forms lower lows during corrections
5. **Spring Release Recovery**: Recovers faster than market after consolidation — compressed spring effect

**RS Timing Principle**: Stocks showing RS during the **last third** of a correction are most likely to become next-uptrend leaders.

### Three-Month Absolute Strength Rankings

During normal uptrends, stocks ranking >85th percentile in 3-month RS are primary candidates. Additionally scan for stocks gapping up or moving higher on volume.

See SKILL.md → Technical, Screening

---

## N-Factor Edge

A fundamental catalyst that dramatically changes institutional evaluation, leading to sustained accumulation. Derived from O'Neil's CANSLIM "N."

1. **Earnings/Revenue Surprise**: Dramatically beats expectations, raises guidance. Most effective with triple-digit or accelerating EPS growth.
2. **Industry-Level Regulatory Change**: Regulation enabling significant new sector growth. Focus on the strongest stock in the group.
3. **Technology Breakthrough**: Advances creating entirely new industries (e.g. AI). Can produce multiple opportunity waves over years.
4. **Revolutionary Product/Service**: Company reinvents itself through new offering (e.g. Netflix DVD → streaming → originals).

**Validation**: N-Factor must lead to actual earnings/sales growth. However compelling the story, if institutional accumulation is not visible in price action, do not act.

---

## Setups

Larger chart patterns taking weeks to form, yielding trends lasting months. Each must provide a defined entry level and failure level for tight risk management.

### Launch Pad Setup

Bottoming pattern where all key MAs (10 SMA, 21 EMA, 50 SMA, 65 EMA, 200 SMA) converge tightly beneath or at price level. Particularly significant when an entire group forms launch pads simultaneously. Typically forms after significant market corrections. **Entry**: consolidation pivots within the launch pad. **Stop**: below the converged MA cluster (tight and logical). Identifies the transition from basing to new uptrend — lowest-risk entry in the subsequent move.

### Gapper Setup

Gap-up day on large volume with a catalyst, creating momentum continuation opportunity. Requires: significant gap up, extremely high volume (ideally HVE/HVIPO/HV1), closing range >50%, game-changing catalyst, preferably within existing uptrend or base emergence. **Focus on first one or two gappers** in a trend — later gaps deteriorate as institutions profit-take. Most powerful with accelerating EPS growth.

### Base Breakout Setup

Classic continuation: stock breaks resistance after multi-week consolidation within a longer-term uptrend. Minimum 5 weeks consolidation. Healthiest bases tighten in price range and volume from left to right. Volume dries up during base, picks up on breakout. The pipeline detects VCP characteristics (successive contractions, shallower pullbacks, contracting volume). **Alternative entries**: enter as stock moves toward breakout level, or on pullback to 21 EMA after breakout. Focus on first few bases for remaining runway.

### Base Count and Quality Degradation

| Base # | Quality | Probability Assessment |
|---|---|---|
| 1st | Highest | Full sizing, broadest stop tolerance |
| 2nd | High | Full sizing, standard stops |
| 3rd | Moderate | 75% sizing, tighter stops |
| 4th | Low | Half sizing max, very tight stops |
| 5th+ | Lowest | Monitor only or minimal test position |

Reset to 1st base after price breaks below 200 SMA and forms new base.

---

## Stock Character Assessment

Pipeline's `stock_profile` output provides: ADR%, clean/choppy classification, character grade, liquidity tier, and MA respect analysis. Use these outputs to set expectations for position management — clean trenders are easier to manage within the TraderLion framework; higher ADR% (3-5%+) enables powerful moves in weeks. A character change (large volume increase, newfound MA respect) often signals institutional recalibration after a catalyst.

---

## Special Patterns

Pipeline's `special_pattern_flags` detects these patterns automatically. Use the interpretations below for analysis context.

### Positive Expectation Breaker

Stock in a structurally bearish configuration (below key MAs, lower highs, near breakdown) that instead breaks out to the upside. Represents hidden institutional accumulation that trapped shorts. One of the most powerful continuation signals across 120+ annotated charts spanning 2004-2024.

### No Follow-Through Down

Bearish event (gap down, support break, distribution day) that fails to produce sustained downside within 1-3 days. Institutional buyers absorbed the selling pressure — a demand signal. ~30% of annotated winning charts display this at least once during base formation or early trend.

### Inside Day / Tight Day / Double Inside Day

Pipeline's `entry_readiness` detects these volatility contraction patterns. Direction of subsequent expansion has high continuation probability. Highest value near key MAs or base pivots on low volume. Double inside day is particularly powerful.

See SKILL.md → Technical, Screening

---

## Opportunity Zones

Three lifecycle zones where stocks commonly double and triple.

### IPO Boom Zone

Right after IPO — short-lived and volatile. Lock-up restrictions create high trend potential; post-lock-up insider selling leads to drawdown and institutional due diligence phase.

### Growth Transition Zone

After initial IPO drawdown, stock establishes range and begins new uptrend. Institutions have researched and begun accumulating. Watch for: IPOs 6-12 months old, leading theme, first profitability, 200 SMA appearing. Look for base breakouts.

### New Momentum Zone

Can occur multiple times. After extended decline/basing, stock forms base and begins new Stage 2 uptrend. Most powerful with catalyst and leading theme.

---

## Winning Characteristics Scoring

Pipeline's `_count_winning_characteristics` evaluates the 12-item checklist (6 fundamental + 6 technical). Use the score for position sizing guidance:

- **0-3**: Low conviction — monitor only
- **4-6**: Moderate conviction — base position sizing (10%)
- **7-9**: High conviction — increased sizing (12.5-17.5%)
- **10-12**: Highest conviction — maximum sizing (20%)

---

## Head-to-Head Comparison Framework

For Type G queries ("A vs B?"), use this 7-axis comparison:

| Axis | What to Evaluate | Scoring |
|------|-----------|---------|
| 1. Edge Count | Volume edges + RS + earnings | Count (0-6) |
| 2. RS Score | RS percentile ranking | Percentile (0-99) |
| 3. Winning Chars | Checklist score | Out of 12 |
| 4. Setup Maturity | VCP quality + base count | Quality + base # |
| 5. Base Count & Risk | Base count analysis | 1st=lowest risk |
| 6. Volume Grade | Accumulation/distribution | A+ through E |
| 7. Constructive Ratio | Closing range bar classification | >0.6 = healthy |

### Tiebreaker Rules

When axis wins are tied: (1) Edge Count wins — primary tiebreaker, (2) RS Score wins, (3) Setup Maturity wins.

### Protocol

1. Obtain SNIPE pipeline analysis for each symbol
2. Build side-by-side comparison table with Winner column
3. Count axis wins; apply tiebreaker if needed
4. State recommendation: "Based on {N}/7 axis wins, {SYMBOL} is the stronger S.N.I.P.E. candidate because [specific advantage]."

**Limitations**: Theme alignment (TIGERS T) and N-Factor quality require agent-level judgment — state as supplementary context. If both stocks are in AVOID/MONITOR territory, neither should be traded.

*Apply this framework independently to the current analysis target.*
