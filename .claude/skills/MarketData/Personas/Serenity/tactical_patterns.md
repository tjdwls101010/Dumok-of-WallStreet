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

### Healthcare / Pharma Sector (6 Heuristics)

1. **FDA Timeline as Capacity Constraint**: FDA approval timelines function like capacity constraints in manufacturing. Multi-year review processes (PDUFA dates, advisory committees, complete response letters) create bottleneck windows where approved products hold temporary monopoly. How to detect: track PDUFA target action dates, phase transition success rates by therapeutic area, and competitive pipeline density in the same indication. When multiple candidates target the same indication, the first-approved captures disproportionate market share — the approval timeline IS the constraint. Transferable principle: regulatory timelines create the same supply scarcity dynamics as physical capacity constraints. The 6-Criteria bottleneck scoring applies: supply concentration (few approved therapies), capacity constraints (fixed review timelines), long lead times (10-15 year development cycle, default value, agent may override with reasoning), and no quick substitutes (cannot accelerate FDA review).

2. **Patent Cliff as Reverse Supply Disruption**: When a blockbuster drug loses patent protection, the effect mirrors a supply disruption — but inverted. Rather than supply contracting, supply floods as biosimilars and generics enter. How to detect: patent expiration calendars (Orange Book for small molecule, Purple Book for biologics), ANDA/biosimilar application count per reference product, and historical brand-to-generic revenue conversion rate (typically 80-90% revenue loss within 12-18 months for small molecule, 30-50% over 3-5 years for biologics; default values, agent may override with reasoning). Transferable principle: supply disruptions can be demand-side (patent cliff removes pricing power) not just supply-side. The same bottleneck analysis framework applies in reverse — when a chokepoint dissolves, the incumbent's pricing power collapses at a rate determined by substitution complexity.

3. **CDMO Dependency as Single-Source Bottleneck**: Contract Development and Manufacturing Organizations (CDMOs) often represent hidden single-source dependencies for biotech companies. A clinical-stage company with one CDMO relationship has the same risk profile as a manufacturer dependent on a sole supplier. How to detect: 10-K risk factor analysis for manufacturing concentration, CDMO capacity utilization rates by modality (mAb, cell therapy, gene therapy), and tech transfer timelines (12-24 months typical for biologics; default value, agent may override with reasoning). When a CDMO is at >85% capacity utilization (default threshold, agent may override with reasoning), all its clients face supply risk simultaneously. Transferable principle: the 6-Criteria bottleneck scoring applies directly — supply concentration, capacity constraints, long lead times, no quick substitutes. CDMO dependency is the pharma equivalent of a single-source semiconductor foundry relationship.

4. **Binary Outcome Framework for Clinical-Stage Companies**: Pre-approval pharma companies have binary catalyst outcomes (approve/reject, succeed/fail) that make standard DCF inappropriate. How to detect: identify late-stage clinical data readouts, advisory committee dates, and PDUFA dates. Apply the Moonshot valuation framework (from methodology) when: (a) Phase 3 data demonstrates statistically significant efficacy, (b) no approved competitor exists in the indication, (c) market cap < peak sales potential multiplied by 3-5x revenue multiple (default range, agent may override with reasoning). Transferable principle: use the Trapped Asset / Moonshot valuation path, not standard DCF. The no-growth stress test applies with adjusted weight — for pre-revenue clinical companies, if the no-growth floor is <20% of market cap (default threshold, agent may override with reasoning), classify as speculative rather than investment-grade.

5. **PBM and Distribution Bottleneck**: Pharmacy Benefit Managers control drug distribution channels and create pricing bottlenecks between manufacturers and patients. Three PBMs control approximately 80% of US prescription volume, creating a distribution chokepoint independent of manufacturing. How to detect: PBM formulary inclusion/exclusion events, rebate structure changes, step-therapy requirements, and legislative actions targeting PBM transparency. When a product loses preferred formulary status, volume can decline 30-60% (default range, agent may override with reasoning) regardless of clinical superiority. Transferable principle: distribution channel concentration creates bottleneck dynamics even when manufacturing is not concentrated. This is an application of the bottleneck concept to demand access rather than supply — the chokepoint is between the product and the patient, not between raw materials and the factory.

6. **Biosimilar Competition Dynamics**: Biosimilar entry follows predictable patterns based on molecule complexity. Simple small-molecule generics face rapid commoditization; complex biologics face slow biosimilar adoption due to manufacturing difficulty and physician switching inertia. How to detect: molecule complexity classification (small molecule = rapid generic entry within 6 months, standard biologic = 3-5 year erosion, complex biologic such as cell/gene therapy = minimal biosimilar threat for 10+ years; default ranges, agent may override with reasoning), number of biosimilar applicants per reference product, and interchangeability designation status. Transferable principle: substitution barriers create natural moats — the harder a product is to replicate, the more durable the bottleneck. This maps directly to the "no quick substitutes" criterion in the 6-Criteria scoring. Molecule complexity is to pharma what process node advancement is to semiconductors — a structural barrier to competitive entry.

