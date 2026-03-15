# Supply Chain, Valuation, and Position Expression

What to evaluate when analyzing a company. Bottleneck discovery, valuation, and position expression flow as one continuous process: find bottleneck, check moat via margins, value, choose instrument.

---

## Part A — Bottleneck Discovery

### True Bottleneck 3-Criteria

Not every bottleneck provides a great investment opportunity. All three must be met simultaneously:

1. **Demand visibly outstripping supply** — evidenced by commodity price spikes, lead time expansion, capacity utilization near limits, or order backlog growth
2. **Oligopoly or monopoly position** — top suppliers dominate market share with no meaningful challenger
3. **No viable substitutes before demand peaks** — no competitor announcements, no capacity expansion plans, no substitute technology in development pipeline

If any single criterion fails, the bottleneck may exist physically but does not produce the pricing power that generates alpha.

### BOM Analysis Method

Break the end-product into its physical components with cost-percentage allocation, then trace each component to its supplier(s) and their market share. BOM reveals where the money actually flows and where hidden leverage exists.

Process:
1. Identify end-product and its total bill of materials
2. Decompose into major component categories with approximate cost contribution
3. For each component: who makes it, what is their market share, what are the margins
4. Identify disproportionate leverage — a component that is 5% of BOM cost but has one supplier commands outsized pricing power

Example chain: GPU module -> HBM -> advanced packaging -> substrates -> rare materials. At each link, a small number of suppliers may control the entire flow.

### Multi-Hop Supply Chain Tracing (7 Layers)

Follow the money flow down — start from demand source, trace layer by layer:

| Layer | Description |
|-------|-------------|
| 0 | End Product / User |
| 1 | System Integrator / OEM |
| 2 | Major Components |
| 3 | Sub-Components |
| 4 | Raw Materials |
| 5 | Equipment / Tools |
| 6 | Feedstock / Chemicals |

At each layer, answer five questions:
- How many suppliers exist?
- What is the lead time for new capacity?
- What is the geographic concentration?
- What is the cost as a percentage of the end product?
- Are there substitutes?

**Criticality Assessment**: At each layer, evaluate criticality — would disruption at this layer halt the entire chain? Assign tiers:
- **Critical**: Disruption halts the chain entirely. No workaround exists.
- **High**: Disruption causes significant delay. Workarounds exist but are expensive or slow.
- **Medium**: Disruption is manageable. Multiple suppliers or substitutes exist.
- **Low**: Commodity input with abundant supply.

Direct attention to Critical and High layers — these are where pricing power concentrates and analyst coverage is thinnest.

The deepest layers (4-6) often have the least analyst coverage and the most mispricing.

### Recursive Tracing — Bottleneck within Bottleneck

After finding a bottleneck at Layer N, ask: "What does THIS company depend on?" Trace upstream recursively until you reach the deepest constraint. The deepest bottleneck often has the most pricing power and the least market attention because analysts covering the end product rarely look past Layer 2.

### Moat Validation

Three dimensions, applied in sequence:

1. **Margins > Capacity** — high gross/operating margins prove pricing power exists NOW. Capacity utilization data shows whether it persists. If margins are expanding while utilization is near peak, the moat is strengthening.

2. **Absence of Alternatives** — Ask: "Who else could do this? How long would it take?" If the answer is "nobody" or "it would take years," the moat is real. Check: no competitor capacity expansion, no substitute technology in pipeline, no regulatory pathway for new entrants, patent/licensing barriers with significant remaining life. A well-funded competitor's FAILURE to replicate is the strongest evidence of moat depth (inverse proxy validation).

3. **Sector-Agnostic Positioning** — Does the company sell tools or materials to ALL players in the space? If yes, the company wins regardless of which end-product competitor prevails. This characteristic amplifies the bottleneck but is not required for a valid thesis.

### Absence Evidence (Negative Space)

"Who else could do this?" If the answer is "nobody" or "it would take > 18 months," that absence IS the evidence of a moat. Specifically check:
- No competitor capacity expansion announcements
- No substitute technology in development pipeline
- No regulatory pathway for new entrants
- Patent or licensing barriers with remaining life > 5 years

### Supply Chain as Multi-Dimensional Graph (V3)

Physical product flow is only one dimension of supply chain analysis. Alpha lives at the intersection of three dimensions:

**Physical Dimension**: Product flow, BOM decomposition, bottleneck identification, criticality tier assessment. This is the traditional supply chain analysis — tracing components from end-product to raw materials.

**Financial Dimension**: Debt and credit structures create contagion pathways that follow DIFFERENT routes than product flow. Two companies in the same sector with the same customers can have opposite contagion exposure based on their balance sheet structure. A company funded by direct hyperscaler contracts is isolated from credit tightening that devastates companies funded by intermediary debt. When assessing a supply chain position, ask: "If the sector leader's credit deteriorates, does the contagion reach this company through its debt structure?"

