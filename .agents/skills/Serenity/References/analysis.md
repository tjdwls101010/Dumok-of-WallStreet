# Analysis — Discover · Evaluate · Size · Enter

The depth behind funnel steps 1, 3, 4, 5. The pipeline (`analyze TICKER`) gives you the quantitative substrate at every step — **don't recompute it; interpret and override it.** Examples here are *archetypes* (shapes to recognize), not picks. All expressions are US-listed; when the real winner is foreign-only, name it honestly and pivot to the US substitute.

---

## §1 — Discovery: generating candidates

When the user hands you a ticker, skip to §2. When they give a theme, a sector, or "what should I look at," this is the engine. The pipeline analyzes a ticker; it can't *find* one — discovery is pure agent work (WebSearch + SEC reading + tracing). Goal: surface the smallest-MC, least-covered node the chain structurally depends on, then feed it to `analyze`.

### Trace the chain (the spine)
Follow the money flow **down** from the end-product: end-product → integrator/OEM → major components → sub-components → raw materials → equipment → feedstock/chemicals. At each layer ask: how many suppliers, lead time for new capacity, geographic concentration, % of end-product cost, substitutes? The deepest layers carry the thinnest coverage and the most mispricing — analysts covering the end-product rarely look past the major components.

**Recursive hop (the core move):** when you find a bottleneck, ask "what does *this* company depend on?" and trace one hop further. A vertically-integrated-*looking* supplier may still buy one critical input from a single outside source — that source is the deeper bottleneck. *(Archetype: a $700M substrate maker the whole AI buildout leans on turns out to buy a high-purity precursor from one chemical firm a tenth its size.)*

