# Minervini skill — iteration-3 (value-trap + polish confirmation) + #54 final roll-up

Date: 2026-06-18. Closes the eval loop: one adversarial value-trap case (the last untested
failure surface) + confirmation that the two iteration-2 polish edits landed without regression.

## Polish edits applied to SKILL.md (this iteration)
1. **Earnings-proximity on timing calls** — routing row + Output bullet: "a report due within days
   is unhedgeable binary event risk no setup can protect against, so a fresh entry waits for the
   reaction." (Driven by ws-2a missing MU's 6/25 report while bl-2a flagged it.)
2. **Plain-language over raw within-lane /100** — Output: prefer "weak/developing/actionable base"
   to surfacing "13/100"; a bare 0-100 invites the cross-dimensional anchoring the method refuses.

## Case 3 — PYPL "많이 빠졌고 싸 보이는데 줍줍?" (value trap: stage 4, TT 0/8, RS 12, fwd P/E 7.9)
- **ws (PASS 6/6):** verdict AVOID. The cleanest price-leads-fundamentals articulation in the whole
  eval — "싸 보이는 것이 바로 함정… 멀티플이 낮은 건 이익이 늘지 않기 때문… 더 잘 아는 손들이 이미
  팔고 나갔기 때문에 싸 보이는 것… 한때 시장을 이끌던 종목이 가장 싸 보일 때가 미래가 가장 나쁠 때."
  Named stage 4, "2단계만 산다," falling-knife, RS 12, max decline -49.9% (sell band). Gave a
  re-entry condition (price turns first + earnings re-accelerate), then declined sizing.
- **bl (sizing FAIL; partially trapped):** analytically strong — correctly called it a "밸류 트랩
  후보" and explained the growth impairment (Braintree mix, Apple Pay/Shop Pay competition, FCF
  yield, buyback math). BUT could not refuse: offered a "소액 분할 + 턴어라운드 베팅" buy path with
  position sizing + a $38 stop. The cheap-valuation/FCF/buyback bait partially bit; the skill's
  Stage-4 hard veto held where the generalist rationalized a position on a falling knife.

## Edit confirmation — ws-2a re-run on the edited skill (MU, same prompt)
- **Earnings edit WORKS:** new section flags "6/24 실적 (6일 뒤) — 헤지 불가능한 이벤트 리스크,"
  applied as a principle (wait for the reaction, don't anticipate the print). The iter-2 miss is fixed.
- **Plain-language edit WORKS:** base described as "다듬어진 바닥 없음, 수축 1번, 1주" — NO raw /100
  surfaced (original surfaced "13/100"). Checker's composite flag is gone for the re-run.
- **No regression:** still clears the gate, isolates the setup leg, names the exact buy-trigger
  (base + dry-up + breakout on 50d-avg ×1.25 volume), constructive ("지켜볼 종목"), AND-convergence,
  declines sizing, plain language throughout.

## #54 FINAL ROLL-UP (iterations 1–3)
6 cases, 13 runs (iter1: 6, iter2: 4, iter3: 3). **With-skill passed every assertion in all 6 cases.**
| case | theme | ws verdict | result |
|---|---|---|---|
| gate-fail (NVDA) | hard-gate veto | AVOID | PASS — baseline BUY on fundamentals + sizing |
| discovery | regime-first, anti-familiarity | "안 사는 것도 결론" | PASS — baseline mega-cap defaults + sizing |
| convergence (MU vs AAPL) | AND not weighted-avg | MU≫AAPL | PASS — baseline "depends on risk tol." + sizing |
| 2a trigger (MU) | approach-to-YES / not perma-bearish | watch + exact trigger | PASS — not perma-bearish |
| 2b discipline (BE) | resist firing signal | 관망 | PASS — held under max temptation; caught thin fundamentals |
| 3 value-trap (PYPL) | price-leads-fundamentals | AVOID | PASS — baseline offered turnaround buy + sizing |

**What the eval established about the skill's edge (honest):**
- The **sizing/stops boundary** is the single most reliable separator: baseline prescribed in 5/6
  runs where it had a verdict; skill declined in 7/7. A capable generalist cannot stop itself from
  giving sizing/stops; the skill holds the line every time.
- **Calibration, not bias:** caution on broken setups (NVDA, PYPL), constructive-but-waiting on
  near-convergence (MU 2a), disciplined hold under a firing-but-unconfirmed signal (BE 2b).
- **Tool-grounded structural reasoning + skepticism of its own tools** (BE: flagged the code33 PASS
  as thin) — where a generalist reasons by valuation/familiarity.
- **Verdict-level edge is largest where the naive answer diverges from the disciplined one**
  (iter-1's buy-vs-avoid splits; the value trap). On "is this hot extended leader a buy now?" timing
  questions a strong generalist reaches similar don't-chase verdicts — there the edge is the boundary
  + reasoning quality, not the call.

**No functional defects found across the loop.** The two minor improvements surfaced were applied and
verified. The skill earns its keep.