### Crypto / Stablecoin / Digital Finance Sector (5 Heuristics)

1. **On-Chain Metrics as Demand Proxy**: Active addresses, transaction volume, and TVL (Total Value Locked) serve as demand proxies analogous to physical throughput metrics in traditional supply chains. How to detect: compare on-chain activity trends (30-day moving average of active addresses, transaction count, fee revenue) versus token price — when on-chain activity accelerates while price is flat or declining, it signals potential mispricing. Conversely, price rising while on-chain activity declines signals speculative premium. Use a divergence threshold of >20% deviation between activity trend and price trend over 60 days (default values, agent may override with reasoning). Transferable principle: demand proxy validation applies — use on-chain data the same way you would use revenue acceleration, factory utilization, or order backlog growth. The underlying logic is identical: rising real usage that the market has not yet priced.

2. **TVL as Capacity Utilization**: For DeFi protocols, the TVL-to-market-cap ratio functions like capacity utilization for a factory. TVL represents actual capital deployed in the protocol (analogous to machines running), while market cap represents the market's valuation of that capacity. How to detect: TVL trending up while token price is flat = potential undervaluation (factory running fuller but stock not moving). TVL declining while price is rising = warning (factory emptying but stock climbing). A TVL/market-cap ratio above 1.0 suggests the protocol holds more real capital than the market values it at (default reference point, agent may override with reasoning). Transferable principle: capital efficiency metrics work the same way as in physical infrastructure — track the ratio of deployed capital to market valuation, just as you would track utilization rate versus enterprise value for a factory or data center.

3. **Regulatory Clarity as Institutional Entry Gate**: Crypto regulatory status creates a binary gate for institutional capital. Unlike traditional sectors where regulation constrains existing operations, in crypto, regulatory clarity ENABLES new capital entry. How to detect: track SEC enforcement actions, legislative progress (committee votes, floor votes, signing), and regulatory clarity events (ETF approvals, stablecoin frameworks, exchange licensing). Each clarity event removes an institutional compliance barrier. Transferable principle: regulatory uncertainty creates both risk and opportunity — clear regulation often triggers institutional entry that reprices the entire sector. This is a variant of the bottleneck concept: regulatory ambiguity is the chokepoint restricting capital flow into the sector. When the chokepoint clears, capital floods in the same way supply floods when a patent cliff arrives.

4. **Stablecoin Flow as Macro Liquidity Indicator**: Stablecoin minting and redemption patterns serve as leading indicators for crypto market liquidity, functioning as a crypto-native money supply metric. How to detect: track aggregate stablecoin supply changes (minting = new capital entering crypto ecosystem, redemption = capital exiting), exchange stablecoin inflows (dry powder accumulating = potential buying pressure), and stablecoin dominance ratio (stablecoin market cap as percentage of total crypto market cap — rising dominance signals risk-off positioning). A sustained stablecoin supply increase of >5% over 30 days without corresponding price appreciation signals accumulation (default threshold, agent may override with reasoning). Transferable principle: stablecoin flows are to crypto what net liquidity is to traditional markets — track the money supply proxy. The same macro-to-sector transmission logic (BM06 pattern) applies: liquidity expansion flows through the system with predictable lag.

5. **Exchange Flow as Institutional Positioning**: Net flows of assets into and out of exchanges signal accumulation versus distribution at scale, analogous to institutional holder quality analysis in traditional markets. How to detect: exchange reserve changes (declining reserves = assets moving to self-custody, typically accumulation signal; rising reserves = assets moving to exchanges, typically distribution or selling preparation), large transaction clustering (transactions above threshold relevant to the specific asset, typically >$1M equivalent; default value, agent may override with reasoning), and exchange-to-exchange flow patterns. Transferable principle: this is the crypto equivalent of tracking 13F institutional positioning — track where large holders are moving capital. The logic mirrors the Institutional Accumulation Detection heuristic from Macro/Cross-Cutting: when price declines but assets leave exchanges (self-custody increases), it signals conviction accumulation behind the price weakness.

### Utilities / Grid / Energy Infrastructure Sector (6 Heuristics)

1. **Rate Case as Capacity Constraint Equivalent**: Regulated utilities must obtain rate case approval from public utility commissions to recover infrastructure investment costs through customer rates. Rate case proceedings (typically 12-24 months from filing to final order; default range, agent may override with reasoning) function as capacity constraints on earnings growth — a utility cannot grow earnings faster than the regulatory process allows. How to detect: track filed versus pending versus approved rate cases, allowed ROE trends by jurisdiction (typical range 9-11%; default values, agent may override with reasoning), rate base growth trajectory, and regulatory lag (the gap between when investment occurs and when rates reflect it). Transferable principle: regulatory approval timelines create the same scarcity dynamics as physical capacity constraints. The bottleneck is not physical but procedural — the rate case queue is the equivalent of a fab construction timeline.

