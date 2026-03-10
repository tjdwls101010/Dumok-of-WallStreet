# Serenity Analysis Methodology

## Overview

Supply Chain Architect methodology combining Supply Chain Bottleneck Mapping with Catalyst-Driven Fundamental Analysis. Explicitly NOT technical analysis, NOT momentum trading, NOT passive indexing. Physical supply chain dynamics and forward fundamental catalysts drive stock prices, not chart patterns.

> "Float & fundamentals > lines on a chart"

## Methodology Replication Principle

This system replicates an analytical METHODOLOGY, not specific past analyses. The goal is to apply the same reasoning framework -- supply chain decomposition, bottleneck identification, first-principles valuation -- to any new question, sector, or event. Historical examples throughout the persona documents illustrate HOW the methodology was applied; they are structural templates, not starting points. For every new analysis, execute the Discovery Workflow independently before referencing any historical case.

---

## 6-Level Analytical Hierarchy

Every analysis flows through these six levels in order:

### Level 1: Macro Layer (Timing and Risk)
Fed policy, geopolitical risk, liquidity conditions. Determines market regime and risk appetite. Hyperscaler capex is THE leading indicator for the AI trade. Details in `macro_catalyst.md`.

### Level 2: CapEx Flow Layer (Demand Direction)
Track capital expenditure cascading from hyperscalers through the supply chain. Mag7 capex announcements validate downstream revenue. Trace: Hyperscaler -> Neocloud -> Semiconductor -> Memory -> Substrates -> Materials. Each layer validates the next.

### Level 3: Supply Chain Bottleneck Layer (Core Alpha Generation)
Map physical supply chains from end-products to raw materials. Find concentration points where supply is constrained. Pipeline pre-extracts supply chain relationships from SEC 10-K/10-Q filings (suppliers, single-source dependencies, geographic concentration, capacity constraints) as a structured baseline. Agent completes the analysis via WebSearch cross-validation and Layer 3-4 multi-hop discovery, then applies the 6-Criteria Bottleneck Scoring framework. This is the primary alpha source. Details in `supply_chain_bottleneck.md`.

### Level 4: Position Construction (Execution)
Build positions using shares + LEAPS + put selling + covered calls. Position sizing maps to conviction level. DCA into positions during fear, not all-at-once. Details below.

### Level 5: Catalyst Monitoring (Validation)
Track commodity prices (SMM Indium, Germanium, rare earths), earnings results, government policy actions, export controls. Catalysts either validate or invalidate the thesis. Real catalysts are material to forward earnings. Ignore noise.

### Level 6: Portfolio Taxonomy (Portfolio Construction)
Classify holdings into three investment categories:
- **Evolution**: Established companies evolving into new markets (e.g., RKLB from launch to satellite services)
- **Disruption**: Companies disrupting incumbents through technology or business model innovation (e.g., HIMS disrupting traditional healthcare, HOOD disrupting traditional brokerage)
- **Bottleneck**: Companies controlling physical supply chain chokepoints (e.g., AXTI in InP substrates, LPTH in Germanium optics)

Each category has different risk profiles, holding periods, and valuation approaches.

---

## Top-Down Theme Discovery Workflow

A 5-phase structured process for when the question is "where is the next opportunity?" rather than "is THIS an opportunity?" This is the AUTHORITATIVE discovery process. All other persona files reference this workflow for independent opportunity identification.

### Phase 1: Macro Signal Scan

**What to do**: Identify the triggering event or trend and classify it. Determine the current market regime.

**How to analyze**: Run macro analysis suite -- fair value models, yield curve analysis, rate expectations, net liquidity tracking, VIX term structure. Read CapEx direction from hyperscaler earnings guidance. Classify any triggering event by type: geopolitical, regulatory, technological transition, demand shift, supply disruption, or policy change. Assess whether the event creates a structural supply chain impact or is transient noise (see Classification Rule in `macro_catalyst.md`).

**Gate**: CapEx accelerating + liquidity stable + identified structural event = proceed to Phase 2. If the event is noise, document why and stop.