**Strategic Dimension**: Large companies have structural incentives to ensure smaller companies succeed — and these incentives create invisible backstops that fundamentally change the downside profile. When a larger entity's strategic position depends on a smaller company's success (e.g., preserving demand for its products against in-house alternatives), the larger entity will backstop the smaller one. Map these incentive structures explicitly: "Which larger entity structurally needs this company to succeed? How existential is that need?"

**Comparative Principle**: Within a sector, the question is not "is this a bottleneck?" but "which is the BEST bottleneck?" Compare candidates on integration depth (full-stack vs bare-metal — full-stack commands structurally higher margins), margin quality, contract visibility, and balance sheet strength. The company controlling the full vertical stack (software + hardware + orchestration) has a deeper moat than one providing capacity alone.

### Co-Development as Risk Discount

When a major partner (defense prime, hyperscaler) is actively co-developing with a smaller company, execution risk drops below what standalone analysis would suggest. The partner brings institutional knowledge, infrastructure, and often capital. Assess: "Does the partner have prior demonstrated capability in this domain?" If yes, the co-development relationship transfers that capability, reducing execution risk.

### Defense Supply Chain Discovery

For defense and national security supply chains, supplier relationships are often undisclosed. A forensic identification method applies: (1) Identify a defense prime's new program from public announcements. (2) Find small-cap companies announcing contracts with unnamed "leading defense" customers. (3) Match hardware specifications (ruggedized components, temperature ranges, edge AI) to program requirements. (4) If specification match confidence is high, the small-cap has an asymmetric re-rating opportunity because the market does not yet know the customer identity.

### Geographic and Geopolitical Risk

Single-country production concentration creates both premium and risk:
- Export controls or sanctions can create instant monopolies for alternative suppliers
- Tariff exposure can shift relative cost structures overnight
- Track: production percentage by country, policy trajectory, ally/adversary alignment

Geopolitical risk is asymmetric — it can destroy a thesis instantly but can also create once-in-a-decade entry points for beneficiaries.

### Historical Analogs for Bottleneck Pricing

When a bottleneck is confirmed, search for historical parallels in other supply chains to calibrate price magnitude and duration expectations. Historical analogs are for magnitude calibration, not stage-by-stage prediction. The analog does not predict, but it anchors expectations about how far and how long a bottleneck-driven repricing can extend.

### Interpretation Caveats

**When bottleneck scores may mislead**: A company can score high on physical bottleneck criteria while being financially exposed through its debt structure. Always cross-check the financial dimension (V3) before acting on a bottleneck score. A physically dominant supplier with toxic debt is not a safe investment.

**When dilution assessment requires judgment**: The pipeline classifies dilution based on quantitative metrics (share count changes, SBC levels, FCF impact). However, whether a dilution event is GOOD (contract-backed growth investment) or BAD (serial value destruction) requires reading the SEC filing context. Key questions: Is the dilution funding a signed contract? What is the interest rate relative to peers? Does management have a history of diluting shareholders at prior companies? These contextual factors override the quantitative classification.

**When full-stack premium does not apply**: In early-stage markets, bare-metal providers may monetize capacity faster than full-stack operators because the software layer is still developing. The integration depth premium applies to mature markets where the orchestration layer has proven its value through margin differentiation.

---

## Part B — Valuation Framework

### 5 Valuation Methods

Choose based on company stage and characteristics:

| Method | When to Use | Key Consideration |
|--------|------------|-------------------|
| **Forward P/E** | Profitable companies with earnings visibility | Benchmark against peers at similar growth rates. A mature retailer at 45x forward P/E with 3% growth is absurdity — use as sanity check |
| **MC/Revenue** | Pre-profit with significant revenue and > 50% gross margins | Revenue quality matters more than revenue size |
| **EV/FCF** | Cash-generative businesses | Use real FCF after stock-based compensation adjustment, not reported FCF |
| **Comparable** | Cross-listed or sector peer multiples | For relative value — works best when peer set is clean |
| **NAV Premium** | Asset-heavy companies | Book value anchors the floor; premium reflects franchise value |

No single method is sufficient. Use at least two for cross-validation.

**Sum-of-Parts**: For multi-segment companies with distinct business lines at different growth stages, value each segment independently using the appropriate method above, then aggregate. This prevents a high-growth segment from being dragged down by a mature segment's multiple, or vice versa.

### Funding Price Floor Heuristic

When institutional investors (PE, VC, strategic) invest at Price X, that price becomes a soft floor. The logic: institutions performed due diligence at that price and generally will defend it.

Stronger when:
- Investment is recent (< 6 months)
- Investor is strategic (not purely financial)
- Amount is significant (> 5% of market cap)

This is NOT a guarantee — it is a probabilistic support level. It fails when the broader market enters distress or when the company's fundamentals deteriorate post-investment.

### Dual-Valuation Rule (Always Both)

Every valuation must present two anchors:

1. **No-Growth Floor**: Current revenue x operating margin x conservative multiple = minimum value. This is where the stock would trade if growth stopped tomorrow.
2. **Growth Upside**: Forward revenue trajectory x target margin x growth-adjusted multiple = target value.

Present the floor FIRST. The gap between floor and upside IS the asymmetry measure. A stock trading near its no-growth floor with visible growth catalysts is the ideal setup.

