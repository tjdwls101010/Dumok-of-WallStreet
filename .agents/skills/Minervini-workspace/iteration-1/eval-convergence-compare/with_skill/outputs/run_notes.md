# Run trace — MU vs AAPL ("which is better to buy now?")

Date executed: 2026-06-17. Venv: .agents/skills/Minervini/Scripts/.venv/bin/python
All tools run LIVE from Scripts/ dir. Funnel order: discover → qualify each → spine deepen survivors → bench → converge.

## Ordered commands + key live values

1. `pipeline discover`  (RAN FIRST — regime)
   - market_verdict = **bull_late**
   - breadth: new_highs 127 / new_lows 68 (ratio 1.87); adv 59.4% / decl 35.9%; >50SMA 52.8%; >200SMA 50.4%
   - distribution_days_25d = 2 (secondary)
   - spy_rs 61, qqq_rs 72
   - top-20 RS leaders (RS99) INCLUDE **MU** (rs_raw 3.80); AAPL absent
   - leadership board top: Metal Fab RS95, Trucking 94, **Semiconductor Equip & Materials 92**, Electronics/Computer Dist 91.5, **Semiconductors 91.3**, Electronic Components 90.6 → semis leading; AAPL's consumer-electronics group not in top tier

2. `pipeline qualify MU` → **PROCEED**; Stage 2 ✅, Trend Template 8/8 ✅, RS 99
3. `pipeline qualify AAPL` → **PROCEED**; Stage 2 ✅, Trend Template 8/8 ✅, RS 70 (bare floor)

   (both passed hard gate → both earned spine deepen)

### Spine — MU
4. `modules/vcp.py detect MU`
   - vcp_detected false; contractions 1; pattern "High Tight Flag"; setup_readiness **13/100 (weak)**
   - current 1036.5, pivot 1089.29; first_correction 21.6% (constructive zone but rel-corr ratio 8.14, excessive_relative true); base 1wk; pivot not tight; volume_confirmation neutral
5. `modules/volume_analysis.py analyze MU`
   - grade **B+**; up/down 50d **1.466**, 20d 1.285; trend accumulation; net_acc_dist +6 (acc13/dist7); cluster_warning true (5-day dist cluster May12–Jun5); breakout_volume_confirmation false
6. `modules/earnings_acceleration.py code33 MU` → **PASS**
   - EPS accelerating true; eps_growth_rates (newest-first) [682.05, 167.04, 156.78]
   - sales_qualifies true (strength_shallow, shallow data)
   - margin_expanding true (net, full): [57.77, 38.41, 28.29, 20.27, 19.66] %
7. `modules/rs_ranking.py score MU` → RS **99**; spy_rs 61; history 6m→now 94→98→98→99 (rising/sustained)

### Spine — AAPL
8. `modules/vcp.py detect AAPL`
   - vcp_detected false; contractions 1; pattern "Power Play"(quality none); setup_readiness **18/100 (weak)**
   - current 299.18, pivot 317.40; first_correction 9.5% (shallow); rel-corr ratio 5.06; pivot not tight; volume_confirmation neutral
9. `modules/volume_analysis.py analyze AAPL`
   - grade **B+**; up/down 50d **1.315**, **20d 0.956 (<1.0)**; recent 20d heavy_dist 7 vs heavy_acc 3; cluster_warning true (Jun1–Jun9); breakout_volume_confirmation false
10. `modules/earnings_acceleration.py code33 AAPL` → **FAIL**
    - EPS accelerating false (decel): [21.82, 18.33, 90.72] newest-first
    - sales_qualifies false; margin_expanding false: [26.6, 29.28, 26.8, 24.92, 25.99] %
11. `modules/rs_ranking.py score AAPL` → RS **70** (floor); spy_rs 61; history 6m→now 73→56→73→72→70 (fading/choppy)

### Bench (late-base / character risk)
12. `modules/base_count.py count MU` → current_base_number **2**, risk_level **moderate**
13. `modules/stage_analysis.py risk MU` → largest_decline_since_stage2 **-30.3% (healthy_leader_band)**; +44.4% above 50MA; climactic false; character **egg** (volatility expanding)
14. `modules/stage_analysis.py risk AAPL` → largest_decline **-13.8% (normal_pullback)**; +3.9% above 50MA; climactic false; character **egg**

## Convergence (analyst's call — no tool emits this)
- MU: regime ✅ + stage/TT ✅ + leadership ✅(99) + fundamental ✅(Code33 PASS, EPS+margin accelerating) = 4 streams aligned; ONLY gap = setup/timing (no built base, mid-pullback, readiness 13, egg). → strong WATCH, not chase today; trigger = completed base + dried-up pivot + volume-confirmed breakout.
- AAPL: stage/TT ✅ but leadership weak (RS70 fading) + fundamental FAIL (EPS decel) + recent 20d distribution (0.956). Streams broke alignment. → NOT a new-buy candidate (familiar mega-cap past its acceleration phase).
- Verdict: MU clearly the better of the two; neither is a buy-it-now. AAPL fails the convergence.

NOTE: SKILL command run FIRST = `pipeline discover`.