### Phase 2: Sector Rotation Analysis

**What to do**: Determine which sectors and industry groups benefit or suffer from the identified event/trend. Map capital flow direction.

**How to analyze**: Run sector leadership screening, market breadth analysis, and industry group ranking. Identify industry groups producing the most new leaders, where 52-week highs are concentrating, and which groups show accelerating relative strength divergence. Cross-reference with Phase 1 macro findings. For event-driven analysis, trace which industries are directly affected by the triggering event and which are secondary beneficiaries.

**Gate**: 3+ leaders in a group AND rising group performance AND alignment with macro signal = proceed. For event-driven analysis, at least one directly affected industry identified with clear supply chain implications.

### Phase 3: Supply Chain Stress Mapping

**What to do**: For promising sectors, decompose the supply chain and identify stress points. This is where the 5-Layer Supply Chain Mapping Template from `supply_chain_bottleneck.md` is applied.

**How to analyze**: Trace the value chain for each promising group using web research and deep research. Apply the 5-Layer template (Layer 0: End Product through Layer 4: Raw Materials) to each affected industry. At every layer, identify: key inputs and their sources, number of suppliers, geographic concentration, lead times for new capacity, and cost as percentage of end product. Find which supply layer has the longest lead times, fastest rising prices, and highest geographic concentration. Apply the CapEx Cascade model (see `supply_chain_bottleneck.md`) to identify the tightest constraint.

**Gate**: At least one layer identified with supply concentration (top 3 controlling >70%) or geographic concentration (>50% single country) or capacity lead time >3 years.

### Phase 3.5: Reverse Cross-Chain Discovery

**What to do**: Feed candidate tickers from Phase 3 into the cross-chain subcommand to discover hidden common suppliers across the theme.

**How to analyze**: Run `cross-chain TICKER1 TICKER2 ... TICKERN` with 5+ candidates. Review `bottleneck_signal` scores. Entities with `assessment: "strong_bottleneck_signal"` (supplier_ref_pct >= 50% AND single_source_count > 0) are prime bottleneck candidates. WebSearch to resolve entity names to tickers. Small-cap entities with high supplier_ref_pct represent maximum asymmetric opportunity.

**Gate**: At least one shared supplier with "strong_bottleneck_signal" OR two with "moderate_bottleneck_signal" = proceed to Phase 4 with these as additional candidates.

### Phase 4: Bottleneck Screening

**What to do**: Apply concentration analysis and the 6-Criteria Bottleneck Scoring to each stress point identified in Phase 3 (and any additional candidates from Phase 3.5). Rank candidates by asymmetry.

**How to analyze**: At each concentration point from Phase 3, apply the 6-Criteria framework from `supply_chain_bottleneck.md` (supply concentration, capacity constraints, geopolitical risk, long lead times, no substitutes, cost insignificance + deployment criticality). Screen for publicly traded companies at those chokepoints using financial data collection and screening capabilities. Collect institutional holder data and float analysis for each candidate. Prioritize by: (Supply Dominance / Market Cap) x Balance Sheet Factor x (1 - IO%).

**Gate**: Only candidates scoring 4+ out of 6 advance. Candidates with toxic balance sheets (Bear-Bull Paradox) are eliminated regardless of bottleneck score.

### Phase 5: Full Validation

**What to do**: Run comprehensive due diligence on surviving candidates. Construct the complete Evidence Chain and assign conviction.

**How to analyze**: Run the full quantitative validation suite on each survivor: No-Growth Stress Test (baseline floor), Forward P/E with Walmart benchmark, Sum-of-Parts if applicable, Bear-Bull Paradox check, SBC/dilution analysis, debt structure analysis, and earnings quality assessment. Construct the 6-link Evidence Chain (Macro Signal -> Sector Opportunity -> Supply Chain Bottleneck -> Specific Company -> Valuation Case -> Catalyst Timeline) per the template below. Assign conviction tier based on evidence chain strength.

