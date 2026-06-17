# Run trace — NVDA "지금 사도 돼?" (Is X a buy? / timing route)

Routing applied: SKILL.md "Should I buy X now?" → discover (regime) → qualify X (cheap gate) → on AVOID, STOP (no deepen). Gate is the only binary verdict; no fundamental buys an exception. Added trend_template check ONLY to name the failing legs (gate constituent, not a deepen past a passed gate). Did NOT run the spine-four (vcp/volume/code33/rs score) because the hard gate failed — running them would be wasted work and a temptation to rescue a gate failure.

Reference files read first: References/spec.md (thresholds). principles.md not needed for a clean gate fail.

## Commands run (in order) + key live values

1. `python -m pipeline discover`  (FIRST command — regime)
   - market_verdict: **bull_late**
   - new_highs_vs_lows: 1.87 (highs 127 vs lows 68)
   - adv/decl: 59.4% / 35.9%; >50SMA 52.8%; >200SMA 50.4%
   - distribution_days_25d: 2 (secondary, not a gate)
   - spy_rs 61, qqq_rs 72
   - Leading industries: Metal Fabrication (95), Trucking (94), Semiconductor Equip & Materials (92), Electronics/Computer Distribution (91.5), Semiconductors (91.3 — leaders MXL/MU/INTC/VSH/AIP). NVDA NOT in any leader_tickers list.

2. `python -m pipeline qualify NVDA`  (Tier-0 hard gate)
   - verdict: **AVOID**, overall_pass: false
   - failed_gates: ["trend_template"]
   - stage_2 gate: PASS (current_stage = 2)
   - trend_template gate: FAIL, score 6/8 (required 8/8)
   - rs_rating: 69

3. `python modules/trend_template.py check NVDA`  (name the failing legs)
   - current_price: 207.45 (date 2026-06-17)
   - passed_count: 6/8
   - PASS: #1 px>150/200MA (207.45 vs 191.43/189.50); #2 150>200 (191.43>189.50); #3 200MA rising +1.90% 1mo; #4 50>150&200 (208.60); #6 +44.4% above 52w low 143.66; #7 -11.9% from 52w high 235.47
   - **FAIL #5**: Price > 50-day MA → 207.45 vs SMA50 **208.60** (just below)
   - **FAIL #8**: RS ≥ 70 → RS **69** (one point short)
   - MAs: sma50 208.60, sma150 191.43, sma200 189.50, sma200_1mo_ago 185.96
   - 52w high 235.47 / low 143.66

## Verdict delivered
AVOID / "지금은 아님(관망)". Failed legs = below 50-day MA (px 207.45 < 208.60) + RS 69 (<70). Stage still 2 (not broken, just cooling within trend). Stopped at the gate per doctrine; gave diagnostic re-entry conditions (reclaim 50DMA + RS back >70 + tight low-volume base) and explicitly left sizing/stops to the user.

Note: first modules/ call hit a doubled-path error (cwd already inside Scripts/); corrected to `modules/trend_template.py`.
