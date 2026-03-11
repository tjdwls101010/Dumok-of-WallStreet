"""Control-layer builders for the Serenity pipeline.

Materiality signals, causal bridge, priced-in assessment,
institutional flow, and expression-layer logic.
"""


def _build_materiality_signals(l3_data, l4_results, l5_results, sec_sc_results):
	"""Compute materiality-relevant signals from existing pipeline data.

	Surfaces structured data for agent materiality classification.
	Does NOT classify materiality itself — that requires event context
	the pipeline cannot know. Provides the quantitative foundation.
	"""
	l4 = l4_results or {}
	info = l4.get("info") or {}

	# 1. Supply Chain Exposure (from L3)
	l3 = l3_data or {}
	sec_sc = l3.get("sec_supply_chain") or {}
	suppliers = sec_sc.get("suppliers") or []
	customers = sec_sc.get("customers") or []
	single_source = sec_sc.get("single_source_dependencies") or []
	geo_conc = sec_sc.get("geographic_concentration") or []

	supply_chain_exposure = {
		"supplier_count": len(suppliers),
		"customer_count": len(customers),
		"single_source_count": len(single_source),
		"geographic_risk_count": len(geo_conc),
		"has_sec_data": l3.get("sec_status") == "SEC_SC_available",
		"exposure_level": (
			"high" if len(single_source) >= 2 or len(geo_conc) >= 2
			else "moderate" if len(single_source) >= 1
			else "low"
		),
	}

	# 2. Margin Sensitivity (from L4 margin_tracker)
	margin = l4.get("margin_tracker") or {}
	gross_margin = info.get("grossMargins")
	op_margin = info.get("operatingMargins")
	margin_flag = str(margin.get("flag", ""))

	margin_sensitivity = {
		"gross_margin_pct": round(gross_margin * 100, 1) if isinstance(gross_margin, (int, float)) else None,
		"operating_margin_pct": round(op_margin * 100, 1) if isinstance(op_margin, (int, float)) else None,
		"margin_trend": margin_flag or "unknown",
		"operating_leverage": (
			"high" if isinstance(gross_margin, (int, float)) and isinstance(op_margin, (int, float))
			and gross_margin > 0 and (gross_margin - op_margin) / gross_margin > 0.5
			else "moderate" if isinstance(gross_margin, (int, float)) and gross_margin > 0.4
			else "low"
		),
	}

	# 3. Earnings Materiality (from L4/L5)
	ea = l4.get("earnings_acceleration") or {}
	surprise = l5_results.get("earnings_surprise") or {} if l5_results else {}
	rev_traj = l4.get("revenue_trajectory") or {}

	latest_rev_growth = None
	quarters = rev_traj.get("quarters") or []
	if len(quarters) >= 2:
		q_latest = quarters[-1].get("revenue")
		q_prev = quarters[-2].get("revenue")
		if isinstance(q_latest, (int, float)) and isinstance(q_prev, (int, float)) and q_prev > 0:
			latest_rev_growth = round((q_latest - q_prev) / q_prev * 100, 1)

	earnings_materiality = {
		"consecutive_beats": surprise.get("consecutive_beats"),
		"sales_accelerating": ea.get("sales_accelerating"),
		"latest_rev_growth_qoq_pct": latest_rev_growth,
		"sales_growth_rates": ea.get("sales_growth_rates"),
	}

	# 4. Recent SEC Events (from sec_sc_results)
	sec_events_raw = (sec_sc_results or {}).get("sec_events") or {}
	events = []
	if not sec_events_raw.get("error"):
		for ev in (sec_events_raw.get("data") or [])[:5]:
			events.append({
				"type": ev.get("event_type"),
				"date": ev.get("filing_date"),
				"context": (ev.get("context") or "")[:200],
			})

	# 5. Exposure Summary (one-line for quick scan)
	parts = []
	if supply_chain_exposure["single_source_count"] > 0:
		parts.append(f"{supply_chain_exposure['single_source_count']} single-source dependencies")
	if supply_chain_exposure["geographic_risk_count"] > 0:
		parts.append(f"{supply_chain_exposure['geographic_risk_count']} geographic concentration risks")
	if margin_sensitivity["operating_leverage"] == "high":
		parts.append("high operating leverage (margin-sensitive)")
	exposure_summary = "; ".join(parts) if parts else "Low supply chain exposure detected"

	return {
		"supply_chain_exposure": supply_chain_exposure,
		"margin_sensitivity": margin_sensitivity,
		"earnings_materiality": earnings_materiality,
		"recent_sec_events": events,
		"exposure_summary": exposure_summary,
	}