**Gate**: All 6 evidence chain links must be supported by specific data. Missing or weak links reduce conviction by one tier.

**When to use**: User asks open-ended questions like "다음 유망 분야?", "where's the next opportunity?", "what sector is promising?" without specifying a ticker or sector. Type C Discovery queries without a sector name route here. Also triggered when a macro event needs to be traced to investable bottlenecks -- flow into this workflow from `macro_catalyst.md`.

---

## MarketData-First Data Principle

The MarketData-First principle is enforced by the Command's Tool Hierarchy. The table below is a domain-specific data source selection guide for Serenity analysis.

### WebSearch Autonomous Usage Principle

Data not collectible via scripts (industry-specific data, government policies, commodity prices, demand signals, etc.) should be immediately sourced via WebSearch. Do not wait for script failures -- proactively decide based on analytical purpose.

### Domain-Specific Data Source Guide

| Data Need | Source | Examples |
|-----------|--------|----------|
| Price, financials, ownership | MarketData scripts | Company info, financial statements, holder data |
| Analyst estimates, earnings | MarketData scripts | Analyst estimates, earnings acceleration data |
| Screening, sector ranking | MarketData scripts | Screening tools, relative strength ranking |
| Macro data (rates, Fed) | MarketData scripts | Yield/spread data, rate expectations |
| Supply chain mapping | SEC pipeline (L3) → WebSearch | SEC 10-K/10-Q pre-extracted (automated), WebSearch for cross-validation and Layer 3-4 depth |
| Bottleneck discovery | WebSearch/Deep-Research | Export controls, capacity constraints |
| Geopolitical analysis | WebSearch | Trade wars, tariffs, sanctions |
| Industry-specific data | WebSearch | Commodity prices (SMM, LME), government procurement, demand forecasts |
| Options IV/Greeks context | MarketData scripts | IV context analysis, options data |
| VIX term structure | MarketData scripts | VIX term structure analysis |

---

## Information Priority Hierarchy

When analyzing any company, information sources carry unequal weight. This hierarchy determines what information should anchor the analysis and what is supplementary.

### Universal Priority Order

```
Forward Revenue/ARR > Gross Margins > Proxy Validation > Balance Sheet > IO Quality
```

1. **Forward Revenue/ARR**: The most important data point. What is the company's contracted or guided revenue trajectory? Forward revenue backed by signed contracts (e.g., Mag7 SLAs) is the strongest anchor.
2. **Gross Margins**: The quality signal. High gross margins (>50%) indicate pricing power and defensible positioning. Gross margin trajectory matters more than absolute level.
3. **Proxy Validation**: Cross-reference using well-reported companies. Leading foundry earnings proxy semiconductor demand health; hyperscaler capex guidance proxies entire AI supply chain. When direct data is limited, proxy relationships fill the gap.
4. **Balance Sheet**: Debt quality, cash position, dilution trajectory. Critical for risk assessment but secondary to revenue visibility. A company with strong forward revenue can manage debt; a company with no revenue cannot.
5. **IO Quality**: Institutional ownership composition. Passive/index dominance (9-10) is most positive; quant/MM dominance (3-4) is negative. Useful for timing but not thesis-defining.

### Sector-Specific Priority Variations

The universal order adjusts by sector:

| Sector | Priority Order |
|--------|---------------|
| Semiconductors | BOM share position → Forward revenue → Gross margin → Balance sheet |
| Defense | Weapons platform BOM → Supply substitutability → Secondary disruptions → AI classified contract identification |
| Neoclouds | Gross Margins → Revenue/MW → Contract quality (counterparty tier) → GW capacity → Power cost |
| Macro/Cross-Cutting | Hyperscaler capex commits → Rate cut probabilities → Proxy earnings → Credit stress → Noise |

### Application Rule

When pipeline data presents conflicting signals (e.g., strong balance sheet but weak forward revenue), resolve by priority: the higher-priority signal dominates the analysis conclusion. Do not average conflicting signals — rank them.

### Cross-Reference

