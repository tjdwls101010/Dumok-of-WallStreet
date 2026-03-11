"""Bottleneck pre-scoring and SEC supply chain helpers for the Serenity pipeline.

Extracted from serenity.py (L3 bottleneck layer). This module is a leaf node
— it imports only standard library modules and has no intra-package dependencies.
"""

import re
from collections import Counter
from datetime import datetime


def _summarize_sec_supply_chain(data):
	"""Trim and cap SEC supply chain extraction for context efficiency.

	- Keeps context fields at full 400 chars (source extraction length)
	- Caps high-volume categories (geographic_concentration, supply_chain_risks) to 10 entries
	- Caps other categories to 15 entries
	"""
	if not data or data.get("error") or not data.get("data"):
		return data

	sc = data.get("data", {}).get("supply_chain")
	if not sc:
		return data

	high_volume = ("geographic_concentration", "supply_chain_risks", "geographic_revenue")
	for category in ("suppliers", "customers", "single_source_dependencies",
					"geographic_concentration", "capacity_constraints",
					"supply_chain_risks", "revenue_concentration",
					"geographic_revenue", "purchase_obligations",
					"market_risk_disclosures", "inventory_composition"):
		items = sc.get(category, [])
		cap = 10 if category in high_volume else 15
		if len(items) > cap:
			sc[category] = items[:cap]

	return data


def _build_l3_bottleneck(sec_sc_results):
	"""Build L3 bottleneck output incorporating SEC supply chain data and pre-scoring."""
	sec_sc_raw = sec_sc_results.get("sec_supply_chain", {})
	sec_events_raw = sec_sc_results.get("sec_events", {})

	sec_sc_data = _summarize_sec_supply_chain(sec_sc_raw)

	# Determine SEC data availability
	has_sc_data = (
		sec_sc_data
		and not sec_sc_data.get("error")
		and sec_sc_data.get("data")
		and sec_sc_data["data"].get("extraction_stats", {}).get("total_matches", 0) > 0
	)
	has_events = (
		sec_events_raw
		and not sec_events_raw.get("error")
		and len(sec_events_raw.get("data", [])) > 0
	)

	# Pre-score bottleneck from SEC data
	bottleneck_pre_score = None
	if has_sc_data:
		bottleneck_pre_score = _pre_score_bottleneck(sec_sc_raw)
		sec_status = "SEC_SC_available"
		note = ("SEC filing supply chain data pre-extracted and pre-scored. "
				"Agent completes 6-Criteria scoring via WebSearch cross-validation.")
	elif sec_sc_data and sec_sc_data.get("data") is not None:
		sec_status = "SEC_SC_partial"
		note = ("SEC filing found but limited supply chain matches. "
				"Agent relies primarily on WebSearch for L3.")
	else:
		sec_status = "SEC_SC_unavailable"
		note = ("SEC supply chain data unavailable. "
				"Agent relies on WebSearch for L3.")

	# Absence Evidence Flags (H7)
	absence_evidence_flags = []
	if has_sc_data:
		data_coverage = sec_sc_data.get("data", {}).get("data_coverage", {})
		supply_chain = sec_sc_data.get("data", {}).get("supply_chain", {})
		if data_coverage:
			# Type 1: No major customer contracts disclosed
			customers = supply_chain.get("customers", [])
			rev_conc = supply_chain.get("revenue_concentration", [])
			if not customers and not rev_conc and data_coverage.get("customers") == "not_disclosed":
				absence_evidence_flags.append({
					"type": "no_major_customer_disclosed",
					"signal": "negative",
					"note": "Company explicitly states no single customer is material — unvalidated revenue pipeline",
				})
			# Type 3: No analyst coverage / minimal data
			if data_coverage.get("revenue_concentration") == "insufficient_context":
				absence_evidence_flags.append({
					"type": "revenue_concentration_unknown",
					"signal": "neutral",
					"note": "Revenue concentration data not found in filing — may indicate limited disclosure",
				})
			# Type 2: No fundamental change + selloff (mechanical selling signal)
			# Detect via SEC events absence — if no recent 8-K filings exist,
			# significant price drops are likely non-fundamental (tax harvest, algo, MM).
			if not has_events:
				absence_evidence_flags.append({
					"type": "no_fundamental_change_selloff",
					"signal": "potential_entry",
					"note": ("No recent SEC event filings (8-K) detected. "
							"If stock has declined significantly, selling may be "
							"mechanical (tax harvesting, MM pinning, algo rebalancing), "
							"not fundamental — verify via WebSearch."),
				})
			# Type 4: No domestic production (geographic concentration all international)
			geo_conc = supply_chain.get("geographic_concentration", [])
			if geo_conc:
				all_intl = all(
					any(loc in (entry.get("location", "").lower())
						for loc in ("taiwan", "china", "korea", "vietnam", "malaysia"))
					for entry in geo_conc if isinstance(entry, dict) and entry.get("location")
				)
				if all_intl:
					absence_evidence_flags.append({
						"type": "no_domestic_production",
						"signal": "geopolitical_risk",
						"note": "All disclosed production concentrated in international high-risk locations",
					})
			# Type 5: Marketed capacity vs contracted capacity gap
			cap_coverage = data_coverage.get("capacity_constraints", "")
			po_coverage = data_coverage.get("purchase_obligations", "")
			if cap_coverage == "extracted" and po_coverage in ("not_disclosed", "insufficient_context"):
				absence_evidence_flags.append({
					"type": "marketed_vs_contracted_capacity_gap",
					"signal": "hype_risk",
					"note": ("Capacity constraints disclosed but purchase obligations "
							"absent or undisclosed — gap between marketed and "
							"contracted capacity is a red flag. Verify via SEC filings."),
				})

	result = {
		"sec_supply_chain": sec_sc_data if not sec_sc_data.get("error") else None,
		"sec_events": sec_events_raw if not sec_events_raw.get("error") else None,
		"sec_status": sec_status,
		"requires_context": True,
		"note": note,
		"absence_evidence_flags": absence_evidence_flags,
	}

	if bottleneck_pre_score and not bottleneck_pre_score.get("error"):
		result["bottleneck_pre_score"] = bottleneck_pre_score

	return result