2. **Rate Cycle to Multiple Expansion Chain**: Interest rate cuts benefit utilities through a specific transmission chain: lower rates reduce debt servicing cost on variable-rate and refinancing debt, improving earnings; the yield spread between utility dividend yield and treasury yield widens, attracting yield-seeking capital; this drives multiple expansion independent of operational improvement. How to detect: track the Fed rate cycle position, utility sector average P/E versus 10-year treasury yield spread (historical average spread of 5-8x P/E points above treasury yield; default range, agent may override with reasoning), and historical utility sector total return during rate cut regimes. When the rate cut cycle begins with utilities trading below the historical P/E-to-yield spread, the setup is favorable. Transferable principle: this is BM06 (macro_to_sector_transmission) applied specifically to rate-sensitive sectors. The causal chain is: macro event (rate cut) -> financial statement impact (lower interest expense) -> valuation impact (multiple expansion) -> sector rotation (capital inflow from yield-seeking investors).

3. **Interconnection Queue as Lead Time Indicator**: The grid interconnection queue — the backlog of generation and storage projects waiting to connect to the transmission grid — creates natural bottlenecks for energy transition. Average interconnection wait times have extended to 4-6 years in many regions (default range, agent may override with reasoning), and withdrawal rates exceed 70% (default value, agent may override with reasoning) because projects cannot survive the wait. How to detect: interconnection queue length trends by region (ISO/RTO data), average wait times from application to commercial operation, withdrawal rates, and the ratio of queue capacity to actual grid capacity. Transferable principle: infrastructure lead times create the same bottleneck dynamics as semiconductor fab construction timelines. The interconnection queue IS the grid equivalent of the chip redesign timeline — a fixed physical and procedural constraint that no amount of capital can compress below a floor.

4. **Renewable Mandate as Demand Guarantee**: State-level renewable portfolio standards (RPS) and clean energy standards create legally mandated demand floors for clean energy capacity. These function as government-guaranteed demand, analogous to multi-year defense contracts. How to detect: RPS compliance timelines by state, gap between current renewable penetration and required percentage, penalty structures for non-compliance, and legislative risk of rollback. When the compliance gap is large and the deadline is near, procurement must accelerate regardless of market conditions. Transferable principle: government mandates create demand certainty analogous to large contract wins — they guarantee a minimum demand floor. This is the energy equivalent of defense spending being structural: individual project delays are noise, but the mandate trajectory is the signal.

5. **Grid Modernization as Bottleneck Migration**: As the grid modernizes to accommodate distributed generation, EV charging, and energy storage, bottlenecks migrate from generation capacity to transmission and distribution infrastructure. How to detect: T&D capital expenditure trends relative to generation capex (historically 40-60% of total utility capex, now rising; default range, agent may override with reasoning), power transformer lead times (currently 2-4 years for large power transformers; default range, agent may override with reasoning), grid reliability metrics (SAIDI/SAIFI trends), and distribution-level hosting capacity constraints. Transferable principle: bottleneck migration — as the system evolves, the chokepoint shifts from one layer to the next. This is the energy grid equivalent of the semiconductor Bottleneck Migration heuristic: resolving the generation constraint reveals the T&D constraint beneath it. Map the migration path to find the next investment layer.

6. **Capex Cascade from AI Demand to Grid Infrastructure**: Data center and AI compute demand is creating a capex cascade from hyperscalers to utilities to grid equipment manufacturers. The Temporal Capex Cascade pattern applies directly: hyperscaler capex announcements (Layer 1) flow to utility generation and interconnection contracts (Layer 2, 1-3 year lag), then to transformer, switchgear, and conductor manufacturers (Layer 3, 2-4 year lag). How to detect: utility capex guidance increases correlated with data center load growth, generation interconnection applications from technology companies, and order backlog growth at grid equipment manufacturers. Compare hyperscaler capex acceleration timing against utility capex guidance revisions — the lag reveals which layer is currently experiencing peak demand. Transferable principle: follow the capex cascade from demand source to supply infrastructure. The same multi-layer timing analysis that applies to semiconductor supply chains applies here — the investment opportunity is at the next layer down, where demand is coming but has not yet been fully priced.

### Space / Drone Sector (6 Heuristics)