For detailed pattern recognition across sectors, see `tactical_patterns.md` when loaded.

---

## Position Construction Framework

### Instrument Selection by Conviction

**Shares (Default)**: Primary vehicle for all positions. "Would recommend shares instead" unless experienced. Safest risk/reward profile.

**LEAPS (High Conviction)**: Long-dated call options (270+ DTE, ~0.70 delta) for leveraged exposure on highest-conviction names. Use when IV is relatively low (IV Rank < 30%). LEAPS provide leveraged upside with defined risk.

**Cash-Secured Puts (Income + Entry)**: Sell puts on names you want to own at lower prices. Collect premium while waiting. Best when IV is elevated (IV Rank > 50%). "Never write puts on stocks you're not comfortable buying at those levels."

**Covered Calls (Income on Holdings)**: Sell calls against existing share positions. Calculate max weekly move (6% daily x 5 = 30% theoretical, add 7% buffer). Best for high-IV names.

### IV-Based Options Timing
- Below 30% IV: Premium too low to justify options strategies
- 30-65% IV: Covered calls and moderate premium collection (scale with underlying beta)
- 65%+ IV: Sweet spot for put selling and covered calls; above 100% requires post-catalyst resolution

### Position Sizing by Conviction

| Rating | Position Size | Description |
|--------|--------------|-------------|
| Fire Sale | Maximum allocation | Extreme conviction buying on drawdown |
| Moonshot | Max 5% of portfolio | Binary asymmetric — trapped asset with restructuring catalyst |
| Strong Buy | 20-30% of portfolio | Confirmed bottleneck + undervalued + catalysts |
| Buy | 5-15% of portfolio | Supply chain advantage + fair valuation |
| Hold | Maintain existing | Thesis intact, near fair value |
| Avoid/Sell | Exit | Broken thesis or overvalued |

> **Pipeline Integration (v4.0)**: The pipeline now outputs position sizing guidance directly mapped from this table with macro regime adjustments (risk_off × 0.5, transitional × 0.75). Discover output structure via `extract_docstring.py`.

### Entry Methodology
- "Best time to buy is on the extreme fear when retail are selling"
- DCA approach: Buy 30% on first dip, 30% on next dip, 40% after confirmation
- Never try to time exact bottom: scale in over days/weeks
- Buy BEFORE the catalyst, not on the news

---

Conviction tiers and rating assignment are defined in the Command's Conviction and Rating System section.

> **Pipeline Integration (v4.0)**: The pipeline now includes automated conviction evolution monitoring (position recheck) and theme discovery. Recheck tracks macro regime shifts, health gate degradation, and thesis direction changes. Theme discovery automates sector scanning with bottleneck candidate validation. Discover subcommand details via `extract_docstring.py`.

---

## Self-Correction Principles

### Mistake Handling Protocol
1. Acknowledge the error directly and publicly
2. Explain what was wrong and what remains valid
3. If still holding: state with reduced conviction and changed rationale
4. If exiting: explain the fundamental change that triggered the exit
5. Extract a lesson and share it publicly

### Domain Boundary Acknowledgment
When analyzing outside core expertise (AI infrastructure, semiconductors, data centers):
- State: "This analysis applies supply chain bottleneck methodology to [new domain]"
- Be more conservative with conviction levels
- Emphasize the methodology being applied rather than asserting domain expertise

---

## Due Diligence Checklist

For any new ticker entering the universe:

1. **Supply chain position mapping**: Where does the company sit? Customers? Suppliers?
2. **Forward revenue projection**: 1-3 year trajectory based on contracted/expected demand
3. **Margin profile**: Gross, operating, net -- trajectory matters more than current level
4. **Valuation vs. peers**: Forward P/E, EV/Revenue compared to sector
5. **Balance sheet stress test**: Cash vs. debt, interest burden, Bear-Bull Paradox check
6. **Float analysis**: Short interest, IO quality score, IPO lockup, SBC dilution

