# Supply Chain Bottleneck Analysis

## Independent Discovery First

When given a new sector, event, or query to analyze, the analyst MUST independently map the supply chain and identify bottlenecks BEFORE referencing any historical examples in this document. The Discovery Workflow (see Scenario-Driven Discovery Protocol below and Top-Down Theme Discovery Workflow in `methodology.md`) is the authoritative process. Historical case studies exist to demonstrate HOW the methodology was applied, not WHAT tickers to start with.

---

## 5-Layer Supply Chain Mapping Template

```
Layer 0: End Product / End User
Layer 1: System Integrator / OEM
Layer 2: Major Components (BOM breakdown with % of total cost)
Layer 3: Sub-Components / Specialized Materials
Layer 4: Raw Materials / Feedstock

Per-layer questions:
- How many suppliers? (1 = monopoly, 2-3 = oligopoly, 4+ = competitive)
- Lead time for new capacity? (months/years)
- Geographic concentration? (single country = geopolitical risk)
- Cost as % of end product? (low cost + high criticality = pricing power)
- Substitutes available? (no substitutes = true bottleneck)
```

### 5-Step Mapping Process

**Step 1: Identify End-Product Driving a Macro Trend.** Start with a confirmed demand trend backed by capex commitments or government funding, not speculation.

**Step 2: Trace the Bill of Materials (BOM).** Break down the end-product into physical components with percentage allocations. The BOM reveals where the money actually flows.

**Step 3: Find Concentration Points.** At each BOM layer, identify suppliers and supply concentration. A monopoly or tight oligopoly at any layer is a potential chokepoint.

**Step 4: Assess Pricing Power at the Chokepoint.** Can the supplier raise prices without losing customers? Would a 10x price increase still be economically rational for the buyer because deployment delay costs orders of magnitude more?

**Step 5: Determine if the Bottleneck is Priced In.** Check market cap against implied revenue from supply chain position. If small-cap bottleneck in a multi-trillion dollar industry, likely underpriced. If institutions have accumulated and analyst coverage is extensive, the opportunity may have passed.

**Key Principle:** "Follow the money flow down." Start from the demand source and trace layer by layer. The opportunity is at the narrowest point of the funnel. Bottlenecks migrate over time as each constraint resolves and demand hits the next one.

---

## Bottleneck 6-Criteria Scoring Framework

This is the SINGLE authoritative scoring framework. Apply these six criteria to every concentration point.

| # | Criterion | Pass (1) | Fail (0) |
|---|-----------|----------|----------|
| 1 | Supply concentration | Top 3 control >70% market share | Fragmented (>10 competitors, none >20%) |
| 2 | Capacity constraints | >3 years to add meaningful capacity | New capacity within 1 year |
| 3 | Geopolitical risk | >50% production in single country/region | Geographically diversified |
| 4 | Long lead times | Lead times measured in months/years | Can be resolved quickly on demand surge |
| 5 | No substitutes | No viable substitute within 2 years | Multiple alternatives available today |
| 6 | Cost insignificance + deployment criticality | Small fraction of system cost but required for deployment; customers cannot reduce consumption | Customers can substitute, delay, or reduce |

**Scoring threshold: 4+ out of 6 = investable bottleneck.**

Criterion 6 is the most asymmetric type: a $100 substrate in a $20B deployment can command $10,000 if supply is constrained, because delaying the deployment costs far more.

---

## Thematic Frameworks

### Quantitative Classification Thresholds

- Full-Stack vs Bare-Metal: Full-Stack = >60% gross margin + own software layer; Bare-Metal = <50% gross margin, rent capacity only
- Bottleneck Classification: Monopoly (>70% share), Oligopoly (40-70%), Competitive (<40%)
- Catalyst Materiality: Mega (>$10B impact), Material ($2-10B), Noise (<$2B)

### Neocloud Infrastructure

AI-focused cloud/datacenter companies providing GPU compute when hyperscalers exceed internal capacity. Classified into a 4-Tier system based on margin quality and execution risk:

**4-Tier Classification:**
- **Tier 1: Full-Stack** (60-75% GM). Own orchestration software + hardware infrastructure. Highest margin quality and customer stickiness. Example: NBIS.
- **Tier 2: GPU Cloud** (40-60% GM). Managed GPU-as-a-service with some software layer but not full vertical integration. May operate on leased or owned infrastructure. Example: CIFR (GPU cloud segment).
- **Tier 3: Colocation / Bare-Metal** (30-45% GM). Infrastructure-only, rent capacity without meaningful software differentiation. Commodity-like pricing risk. Example: IREN.
- **Tier 4: BTC Miner Pivoting** (GM volatile, highest execution risk). Crypto miners repurposing existing power/cooling infrastructure for AI compute. Unproven unit economics in AI, legacy mining operations may subsidize or drag. Execution risk is the dominant variable.

