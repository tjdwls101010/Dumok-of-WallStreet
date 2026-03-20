"""Output compression for Minervini SEPA pipeline.

Formats earnings data concisely, compresses volume analysis details,
caps long lists, removes duplicate fields, and compresses noisy data
per Context Efficiency (Section 2.4) and Self-Documenting Output (Section 2.8).

Iteration 3 additions:
- compress_earnings_surprise: Keep only most recent 4 quarters in surprise_history
- compress_estimate_revisions: Replace verbose structure with direction/revision pcts
- compress_forward_pe: Strip intermediate calculation fields
- compress_info: Remove MA/52w fields (duplicated in trend_template)
- compress_margin_tracker: Keep only most recent 3 quarters in trajectory
- Add growth_rates_order to earnings_acceleration
"""


# Fields that duplicate top-level ticker/metadata — strip from each module output
_STRIP_FIELDS = {"symbol", "date", "current_price", "interval", "benchmark"}


def _strip_module_meta(result):
	"""Remove symbol/date/current_price from module output (A.1)."""
	if not isinstance(result, dict) or result.get("error"):
		return result
	return {k: v for k, v in result.items() if k not in _STRIP_FIELDS}


def compress_earnings(code33_result):
	"""Format earnings data concisely from code33 output."""
	if not code33_result or code33_result.get("error"):
		return code33_result

	compressed = {}
	# Keep status flags
	for key in ("eps_accelerating", "eps_improving", "sales_accelerating",
				"sales_improving", "margin_expanding", "margin_data_quality",
				"data_quality", "quarters_analyzed", "code33_status"):
		if key in code33_result:
			compressed[key] = code33_result[key]

	# Keep only 3 most recent growth rates
	for key in ("eps_growth_rates", "sales_growth_rates", "margin_trend"):
		if key in code33_result:
			val = code33_result[key]
			if isinstance(val, list):
				compressed[key] = val[:3]

	# Keep thresholds
	if "thresholds" in code33_result:
		compressed["thresholds"] = code33_result["thresholds"]

	return compressed


def compress_volume_analysis(vol_result):
	"""Compress volume analysis to essential fields."""
	if not vol_result or vol_result.get("error"):
		return vol_result

	compressed = {
		"accumulation_distribution_rating": vol_result.get("accumulation_distribution_rating"),
		"up_down_volume_ratio_50d": vol_result.get("up_down_volume_ratio_50d"),
		"up_down_volume_ratio_50d_unit": vol_result.get("up_down_volume_ratio_50d_unit"),
		"up_down_volume_ratio_20d": vol_result.get("up_down_volume_ratio_20d"),
		"volume_vs_50day_avg_pct": vol_result.get("volume_vs_50day_avg_pct"),
		"breakout_volume_confirmation": vol_result.get("breakout_volume_confirmation"),
		"volume_trend": vol_result.get("volume_trend"),
		"pullback_volume_declining": vol_result.get("pullback_volume_declining"),
		"distribution_clusters": vol_result.get("distribution_clusters"),
	}
	if "thresholds" in vol_result:
		compressed["thresholds"] = vol_result["thresholds"]
	return compressed


def compress_volume_for_recheck(vol_result):
	"""Compress volume analysis for recheck command — only key fields (C.6)."""
	if not vol_result or vol_result.get("error"):
		return vol_result

	clusters = vol_result.get("distribution_clusters", {})
	return {
		"grade": vol_result.get("accumulation_distribution_rating"),
		"weighted_ratio_50d": vol_result.get("up_down_volume_ratio_50d"),
		"cluster_warning": clusters.get("cluster_warning") if isinstance(clusters, dict) else None,
		"breakout_volume_confirmation": vol_result.get("breakout_volume_confirmation"),
	}


def cap_shakeout_details(vcp_result, max_shakeouts=3):
	"""Cap shakeout details to top N entries in VCP output."""
	if not vcp_result or vcp_result.get("error"):
		return vcp_result

	shakeout = vcp_result.get("shakeout", {})
	details = shakeout.get("shakeouts_detail", [])
	if len(details) > max_shakeouts:
		shakeout = dict(shakeout)
		shakeout["shakeouts_detail"] = details[:max_shakeouts]
		shakeout["shakeouts_capped"] = True
		vcp_result = dict(vcp_result)
		vcp_result["shakeout"] = shakeout

	return vcp_result


