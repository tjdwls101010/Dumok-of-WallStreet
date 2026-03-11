"""Thesis signal generation, SoP triggers, trapped-asset override, taxonomy
classification, earnings proximity parsing, and composite investment grade
derivation for the Serenity pipeline."""

import re
from datetime import datetime


def _build_thesis_signals(l4_results, l5_results):
	"""Map L4/L5 results to thesis strengthening/weakening signals."""
	l4 = l4_results or {}
	l5 = l5_results or {}
	strengthening = []
	weakening = []

	margin_tracker = l4.get("margin_tracker") or {}
	earnings_acc = l4.get("earnings_acceleration") or {}
	margin_flag = str(margin_tracker.get("flag", ""))

	# Strengthening
	if "EXPANDING" in margin_flag.upper() and earnings_acc.get("sales_accelerating") is True:
		strengthening.append("pricing_power_confirmed")
	earnings_surprise = l5.get("earnings_surprise") or {}
	beats = earnings_surprise.get("consecutive_beats", 0)
	if isinstance(beats, (int, float)) and beats >= 3:
		strengthening.append("execution_validated")
	analyst_rev = l5.get("analyst_revisions") or {}
	if analyst_rev and not analyst_rev.get("error"):
		rev_dir = analyst_rev.get("revisions_direction", "")
		if isinstance(rev_dir, str) and rev_dir.lower() == "up":
			strengthening.append("street_catching_up")
		else:
			for key in ("current_quarter", "next_quarter", "current_year", "next_year"):
				val = analyst_rev.get(key)
				if isinstance(val, dict):
					val = val.get("change") or val.get("revision")
				if isinstance(val, (int, float)) and val > 0:
					strengthening.append("street_catching_up")
					break
	inst_quality = l4.get("institutional_quality") or {}
	io_score = inst_quality.get("io_quality_score")
	if isinstance(io_score, (int, float)) and io_score >= 7:
		strengthening.append("smart_money_accumulating")

	# Weakening
	if "COLLAPSE" in margin_flag.upper():
		weakening.append("pricing_power_eroding")
	sbc = l4.get("sbc_analyzer") or {}
	if str(sbc.get("flag", "")).lower() == "toxic" or str(sbc.get("dilution_flag", "")).lower() == "active_dilution":
		weakening.append("dilution_destroying_value")
	if earnings_acc.get("sales_accelerating") is False:
		sgr = earnings_acc.get("sales_growth_rates")
		if isinstance(sgr, list) and len(sgr) > 0 and isinstance(sgr[-1], (int, float)) and sgr[-1] < 0:
			weakening.append("demand_weakening")
	if isinstance(io_score, (int, float)) and io_score <= 3:
		weakening.append("institutional_exit")

	s_count, w_count = len(strengthening), len(weakening)
	net_direction = "strengthening" if s_count > w_count else "weakening" if w_count > s_count else "neutral"

	# Raw data for agent reasoning
	detail = {
		"margin_flag": margin_flag or None,
		"sales_accelerating": earnings_acc.get("sales_accelerating"),
		"sales_growth_rates": earnings_acc.get("sales_growth_rates"),
		"consecutive_beats": beats if isinstance(beats, (int, float)) else None,
		"revisions_direction": analyst_rev.get("revisions_direction") if not analyst_rev.get("error") else None,
		"io_quality_score": io_score,
		"sbc_flag": sbc.get("flag") or sbc.get("dilution_flag"),
	}

	return {
		"strengthening": strengthening, "weakening": weakening, "net_direction": net_direction,
		"conviction_delta": s_count - w_count, "detail": detail,
		"signal_definitions": {
			"pricing_power_confirmed": "Margins expanding while sales accelerating — company raising prices successfully",
			"execution_validated": "3+ consecutive earnings beats — consistent delivery",
			"street_catching_up": "Analyst revisions trending upward — consensus lagging actual performance",
			"smart_money_accumulating": "IO quality score >= 7 — quality institutions building positions",
			"pricing_power_eroding": "Margin collapse — competitive pressure or cost inflation destroying pricing power",
			"dilution_destroying_value": "SBC toxic or active dilution — shareholder value being eroded",
			"demand_weakening": "Sales decelerating with negative growth — demand slowing",
			"institutional_exit": "IO quality score <= 3 — smart money leaving",
		},
	}