### Five tacit techniques (non-obvious — where the alpha hides)
- **SEC competitor-list mining**: a known winner's 10-K lists its competitors. That list is a vetted candidate pool of smaller, earlier names in the same chain. *(A leading optics maker's filed competitor list, read years early, held several names that later 20×'d.)*
- **Analyst-report gap**: read institutional reports for the *omission* — the supplier clearly in the chain but NOT on the list. "Institutions haven't found it yet" is exactly where the highest returns are; the names *on* the list are already priced.
- **Re-rating anomaly**: a whole ecosystem up hundreds of percent but one *critical* node still flat/small = the undiscovered gem. Ask why it hasn't moved — usually coverage gap, not a flaw.
- **Second-order beneficiary**: from a catalyst, trace who supplies the supplier that just maxed out. *(A transceiver maker's demand blowout → the epi-reactor makers it must now buy from go from afterthought to bottleneck.)*
- **Convergence-find**: list the obvious players in a theme, then ask "which single company do *most* of these rely on?" That common dependency is often the real chokepoint.

(For undisclosed defense/national-security chains: match a prime's new-program specs — ruggedization, temperature range, edge-AI — to small-caps announcing contracts with an unnamed "leading defense" customer.)

### Track the signal, not the price
Information propagates in order: supply-chain derivative signals (commodity spot, procurement, utilization) → paid industry reports → public news → repricing → earnings confirmation. **Edge is proportional to how early you observe.** Earnings confirmation is the *end* of the chain — by then the move is mostly done. Ask: "what is the earliest publicly observable signal that would confirm or deny this thesis?" and watch *that*.

### Discovery discipline
You'll go through *tens* and reject most — sounding "good" (a real chokepoint) is not the bar; passing the §2 winner-gates is. Don't fall in love with a name because you found it. And **US-listed filter**: discovery often surfaces foreign small-caps — name the real winner, then run the US-accessible expression (ADR, meaningfully-weighted ETF, or nearest US-listed analog) through `analyze`.

---

## §2 — Winner-gates: chokepoint ≠ winner

The pipeline gives `bottleneck_pre_score` (5 criteria) + SEC supply-chain entities — that answers **"is this a bottleneck?"** Your harder job: **"is it an investable winner, or just a chokepoint?"**

### Step 1 — Is it a real bottleneck? (pipeline scores; you sanity-check)
Classify the supply limitation — only one of three supports a multi-year thesis:
- **Bottleneck** — physical scarcity capital alone can't fix, concentrated, durable pricing power → multi-year conviction.
- **Constraint** — resolvable with enough capital + time, transient pricing power → tactical trade only.
- **Risk** — a probabilistic event, not a structural state → hedge, don't build.

Boundary test: **"Can money solve this?"** If any amount of capital, given time, removes the scarcity, it's a constraint, not a bottleneck. *Physics trumps capital.* A true bottleneck meets all three pre-score criteria: demand outstripping supply · oligopoly/monopoly · no substitute before demand peaks.

### Step 2 — Is the bottleneck a WINNER? (pure judgment — pipeline can't)
A confirmed chokepoint is investable only if it clears these gates. Each doubles as a bear-case generator.

1. **Monetization** — does the position translate to *revenue + FCF*? Being a critical materials bottleneck ≠ money in the door. Demand a forward revenue ramp you can model. *(A name "critical to the chain" that can't bill for it is a fascination, not an investment.)*
2. **Pricing realization (behavioral, not just structural)** — having pricing power ≠ exercising it. A sole-source supplier whose culture/structure *won't* hike prices captures none of the upside. *(A sole-source feedstock maker that never raises price caps near book value — an 85% move, not the 5× a price-hiking equivalent delivers.)* Ask not "can they raise price?" but "will they?"
3. **Survival to the ramp** — can the balance sheet last until monetization? A genuine chokepoint whose debt exceeds its market cap, or that's months from dilution-to-zero, is not investable however critical. *Interesting in the supply chain ≠ a good long.* (Pipeline `debt_health`/`dilution` flag the quant; you read the SEC context — is the raise contract-backed growth, or value destruction?)
4. **TAM expansion / value migration** — a static chokepoint with a tiny TAM caps the return. Winners use the position as a launchpad: expand downstream into more of the stack, then integrate upstream for margin. *(A supplier that only sells the raw component is capped; one that grows into the whole subsystem, then the fab, re-rates many-fold.)*
5. **Allocation control = synthetic bottleneck** — you needn't be the physical sole-source. Control multi-year *output allocation* and you *become* the bottleneck with its pricing power. *(When buyers fight over your finished-good capacity, you're the chokepoint — even if someone upstream "makes" the raw input.)*
6. **Demand breadth / inelasticity** — selling to *every* player (sector-agnostic, inelastic like yield/test/inspection) beats serving one customer on a dev contract: you win regardless of which end-product prevails, and can charge what you like.

### The 3-dimensional graph (where the gates get evidence)
- **Physical** — BOM, bottleneck, criticality tier. (the obvious dimension)
- **Financial** — debt/credit contagion travels *different* routes than product flow. Two peers with identical customers can have opposite exposure by balance-sheet structure. "If the sector leader's credit cracks, does it reach this name through its debt?" (gate 3)
- **Strategic** — who structurally *needs* this company to succeed? A larger entity whose position depends on a smaller one will backstop it — an invisible floor that changes the downside. An active co-development partner (hyperscaler, defense prime) with prior capability transfers it, dropping execution risk below what standalone analysis suggests.

**Comparative principle**: within a sector, not "is this a bottleneck?" but "which is the *best* one?" Rank on integration depth (full-stack > capacity-only), margin quality, contract visibility, balance-sheet strength. **Inverse-proxy validation**: a well-funded competitor's *failure* to replicate is the strongest evidence of moat depth — "who tried this and failed, and what does that reveal?"

### The designed-out test (this IS kill signal #9 — keep it in the bear case)
Designing a supplier *in* is gradual; designing it *out* is one customer decision. Does the position rest on **physical inevitability** (no alternative material/process exists) or **current convenience** (best option now, but alternatives could be built)? Physics-based positions are durable; convenience-based ones are fragile. Every bottleneck thesis must answer: "what if the customer designs us out?"

---

## §3 — Valuation

The pipeline computes forward P/E (1y/2y), PEG, and the **dual valuation** (no-growth floor + growth upside). Interpret, don't recompute.

- **Dual valuation, floor first**: present the no-growth floor (where it trades if growth stopped tomorrow) BEFORE the upside. The *gap* is the asymmetry; a name near its floor with visible catalysts is the ideal setup. (Pre-revenue: floor is inapplicable — say so, make the growth case primary, apply a larger uncertainty discount.)
- **Forward P/E gate — it's PEG, not a P/E number**: the gate measures P/E *relative to growth*. <15× at 50% growth "screams" because PEG ≈ 0.3 — you're paying a third of the growth rate, i.e., the market hasn't priced the trajectory. That generative point explains the rest: a high *absolute* P/E is not a reject (30–40× at 60%+ growth is still cheap on PEG — the biggest winners lived there), and a *low* P/E can be a trap (12× at 5% growth is expensive). Avoid = above sector comp at *decelerating* growth, regardless of narrative. (Pipeline gives forward P/E + PEG; you judge the peer set — build a custom one for hyper-growth with no clean comp.)
- **When the framework breaks**: strategic monopolies in existential chains, policy-mandated demand, and paradigm-shift growth resist P/E and P/S. When conventional valuation returns an absurd result (a monopoly substrate maker priced at commodity multiples), *say the framework is failing* rather than forcing false precision. Anchor instead on subsidy scale, policy-mandated TAM floor, the strategic value of irreplaceability.
- **Revenue quality** (a higher-quality dollar deserves a higher multiple): contracted (especially *customer-funded* CapEx) > recurring > speculative. At equal multiples, the higher-quality revenue is cheaper.
- **Earnings quality** (pipeline flags most — `cockroach_effect`, `real_fcf`): consecutive beats = execution validated; revenue acceleration > EPS acceleration = healthy organic growth; reported FCF positive but real FCF (after SBC) negative = optical illusion.
- **Funding price floor**: a recent (<6mo), significant (>5% of MC), strategic investment is a soft floor — institutions did diligence there and defend it. Probabilistic; fails in broad distress.

---

## §4 — Cycle stage → sizing

The pipeline gives `capex_flow.direction`, earnings momentum, `margins.flag`, and a `position_guidance` size. But **where in maturation** a name sits — and how much to concentrate — is your call.

### The 5-stage cycle
| Stage | What you see | Return profile | Concentration |
|---|---|---|---|
| ① Guess the next bottleneck | not yet qualified; public info only | highest magnitude, lowest probability | **<2%** (lottery tickets) |
| ② Qualified, no order ramp | in the chain, no volume yet | **highest returns** — but live designed-out risk | small ("less") |
| ③ Inflection, early | earnings + extreme projections; the easy point | large | "quite a bit" if high conviction |
| ④ Inflection, mid-cycle | ramping, confirmed, "can't fight the earnings" | smaller but obvious (another ~100%) | **MOST** |
| ⑤ End / structural | revenue cliff, or structural compounder | low / negative | compounder hold, or exit |

### The sizing correction (subtle and important)
Naively you'd concentrate where *probability-adjusted return* peaks (≈ stage ②, qualified-but-not-repriced). **That's wrong.** Magnitude peaks at ②, but **concentration peaks at ④** — the confirmed, ongoing ramp. The gap is the *binary designed-out risk* you refuse to over-size into. Take *small* high-asymmetry bets early (②); put the *bulk* of capital where earnings are de-risking the thesis quarter after quarter (④). This is risk-adjusted sizing, not EV-maximizing — you trade some magnitude for a thesis the earnings actively validate.

### Stage migration is the hold thesis
A name migrates ②→③→④, and that migration IS why you hold through an ugly stretch. *(A buildout-phase name burning capital is a ②/③; once the spend converts to FCF, it's a ④ — holding through the capex phase is the whole thesis.)* Enter ~8–12 months *before* an inflection — a bottleneck two years out is dead money now; re-enter closer to the ramp.

### Power-law allocation
Why power-law and not equal-weight? Because *returns* are themselves power-law distributed — a few names drive almost all the alpha — so allocation should mirror the return distribution: concentrate where conviction × evidence is highest (that's where the asymmetry lives), and run 15–25 satellites at 0.2–2% as cheap optionality, where even a 2% stake that 10×'s still moves the book. Equal-weighting throws away your conviction signal. So: 3–5 core hold 60–80%; position size IS the conviction signal; a new core that dilutes an existing core must clear a *higher* bar (you're trading proven conviction for a hypothesis); satellites add freely. (Pipeline's `position_guidance` + `regime_adjustment` is the starting number — scale by cycle stage and conviction. In risk-off, halve all sizes; capital preservation overrides conviction.)

---

## §5 — Fear vs Fundamental: the entry

V1 says buy fear-driven dips — but V1 *alone* catches falling knives. When a name you'd own drops hard, run the discrimination **before** responding, and respect the guardrail.

### "Falling knife or dip-buy?" — the 4-step
The pipeline flags candidates via `absence_evidence_flags.no_fundamental_change_selloff → potential_entry`; you *validate* it:
1. **Identify the mechanism** (V10): mechanical/sentiment — MM hedging / option-pinning, algo misreading a one-time tax charge, margin-liquidation cascade, sector contagion by association, tax-loss harvesting, retail panic — or a *real* fundamental change? Tell: mechanical drops reverse when the switch flips, and their magnitude is disconnected from any real news.
2. **Prove the math** — does the scary headline actually hit the numbers? If it's *bad math* (an energy spike denting margins <2% on a 60%-margin oligopoly; a "displacement" physically impossible mid-cycle), the gap between fundamentals and price *is* the trade. "If margins were genuinely threatened, the selloff would be justified."
3. **Institutional-accumulation tell** (V8): in a true fear-dip, institutions accumulate *into* the drop — IO% rising, dark-pool prints — while retail panic-sells. (Pipeline `institutional_quality`; 13F lags, so corroborate.)
4. **Clear the kill signals** (§6): if a real one fired — designed-out, dilution, sector-price crash, CapEx cancellation, restatement — it is NOT a fear-dip. Step aside.

### The V1 guardrail (the lesson written in losses)
Even when the discrimination says "buy," **fear overshadows fundamentals short-term — you'll be right *and* early.** So scale in slowly, never on margin in a high-fear tape, and expect to bleed before vindication. The repeated, confessed mistake is conviction-without-the-right-vehicle: catching the knife with shares instead of getting paid to wait.

### Expression — let IV choose the vehicle
The pipeline classifies `iv_tier` and suggests a vehicle. The discipline:
- **Compressed IV + high conviction → LEAPS** (cheap leverage + the IV-expansion tailwind). Also the move on low-IV sector/index ETFs you believe are directionally going up.
- **Elevated IV (the fear-dip default) → cash-secured puts**: sell a put at a strike you'd happily own — assignment = bought at target + premium; no assignment = paid to wait. The fat premium *is* the fear's volatility, harvested. CSP > knife-catching shares whenever IV is elevated; shares are the exception (extreme drops, or low IV).
- **Extreme IV → covered calls** on names you already own (sell premium, don't buy long options).
- Rules: only on names that pass the full framework (a strike you'd own); never sell CSPs into earnings week (gap risk); size leverage by beta. TA (support/resistance) informs *where* to enter a validated name — never *whether*.

---

## §6 — Kill Signals

A kill signal isn't "the price dropped" — it's anything that **breaks a load-bearing assumption of the thesis** or **flips the risk asymmetry** so downside now structurally exceeds upside. *That definition is the point:* the nine below are the recurring instances, but you spot a *novel* one (#10) by the principle, not the list. And the response falls out of *which kind* it is — a broken core assumption means the thesis is gone (exit, no trim); a mechanical, quantifiable, recoverable pressure means reduce/hedge and wait. The pipeline's `health_gates` catch several quantitatively; this is the watchlist your bear case monitors.
1. **MC/valuation disconnect** — no revenue/earnings path anchors the price → exit, no partial trim.
2. **Suspicious fundamentals** — restatement, auditor change, revenue-recognition anomaly → exit immediately; the asymmetry flips.
3. **Meme trap** — price fully decoupled from any thesis → trim to zero; no longer analyzable.
4. **Lockup expiration** — insider incentive to sell into the unlock → reduce/hedge; model the overhang.
5. **Inverse Cathie Wood** — ARKK accumulation as a hype-peak warning → tighten discipline, re-examine the bear case (not an auto-exit).
6. **Sector-collapse signal** — the chain's leading indicator crashes (NAND/DRAM spot for memory, fab utilization for semis) → reassess the *whole* chain.
7. **CapEx cancellation** — a downstream customer cancels/delays CapEx that was a key revenue assumption → if >20% of your forward model, the thesis may be broken.
8. **Serial dilution history** — management with a track record of value-destroying ATM raises → exit on first dilution; the behavioral pattern is the signal.
9. **Designed-out** — the customer develops an alternative, a cheaper source emerges, or a tech shift removes the need. The position rested on *convenience*, not physical inevitability → exit; this is the §2 bear case firing.

---

## §7 — Conviction dynamics & management

Conviction is a continuous variable (V9), not binary — manage it.
- **Strengthening**: a high-conviction name drops with NO kill signal → asymmetry rose. Re-check every kill signal; if all clear and the cause is mechanical (§5), scale up one tier. *Not* blind averaging-down — one ambiguous kill signal and you don't escalate.
- **Erosion**: no kill signal fires, but no catalyst materializes either. At ~2× the expected catalyst timeline, force a re-examination; if the thesis holds but urgency faded, cut to satellite size; if you can't re-articulate it with fresh conviction, exit. Zombie positions held by inertia dilute alpha (V7).
- **Thesis inheritance**: when a thesis wins, its transferable pattern (formation, sector dynamics, customer profile, margin structure) is a *hypothesis* for similar names — but each must independently pass the §2 gates. Inheritance accelerates discovery; it never bypasses validation.
- **Post-mortem** (every loss): classify — (A) right thesis, wrong timing → adjust horizon; (B) partially wrong → find the blind spot; (C) fully wrong → what evidence did you misread; (D) process error (sizing, vehicle, ignored kill signal) → fix the process.

Underneath all of it, one filter (V2): **"does this change forward revenue?"** If no, it's noise — ignore it regardless of headline volume. And every conviction long carries an explicit bear case; if you can't articulate it, you don't understand the position well enough to hold it.
