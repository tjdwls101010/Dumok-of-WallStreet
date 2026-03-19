"""SEPA Composite Score calculator for Minervini pipeline.

Computes a 0-100 composite score across 4 dimensions (25 pts each):
Trend Quality, Fundamental Strength, Setup Readiness, Risk Profile.

Hard gates (fail -> immediately "avoid"):
- Stage 2 check: current_stage must == 2
- Trend Template: overall_pass must == True

Returns a tuple: (total_score, classification, hard_gate_fail, hard_gates, dim_scores)
- dim_scores: {"trend": {"score": N, "max": 25}, ...} for embedding in each dimension section
"""


def _grade_code33(code33_result):
	"""Grade Code 33 intermediate level from earnings_acceleration output.

	Count how many of (eps_accelerating, sales_accelerating, margin_expanding) are True.
	3/3 = PASS, 2/3 = CANDIDATE, 1/3 = PARTIAL, 0/3 = FAIL.
	"""
	if not code33_result or code33_result.get("error"):
		return "FAIL", 0

	count = 0
	if code33_result.get("eps_accelerating"):
		count += 1
	if code33_result.get("sales_accelerating"):
		count += 1
	if code33_result.get("margin_expanding"):
		count += 1

	if count == 3:
		return "PASS", 15
	elif count == 2:
		return "CANDIDATE", 10
	elif count == 1:
		return "PARTIAL", 5
	else:
		return "FAIL", 0


def _score_trend_quality(results):
	"""Trend Quality dimension (25 pts max)."""
	score = 0

	# RS ranking percentile (0-15)
	rs = results.get("rs_ranking", {})
	rs_score = rs.get("rs_score", 0) if not rs.get("error") else 0
	rs_pts = min(15, round(rs_score * 15 / 99)) if rs_score else 0
	score += rs_pts

	# Stage 2 confidence (0-5) — derived from winning stage score / theoretical max
	stage = results.get("stage_analysis", {})
	if not stage.get("error"):
		stage_scores = stage.get("scores", {})
		winning_stage = stage.get("stage", 0)
		# Theoretical max per stage
		_max_map = {1: 80, 2: 95, 3: 90, 4: 95}
		winning_score = stage_scores.get(str(winning_stage), 0)
		theo_max = _max_map.get(winning_stage, 95)
		confidence = min(winning_score / theo_max * 100, 100.0) if theo_max > 0 else 0
	else:
		confidence = 0
	conf_pts = min(5, round(confidence * 5 / 100))
	score += conf_pts

	# Base count (0-5): 1st=5, 2nd=4, 3rd=2, 4th+=0
	base = results.get("base_count", {})
	base_num = base.get("current_base_number", 0) if not base.get("error") else 0
	base_pts_map = {1: 5, 2: 4, 3: 2}
	base_pts = base_pts_map.get(base_num, 0)
	score += base_pts

	return score


def _score_fundamental_strength(results):
	"""Fundamental Strength dimension (25 pts max)."""
	score = 0

	# Code 33 grade (0-15)
	code33 = results.get("earnings_acceleration", {})
	_, grade_pts = _grade_code33(code33)
	score += grade_pts

	# EPS acceleration (0-5)
	eps_accel = code33.get("eps_accelerating", False) if not code33.get("error") else False
	eps_improving = code33.get("eps_improving", False) if not code33.get("error") else False
	if eps_accel:
		score += 5
	elif eps_improving:
		score += 3

	# Sales acceleration (0-5)
	sales_accel = code33.get("sales_accelerating", False) if not code33.get("error") else False
	sales_improving = code33.get("sales_improving", False) if not code33.get("error") else False
	if sales_accel:
		score += 5
	elif sales_improving:
		score += 3

	return score


