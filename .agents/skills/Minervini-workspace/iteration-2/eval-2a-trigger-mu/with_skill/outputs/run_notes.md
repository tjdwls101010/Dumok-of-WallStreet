# Run trace — MU "Should I buy now?" (timing path)

Path followed: discover (regime) -> qualify MU (cheap gate) -> PROCEED -> spine deepen (vcp, volume_analysis, code33, rs_ranking) -> bench (base_count, entry_patterns, stage_analysis risk) -> converge.

FIRST command run: `pipeline discover` (run in parallel with `pipeline qualify MU`).

## Ordered commands + key live values (date 2026-06-17 data)

1. `pipeline discover`
   - market_verdict: **bull_late**
   - new_highs 132 vs new_lows 74 (ratio 1.78); distribution_days_25d: 2
   - %above 50SMA 51.9 / 200SMA 50.1; adv 53.9% / decl 41.3%
   - spy_rs 61, qqq_rs 72
   - Sector ranking: Technology #2 (avg_rs 55.7)
   - Industry leadership: Semiconductors rank #5 (avg_rs 91.3), leaders include MU; Semiconductor Equip #3 (92.0)
   - MU appears in top_20 RS leaders (rs_rating 99)

2. `pipeline qualify MU`  -> **PROCEED**
   - stage: 2 (pass), trend_template: **8/8** (pass), rs_rating: 99
   - failed_gates: none

3. `modules/vcp.py detect MU` (SPINE setup)
   - vcp_detected: **false**; current_price 1036.67; pivot 1089.29 (price ~4.8% below pivot)
   - contractions_count 1; base_duration_weeks **1**; depth 21.57% (constructive zone, <25% ceiling)
   - pattern_type: **High Tight Flag**; pattern_quality none
   - setup_readiness: **13.0 / 100 -> "weak"**
   - relative_correction ratio **8.14** (stock 21.57% vs SPY 2.65%) -> excessive_relative true
   - pivot_tightness is_tight **false** (atr_ratio 1.29); pivot_area_dryup **false**; volume_confirmation neutral
   - breakout_volume_confirmed false

4. `modules/volume_analysis.py analyze MU` (SPINE demand)
   - accumulation_distribution_rating: **B+**; up/down vol ratio 50d 1.469, 20d 1.291
   - acc_days 13 / dist_days 7 (net +6); volume_trend "accumulation"
   - distribution_clusters: 1 cluster, **max_cluster_size 5 (cluster_warning true)**, 2026-05-12..06-05
   - breakout_volume_confirmation false; current vol 29.1% of 50d avg
   - climactic_days: none

5. `modules/earnings_acceleration.py code33 MU` (SPINE fundamental) -> **PASS**
   - eps_accelerating **true**; eps_growth_rates [682.05, 167.04, 156.78] (newest first)
   - sales_accelerating false BUT sales_qualifies **true** (basis strength_shallow; yfinance depth-limited)
   - margin_expanding **true** (net basis, full quality); net margin % [57.77, 38.41, 28.29, 20.27, 19.66] newest-first
   - data_quality: minimal (quarters_analyzed 1)

6. `modules/rs_ranking.py score MU` (SPINE leadership)
   - rs_rating **99**; spy_rs 61
   - history: 6m 94 -> 3m 98 -> 1m 98 -> 1w 99 (rising/strengthening)

7. `modules/base_count.py count MU` (BENCH — late/extended check)
   - current_base_number **2**; base_stage_assessment "**Early stage - optimal entry zone**"; risk_level moderate
   - base1 depth 20.3% (Cup), base2 depth 31.6% (Cup); cross_base correction_trend **deepening**
   - reset_detected false

8. `modules/entry_patterns.py scan MU` (BENCH — active trigger)
   - active_patterns: **[] (none)**; setup_readiness none

9. `modules/stage_analysis.py risk MU` (BENCH — character/sell-tell, recovery looked climactic)
   - largest_decline_since_stage2 -30.3% -> healthy_leader_band
   - climax_extension: **+44.4% above 50MA**, weeks_of_advance 10, climactic false (range not expanding)
   - character: **"egg"** (volatility_expanding true, near_recent_high false) — not "tennis_ball"

## Convergence verdict
4 of 5 streams strong (regime bull / Stage2+8-8 / RS99 rising / Code33 PASS); SETUP+TIMING leg BROKEN (no base, 1wk high-tight-flag, weak 13/100, no dry-up, dist cluster=5, +44% above 50MA, egg character, no active trigger, ~4.8% below pivot). AND-gate => **NO TRADE NOW / WATCH.** Buy trigger = proper tightening base + volume dry-up + volume-confirmed pivot breakout, with RS/Stage/regime intact.
