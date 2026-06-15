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
	earnings_acc = l4.get("growth_profile") or {}
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
		rev_dir = analyst_rev.get("trend_direction", "")
		if isinstance(rev_dir, str) and rev_dir.lower() == "rising":
			strengthening.append("street_catching_up")
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
		"trend_direction": analyst_rev.get("trend_direction") if not analyst_rev.get("error") else None,
		"io_quality_score": io_score,
		"sbc_flag": sbc.get("flag") or sbc.get("dilution_flag"),
	}

	return {
		"strengthening": strengthening, "weakening": weakening, "net_direction": net_direction,
		"conviction_delta": s_count - w_count,
	}


def _classify_dilution(l4_results):
	"""Classify dilution as growth, value-destruction, or accounting illusion.

	Decision tree combining revenue growth, SBC ratio, and FCF reality.
	"""
	l4 = l4_results or {}
	sbc = l4.get("sbc_analyzer") or {}
	ea = l4.get("growth_profile") or {}
	fpe = l4.get("forward_pe") or {}

	if sbc.get("error"):
		return {"classification": "unknown", "note": "SBC data unavailable"}

	sbc_pct = sbc.get("sbc_pct_revenue")
	reported_fcf = sbc.get("reported_fcf")
	real_fcf = sbc.get("real_fcf")
	shares_change = sbc.get("shares_change_qoq_pct")

	# Revenue growth from forward_pe or growth_profile
	revenue_growth = None
	if isinstance(fpe, dict) and not fpe.get("error"):
		rg = fpe.get("revenue_growth_yoy")
		if isinstance(rg, (int, float)):
			revenue_growth = rg * 100 if rg < 1 else rg  # normalize to percent

	# Fallback: check sales growth from growth_profile
	if revenue_growth is None and isinstance(ea, dict) and not ea.get("error"):
		sgr = ea.get("sales_growth_rates")
		if isinstance(sgr, list) and sgr:
			latest = sgr[-1] if isinstance(sgr[-1], (int, float)) else None
			if latest is not None:
				revenue_growth = latest

	# Classification decision tree
	sbc_pct_val = sbc_pct if isinstance(sbc_pct, (int, float)) else 0
	growth_val = revenue_growth if isinstance(revenue_growth, (int, float)) else 0

	# Check accounting illusion first (highest priority)
	if (isinstance(reported_fcf, (int, float)) and isinstance(real_fcf, (int, float))
		and reported_fcf > 0 and real_fcf < 0):
		margin_data = l4.get("margin_tracker") or {}
		margin_flag = str(margin_data.get("flag", "")).upper()
		if "COMPRESSION" in margin_flag or "COLLAPSE" in margin_flag:
			classification = "accounting_illusion"
		else:
			classification = "accounting_illusion"
	elif growth_val > 25 and sbc_pct_val < 20:
		classification = "growth_dilution"
	elif growth_val < 5 and sbc_pct_val > 15:
		classification = "value_destruction"
	elif growth_val > 15 and sbc_pct_val < 30:
		classification = "acceptable"
	else:
		classification = "moderate_concern"

	return {
		"classification": classification,
		"revenue_growth_pct": round(growth_val, 1) if isinstance(growth_val, (int, float)) else None,
		"sbc_pct_revenue": sbc_pct,
		"reported_fcf": reported_fcf,
		"real_fcf": real_fcf,
		"shares_change_qoq_pct": shares_change,
		"thresholds": {
			"growth_dilution": "rev_growth > 25% + sbc < 20%",
			"value_destruction": "rev_growth < 5% + sbc > 15%",
			"accounting_illusion": "reported_fcf > 0 + real_fcf < 0",
			"acceptable": "rev_growth > 15% + sbc < 30%",
			"moderate_concern": "otherwise",
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
	earnings_acc = l4.get("growth_profile") or {}
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

	return {"classification": classification, "confidence": confidence, "evidence": evidence}


def _parse_days_to_earnings(l5_results):
	"""Days until the nearest FUTURE earnings date (fallback parser).

	Mirrors actions._parse_days_to_next_earnings: yfinance puts the dates in the
	DataFrame INDEX, so after normalize() they become the KEYS of each value
	column (e.g. "EPS Estimate": {"2026-08-26 16:00:00-04:00": 2.08, ...}) — there
	is no top-level "Earnings Date" column.
	"""
	if not isinstance(l5_results, dict):
		return None
	ed = l5_results.get("earnings_dates")
	if not isinstance(ed, dict) or ed.get("error"):
		return None
	date_strs = set()
	explicit = ed.get("Earnings Date")
	if isinstance(explicit, dict):
		date_strs.update(v for v in explicit.values() if isinstance(v, str))
	for key, col in ed.items():
		if key in ("days_to_next", "error", "Earnings Date"):
			continue
		if isinstance(col, dict):
			date_strs.update(k for k in col.keys() if isinstance(k, str))
	today = datetime.now().date()
	min_days = None
	for s in date_strs:
		d = None
		try:
			d = datetime.fromisoformat(s).date()
		except (ValueError, TypeError):
			for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%b %d, %Y"):
				try:
					d = datetime.strptime(s.strip(), fmt).date()
					break
				except (ValueError, TypeError):
					continue
		if d is None:
			continue
		delta = (d - today).days
		if delta >= 0 and (min_days is None or delta < min_days):
			min_days = delta
	return min_days


_SEC_CATALYST_KEYWORDS = re.compile(
	r"customer|contract|agreement|award|qualif|design[\s-]?win|capacity|"
	r"expansion|supply|partnership|order|approval|clearance",
	re.IGNORECASE,
)


def _recent_material_sec_catalyst(sec_sc_results):
	"""Return a material SEC/8-K catalyst type from recent events, else None.

	Broadens 'catalyst' beyond scheduled earnings: a recent design win / supply
	agreement / qualification / named contract (the catalysts that dominate
	Serenity's track record) read from the L3 SEC events feed.
	"""
	if not isinstance(sec_sc_results, dict):
		return None
	events_raw = sec_sc_results.get("sec_events", {}) or {}
	if not isinstance(events_raw, dict) or events_raw.get("error"):
		return None
	events = events_raw.get("data", []) or []
	if not isinstance(events, list):
		return None
	for ev in events:
		if not isinstance(ev, dict):
			continue
		text = f"{ev.get('event_type', '')} {ev.get('context', '')}"
		if _SEC_CATALYST_KEYWORDS.search(text):
			return ev.get("event_type") or "material_sec_event"
	return None


def _generate_composite_signal(l1_result, l4_results, l5_results, health_severity_score,
	bottleneck_pre_score, thesis_signals, auto_classification, trapped_asset_override,
	sec_sc_results=None):
	"""Generate integrated investment grade from all pipeline data."""

	l4 = l4_results if isinstance(l4_results, dict) else {}
	info_data = l4.get("info") or {}
	if isinstance(info_data, dict) and info_data.get("error"):
		info_data = {}
	fpe = l4.get("forward_pe") or {}
	if isinstance(fpe, dict) and fpe.get("error"):
		fpe = {}

	# V2 fundamental-reality status (tri-state). Distinguish MISSING data from a
	# confirmed pre-revenue company. We never auto-AVOID: missing data is a judgment
	# call for the agent (yfinance returns None for many micro-caps/foreign/ADR rows
	# that DO have revenue), and a confirmed pre-revenue bottleneck is sized down, not
	# zeroed (SIVE/POET/AEHR-early are exactly this winner pattern).
	revenue_status = "has_revenue"
	if isinstance(info_data, dict) and info_data:
		total_revenue = info_data.get("totalRevenue")
		if total_revenue is None:
			revenue_status = "data_insufficient"
		elif isinstance(total_revenue, (int, float)) and total_revenue <= 0:
			revenue_status = "confirmed_pre_revenue"
	else:
		revenue_status = "data_insufficient"

	score_breakdown = {}
	total_score = 0.0

	l1 = l1_result if isinstance(l1_result, dict) else {}
	regime = (l1.get("regime", "transitional") if l1 else "unknown")

	# Component 1: Bottleneck (30 pts) — archetype-conditional.
	# The bottleneck pre-score is SEC physical-supply-chain mining; it structurally
	# under-scores Disruption/Evolution names (fintech, neocloud, software/services),
	# forfeiting up to 30 pts off the top. For those archetypes substitute an
	# archetype-appropriate score so a non-physical winner is not capped below STRONG_BUY.
	bn = bottleneck_pre_score if isinstance(bottleneck_pre_score, dict) and not (bottleneck_pre_score or {}).get("error") else {}
	bn_raw = bn.get("pre_score", 0) if bn else 0
	if not isinstance(bn_raw, (int, float)):
		bn_raw = 0
	bn_max = bn.get("pre_score_max", 4.25) if bn else 4.25
	bn_points = (bn_raw / bn_max) * 30.0 if bn_max else 0.0
	ac = auto_classification if isinstance(auto_classification, dict) else {}
	ac_class = ac.get("classification", "unclassified")
	archetype_adjusted = False
	if ac_class in ("disruption", "evolution") and bn_points < 15.0:
		rev_growth = fpe.get("revenue_growth_yoy")
		gross_margins = info_data.get("grossMargins")
		ts_dir_pre = (thesis_signals or {}).get("net_direction", "neutral") if isinstance(thesis_signals, dict) else "neutral"
		arch_pts = 0.0
		if isinstance(rev_growth, (int, float)):
			arch_pts += 12.0 if rev_growth > 50 else 8.0 if rev_growth > 25 else 5.0 if rev_growth > 15 else 0.0
		if isinstance(gross_margins, (int, float)):
			arch_pts += 9.0 if gross_margins > 0.60 else 6.0 if gross_margins > 0.40 else 0.0
		arch_pts += 9.0 if ts_dir_pre == "strengthening" else 4.0 if ts_dir_pre == "neutral" else 0.0
		arch_pts = min(arch_pts, 30.0)
		if arch_pts > bn_points:
			bn_points = arch_pts
			archetype_adjusted = True
	score_breakdown["bottleneck"] = {
		"raw": bn_raw if bn else None, "max": bn_max, "points": round(bn_points, 2),
		"archetype_substituted": archetype_adjusted, "archetype": ac_class,
	}
	total_score += bn_points

	# Component 2: Health severity (25 pts) — 5 gates
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

	# Component 4: Catalyst (10 pts) — scheduled earnings OR a recent material SEC event.
	days = None
	if isinstance(l5_results, dict):
		ed = l5_results.get("earnings_dates")
		if isinstance(ed, dict) and not ed.get("error"):
			days = ed.get("days_to_next")
	if days is None:
		days = _parse_days_to_earnings(l5_results)
	earnings_pts = 10.0 if (days is not None and days <= 30) else 5.0 if (days is not None and days <= 60) else 0.0
	sec_catalyst = _recent_material_sec_catalyst(sec_sc_results)
	sec_pts = 7.0 if sec_catalyst else 0.0
	cat_points = max(earnings_pts, sec_pts)
	if earnings_pts >= sec_pts and earnings_pts > 0:
		catalyst_type = "earnings_near"
	elif sec_pts > 0:
		catalyst_type = sec_catalyst
	else:
		catalyst_type = "none"
	score_breakdown["catalyst"] = {
		"days_to_earnings": days, "sec_event": sec_catalyst,
		"catalyst_type": catalyst_type, "points": round(cat_points, 2),
	}
	total_score += cat_points

	# Component 5: Taxonomy (10 pts)
	tax_points = 10.0 if ac_class in ("bottleneck", "disruption") else 7.0 if ac_class == "evolution" else 5.0
	score_breakdown["taxonomy"] = {"classification": ac_class, "points": round(tax_points, 2)}
	total_score += tax_points

	# Component 6: Valuation (10 pts) — PEG-first for growth names, no-growth floor MoS
	# for low/no-growth names. The no-growth floor sits far below price for any grower,
	# so scoring on MoS alone zeroes every growth name and inverts the PEG-first doctrine.
	ngv = l4.get("no_growth_valuation") or {}
	if isinstance(ngv, dict) and ngv.get("error"):
		ngv = {}
	mos_pct = ngv.get("margin_of_safety_pct")
	rev_growth_v = fpe.get("revenue_growth_yoy")
	peg = fpe.get("peg_ratio")
	fpe1_v = fpe.get("forward_pe_1y")
	fpe2_v = fpe.get("forward_pe_2y")
	is_growth = isinstance(rev_growth_v, (int, float)) and rev_growth_v >= 15
	pe_contraction = isinstance(fpe1_v, (int, float)) and isinstance(fpe2_v, (int, float)) and fpe2_v < fpe1_v
	if is_growth and isinstance(peg, (int, float)) and peg > 0:
		val_points = 10.0 if peg < 1.0 else 6.0 if peg < 2.0 else 2.0
		if pe_contraction:
			val_points = min(10.0, val_points + 2.0)
		score_breakdown["valuation"] = {
			"track": "peg", "peg_ratio": peg, "pe_contraction": pe_contraction,
			"mos_pct_floor": round(mos_pct, 2) if isinstance(mos_pct, (int, float)) else None,
			"points": round(val_points, 2),
		}
	elif isinstance(mos_pct, (int, float)):
		# Growth name missing PEG, or a genuine low/no-growth name. A grower's no-growth
		# floor below price is EXPECTED (not a kill) — floor growth names at 3, not 0.
		val_points = 10.0 if mos_pct > 20 else 5.0 if mos_pct >= 0 else (3.0 if is_growth else 0.0)
		score_breakdown["valuation"] = {
			"track": "no_growth_floor", "mos_pct": round(mos_pct, 2),
			"is_growth": is_growth, "points": round(val_points, 2),
		}
	else:
		val_points = 0.0
		score_breakdown["valuation"] = {"track": None, "mos_pct": None, "points": 0.0, "note": "unavailable"}
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

	# Pre-revenue handling (tri-state). A confirmed pre-revenue name needs a MATERIAL
	# CATALYST (near earnings, recent material SEC event, or a strong bottleneck) to be
	# investable, and is size-capped — never AVOID-zeroed. Missing data changes nothing
	# here (the agent judges it via the data_insufficient flag).
	material_catalyst = (cat_points > 0) or (isinstance(bn_raw, (int, float)) and bn_raw >= 3.0)
	pre_revenue_note = None
	if revenue_status == "confirmed_pre_revenue":
		if material_catalyst:
			pre_revenue_note = "confirmed pre-revenue WITH a material catalyst (near earnings / recent SEC event / strong bottleneck) — investable as a size-capped MOONSHOT-tier bet"
		else:
			if total_score > 34:
				total_score = 34.0
			pre_revenue_note = "confirmed pre-revenue with NO material catalyst — speculative; not investable without a design win / qualification / named contract"

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

	# Position sizing — grade-derived BASELINE only. suggested_size_pct is a floor to
	# scale UP by cycle stage and conviction under the power-law doctrine (3-5 core names
	# at 60-80% combined), NOT a ceiling. The agent owns the final size.
	pos_table = {
		"STRONG_BUY": ("High", "5-7%", "1.5%"), "BUY": ("Medium", "2-4%", "1.0%"),
		"ACCUMULATE": ("Low", "1-2%", "0.5%"), "HOLD": (None, "hold_existing", None),
		"AVOID": (None, "no_entry", None), "MOONSHOT": ("Special", "max_5%", "2.5%"),
	}
	conviction, size, max_loss = pos_table.get(grade, (None, "no_entry", None))
	regime_adj = "risk_off_0.5x" if regime == "risk_off" else "transitional_0.75x" if regime == "transitional" else "none"
	conviction_delta = ts.get("conviction_delta", 0)
	# Pre-revenue investable bets are size-capped regardless of the grade band.
	if revenue_status == "confirmed_pre_revenue" and size not in ("no_entry", "hold_existing"):
		size = "max_3%"

	score_breakdown_out = {}
	for key, val in score_breakdown.items():
		score_breakdown_out[key] = val.get("points", val.get("raw", 0))

	return {
		"composite_score": total_score, "grade": grade,
		"score_breakdown": score_breakdown_out,
		"score_breakdown_detail": score_breakdown,
		"composite_thresholds": {
			"weights": {"bottleneck": 30, "health": 25, "thesis": 15, "catalyst": 10, "taxonomy": 10, "valuation": 10},
			"grades": {"STRONG_BUY": ">=80", "BUY": ">=65", "ACCUMULATE": ">=50", "HOLD": ">=35", "AVOID": "<35"},
		},
		"position_guidance": {
			"conviction_tier": conviction, "suggested_size_pct": size,
			"max_loss_pct": max_loss, "regime_adjustment": regime_adj,
			"conviction_delta": conviction_delta,
			"sizing_basis": "grade-derived baseline — NOT a ceiling. Scale by cycle stage (analysis.md §4: small at stage 2, bulk at confirmed ramp 4) and conviction; Serenity concentrates 3-5 core names at 60-80% combined.",
		},
		"revenue_status": revenue_status,
		"data_insufficient": revenue_status == "data_insufficient",
		"pre_revenue_note": pre_revenue_note,
		"archetype_adjusted": archetype_adjusted,
		"catalyst_type": catalyst_type,
		"sop_triggered": False,
		"trapped_asset_eligible": trapped_override_applied,
		"regime_cap_applied": regime_cap_applied,
	}
