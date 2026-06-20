"""Thesis signal generation, SoP triggers, trapped-asset override, taxonomy
classification, earnings proximity parsing, and composite investment grade
derivation for the Serenity pipeline."""

import re
from datetime import datetime

from ._bottleneck import _build_l3_bottleneck
from ._health import _extract_health_gates


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
			revenue_growth = rg  # forward_pe.revenue_growth_yoy is already in percent

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
	"""Rule-based L6 taxonomy pre-classification (sector-aware).

	Triage only - the agent reads the business and overrides this (SKILL.md
	archetype routing). The business model is the strongest tell: size + growth
	alone cannot separate a stablecoin issuer (Disruption) from a substrate maker
	(Bottleneck). Priority: a score-backed physical chokepoint (Bottleneck) > a
	profit-pool/financial attacker (Disruption) > a new-category step-change or
	large-growth residual (Evolution). Keywords are deliberately narrow and the
	Bottleneck set matches the SECTOR+INDUSTRY classification only (not
	the free-text summary, which names served markets and creates false 'mining'-type
	hits); Disruption and Evolution also read the description, where signal words like
	'telehealth'/'drone' live. An ambiguous name falls to the LOW-confidence residual rather than a wrong tag.
	"""
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
	revenue_growth = forward_pe.get("revenue_growth_yoy")  # percent, e.g. 40.2 = 40.2%
	sales_accelerating = earnings_acc.get("sales_accelerating")
	# Sector+industry is a clean classification; the business summary names served
	# markets/partners and produces false keyword hits, so only Evolution (whose
	# signal words like "drone"/"autonomous" live in the description) reads it.
	text_cls = " ".join(str(info.get(k) or "") for k in ("sector", "industry")).lower()
	text_all = (text_cls + " " + str(info.get("longBusinessSummary") or "")).lower()

	bn = bottleneck_pre_score if isinstance(bottleneck_pre_score, dict) and not (bottleneck_pre_score or {}).get("error") else {}
	bn_ps = bn.get("pre_score") if isinstance(bn.get("pre_score"), (int, float)) else 0.0
	# Route the sector-gated rule on the STABLE assessment bucket, not the
	# knife-edge raw score: enum extraction can drift a physical name's raw
	# pre_score across the 2.0 line run-to-run (a judgment enum flips) while
	# the bucket stays "partial" — bucketing keeps the taxonomy reproducible.
	bn_assessment = bn.get("assessment")

	BOTTLENECK_KW = ("semiconductor", "materials", "chemical", "metals", "mining",
		"rare earth", "substrate", "wafer", "optical", "photonic",
		"electronic components", "industrial machinery", "specialty industrial")
	DISRUPTION_KW = ("financial", "credit services", "capital markets", "bank",
		"insurance", "asset management", "payment", "fintech", "crypto", "blockchain",
		"stablecoin", "brokerage", "exchange", "lending", "direct-to-consumer",
		"telehealth", "health information")
	EVOLUTION_KW = ("aerospace", "defense", "space", "satellite", "launch", "spacecraft",
		"robot", "drone", "autonomous", "unmanned", "electric vehicle", "renewable",
		"solar", "nuclear", "hydrogen", "quantum", "biotechnology", "genomic")
	def hit(kws, t):
		return next((k for k in kws if k in t), None)

	# Rule 1 - Bottleneck (physical chokepoint), strongest claim, must be score-backed.
	if bn_ps >= 3.0:
		classification = "bottleneck"
		evidence.append(f"bottleneck_pre_score {bn_ps}/{bn.get('pre_score_max', 4.25)} >= 3.0")
		confidence = "high" if bn_ps >= 3.5 else "medium"
	else:
		bk = hit(BOTTLENECK_KW, text_cls)
		if bk and bn_assessment in ("strong", "partial"):
			classification = "bottleneck"
			evidence.append(f"physical-goods sector ('{bk}') + bottleneck assessment '{bn_assessment}' (>= partial)")
			confidence = "medium"

	# Rule 2 - Disruption (profit-pool/financial attacker), size-independent.
	if classification == "unclassified":
		dk = hit(DISRUPTION_KW, text_all)
		if dk:
			classification = "disruption"
			evidence.append(f"profit-pool/financial sector ('{dk}')")
			confidence = "high" if (isinstance(gross_margins, (int, float)) and gross_margins > 0.40 and isinstance(revenue_growth, (int, float)) and revenue_growth > 20) else "medium"

	# Rule 3 - Evolution (new-category step-change); reads the description too.
	if classification == "unclassified":
		ek = hit(EVOLUTION_KW, text_all)
		if ek:
			classification = "evolution"
			evidence.append(f"step-change category ('{ek}')")
			confidence = "medium"

	# Residual fallbacks (no clear sector signal) - LOW confidence, agent should override.
	if classification == "unclassified":
		if bn_assessment in ("strong", "partial"):
			classification = "bottleneck"
			evidence.append(f"bottleneck assessment '{bn_assessment}' (>= partial, no sector signal)")
		elif isinstance(gross_margins, (int, float)) and gross_margins > 0.40 and isinstance(revenue_growth, (int, float)) and revenue_growth > 20:
			classification = "disruption"
			evidence.append(f"high margin {gross_margins:.2f} + growth {revenue_growth:.2f} (no sector signal)")
		elif isinstance(market_cap, (int, float)) and market_cap > 10e9 and ((isinstance(revenue_growth, (int, float)) and revenue_growth > 20) or sales_accelerating is True):
			classification = "evolution"
			evidence.append(f"large-cap growth {market_cap/1e9:.1f}B (residual)")
		else:
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


