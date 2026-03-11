# Supply Chain Bottleneck Analysis

## Independent Discovery First

When given a new sector, event, or query to analyze, ALWAYS execute the Unified Discovery Workflow in `methodology.md` BEFORE referencing any historical examples in this document. That workflow is the single authoritative process for independent opportunity identification. Historical case studies here demonstrate HOW the methodology was applied, not WHAT tickers to start with.

---

## SEC Filing as Discovery Starting Point

When the pipeline provides `sec_supply_chain` data (sec_status = SEC_SC_available), use it as the structured foundation for supply chain mapping:

### Anchoring Layer 1-2 from SEC Data
- SEC Item 1 (Business) discloses key suppliers, customers, and supply chain relationships as legal requirements
- SEC Item 1A (Risk Factors) discloses single-source dependencies, geographic concentration, and capacity constraints
- Use these as verified Layer 1-2 anchors: named entities with their relationships and concentration data
- High-confidence matches (entity + quantitative data) can be used directly as evidence for 6-Criteria Scoring

### Mapping SEC Data to 6-Criteria Scoring
| SEC Category | Maps to Criterion | Usage |
|---|---|---|
| single_source_dependencies | 1 (Supply concentration) | Direct evidence — sole/single source = high concentration |
| geographic_concentration | 3 (Geopolitical risk) | Direct evidence — country-level production concentration |
| capacity_constraints | 2 (Capacity constraints), 4 (Long lead times) | Lead time and backlog disclosures |
| supply_chain_risks | 5 (No substitutes), 6 (Cost insignificance) | Risk language indicating substitutability and criticality |
| suppliers | 1 (Supply concentration) | Named supplier relationships for concentration analysis |
| revenue_concentration | 1 (Supply concentration) | Customer % data from Notes — revenue dependence quantification |
| geographic_revenue | 3 (Geopolitical risk) | Quantitative geo-revenue % from Notes — overrides heuristic scoring |
| purchase_obligations | 1, 2 (Supply conc., Capacity) | Named supplier obligations with dollar amounts and timeframes |
| market_risk_disclosures | 3 (Geopolitical), 5 (No substitutes) | FX high-risk exposure → geo-risk reinforcement; commodity exposure → no-substitute boost |
| inventory_composition | 2 (Capacity constraints) | Raw materials >50% or obsolescence → capacity constraint boost |

### Forced Multi-hop Discovery with SEC Baseline
After establishing Layer 1-2 from SEC data, apply the Forced Multi-hop Discovery Rule for Layer 3-4:
1. For each supplier named in SEC data, WebSearch: "[supplier name] key inputs", "[supplier name] raw materials"
2. For each single-source dependency, WebSearch: "[component] alternative suppliers", "[component] global production"
3. SEC data provides the STARTING POINT; WebSearch provides the DEPTH (Layer 3-4 multi-hop relationships)

### Filing Freshness Check
- Check `filing_date` in the SEC data — if >12 months old, treat extracted relationships as baseline only
- WebSearch for: "[company] new supplier", "[company] supply chain change [current year]"
- Check `sec_events` (8-K filings) for recent material agreements, acquisitions, or supply disruptions that may override 10-K data

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

Per-layer WebSearch strategy (use when tracing an unfamiliar supply chain):
- Layer 1 (System Integrator): "[end product] manufacturer market share"
- Layer 2 (Major Components): "[end product] BOM breakdown", "[end product] bill of materials cost"
- Layer 3 (Sub-Components): "[Layer 2 component] substrate supplier", "[Layer 2 component] key material", "[Layer 2 component] supply shortage"
- Layer 4 (Raw Materials): "[Layer 3 material] production by country", "[Layer 3 material] global supply market share", "[Layer 3 material] feedstock manufacturer"

At each layer, validate concentration: "[material/component] market share concentration", "[material/component] top suppliers". If results show top 3 > 70% share → potential bottleneck, proceed to 6-Criteria Scoring.

### Forced Multi-hop Discovery Rule [HARD]