1. **Government Contract as Revenue Visibility**: Space and drone companies with multi-year government contracts have unusually high revenue visibility compared to commercial-only peers. How to detect: contract backlog-to-annual-revenue ratio (>3x suggests multi-year visibility; default threshold, agent may override with reasoning), contract award cadence and win rate trends, recompete timing and incumbent advantage, and the mix of cost-plus versus fixed-price contracts (cost-plus provides revenue certainty, fixed-price provides margin upside). Transferable principle: government contracts function like long-term supply agreements — they provide demand certainty analogous to hyperscaler capacity commitments in the neocloud sector. Apply the same counterparty quality framework: government-backed revenue is Tier A counterparty, similar to Mag7-backed revenue in the tech supply chain.

2. **Technology Readiness Level (TRL) as Maturity Risk Framework**: The TRL 1-9 scale (from basic principles observed at TRL 1 to flight-proven at TRL 9) measures how far a technology is from operational deployment. Lower TRL = higher technical risk but potentially higher return if successful. How to detect: TRL classification from government contract filings (SBIR/STTR awards, OTA agreements), prototype versus production contract status, and transition from development to procurement budget line items. Companies with TRL 7+ technology on production contracts have fundamentally different risk profiles than TRL 4-5 companies on development contracts. Transferable principle: TRL is to space and defense what clinical trial phases are to pharma — a structured maturity framework that maps directly to risk/reward. TRL 1-3 is analogous to preclinical, TRL 4-6 to Phase 1-2, and TRL 7-9 to Phase 3 and approval. Apply the Binary Outcome Framework when a company has a single program at a critical TRL transition point.

3. **Launch Capacity as Physical Supply Concentration**: Global orbital launch capacity is concentrated among a small number of providers, creating a physical bottleneck for all space-based businesses — satellite operators, constellation builders, space stations, and in-space services all depend on the same constrained launch supply. How to detect: launch provider market share by mass-to-orbit, manifest backlog length and average wait time, price per kilogram to orbit trends by orbit type, and launch cadence growth rate versus demand growth rate. When demand for launches grows faster than cadence can expand, launch costs rise and timelines extend for all downstream space businesses. Transferable principle: launch capacity is a physical bottleneck where the 6-Criteria scoring applies directly — supply concentration (few qualified providers), capacity constraints (fixed pad and vehicle production rates), long lead times (vehicle production 12-24 months; default range, agent may override with reasoning), no quick substitutes (new launch vehicles require 5-10 years development). This is the space equivalent of advanced semiconductor packaging capacity.

4. **Spectrum Allocation as Regulatory Bottleneck**: Radio frequency spectrum is a finite resource allocated by national and international regulatory bodies. Spectrum rights create government-granted moats that function like patent protection — they grant exclusive access to a scarce resource for defined periods. How to detect: spectrum auction results and pricing trends, allocation timeline for new bands, interference constraints between adjacent allocations, and secondary market transaction values for spectrum licenses. Companies holding spectrum allocations suited to emerging use cases (LEO satellite broadband, drone command-and-control, direct-to-device) possess regulatory moats. Transferable principle: spectrum allocation is the communications equivalent of patent protection — a government-granted bottleneck that creates exclusivity. The same framework for analyzing patent cliffs applies: track when spectrum licenses expire or face reallocation risk, and assess the replacement cost of acquiring equivalent spectrum.

5. **Pre-Revenue Predominance and Valuation Discipline**: The space sector has a disproportionately high percentage of pre-revenue and early-revenue companies compared to most sectors. This requires heightened valuation discipline. How to detect: revenue existence check (zero revenue vs. early revenue vs. scaled revenue), commercial contract count versus government prototype-only funding, cash runway relative to milestones (does the company have sufficient cash to reach the next value-creating milestone without dilutive financing), and the ratio of announced partnerships to binding revenue contracts. Transferable principle: apply the no-growth stress test with increased default weight for space-sector pre-revenue companies. If the no-growth valuation floor is <20% of current market cap (default threshold, agent may override with reasoning), classify as speculative rather than investment-grade. This is the same discipline applied to clinical-stage pharma — pre-revenue companies require the Moonshot/Trapped Asset valuation path, with explicit probability weighting rather than DCF extrapolation.

6. **Constellation Scale as Network Effect Proxy**: Satellite constellations exhibit network effects — coverage, capacity, and service quality increase non-linearly with the number of operational satellites. How to detect: satellites deployed versus total planned constellation size, coverage percentage by target market geography, time to full operational capability, replenishment rate and satellite lifespan, and ground station infrastructure buildout progress. A constellation below minimum viable coverage (<30-40% of planned satellites; default threshold, agent may override with reasoning) cannot generate meaningful commercial revenue; above that threshold, each additional satellite adds disproportionate value. Transferable principle: constellation completion percentage functions like market penetration — early stages carry the highest binary risk (will the constellation reach minimum viable scale?) but also the highest potential asymmetric return. This maps to the Thesis Lifecycle phases: Enthusiasm (constellation announced), Consolidation (early launches), Prove It (minimum viable constellation operational), Maturation (full constellation, revenue scaling).

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