def _score_setup_readiness(results):
	"""Setup Readiness dimension (25 pts max)."""
	score = 0

	# VCP setup_readiness score (0-15): map 0-100 to 0-15
	vcp = results.get("vcp", {})
	if not vcp.get("error") and vcp.get("vcp_detected"):
		readiness = vcp.get("setup_readiness", {})
		vcp_score = readiness.get("score", 0)
		vcp_pts = min(15, round(vcp_score * 15 / 100))
	else:
		vcp_pts = 0
	score += vcp_pts

	# Entry pattern active (0-5): pattern_count > 0 with quality weighting
	entry = results.get("entry_patterns", {})
	if not entry.get("error"):
		pattern_count = entry.get("pattern_count", 0)
		patterns = entry.get("active_patterns", [])
		high_count = sum(1 for p in patterns if p.get("quality") == "high")
		if high_count >= 2:
			entry_pts = 5
		elif high_count >= 1:
			entry_pts = 4
		elif pattern_count >= 2:
			entry_pts = 3
		elif pattern_count >= 1:
			entry_pts = 2
		else:
			entry_pts = 0
	else:
		entry_pts = 0
	score += entry_pts

	# Volume dryup quality (0-5): from VCP/tight_closes volume analysis
	vol_pts = 0
	if not vcp.get("error") and vcp.get("vcp_detected"):
		vol_data = vcp.get("volume", {})
		if vol_data.get("pivot_area_dryup"):
			vol_pts += 3
		if vol_data.get("contraction_vol_declining"):
			vol_pts += 1
		if vol_data.get("contraction_vol_strongly_declining"):
			vol_pts += 1
	# Supplement from tight_closes
	tight = results.get("tight_closes", {})
	if not tight.get("error"):
		signal = tight.get("signal_strength", "")
		if signal == "strong" and vol_pts < 5:
			vol_pts = min(5, vol_pts + 2)
		elif signal == "moderate" and vol_pts < 5:
			vol_pts = min(5, vol_pts + 1)
	vol_pts = min(5, vol_pts)
	score += vol_pts

	return score


def _score_risk_profile(results, risk_data):
	"""Risk Profile dimension (25 pts max)."""
	score = 0

	# R:R ratio (0-15)
	rr = risk_data.get("risk_reward_ratio")
	if rr is not None:
		if rr >= 4.0:
			rr_pts = 15
		elif rr >= 3.0:
			rr_pts = 12
		elif rr >= 2.0:
			rr_pts = 8
		elif rr >= 1.0:
			rr_pts = 3
		else:
			rr_pts = 0
	else:
		rr_pts = 0
	score += rr_pts

	# Stock character grade (0-5): A=5, B=4, C=2, D=0
	char = results.get("stock_character", {})
	char_grade = char.get("character_grade", "D") if not char.get("error") else "D"
	char_map = {"A": 5, "B": 4, "C": 2, "D": 0}
	char_pts = char_map.get(char_grade, 0)
	score += char_pts

	# Sell signal absence (0-5): no signals=5, low severity=3, high severity=0
	sell = results.get("sell_signals", {})
	if not sell.get("error"):
		severity = sell.get("severity", "healthy")
		if severity == "healthy":
			sell_pts = 5
		elif severity == "caution":
			sell_pts = 3
		elif severity == "warning":
			sell_pts = 1
		else:  # critical
			sell_pts = 0
	else:
		sell_pts = 5  # no data = assume no signals
	score += sell_pts

	return score


def compute_sepa_score(results, risk_data):
	"""Compute the full SEPA composite score.

	Returns:
		tuple: (total_score, classification, hard_gate_fail, hard_gates, dim_scores)
		- hard_gates: list of structured gate dicts
		- dim_scores: {"trend": {"score": N, "max": 25}, ...}
	"""
	# Hard gates — structured
	hard_gate_fail = False
	hard_gates = []

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

	# Always compute dimensions
	trend_score = _score_trend_quality(results)
	fund_score = _score_fundamental_strength(results)
	setup_score = _score_setup_readiness(results)
	risk_score = _score_risk_profile(results, risk_data)

	dim_scores = {
		"trend": {"score": trend_score, "max": 25},
		"fundamentals": {"score": fund_score, "max": 25},
		"setup": {"score": setup_score, "max": 25},
		"risk": {"score": risk_score, "max": 25},
	}

	if hard_gate_fail:
		return 0, "avoid", True, hard_gates, dim_scores

	total = trend_score + fund_score + setup_score + risk_score

	# Classification
	if total >= 80:
		classification = "prime"
	elif total >= 60:
		classification = "actionable"
	elif total >= 40:
		classification = "developing"
	elif total >= 20:
		classification = "not_ready"
	else:
		classification = "avoid"

	# Provisional check
	error_count = sum(1 for k, v in results.items() if isinstance(v, dict) and v.get("error"))
	if error_count > 2:
		classification += " (provisional)"

	return total, classification, False, hard_gates, dim_scores