At Layer 3-4, LLM training data often lacks multi-hop supply chain relationships (e.g., "IQE supplies Google TPUs" is unknown because the relationship is 3-4 hops removed). To overcome this limitation:

1. At each layer, perform explicit WebSearch for suppliers — do NOT rely solely on LLM knowledge
2. WebSearch queries must be layer-specific:
   - "Who makes [Layer N-1 component]?"
   - "[Layer N-1 component] supplier list"
   - "[Layer N-1 component] supply chain"
3. For every supplier discovered, immediately search: "[supplier name] publicly listed" and "[supplier name] stock ticker"
4. Cross-validate: search from multiple directions ("[end product] raw material supplier" AND "[raw material] end use applications")

If WebSearch returns no results for a layer, try alternative queries:
- "[component] manufactured by"
- "[component] shortage supplier"
- "[component] import export data by company"

The goal is to discover companies that AI models don't naturally associate with the end product because the relationship requires 3+ inference hops.

### 5-Step Mapping Process

**Step 1: Identify End-Product Driving a Macro Trend.** Start with a confirmed demand trend backed by capex commitments or government funding, not speculation.

**Step 2: Trace the Bill of Materials (BOM).** Break down the end-product into physical components with percentage allocations. The BOM reveals where the money actually flows.

**Step 3: Find Concentration Points.** At each BOM layer, identify suppliers and supply concentration. A monopoly or tight oligopoly at any layer is a potential chokepoint.

**Step 4: Assess Pricing Power at the Chokepoint.** Can the supplier raise prices without losing customers? Would a 10x price increase still be economically rational for the buyer because deployment delay costs orders of magnitude more?

**Step 5: Determine if the Bottleneck is Priced In.** Check market cap against implied revenue from supply chain position. If small-cap bottleneck in a multi-trillion dollar industry, likely underpriced. If institutions have accumulated and analyst coverage is extensive, the opportunity may have passed.

**Key Principle:** "Follow the money flow down." Start from the demand source and trace layer by layer. The opportunity is at the narrowest point of the funnel. Bottlenecks migrate over time as each constraint resolves and demand hits the next one.

**Depth Gate [HARD]:** The mapping is NOT complete until Layer 4 (Raw Materials / Feedstock) has been reached. If your current mapping stops at Layer 1-2, you have found the OBVIOUS companies, not the ASYMMETRIC ones. The smallest market cap bottleneck is almost always at Layer 3-4, not Layer 1-2. When tracing a supply chain:
- Layer 1-2 companies (system integrators, major components) are typically large-cap, well-covered by analysts, and already priced in
- Layer 3-4 companies (sub-components, raw materials) are where supply concentration is most extreme, market caps are smallest, and discovery alpha is highest
- If you cannot identify Layer 4, search explicitly: "[Layer 3 material] raw material source", "[Layer 3 material] feedstock supplier", "[Layer 3 material] production by country"
- Exception: If the target is a pure-service or pure-software company with no physical supply chain, document why Layer 4 is not applicable and skip
- When mapping multiple supply chain cascades, apply the Depth Gate to EACH cascade independently. Do not compensate for a shallow secondary cascade by going deeper on the primary. Each cascade is a separate discovery opportunity

### Forced Multi-hop Discovery Execution Protocol

The Forced Multi-hop Discovery Rule above establishes the WHAT and WHY. This protocol defines the HOW — a concrete 4-hop execution template that transforms the rule into a traceable, repeatable process. The goal is to move beyond the obvious layer and systematically discover upstream bottleneck candidates that are invisible to surface-level analysis.

#### 4-Hop Execution Template

**Hop 0 (Anchor): Start from the End Product or Known Bottleneck**
- Identify the end product, deployment, or known bottleneck company that anchors the supply chain.
- Extract supply chain relationships from SEC 10-K/10-Q filings (Item 1, Item 1A). Use the `sec_supply_chain` pipeline output when available.
- Document: What does this company make? Who are its customers? What are its key inputs?
- Output: A list of named suppliers, single-source dependencies, geographic concentrations, and capacity constraints — all sourced from regulatory filings.