For pre-revenue companies: acknowledge the floor is inapplicable, explain why the growth valuation is primary, and apply a larger uncertainty discount.

### Earnings Quality Signals

- **Consecutive beats** (3+ quarters) = execution validated — the cockroach effect in reverse (good surprises cluster too)
- **Revenue acceleration > EPS acceleration** = organic growth, healthy
- **EPS acceleration > revenue acceleration via margin expansion** = check sustainability — is it operating leverage or accounting tricks?
- **Real FCF vs reported FCF** — if reported FCF is positive but FCF after stock-based compensation is negative, the profitability is an optical illusion

### Revenue Quality Hierarchy

Higher quality revenue deserves a higher multiple:

| Tier | Revenue Type | Signal |
|------|-------------|--------|
| **Contracted** | Locked government/defense contracts, long-term contracted revenue with customer-funded CapEx | Highest quality — cancellation risk near zero, visibility years out |
| **Recurring** | Subscription/license revenue, royalty income, revenue-guaranteed agreements | Medium quality — stable but renegotiation risk exists |
| **Speculative** | One-time product sales, narrative-driven TAM projections, exploratory revenue | Lowest quality — apply uncertainty discount |

Within the Contracted tier, a critical sub-distinction: contracts where the customer funds the CapEx are categorically superior to contracts where the supplier absorbs CapEx. The margin structure of the contract matters as much as its existence.

When comparing companies at similar multiples, the one with higher-quality revenue is cheaper.

### Float and Dilution Dynamics

**Good dilution**: Issued above market price, zero or low interest, proceeds fund contracted growth commitments. This is growth capital.

**Bad dilution**: Issued below market price, high stock-based compensation as a percentage of revenue, no corresponding revenue growth. This is value destruction.

Track: shares outstanding change quarter-over-quarter, stock-based compensation as a percentage of revenue, real vs reported free cash flow. Also mark IPO lockup expiration dates — expect selling pressure.

### Priced-In Assessment

The core question: "Does this catalyst change forward revenue?" Then:

- If analyst consensus already incorporates the catalyst, it is partially or fully priced in
- If short interest is < 3% and analyst target gap is < 5%, likely fully priced in
- If forward P/E is at historical high for this growth rate, the growth premium is exhausted
- If the catalyst is known but the magnitude is uncertain, the direction is priced in but the magnitude is not

### Buyback as Asymmetric Signal

A company buying back its own shares signals management believes the stock is undervalued — they are putting skin in the game. The signal is stronger when:
- Insider buying accompanies the buyback program
- Free cash flow fully covers the buyback (no debt-funded buybacks)
- The buyback is executed at or below intrinsic value estimates

---

## Part C — Position Expression

### IV Tier Framework

Implied volatility percentile drives instrument selection — do not fight the vol regime:

| IV Percentile | Tier | Strategy |
|--------------|------|----------|
| < 30% | Compressed | LEAPS — cheap leverage on high-conviction thesis |
| 30-45% | Normal-Low | Shares or LEAPS depending on conviction level |
| 45-65% | Normal | Shares — no volatility edge in either direction |
| 65-85% | Elevated | Cash-secured puts — sell puts for better entry, collect premium |
| > 85% | Extreme | Covered calls on existing positions; no new long options |

The key insight: buying options when IV is compressed gives you the volatility expansion tailwind. Selling options when IV is elevated gives you the volatility compression tailwind.

### Position Sizing and Conviction

| Level | Size | Condition |
|-------|------|-----------|
| Starter | 1-2% | Thesis identified but not yet validated by data |
| Conviction | 3-5% | Valuation passes, health gates clear |
| High conviction | 5-7% | Bottleneck confirmed + catalyst timeline defined |
| Maximum | 7%+ | Generational opportunity, multiple independent confirmations |

Regime modifier: in risk-off environments, multiply all sizes by 0.5. Capital preservation overrides conviction.

### Option Income Strategy

**Cash-Secured Put (CSP)**:
- Sell at a price you would happily own the stock — the strike should be at or below the no-growth floor or funding price floor
- Only sell CSPs on stocks that pass the full valuation framework (V2)
- Margin leverage varies by underlying volatility: conservative leverage for high-beta names, more aggressive leverage for low-beta blue chips
- Do NOT sell CSPs during earnings week — the gap risk is asymmetric

**Covered Call (CC)**:
- Only on positions at or near fair value where you would accept assignment
- Never on positions with a near-term catalyst that could drive a breakout
- Strike selection formula: estimate the stock's typical daily positive move, multiply by trading days to expiry, add a buffer — this is the minimum OTM percentage for strike selection
- If the thesis is still in early innings, covered calls cap upside for minimal premium — avoid

**Duration**: Prefer 30-45 DTE for the theta decay sweet spot. Shorter duration for elevated IV; longer duration for compressed IV.

**Weekly Income Compounding**: For established positions with high conviction, systematic weekly option selling (CSP on names you want to own, CC on positions near fair value) compounds returns. The prerequisite is fundamental conviction — premium is collected on names you have independently validated, never on names selected for premium alone.
