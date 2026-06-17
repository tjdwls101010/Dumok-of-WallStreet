"""Hard-gate computation for the Minervini SEPA pipeline.

There is no composite 0-100 score here, and that is deliberate. A single number
invites the analyst to defer to it instead of reasoning — to anchor on "72/100"
rather than read what the modules actually say. SEPA convergence is a JUDGMENT
(do the elements line up like four cars at a four-way stop?), and that judgment
belongs to the analyst reading the raw module outputs against doctrine, not to a
weighted average frozen in code.

What DOES belong in code is the part that admits no judgment: the two
deterministic hard gates. They are binary, non-negotiable, and identical every
time — exactly what a machine should own so the analyst can't rationalize past
them.

- Stage 2:        stage_analysis.stage must == 2 (Stage 1/3/4 -> disqualified)
- Trend Template: trend_template.overall_pass, all 8/8 (no partial credit)

A failed hard gate means structurally disqualified. Full stop. Everything
downstream is then read for *why* and for watch-list value, not to rescue the
name past the gate.
"""


def compute_hard_gates(results):
	"""Compute the two deterministic SEPA hard gates.

	Returns:
		tuple: (hard_gate_fail: bool, hard_gates: list[dict], overall_pass: bool)
		- hard_gates: structured gate dicts (gate, passed, + context)
	"""
	hard_gate_fail = False
	hard_gates = []

	# Gate 1 — Stage 2 (lifecycle timing: only Stage 2 advances)
	stage = results.get("stage_analysis", {})
	current_stage = stage.get("stage") if not stage.get("error") else None
	stage_passed = current_stage == 2
	hard_gates.append({
		"gate": "stage_2",
		"passed": stage_passed,
		"current_stage": current_stage,
		"required": 2,
	})
	if not stage_passed:
		hard_gate_fail = True

	# Gate 2 — Trend Template (all 8 criteria; no in-between)
	tt = results.get("trend_template", {})
	tt_passed = tt.get("overall_pass", False) if not tt.get("error") else False
	tt_count = tt.get("passed_count", 0) if not tt.get("error") else 0
	tt_total = tt.get("total_count", 8) if not tt.get("error") else 8
	hard_gates.append({
		"gate": "trend_template",
		"passed": tt_passed,
		"score": f"{tt_count}/{tt_total}",
		"required": f"{tt_total}/{tt_total}",
	})
	if not tt_passed:
		hard_gate_fail = True

	return hard_gate_fail, hard_gates, (not hard_gate_fail)