**Hop 1 (Tier 1 Suppliers): Direct Supplier Investigation**
- For each supplier identified in Hop 0, investigate independently:
  - Check SEC filings for the supplier (if publicly traded) to extract ITS supply chain relationships
  - Determine if the supplier is single-source or part of an oligopoly for its product
  - Apply the 6-Criteria initial scan: Does this supplier show concentration signals (top 3 >70% share)? Geographic concentration? Capacity constraints?
- WebSearch to supplement: "[supplier name] competitors", "[supplier product] market share", "[supplier product] alternative sources"
- Output for each Tier 1 supplier: name, supply chain role, concentration assessment, SEC data availability, preliminary bottleneck potential (high / medium / low).

**Hop 2 (Tier 2 Suppliers): Supplier-of-Supplier Discovery**
- For suppliers identified in Hop 1 as having bottleneck potential (medium or high), trace THEIR suppliers.
- SEC filings are often unavailable at this depth. WebSearch becomes the primary tool:
  - "[Tier 1 supplier product] key inputs"
  - "[Tier 1 supplier product] raw materials"
  - "[Tier 1 supplier product] substrate supplier"
  - "[Tier 1 supplier] supply chain dependencies"
- For each Tier 2 supplier discovered, immediately search: "[supplier name] publicly listed", "[supplier name] stock ticker"
- Apply the 6-Criteria scan again. Cross-chain utilization check: does this Tier 2 supplier appear in multiple downstream chains?
- Output for each Tier 2 supplier: name, supply chain role, concentration level, SEC data availability (often "none" at this tier), preliminary bottleneck assessment.

**Hop 3 (Raw Material / Feedstock): Upstream Terminus**
- Continue upstream from Hop 2 until reaching commodity inputs or specialized feedstock.
- This is often where the hidden bottleneck lives — the material or process that everyone depends on but few analysts trace back to.
- WebSearch focus shifts to production geography and capacity:
  - "[material] production by country"
  - "[material] global supply market share"
  - "[material] capacity expansion timeline"
  - "[feedstock] manufacturers"
- Geographic concentration at this level is often extreme (single country controlling >80% of production).
- Output: material/feedstock identification, production geography, supplier names (if identifiable), concentration ratio, capacity lead time.

#### Per-Hop Validation Checklist

At each hop, apply the following checks:

1. **6-Criteria Scoring**: Apply the Bottleneck 6-Criteria Scoring Framework to every entity with concentration signals. Score need not be complete at every hop — partial evidence is expected at deeper tiers.
2. **Cross-chain utilization**: Check whether the same supplier appears in multiple downstream chains. A shared supplier across 3+ end-product chains is a compounding bottleneck signal.
3. **Geographic concentration check**: Flag any hop where >50% of production is in a single country. This reinforces Criterion 3 (geopolitical risk) and amplifies disruption impact.
4. **Capacity constraint timeline**: For each bottleneck candidate, estimate time to add meaningful new capacity. Constraints measured in years (reactors, fabs, mines) are structural; constraints measured in months (assembly lines, software licenses) are transient.

#### Stopping Conditions

Do not trace indefinitely. Stop the multi-hop traversal when:

1. **Reached commodity level**: The upstream input is a broadly traded commodity (silicon, copper, aluminum, rare earth oxides). Commodity-level bottlenecks follow different dynamics — they are driven by mining permits, refining capacity, and geopolitical controls rather than company-specific concentration. Document the commodity and its geographic concentration, but do not continue hopping.
2. **Persistent data gaps**: 3 consecutive hops where SEC data is unavailable AND WebSearch cannot identify specific suppliers or production data. At this point, the supply chain is too opaque for evidence-based analysis.
3. **Supply chain diffusion**: The supply base becomes too fragmented — more than 10 suppliers at the same tier, none controlling more than 5% of supply. Fragmented tiers do not produce bottleneck candidates.

#### Discovery Quality Indicators

Assess the quality of each multi-hop discovery effort against these tiers:

| Quality | Criteria |
|---|---|
| **Excellent** | Traced to raw material/feedstock level (Hop 3) with 3+ investable bottleneck candidates identified at different tiers. Full evidence chain from end product to upstream terminus. |
| **Good** | Traced 2+ hops beyond the anchor with at least 1 non-obvious bottleneck candidate (not the company everyone already knows). Evidence chain has minor gaps but overall direction is clear. |
| **Minimum** | Completed at least 1 hop beyond the obvious layer. Identified at least one supplier relationship that was not immediately apparent from the anchor company's analyst coverage. |
| **Insufficient** | Stayed at the obvious company level (Hop 0-1 only). Did not discover any relationship beyond what is available from a standard analyst report. This does not meet the Forced Multi-hop Discovery Rule. |

Every discovery effort should target "Good" or above. "Minimum" is acceptable only when data gaps genuinely prevent deeper tracing (per stopping condition 2). "Insufficient" indicates that the Depth Gate has not been satisfied.

#### Per-Hop Output Structure

For each hop, document:
- **Supplier/entity name**: The company or material identified
- **Supply chain role**: What it provides to the downstream hop (substrate, feedstock, component, service)
- **Concentration level**: Monopoly (>70%), oligopoly (40-70%), competitive (<40%), or unknown
- **SEC data availability**: Available (with filing date) / unavailable / not applicable (private company, commodity)
- **Preliminary bottleneck assessment**: High potential (multiple 6-Criteria signals) / medium potential (1-2 signals) / low potential (no concentration signals) / insufficient data

Reference BM02 (multi_hop_bottleneck_discovery) benchmark behavior: the expectation is to NOT stop at the obvious component layer but to trace upstream to substrates, specialized materials, and feedstock sources. The benchmark specifically rewards discovering entities at Hop 2-3 that are invisible from the anchor company's level — the kind of supplier-of-supplier relationships that require 3+ inference hops to uncover.

---

## Bottleneck 6-Criteria Scoring Framework

This is the SINGLE authoritative scoring framework. Apply these six criteria to every concentration point.

Pipeline auto-scores criteria 1-5 from SEC supply chain data with scoring guide and assessment thresholds in output. Agent validates via WebSearch and evaluates criterion 6 directly.

| # | Criterion | Agent Role |
|---|-----------|------------|
| 1 | Supply concentration | Review pipeline score; cross-validate concentration claims via WebSearch |
| 2 | Capacity constraints | Review pipeline score; verify duration estimates and recent changes |
| 3 | Geopolitical risk | Review pipeline score; assess current geopolitical context |
| 4 | Long lead times | Review pipeline score; check for recent capacity expansion announcements |
| 5 | No substitutes | Review pipeline score; WebSearch for emerging alternatives |
| 6 | Cost insignificance + deployment criticality | **Agent-only evaluation**: Small fraction of system cost but required for deployment; customers cannot reduce consumption. Would delaying deployment cost far more than the component? |

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
- **Tier 1: Full-Stack** (60-75% GM; 기본 범위, 비즈니스 모델에 따라 조정 가능). Own orchestration software + hardware infrastructure. Highest margin quality and customer stickiness.
- **Tier 2: GPU Cloud** (40-60% GM). Managed GPU-as-a-service with some software layer but not full vertical integration. May operate on leased or owned infrastructure.
- **Tier 3: Colocation / Bare-Metal** (30-45% GM). Infrastructure-only, rent capacity without meaningful software differentiation. Commodity-like pricing risk.
- **Tier 4: BTC Miner Pivoting** (GM volatile, highest execution risk). Crypto miners repurposing existing power/cooling infrastructure for AI compute. Unproven unit economics in AI, legacy mining operations may subsidize or drag. Execution risk is the dominant variable.

**Cross-Tier Comparison Rule:** When comparing companies across tiers, ALWAYS explicitly state the tier difference and explain why the comparison is still valid (e.g., shared customer base, same datacenter market). Do NOT compare Tier 1 and Tier 3 companies on gross margin without noting the structural difference in business model. A Tier 1 at 65% GM and a Tier 3 at 35% GM are not "comparable" without this context.

**How to apply:** First classify company into tier. Evaluate gross margins as primary differentiator -- "Gross Margins > GW capacity." Assess contract quality (confirmed Mag7 contracts vs speculative pipeline). Check "Prove It" phase status: has it demonstrated execution on contracted revenue?