**Cross-Tier Comparison Rule:** When comparing companies across tiers, ALWAYS explicitly state the tier difference and explain why the comparison is still valid (e.g., shared customer base, same datacenter market). Do NOT compare Tier 1 and Tier 3 companies on gross margin without noting the structural difference in business model. A Tier 1 at 65% GM and a Tier 3 at 35% GM are not "comparable" without this context.

**How to apply:** First classify company into tier. Evaluate gross margins as primary differentiator -- "Gross Margins > GW capacity." Assess contract quality (confirmed Mag7 contracts vs speculative pipeline). Check "Prove It" phase status: has it demonstrated execution on contracted revenue?

**Phase Progression Model:** Enthusiasm (broad basket buying) -> Consolidation (capital concentrates into leaders) -> Conviction Crystallization (single-name positions) -> "Prove It" Execution (revenue delivery validation) -> Maturation (focus shifts to upstream bottlenecks). Apply this progression pattern to any emerging sector.

**GPU Depreciation Risk Checklist (Mandatory Bear-Case for All Neoclouds):**
Every neocloud analysis MUST address GPU depreciation as a structural risk:
- FASB accounting allows 3-5 year useful life for GPUs, but effective technological useful life is 18-24 months due to rapid generational improvements (e.g., H100 -> B200 -> next gen).
- Depreciation burden typically consumes 30-40% of gross margin for capital-heavy neocloud operators.
- Verification step: Check 10-K for stated useful life assumptions and depreciation schedule. If stated useful life exceeds 3 years for GPUs, flag as aggressive accounting.
- Bear-case question: "If GPU fleet requires full replacement every 2 years, what is the sustainable margin after depreciation?"
- Tier 1 (Full-Stack) companies can partially offset through software margins; Tier 3-4 companies bear the full depreciation impact on already-thin margins.

**Counterparty Risk Hierarchy (Mandatory for Contracted Revenue Claims):**
When a neocloud claims contracted or committed revenue, classify the counterparty:
- **Tier A: Mag7 Fortress** (AAPL, MSFT, GOOG, AMZN, META, NVDA, TSLA). Near-zero default risk. Multi-year contracts are bankable.
- **Tier B: Enterprise Cloud / Large Tech** (ORCL, CRM, IBM, SAP, large enterprise customers). Low default risk but contracts may have flexibility clauses.
- **Tier C: VC-Funded AI Companies** (well-funded AI startups with $500M+ raised). Moderate risk -- funding runway matters. Verify latest funding round and burn rate.
- **Tier D: Startup / Early-Stage** (seed to Series B AI companies, small crypto firms). High default risk. Revenue from Tier D counterparties should be heavily discounted in valuation.
- **Rule:** When evaluating contracted revenue, always identify counterparty tier. "$2B contracted revenue" from Tier A is fundamentally different from "$2B contracted revenue" from Tier C/D mix.

**CRWV as Negative Benchmark:**
Use CRWV (CrowdStrike rival/crypto-adjacent infrastructure) as a standing reference point for what "bad" looks like in neocloud balance sheets: toxic debt structure (8-10%+ implied interest rate), serial dilution history, pre-revenue inflation. When analyzing any neocloud, compare its debt quality grade and dilution metrics against CRWV as the lower bound. If a company's metrics approach CRWV levels, apply Bear-Bull Paradox filter from `valuation_fundamentals.md`.

### Memory Supercycle

AI demand creates sustained price hikes for DRAM/NAND, breaking the traditional boom/bust cycle. When forward P/Es compress to single digits despite massive revenue growth, the market is pricing cyclical reversion that may not come.

**How to apply:** Monitor DRAM spot, NAND contract, HBM pricing. Compare forward P/Es to growth rates. Calculate gap between street estimates and actual pricing -- the excess flows directly to bottom line. Use the Walmart benchmark: memory companies growing 100%+ Y/Y at lower P/Es than a slow-growth retailer = strong mispricing signal.

**Legacy Void sub-framework:** When major producers pivot to HBM/enterprise SSD, they abandon legacy products. Remaining suppliers inherit premium pricing power -- "selling water in a desert." Map which products are abandoned, find remaining suppliers, assess pricing power.

### InP Chokepoint

