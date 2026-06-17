#!/usr/bin/env python3
"""Mechanical assertion checker for the Minervini skill eval.

Surfaces regex hits for the deterministic assertions so a human can judge fast:
  - coined-label leakage (the no-branding rule) -> hard FAIL if any hit in response.md
  - sizing / stops-as-orders / R:R / expectancy terms -> REVIEW (human decides order vs structure)
  - single 0-100 composite-score anchoring -> REVIEW
  - skill-command presence + first-command (from run_notes.md) -> process-order check

Subjective assertions (AND-convergence reasoning, good-company!=good-stock,
regime-via-leadership, live-number citation) are left to human reading.

Usage: python check_assertions.py [iteration_dir]   (default: script's own dir)
"""
import re, sys, json
from pathlib import Path

ITER = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent

# --- coined labels: literal brand terms only. Plain-language descriptions are fine. ---
COINED = {
    "minervini": r"minervini|미너비니",
    "sepa": r"\bsepa\b",
    "vcp": r"\bvcp\b",
    "trend_template": r"trend\s*template|트렌드\s*템플릿",
    "code33": r"code\s*33|코드\s*33",
    "power_play": r"power\s*play|파워\s*플레이",
    "pocket_pivot": r"pocket\s*pivot|포켓\s*피벗",
}
# generic chart vocabulary that is EXPLICITLY allowed (do not flag): uptrend, base,
# breakout, relative strength, four stages / 2단계 etc. -> simply not in COINED.

# --- sizing / stops-as-orders / R:R / expectancy -> out of scope; REVIEW hits ---
# NOTE: this is inherently noisy because the skill's CORRECT behavior is to *decline*
# sizing ("얼마를 살지·손절은 본인 몫") -- which names the same words it refuses. So a
# hit is a surface, not a verdict: read the context snippet to see prescribe-vs-decline.
SIZING = {
    "position_size": r"포지션\s*(크기|사이즈)|position\s*siz|(작은|적은|일부|소액)\s*비중|비중\s*(을|를|\d|관리|조절|축소|확대)|매수\s*비중|전체\s*자산|자산\s*대비|분할\s*(매수|진입|매도)|몰빵",
    "stop_order": r"손절\s*(가|선|폭|라인|가격|선을|을|를)|손절선|stop[\s-]*loss|스탑|[-−]\s*\d+\s*[~%]",
    "rr_target": r"손익비|risk[\s/:-]*reward|위험[\s/:-]*보상|\bR\s*:\s*R\b|R/R|목표\s*주가|목표가\s*\d|price\s*target|target\s*price",
    "expectancy": r"기대[값갓]|expectancy",
}

# --- single 0-100 *cross-dimensional* composite anchoring -> REVIEW.
# Within-lane scores (vcp setup_readiness "/100", A-E grade, RS "99점", "1점 차이",
# trend "6/8") are EXPLICITLY allowed by doctrine -> do NOT flag bare "\d점" or "n/8".
# Only the blended verdict-score is banned; a "/100" still needs human read (could be
# the legit within-lane setup_readiness). ---
SCORE = {
    "composite_0_100": r"/\s*100\b|종합\s*점수|총점|composite\s*score|sepa\s*score|\d+\s*점\s*만점|\bscore\s*[:=]\s*\d",
}

# --- skill commands we expect to see in run_notes.md (process-order) ---
CMDS = ["qualify", "discover", "code33", "trend_template", "stage", "vcp",
        "volume", "earnings", "rs_ranking", "base_count", "entry", "tight"]


def scan(text, groups, want_context=False):
    out = {}
    for name, pat in groups.items():
        ms = list(re.finditer(pat, text, re.IGNORECASE))
        if not ms:
            continue
        entry = {"count": len(ms), "samples": sorted({m.group(0) for m in ms})[:5]}
        if want_context:
            # ±35 char window per hit so prescribe-vs-decline is readable at a glance
            ctx = []
            for m in ms[:4]:
                a, b = max(0, m.start() - 35), min(len(text), m.end() + 35)
                ctx.append("…" + text[a:b].replace("\n", " ") + "…")
            entry["context"] = ctx
        out[name] = entry
    return out


def first_command(notes):
    """Return the first skill command mentioned in run_notes (rough order proxy)."""
    positions = []
    for c in CMDS:
        m = re.search(re.escape(c), notes, re.IGNORECASE)
        if m:
            positions.append((m.start(), c))
    positions.sort()
    return positions[0][1] if positions else None


def cmds_present(notes):
    return [c for c in CMDS if re.search(re.escape(c), notes, re.IGNORECASE)]


report = {}
for case_dir in sorted(p for p in ITER.iterdir() if p.is_dir() and p.name.startswith("eval-")):
    case = case_dir.name
    report[case] = {}
    for arm in ("with_skill", "without_skill"):
        resp = case_dir / arm / "outputs" / "response.md"
        notes = case_dir / arm / "outputs" / "run_notes.md"
        entry = {"response_exists": resp.exists(), "notes_exists": notes.exists()}
        if resp.exists():
            t = resp.read_text(encoding="utf-8", errors="replace")
            entry["response_chars"] = len(t)
            entry["coined_labels"] = scan(t, COINED)                      # any hit = FAIL
            entry["sizing"] = scan(t, SIZING, want_context=True)          # REVIEW (read ctx)
            entry["score_anchor"] = scan(t, SCORE, want_context=True)     # REVIEW (read ctx)
        if notes.exists():
            n = notes.read_text(encoding="utf-8", errors="replace")
            entry["first_command"] = first_command(n)
            entry["commands_present"] = cmds_present(n)
        report[case][arm] = entry

print(json.dumps(report, ensure_ascii=False, indent=2))

# --- compact verdict lines ---
print("\n=== COMPACT ===")
for case, arms in report.items():
    for arm, e in arms.items():
        if not e.get("response_exists"):
            print(f"[{case}/{arm}] MISSING response.md")
            continue
        flags = []
        if e.get("coined_labels"):
            flags.append("LABEL-LEAK:" + ",".join(e["coined_labels"]))
        if e.get("sizing"):
            flags.append("sizing?:" + ",".join(e["sizing"]))
        if e.get("score_anchor"):
            flags.append("score?:" + ",".join(e["score_anchor"]))
        fc = e.get("first_command", "-")
        print(f"[{case}/{arm}] {e.get('response_chars')}c first_cmd={fc} "
              f"cmds={e.get('commands_present', [])} "
              f"{'| ' + ' | '.join(flags) if flags else '| clean'}")
