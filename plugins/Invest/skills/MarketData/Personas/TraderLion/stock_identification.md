# TraderLion Stock Identification

## Overview

Systematic framework for identifying high-potential growth stocks through volume edges, Relative Strength analysis, catalyst identification, and actionable setup recognition. Each edge and setup includes precise detection conditions and interpretation guidelines. The more edges a stock exhibits simultaneously, the stronger the evidence for institutional accumulation and potential outperformance.

> "A proper setup is not necessarily special because of its ability to always produce strong returns consistently, but rather because it allows traders to manage risk tightly and logically."

---

## Volume Edges

Volume signatures indicate that a stock is undergoing a potential significant character change. A gap up on extremely large volume can lead to a strong momentum move and/or a long-term new trend.

### HVE — Highest Volume Ever

**Definition**: The trading day's volume exceeds the maximum volume ever recorded for the stock across its entire trading history.

**Detection Conditions**:
- Volume today > Maximum volume of all historical trading days
- Closing range >40%
- Stock is up on the day
- Minimum $3M dollar volume

**Interpretation**: Represents the most extreme institutional interest signal. When paired with a game-changing catalyst (first-time profitability, revolutionary product launch, industry-level regulatory change), this often marks the beginning of a new long-term trend. HVE is the strongest of the three HV edges.

**Caution**: Biotech stocks frequently appear on HVE screens due to drug trial news — these often gap up but go nowhere. Prefer stocks in other industries with catalysts that translate directly to sustained earnings and sales growth.

*Apply this framework independently to the current analysis target.*

---

### HVIPO — Highest Volume Since IPO Week

**Definition**: The trading day's volume exceeds the maximum volume recorded since the stock's IPO week (excluding the IPO week itself, which typically has anomalous volume).

**Detection Conditions**:
- Volume today > Maximum volume since IPO week
- Closing range >40%
- Stock is up on the day
- Minimum $3M dollar volume

**Interpretation**: Indicates that institutional interest has reached a level not seen since the initial public offering excitement. Particularly meaningful for stocks that have been public for at least 6-12 months, as it suggests a fundamental re-evaluation by the market. The longer the time since IPO, the more significant this signal becomes.

*Apply this framework independently to the current analysis target.*

---

### HV1 — Highest Volume in 1 Year

**Definition**: The trading day's volume exceeds the maximum volume recorded over the prior 250 trading days.

**Detection Conditions**:
- Volume today > Maximum volume of past 250 trading days
- Closing range >40%
- Stock is up on the day
- Minimum $3M dollar volume

**Interpretation**: The most frequently occurring HV edge. Signals that something has materially changed in how institutions view the stock. Most effective when associated with a game-changing catalyst. Look for follow-through — if the stock rises the next day on even higher volume, the character change is confirmed.

**Screen Logic**: Volume > Max(Volume, 250 days); DCR > 40%; % Change > 0; Dollar Volume > $3M

*Apply this framework independently to the current analysis target.*

---

### Increasing Average Volume

**Definition**: A sustained, step-function increase in the stock's average daily trading volume, typically coinciding with the early stages of a major move.

**Detection Conditions**:
- Average volume trending upward over weeks or months
- Step-change increases visible during base formation
- Further volume increase as stock begins its uptrend
- Large weekly volume spikes appearing with increasing frequency

**Interpretation**: Indicates the stock is becoming more liquid and attracting more institutional participants. Institutions managing billions need sufficient liquidity to build positions of tens of millions of dollars. As more institutions become involved, average daily volume increases and large weekly volume spikes appear. This change in supply/demand dynamics positively contributes to sustained price trends.

**Key Distinction from HV Edges**: HV edges are single-day events. Increasing Average Volume is a multi-week/month trend that provides context and confirmation.

See SKILL.md -> Technical, Screening

---

## Relative Strength Edge

### RS Line Interpretation

**Definition**: The Relative Strength (RS) line plots the ratio of the stock's price divided by an index (typically SPY). It is fundamentally different from the RSI (Relative Strength Index).

**Key Principle**: The absolute value of the RS line is not meaningful — the trend is what matters.
- Uptrend = outperformance versus the index
- Downtrend = underperformance versus the index

**Most Powerful Signal**: RS line making new highs before the stock's price makes new highs. This is a hallmark of future market leaders observed cycle after cycle in model book studies.

### RS Days

**Definition**: A day where the stock outperforms the market (positive relative performance), tracked especially during market corrections.

**Detection Criteria**:
- During a market correction, count the percentage of days the stock outperformed the market
- **Threshold**: >60% RS days during a correction indicates strong institutional accumulation

### RS Edge Detection — Five Manifestations