def _compress_contractions_detail(vcp_result, price_data=None):
	"""Convert high_idx/low_idx to dates in contractions_detail (C.2)."""
	if not vcp_result or vcp_result.get("error"):
		return vcp_result

	detail = vcp_result.get("contractions_detail", [])
	if not detail:
		return vcp_result

	compressed_detail = []
	for c in detail:
		entry = {
			"high_price": c.get("high_price"),
			"low_price": c.get("low_price"),
			"depth_pct": c.get("depth_pct"),
		}
		if "high_date" in c:
			entry["high_date"] = c["high_date"]
		if "low_date" in c:
			entry["low_date"] = c["low_date"]
		if "ratio_vs_prior" in c:
			entry["ratio_vs_prior"] = c["ratio_vs_prior"]
		if "ratio_grade" in c:
			entry["ratio_grade"] = c["ratio_grade"]
		compressed_detail.append(entry)

	vcp_result = dict(vcp_result)
	vcp_result["contractions_detail"] = compressed_detail
	return vcp_result


def compress_vcp(vcp_result):
	"""Compress VCP output to essential fields for the pipeline response."""
	if not vcp_result or vcp_result.get("error"):
		return vcp_result

	# Cap shakeouts first
	vcp_result = cap_shakeout_details(vcp_result)

	# Compress contractions_detail (C.2)
	vcp_result = _compress_contractions_detail(vcp_result)

	compressed = {}
	# Core pattern fields
	for key in ("vcp_detected", "contractions_count",
				"base_duration_weeks",
				"correction_depths", "pivot_price", "technical_footprint",
				"pattern_type", "pattern_quality", "first_correction_zone",
				"setup_readiness", "contractions_detail"):
		if key in vcp_result:
			compressed[key] = vcp_result[key]

	# Cup & handle
	cah = vcp_result.get("cup_and_handle", {})
	if cah.get("detected"):
		compressed["cup_and_handle"] = cah

	# Cup completion cheat
	ccc = vcp_result.get("cup_completion_cheat", {})
	if ccc.get("detected"):
		compressed["cup_completion_cheat"] = ccc

	# Power play
	pp = vcp_result.get("power_play", {})
	if pp.get("detected"):
		compressed["power_play"] = pp

	# Relative correction
	rc = vcp_result.get("relative_correction", {})
	if rc:
		compressed["relative_correction"] = rc

	# Shakeout summary
	shakeout = vcp_result.get("shakeout", {})
	if shakeout.get("count", 0) > 0:
		compressed["shakeout"] = shakeout

	# Volume essentials
	vol = vcp_result.get("volume", {})
	if vol:
		compressed["volume"] = {
			"contraction_vol_declining": vol.get("contraction_vol_declining"),
			"pivot_area_dryup": vol.get("pivot_area_dryup"),
			"pivot_vol_vs_base_pct": vol.get("pivot_vol_vs_base_pct"),
			"breakout_vol_target_min": vol.get("breakout_vol_target_min"),
			"volume_confirmation": vol.get("volume_confirmation"),
		}
		if "thresholds" in vol:
			compressed["volume"]["thresholds"] = vol["thresholds"]

	# Pivot tightness
	pt = vcp_result.get("pivot_tightness", {})
	if pt:
		compressed["pivot_tightness"] = pt

	return compressed


def compress_tight_closes(tight_result):
	"""Compress tight_closes: keep only most recent 3 clusters + best (C.1)."""
	if not tight_result or tight_result.get("error"):
		return tight_result

	clusters = tight_result.get("tight_close_clusters", [])
	total_count = len(clusters)

	compressed = {}
	# Keep most recent 3 clusters (they are sorted oldest -> newest)
	if total_count > 3:
		compressed["tight_close_clusters"] = clusters[-3:]
	else:
		compressed["tight_close_clusters"] = clusters

	compressed["total_count"] = total_count

	# best_cluster
	if "best_cluster" in tight_result:
		compressed["best_cluster"] = tight_result["best_cluster"]

	# signal_strength
	if "signal_strength" in tight_result:
		compressed["signal_strength"] = tight_result["signal_strength"]

	# thresholds (§2.8)
	if "thresholds" in tight_result:
		compressed["thresholds"] = tight_result["thresholds"]

	return compressed


def compress_closing_range(cr_result):
	"""Compress closing_range: remove bar counts, keep ratios (C.4)."""
	if not cr_result or cr_result.get("error"):
		return cr_result

	compressed = {}
	# Fields to KEEP
	keep_fields = (
		"period_analyzed", "constructive_ratio", "recent_trend",
		"assessment", "latest_bar", "avg_closing_range_pct",
		"consecutive_constructive", "consecutive_non_constructive",
	)
	for key in keep_fields:
		if key in cr_result:
			compressed[key] = cr_result[key]

	return compressed