**Phase Progression Model:** Enthusiasm (broad basket buying) -> Consolidation (capital concentrates into leaders) -> Conviction Crystallization (single-name positions) -> "Prove It" Execution (revenue delivery validation) -> Maturation (focus shifts to upstream bottlenecks). Apply this progression pattern to any emerging sector.

**Full Bear Case Checklist (Mandatory for All Neoclouds):**
Every neocloud analysis MUST address ALL 10 bear case items:

1. **GPU Depreciation Burden**: FASB allows 3-5 year useful life, but effective technological life is 18-24 months. Depreciation typically consumes 30-40% of gross margin. If stated useful life exceeds 3 years, flag as aggressive accounting.
2. **OpenAI Contagion Risk**: Exposure to OpenAI or VC-funded AI companies as primary customers. If OpenAI restructures, pivots, or reduces compute spend, which neoclouds face demand cliffs?
3. **Credit Tightening Impact**: Higher rates kill weak balance sheets. Can the company refinance at reasonable rates? Check debt quality grade — Grade D (>8% implied rate) is existential.
4. **Datacenter Construction Delays**: Construction timelines are 18-36 months. Delays between announced and operational capacity create revenue gaps. Verify construction milestones via 8-K filings.
5. **Utilization Drag**: GPU fleet economics depend on >70% utilization. Below that threshold, depreciation overwhelms revenue. Ask: "What is contracted utilization vs total capacity?"
6. **NVDA Competition Risk**: NVIDIA's DGX Cloud competes directly with neoclouds. As NVDA expands its cloud offering, neoclouds face margin compression from the supplier competing downstream.
7. **Custom Silicon Displacement**: Mag7 developing custom ASICs (Google TPU, Amazon Trainium) reduces dependence on NVDA GPUs and potentially on GPU cloud providers. Timeline: 2-4 years for full displacement risk.
8. **Interest Rate Sensitivity**: Capital-intensive business models amplify rate sensitivity. Calculate: interest expense / revenue ratio. Above 15% = structural disadvantage.
9. **Execution Risk (Pivot Quality)**: For BTC miner pivots: has the company demonstrated AI/HPC revenue, or is it pre-revenue marketing? Pivoting is announced frequently; successful execution is rare.
10. **Dilution/Debt Quality**: Toxic debt (8%+ implied rate) + serial dilution = value destruction. Cross-reference with Bear-Bull Paradox filter. Grade D debt + active dilution = Strong Sell candidate regardless of other factors.

Tier 1 (Full-Stack) companies can partially offset items 1, 5, 6 through software margins; Tier 3-4 companies bear the full impact. When 3+ items flag simultaneously, cap rating at Hold unless Trapped Asset Override conditions are met.

**Counterparty Risk Hierarchy (Mandatory for Contracted Revenue Claims):**
When a neocloud claims contracted or committed revenue, classify the counterparty:
- **Tier A: Mag7 Fortress** (AAPL, MSFT, GOOG, AMZN, META, NVDA, TSLA). Near-zero default risk. Multi-year contracts are bankable.
- **Tier B: Enterprise Cloud / Large Tech** (ORCL, CRM, IBM, SAP, large enterprise customers). Low default risk but contracts may have flexibility clauses.
- **Tier C: VC-Funded AI Companies** (well-funded AI startups with $500M+ raised). Moderate risk -- funding runway matters. Verify latest funding round and burn rate.
- **Tier D: Startup / Early-Stage** (seed to Series B AI companies, small crypto firms). High default risk. Revenue from Tier D counterparties should be heavily discounted in valuation.
- **Rule:** When evaluating contracted revenue, always identify counterparty tier. "$2B contracted revenue" from Tier A is fundamentally different from "$2B contracted revenue" from Tier C/D mix.

### Three-Factor Crash Triage

When a sector-wide selloff hits neocloud/AI infrastructure stocks, apply this triage to isolate which companies survive vs fail:

