# Run notes — BE "지지선 회복 매수 신호, 지금 들어가도 되나?" (timing)

Date context: 2026-06-17/18 (live tools). Path = "Should I buy X now?" → discover → qualify → spine deepen (PROCEED) → entry trigger + bench risk → converge.

## Commands run (ordered) + key live values

1. `pipeline discover` (FIRST)
   - market_verdict = **bull_late**
   - new_highs_vs_lows = 1.78 (new_highs 132 / new_lows 74); distribution_days_25d = 2
   - breadth: %above50SMA 51.9, %above200SMA 50.1 (thin)
   - rs_leaders: spy_rs 61, qqq_rs 72; **BE present in top_20 board, rs 99**

2. `pipeline qualify BE`
   - verdict = **PROCEED**; Stage = 2; Trend Template = **8/8**; rs_rating = 99; failed_gates = []

3. `modules/volume_analysis.py analyze BE`
   - acc/dist grade = **B**; up_down_50d = 1.233; up_down_20d = **0.863** (recent selling)
   - distribution_clusters: cluster_warning = **true** (max cluster 5); acc_days 9 / dist_days 9 → net_acc_dist = **0**
   - breakout_volume_confirmation = false; 1 climactic up day (2026-04-14, +23.98%, 2.4x)

4. `modules/vcp.py detect BE`
   - vcp_detected = **false**; contractions = 1; base_duration_weeks = 1
   - setup_readiness = **15.2 / "weak"**; pivot_price 302.99; current 287.6
   - pivot_tightness.is_tight = false (atr_ratio 1.64); volume.pivot_area_dryup = false; volume_confirmation = neutral
   - relative_correction ratio = 6.69 (stock 17.79% vs SPY 2.66%) → excessive_relative = true

5. `modules/earnings_acceleration.py code33 BE`
   - code33_status = **PASS** but data_quality = **"minimal"**, quarters_analyzed = 1
   - eps_accelerating true; eps_growth_rates [1366.67, 4.65, -1600.0] (just turned profitable)
   - sales: sales_basis "strength_shallow", sales_data_quality "shallow", no YoY series
   - margin_expanding true (net), values_pct [9.41, 0.14, -4.45, -10.62, -7.3]

6. `modules/rs_ranking.py score BE`
   - rs_rating = **99**; spy_rs 61; history 1w/1m=99, 3m/6m=98

7. `modules/entry_patterns.py scan BE`  (user's "support reclaim" claim — directly checked)
   - active pattern = **SUPPORT_RECLAIM**, support/trigger = 254.83, reclaim_date 2026-06-17
   - **volume_surge_on_reclaim = false**; quality = "moderate"; setup_readiness = "developing"
   - NOTE: current price ~287-288 vs trigger 254.83 → already **~13% extended past the signal**

8. `modules/stage_analysis.py risk BE`
   - largest_decline_since_stage2 = **-45.9%**, band = **caution_exceeds_healthy_band**
   - climax_extension 13% above 50MA, climactic = false; character read = mixed

9. `modules/base_count.py count BE`
   - current_base_number 0; forming_base duration 3wk, correction_depth **28.6%** (high 322.83 / low 230.6); base_history empty

## Convergence (the call — no tool emits this)
Gate PASS (Stage2 + 8/8 + RS99 leader) BUT setup absent (no base, weak 15.2, no pivot tightness),
entry signal is low-conviction (support reclaim, NO volume) and ALREADY ~13% extended past trigger,
demand tilting to distribution (20d ratio 0.86, cluster warning, net acc/dist 0), earnings thin (minimal),
high volatility (-45.9% decline band caution). ≥3 streams broken → **NOT A BUY now = WATCH/관망, do not chase.**
Confirm: weeks-long base → volume dry-up → high-volume (≥1.25x) breakout through ~303 pivot.
Invalidation: forming-base low ~230 breaks on volume. No sizing/stop-order given (out of scope).