def _summarize_rev_trajectory_brief(rev_traj):
	"""One-line summary of revenue trajectory from 8-quarter data."""
	quarters = rev_traj.get("quarters") or []
	if len(quarters) < 2:
		return "insufficient_data"
	revenues = [q.get("revenue") for q in quarters if isinstance(q.get("revenue"), (int, float))]
	if len(revenues) < 2:
		return "insufficient_data"
	latest, earliest = revenues[-1], revenues[0]
	if earliest > 0:
		total_growth = (latest - earliest) / earliest * 100
		direction = "accelerating" if len(revenues) >= 3 and latest > revenues[-2] > revenues[-3] else "growing"
		return f"{direction} ({total_growth:+.0f}% over {len(revenues)}Q)"
	return "unknown"


def _build_causal_bridge_data(l1_result, l3_data, l4_results, l5_results, capex_data):
	"""Pre-fill the causal bridge chain with available pipeline data.

	Output: structured data for each causal bridge layer.
	Agent completes the bridge by connecting layers with causal reasoning.
	"""
	l1 = l1_result if isinstance(l1_result, dict) else {}
	l4 = l4_results or {}
	l3 = l3_data or {}
	info = l4.get("info") or {}

	# Layer 1: Macro Context
	macro_context = {
		"regime": l1.get("regime", "unknown"),
		"risk_level": l1.get("risk_level", "unknown"),
		"key_signals": [],
	}
	signals = l1.get("signals") or {}
	if signals.get("vix_regime"):
		macro_context["key_signals"].append(f"VIX regime: {signals['vix_regime']}")
	if signals.get("net_liq_direction"):
		macro_context["key_signals"].append(f"Net liquidity: {signals['net_liq_direction']}")
	if signals.get("real_rate") is not None:
		macro_context["key_signals"].append(f"Real rate: {signals['real_rate']}%")

	# Layer 2: Supply Chain Position
	bn_pre = l3.get("bottleneck_pre_score") or {}
	supply_chain_position = {
		"sector": info.get("sector"),
		"industry": info.get("industry"),
		"bottleneck_pre_score": bn_pre.get("pre_score"),
		"key_dependencies": [],
		"sec_available": l3.get("sec_status") == "SEC_SC_available",
	}
	sec_sc = l3.get("sec_supply_chain") or {}
	for dep in (sec_sc.get("single_source_dependencies") or [])[:3]:
		if isinstance(dep, dict):
			supply_chain_position["key_dependencies"].append(dep.get("supplier") or dep.get("name") or str(dep))
		elif isinstance(dep, str):
			supply_chain_position["key_dependencies"].append(dep)

	# Layer 3: Financial Transmission
	margin = l4.get("margin_tracker") or {}
	rev_traj = l4.get("revenue_trajectory") or {}
	capex = capex_data or {}

	financial_transmission = {
		"revenue_trajectory": _summarize_rev_trajectory_brief(rev_traj),
		"margin_trend": str(margin.get("flag", "unknown")),
		"capex_direction": capex.get("direction") if isinstance(capex, dict) else "unknown",
		"capex_trend_quarters": capex.get("quarters_count") if isinstance(capex, dict) else None,
	}

	# Layer 4: Valuation Gap
	ngv = l4.get("no_growth_valuation") or {}
	fpe = l4.get("forward_pe") or {}
	current_price = info.get("currentPrice")

	no_growth_floor = ngv.get("intrinsic_value") or ngv.get("no_growth_value")
	forward_pe_val = fpe.get("forward_pe")

	valuation_gap = {
		"current_price": current_price,
		"no_growth_floor": no_growth_floor,
		"no_growth_gap_pct": (
			round((current_price - no_growth_floor) / no_growth_floor * 100, 1)
			if isinstance(current_price, (int, float)) and isinstance(no_growth_floor, (int, float)) and no_growth_floor > 0
			else None
		),
		"forward_pe": forward_pe_val,
		"growth_upside": ngv.get("margin_of_safety_pct"),
	}

	return {
		"macro_context": macro_context,
		"supply_chain_position": supply_chain_position,
		"financial_transmission": financial_transmission,
		"valuation_gap": valuation_gap,
		"note": "Causal bridge data pre-filled from pipeline. Agent must connect layers with event-specific causal reasoning.",
	}


