"""SEPA Composite Score calculator for Minervini pipeline.

Computes a 0-100 composite score across 4 dimensions (25 pts each):
Trend Quality, Fundamental Strength, Setup Readiness, Risk Profile.

Hard gates (fail -> immediately "avoid"):
- Stage 2 check: current_stage must == 2
- Trend Template: overall_pass must == True

Soft scoring dimensions:
1. Trend Quality (25): RS ranking (0-15) + Stage 2 confidence (0-5) + Base count (0-5)
2. Fundamental Strength (25): Code 33 grade (0-15) + EPS accel (0-5) + Sales accel (0-5)
3. Setup Readiness (25): VCP readiness (0-15) + Entry patterns (0-5) + Volume dryup (0-5)
4. Risk Profile (25): R:R ratio (0-15) + Stock character (0-5) + Sell signal absence (0-5)
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
	detail = {}

	# RS ranking percentile (0-15)
	rs = results.get("rs_ranking", {})
	rs_score = rs.get("rs_score", 0) if not rs.get("error") else 0
	rs_pts = min(15, round(rs_score * 15 / 99)) if rs_score else 0
	score += rs_pts
	detail["rs_score"] = rs_score
	detail["rs_pts"] = rs_pts

	# Stage 2 confidence (0-5)
	stage = results.get("stage_analysis", {})
	confidence = stage.get("stage_confidence", 0) if not stage.get("error") else 0
	conf_pts = min(5, round(confidence * 5 / 100))
	score += conf_pts
	detail["stage_confidence"] = confidence
	detail["confidence_pts"] = conf_pts

	# Base count (0-5): 1st=5, 2nd=4, 3rd=2, 4th+=0
	base = results.get("base_count", {})
	base_num = base.get("current_base_number", 0) if not base.get("error") else 0
	base_pts_map = {1: 5, 2: 4, 3: 2}
	base_pts = base_pts_map.get(base_num, 0)
	score += base_pts
	detail["base_number"] = base_num
	detail["base_pts"] = base_pts

	return score, detail


def _score_fundamental_strength(results):
	"""Fundamental Strength dimension (25 pts max)."""
	score = 0
	detail = {}

	# Code 33 grade (0-15)
	code33 = results.get("earnings_acceleration", {})
	grade, grade_pts = _grade_code33(code33)
	score += grade_pts
	detail["code33_grade"] = grade
	detail["code33_pts"] = grade_pts

	# EPS acceleration (0-5)
	eps_accel = code33.get("eps_accelerating", False) if not code33.get("error") else False
	eps_improving = code33.get("eps_improving", False) if not code33.get("error") else False
	if eps_accel:
		eps_pts = 5
	elif eps_improving:
		eps_pts = 3
	else:
		eps_pts = 0
	score += eps_pts
	detail["eps_accelerating"] = eps_accel
	detail["eps_pts"] = eps_pts

	# Sales acceleration (0-5)
	sales_accel = code33.get("sales_accelerating", False) if not code33.get("error") else False
	sales_improving = code33.get("sales_improving", False) if not code33.get("error") else False
	if sales_accel:
		sales_pts = 5
	elif sales_improving:
		sales_pts = 3
	else:
		sales_pts = 0
	score += sales_pts
	detail["sales_accelerating"] = sales_accel
	detail["sales_pts"] = sales_pts

	return score, detail


def _score_setup_readiness(results):
	"""Setup Readiness dimension (25 pts max)."""
	score = 0
	detail = {}

	# VCP setup_readiness score (0-15): map 0-100 to 0-15
	vcp = results.get("vcp", {})
	if not vcp.get("error") and vcp.get("vcp_detected"):
		readiness = vcp.get("setup_readiness", {})
		vcp_score = readiness.get("score", 0)
		vcp_pts = min(15, round(vcp_score * 15 / 100))
	else:
		vcp_score = 0
		vcp_pts = 0
	score += vcp_pts
	detail["vcp_readiness_score"] = vcp_score
	detail["vcp_pts"] = vcp_pts

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
		pattern_count = 0
		entry_pts = 0
	score += entry_pts
	detail["pattern_count"] = pattern_count
	detail["entry_pts"] = entry_pts

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
	detail["volume_dryup_pts"] = vol_pts

	return score, detail


def _score_risk_profile(results, risk_data):
	"""Risk Profile dimension (25 pts max)."""
	score = 0
	detail = {}

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
	detail["risk_reward_ratio"] = rr
	detail["rr_pts"] = rr_pts

	# Stock character grade (0-5): A=5, B=4, C=2, D=0
	char = results.get("stock_character", {})
	char_grade = char.get("character_grade", "D") if not char.get("error") else "D"
	char_map = {"A": 5, "B": 4, "C": 2, "D": 0}
	char_pts = char_map.get(char_grade, 0)
	score += char_pts
	detail["character_grade"] = char_grade
	detail["character_pts"] = char_pts

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
	detail["sell_severity"] = sell.get("severity", "unknown") if not sell.get("error") else "unknown"
	detail["sell_pts"] = sell_pts

	return score, detail


def compute_sepa_score(results, risk_data):
	"""Compute the full SEPA composite score.

	Args:
		results: dict of module name -> module output
		risk_data: dict from _risk_gate with risk_reward_ratio

	Returns:
		dict with sepa_score, classification, dimension scores, hard_gate status
	"""
	# Hard gates
	hard_gate_fail = False
	hard_gate_reasons = []

	stage = results.get("stage_analysis", {})
	if stage.get("error"):
		hard_gate_fail = True
		hard_gate_reasons.append("stage_analysis_unavailable")
	elif stage.get("current_stage") != 2:
		hard_gate_fail = True
		hard_gate_reasons.append(f"not_stage_2 (current: {stage.get('current_stage')})")

	tt = results.get("trend_template", {})
	if tt.get("error"):
		hard_gate_fail = True
		hard_gate_reasons.append("trend_template_unavailable")
	elif not tt.get("overall_pass"):
		hard_gate_fail = True
		hard_gate_reasons.append(f"trend_template_fail ({tt.get('passed_count', 0)}/{tt.get('total_count', 8)})")

	if hard_gate_fail:
		return {
			"sepa_score": 0,
			"classification": "avoid",
			"hard_gate_fail": True,
			"hard_gate_reasons": hard_gate_reasons,
			"dimensions": None,
			"thresholds": "prime: >=80 | actionable: 60-79 | developing: 40-59 | not_ready: 20-39 | avoid: <20 or hard_gate_fail",
		}

	# Soft scoring
	trend_score, trend_detail = _score_trend_quality(results)
	fund_score, fund_detail = _score_fundamental_strength(results)
	setup_score, setup_detail = _score_setup_readiness(results)
	risk_score, risk_detail = _score_risk_profile(results, risk_data)

	total = trend_score + fund_score + setup_score + risk_score

	# Check provisional status
	error_count = sum(1 for k, v in results.items() if isinstance(v, dict) and v.get("error"))
	provisional = error_count > 2

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

	if provisional:
		classification += " (provisional)"

	return {
		"sepa_score": total,
		"classification": classification,
		"hard_gate_fail": False,
		"hard_gate_reasons": [],
		"provisional": provisional,
		"dimensions": {
			"trend_quality": {"score": trend_score, "max": 25, "detail": trend_detail},
			"fundamental_strength": {"score": fund_score, "max": 25, "detail": fund_detail},
			"setup_readiness": {"score": setup_score, "max": 25, "detail": setup_detail},
			"risk_profile": {"score": risk_score, "max": 25, "detail": risk_detail},
		},
		"thresholds": "prime: >=80 | actionable: 60-79 | developing: 40-59 | not_ready: 20-39 | avoid: <20 or hard_gate_fail",
	}