1. **RS Line Uptrend**: The RS line is trending upward and ideally making new highs, indicating persistent outperformance
2. **High RS Day Percentage**: On over 60% of days during a correction, the stock outperforms the market
3. **MA Maintenance**: The stock holds above key moving averages (21 EMA, 50 SMA) as the market undercuts them
4. **Divergent Higher Lows**: During the later part of a correction, the stock ignores market pullbacks and forms higher lows as the market forms lower lows
5. **Spring Release Recovery**: As the market moves up the right side after consolidating, the stock "jumps up" and recovers faster — as if pressure on a spring has been released

### MA Maintenance Criteria

The following moving averages are monitored for RS analysis:
- **10-day SMA**: Short-term trend; sustained trending stocks hold this during strong momentum phases
- **21-day EMA**: Key swing-trading support; holding this during corrections is a strong RS signal
- **50-day SMA**: Medium-term institutional reference; first major support level for position traders
- **65-day EMA**: Secondary medium-term reference
- **200-day SMA**: Long-term trend definition; price must be above this for a valid Stage 2 uptrend

**Strength Ranking**: A stock that holds the 21 EMA while the market undercuts the 50 SMA demonstrates exceptional relative strength and is a top candidate for leadership in the next uptrend.

### Three-Month Absolute Strength Rankings

During normal uptrends, use three-month RS rankings (percentile scale) to identify the strongest stocks. Stocks ranking >85th percentile in 3-month RS are primary candidates. Additionally, scan for stocks gapping up or moving higher on volume — any standout price action.

See SKILL.md -> Technical, Screening

---

## N-Factor Edge

### Game-Changing Catalyst Identification Framework

**Definition**: A fundamental catalyst that dramatically changes how institutions evaluate a company, leading to sustained accumulation and a significant stock advance. Derived from the "N" in O'Neil's CANSLIM methodology.

**Catalyst Categories**:

1. **Earnings/Revenue Surprise**: Company dramatically beats expectations and raises forward guidance. Forces institutions to re-model and accumulate. Most effective when EPS growth is triple-digit or shows acceleration.

2. **Industry-Level Regulatory Change**: Regulation changes that allow significant new development and growth across an entire sector. Focus on the strongest stock in the group, not laggards.

3. **Technology Breakthrough**: Advances creating entirely new industries (e.g., AI emergence driven by hardware and software advances). These transformative themes can produce multiple waves of opportunity over years.

