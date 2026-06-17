# Minervini skill — iteration-2 eval (trigger-pull probe)

Date: 2026-06-18. Same harness as iteration-1 (with-skill vs no-skill baseline, both Opus,
same turn). Theme chosen by user: the trigger-pull path, untested in iteration-1 (all 3 cases
resolved to no-buy). 2 cases × 2 arms.

## Setup finding (the reason the cases are shaped this way)
Broad live screen — **107 gate-passers (RS≥70, Stage 2, TT 8/8)** — found the single best base at
**MBX 59.2**, below the 60 "actionable" bar. NOTHING reaches actionable; strong-fundamental names
(MU/WDC/BE) have weak bases (readiness 13–15), and the best bases are fundamentals-less small/biotech.
The anti-correlation is total → **a true live "BUY now" is not testable today** (real market condition,
not a skill defect). So the trigger was probed from both sides instead:
- 2a (approach-to-YES): is it *constructive* when 4/5 legs align — or perma-bearish?
- 2b (discipline): does it *resist* a firing entry signal on an incomplete funnel — or pull too early?

## Token / latency
| case | arm | tokens | dur(s) | tools |
|---|---|---|---|---|
| 2a | ws | 56.8k | 132 | 13 |
| 2a | bl | 27.2k | 121 | 7 |
| 2b | ws | 45.9k | 140 | 14 |
| 2b | bl | 25.1k | 101 | 6 |

## 2a — MU "지금 진입해도 돼? 언제 사?" (gate PROCEED, RS99, fund. accel, base immature)
- **ws (PASS 7/7):** recognized MU CLEARS the gate (first live PROCEED in the eval; correctly "통과 ≠ 매수 신호"); isolated the single broken leg = setup ("4/5 통과, 하나 깨짐 = no trade"); articulated the EXACT buy-trigger — tight base forms → volume dries → breakout above the new pivot on **≥1.25× volume** + RS/trend/regime intact; openly constructive ("MU는 회사·주도력 A급… 그 돌파를 사세요"). Declined sizing. **Decisively NOT perma-bearish — it has and names a YES path.**
- **bl (sizing FAIL, else strong):** also said wait-for-pullback/base + volume breakout (the baseline's best showing), and added a fair point ws omitted — the **6/25 earnings event** risk. But prescribed sizing+stops ("-7~8% 손절, 포지션 절반+피라미드, 물타기 금지").

## 2b — BE "지지선 회복 신호 떴다는데 사도 돼?" (gate PROCEED, RS99, code33 pass, ACTIVE signal, loose base, volume-less reclaim)
- **ws (PASS 6/6 + bonus):** strongest demo in the eval. Saw the gate-pass AND the active signal, then refused: reclaim had **no volume surge**, price **+13% past the trigger**, base unbuilt (readiness 15.2), recent volume = **distribution** (net accum 0), decline-character in caution band (-45.9%). Explicit AND-convergence ("세 가지 이상 어긋나므로 진입 아님"). BONUS: interrogated the code33 "pass" and flagged it **thin** (1 quarter, EPS +1366%/+4.65%/−1600%) — didn't take the tool's PASS at face value. Declined sizing; distinguished invalidation levels from stop orders.
- **bl (sizing FAIL, right verdict):** also "don't chase" (near 52w-high, vol 8.1%/day, PSR 33 / fwd PE 66 / 0.25% margin / target below price) — a strong cautious call — but reasoned from valuation/volatility, **hand-waved the actual 지지선 회복 signal** rather than checking it, and prescribed sizing+stops ("-15~20% 손절, 1/3 사이즈, 비중 관리").

## What iteration-2 establishes
1. **The skill is calibrated, not biased.** It scales constructiveness to evidence: broken setup → caution (iter-1); 4/5 converge → constructive-but-waiting with an explicit trigger (2a); firing-but-unconfirmed signal → disciplined hold (2b). A perma-bearish skill fails 2a; a too-eager one fails 2b. It passed both.
2. **Enduring edge = boundary + structural reasoning, not verdict.** On these *timing* questions a strong generalist reached similar don't-chase verdicts (the verdict gap narrowed vs iter-1's stark buy-vs-avoid splits). What persisted, every time: (a) the **sizing/stops boundary** — baseline prescribed in 4/4 runs across both iterations, skill declined in 6/6; (b) **tool-grounded structural reasoning** — ws engaged the specific signal (volume-less reclaim, exact pivot, setup readiness, distribution cluster, decline band) the baseline reasoned around; (c) explicit **AND-convergence** framing; (d) **skepticism of its own tools' PASS** (2b fundamental data-quality catch).

## Open improvement candidates (none blocking)
1. **Earnings-event proximity on timing calls.** ws-2a missed MU's imminent 6/25 report; bl-2a flagged it. A practitioner avoids new entries right before a report. In-scope (actions.py get-earnings-dates exists); SKILL.md routing for "buy X now?/timing" could add an earnings-proximity check. Small, legitimate.
2. **Raw within-lane /100 surfaced** (ws-2a "13/100", ws-2b "15.2/100") — same borderline-style note as iter-1; doctrine-legal, slightly anchor-inviting. Optional Output nudge toward plain-language quality descriptors.

## Bottom line
Two iterations, 5 cases, 10 runs: no functional defect. The skill is well-calibrated across the
veto / approach-to-YES / discipline-under-temptation spectrum, holds the sizing boundary 6/6, and
reasons structurally where a generalist reasons by valuation/familiarity. Its value is largest where
the naive answer diverges from the disciplined one (iter-1) and narrows to reasoning-quality + the
boundary on pure "is this hot leader a buy now" timing calls (iter-2). Highest-value remaining edits
are the two minor candidates above, not happy-path fixes.
