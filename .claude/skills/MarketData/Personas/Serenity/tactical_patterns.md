# Tactical Patterns & Sector Heuristics

## Selective Loading Note

This file is loaded only for specific query types:
- Type D (Supply Chain & Bottleneck): Cross-sector patterns and sector heuristics
- Type F (Thematic Portfolio): Thesis lifecycle and contagion mapping
- Type A (Market & Macro): Only when crash/contagion analysis is needed
- Type C-3 (Discovery, thematic): Sector heuristics for the relevant sector

Do not load for simple Type B (Stock Diagnosis) queries unless the analysis reveals cross-sector bottleneck dynamics.

---

## Cross-Sector Pattern Library

Five transferable patterns that recur across semiconductors, defense, neoclouds, and macro analysis. Apply these as analytical lenses when mapping any supply chain.

### Pattern 1: Temporal Capex Cascade

**What it is**: Capital expenditure flows through supply chain layers with predictable time delays. Each layer experiences its demand surge 1-2 years after the layer above it.

**How to detect**: Track capex announcements at the top of the chain (hyperscalers). When top-layer capex accelerates, map downstream layers and estimate when demand reaches each layer based on production lead times.

**How to apply**: Identify which layer is currently experiencing peak demand. The NEXT layer down is where the asymmetric opportunity lies -- demand is coming but hasn't been priced in yet. The layer that peaked 2 years ago is where opportunities have likely passed.

**Transferable principle**: In any capital-intensive industry with multi-layer supply chains, investment opportunities cascade downward with time lag.

### Pattern 2: Recursive Bottleneck Discovery

**What it is**: When a bottleneck is found, that bottleneck itself has inputs that may be bottlenecked. The deeper bottleneck often has smaller market cap and higher asymmetry.

**How to detect**: After identifying a bottleneck (4+/6 scoring), immediately ask: "What does THIS company need to produce its output? Who supplies THAT?" Apply 5-Layer Mapping to the bottleneck itself.

**How to apply**: If the nested bottleneck scores 3+/6, it represents compounding pricing power -- the original bottleneck cannot resolve without the nested bottleneck resolving first. Prioritize the deepest bottleneck with the smallest market cap.

**Transferable principle**: In any constrained system, the binding constraint at the deepest level controls the entire chain's throughput.

### Pattern 3: Mag7-Customer Dependency

**What it is**: When a Mag7 company (or equivalent dominant buyer) becomes dependent on a small supplier, that supplier's growth trajectory explodes. The same question -- "Is the dominant buyer dependent on this company?" -- identifies opportunities across sectors.

**How to detect**: Search SEC filings and earnings transcripts for large-company mentions of small suppliers. Check if the small company appears in multiple Mag7 supply chains. The cross-chain analysis reveals shared dependencies.

**How to apply**: If a small-cap company appears in 3+ Mag7 supply chains as a supplier or single-source dependency, it likely controls a critical chokepoint. Evaluate whether the large buyers have alternatives.

**Transferable principle**: In any industry, when dominant buyers depend on small suppliers, the power dynamic inverts.

### Pattern 4: Second-Player Duopoly Valuation

**What it is**: In duopolies, the leader's valuation re-rating lifts the floor for the follower. The follower trades at a fraction of the leader but captures proportional upside when the market recognizes the duopoly.

**How to detect**: Identify markets where exactly 2 companies control >80% of supply. Check if the leader has recently re-rated (IPO, major contract, valuation milestone). The follower's valuation floor rises proportionally.

**How to apply**: Value the follower as a fraction of the leader's valuation, adjusted for market share difference. If the follower trades below this implied floor, it's mispriced.

**Transferable principle**: In any duopoly, the follower's floor price is set by the leader's valuation.

### Pattern 5: Cross-Domain Capacity Pivot

**What it is**: Companies with legacy physical infrastructure (factories, reactors, power capacity) can pivot to higher-value applications when a restructuring catalyst emerges. The physical assets are the same; the end market changes.

**How to detect**: Look for companies with: (a) substantial physical assets valued below replacement cost, (b) legacy business in declining market, (c) potential high-growth market that needs the same physical capability, (d) management or activist signaling a pivot.

**How to apply**: Use Physical Asset Replacement Valuation (from `valuation_fundamentals.md`). If replacement cost of assets >> current market cap, and a viable pivot market exists, the company is a restructuring candidate.

**Transferable principle**: Physical assets retain value across applications. The market often prices the legacy use case, not the pivot potential.

---

## Sector Heuristics

Reasoning patterns specific to each sector. These encode HOW to analyze, not WHAT to conclude about specific companies.

### Semiconductor Sector (7 Heuristics)