def _build_priced_in_assessment(l4_results, l5_results):
	"""Compute priced-in risk assessment from L4/L5 data.

	Composite score 0-100:
	- Higher score = more priced in (less upside)
	- Lower score = less priced in (more opportunity)
	"""
	l4 = l4_results or {}
	l5 = l5_results or {}
	info = l4.get("info") or {}

	signals = {}
	risk_score = 0.0

	# Signal 1: 52W Range Position (0-100)
	current = info.get("currentPrice")
	low52 = info.get("fiftyTwoWeekLow")
	high52 = info.get("fiftyTwoWeekHigh")
	range_pct = None
	if all(isinstance(v, (int, float)) for v in [current, low52, high52]) and high52 > low52:
		range_pct = round((current - low52) / (high52 - low52) * 100, 1)
		signals["52w_range_pct"] = range_pct
		if range_pct > 80:
			risk_score += 18
		elif range_pct > 60:
			risk_score += 10
		elif range_pct < 20:
			risk_score -= 5
	else:
		signals["52w_range_pct"] = None

	# Signal 2: Price vs 50d MA
	ma50 = info.get("fiftyDayAverage")
	if isinstance(current, (int, float)) and isinstance(ma50, (int, float)) and ma50 > 0:
		ma50_gap = round((current - ma50) / ma50 * 100, 1)
		signals["price_vs_50d_ma_pct"] = ma50_gap
		if ma50_gap > 20:
			risk_score += 12
		elif ma50_gap > 10:
			risk_score += 6
	else:
		signals["price_vs_50d_ma_pct"] = None

	# Signal 3: Price vs 200d MA
	ma200 = info.get("twoHundredDayAverage")
	if isinstance(current, (int, float)) and isinstance(ma200, (int, float)) and ma200 > 0:
		ma200_gap = round((current - ma200) / ma200 * 100, 1)
		signals["price_vs_200d_ma_pct"] = ma200_gap
		if ma200_gap > 30:
			risk_score += 15
		elif ma200_gap > 15:
			risk_score += 8
	else:
		signals["price_vs_200d_ma_pct"] = None

	# Signal 4: Short Interest
	si = info.get("shortPercentOfFloat")
	signals["short_interest_pct"] = round(si * 100, 1) if isinstance(si, (int, float)) else None
	if isinstance(si, (int, float)):
		if si < 0.03:
			risk_score += 8
		elif si > 0.15:
			risk_score -= 5

	# Signal 5: Analyst Price Target Gap
	pt_data = l5.get("analyst_price_targets") or {}
	mean_target = pt_data.get("mean") or pt_data.get("targetMeanPrice")
	if isinstance(current, (int, float)) and isinstance(mean_target, (int, float)) and current > 0:
		target_gap = round((mean_target - current) / current * 100, 1)
		signals["analyst_target_gap_pct"] = target_gap
		if target_gap < 5:
			risk_score += 18
		elif target_gap < 15:
			risk_score += 10
		elif target_gap > 40:
			risk_score -= 5
	else:
		signals["analyst_target_gap_pct"] = None

	# Signal 6: Revision Direction
	rev_data = l5.get("analyst_revisions") or {}
	rev_dir = rev_data.get("revisions_direction", "unknown") if not rev_data.get("error") else "unknown"
	signals["revision_direction"] = rev_dir
	if rev_dir == "up":
		risk_score += 12
	elif rev_dir == "down":
		risk_score -= 8

	# Signal 7: Revision Magnitude (if available)
	rev_magnitude = None
	for key in ("current_year", "next_year"):
		val = rev_data.get(key)
		if isinstance(val, dict):
			change = val.get("change") or val.get("revision")
			if isinstance(change, (int, float)):
				rev_magnitude = change
				break
		elif isinstance(val, (int, float)):
			rev_magnitude = val
			break
	signals["revision_magnitude"] = rev_magnitude

	# Signal 8: IO Quality Score
	io_data = l4.get("institutional_quality") or {}
	io_score = io_data.get("io_quality_score")
	signals["io_quality_score"] = io_score
	if isinstance(io_score, (int, float)):
		if io_score >= 8:
			risk_score += 12
		elif io_score >= 6:
			risk_score += 6
		elif io_score <= 3:
			risk_score -= 5

	# Clamp and classify
	risk_score = max(0, min(100, round(risk_score)))

	if risk_score >= 55:
		assessment = "fully_priced_in"
	elif risk_score >= 30:
		assessment = "partially_priced_in"
	else:
		assessment = "not_priced_in"

	return {
		"signals": signals,
		"risk_score": risk_score,
		"assessment": assessment,
		"note": f"Priced-in risk score {risk_score}/100 -> {assessment}. Agent must contextualize with sector/event awareness.",
		"signal_weights": {
			"52w_range_position": "+18 (>80%) / +10 (>60%) / -5 (<20%)",
			"price_vs_50d_ma": "+12 (>20% above) / +6 (>10%)",
			"price_vs_200d_ma": "+15 (>30% above) / +8 (>15%)",
			"short_interest": "+8 (<3%) / -5 (>15%)",
			"analyst_target_gap": "+18 (<5% to target) / +10 (<15%) / -5 (>40%)",
			"revision_direction": "+12 (up) / -8 (down)",
			"io_quality": "+12 (>=8) / +6 (>=6) / -5 (<=3)",
			"total_range": "0-100, clamped",
			"assessment_thresholds": "fully_priced_in: >=55 | partially_priced_in: >=30 | not_priced_in: <30",
		},
	}