Supply bottleneck from limited Indium Phosphide substrate supply constraining photonics/optical interconnect production. A "bottleneck within a bottleneck."

**How to apply:** Identify the constraining material. Map who controls global supply (Herfindahl-style: how many companies control 80%+?). Assess geopolitical risk from export controls. Calculate cost insignificance ratio (component cost vs total system cost). Evaluate historical analogies for price response magnitude. Find the publicly traded company with most leverage at the chokepoint. Reapply this lens to any new technology transition.

### CapEx Funnel / Mag7

Capital expenditure flow from the seven largest tech companies down through the supply chain. The master demand signal for the entire AI investment ecosystem.

**How to apply:** Monitor quarterly capex guidance. Calculate total combined capex and Y/Y change. Trace layer by layer: Hyperscaler -> Neocloud -> Semiconductor -> Memory -> Substrates -> Materials -> Energy. Identify which layer sees the largest % demand increase relative to existing capacity. "If Mag7 is dependent on a company, the company will blow away expectations quarter after quarter."

### Bottleneck Investing (7-Step Framework)

Serenity's signature framework for finding smallest public companies controlling critical supply chain bottlenecks.

1. Identify a physical material constraint in a high-growth supply chain
2. Map who controls supply (company names, market shares, geographic locations)
3. Assess Western vs geopolitical supply chain concentration
4. Find the smallest company with most leverage at the bottleneck
5. Verify balance sheet health (avoid Bear-Bull Paradox situations)
6. Check if markets have priced in the bottleneck (analyst coverage, IO%, recent price moves)
7. Enter when the supply shock has not been recognized yet

**Self-awareness:** "Not every bottleneck provides a great investment opportunity." Discipline in applying ALL seven steps prevents chasing already-priced-in opportunities.

### Full-Stack vs Bare Metal

Evaluate vertical integration value in any industry. Calculate normalized gross margins per-unit (e.g., per-MW for Neoclouds). Assess replicability of software vs infrastructure layers. Monitor for convergence: bare-metal players building software could achieve highest margins of all.

### Additional Frameworks (Brief Reference)

- **Material vs Immaterial**: Filter signal from noise. Multi-billion contracts = material. FDA warning letters, conference attendance = immaterial. Buy on material catalysts before recognition.
- **TACO/Valuation Gift**: Tariff anxiety, geopolitical noise, and sentiment-driven selloffs create buying opportunities when fundamentals are unchanged. If no contracts cancelled and no supply chains physically disrupted, selling is emotional, not fundamental.
- **Bear-Bull Paradox**: Great tech does not overcome terrible financials. Full framework in `valuation_fundamentals.md` Filter 5.
- **Legacy Void**: When majors abandon market segments, remaining suppliers inherit premium pricing. Map abandoned products, find remaining suppliers.
- **Follow the Leader**: When one stock rallies on fundamentals, identify peer companies in same supply chain tier that have not yet moved. Laggards often follow.
- **Tactical Entry (Tax Harvesting / Made in America)**: In Nov-Dec, screen for tax-loss-harvested stocks with intact fundamentals. Year-round, screen for US-domiciled sole producers in strategic sectors benefiting from tariffs and export controls.

---

## BOM Analysis Methodology

When constructing a Bill of Materials breakdown:
1. Start from total system cost (GPU cluster cost, drone unit cost, etc.)
2. Break into major categories first (memory, logic, packaging, optics, power)
3. Estimate percentage allocation from industry reports and earnings disclosures
4. Within each category, identify specific suppliers and their market share
5. Cross-check across multiple sources -- earnings transcripts, teardown analyses, and industry reports should roughly agree
6. Flag any component where a single supplier exceeds 40% market share as requiring deeper bottleneck analysis

---

## Commodity Price as Leading Indicator

Track commodity prices as early warning signals for bottleneck formation:

- **SMM (Shanghai Metal Markets)**: Indium, Germanium, Gallium, rare earth real-time pricing
- **Asian Metal**: Supplementary pricing data for critical materials
- **Industry sources**: TrendForce, Yole, LightCounting for semiconductor-specific pricing

**Historical analogies for bottleneck pricing magnitude:**
- Neon Gas: ~2000% price spike during Russia-Ukraine supply disruption
- Dysprosium: ~2300% spike during rare earth export restrictions
- These provide order-of-magnitude reference points for how far prices can move when supply is truly constrained

When raw material prices hit all-time highs weekly (e.g., Indium during InP substrate shortage), the bottleneck is actively tightening and downstream pricing power is materializing.

---

## Scenario-Driven Discovery Protocol