4. **Revolutionary Product/Service**: Company reinvents itself through a new offering (e.g., Netflix's transition from mail-order DVDs to streaming to original content). Each reinvention can trigger a new multi-month uptrend.

**Validation Requirement**: The N-Factor must be directly leading to growth in earnings and sales. Talk of future potential without current financial impact (e.g., early autonomous driving narratives) does not qualify until institutions confirm with buying, visible in price and volume action.

**Key Principle**: However compelling the story, if institutional accumulation is not visible in the price action, do not act. Return when the market starts taking notice.

*Apply this framework independently to the current analysis target.*

---

## Setups

Setups are larger chart patterns that take weeks to form but yield trends that can last months. Each setup must provide a clearly defined entry level and a corresponding failure level for tight risk management.

### Launch Pad Setup

**Definition**: A bottoming pattern formed when all key moving averages converge and the stock begins to consolidate and shape up.

**Conditions for Identification**:
- **MA Convergence**: The 10-day SMA, 21-day EMA, 50-day SMA, 65-day EMA, and 200-day SMA all come together tightly beneath or at the price level
- **Group Confirmation**: Particularly significant when an entire group of stocks in the same theme forms launch pads simultaneously — this signals the beginning of a group move
- **Context**: Typically forms after significant market corrections and bear markets as stocks form bottoms
- **Price Action**: Stock begins to consolidate and trade tightly within the converging MAs

**Entry Approach**: Look for clear consolidation pivots and entry tactics within the launch pad that allow risk management against the converged MAs.

**Risk Management**: Stop loss placed below the cluster of converged moving averages. Because the MAs are converged, this provides a tight and logical stop level.

**Significance**: One of TraderLion's core setups. It identifies the transition point where a stock shifts from a bottoming/basing phase to the beginning of a new uptrend. Early recognition provides the lowest-risk entry point in the entire subsequent move.

*Apply this framework independently to the current analysis target.*

---

### Gapper Setup

**Definition**: A gap-up day on large volume with a catalyst, creating the foundation for a momentum continuation trade.

**Conditions for Identification**:
- **Gap-Up**: Stock opens significantly above prior day's close
- **Volume**: Trading on extremely high volume relative to average (ideally qualifying as HVE, HVIPO, or HV1)
- **Closing Range >50%**: The stock closes in the upper half of its daily range, indicating buyers maintained control throughout the session
- **Catalyst Present**: Must be accompanied by a game-changing fundamental catalyst (earnings surprise, new product, industry change)
- **Trend Context**: Preferably occurring within an existing uptrend or at the emergence from a base

**Multiple Gapper Protocol**:
- Focus on the **first one or two** gappers in a stock's trend
- Later in the trend, momentum deteriorates and gaps may be sold into as institutions take profit
- **Exception**: A later gapper is actionable if (a) it follows a significant base formation, or (b) the first gap occurred very low in a base structure

**Growth Confirmation**: Gappers are most powerful when accompanied by accelerating EPS growth. Track sequential quarterly EPS growth and EPS surprise percentages.

*Apply this framework independently to the current analysis target.*

---

### Base Breakout Setup (Including VCP)

**Definition**: A classic continuation setup where a stock breaks through a line of resistance after a multi-week consolidation within a longer-term uptrend.

**Conditions for Identification**:
- **Minimum Duration**: At least five weeks of consolidation
- **Trend Context**: Must be within the context of a longer-term uptrend (continuation, not reversal)
- **Tightening Action**: The healthiest bases tighten in price range and volume from left to right (this tightening pattern within a base is the core of the Volatility Contraction Pattern — VCP)
- **Volume Pattern**: Volume dries up during the base, then picks up sharply on the breakout — these are the "elephant tracks" of large institutions
- **Clean Resistance Break**: Price moves cleanly through a clearly defined line of horizontal resistance

**VCP Characteristics**:
- Successive contractions in price range within the base
- Each pullback within the base is shallower than the previous one
- Volume contracts with each successive contraction
- The final contraction is the tightest, creating the launch point

**Entry Considerations**:
- In recent markets, breakout failures are more common than in the 1990s
- **Alternative early entry**: Enter as the stock moves up toward the breakout level rather than waiting for the breach
- **Alternative pullback entry**: Enter when a stock stalls after breakout and falls back to a key MA (particularly the 21 EMA), then resets

**Focus Prioritization**: Like the gapper, focus on the first few bases in a stock's longer-term move to ensure remaining runway.

*Apply this framework independently to the current analysis target.*

---

## Closing Range and Bar Classification

### Daily Closing Range (DCR) Calculation

**Formula**: DCR = ((Close - Low) / (High - Low)) x 100

**Interpretation**:
- **DCR = 100%**: Stock closed at the high of the day — maximum buying pressure
- **DCR = 0%**: Stock closed at the low of the day — maximum selling pressure
- **DCR > 50%**: Closed in the upper half of the range — buyers controlled the session
- **DCR < 50%**: Closed in the lower half of the range — sellers controlled the session

### Constructive Bar Classification

A bar (daily candlestick) is classified as **constructive** when it demonstrates institutional accumulation:

**Constructive Characteristics**:
- High closing range (>50%, ideally >70%)
- Above-average volume supporting the advance
- Stock holds above key MAs (especially 21 EMA)
- Tight price range with close near the high (low-volatility accumulation)
- Gap-up days that hold their gains into the close
- On down market days: stock shows high DCR even if slightly red (relative strength)

### Non-Constructive Bar Classification

A bar is classified as **non-constructive** when it demonstrates institutional distribution:

**Non-Constructive Characteristics**:
- Low closing range (<40%)
- High volume accompanying price decline (distribution)
- Stock closes below key MAs
- Wide price range with close near the low (selling pressure)
- Gap-up days that fade and close in the lower portion of the range
- Climax-top behavior: acceleration upward on extreme volume after a major advance, then reversal to close red — signals end of the move

### Application

Track the ratio of constructive to non-constructive bars over rolling periods. A stock transitioning from predominantly constructive to non-constructive bars is undergoing a character change from accumulation to distribution, regardless of whether the overall price level still appears high.

See SKILL.md -> Technical, Screening

---

## Winning Characteristics Checklist

The complete checklist of characteristics that high-potential growth stocks exhibit. The more items checked, the higher the probability of a significant advance and the larger the warranted position size.

### Fundamental Characteristics

1. **Theme Alignment**: Stock is part of a current leading transformative or cyclical theme with visible group strength
2. **Innovation / N-Factor**: Company possesses a standout, game-changing competitive advantage driving institutional interest
3. **Quarterly EPS Growth >25% YoY**: Ideally triple-digit and accelerating across sequential quarters
4. **Quarterly Sales Growth >25% YoY**: Revenue growth confirming demand, especially critical for growth-at-all-cost companies
5. **EPS/Revenue Surprises**: Consistent positive surprises forcing institutional re-evaluation and accumulation
6. **Strong Forward Estimates**: Next-quarter EPS growth estimates also exceeding 30%, confirming sustainability

### Technical Characteristics

7. **HV Edge Present**: At least one of HVE, HVIPO, or HV1 observed on a catalyst day
8. **Increasing Average Volume**: Multi-week trend of rising average daily volume and large weekly volume spikes indicating growing institutional participation
9. **RS Line Uptrend / New Highs**: Relative Strength line trending upward, ideally making new highs before price — the hallmark of future leaders
10. **RS Days >60%**: During market corrections, the stock outperforms the market on more than 60% of trading days
11. **MA Respect and Maintenance**: Stock holds above key MAs (especially 21 EMA, 50 SMA) during market pullbacks while broader market undercuts
12. **Actionable Setup Formation**: Stock is forming or has completed one of the mastered setups (Launch Pad, Gapper, or Base Breakout) with a clearly defined entry and tight logical stop level

### Scoring Guidance

- **0-3 characteristics**: Low conviction — monitor only
- **4-6 characteristics**: Moderate conviction — base position sizing (10%)
- **7-9 characteristics**: High conviction — increased position sizing (12.5-17.5%)
- **10-12 characteristics**: Highest conviction — maximum position sizing (20%)

See SKILL.md -> Technical, Screening

---

## Head-to-Head Comparison Framework

When comparing two or more stocks (Type G query: "A vs B?"), use this structured 7-axis comparison to determine which candidate offers a superior risk-adjusted entry.

### Comparison Axes

| Axis | What to Evaluate | Scoring |
|------|-----------|---------|
| 1. Edge Count | Volume edge detection + RS ranking + earnings data | Count of edges present (0-6). More edges = stronger institutional conviction. |
| 2. RS Score | RS percentile ranking | Percentile ranking (0-99). Higher = stronger relative performance vs market. |
| 3. Winning Characteristics | See checklist above | Score out of 12. Higher = more complete growth stock profile. |
| 4. Setup Maturity | VCP quality assessment + base count | VCP quality (high/moderate/low) + base number (1st > 2nd > 3rd). Earlier bases with higher quality VCP preferred. |
| 5. Base Count & Risk | Base count analysis | 1st base = lowest risk, 4th+ = highest risk. Prefer stocks in earlier bases. |
| 6. Volume Grade | Volume accumulation/distribution grading | A+ through E. Higher grade = stronger accumulation evidence. |
| 7. Constructive Ratio | Closing range bar classification | Ratio of constructive bars over 20 days. >0.6 = healthy accumulation. |

### Comparison Output Format

Present as a side-by-side table:

| Axis | {SYMBOL_A} | {SYMBOL_B} | Winner |
|------|-----------|-----------|--------|
| Edge Count | {count_a} ({list}) | {count_b} ({list}) | {winner} |
| RS Score | {rs_a} | {rs_b} | {winner} |
| Winning Chars | {wc_a}/12 | {wc_b}/12 | {winner} |
| Setup Maturity | {setup_a} | {setup_b} | {winner} |
| Base Count | #{base_a} ({risk_a}) | #{base_b} ({risk_b}) | {winner} |
| Volume Grade | {vol_a} | {vol_b} | {winner} |
| Constructive Ratio | {cr_a} | {cr_b} | {winner} |
| **Overall** | **{wins_a}/7** | **{wins_b}/7** | **{overall}** |

### Tiebreaker Rules

When axis wins are tied:
1. **Edge Count wins**: More edges = more institutional evidence. This is the primary tiebreaker.
2. **RS Score wins**: Stronger relative strength during corrections predicts future leadership.
3. **Setup Maturity wins**: Earlier base with better pattern quality offers more remaining upside.

### Comparison Protocol

1. Obtain SNIPE pipeline analysis for each symbol (see SKILL.md for execution details)
2. Extract data for all 7 axes
3. Build the comparison table
4. Count axis wins per symbol
5. Apply tiebreaker if needed
6. State clear recommendation with rationale: "Based on {N}/7 axis wins, {SYMBOL} is the stronger S.N.I.P.E. candidate because [specific edge/RS/setup advantage]."

### Limitations

- **Theme alignment (TIGERS T)** and **N-Factor catalyst quality** require agent-level judgment and cannot be scored purely from scripts. State these assessments as supplementary context alongside the 7-axis comparison.
- If both stocks are in AVOID/MONITOR signal territory, comparison is academic — neither should be traded. State this explicitly.
- A stock winning 7/7 axes is rare. In practice, 4-5/7 wins with a clear edge count advantage is a strong differentiation.

*Apply this framework independently to the current analysis target.*