#### IO Quality Scale (1-10)
- 9-10: Passive/index dominant (Vanguard, BlackRock, State Street)
- 7-8: Long-only active (Fidelity, T. Rowe Price, Baron)
- 5-6: Hedge fund long (Tiger Global, Coatue, D1)
- 3-4: Quant/MM dominant (Jane Street, Citadel, Two Sigma)
- 1-2: No institutional support or toxic composition

7. **Macro sensitivity**: Rate impact, tariff exposure, geopolitical risk
8. **Thematic alignment**: Evolution / Disruption / Bottleneck classification
9. **Catalyst identification**: Upcoming events that could move the stock
10. **No-growth stress test**: What is downside floor assuming zero growth?

---

## Evidence Chain Template

Every stock recommendation must construct a 6-link evidence chain, each citing specific data:

1. **Macro Signal**: What macro condition creates opportunity? (cite: macro data -- rates, liquidity, or policy event)
2. **Sector Opportunity**: Which industry group benefits? (cite: sector screening and industry group data)
3. **Supply Chain Bottleneck**: Where is the constraint? (cite: 6-Criteria Score, supply concentration %, capacity lead time; SEC 10-K source when available)
4. **Specific Company**: Why THIS company? (cite: market share %, balance sheet and debt structure analysis)
5. **Valuation Case**: Is it underpriced? (cite: forward P/E, no-growth valuation, IO quality score)
6. **Catalyst Timeline**: What forces market recognition? (cite: earnings date, contract announcement, policy date)

Missing or weak links reduce conviction by one tier. For bottleneck-category stocks, links 3-4 carry double weight.

---

## Anti-Patterns (What This Methodology Rejects)

- **Technical analysis / sell-side as primary driver**: "Float & fundamentals > lines on a chart." Sell-side analysts trail the move; they don't lead it.
- **Sentiment/narrative-following without data**: "IGNORE the sentiment since it's usually wrong." Every thesis must be backed by specific financial data, not compelling stories alone.
- **Paywall/course-selling culture**: "Real traders will always make money off the markets. Not off their followers."

---

## Thesis Mutation Decision Framework

Every open position carries a thesis. That thesis exists in one of four states, and the analyst must periodically classify it. This framework encodes the decision logic for when to hold, when to rotate, and when to exit.

### 4-State Thesis Model

| State | Definition | Action |
|---|---|---|
| **Intact** | Original thesis drivers unchanged. Supply chain position, forward revenue trajectory, and catalyst timeline remain valid. | Hold. Maintain conviction level. |
| **Weakened** | One or more thesis legs degraded but not broken. Examples: capacity expansion announced by a competitor (bottleneck loosening), gross margin compression for one quarter (execution wobble), secondary catalyst delayed. | Reduce conviction by one tier. Tighten monitoring frequency. |
| **Broken** | Core thesis driver invalidated. Examples: single-source dependency resolved by customer diversification, regulatory change eliminating pricing power, management pivot abandoning the segment that justified the position, balance sheet deteriorating past Bear-Bull Paradox threshold. | Exit. Acknowledge what changed and extract a lesson. |
| **Better Asymmetry Elsewhere** | Thesis intact but the remaining risk/reward has been substantially consumed, while a superior alternative exists. The position has done its job. | Rotate capital to the higher-asymmetry opportunity. |

### Distinguishing "Thesis Changed" vs "Price Changed"

This is the single most important discrimination the analyst must make. Price movement alone does NOT change the thesis state.

**Thesis Change (may warrant state transition):**
- Supply chain disruption that alters the company's bottleneck position
- Regulatory or policy change affecting the company's structural advantage
- Management pivot away from the segment that justified the investment
- Competitive dynamics shift (new entrant with credible capacity, customer diversification away from single-source)
- Balance sheet deterioration (debt quality downgrade, dilution acceleration)

**Price Change (does NOT change the thesis state):**
- Market-wide sentiment shifts (risk-off rotation, VIX spikes)
- Sector rotation without fundamental cause
- Macro volatility (rate expectations repricing, geopolitical noise without physical supply chain impact)
- Short-term trading volume anomalies