1. **BOM-Share Valuation**: For any chip program, calculate each supplier's BOM percentage x total program capex = addressable revenue. This quantifies the real revenue opportunity, not speculative TAM.

2. **Bottleneck Migration**: Bottlenecks migrate deeper into the supply chain over time as each constraint resolves and demand hits the next layer. Track which layer is currently constrained and predict the next migration based on capacity expansion timelines.

3. **Cost Insignificance = Overpay Willingness**: When a component represents <1% of total system cost but is required for deployment, the buyer will pay extreme premiums (10-100x) rather than delay deployment. Identify components where delay cost >> component cost.

4. **Chip Redesign Timeline**: Semiconductor redesign follows fixed physical steps: 12 months RTL design + 9-12 months physical design + 3-5 months fabrication + 6-9 months validation = 30-38 months minimum. Any claim of faster replacement violates engineering physics.

5. **ASIC-Agnostic Positioning**: In GPU vs custom ASIC debates, identify companies that win regardless of which architecture prevails. Companies supplying materials, packaging, or connectivity needed by ALL architectures have the safest positioning.

6. **Thermal Bottleneck Prediction**: As chip wattage increases, thermal management becomes binding. When GPU/accelerator TDP exceeds previous generation by >50%, search for thermal solution suppliers -- they become the next bottleneck.

7. **Material Spread Arbitrage**: When production of a critical material is concentrated in one region but consumption is in another, the spread between production cost and consumption-region price indicates structural margin opportunity for Western-positioned alternatives.

### Defense Sector (7 Heuristics)

1. **Military Operation -> BOM Decomposition**: When a military operation occurs, immediately decompose the weapons platforms being deployed into their bills of materials. Each component supplier becomes a potential investment.

2. **Export Control -> Sole Western Supplier**: When an export control is announced, immediately search for the sole Western alternative supplier for the restricted material. The Western alternative inherits monopoly pricing.

3. **Prime Contractor Co-Development De-Risks**: When a small defense company has a co-development partnership with a prime contractor (e.g., top 5 defense company), execution risk is substantially reduced.

4. **Government Balance Sheet Backing**: When a government takes an equity stake in a company or sector, it signals long-term commitment. Government-backed sectors rarely face permanent capital destruction.

5. **Defense Spending is Structural**: Individual contract cancellations or delays are noise. Total defense budget trajectory is the signal. Analyze at the macro budget level, not individual program level.

6. **Pre-Headline Pricing**: Defense ETFs and defense stocks often price in geopolitical events before headlines. If defense sector outperformance precedes a geopolitical event, institutional positioning is already complete.

7. **Multi-Model AI Consensus for Opaque Sectors**: For classified contracts or opaque sectors, cross-reference multiple AI models' assessments. When 3+ independent AI models converge on a probability range, it provides a useful baseline for sectors where traditional analysis has limited data.

### Neocloud Sector (7 Heuristics)

1. **Utilization > Power Cost by 30-70x**: Software utilization rate matters 30-70x more than cheap power for neocloud economics. A company with 90% utilization at expensive power beats 50% utilization at cheap power.

2. **Per-MW Normalized Economics**: Normalize all neocloud comparisons to Revenue/MW/Year, COGS/MW/Year, and Gross Profit/MW. This enables apples-to-apples comparison across different scales and hardware vintages.

3. **Dilution Quality Assessment**: Not all dilution is equal. 0% interest convertible notes at 30%+ premium to market = acceptable growth financing. 8%+ interest rate debt = toxic. Classify dilution as productive (funds revenue-generating assets) or destructive (funds operations or enriches management).

4. **Conditional Bull Case Detection**: Some companies may achieve dramatically higher margins than current operations suggest. Identify conditions under which a lower-tier company could achieve Tier 1 margins (e.g., bare-metal + software addition). Track progress toward those conditions.

5. **Composite Rating with Multiple Dimensions**: Simple buy/sell is insufficient for neoclouds. Rate across multiple dimensions: contract quality, margin quality, balance sheet, execution, and counterparty risk. A company can be Strong Buy on contracts but Avoid on balance sheet.

6. **Phase Progression Awareness**: Know which phase the sector is in (see Thesis Lifecycle below). Buying in Enthusiasm phase requires broad baskets; buying in Prove It phase requires surgical selection of survivors.

7. **Full Bear Case Before Any Bull Case**: Before building a bull thesis for any neocloud, MUST complete the 10-item bear case checklist (see `supply_chain_bottleneck.md`). Bull case is only valid after all 10 items are addressed.

### Macro/Cross-Cutting (6 Heuristics)

1. **Institutional Accumulation Detection**: When price declines but institutional ownership percentage increases, it signals dark pool accumulation. The institutions are buying what retail is selling. This is a positive divergence signal.