**Factor 1: Mag7 Contract Visibility**
- Does the company have named, public Mag7 contracts with specific dollar amounts and timelines?
- Tier A counterparties (Mag7) provide near-zero default risk revenue backstop
- Companies with only Tier C/D counterparties face demand cliff risk during sector stress

**Factor 2: Cash vs Toxic Debt**
- Net cash position (cash - total debt) determines survival runway
- Debt quality grade: A-B survives any credit cycle; C is stressed; D is existential
- During crashes, credit markets close to Grade C/D issuers — they cannot refinance

**Factor 3: Counterparty Isolation**
- Is the company's revenue exposed to a single at-risk counterparty (e.g., OpenAI-dependent)?
- Diversified Mag7 exposure is resilient; single-counterparty concentration is fragile
- Map each company's revenue sources to counterparty tiers and identify contagion paths

**Triage Decision Rule**: Companies passing all 3 factors (Mag7 contracts + net cash/Grade A-B + diversified counterparties) are BUY on crash. Companies failing 2+ factors are AVOID until stress resolves. Companies failing Factor 2 alone may be terminal.

**Negative Balance Sheet Benchmark:**
When analyzing any neocloud, identify the worst balance sheet in the peer group as a standing reference point for toxic financials: toxic debt structure (8-10%+ implied interest rate; 기본 임계값, sector stress level에 따라 조정 가능), serial dilution history, pre-revenue inflation. Compare each company's debt quality grade and dilution metrics against this lower bound. If a company's metrics approach these levels, apply Bear-Bull Paradox filter from `valuation_fundamentals.md`.

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

## Absence Evidence Checklist

Information absence itself carries analytical signal. When data is missing, classify the type of absence and apply the corresponding interpretation framework.

### 5 Types of Absence Evidence

| # | Absence Type | Signal | Interpretation Framework |
|---|-------------|--------|------------------------|
| 1 | **No Hyperscaler/Mag7 Contract** | Negative for execution certainty | Company claiming infrastructure demand without named Mag7 contracts has unvalidated revenue pipeline. Compare against peers with confirmed contracts to assess discount. |
| 2 | **No Fundamental Change + Selloff** | Positive for entry | When price drops significantly without any news, earnings miss, or contract cancellation, the selling is mechanical (tax harvesting, MM pinning, algo rebalancing), not fundamental. Potential accumulation opportunity. |
| 3 | **No Analyst Coverage** | Mispricing signal | Zero or minimal analyst coverage combined with strong fundamentals suggests the market has not discovered the company. Highest alpha potential but requires independent validation. |
| 4 | **No Domestic Production** | Geopolitical vulnerability | When a critical material has zero Western/domestic production capability, the geopolitical risk is maximal. Any export control or disruption creates immediate sole-source situations for the nearest Western alternative. |
| 5 | **Marketed Capacity vs Contracted Capacity** | Fraud/hype signal | When a company markets capacity (MW, units, etc.) but has no disclosed contracts or SLAs for that capacity, the gap between marketed and contracted is a red flag. Verify via SEC filings. |

### Application Rules

