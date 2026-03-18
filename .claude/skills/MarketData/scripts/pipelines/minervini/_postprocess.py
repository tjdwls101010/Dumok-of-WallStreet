"""Output compression for Minervini SEPA pipeline.

Formats earnings data concisely, compresses volume analysis details,
and caps long lists (e.g., shakeout details to top 3).
"""


def compress_earnings(code33_result):
	"""Format earnings data concisely from code33 output."""
	if not code33_result or code33_result.get("error"):
		return code33_result

	compressed = {}
	# Keep status flags
	for key in ("eps_accelerating", "eps_improving", "sales_accelerating",
				"sales_improving", "margin_expanding", "margin_data_quality",
				"data_quality", "quarters_analyzed"):
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

	return {
		"accumulation_distribution_rating": vol_result.get("accumulation_distribution_rating"),
		"up_down_volume_ratio_50d": vol_result.get("up_down_volume_ratio_50d"),
		"up_down_volume_ratio_20d": vol_result.get("up_down_volume_ratio_20d"),
		"volume_vs_50day_avg_pct": vol_result.get("volume_vs_50day_avg_pct"),
		"breakout_volume_confirmation": vol_result.get("breakout_volume_confirmation"),
		"volume_trend": vol_result.get("volume_trend"),
		"pullback_volume_declining": vol_result.get("pullback_volume_declining"),
		"distribution_clusters": vol_result.get("distribution_clusters"),
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


def compress_vcp(vcp_result):
	"""Compress VCP output to essential fields for the pipeline response."""
	if not vcp_result or vcp_result.get("error"):
		return vcp_result

	# Cap shakeouts first
	vcp_result = cap_shakeout_details(vcp_result)

	compressed = {}
	# Core pattern fields
	for key in ("vcp_detected", "contractions_count", "contraction_ratios",
				"contraction_ratio_grades", "base_duration_weeks",
				"correction_depths", "pivot_price", "technical_footprint",
				"pattern_type", "pattern_quality", "first_correction_zone",
				"setup_readiness"):
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

	# Pivot tightness
	pt = vcp_result.get("pivot_tightness", {})
	if pt:
		compressed["pivot_tightness"] = pt

	return compressed


def postprocess_results(results):
	"""Apply all post-processing to module results.

	Args:
		results: dict of module name -> module output

	Returns:
		dict of module name -> compressed module output
	"""
	processed = dict(results)

	# Compress earnings
	if "earnings_acceleration" in processed:
		processed["earnings_acceleration"] = compress_earnings(
			processed["earnings_acceleration"])

	# Compress volume analysis
	if "volume_analysis" in processed:
		processed["volume_analysis"] = compress_volume_analysis(
			processed["volume_analysis"])

	# Compress VCP
	if "vcp" in processed:
		processed["vcp"] = compress_vcp(processed["vcp"])

	return processed