def _build_institutional_flow(l4_results):
	"""Extract institutional flow signals from L4 data."""
	l4 = l4_results or {}

	# Insider direction
	insider = l4.get("insider_transactions") or {}
	insider_summary = insider.get("summary") or {}
	insider_direction = insider_summary.get("net_direction", "unknown")
	insider_net_value = insider_summary.get("net_value")

	# IO quality
	io = l4.get("institutional_quality") or {}
	io_score = io.get("io_quality_score")
	io_assessment = (
		"strong_accumulation" if isinstance(io_score, (int, float)) and io_score >= 8
		else "healthy" if isinstance(io_score, (int, float)) and io_score >= 5
		else "weak" if isinstance(io_score, (int, float))
		else "unknown"
	)

	# IV signal
	iv = l4.get("iv_context") or {}
	iv_percentile = iv.get("iv_percentile") or iv.get("percentile") or iv.get("iv_rank")
	iv_regime = (
		"elevated" if isinstance(iv_percentile, (int, float)) and iv_percentile > 70
		else "depressed" if isinstance(iv_percentile, (int, float)) and iv_percentile < 30
		else "normal" if isinstance(iv_percentile, (int, float))
		else "unknown"
	)

	# Composite flow assessment
	flow_signals = []
	if insider_direction == "buying":
		flow_signals.append("insider_accumulation")
	if insider_direction == "selling":
		flow_signals.append("insider_distribution")
	if io_assessment == "strong_accumulation":
		flow_signals.append("institutional_conviction")
	if io_assessment == "weak":
		flow_signals.append("institutional_exit_risk")

	return {
		"insider_net_direction": insider_direction,
		"insider_net_value": insider_net_value,
		"io_quality_score": io_score,
		"io_assessment": io_assessment,
		"iv_percentile": iv_percentile,
		"iv_regime": iv_regime,
		"flow_signals": flow_signals,
		"flow_assessment": (
			"positive" if "insider_accumulation" in flow_signals or "institutional_conviction" in flow_signals
			else "negative" if "insider_distribution" in flow_signals and "institutional_exit_risk" in flow_signals
			else "neutral"
		),
	}


def _build_expression_layer(l4_results, composite_signal):
	"""Recommend thesis expression vehicle based on IV and conviction."""
	l4 = l4_results or {}
	iv = l4.get("iv_context") or {}

	iv_percentile = iv.get("iv_percentile") or iv.get("percentile") or iv.get("iv_rank")
	iv_rank = iv.get("iv_rank")

	# Conviction from composite signal
	cs = composite_signal if isinstance(composite_signal, dict) else {}
	grade = cs.get("grade", "HOLD")
	conviction = cs.get("position_guidance", {}).get("conviction_tier")

	# Expression logic
	if not isinstance(iv_percentile, (int, float)):
		recommended = "shares"
		reasoning = "IV data unavailable — default to shares"
	elif iv_percentile > 70:
		if grade in ("STRONG_BUY", "BUY", "ACCUMULATE"):
			recommended = "csp"
			reasoning = f"IV elevated ({iv_percentile}th pctl) + bullish thesis -> sell puts for better entry"
		else:
			recommended = "covered_calls"
			reasoning = f"IV elevated ({iv_percentile}th pctl) + neutral/weak thesis -> write calls for income"
	elif iv_percentile < 30:
		if grade in ("STRONG_BUY", "BUY"):
			recommended = "leaps"
			reasoning = f"IV depressed ({iv_percentile}th pctl) + high conviction -> buy LEAPS for leverage"
		else:
			recommended = "shares"
			reasoning = f"IV depressed ({iv_percentile}th pctl) + moderate conviction -> shares (LEAPS need higher conviction)"
	else:
		recommended = "shares"
		reasoning = f"IV neutral ({iv_percentile}th pctl) -> shares (no clear vol edge)"

	return {
		"iv_percentile": iv_percentile,
		"iv_rank": iv_rank,
		"iv_regime": (
			"elevated" if isinstance(iv_percentile, (int, float)) and iv_percentile > 70
			else "depressed" if isinstance(iv_percentile, (int, float)) and iv_percentile < 30
			else "normal" if isinstance(iv_percentile, (int, float))
			else "unknown"
		),
		"conviction_tier": conviction,
		"recommended_vehicle": recommended,
		"reasoning": reasoning,
		"iv_thresholds": "elevated: >70th percentile | depressed: <30th | normal: 30-70th",
	}
