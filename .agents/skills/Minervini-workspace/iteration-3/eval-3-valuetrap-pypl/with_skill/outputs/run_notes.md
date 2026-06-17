# Run trace — PYPL value-trap check

Date of run: 2026-06-18 (data dated 2026-06-17)

## Funnel path
discover (regime) + qualify (cheap hard gate) run in parallel FIRST → AVOID at gate → did NOT deepen the spine (correct per doctrine; a failed hard gate stops the funnel). Ran 3 diagnostic bench reads to substantiate the value-trap thesis on an already-rejected name.

## Commands run, in order

1. `python -m pipeline qualify PYPL`  **(FIRST gate command)**
   - verdict: **AVOID**
   - failed_gates: stage_2, trend_template
   - current_stage: **4** (required 2)
   - trend_template_score: **0/8** (required 8/8)
   - rs_rating: **12**

2. `python -m pipeline discover` (regime, parallel with #1)
   - market_verdict: **bull_late**
   - new_highs 194 vs new_lows 171 (ratio 1.13); distribution_days_25d: 2
   - SPY RS 60, QQQ RS 72
   - leadership: semis / metal fab / trucking / precious metals lead; Credit Services industry avg_rs only ~62 (PYPL not a leader in its group)

3. `modules/trend_template.py check PYPL`
   - current_price: **42.08**
   - SMA50 45.80, SMA150 50.19, SMA200 54.67; SMA200 1mo ago 57.32 (-4.63%, falling)
   - 52w high 77.55 / 52w low 38.83
   - price -45.7% from 52w high; only +8.4% above 52w low
   - all 8 criteria FAIL; RS score **12**

4. `modules/stage_analysis.py risk PYPL`
   - largest_decline_since_stage2: **-49.9%** → band "caution_exceeds_healthy_band"
   - climax_extension: -8.1% below 50MA, not climactic
   - character read: mixed

5. `modules/earnings_acceleration.py valuation PYPL`
   - forward_pe_1y **7.9**, forward_pe_2y **7.3** (contracting=true)
   - eps_growth_rate_used_pct **-0.1%**
   - revenue_growth_yoy_pct **+4.2%**
   - gross_margin_pct 40.93
   - PEG: null

## Convergence verdict
AVOID / not a buy. Hard gate fails on TWO legs (Stage 4, not Stage 2; trend template 0/8). RS bottom-decile (12). Cheap fwd P/E (~7.9) sits against ~0% EPS growth + 4.2% revenue growth = textbook value trap. No deepening of vcp/volume/code33/rs spine since the gate already disqualified — surfacing those would be a rescue attempt the doctrine forbids. Diagnostic reads (#3–5) only confirm the broken-leader / value-trap read.
