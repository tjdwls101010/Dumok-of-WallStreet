"""Multi-ticker comparison helpers: relative strength determination and
market-cap string parsing for the Serenity pipeline."""


def _determine_relative_strengths(tickers, table):
	"""Determine best ticker for each metric from comparative table."""
	strengths = {}

	# Best valuation = lowest positive forward PE
	fpe_vals = {
		t: v for t, v in table["forward_pe"].items()
		if v is not None and isinstance(v, (int, float)) and v > 0
	}
	if fpe_vals:
		strengths["best_valuation"] = min(fpe_vals, key=fpe_vals.get)
	else:
		strengths["best_valuation"] = None

	# Best margin trajectory = EXPANDING preferred, else highest margin status
	margin_priority = {
		"EXPANDING": 4,
		"STABLE": 3,
		"COMPRESSION": 2,
		"CONTRACTING": 1,
		"COLLAPSE": 0,
	}
	margin_vals = {}
	for t in tickers:
		status = table["margin_status"].get(t)
		if status is not None:
			# Check each priority keyword
			best_priority = -1
			for keyword, priority in margin_priority.items():
				if keyword in str(status).upper():
					best_priority = max(best_priority, priority)
			if best_priority >= 0:
				margin_vals[t] = best_priority
	if margin_vals:
		strengths["best_margin_trajectory"] = max(margin_vals, key=margin_vals.get)
	else:
		strengths["best_margin_trajectory"] = None

	# Best IO quality = highest quality score
	io_vals = {
		t: v for t, v in table["io_quality_score"].items()
		if v is not None and isinstance(v, (int, float))
	}
	if io_vals:
		strengths["best_io_quality"] = max(io_vals, key=io_vals.get)
	else:
		strengths["best_io_quality"] = None

	# Best balance sheet = grade A > B > C > D
	grade_priority = {"A": 4, "B": 3, "C": 2, "D": 1}
	grade_vals = {}
	for t in tickers:
		grade = table["debt_quality_grade"].get(t)
		if grade is not None:
			# Take the first character as the grade letter
			grade_letter = str(grade).strip()[0].upper() if grade else ""
			grade_vals[t] = grade_priority.get(grade_letter, 0)
	if grade_vals:
		strengths["best_balance_sheet"] = max(grade_vals, key=grade_vals.get)
	else:
		strengths["best_balance_sheet"] = None

	# Best revenue growth = highest YoY revenue growth
	rev_vals = {
		t: v for t, v in table.get("revenue_growth_yoy", {}).items()
		if v is not None and isinstance(v, (int, float))
	}
	if rev_vals:
		strengths["best_revenue_growth"] = max(rev_vals, key=rev_vals.get)
	else:
		strengths["best_revenue_growth"] = None

	# Best 52-week position = highest position (closest to 52w high)
	pos_vals = {
		t: v for t, v in table.get("52w_range_position", {}).items()
		if v is not None and isinstance(v, (int, float))
	}
	if pos_vals:
		strengths["best_52w_position"] = max(pos_vals, key=pos_vals.get)
	else:
		strengths["best_52w_position"] = None

	# Best SBC health = healthy > warning > toxic
	sbc_priority = {"healthy": 3, "warning": 2, "toxic": 1}
	sbc_vals = {}
	for t in tickers:
		flag = table.get("sbc_flag", {}).get(t)
		if flag is not None:
			sbc_vals[t] = sbc_priority.get(str(flag).lower(), 0)
	if sbc_vals:
		strengths["best_sbc_health"] = max(sbc_vals, key=sbc_vals.get)
	else:
		strengths["best_sbc_health"] = None

	# Best earnings momentum = most consecutive beats
	beat_vals = {
		t: v for t, v in table.get("consecutive_beats", {}).items()
		if v is not None and isinstance(v, (int, float))
	}
	if beat_vals:
		strengths["best_earnings_momentum"] = max(beat_vals, key=beat_vals.get)
	else:
		strengths["best_earnings_momentum"] = None

	# Best asymmetry = highest bottleneck asymmetry score
	asym_vals = {
		t: v for t, v in table.get("asymmetry_score", {}).items()
		if v is not None and isinstance(v, (int, float))
	}
	if asym_vals:
		strengths["best_asymmetry"] = max(asym_vals, key=asym_vals.get)
	else:
		strengths["best_asymmetry"] = None

	return strengths


def _parse_mcap_string(mcap_str):
	"""Parse market cap string like '1.5B', '500M', '10B' to a numeric value.

	Returns:
		float or None if parsing fails
	"""
	if not mcap_str or not isinstance(mcap_str, str):
		return None
	mcap_str = mcap_str.strip().upper()
	multipliers = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}
	for suffix, mult in multipliers.items():
		if mcap_str.endswith(suffix):
			try:
				return float(mcap_str[:-1]) * mult
			except ValueError:
				return None
	try:
		return float(mcap_str)
	except ValueError:
		return None