This protocol is the step-by-step process for independently discovering bottleneck opportunities from any new event or query. It operationalizes the Top-Down Theme Discovery Workflow from `methodology.md` for scenario-specific analysis.

### Step-by-Step Discovery Framework

**Step 1: Event Classification.** Identify the macro event or trend and classify it into one of the 6 Scenario Categories below. Determine: What changed? Is the change structural (persists for months/years) or transient (resolves in weeks)? What physical supply chains are directly affected?

**Step 2: Impact Mapping.** Trace which industries and supply chains are directly affected by the classified event. Use web research and deep research to identify: which end-products depend on the disrupted supply, which geographic regions are impacted, and which companies have publicly disclosed exposure. Cast a wide net at this stage -- do not prematurely narrow to familiar sectors.

**Step 3: Supply Chain Decomposition.** For each affected industry, apply the 5-Layer Supply Chain Mapping Template (defined above in this document). At each layer, identify key inputs, suppliers, processes, geographic concentration, and lead times.

**Step 4: Concentration Point Detection.** At each layer, identify supply concentration using the per-layer questions from the 5-Layer template above. Validate with financial data collection capabilities.

**Step 5: Bottleneck Scoring.** Apply the 6-Criteria Bottleneck Scoring Framework (defined above). Only concentration points scoring 4+ out of 6 qualify as investable. Document the score and evidence for each criterion.

**Step 6: Validation.** Cross-check surviving bottleneck candidates with fundamental analysis: debt structure analysis, dilution assessment, earnings quality, No-Growth Stress Test, and Bear-Bull Paradox filter. Companies with toxic balance sheets are eliminated regardless of bottleneck score. Construct the 6-link Evidence Chain from `methodology.md` for each validated candidate.

### 5-Element Scenario Structure

Every scenario requires: (1) Triggering Event -- specific, falsifiable, observable; (2) Probability Assessment -- High >60%, Medium 30-60%, Low <30%; (3) Timeline -- Immediate <3mo, Near-term 3-12mo, Medium-term 1-3yr; (4) Physical Supply Chain Disruption Mechanism -- which factories stop, routes blocked, materials unavailable; (5) Measurable Invalidation Criteria -- specific evidence that would disprove the scenario.

### 6 Scenario Categories

1. **Export Ban / Sanctions** (Highest conviction): Binary, immediate supply removal. Research focus: Western alternative supplier, capacity, scale timeline.
2. **Military Conflict / Defense Escalation**: Inelastic government-funded demand. Research focus: Defense platform BOM, consumed materials, budget allocation.
3. **Technology Transition**: New tech creates demand existing supply cannot meet. Research focus: New materials needed, capacity gap.
4. **Regulatory Shift**: Compliance requirements benefit pre-positioned companies. Research focus: Which companies already meet new standards.
5. **Natural Disaster / Infrastructure Failure**: Physical disruption of concentrated production. Research focus: Single points of failure, alternative suppliers.
6. **Currency / Capital Flow Shift**: Gradual but persistent effects on sourcing decisions. Research focus: Exporter competitiveness, reshoring acceleration. 6-18 month supply chain lag.

### Research-to-Bottleneck Mapping (6-Stage Funnel)

**Stage 1 (Extract):** Pull structured data from research -- company names, tickers, market share, capacity, geography, customers, substitutes.

**Stage 2 (Layer Assignment):** Assign each element to supply chain layer (Layer 0: raw materials through Layer 4: end products).

**Stage 3 (Concentration Scoring):** Calculate HHI or top-3 concentration ratio. Flag geographic concentration (single country) and facility concentration (single factory).

**Stage 4 (6-Criteria Scoring):** Apply the bottleneck scoring table above. Threshold: 4+ out of 6 = investable.

**Stage 5 (Company Prioritization):** Rank by: smallest market cap (most asymmetric), highest supply chain dominance, healthiest balance sheet, lowest IO% (most discovery upside). Priority = (Supply Dominance / Market Cap) x Balance Sheet Factor x (1 - IO%).

**Stage 6 (Quantitative Validation):** Pass through full MarketData validation before conviction assignment. Companies failing quantitative gate are downgraded regardless of bottleneck score.

### Tool Sequencing for Scenario Discovery

Sequential Thinking (construct scenario) -> Deep Research (discover supply chains) -> WebSearch (supplement with real-time data) -> MarketData scripts (quantitative validation) -> Sequential Thinking (synthesize). Do NOT reverse this order. The scenario must drive the research.

### Common Mapping Pitfalls