2. **Active Monitoring Over Passive Patience**: "Hold with conviction" is not passive waiting. It requires continuous monitoring of: momentum shifts, catalyst developments, IV changes, options flow, and institutional positioning changes. Inaction should be a deliberate decision, not default.

3. **Experience-Based Pattern Recognition**: Some trading signals come from extended observation (daily price + IV tracking over 12+ months) rather than from indicators. Acknowledge this limitation -- the agent cannot replicate multi-year observational intuition but can flag when standard indicators diverge.

4. **Asymmetric Hedge Construction**: When portfolio is concentrated in one theme, identify companies that benefit from the inverse scenario. Companies that profit from market volatility itself (market makers, exchanges) can hedge thematic concentration.

5. **Loss-Specific Lesson Extraction**: Every losing position must generate a specific, actionable lesson -- not generic "I should have been more careful." The lesson must change future behavior on a specific dimension (timing, sizing, due diligence process).

6. **Legislative-to-Bear-Case Mapping**: Specific legislation or regulation can eliminate specific bear case items. When a law addresses a bear case concern (e.g., accelerated permitting eliminates construction delay risk), update the bear case assessment accordingly.

---

## Thesis Lifecycle Tracker

Investment themes progress through predictable phases. Identifying the current phase determines the appropriate strategy.

### 5-Phase Progression Model

| Phase | Characteristics | Strategy |
|-------|----------------|----------|
| **1. Enthusiasm** | New theme discovered. Broad basket buying across all related names. High optimism, limited differentiation. | Broad exposure: buy the basket. Small positions across many names. |
| **2. Consolidation** | Leaders emerge. Margin and execution differences become visible. Capital concentrates into top names. | Narrow: sell laggards, increase leaders. Focus on margin quality. |
| **3. Prove It** | Sector-wide stress test (selloff, earnings miss, credit event). Only fundamentally strong companies survive. | Surgical: apply Three-Factor Crash Triage. Buy survivors, exit failures. |
| **4. Maturation** | Survivors are widely recognized. Analyst coverage increases. Valuations approach fair value. Sector becomes "priced in." | Reduce: take profits on fully valued names. Hold only highest conviction. |
| **5. Upstream Pivot** | Focus shifts from the matured sector to its upstream suppliers. The next bottleneck layer becomes the new frontier. | Rotate: apply Temporal Capex Cascade pattern to identify next layer. |

### Phase Detection Method

To determine current phase, check these indicators:
- **Enthusiasm -> Consolidation**: When gross margin dispersion across sector exceeds 20pp, consolidation has begun.
- **Consolidation -> Prove It**: When sector experiences 20%+ drawdown from peak, Prove It phase has arrived.
- **Prove It -> Maturation**: When surviving companies report 2+ quarters of execution on contracted revenue.
- **Maturation -> Upstream Pivot**: When analyst coverage of sector leaders reaches saturation (5+ analysts) AND sector P/E approaches historical mean.

### Application Rule
Always state the current phase assessment when analyzing a thematic sector. Phase determines position sizing, entry/exit timing, and which names to focus on.

---

## Contagion Isolation Mapping

When a sector-wide selloff occurs, not all companies are equally affected. This framework isolates company-specific risk exposure.

### 3 Risk Types to Isolate

1. **Counterparty Contagion**: Company's revenue depends on an at-risk counterparty. If that counterparty fails, the company faces a demand cliff. Map each company's revenue to counterparty tiers (Mag7 Fortress -> Enterprise -> VC-funded -> Startup).

2. **Credit Contagion**: Company's survival depends on access to credit markets. During stress, Grade C/D issuers lose refinancing ability. Map each company's debt maturity schedule against stress scenario timeline.

3. **Sentiment Contagion**: Company is sold purely because it's in the same sector, not because of fundamental exposure. These are the buying opportunities -- the company is being punished for sector membership, not company-specific risk.

### Isolation Process
1. For each company in the affected sector, classify its primary risk exposure into one of the 3 types above
2. Companies with only Sentiment Contagion (no counterparty or credit exposure) are the strongest buy candidates during the selloff
3. Companies with Counterparty Contagion require assessment of the counterparty's actual risk level
4. Companies with Credit Contagion require immediate assessment of cash runway and refinancing timeline

### Decision Matrix
| Risk Type | Action During Selloff |
|-----------|----------------------|
| Sentiment only | Accumulate aggressively |
| Counterparty (Tier A-B) | Hold, monitor counterparty |
| Counterparty (Tier C-D) | Reduce or exit |
| Credit (Grade A-B) | Hold with confidence |
| Credit (Grade C-D) | Exit immediately |
| Multiple risk types | Apply worst-case risk type |