def compress_pocket_pivot(pp_result):
	"""Compress institutional demand (pocket_pivot): keep only most_recent + count (C.5)."""
	if not pp_result or pp_result.get("error"):
		return pp_result

	compressed = {
		"demand_day_count": pp_result.get("demand_day_count", pp_result.get("pocket_pivot_count", 0)),
	}

	if "most_recent" in pp_result:
		compressed["most_recent"] = pp_result["most_recent"]
	elif "most_recent_pp" in pp_result:
		compressed["most_recent"] = pp_result["most_recent_pp"]

	if "base_context" in pp_result:
		compressed["base_context"] = pp_result["base_context"]

	if "thresholds" in pp_result:
		compressed["thresholds"] = pp_result["thresholds"]

	return compressed


def filter_active_sell_signals(sell_result):
	"""Remove inactive sell signals from signals dict (C.3)."""
	if not sell_result or sell_result.get("error"):
		return sell_result

	result = dict(sell_result)
	signals = result.get("signals", {})
	if signals:
		# Keep only active signals
		active_signals = {k: v for k, v in signals.items()
						 if isinstance(v, dict) and v.get("active", False)}
		result["signals"] = active_signals

	return result


def filter_margin_trajectory(margin_result):
	"""Filter null entries from margin_tracker trajectory (E.4)."""
	if not margin_result or margin_result.get("error"):
		return margin_result

	result = dict(margin_result)
	trajectory = result.get("trajectory", [])
	if trajectory:
		result["trajectory"] = [
			entry for entry in trajectory
			if entry is not None and isinstance(entry, dict)
			and entry.get("gross") is not None
		]

	return result


def compress_earnings_surprise(data):
	"""Keep only most recent 8 entries in surprise_history (for eps_history)."""
	if not data or data.get("error"):
		return data

	result = dict(data)
	history = result.get("surprise_history", [])
	if len(history) > 8:
		result["surprise_history"] = history[:8]

	return result


def compress_estimate_revisions(data):
	"""Replace verbose revisions structure with compressed summary (I3.2)."""
	if not data or data.get("error"):
		return data

	compressed = {}

	# Direction: net upward vs downward in last 30 days
	revisions = data.get("eps_revisions", {})
	up_30d = revisions.get("upLast30days", {})
	down_30d = revisions.get("downLast30days", {})
	net_up = sum(up_30d.get(k, 0) for k in ("0q", "+1q", "0y", "+1y"))
	net_down = sum(down_30d.get(k, 0) for k in ("0q", "+1q", "0y", "+1y"))
	compressed["direction"] = "up" if net_up > net_down else "down" if net_down > net_up else "flat"

	# Current quarter estimate from eps_trend
	eps_trend = data.get("eps_trend", {})
	current = eps_trend.get("current", {})
	compressed["current_quarter_estimate"] = current.get("0q")

	# Revision percentages from eps_trend changes
	ago_7d = eps_trend.get("7daysAgo", {})
	ago_30d = eps_trend.get("30daysAgo", {})
	ago_90d = eps_trend.get("90daysAgo", {})

	cq = current.get("0q")
	if cq and ago_7d.get("0q"):
		compressed["revision_7d_pct"] = round((cq - ago_7d["0q"]) / abs(ago_7d["0q"]) * 100, 1) if ago_7d["0q"] != 0 else 0.0
	if cq and ago_30d.get("0q"):
		compressed["revision_30d_pct"] = round((cq - ago_30d["0q"]) / abs(ago_30d["0q"]) * 100, 1) if ago_30d["0q"] != 0 else 0.0
	if cq and ago_90d.get("0q"):
		compressed["revision_90d_pct"] = round((cq - ago_90d["0q"]) / abs(ago_90d["0q"]) * 100, 1) if ago_90d["0q"] != 0 else 0.0

	# Growth estimates
	growth = data.get("growth_estimates", {})
	stock_trend = growth.get("stockTrend", {})
	if stock_trend.get("0y") is not None:
		compressed["stock_growth_0y"] = round(stock_trend["0y"] * 100, 1)
	if stock_trend.get("+1y") is not None:
		compressed["stock_growth_1y"] = round(stock_trend["+1y"] * 100, 1)

	compressed["thresholds"] = "5%+ revision in 30d is significant"

	return compressed


def compress_forward_pe(data):
	"""Strip intermediate fields from forward_pe, keep PEG + thresholds (I3.3)."""
	if not data or data.get("error"):
		return data

	keep_fields = (
		"forward_pe_1y", "forward_pe_2y", "peg_ratio", "peg_ratio_unit",
		"revenue_growth_yoy", "gross_margin_pct", "thresholds",
		# Legacy field names (backward compat during transition)
		"forward_1y_pe", "forward_2y_pe",
	)
	return {k: v for k, v in data.items() if k in keep_fields}


def compress_info(data):
	"""Remove MA/52w fields that duplicate trend_template data (I3.4)."""
	if not data or data.get("error"):
		return data

	remove_fields = {
		"fiftyDayAverage", "twoHundredDayAverage",
		"fiftyTwoWeekLow", "fiftyTwoWeekHigh",
	}
	return {k: v for k, v in data.items() if k not in remove_fields}