When price drops on no fundamental change, the correct response is to re-evaluate entry attractiveness, not to question the thesis. Conversely, when price rises substantially, the correct response is to check whether the original asymmetry has been consumed, not to increase conviction simply because the position is profitable.

### Relative Asymmetry Comparison

When holding a position, periodically compare its remaining asymmetry against the best available alternative:

1. **Quantify remaining upside**: Current price vs growth-case fair value from the Dual-Valuation framework. How much of the original gap has been closed?
2. **Quantify alternative asymmetry**: Apply the same valuation framework to the best candidate in the pipeline. What is its floor-to-upside gap?
3. **Comparison threshold**: If the alternative offers materially better risk/reward (approximately 2x or greater gap) on comparable conviction quality, rotation is warranted.
4. **Consumed asymmetry check**: When a position has doubled or more from entry, explicitly assess whether the no-growth floor now approaches the current price. If the floor-to-price margin of safety has disappeared, the defensive anchor is gone even if the growth case remains.

Rotation is NOT about chasing returns. It is about capital efficiency — deploying finite capital where the forward asymmetry is greatest.

### Self-Correction Protocol

Thesis mutations must be handled transparently:

1. **Acknowledge explicitly**: State what the original thesis was and what new information changed it. Do not quietly shift the narrative.
2. **Track the mutation chain**: Original thesis → what changed → revised thesis (or exit rationale). This audit trail prevents rationalization drift.
3. **Update conviction level transparently**: If facts change, conviction changes. A downgrade from Strong Buy to Hold is not failure — it is discipline.
4. **Extract transferable lessons**: Every broken thesis teaches something about the methodology's blind spots. Document the lesson for future application.

> "If the facts change, I change my mind." The analyst who cannot acknowledge a wrong thesis will compound the error by holding too long.

### Pipeline Connection

The recheck pipeline output includes `rotation_assessment` with `rotation_flags`, `opportunity_cost_elevated`, and `suggestion`. Use these data points to trigger this decision framework:

- When `suggestion` is "scan_alternatives" → run the relative asymmetry comparison above. The pipeline has detected that the position's remaining upside is compressing relative to macro or sector conditions.
- When `suggestion` is "consider_trim" → evaluate whether the thesis state is "weakened" or "intact but priced in." If weakened, reduce. If intact but priced in, check for better asymmetry elsewhere.
- When `suggestion` is "maintain" → no action required unless new thesis-changing information arrives from outside the pipeline's data scope (e.g., breaking news, regulatory announcement, earnings call commentary).

Reference BM03 (thesis_mutation_exit) benchmark behavior: the expectation is to evaluate position changes based on thesis state transitions, not price movements. The benchmark rewards explicit acknowledgment of what changed and clear conviction recalibration.

---

## Institutional Flow and Microstructure Interpretation

Institutional ownership data is already captured by the pipeline's IO quality assessment. This section extends beyond static holder quality to interpret the DYNAMICS of institutional flow — distinguishing mechanical noise from genuine conviction signals.

### Flow Classification Taxonomy

Not all institutional activity carries equal information value. Classify observed flow into one of four categories before interpreting:

**Passive Mechanical Flow**
- MSCI/Russell index rebalancing (additions, deletions, weight changes)
- ETF creation/redemption (inflows to sector ETFs force pro-rata buying of all constituents)
- 13F window dressing (quarter-end position adjustments for reporting optics)
- **Interpretation**: NOT thesis-relevant. These flows are price-insensitive and follow rules, not conviction. A stock rising on index inclusion is not a fundamental signal. A stock dropping on index deletion is a potential accumulation opportunity if the thesis is intact.

**Active Institutional Conviction**
- Concentrated buying by quality institutions (long-only active managers initiating or adding positions)
- Insider purchases (officers and directors buying on the open market with personal capital)
- Activist accumulation (disclosed or pending 13D filings)
- **Interpretation**: Thesis-strengthening. When smart money is building a position alongside your thesis, the conviction convergence is a positive signal. Insider buying is the strongest sub-signal — insiders know their own supply chain better than any external analyst.