def _check_sop_triggers(l4_results):
	"""Detect Sum-of-Parts valuation triggers from info and financials."""
	l4 = l4_results or {}
	info = l4.get("info") or {}
	debt_structure = l4.get("debt_structure") or {}
	triggers_found = []
	notes_parts = []

	conglomerate_keywords = ("conglomerate", "diversified", "holding", "industrial conglomerate")
	sector = str(info.get("sector", "")).lower()
	industry = str(info.get("industry", "")).lower()
	for kw in conglomerate_keywords:
		if kw in sector or kw in industry:
			triggers_found.append("conglomerate_classification")
			notes_parts.append("sector/industry classified as conglomerate or diversified")
			break

	summary = str(info.get("longBusinessSummary", ""))
	segment_keywords = ("subsidiary", "subsidiaries", "division", "divisions", "segment", "segments", "business unit")
	if sum(1 for kw in segment_keywords if kw in summary.lower()) >= 2:
		triggers_found.append("multi_segment_description")
		notes_parts.append("company description mentions multiple business segments")

	market_cap = info.get("marketCap")
	total_cash = info.get("totalCash") or debt_structure.get("total_cash")
	if isinstance(market_cap, (int, float)) and market_cap > 0 and isinstance(total_cash, (int, float)):
		cash_ratio = total_cash / market_cap
		if cash_ratio > 0.20:
			triggers_found.append("cash_exceeds_20pct_mc")
			notes_parts.append(f"cash exceeds 20% of market cap ({cash_ratio:.0%})")

	triggered = len(triggers_found) > 0
	note = ("SoP analysis recommended — " + " and ".join(notes_parts) + ".") if triggered else "No SoP triggers detected."
	return {"triggered": triggered, "triggers_found": triggers_found, "note": note}


_RESTRUCTURING_KEYWORDS = re.compile(
	r"restructur|strategic\s+review|activist|asset\s+sale|"
	r"spin.?off|separation|divestiture|management\s+change",
	re.IGNORECASE,
)