# Narrow set: the design-win / qualification / offtake / multi-year supply events
# that actually move forward revenue. The old set ('customer', 'contract',
# 'agreement', 'capacity', 'approval'…) fired on almost any routine 8-K, handing a
# free +7 to names with no real catalyst.
_SEC_CATALYST_KEYWORDS = re.compile(
	r"design[\s-]?win|qualif|offtake|multi.?year\s+supply|supply\s+agreement|"
	r"long.?term\s+(?:supply|purchase)\s+agreement|strategic\s+partnership|capacity\s+expansion",
	re.IGNORECASE,
)
# 8-K item codes for a material definitive agreement (1.01) or its termination (1.02).
_SEC_CATALYST_ITEMS = ("1.01", "1.02")


def _recent_material_sec_catalyst(sec_sc_results):
	"""Return a material SEC/8-K catalyst type from recent events, else None.

	A real design win / supply agreement / qualification (the catalysts that
	dominate the track record) — NOT routine 8-K prose. The bar: the event must
	carry an 8-K material-agreement item code (1.01/1.02) OR match the narrow
	phrase set above, AND (for a phrase-only match) be flagged medium/high
	confidence. A bare keyword hit on a boilerplate filing no longer qualifies.
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
		et = str(ev.get("event_type", ""))
		conf = str(ev.get("confidence", "")).lower()
		item_hit = any(et.strip().startswith(code) for code in _SEC_CATALYST_ITEMS)
		phrase_hit = bool(_SEC_CATALYST_KEYWORDS.search(f"{et} {ev.get('context', '')}"))
		# An item code is structural enough on its own; a phrase match needs
		# confidence backing it (item-code events fire even when confidence is absent).
		if item_hit or (phrase_hit and conf in ("medium", "high")):
			return et or "material_sec_event"
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
	moat_proxies = []
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
		# Deterministic moat gate. Growth + margin + a strengthening thesis say a name
		# is BIG and HOT — not that it owns a durable edge. A Disruption/Evolution name
		# earns the full 30-pt substitution only if it shows >=1 hard moat proxy from
		# the SEC enums: a regulatory mandate (the §3 'don't value it like its category'
		# re-rating lever), a named strategic backstop (the Evolution gate-3), captive
		# demand, or realized pricing power. Without one, the substitution is capped at
		# 18 so a moat-less hot story can't reach STRONG_BUY on archetype points alone —
		# the failure mode being a no-moat 'financial' name printing 100.0/STRONG_BUY.
		if bn.get("regulatory_posture") == "enabled_by_regulation":
			moat_proxies.append("regulatory_tailwind")
		if bn.get("strategic_backstop"):
			moat_proxies.append("strategic_backstop")
		if bn.get("customer_concentration") == "captive":
			moat_proxies.append("captive_demand")
		if bn.get("pricing_posture") == "raises_prices":
			moat_proxies.append("realized_pricing")
		if not moat_proxies:
			arch_pts = min(arch_pts, 18.0)
		arch_pts = min(arch_pts, 30.0)
		if arch_pts > bn_points:
			bn_points = arch_pts
			archetype_adjusted = True
	score_breakdown["bottleneck"] = {
		"raw": bn_raw if bn else None, "max": bn_max, "points": round(bn_points, 2),
		"archetype_substituted": archetype_adjusted, "archetype": ac_class,
		"moat_proxies": moat_proxies,
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

	# Component 5: Taxonomy (10 pts). The three archetypes are CO-EQUAL (analysis.md
	# "Three thesis archetypes" — "Bottleneck is one of three, not the spine"), so Evolution
	# earns the same 10 as Bottleneck/Disruption. (It used to be docked to 7 — an unjustified
	# 3-pt tax that, stacked on the physical-moat cap below, made a perfect Evolution name
	# ceiling under the STRONG_BUY line. Un-caps no loser: the quantum/pre-commercial set is
	# held by speculative_cap, not by this component.)
	tax_points = 10.0 if ac_class in ("bottleneck", "disruption", "evolution") else 5.0
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
	elif is_growth and isinstance(mos_pct, (int, float)) and mos_pct < 0:
		# Driver-proxy track — the capital structure picks the metric (analysis.md §3
		# "Lens-mismatch"). A genuine grower with NO usable PEG (pre-profit / asset-financed
		# capacity buildout / pre-scale disruptor) whose no-growth floor sits BELOW price: the
		# floor is the WRONG lens here — it "fabricates an overvalued verdict" the doctrine
		# explicitly forbids (and used to hard-floor these names at 3/10). Floor-below-price is
		# EXPECTED for a grower, not a kill, so score on GROWTH QUALITY as a proxy for the
		# driver-based anchor (levered IRR / contracted-and-customer-funded backlog / TAM
		# option) the agent computes and DEFENDS in prose. Capped at 8, not 10: the agent must
		# do the real driver math to claim "screaming cheap." This does NOT loosen V2/V6 — a
		# moat-less cash-burner is still held by the separate speculative_cap and pre-revenue
		# cap below; this branch only stops the floor model from fabricating a penalty.
		val_points = 8.0 if rev_growth_v > 50 else 6.0 if rev_growth_v > 25 else 4.0
		score_breakdown["valuation"] = {
			"track": "driver_proxy", "rev_growth_yoy": round(rev_growth_v, 1),
			"mos_pct_floor": round(mos_pct, 2), "points": round(val_points, 2),
			"note": "no-growth floor N/A (asset-financed / pre-profit grower) — growth-quality proxy; agent computes & defends the levered-IRR / contracted-backlog band",
		}
	elif isinstance(mos_pct, (int, float)):
		# The no-growth floor IS the right lens here: a genuine low/no-growth name, or a grower
		# cheap even at zero growth (mos>=0). A NON-grower trading below its own no-growth floor
		# (mos<0) is a value trap -> 0. (A growing name with mos<0 was routed to driver_proxy.)
		val_points = 10.0 if mos_pct > 20 else 5.0 if mos_pct >= 0 else 0.0
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
			pre_revenue_note = "confirmed pre-revenue WITH a material catalyst (near earnings / recent SEC event / strong bottleneck) — investable but speculative (MOONSHOT-tier)"
		else:
			if total_score > 34:
				total_score = 34.0
			pre_revenue_note = "confirmed pre-revenue with NO material catalyst — speculative; not investable without a design win / qualification / named contract"

	# Pre-commercial speculation cap. Operating losses that EXCEED revenue (op margin
	# < -100%) mean there is no commercial business to value yet — a story priced on a
	# promise. Burning cash pre-ramp isn't itself disqualifying (a genuine early winner
	# does the same); a MOAT is what separates them, and we test it ROBUSTLY by requiring a
	# STRONG bottleneck (assessment == strong, pre-score >= 3.0) — nothing weaker exempts.
	# The reason is extraction stability, measured not guessed: RGTI's frozen filing sits at
	# pre-score 1.45, and perturbing a SINGLE judgment enum to its most-bottleneck-favorable
	# value (designed_out -> physical_inevitability) lifts it to 2.1 — so a "partial" bucket,
	# or any buffer up to ~2.5, can be reached by one LLM wobble and would un-cap the loser.
	# 3.0 cannot: even stacking the two largest single-enum swings on RGTI stays ~2.5, clear
	# of the bar. We also do NOT key the exemption on individual moat enums (named backstop,
	# captive customer) — those fire on the speculative names themselves (RGTI lists Quanta
	# as a backstop, QBTS shows a captive customer) and would un-cap the very losers this
	# targets. The cost of "strong only" is that a genuinely partial-bottleneck pre-commercial
	# name is capped too — accepted, because the cap is a FLOOR the agent overrides upward on
	# the bottleneck thesis, not a verdict. Caveat handed to the agent: this is yfinance TTM
	# operating margin, so a real business pushed < -100% by a one-time charge is also capped
	# — speculative_cap_reason is the cue to check for non-recurring items and override up. A
	# data-sparse name (margin missing) never trips it; a trapped-asset override is exempt.
	op_margin = info_data.get("operatingMargins") if isinstance(info_data, dict) else None
	bn_assessment = bn.get("assessment") if isinstance(bn, dict) else None
	has_bottleneck_moat = bn_assessment == "strong"
	speculative_cap_applied = False
	speculative_cap_reason = None
	if (isinstance(op_margin, (int, float)) and op_margin < -1.0
			and not has_bottleneck_moat and not trapped_override_applied):
		if total_score > 49:
			total_score = 49.0
		speculative_cap_applied = True
		speculative_cap_reason = "operating_losses_exceed_revenue_no_moat"

	# Unsubstantiated-bottleneck flag — a SIGNAL, not a cap. A bottleneck classification
	# predicts pricing power and demand pull, which should show as growth or operating
	# profit. A bottleneck label on a name that NEITHER grows (revenue growth < 15%) NOR
	# earns (operating losses) isn't bearing out the thesis. We do NOT cap, on purpose:
	# this same point-in-time pattern also fits a strong bottleneck at a cycle TROUGH, and
	# a fixed cap would misfire there. The flag only raises the tension; the agent resolves
	# it — melting legacy asset vs cyclical trough — via the prototype-vs-production lens
	# and the revenue/margin TRAJECTORY (this is a level check, blind to direction).
	ac_class = auto_classification.get("classification") if isinstance(auto_classification, dict) else None
	rev_growth_pct = fpe.get("revenue_growth_yoy") if isinstance(fpe, dict) else None
	unsubstantiated_bottleneck = (
		ac_class == "bottleneck"
		and isinstance(rev_growth_pct, (int, float)) and rev_growth_pct < 15
		and isinstance(op_margin, (int, float)) and op_margin < 0
	)

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
		"revenue_status": revenue_status,
		"data_insufficient": revenue_status == "data_insufficient",
		"pre_revenue_note": pre_revenue_note,
		"archetype_adjusted": archetype_adjusted,
		"catalyst_type": catalyst_type,
		"sop_triggered": False,
		"trapped_asset_eligible": trapped_override_applied,
		"regime_cap_applied": regime_cap_applied,
		"speculative_cap_applied": speculative_cap_applied,
		"speculative_cap_reason": speculative_cap_reason,
		"unsubstantiated_bottleneck": unsubstantiated_bottleneck,
	}


def derive_core_signals(l1_result, l4_results, l5_results, sec_sc_results):
	"""Run the deterministic scoring layer on already-gathered pipeline inputs.

	This is the SINGLE source of truth for how raw L1/L4/L5/SEC results become
	the L3 bottleneck score, health gates, thesis signals, taxonomy, trapped-asset
	override, and the composite grade. cmd_analyze calls it on live results; the
	golden regression harness calls it on FROZEN results so a scoring-logic change
	is tested deterministically — free of live-data drift and LLM-extraction noise,
	the two things that would otherwise masquerade as a regression.

	Keep it network-free: same inputs must always yield the same output. (That is
	why cmd_analyze's S-3 dilution lookup lives OUTSIDE this function — it hits the
	network and only enriches output, never the score.)
	"""
	l3_data = _build_l3_bottleneck(sec_sc_results)
	bottleneck_pre_score = l3_data.get("bottleneck_pre_score")
	health_gates = _extract_health_gates(l4_results)
	thesis_signals = _build_thesis_signals(l4_results, l5_results)
	sop_triggers = _check_sop_triggers(l4_results)
	trapped_asset_override = _check_trapped_asset_override(l4_results, bottleneck_pre_score, sec_sc_results)
	auto_classification = _auto_classify_taxonomy(l4_results, bottleneck_pre_score)
	composite_signal = _generate_composite_signal(
		l1_result, l4_results, l5_results,
		health_gates.get("severity_score"),
		bottleneck_pre_score, thesis_signals,
		auto_classification, trapped_asset_override,
		sec_sc_results,
	)
	return {
		"l3_data": l3_data,
		"bottleneck_pre_score": bottleneck_pre_score,
		"health_gates": health_gates,
		"thesis_signals": thesis_signals,
		"sop_triggers": sop_triggers,
		"trapped_asset_override": trapped_asset_override,
		"auto_classification": auto_classification,
		"composite_signal": composite_signal,
	}