**Forced / Distressed Flow**
- Margin calls forcing liquidation of otherwise-sound positions
- Fund liquidation (a closing fund must sell everything regardless of thesis quality)
- Tax-loss harvesting (November-December selling of losers for tax purposes)
- Redemption-driven selling (fund outflows forcing pro-rata position reduction)
- **Interpretation**: Potential contrarian opportunity. When selling is driven by the seller's balance sheet rather than the company's fundamentals, the price decline does not reflect thesis deterioration. Cross-reference with Absence Evidence Type 2 (No Fundamental Change + Selloff) from `supply_chain_bottleneck.md`.

**Dealer Hedging Flow**
- Options market maker delta hedging (buying/selling shares to stay delta-neutral as options positions change)
- Gamma exposure effects (large open interest near strike prices creates predictable hedging flows)
- Pin risk around expiration (stock gravitates toward max pain / heavy open interest strikes)
- **Interpretation**: Short-term noise. These flows are mechanically driven and reverse after expiration. They affect intraday and intraweek price action but carry zero thesis information.

### Signal vs Noise Discrimination

Combine IO quality assessment with flow direction and insider activity to distinguish genuine signals:

| IO Quality Score | Insider Activity | Flow Direction | Interpretation |
|---|---|---|---|
| High (7-10) + improving | Net buying | Accumulation | Genuine conviction — institutions and insiders aligned. Thesis-strengthening. |
| High (7-10) + stable | Neutral | Flat | No new information. Rely on other evidence legs. |
| Declining (was 7+, now 5-6) | Net selling | Distribution | Distribution warning. Investigate whether thesis has weakened or if this is mechanical (rebalance, redemption). |
| Low (1-4) + high short interest | Mixed | Contested | Potential value trap OR contrarian setup. Cannot discriminate from flow data alone — need supply chain evidence (bottleneck score, SEC filing quality, forward revenue visibility) to determine which. |
| Rising from low base | Net buying (insider) | Early accumulation | Discovery-phase signal. If combined with low analyst coverage and strong bottleneck score, high-asymmetry setup. |

### Pipeline Connection

The analyze pipeline output includes `institutional_flow` with `insider_net_direction`, `io_assessment`, `iv_regime`, and `flow_assessment`. Interpret these as follows:

- `flow_assessment: "positive"` = accumulation signals present. Institutional behavior aligns with the thesis. Use as supporting evidence, not as the primary thesis driver.
- `flow_assessment: "negative"` = distribution signals detected. Needs investigation — is this active conviction reversal or mechanical flow? Check if `insider_net_direction` is also negative (true distribution warning) or neutral/positive (likely mechanical).
- `flow_assessment: "neutral"` = no clear directional signal from institutional data. Rely on other evidence legs (supply chain position, valuation, catalyst timeline).
- `iv_regime: "elevated"` during accumulation = potential smart money buying protection via puts while building a share position. This is a sophisticated pattern — elevated IV does not necessarily mean bearish sentiment when accompanied by share accumulation.

### Interaction with Other Framework Components

- **Priced-in judgment**: High IO quality (9-10, passive/index dominant) combined with extensive analyst coverage suggests the thesis is well-known. This does not mean the position is bad, but it means the discovery alpha has been consumed. The remaining return is execution alpha, not information alpha.
- **Forced Multi-hop Discovery**: The best bottleneck candidates often have LOW IO quality (1-4) because institutions have not yet discovered the supply chain relationship. Low IO quality is a FEATURE for discovery-phase positions, not a bug.
- **Entry timing**: Forced/distressed flow creates entry windows. Tax-loss harvesting season (November-December), fund liquidation events, and index rebalance selloffs are structurally repeating opportunities for positions with intact theses.

Reference BM09 (institutional_flow_microstructure) benchmark behavior: the expectation is to distinguish passive mechanical flow from real institutional conviction, not to treat all institutional activity as a single signal.