def _check_trapped_asset_override(l4_results, bottleneck_pre_score_result, sec_sc_results=None):
	"""Check conditions for the Trapped Asset Override valuation path."""
	if bottleneck_pre_score_result is None or (isinstance(bottleneck_pre_score_result, dict) and "error" in bottleneck_pre_score_result):
		return {"conditions_met": 0, "condition_details": {}, "eligible": False, "note": "Cannot evaluate — no bottleneck pre-score available."}

	l4 = l4_results or {}
	info = l4.get("info") or {}
	debt_structure = l4.get("debt_structure") or {}
	condition_details = {}
	conditions_met = 0

	# Condition 1: Bottleneck pre_score >= 3.0
	pre_score = bottleneck_pre_score_result.get("pre_score", 0)
	bn_met = isinstance(pre_score, (int, float)) and pre_score >= 3.0
	condition_details["bottleneck_score"] = {"met": bn_met, "value": pre_score, "threshold": 3.0}
	if bn_met:
		conditions_met += 1

	# Condition 2: Physical asset floor > 50% of market cap
	asset_ratio = None
	asset_note = "Insufficient data"
	market_cap = info.get("marketCap")
	bv = info.get("bookValue")
	shares = info.get("sharesOutstanding")
	if isinstance(bv, (int, float)) and isinstance(shares, (int, float)) and isinstance(market_cap, (int, float)) and market_cap > 0:
		asset_ratio = (bv * shares) / market_cap
		asset_note = f"Book value / MC = {asset_ratio:.0%}"
	else:
		total_equity = debt_structure.get("book_value") or debt_structure.get("total_equity")
		if isinstance(total_equity, (int, float)) and isinstance(market_cap, (int, float)) and market_cap > 0:
			asset_ratio = total_equity / market_cap
			asset_note = f"Total equity / MC = {asset_ratio:.0%}"

	asset_met = isinstance(asset_ratio, (int, float)) and asset_ratio > 0.50
	condition_details["physical_asset_floor"] = {"met": asset_met, "value": asset_ratio, "threshold": 0.50, "note": asset_note}
	if asset_met:
		conditions_met += 1

	# Condition 3: Active Restructuring Catalyst (from SEC events)
	restructuring_catalyst = False
	catalyst_evidence = "No SEC events data available"
	if sec_sc_results:
		events_raw = sec_sc_results.get("sec_events", {})
		events_data = events_raw.get("data", []) if not events_raw.get("error") else []
		for event in events_data:
			text = f"{event.get('event_type', '')} {event.get('context', '')}"
			if _RESTRUCTURING_KEYWORDS.search(text):
				restructuring_catalyst = True
				catalyst_evidence = f"Restructuring signal found: {event.get('event_type', 'unknown')}"
				break
		if not restructuring_catalyst and events_data:
			catalyst_evidence = f"Checked {len(events_data)} SEC events — no restructuring signals"
	condition_details["restructuring_catalyst"] = {"met": restructuring_catalyst, "evidence": catalyst_evidence}
	if restructuring_catalyst:
		conditions_met += 1

	eligible = conditions_met >= 3
	note = f"{conditions_met}/3 override conditions met."
	return {"conditions_met": conditions_met, "condition_details": condition_details, "eligible": eligible, "note": note}


def _auto_classify_taxonomy(l4_results, bottleneck_pre_score):
	"""Rule-based L6 taxonomy pre-classification."""
	classification = "unclassified"
	confidence = "low"
	evidence = []

	l4 = l4_results if isinstance(l4_results, dict) else {}
	info = l4.get("info") or {}
	if isinstance(info, dict) and info.get("error"):
		info = {}
	forward_pe = l4.get("forward_pe") or {}
	if isinstance(forward_pe, dict) and forward_pe.get("error"):
		forward_pe = {}
	earnings_acc = l4.get("earnings_acceleration") or {}
	if isinstance(earnings_acc, dict) and earnings_acc.get("error"):
		earnings_acc = {}

	market_cap = info.get("marketCap")
	gross_margins = info.get("grossMargins")
	revenue_growth = forward_pe.get("revenue_growth_yoy")
	sales_accelerating = earnings_acc.get("sales_accelerating")

	# Rule 1: Bottleneck
	bn = bottleneck_pre_score if isinstance(bottleneck_pre_score, dict) and not (bottleneck_pre_score or {}).get("error") else None
	if bn:
		ps = bn.get("pre_score", 0)
		if isinstance(ps, (int, float)) and ps >= 3.0:
			classification = "bottleneck"
			evidence.append(f"bottleneck_pre_score {ps}/{bn.get('pre_score_max', 4.25)} >= 3.0")
			confidence = "high" if ps >= 3.5 else "medium"

	# Rule 2: Evolution
	if classification == "unclassified" and isinstance(market_cap, (int, float)) and market_cap > 10e9:
		growth_met = False
		if isinstance(revenue_growth, (int, float)) and revenue_growth > 0.20:
			growth_met = True
			evidence.append(f"revenue_growth_yoy {revenue_growth:.2f} > 0.20")
		if sales_accelerating is True:
			growth_met = True
			evidence.append("sales_accelerating")
		if growth_met:
			classification = "evolution"
			evidence.append(f"marketCap {market_cap/1e9:.1f}B > 10B")
			confidence = "high" if (isinstance(revenue_growth, (int, float)) and revenue_growth > 0.20 and sales_accelerating is True) else "medium"

	# Rule 3: Disruption
	if classification == "unclassified" and isinstance(market_cap, (int, float)) and market_cap < 10e9:
		if isinstance(gross_margins, (int, float)) and gross_margins > 0.40 and isinstance(revenue_growth, (int, float)) and revenue_growth > 0.50:
			classification = "disruption"
			evidence.append(f"marketCap {market_cap/1e9:.1f}B < 10B, grossMargins {gross_margins:.2f}, revenue_growth {revenue_growth:.2f}")
			confidence = "high" if gross_margins > 0.60 and revenue_growth > 0.80 else "medium"

	if classification == "unclassified":
		evidence.append("No rule matched")

	return {"classification": classification, "confidence": confidence, "evidence": evidence, "requires_llm": True,
		"note": "Rule-based pre-classification. Agent should verify and may override."}


