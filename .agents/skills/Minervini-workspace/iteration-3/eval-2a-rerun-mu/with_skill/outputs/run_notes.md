# Run notes — MU "지금 진입해도 되는 자리?" (timing call)

Venv: `.agents/skills/Minervini/Scripts/.venv/bin/python`, run from `Scripts/` dir.
Date context: 2026-06-18 (data "date" field = 2026-06-17).

## Ordered commands run + key live values

1. **`pipeline discover`** (regime — SPINE, run FIRST alongside qualify)
   - market_verdict = **bull_late**
   - breadth: new_highs 194 / new_lows 171 (NH/NL ratio 1.13); above 50MA 47.5%, above 200MA 48.3%; adv 32.9% / decl 62.6%
   - distribution_days_25d = 2 (secondary, not gate)
   - rs_leaders: spy_rs 60, qqq_rs 72; **MU in top_20 (rs_rating 99)**; group peers SNDK/WDC/STX all 99

2. **`pipeline qualify MU`** (cheap hard gate — SPINE, FIRST)
   - verdict = **PROCEED** (overall_pass true, failed_gates [])
   - stage_2 = passed (current_stage 2)
   - trend_template = passed **8/8**
   - rs_rating = 99

3. **`modules/vcp.py detect MU`** (setup — SPINE)
   - **vcp_detected = false**; contractions_count 1; base_duration_weeks 1
   - current_price 1043.19; pivot_price 1089.29 (price ~4% BELOW pivot)
   - correction_depth 21.57% (first_correction_zone constructive but relative_correction ratio 8.14 vs SPY 2.65% → excessive_relative true)
   - pattern_type "High Tight Flag", pattern_quality none
   - setup_readiness score 13.0 → classification **weak**
   - pivot_tightness.is_tight false; pivot_area_dryup false; breakout_volume_confirmed false
   - power_play / cup_and_handle / cheat all false; shakeout count 0

4. **`modules/volume_analysis.py analyze MU`** (demand — SPINE)
   - accumulation rating **B+**; up_down_vol_ratio_50d 1.499, 20d 1.359
   - volume_trend accumulation; net_acc_dist +5 (acc 12 / dist 7)
   - breakout_volume_confirmation = false
   - **distribution cluster warning = true** (5-day cluster 2026-05-12→06-05)
   - volume_vs_50day_avg 89.1%

5. **`modules/earnings_acceleration.py code33 MU`** (fundamental quality — SPINE)
   - **code33_status = PASS**
   - eps_accelerating true; eps_growth_rates (newest-first) [682.05, 167.04, 156.78]
   - margin_expanding true (basis net, full quality); margin_values_pct [57.77, 38.41, 28.29, 20.27, 19.66]
   - sales_qualifies true via strength_shallow fallback (yfinance revenue depth shallow; sales_growth_rates [])
   - data_quality minimal (quarters_analyzed 1) — note caveat

6. **`modules/rs_ranking.py score MU`** (leadership — SPINE)
   - rs_rating 99; spy_rs 60
   - history: 1w 99, 1m 98, 3m 98, 6m 94 (steady leadership, no divergence)

7. **`modules/actions.py get-earnings-dates MU`** (event-risk check for timing call — BENCH/critical)
   - **Next earnings: 2026-06-24 (6 days out)** — EPS estimate 19.69, reported null
   - Beat history: 2026-03-18 +33.21%, 2025-12-17 +20.58% surprise (cockroach pattern)

8. **`modules/entry_patterns.py scan MU`** (active trigger check — BENCH)
   - active_patterns [] → **pattern_count 0**, classification none (no live entry trigger)

9. **`modules/base_count.py count MU`** (lateness check — BENCH)
   - current_base_number 2 → base_stage_assessment "Early stage - optimal entry zone", risk_level moderate
   - cross_base correction_trend "deepening" (20.3% → 31.6%) — mild late-stage caution
   - no reset detected

## Convergence (analyst's call, no tool emits it)
- Regime bull_late (thin breadth) — hunting allowed but selective. ✓-ish
- Gate (stage+TT): PASS ✓
- Setup: **FAIL to converge** — no base, vcp false, weak readiness 13, price below pivot, no dryup, dist cluster, 0 active triggers. ✗
- Fundamental: PASS (Code33, EPS 682% YoY, margin 5q expansion) ✓
- Leadership: PASS (RS 99, top-20, group leadership) ✓
- **Event risk:** earnings in 6 days = unhedgeable binary; fresh entry must wait for the reaction.

→ Three+ streams strong but **setup does not converge** + imminent print → **verdict: WATCH / do not chase now.** Buy trigger = post-6/24 reaction → new 2–6wk base with volume dry-up → high-volume breakout above a clean pivot while RS stays 99.
