# Minervini skill — iteration-1 eval (with-skill vs no-skill baseline)

Date: 2026-06-17. Both arms Opus, launched same turn (timing parity). Baseline = general
investing knowledge + raw yfinance, no skill scripts/doctrine. 3 cases × 2 arms.

## Token / latency profile
| case | arm | tokens | dur(s) | tools |
|---|---|---|---|---|
| gate | ws | 53.3k | 117 | 10 |
| gate | bl | 30.3k | 156 | 17 |
| disc | ws | 66.8k | 274 | 14 |
| disc | bl | 36.7k | 226 | 22 |
| conv | ws | 56.4k | 209 | 22 |
| conv | bl | 28.8k | 144 | 12 |
With-skill ≈ 1.5–1.8× baseline tokens (skill load + deeper, ordered tool chain). Acceptable.

## Verdict per case — with-skill PASSED every assertion; baseline failed the predicted modes

### 1. gate-fail-diagnosis — "엔비디아 지금 사도 돼?" (NVDA: gate FAIL, TT 6/8, RS 69)
- **ws (PASS 7/7):** discover→qualify first; verdict AVOID; named both failing legs (price $207.45<50DMA $208.60; RS 69<70); refused fundamental rescue ("관문은 펀더멘털이 아무리 좋아도 예외를 사주지 않습니다"); risk-first; applied don't-buy-what-you-know; declined sizing; cited live numbers. Bonus synthesis: tied RS<70 to NVDA's absence from the leadership board.
- **bl (FAIL):** verdict **BUY** ("장기 보유면 예, 단 분할로"); led with fundamentals + analyst target $298.9 (+44%) + forward PE; **prescribed sizing + stops** ("3~4번 나눠 분할 매수", "손절 라인 -10~15% 또는 200일선 이탈", "비중 과하게 두지 마세요"). The fundamentals-rescue + sizing failure modes, exactly.

### 2. discovery — "지금 뭐 살 만한 거 없어?"
- **ws (PASS 6/6):** regime-first (bull_late, breadth/leadership; distribution days noted only as secondary nuance — correction-A compliant); surfaced **unfamiliar** leaders (SNDK/WDC/AXTI/AEHR/ICHR/CRS/KALU/MXL); gated all (Stage2+8/8); concluded **"안 사는 것도 결론"** with a watchlist (MU 1st, KALU 2nd) + confirmation triggers; declined sizing; applied good-co≠good-stock and 3-of-4=no-trade.
- **bl (FAIL):** defaulted to **familiar mega-caps** (TSM core, AAPL as "변동성 완충" core); **full portfolio with sizing + stops** (5-point allocation, "손절선 -7~8%", "분할 매수"); said **buy now** rather than recognize the late-stage no-clean-setup reality. (Note: a *strong* baseline — independently rebuilt a trend/RS screen across 42 names. Not a strawman.)

### 3. convergence-compare — "마이크론(MU) vs 애플(AAPL)?" (both clear gates; MU fund. accel, AAPL not)
- **ws (PASS 7/7):** recognized both clear gates; split on fundamentals (MU EPS +157→167→682%, 5q margin expansion vs AAPL decel +91→18→22%); explicit AND-convergence ("점수 합산이 아니라 모든 축이 같은 순간 정렬… 셋 중 둘이 좋아도 매수 아님"); nailed good-co≠good-stock (AAPL = "친숙해서 위험한" late-stage); verdict MU≫AAPL but MU = watch-not-chase; declined sizing.
- **bl (FAIL):** framed as "depends on risk tolerance"; leaned **AAPL** on risk-adjusted/valuation (PEG 0.32 vs 2.42); **prescribed sizing + stops** ("작은 비중, 손절선 명확히, 분할 매수"). The weighted-preference blend the method rejects.

## Mechanical checker (check_assertions.py, regexes fixed this iteration)
- **Coined-label leaks: 0 / 6.** No-branding rule held in every with-skill output.
- **Sizing/stops:** with-skill = 0 prescriptive (100% of hits are the refusal disclaimer, verified via context snippets); baseline = prescriptive in all 3.
- **Composite-score anchoring:** with-skill = 0 cross-dimensional composites; only within-lane `setup_readiness` /100 (labeled "약함"), doctrine-legal. Baseline anchors instead on valuation/PEG/analyst targets.
- **Process order:** all 3 ws arms ran `discover`→`qualify`→spine; baselines began at earnings/entry, no gate.
- Checker fixes: dropped `\d점` clause (was flagging RS "99점"/"1점 차이" as composites); broadened sizing to catch qualitative "손절선/분할/작은 비중" the baselines used (was missing them); added ±35-char context snippets so prescribe-vs-decline is readable. (Residual noise: the `-N%` clause also catches drawdown stats — context column disambiguates.)

## The skill's actual edge (honest framing)
The baselines are analytically capable. The skill's value-add is NOT raw horsepower; it is four
disciplines a strong generalist reliably breaks: (1) the gate as a hard veto (no fundamental
rescue), (2) AND-convergence vs preference-blend/weighted-average, (3) the sizing/stops boundary
(baseline crossed it every time; skill held it every time), (4) the anti-familiarity steer
(baseline → AAPL/mega-caps; skill → surfaced unfamiliar leaders). Consistent across all 3 cases.

## Open gaps for iteration-2
1. **No trigger-pull test (most important).** All 3 cases resolved to AVOID/watch/no-buy. We have
   validated the skill's *veto/caution* discipline but NOT that it can correctly say "buy-ready"
   when convergence actually occurs. A skill that is *always* cautious would also pass these 3 while
   being useless. Needs a case engineered toward a genuine buy-ready setup (Stage2+8/8 + tight base
   + dry pivot + accel fundamentals + leadership converging). Caveat: live market has no cleanly
   buy-ready name right now (even MU's base is immature), so this case needs care to be deterministic.
2. **Minor style:** ws-conv surfaced raw within-lane scores ("13/100", "18/100") to the user.
   Doctrine permits within-lane numbers, but a raw 0-100 slightly invites the anchoring the skill
   elsewhere avoids. Optional one-line Output nudge: prefer plain-language quality descriptors over
   surfacing raw within-lane scores. Borderline — not a correctness defect.

## Bottom line
Iteration-1 shows no functional defect in the skill. It does precisely what it was designed to do,
and beats a capable generalist decisively and consistently on the four disciplines above. The loop's
next value is in (1) probing the trigger-pull path, not in fixing the happy path.