def _parse_days_to_earnings(l5_results):
	"""Parse L5 earnings_dates and return days until the nearest future date."""
	if not isinstance(l5_results, dict):
		return None
	ed = l5_results.get("earnings_dates")
	if not isinstance(ed, dict) or ed.get("error"):
		return None
	dates_col = ed.get("Earnings Date", {})
	if not isinstance(dates_col, dict):
		return None
	now = datetime.now()
	min_days = None
	for _idx, date_str in dates_col.items():
		if not isinstance(date_str, str):
			continue
		for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%b %d, %Y"):
			try:
				dt = datetime.strptime(date_str.strip(), fmt)
				delta = (dt - now).days
				if delta >= 0 and (min_days is None or delta < min_days):
					min_days = delta
				break
			except ValueError:
				continue
	return min_days


def _generate_composite_signal(l1_result, l4_results, l5_results, health_severity_score,
	bottleneck_pre_score, thesis_signals, auto_classification, trapped_asset_override):
	"""Generate integrated investment grade from all pipeline data."""
	score_breakdown = {}
	total_score = 0.0

	l1 = l1_result if isinstance(l1_result, dict) else {}
	regime = l1.get("regime", "transitional")

	# Component 1: Bottleneck (30 pts)
	bn = bottleneck_pre_score if isinstance(bottleneck_pre_score, dict) and not (bottleneck_pre_score or {}).get("error") else {}
	bn_raw = bn.get("pre_score", 0) if bn else 0
	if not isinstance(bn_raw, (int, float)):
		bn_raw = 0
	bn_max = bn.get("pre_score_max", 4.25) if bn else 4.25
	bn_points = (bn_raw / bn_max) * 30.0
	score_breakdown["bottleneck"] = {"raw": bn_raw if bn else None, "max": bn_max, "points": round(bn_points, 2)}
	total_score += bn_points

	# Component 2: Health severity (25 pts) — 5 gates (4 original + io_quality_concern)
	if isinstance(health_severity_score, (int, float)):
		hs_points = (health_severity_score / 5.0) * 25.0
		score_breakdown["health"] = {"raw": health_severity_score, "max": 5.0, "points": round(hs_points, 2)}
	else:
		hs_points = 0.0
		score_breakdown["health"] = {"raw": None, "max": 5.0, "points": 0.0, "note": "unavailable"}
	total_score += hs_points

	# Component 3: Thesis signals (15 pts)
	ts = thesis_signals if isinstance(thesis_signals, dict) else {}
	ts_dir = ts.get("net_direction", "neutral")
	ts_points = 15.0 if ts_dir == "strengthening" else 7.5 if ts_dir == "neutral" else 0.0
	score_breakdown["thesis"] = {"direction": ts_dir, "points": round(ts_points, 2)}
	total_score += ts_points

	# Component 4: Catalyst proximity (10 pts)
	days = _parse_days_to_earnings(l5_results)
	cat_points = 10.0 if (days is not None and days <= 30) else 5.0 if (days is not None and days <= 60) else 0.0
	score_breakdown["catalyst"] = {"days_to_earnings": days, "points": round(cat_points, 2)}
	total_score += cat_points

	# Component 5: Taxonomy (10 pts)
	ac = auto_classification if isinstance(auto_classification, dict) else {}
	ac_class = ac.get("classification", "unclassified")
	tax_points = 10.0 if ac_class in ("bottleneck", "disruption") else 7.0 if ac_class == "evolution" else 5.0
	score_breakdown["taxonomy"] = {"classification": ac_class, "points": round(tax_points, 2)}
	total_score += tax_points

	# Component 6: Valuation MoS (10 pts)
	l4 = l4_results if isinstance(l4_results, dict) else {}
	ngv = l4.get("no_growth_valuation") or {}
	if isinstance(ngv, dict) and ngv.get("error"):
		ngv = {}
	mos_pct = ngv.get("margin_of_safety_pct")
	if isinstance(mos_pct, (int, float)):
		val_points = 10.0 if mos_pct > 20 else 5.0 if mos_pct >= 0 else 0.0
		score_breakdown["valuation"] = {"mos_pct": round(mos_pct, 2), "points": round(val_points, 2)}
	else:
		val_points = 0.0
		score_breakdown["valuation"] = {"mos_pct": None, "points": 0.0, "note": "unavailable"}
	total_score += val_points

	# Regime cap & trapped asset override
	regime_cap_applied = False
	trapped_override_applied = False
	ta = trapped_asset_override if isinstance(trapped_asset_override, dict) else {}
	ta_eligible = ta.get("eligible") is True

	if regime == "risk_off":
		if ta_eligible:
			trapped_override_applied = True
		else:
			if total_score > 49:
				total_score = 49.0
			regime_cap_applied = True

	total_score = round(total_score, 2)

	# Grade mapping
	if trapped_override_applied and total_score >= 50:
		grade = "MOONSHOT"
	elif total_score >= 80:
		grade = "STRONG_BUY"
	elif total_score >= 65:
		grade = "BUY"
	elif total_score >= 50:
		grade = "ACCUMULATE"
	elif total_score >= 35:
		grade = "HOLD"
	else:
		grade = "AVOID"

	# Position sizing
	pos_table = {
		"STRONG_BUY": ("High", "5-7%", "1.5%"), "BUY": ("Medium", "2-4%", "1.0%"),
		"ACCUMULATE": ("Low", "1-2%", "0.5%"), "HOLD": (None, "hold_existing", None),
		"AVOID": (None, "no_entry", None), "MOONSHOT": ("Special", "max_5%", "2.5%"),
	}
	conviction, size, max_loss = pos_table.get(grade, (None, "no_entry", None))
	regime_adj = "risk_off_0.5x" if regime == "risk_off" else "transitional_0.75x" if regime == "transitional" else "none"

	return {
		"composite_score": total_score, "grade": grade, "score_breakdown": score_breakdown,
		"position_guidance": {"conviction_tier": conviction, "suggested_size_pct": size, "max_loss_pct": max_loss, "regime_adjustment": regime_adj},
		"regime_cap_applied": regime_cap_applied, "trapped_asset_override_applied": trapped_override_applied,
		"requires_agent_review": True, "note": "Automated composite signal. Agent must review before final rating assignment.",
		"score_methodology": {
			"components": "bottleneck(30) + health(25) + thesis(15) + catalyst(10) + taxonomy(10) + valuation_mos(10) = max 100",
			"grade_thresholds": "STRONG_BUY: >=80 | BUY: >=65 | ACCUMULATE: >=50 | HOLD: >=35 | AVOID: <35 | MOONSHOT: >=50 + trapped_asset",
			"regime_cap": "risk_off regime caps score at 49 (max HOLD) unless trapped_asset eligible",
			"caveat": "Agent must verify component breakdown. A high total score with low health component may mask fundamental weakness.",
		},
	}