# ---------------------------------------------------------------------------
# v4.0 Helpers: Bottleneck Pre-Scoring, Thesis Signals, SoP Triggers,
# Trapped Asset Override, Auto-Classification, Composite Signal
# ---------------------------------------------------------------------------

_HIGH_RISK_LOCATIONS = {"taiwan", "china", "hong kong", "mainland china"}
_MEDIUM_RISK_LOCATIONS = {"south korea", "korea", "israel", "vietnam", "russia"}
# Currency keywords → high-risk location mapping (for FX boost in _pre_score_bottleneck)
_FX_HIGH_RISK_CURRENCIES = {
	"nt dollar": "taiwan", "nt$": "taiwan", "new taiwan dollar": "taiwan", "twd": "taiwan",
	"renminbi": "china", "rmb": "china", "cny": "china", "yuan": "china", "cnh": "china",
	"hkd": "hong kong", "hong kong dollar": "hong kong",
}


def _pre_score_bottleneck(sec_sc_data):
	"""Score SEC supply chain data against the 6-Criteria Bottleneck Framework."""
	if sec_sc_data is None:
		return {"error": "No SEC supply chain data available"}
	if isinstance(sec_sc_data, dict) and "error" in sec_sc_data:
		return {"error": "No SEC supply chain data available"}

	try:
		supply_chain = sec_sc_data["data"]["supply_chain"]
	except (KeyError, TypeError):
		return {"error": "No SEC supply chain data available"}

	criteria = {}

	# Collect all text from all categories for broader search
	all_texts = []
	for cat_key in ("suppliers", "customers", "single_source_dependencies",
		"geographic_concentration", "capacity_constraints", "supply_chain_risks",
		"revenue_concentration", "geographic_revenue", "purchase_obligations",
		"market_risk_disclosures", "inventory_composition"):
		for entry in (supply_chain.get(cat_key) or []):
			if isinstance(entry, dict):
				for field in ("context", "constraint", "risk", "relationship", "activity",
					"component", "obligation_type", "amount", "timeframe",
					"risk_type", "exposure", "sensitivity", "hedging",
					"category", "pct_of_total"):
					val = entry.get(field, "") or ""
					if val:
						all_texts.append(str(val))
	all_text_blob = " ".join(all_texts)

	# 1. Supply concentration (single_source_dependencies + purchase_obligations)
	ssd = supply_chain.get("single_source_dependencies") or []
	suppliers = supply_chain.get("suppliers") or []
	purchase_obs = supply_chain.get("purchase_obligations") or []
	high_conf = [d for d in ssd if d.get("confidence") == "high"]
	# Check for sole/primary keywords in supplier relationships
	sole_primary_pattern = re.compile(r"sole|primary|only|exclusive|single.?source|de\s*facto", re.IGNORECASE)
	sole_supplier_count = sum(
		1 for s in suppliers
		if sole_primary_pattern.search(s.get("relationship", "") or "")
	)
	# Named purchase obligations reinforce supply concentration
	named_obligations = sum(1 for po in purchase_obs if po.get("counterparty"))
	if len(high_conf) >= 2 or (len(ssd) >= 1 and sole_supplier_count >= 1):
		criteria["supply_concentration"] = {
			"score": 1.0,
			"evidence": f"{len(high_conf)} high-conf SSD + {sole_supplier_count} sole/primary suppliers" + (f" + {named_obligations} named purchase obligations" if named_obligations else ""),
		}
	elif len(ssd) >= 1 or sole_supplier_count >= 1 or named_obligations >= 2:
		sc_score = 0.75 if named_obligations >= 2 else 0.5
		criteria["supply_concentration"] = {
			"score": sc_score,
			"evidence": f"{len(ssd)} SSD, {sole_supplier_count} sole/primary supplier mentions" + (f", {named_obligations} named purchase obligations" if named_obligations else ""),
		}
	else:
		criteria["supply_concentration"] = {"score": 0.0, "evidence": "No single-source dependencies found"}

	# 2. Capacity constraints (with duration extraction + purchase obligations)
	cc = supply_chain.get("capacity_constraints") or []
	duration_pattern = re.compile(r"(\d+)\s*(?:month|year|quarter)", re.IGNORECASE)
	resolving_pattern = re.compile(r"resolv|improv|eas|normaliz", re.IGNORECASE)
	billion_pattern = re.compile(r"\$[\d.]+\s*billion", re.IGNORECASE)
	multi_year_pattern = re.compile(r"(?:through|until|ending)\s+(?:fiscal\s+)?\d{4}|multi.?year|\d+\s*year", re.IGNORECASE)
	# Check purchase obligations for multi-year billion-dollar commitments
	large_obligations = 0
	for po in purchase_obs:
		amt = (po.get("amount", "") or "") + " " + (po.get("context", "") or "")
		tf = (po.get("timeframe", "") or "") + " " + (po.get("context", "") or "")
		if billion_pattern.search(amt) and multi_year_pattern.search(tf):
			large_obligations += 1
	if cc or large_obligations:
		max_duration_months = 0
		is_resolving = False
		for entry in cc:
			ctx = (entry.get("context", "") or "") + " " + (entry.get("constraint", "") or "")
			m = duration_pattern.search(ctx)
			if m:
				val = int(m.group(1))
				unit_text = ctx[m.start():m.end()].lower()
				if "year" in unit_text:
					val *= 12
				elif "quarter" in unit_text:
					val *= 3
				max_duration_months = max(max_duration_months, val)
			if resolving_pattern.search(ctx):
				is_resolving = True
		if max_duration_months >= 12 or large_obligations >= 1:
			cc_score = 0.75
			cc_evidence = f"{len(cc)} constraint(s), duration >= {max_duration_months} months"
			if large_obligations:
				cc_score = min(1.0, cc_score + 0.25)
				cc_evidence += f" + {large_obligations} multi-year billion-dollar purchase obligation(s)"
		elif cc:
			cc_score = 0.5
			cc_evidence = f"{len(cc)} constraint(s) mentioned"
		else:
			cc_score = 0.5
			cc_evidence = f"{large_obligations} large purchase obligation(s) indicate capacity commitment"
		if is_resolving:
			cc_score = min(cc_score, 0.25)
			cc_evidence += " (resolving language detected — capped)"
		# Inventory composition boost: raw materials >50% or obsolescence → capacity signal
		inv_comp = supply_chain.get("inventory_composition") or []
		if inv_comp:
			raw_pct = 0.0
			obsolescence_found = False
			for inv_entry in inv_comp:
				if inv_entry.get("category") == "raw_materials" and inv_entry.get("pct_of_total"):
					raw_pct = max(raw_pct, inv_entry["pct_of_total"])
				inv_ctx = (inv_entry.get("context", "") or "").lower()
				if any(kw in inv_ctx for kw in ("obsolescen", "write-down", "write down", "impairment", "valuation adjustment")):
					obsolescence_found = True
			if raw_pct > 50 or obsolescence_found:
				cc_score = min(1.0, cc_score + 0.15)
				cc_evidence += f" + inventory signal (raw_materials={raw_pct:.0f}%, obsolescence={'yes' if obsolescence_found else 'no'})"
		criteria["capacity_constraints"] = {"score": cc_score, "evidence": cc_evidence}
	else:
		criteria["capacity_constraints"] = {"score": 0.0, "evidence": "No capacity constraints mentioned"}

	# 3. Geopolitical risk (geographic concentration with risk tiers + geographic_revenue override)
	geo_rev = supply_chain.get("geographic_revenue") or []
	gc = supply_chain.get("geographic_concentration") or []
	# Quantitative override: if geographic_revenue has % data, use it directly
	geo_risk_override = False
	if geo_rev:
		high_risk_rev_pct = 0.0
		high_risk_regions = []
		for entry in geo_rev:
			region = (entry.get("region", "") or "").strip().lower()
			pct = entry.get("revenue_pct")
			if pct and any(hr in region for hr in _HIGH_RISK_LOCATIONS):
				high_risk_rev_pct += pct
				high_risk_regions.append(entry.get("region", ""))
		if high_risk_rev_pct > 0:
			geo_risk_override = True
			if high_risk_rev_pct >= 30:
				criteria["geopolitical_risk"] = {
					"score": 1.0,
					"evidence": f"HIGH_RISK geographic revenue: {high_risk_rev_pct:.1f}% in {', '.join(high_risk_regions)} (Notes quantitative data)",
				}
			elif high_risk_rev_pct >= 15:
				criteria["geopolitical_risk"] = {
					"score": 0.75,
					"evidence": f"Moderate high-risk geographic revenue: {high_risk_rev_pct:.1f}% in {', '.join(high_risk_regions)} (Notes quantitative data)",
				}
			else:
				criteria["geopolitical_risk"] = {
					"score": 0.5,
					"evidence": f"Low high-risk geographic revenue: {high_risk_rev_pct:.1f}% in {', '.join(high_risk_regions)} (Notes quantitative data)",
				}
	# Heuristic fallback: use geographic_concentration activity count
	if not geo_risk_override:
		if gc:
			locations = [entry.get("location", "").strip().lower() for entry in gc if entry.get("location")]
			total = len(locations)
			if total > 0:
				loc_counts = Counter(loc for loc in locations if loc)
				high_risk_count = sum(c for loc, c in loc_counts.items() if loc in _HIGH_RISK_LOCATIONS)
				medium_risk_count = sum(c for loc, c in loc_counts.items() if loc in _MEDIUM_RISK_LOCATIONS)
				most_common_loc, most_common_count = loc_counts.most_common(1)[0] if loc_counts else ("", 0)
				if high_risk_count > 0 and most_common_count / total > 0.3:
					criteria["geopolitical_risk"] = {
						"score": 1.0,
						"evidence": f"HIGH_RISK location concentration: {high_risk_count}/{total} entries in {', '.join(l for l in loc_counts if l in _HIGH_RISK_LOCATIONS)}",
					}
				elif medium_risk_count > 0 or most_common_count / total > 0.5:
					criteria["geopolitical_risk"] = {
						"score": 0.75,
						"evidence": f"Geographic concentration in medium-risk or dominant location: '{most_common_loc}' ({most_common_count}/{total})",
					}
				elif total > 0:
					criteria["geopolitical_risk"] = {"score": 0.5, "evidence": f"Geographic data present across {len(loc_counts)} locations"}
				else:
					criteria["geopolitical_risk"] = {"score": 0.0, "evidence": "No geographic concentration data"}
			else:
				criteria["geopolitical_risk"] = {"score": 0.0, "evidence": "No geographic concentration data"}
		else:
			criteria["geopolitical_risk"] = {"score": 0.0, "evidence": "No geographic concentration data"}

	# FX market risk reinforcement: high-risk location FX exposure → geo-risk boost
	mrd = supply_chain.get("market_risk_disclosures") or []
	fx_high_risk = False
	for mr_entry in mrd:
		if (mr_entry.get("risk_type") or "").lower() == "fx":
			exp_text = ((mr_entry.get("exposure", "") or "") + " " + (mr_entry.get("context", "") or "")).lower()
			if any(loc in exp_text for loc in _HIGH_RISK_LOCATIONS):
				fx_high_risk = True
				break
			if any(cur in exp_text for cur in _FX_HIGH_RISK_CURRENCIES):
				fx_high_risk = True
				break
	if fx_high_risk and "geopolitical_risk" in criteria:
		geo_score = criteria["geopolitical_risk"]["score"]
		if geo_score > 0:
			new_geo = min(1.0, geo_score + 0.15)
			criteria["geopolitical_risk"]["score"] = new_geo
			criteria["geopolitical_risk"]["evidence"] += " + FX high-risk location exposure (Item 7A)"

	# 4. Long lead times (search all categories + numeric extraction)
	lead_time_pattern = re.compile(r"lead\s*time|backlog|wait\s*time|delivery\s*delay|allocation|extended\s*lead", re.IGNORECASE)
	lead_duration_pattern = re.compile(r"(\d+)\s*(?:month|week|year|quarter)", re.IGNORECASE)
	lead_time_found = lead_time_pattern.search(all_text_blob) is not None
	lead_duration_months = 0
	if lead_time_found:
		for m in lead_duration_pattern.finditer(all_text_blob):
			val = int(m.group(1))
			unit_text = all_text_blob[m.start():m.end()].lower()
			if "year" in unit_text:
				val *= 12
			elif "quarter" in unit_text:
				val *= 3
			elif "week" in unit_text:
				val = max(1, val // 4)
			lead_duration_months = max(lead_duration_months, val)
	if lead_duration_months >= 6:
		criteria["long_lead_times"] = {"score": 0.75, "evidence": f"Lead time >= {lead_duration_months} months detected"}
	elif lead_time_found:
		criteria["long_lead_times"] = {"score": 0.5, "evidence": "Lead time / backlog language found"}
	else:
		criteria["long_lead_times"] = {"score": 0.0, "evidence": "No lead time indicators found"}

	# 5. No substitutes (search all categories + expanded patterns)
	no_sub_pattern = re.compile(
		r"cannot\s.*?replace|no\s.*?alternative|sole\s.*?source|only\s.*?supplier|"
		r"irreplaceable|no\s+viable\s+substitute|proprietary\s+process|"
		r"unique\s+capability|no\s+second\s+source|limited\s+alternative",
		re.IGNORECASE,
	)
	no_sub_found = no_sub_pattern.search(all_text_blob) is not None
	# Also check single_source_dependencies entries
	if not no_sub_found and ssd:
		for entry in ssd:
			ctx = (entry.get("context", "") or "") + " " + (entry.get("component", "") or "")
			if no_sub_pattern.search(ctx):
				no_sub_found = True
				break
	if no_sub_found and len(ssd) >= 1:
		criteria["no_substitutes"] = {"score": 0.75, "evidence": "Sole source language + single-source dependencies confirmed"}
	elif no_sub_found:
		criteria["no_substitutes"] = {"score": 0.5, "evidence": "Sole source / no substitute language found"}
	else:
		criteria["no_substitutes"] = {"score": 0.0, "evidence": "No sole-source language found"}

	# Commodity market risk reinforcement: commodity exposure + existing score → boost
	commodity_found = any(
		(mr.get("risk_type") or "").lower() == "commodity" for mr in mrd
	)
	if commodity_found and criteria["no_substitutes"]["score"] > 0:
		ns_score = min(1.0, criteria["no_substitutes"]["score"] + 0.15)
		criteria["no_substitutes"]["score"] = ns_score
		criteria["no_substitutes"]["evidence"] += " + commodity price exposure (Item 7A)"

	# 6. Cost insignificance — requires agent assessment
	criteria["cost_insignificance"] = {"score": 0, "evidence": "Cannot determine from SEC data", "requires_agent_assessment": True}

	# Max excludes cost_insignificance (agent-only)
	pre_score = sum(c["score"] for c in criteria.values())
	pre_score_max = 4.25

	if pre_score >= 3.0:
		assessment = "strong"
	elif pre_score >= 1.5:
		assessment = "partial"
	else:
		assessment = "weak"

	# Sole Western Flag (H10 Defense Heuristic #2)
	sole_western_flag = False
	suppliers = supply_chain.get("suppliers", [])
	ssd = supply_chain.get("single_source_dependencies", [])
	western_count = 0
	intl_count = 0
	for entry in suppliers + ssd:
		geo = entry.get("supplier_geography", "Unknown")
		if geo == "Western":
			western_count += 1
		elif geo == "International":
			intl_count += 1
	# Flag when there's exactly 1 Western supplier and it's single-source or sole
	if western_count == 1 and intl_count >= 1 and len(ssd) >= 1:
		sole_western_flag = True

	filing_date_str = None
	stale_warning = None
	try:
		filing_date_str = sec_sc_data["data"]["filing"]["filing_date"]
		filing_dt = datetime.strptime(filing_date_str, "%Y-%m-%d")
		if (datetime.now() - filing_dt).days > 365:
			stale_warning = "Filing date > 12 months old"
	except (KeyError, TypeError, ValueError):
		pass

	return {
		"pre_score": pre_score, "pre_score_max": pre_score_max,
		"criteria": criteria, "assessment": assessment,
		"filing_date": filing_date_str, "stale_data_warning": stale_warning,
		"sole_western_flag": sole_western_flag,
		"scoring_guide": {
			"total": "Sum of 5 criteria (max 4.25). Agent evaluates criterion 6 (cost insignificance) separately.",
			"assessment_thresholds": "strong: >=3.0 | partial: >=1.5 | weak: <1.5",
			"investable_threshold": "4+/6 with agent's criterion 6 evaluation",
		},
	}