def compress_margin_tracker(data):
	"""Keep only most recent 3 quarters in trajectory (I3.5)."""
	if not data or data.get("error"):
		return data

	result = dict(data)
	trajectory = result.get("trajectory", [])
	if len(trajectory) > 3:
		result["trajectory"] = trajectory[:3]

	return result


def compress_trend_template(tt_result):
	"""Compress trend_template: remove passed_count/total_count/overall_pass/score_pct/moving_averages/week52.

	Add passed: "N/8". Remove description from each criterion (threshold suffices).
	"""
	if not tt_result or tt_result.get("error"):
		return tt_result

	result = dict(tt_result)

	# Build "N/8" from passed_count/total_count before removing them
	passed_count = result.pop("passed_count", 0)
	total_count = result.pop("total_count", 8)
	result.pop("overall_pass", None)
	result.pop("score_pct", None)
	result.pop("moving_averages", None)
	result.pop("week52", None)

	result["passed"] = f"{passed_count}/{total_count}"

	# Remove description from each criterion (threshold field already covers it)
	criteria = result.get("criteria", [])
	if criteria:
		compressed_criteria = []
		for c in criteria:
			entry = {k: v for k, v in c.items() if k != "description"}
			compressed_criteria.append(entry)
		result["criteria"] = compressed_criteria

	return result


def postprocess_results(results, mode="analyze"):
	"""Apply all post-processing to module results.

	Args:
		results: dict of module name -> module output
		mode: "analyze" | "recheck" — determines compression level

	Returns:
		dict of module name -> compressed module output
	"""
	processed = dict(results)

	# A.1: Strip symbol/date/current_price from all module outputs
	for key in list(processed.keys()):
		processed[key] = _strip_module_meta(processed[key])

	# A.2: Compress trend_template (remove passed_count/total_count/overall_pass/score_pct/moving_averages/week52, add passed: "N/8")
	if "trend_template" in processed:
		processed["trend_template"] = compress_trend_template(
			processed["trend_template"])

	# Compress earnings + add growth_rates_order (I3.7)
	if "earnings_acceleration" in processed:
		processed["earnings_acceleration"] = compress_earnings(
			processed["earnings_acceleration"])
		ea = processed["earnings_acceleration"]
		if isinstance(ea, dict) and not ea.get("error"):
			ea["growth_rates_order"] = "newest_first"

	# Compress volume analysis
	if "volume_analysis" in processed:
		if mode == "recheck":
			processed["volume_analysis"] = compress_volume_for_recheck(
				processed["volume_analysis"])
		else:
			processed["volume_analysis"] = compress_volume_analysis(
				processed["volume_analysis"])

	# Compress VCP
	if "vcp" in processed:
		processed["vcp"] = compress_vcp(processed["vcp"])

	# C.1: Compress tight_closes
	if "tight_closes" in processed:
		processed["tight_closes"] = compress_tight_closes(
			processed["tight_closes"])


	# C.5: Compress pocket_pivot
	if "pocket_pivot" in processed:
		processed["pocket_pivot"] = compress_pocket_pivot(
			processed["pocket_pivot"])

	# C.3: Filter inactive sell signals
	if "sell_signals" in processed:
		processed["sell_signals"] = filter_active_sell_signals(
			processed["sell_signals"])

	# E.4: Filter null margin trajectory
	if "margin_tracker" in processed:
		processed["margin_tracker"] = filter_margin_trajectory(
			processed["margin_tracker"])

	# --- Iteration 3 compressions (analyze mode only) ---
	if mode == "analyze":
		# I3.1: Compress earnings_surprise to 4 most recent quarters
		if "earnings_surprise" in processed:
			processed["earnings_surprise"] = compress_earnings_surprise(
				processed["earnings_surprise"])

		# I3.2: estimate_revisions — kept raw for _build_earnings_unified extraction

		# I3.3: Compress forward_pe — strip intermediate fields
		if "forward_pe" in processed:
			processed["forward_pe"] = compress_forward_pe(
				processed["forward_pe"])

		# I3.4: Compress info — remove MA/52w duplicates
		if "info" in processed:
			processed["info"] = compress_info(
				processed["info"])

		# I3.5: Compress margin_tracker trajectory to 3 quarters
		if "margin_tracker" in processed:
			processed["margin_tracker"] = compress_margin_tracker(
				processed["margin_tracker"])

	# --- Iteration 4 noise removal ---
	# I4.10: Remove base_stage_assessment from base_count
	bc = processed.get("base_count")
	if isinstance(bc, dict):
		bc.pop("base_stage_assessment", None)

	return processed
