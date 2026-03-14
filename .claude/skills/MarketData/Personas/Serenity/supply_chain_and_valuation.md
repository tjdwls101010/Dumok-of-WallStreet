# Supply Chain, Valuation, and Position Expression

What to evaluate when analyzing a company. Bottleneck discovery, valuation, and position expression flow as one continuous process: find bottleneck, check moat via margins, value, choose instrument.

---

## Part A — Bottleneck Discovery

### True Bottleneck 3-Criteria

Not every bottleneck provides a great investment opportunity. All three must be met simultaneously:

1. **Demand/supply ratio >= 2:1** — provable through order backlogs, lead times, or capacity utilization data
2. **Oligopoly or monopoly** — top 3 players hold > 70% market share
3. **No viable substitutes within 18 months** — no competitor announcements, no capacity expansion plans, no substitute R&D in the pipeline

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

The deepest layers (4-6) often have the least analyst coverage and the most mispricing.

### Recursive Tracing — Bottleneck within Bottleneck

After finding a bottleneck at Layer N, ask: "What does THIS company depend on?" Trace upstream recursively until you reach the deepest constraint. The deepest bottleneck often has the most pricing power and the least market attention because analysts covering the end product rarely look past Layer 2.

### Moat Validation

Three tests, applied in sequence:

1. **Margins > Capacity** — high gross/operating margins prove pricing power exists NOW. Capacity utilization data shows whether it persists. If margins are expanding while utilization is near peak, the moat is strengthening.

2. **Oracle Test** — "If Oracle (or the best-funded competitor) tried to build this in-house, how long and how much?" If the answer is > 3 years and > $1B, the moat is real. Shorter timelines or lower capital requirements mean the moat is shallow.

3. **Picks & Shovels Test** — Does the company sell tools or materials to ALL players in the space? If yes, the moat is sector-agnostic: the company wins regardless of which end-product competitor prevails.

### Absence Evidence (Negative Space)

"Who else could do this?" If the answer is "nobody" or "it would take > 18 months," that absence IS the evidence of a moat. Specifically check:
- No competitor capacity expansion announcements
- No substitute technology in development pipeline
- No regulatory pathway for new entrants
- Patent or licensing barriers with remaining life > 5 years

### Geographic and Geopolitical Risk

Single-country production concentration creates both premium and risk:
- Export controls or sanctions can create instant monopolies for alternative suppliers
- Tariff exposure can shift relative cost structures overnight
- Track: production percentage by country, policy trajectory, ally/adversary alignment

Geopolitical risk is asymmetric — it can destroy a thesis instantly but can also create once-in-a-decade entry points for beneficiaries.

### Historical Analogs for Bottleneck Pricing

When a bottleneck is confirmed, search for historical parallels in other supply chains. The recurring pattern:
1. Initial price spike as shortage becomes apparent
2. Demand destruction attempt by end-product makers
3. Failed substitution — alternatives prove inadequate or too slow
4. Permanent re-pricing at a structurally higher level

Use analogs to estimate pricing trajectory and duration. The analog does not predict, but it calibrates expectations.

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

1. Locked government/defense contracts (cancellation risk near zero)
2. Long-term contracted revenue
3. Recurring subscription/license revenue
4. Interest/royalty income
5. One-time product sales
6. Narrative-driven "TAM" projections

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

### Covered Call and Cash-Secured Put Rules

**Cash-Secured Put (CSP)**:
- Sell at a price you would happily own the stock
- Strike selection: no-growth floor value or funding price floor — whichever is lower
- Only sell CSPs on stocks that pass the full valuation framework

**Covered Call (CC)**:
- Only on positions at or near fair value where you would accept assignment
- Never on positions with a near-term catalyst that could drive a breakout
- If the thesis is still in early innings, covered calls cap your upside for minimal premium

**Duration**: Prefer 30-45 DTE for the theta decay sweet spot. Shorter duration for elevated IV; longer duration for compressed IV.