- **Anchoring on familiar tickers**: When given a new event, do NOT start with known tickers from historical cases. Execute Steps 1-4 above to discover candidates independently. Historical cases are structural templates, not starting points.
- **Narrative is not bottleneck**: Compelling story does not create investable bottleneck without PHYSICAL concentration at a specific layer
- **Ignoring balance sheet**: Perfect bottleneck position with terrible financials = uninvestable (Bear-Bull Paradox)
- **Not checking if priced in**: If stock moved 300%+ in 6 months with rising analyst coverage and IO%, the discovery window has closed
- **Single-source research bias**: Cross-reference across queries; check data currency against recent policy changes

---

## Cross-Chain Analysis

### How Chains Interact
Bottlenecks in one chain amplify constraints in another. Foundry capacity constraints simultaneously limit GPU AND memory production. InP shortage constrains both optical interconnects AND photonic ICs. Critical mineral shortage may affect both defense optics AND semiconductor applications.

### The Capex Cascade
Primary cross-chain flow: Hyperscaler capex -> validates neocloud revenue -> drives semiconductor orders -> drives memory demand -> drives substrate/materials demand -> drives energy demand. Each link validates the next.

### Proxy Relationships
Use well-reported chains to validate less transparent ones: leading foundry earnings proxy for semiconductor demand health, major memory producer pricing proxies for cycle positioning, optical component orders proxy for interconnect demand, hyperscaler capex guidance proxies for entire AI supply chain.

### Application Steps
1. Map each chain independently
2. Identify shared nodes (companies/materials appearing in multiple chains)
3. Assess whether bottlenecks in one chain create demand pressure on another
4. Use proxy data from well-reported chains to validate assumptions about less transparent chains
5. When multiple chains simultaneously validate the same bottleneck, conviction increases

### When to Update a Map
Update when: a major player enters or exits a layer, export controls change material availability, new technology creates a substitute, capacity expansions resolve a constraint, or pricing data indicates bottleneck migration.

---

## Appendix: Historical Case Studies (Reference Only)

> **HARD GUARDRAIL**: These cases are structural templates showing HOW the methodology was applied. They are NOT starting points for new analysis. For every new query, the Discovery Workflow MUST be executed independently and completed BEFORE any historical case is referenced. Defaulting to these tickers on a new query is an anti-pattern.

### AXTI / InP (Optical Interconnect Bottleneck)
*Historical Application:* Traced optical interconnect chain backward to substrates. InP identified as binding constraint when China-Japan export controls disrupted Sumitomo, creating effective monopoly for AXTI (~40% global share). Cost insignificance: hyperscaler would pay 100x substrate price rather than delay $20B TPU deployment. Scored 5/6. *Apply this discovery pattern -- tracing a supply chain backward from end-product to find the binding constraint -- independently to the current analysis target.*

### MU / Memory (Supercycle + Legacy Void)
*Historical Application:* AI demand breaking traditional boom/bust cycle. Major producers pivoting to HBM abandoned legacy DRAM/NAND, creating "Legacy Void" pricing power. Street estimated 33-38% NAND hikes; actual 100%. Forward P/Es at single digits despite 100%+ Y/Y growth -- Walmart benchmark confirmed mispricing. *Apply this pattern -- identifying when major players abandon a market segment, creating pricing power for remaining suppliers -- independently to the current analysis target.*

### NBIS / Neocloud (Full-Stack Infrastructure)
*Historical Application:* Full-Stack neocloud (own orchestration software, 60-75% gross margin). Tracked through Enthusiasm -> Consolidation -> "Prove It" phases. Confirmed multi-billion Mag7 contracts as execution validation. Per-MW unit economics normalized for comparison. *Apply this pattern -- classifying companies by vertical integration and tracking sector phase progression -- independently to the current analysis target.*

### CPSH / AlSiC (Thermal Management Bottleneck)
*Historical Application:* GPU wattage increases made thermal solutions a binding constraint. BOM analysis identified AlSiC as critical material. CPSH = primary Western supplier at chokepoint with concentrated supply and multi-year capacity lead times. *Apply this pattern -- using BOM analysis to find critical but overlooked materials -- independently to the current analysis target.*

### LPTH / Germanium (Defense Material Bottleneck)
*Historical Application:* Scenario-driven: China germanium export ban created Western supply gap. LPTH's "Black Diamond" lenses = sole Western source for multi-spectral IR optics. Scored 6/6. Cross-chain validation in both germanium/defense AND photonics chains -- strongest conviction signal. *Apply this pattern -- tracing export control impacts to find sole Western alternatives -- independently to the current analysis target.*
