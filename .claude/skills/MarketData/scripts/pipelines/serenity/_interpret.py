"""Self-documenting interpretation helpers for Serenity pipeline outputs."""


def _interpret_bottleneck_signal(assessment, supplier_pct, single_source_count):
	"""Human-readable interpretation for cross-chain bottleneck signal."""
	if assessment == "strong_bottleneck_signal":
		return (
			f"Strong bottleneck signal: {supplier_pct}% of tickers reference as supplier "
			f"AND {single_source_count} single-source dependency(ies). Prime candidate for investigation."
		)
	if assessment == "moderate_bottleneck_signal":
		parts = []
		if supplier_pct >= 50:
			parts.append(f"referenced by {supplier_pct}% of tickers")
		if single_source_count > 0:
			parts.append(f"{single_source_count} single-source dependency(ies)")
		return f"Moderate bottleneck signal: {' and '.join(parts)}. Investigate if small-cap."
	if assessment == "weak_signal":
		return f"Weak signal: referenced by {supplier_pct}% of tickers but no single-source dependencies. Monitor."
	return f"Low signal: referenced by {supplier_pct}% of tickers. Not a significant bottleneck indicator."


def _interpret_rotation_assessment(flags, opp_cost, suggestion):
	"""Human-readable interpretation for recheck rotation assessment."""
	if not flags:
		return "No rotation flags. Position dynamics healthy — maintain."
	flag_descs = {
		"extreme_forward_pe": "forward P/E exceeds 50x",
		"deep_below_no_growth_floor": "trading >30% below no-growth floor",
		"position_doubled_check_asymmetry": "position has doubled — check remaining asymmetry",
		"losing_position_thesis_weakening": "losing position with weakening thesis signals",
	}
	desc = "; ".join(flag_descs.get(f, f) for f in flags)
	if suggestion == "scan_alternatives":
		return (
			f"Opportunity cost elevated ({len(flags)} flags: {desc}). "
			"Run relative asymmetry comparison — pipeline suggests scanning alternatives."
		)
	if suggestion == "consider_trim":
		return (
			f"Single rotation flag detected ({desc}). "
			"Evaluate whether thesis is weakened or intact but priced in."
		)
	return f"Rotation flags: {desc}."


def _interpret_institutional_flow(io_assessment, iv_regime, flow_assessment, insider_dir):
	"""Human-readable interpretation for institutional flow assessment."""
	context = f"IO quality: {io_assessment}, IV regime: {iv_regime}, insider direction: {insider_dir}"
	if flow_assessment == "positive":
		summary = "Accumulation signals present — institutional behavior aligns with bullish thesis."
	elif flow_assessment == "negative":
		summary = "Distribution signals detected — investigate whether active conviction reversal or mechanical flow."
	else:
		summary = "No clear directional signal from institutional data — rely on other evidence legs."
	return f"{summary} ({context})"