1. **During pipeline analysis**: When SEC filing data shows empty categories, check the `data_coverage` field to distinguish "not_disclosed" (company deliberately stated no concentration) from "insufficient_context" (data simply wasn't found).
2. **During WebSearch validation**: Actively search for the absence — "Does [company] have Mag7 contracts?", "[material] US production capacity". The answer "no results found" is itself evidence.
3. **Interaction with 6-Criteria Scoring**: Absence Type 4 (no domestic production) directly reinforces Criterion 3 (geopolitical risk). Absence Type 1 (no Mag7 contract) weakens conviction regardless of bottleneck score.

---

## Scenario-Driven Discovery

For the full discovery workflow including entry routing, scenario framing (5-element structure, 6 scenario categories), phases, research-to-bottleneck mapping funnel, tool sequencing, and common pitfalls, see the **Unified Discovery Workflow** in `methodology.md`. That workflow is the single authoritative process.

This file provides the sub-protocols that the Unified Discovery Workflow references: 5-Layer Supply Chain Mapping Template (above), Forced Multi-hop Discovery Execution Protocol (above), 6-Criteria Bottleneck Scoring Framework (above), and the Historical Case Studies (below).

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

### Reverse Cross-Chain Discovery (Pipeline-Assisted)

The cross-chain subcommand scores each shared entity for bottleneck potential with thresholds and interpretation in output.

| Assessment Level | Action |
|-----------------|--------|
| Strong bottleneck signal | Must investigate — WebSearch for ticker |
| Moderate bottleneck signal | Investigate if small-cap |
| Weak signal | Note for monitoring |
| Low signal | Ignore |

This automates the principle: "If a supplier appears in many companies' SEC filings, it likely controls a supply chain chokepoint." Only supplier and single-source roles generate bottleneck signals; customer roles indicate revenue concentration risk.

### When to Update a Map
Update when: a major player enters or exits a layer, export controls change material availability, new technology creates a substitute, capacity expansions resolve a constraint, or pricing data indicates bottleneck migration.

---

## Appendix: Historical Case Studies (Reference Only)

> **HARD GUARDRAIL**: These cases are structural templates showing HOW the methodology was applied. They are NOT starting points for new analysis. For every new query, the Discovery Workflow MUST be executed independently and completed BEFORE any historical case is referenced. Defaulting to these tickers on a new query is an anti-pattern.

> [METHODOLOGY EXAMPLES — The tickers below illustrate methodology PATTERNS, not starting points.
> For any new analysis, execute the Unified Discovery Workflow independently before referencing these cases.
> Do not anchor on these specific tickers or sectors.]

### Pattern: Backward Supply Chain Tracing → Binding Constraint Discovery
*Historical example (semiconductor substrate):* Traced optical interconnect chain backward to substrates. Identified a specific compound semiconductor material as binding constraint when export controls disrupted a major non-Western supplier, creating effective near-monopoly for the Western alternative (~40% global share). Cost insignificance: hyperscaler would pay 100x substrate price rather than delay deployment. Scored 5/6.

### Pattern: Legacy Void Pricing Power
*Historical example (memory supercycle):* AI demand breaking traditional boom/bust cycle. Major producers pivoting to next-gen memory abandoned legacy product lines, creating "Legacy Void" pricing power for remaining suppliers. Street estimated 33-38% price hikes; actual 100%. Forward P/Es at single digits despite 100%+ Y/Y growth — Walmart benchmark confirmed mispricing.

### Pattern: Vertical Integration Classification + Sector Phase Tracking
*Historical example (neocloud infrastructure):* Full-Stack neocloud (own orchestration software, 60-75% gross margin). Tracked through Enthusiasm → Consolidation → "Prove It" phases. Confirmed multi-billion Mag7 contracts as execution validation. Per-MW unit economics normalized for cross-company comparison.

### Pattern: BOM Analysis → Overlooked Critical Material
*Historical example (thermal management):* GPU wattage increases made thermal solutions a binding constraint. BOM analysis identified a specialized metal matrix composite as critical material. Primary Western supplier at chokepoint with concentrated supply and multi-year capacity lead times.

### Pattern: Export Control → Sole Western Alternative
*Historical example (defense optics material):* Scenario-driven: export ban on a critical optical material created Western supply gap. One company's proprietary processing = sole Western source for multi-spectral IR optics. Scored 6/6. Cross-chain validation across defense AND photonics chains — strongest conviction signal.

### Pattern: FDA Approval as Regulatory Bottleneck
*Example (healthcare):* First-in-class therapy for an underserved indication. Multi-year FDA review timeline created temporary monopoly. Applying the same discovery logic: regulatory approval IS the capacity constraint. 6-Criteria scoring applied — supply concentration (sole approved therapy), long lead times (10-15yr development), no substitutes within 2 years.

### Pattern: Grid Infrastructure as Cascading Bottleneck
*Example (energy/utilities):* AI datacenter demand creating capex cascade from hyperscalers to utilities to transformer manufacturers. Power transformer lead times of 2-4 years = structural constraint. Same multi-hop discovery logic: trace demand from end-use (compute) through infrastructure layers to find the binding constraint.
