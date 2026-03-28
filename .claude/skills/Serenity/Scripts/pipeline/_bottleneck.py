"""Bottleneck pre-scoring, SEC supply chain extraction schema, and helpers
for the Serenity pipeline.

Includes the Pydantic schema for SEC filing supply chain intelligence
extraction and the bottleneck pre-scoring heuristics.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import ClassVar, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# SEC Supply Chain Extraction Schema (Pydantic)
# ---------------------------------------------------------------------------

class SupplyEntity(BaseModel):
	entity: str = Field(description="Supplier company name. Use exact name from the filing.")
	role: str = Field(default="", description="Functional role in supply chain as described in the filing.")
	relationship: str = Field(default="", description="Nature of the supply relationship.")
	context: str = Field(default="", description="1-3 sentences from the filing.")


class DemandEntity(BaseModel):
	entity: str = Field(description="Customer name. Use 'Direct Customer A/B/C' if the filing does not disclose the name.")
	relationship: str = Field(default="", description="Nature of the customer relationship.")
	revenue_pct: float | None = Field(default=None, description="% of total revenue if disclosed.")
	revenue_amount: str = Field(default="", description="Dollar amount if disclosed.")
	concentration_flag: Literal["captive", "major", "diversified", "unnamed"] = Field(
		default="unnamed",
		description="captive: >50% revenue or sole contract dependency. major: 10-50%. diversified: <10%. unnamed: name not disclosed.",
	)
	context: str = Field(default="", description="1-3 sentences from the filing.")


class GeographicExposure(BaseModel):
	region: str = Field(description="Country or region name.")
	supply_activity: str = Field(default="", description="Supply-side activity at this location if applicable.")
	revenue_pct: float | None = Field(default=None, description="% of total revenue from this region if disclosed.")
	revenue_amount: str = Field(default="", description="Dollar amount if disclosed.")
	context: str = Field(default="", description="1-3 sentences from the filing.")


class OperationalRisk(BaseModel):
	type: Literal[
		"capacity_constraint", "supply_disruption", "geopolitical",
		"regulatory", "technology_transition", "competitive", "other",
	] = Field(description="Risk category.")
	risk: str = Field(description="Specific risk description.")
	context: str = Field(default="", description="1-3 sentences from the filing.")


class PurchaseObligationEntry(BaseModel):
	counterparty: str = Field(default="", description="Supplier name if disclosed.")
	obligation_type: str = Field(description="Type of obligation.")
	amount: str = Field(default="", description="Dollar amount if disclosed.")
	timeframe: str = Field(default="", description="Duration or end date.")
	context: str = Field(default="", description="1-3 sentences from Notes.")


class MarketRiskEntry(BaseModel):
	risk_type: Literal["commodity", "fx", "interest_rate"] = Field(description="Market risk type.")
	exposure: str = Field(default="", description="Specific exposure.")
	sensitivity: str = Field(default="", description="Quantitative impact if disclosed.")
	hedging: str = Field(default="", description="Hedging strategy if disclosed.")
	context: str = Field(default="", description="1-3 sentences from filing.")


class InventoryCompositionEntry(BaseModel):
	category: Literal["raw_materials", "work_in_progress", "finished_goods"] = Field(description="Inventory category.")
	amount: str = Field(default="", description="Dollar amount if disclosed.")
	pct_of_total: float | None = Field(default=None, description="% of total inventory.")
	context: str = Field(default="", description="1-3 sentences from Notes.")


class SupplyChain(BaseModel):
	"""Supply chain intelligence extraction from SEC filings."""

	__prompt__: ClassVar[str] = """\
You are a financial analyst extracting supply chain intelligence from SEC filings.
Extract entities and relationships exactly as stated in the filing text.

The filing text below is the complete SEC filing in markdown format.
Identify relevant sections by their natural headings:
- Item 1 (Business): suppliers, customers, technology, competitive landscape
- Item 1A (Risk Factors): supply chain risks, geographic concentration, technology transitions, competitive threats
- Item 7 (MD&A): capacity constraints, operating discussion
- Item 7A (Market Risk): commodity/FX/interest rate exposures
- Item 8 Notes: revenue segments, inventory, commitments, concentration
For 20-F filings, look for equivalent items (Item 4, 3D, 5, 11, 18/19).

Rules:
1. Use exact company names from the filing — do not paraphrase or invent.
2. For context fields, copy 1-3 relevant sentences verbatim from the filing.
3. If a category has no relevant data, return an empty list.
4. Do NOT extract the filing company itself as its own supplier or customer.
5. Focus on factual supply chain relationships — skip generic boilerplate.
6. Supplier role: describe the functional role as stated in the filing
   (e.g., "contract manufacturer", "raw material supplier", "foundry",
   "logistics provider", "technology licensor").
7. Customer extraction: Look for revenue concentration disclosures, named buyers,
   and "accounted for X% of revenue" language. If the filing anonymizes a customer
   (e.g., "one customer" or "Customer A"), use "Direct Customer A/B/C" as entity.
8. Concentration flag: captive = single customer >50% of revenue or described as
   sole/primary contract dependency. major = 10-50% of revenue. diversified = <10%.
   unnamed = customer name not disclosed (use even if revenue_pct is known).
9. Geographic exposure: merge supply-side (manufacturing, sourcing locations) and
   demand-side (revenue by region) into one entry per region when both exist.
   Include supply_activity AND revenue_pct when both are available for the same region.
10. Operational risks must be classified by type:
    - capacity_constraint: production limits, extended lead times, backlogs, allocation
    - supply_disruption: shortages, force majeure, single-source dependency language
    - geopolitical: tariffs, export controls, sanctions, regional instability
    - regulatory: government policy, compliance requirements, legal proceedings
    - technology_transition: migration to new technologies, platform transitions,
      next-generation product development, obsolescence risk
    - competitive: alternative suppliers, new entrants, customer self-sourcing,
      market share shifts, substitute products
11. Purchase obligations: From Notes (Commitments and Contingencies), extract purchase
    commitments, capacity reservations, take-or-pay contracts.
12. Market risk disclosures: From Item 7A, extract commodity/FX/interest rate exposures.
    Classify risk_type as "commodity", "fx", or "interest_rate".
13. Inventory composition: From Notes, extract raw materials, work-in-progress, and
    finished goods amounts and percentages.
14. Use precise relationship descriptions based on what the filing states.

Filing company: {company_name}

Extract all supply chain entities from this SEC filing text:

{filing_text}
"""

	supply_entities: list[SupplyEntity] = Field(default_factory=list, description="Companies that supply products, materials, or services to the filing company.")
	demand_entities: list[DemandEntity] = Field(default_factory=list, description="Companies that purchase from the filing company, with revenue concentration.")
	geographic_exposure: list[GeographicExposure] = Field(default_factory=list, description="Regions with supply-side activity and/or demand-side revenue.")
	operational_risks: list[OperationalRisk] = Field(default_factory=list, description="Supply chain risks classified by type.")
	purchase_obligations: list[PurchaseObligationEntry] = Field(default_factory=list, description="Purchase commitments from Notes.")
	market_risk_disclosures: list[MarketRiskEntry] = Field(default_factory=list, description="Market risk exposures from Item 7A.")
	inventory_composition: list[InventoryCompositionEntry] = Field(default_factory=list, description="Inventory breakdown from Notes.")


# ---------------------------------------------------------------------------
# Post-processing helpers
# ---------------------------------------------------------------------------

_WESTERN_LOCATIONS = {
	"united states", "us", "usa", "canada", "united kingdom", "uk",
	"germany", "france", "italy", "netherlands", "ireland", "switzerland",
	"sweden", "finland", "norway", "denmark", "spain", "belgium",
	"australia", "japan", "new zealand", "austria",
}
_INTERNATIONAL_HIGH_RISK = {
	"taiwan", "china", "mainland china", "hong kong", "south korea",
	"korea", "vietnam", "india", "malaysia", "thailand", "singapore",
	"indonesia", "philippines", "israel", "russia",
}

# Role keyword mapping for post-processing (Serenity tacit knowledge)
_ROLE_KEYWORDS = {
	"foundry": re.compile(r"foundry|foundries|fabricat|wafer\s*fab", re.IGNORECASE),
	"memory": re.compile(r"memory|dram|hbm|nand|sram", re.IGNORECASE),
	"assembly": re.compile(r"assembl|packag|testing\s*and\s*packag|subcontract", re.IGNORECASE),
	"IP_licensor": re.compile(r"licens|intellectual\s*property|patent|royalt", re.IGNORECASE),
	"connectivity": re.compile(r"switch|transceiver|optic|interconnect|network", re.IGNORECASE),
	"substrate": re.compile(r"substrate|wafer|material\s*supplier|raw\s*material", re.IGNORECASE),
	"power_mgmt": re.compile(r"voltage\s*regulat|power\s*management|power\s*supply", re.IGNORECASE),
	"cooling": re.compile(r"cool|thermal|heat\s*sink|cdu|chiller", re.IGNORECASE),
	"software": re.compile(r"software|middleware|orchestrat|platform|cloud\s*service", re.IGNORECASE),
}


def _classify_supplier_role(entry):
	"""Classify a supply entity's free-text role into Serenity's taxonomy."""
	text = " ".join([
		entry.get("role", ""),
		entry.get("relationship", ""),
		entry.get("context", ""),
	]).lower()
	for role_name, pattern in _ROLE_KEYWORDS.items():
		if pattern.search(text):
			return role_name
	return "other"


def _label_supplier_geography(supply_chain):
	"""Add geography labels to supply_entities."""
	for entry in (supply_chain.get("supply_entities") or []):
		if not isinstance(entry, dict):
			continue
		text = " ".join([
			entry.get("context", ""),
			entry.get("entity", ""),
			entry.get("relationship", ""),
		]).lower()

		geo_label = "Unknown"
		for loc in _INTERNATIONAL_HIGH_RISK:
			if loc in text:
				geo_label = "International"
				break
		if geo_label == "Unknown":
			for loc in _WESTERN_LOCATIONS:
				if loc in text:
					geo_label = "Western"
					break

		entry["supplier_geography"] = geo_label
		entry["classified_role"] = _classify_supplier_role(entry)


_BOILERPLATE_PATTERNS = [
	re.compile(r"no single customer accounted for", re.IGNORECASE),
	re.compile(r"we are not dependent on any single supplier", re.IGNORECASE),
	re.compile(r"no single supplier is material", re.IGNORECASE),
	re.compile(r"we do not believe.{0,30}dependent on any single", re.IGNORECASE),
	re.compile(r"no (?:material|significant) concentration", re.IGNORECASE),
]


def _assess_data_coverage(supply_chain):
	"""Classify data coverage for each supply chain category."""
	categories = [
		"supply_entities", "demand_entities", "geographic_exposure",
		"operational_risks", "purchase_obligations",
		"market_risk_disclosures", "inventory_composition",
	]
	all_contexts = []
	for cat in categories:
		for entry in (supply_chain.get(cat) or []):
			if isinstance(entry, dict):
				ctx = entry.get("context", "")
				if ctx:
					all_contexts.append(ctx)
	all_text = " ".join(all_contexts)
	has_boilerplate = any(p.search(all_text) for p in _BOILERPLATE_PATTERNS)

	coverage = {}
	for cat in categories:
		entries = supply_chain.get(cat) or []
		if len(entries) > 0:
			coverage[cat] = "extracted"
		elif has_boilerplate:
			coverage[cat] = "not_disclosed"
		else:
			coverage[cat] = "insufficient_context"
	return coverage


def _summarize_sec_supply_chain(data):
	"""Trim and cap SEC supply chain extraction for context efficiency."""
	if not data or data.get("error") or not data.get("data"):
		return data

	sc = data.get("data", {}).get("supply_chain")
	if not sc:
		return data

	high_volume = ("geographic_exposure", "operational_risks")
	for category in ("supply_entities", "demand_entities", "geographic_exposure",
					"operational_risks", "purchase_obligations",
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

	bottleneck_pre_score = None
	if has_sc_data:
		bottleneck_pre_score = _pre_score_bottleneck(sec_sc_raw)

	cleaned_sc = None
	if sec_sc_data and not sec_sc_data.get("error") and sec_sc_data.get("data"):
		sc_data = sec_sc_data["data"]
		cleaned_sc = {
			"filing": sc_data.get("filing"),
			"supply_chain": sc_data.get("supply_chain"),
		}

	cleaned_events = []
	if has_events:
		for ev in (sec_events_raw.get("data") or []):
			cleaned_events.append({
				"filing_date": ev.get("filing_date"),
				"event_type": ev.get("event_type"),
				"context": ev.get("context"),
				"confidence": ev.get("confidence"),
			})

	# Absence Evidence Flags
	absence_evidence_flags = []
	if has_sc_data:
		data_coverage = sec_sc_data.get("data", {}).get("data_coverage", {})
		supply_chain = sec_sc_data.get("data", {}).get("supply_chain", {})
		if data_coverage:
			demand = supply_chain.get("demand_entities", [])
			if not demand and data_coverage.get("demand_entities") == "not_disclosed":
				absence_evidence_flags.append({
					"type": "no_major_customer_disclosed",
					"signal": "negative",
				})
			if data_coverage.get("demand_entities") == "insufficient_context":
				absence_evidence_flags.append({
					"type": "revenue_concentration_unknown",
					"signal": "neutral",
				})
			if not has_events:
				absence_evidence_flags.append({
					"type": "no_fundamental_change_selloff",
					"signal": "potential_entry",
				})
			geo_exp = supply_chain.get("geographic_exposure", [])
			if geo_exp:
				supply_entries = [e for e in geo_exp if isinstance(e, dict) and e.get("supply_activity")]
				if supply_entries:
					all_intl = all(
						any(loc in (entry.get("region", "").lower())
							for loc in ("taiwan", "china", "korea", "vietnam", "malaysia"))
						for entry in supply_entries
					)
					if all_intl:
						absence_evidence_flags.append({
							"type": "no_domestic_production",
							"signal": "geopolitical_risk",
						})

			cap_coverage = data_coverage.get("operational_risks", "")
			po_coverage = data_coverage.get("purchase_obligations", "")
			if cap_coverage == "extracted" and po_coverage in ("not_disclosed", "insufficient_context"):
				absence_evidence_flags.append({
					"type": "marketed_vs_contracted_capacity_gap",
					"signal": "hype_risk",
				})

		# V3 Contagion Isolation: Mag7 direct customer flag
		MAG7_NAMES = {"microsoft", "google", "alphabet", "meta", "amazon", "apple", "nvidia"}
		all_customer_names = []
		for c in demand:
			if isinstance(c, dict):
				all_customer_names.append(c.get("entity", "").lower())
		mag7_matches = [n for n in all_customer_names if any(m in n for m in MAG7_NAMES)]
		if mag7_matches:
			absence_evidence_flags.append({
				"type": "mag7_direct_customer",
				"signal": "contagion_isolated",
				"matched": mag7_matches[:5],
				"thresholds": {"rule": "Mag7 direct contract = isolated from intermediary credit contagion", "source": "V3 financial dimension"},
			})

		# V3 Domestic production: reshoring beneficiary flag
		if geo_exp:
			has_domestic = any(
				any(loc in (entry.get("region", "").lower())
					for loc in ("united states", "usa", "u.s.", "texas", "california", "arizona", "ohio", "new york"))
				for entry in geo_exp if isinstance(entry, dict) and entry.get("region")
			)
			if has_domestic:
				absence_evidence_flags.append({
					"type": "domestic_production",
					"signal": "reshoring_beneficiary",
					"thresholds": {"rule": "US-based production = potential reshoring beneficiary", "source": "V3"},
				})

	# Clean bottleneck_pre_score
	cleaned_bn_score = None
	if bottleneck_pre_score and not bottleneck_pre_score.get("error"):
		cleaned_bn_score = {
			"pre_score": bottleneck_pre_score.get("pre_score"),
			"criteria": bottleneck_pre_score.get("criteria"),
			"assessment": bottleneck_pre_score.get("assessment"),
			"filing_date": bottleneck_pre_score.get("filing_date"),
			"sole_western_flag": bottleneck_pre_score.get("sole_western_flag"),
			"assessment_thresholds": {"strong": ">=3.0", "partial": ">=1.5", "weak": "<1.5"},
		}
		stale = bottleneck_pre_score.get("stale_data_warning")
		if stale:
			cleaned_bn_score["stale_data_warning"] = stale
		# Tacit knowledge flags
		for flag_key in ("technology_transition_flag", "competitive_risk_flag", "demand_concentration_flag"):
			val = bottleneck_pre_score.get(flag_key)
			if val:
				cleaned_bn_score[flag_key] = val

	result = {
		"data": {
			"sec_supply_chain": cleaned_sc,
			"sec_events": cleaned_events,
		},
		"bottleneck_pre_score": cleaned_bn_score,
		"absence_evidence_flags": absence_evidence_flags,
	}

	return result


# ---------------------------------------------------------------------------
# Bottleneck Pre-Scoring
# ---------------------------------------------------------------------------

_HIGH_RISK_LOCATIONS = {"taiwan", "china", "hong kong", "mainland china"}
_MEDIUM_RISK_LOCATIONS = {"south korea", "korea", "israel", "vietnam", "russia"}
_FX_HIGH_RISK_CURRENCIES = {
	"nt dollar": "taiwan", "nt$": "taiwan", "new taiwan dollar": "taiwan", "twd": "taiwan",
	"renminbi": "china", "rmb": "china", "cny": "china", "yuan": "china", "cnh": "china",
	"hkd": "hong kong", "hong kong dollar": "hong kong",
}


def _pre_score_bottleneck(sec_sc_data):
	"""Score SEC supply chain data against the 5-Criteria Bottleneck Framework."""
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
	for cat_key in ("supply_entities", "demand_entities", "geographic_exposure",
		"operational_risks", "purchase_obligations",
		"market_risk_disclosures", "inventory_composition"):
		for entry in (supply_chain.get(cat_key) or []):
			if isinstance(entry, dict):
				for field in ("context", "risk", "relationship", "role",
					"supply_activity", "obligation_type", "amount", "timeframe",
					"risk_type", "exposure", "sensitivity", "hedging",
					"category", "pct_of_total"):
					val = entry.get(field, "") or ""
					if val:
						all_texts.append(str(val))
	all_text_blob = " ".join(all_texts)

	supply_ents = supply_chain.get("supply_entities") or []
	purchase_obs = supply_chain.get("purchase_obligations") or []
	op_risks = supply_chain.get("operational_risks") or []

	# 1. Supply concentration (sole/primary keywords in supply_entities + purchase_obligations)
	sole_primary_pattern = re.compile(r"sole|primary|only|exclusive|single.?source|de\s*facto", re.IGNORECASE)
	sole_supplier_count = sum(
		1 for s in supply_ents
		if sole_primary_pattern.search((s.get("relationship", "") or "") + " " + (s.get("context", "") or ""))
	)
	# supply_disruption risks mentioning single-source act as SSD proxy
	ssd_proxy_count = sum(
		1 for r in op_risks
		if r.get("type") == "supply_disruption"
		and sole_primary_pattern.search((r.get("risk", "") or "") + " " + (r.get("context", "") or ""))
	)
	named_obligations = sum(1 for po in purchase_obs if po.get("counterparty"))

	total_sole = sole_supplier_count + ssd_proxy_count
	if total_sole >= 2:
		criteria["supply_concentration"] = {
			"score": 1.0,
			"evidence": f"{sole_supplier_count} sole/primary suppliers + {ssd_proxy_count} supply_disruption SSD mentions" + (f" + {named_obligations} named obligations" if named_obligations else ""),
		}
	elif total_sole >= 1 or named_obligations >= 2:
		sc_score = 0.75 if (total_sole >= 1 and named_obligations >= 1) else 0.5 if total_sole >= 1 else 0.75
		criteria["supply_concentration"] = {
			"score": sc_score,
			"evidence": f"{total_sole} sole/primary mentions, {named_obligations} named purchase obligations",
		}
	else:
		criteria["supply_concentration"] = {"score": 0.0, "evidence": "No single-source dependencies found"}

	# Tacit knowledge boost: foundry role + Taiwan/Korea geography → supply concentration reinforcement
	for s in supply_ents:
		classified = s.get("classified_role", _classify_supplier_role(s))
		geo = s.get("supplier_geography", "Unknown")
		if classified == "foundry" and geo == "International":
			geo_text = " ".join([s.get("context", ""), s.get("entity", "")]).lower()
			if any(loc in geo_text for loc in ("taiwan", "korea", "south korea")):
				current_score = criteria["supply_concentration"]["score"]
				if current_score > 0:
					criteria["supply_concentration"]["score"] = min(1.0, current_score + 0.15)
					criteria["supply_concentration"]["evidence"] += " + foundry in Taiwan/Korea (tacit boost)"
				break

	# 2. Capacity constraints (from operational_risks type=capacity_constraint + purchase_obligations)
	cc_risks = [r for r in op_risks if r.get("type") == "capacity_constraint"]
	duration_pattern = re.compile(r"(\d+)\s*(?:month|year|quarter)", re.IGNORECASE)
	resolving_pattern = re.compile(r"resolv|improv|eas|normaliz", re.IGNORECASE)
	billion_pattern = re.compile(r"\$[\d.]+\s*billion", re.IGNORECASE)
	multi_year_pattern = re.compile(r"(?:through|until|ending)\s+(?:fiscal\s+)?\d{4}|multi.?year|\d+\s*year", re.IGNORECASE)

	large_obligations = 0
	for po in purchase_obs:
		amt = (po.get("amount", "") or "") + " " + (po.get("context", "") or "")
		tf = (po.get("timeframe", "") or "") + " " + (po.get("context", "") or "")
		if billion_pattern.search(amt) and multi_year_pattern.search(tf):
			large_obligations += 1

	if cc_risks or large_obligations:
		max_duration_months = 0
		is_resolving = False
		for entry in cc_risks:
			ctx = (entry.get("context", "") or "") + " " + (entry.get("risk", "") or "")
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
			cc_evidence = f"{len(cc_risks)} constraint(s), duration >= {max_duration_months} months"
			if large_obligations:
				cc_score = min(1.0, cc_score + 0.25)
				cc_evidence += f" + {large_obligations} multi-year billion-dollar purchase obligation(s)"
		elif cc_risks:
			cc_score = 0.5
			cc_evidence = f"{len(cc_risks)} constraint(s) mentioned"
		else:
			cc_score = 0.5
			cc_evidence = f"{large_obligations} large purchase obligation(s) indicate capacity commitment"
		if is_resolving:
			cc_score = min(cc_score, 0.25)
			cc_evidence += " (resolving language detected — capped)"
		# Inventory composition boost
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

	# 3. Geopolitical risk (geographic_exposure with revenue_pct override)
	geo_exp = supply_chain.get("geographic_exposure") or []
	geo_risk_override = False

	# Quantitative override: entries with revenue_pct
	if geo_exp:
		high_risk_rev_pct = 0.0
		high_risk_regions = []
		for entry in geo_exp:
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
					"evidence": f"HIGH_RISK geographic revenue: {high_risk_rev_pct:.1f}% in {', '.join(high_risk_regions)} (quantitative)",
				}
			elif high_risk_rev_pct >= 15:
				criteria["geopolitical_risk"] = {
					"score": 0.75,
					"evidence": f"Moderate high-risk geographic revenue: {high_risk_rev_pct:.1f}% in {', '.join(high_risk_regions)} (quantitative)",
				}
			else:
				criteria["geopolitical_risk"] = {
					"score": 0.5,
					"evidence": f"Low high-risk geographic revenue: {high_risk_rev_pct:.1f}% in {', '.join(high_risk_regions)} (quantitative)",
				}

	# Heuristic fallback: use supply_activity entries
	if not geo_risk_override:
		supply_geo = [e for e in geo_exp if isinstance(e, dict) and e.get("supply_activity")]
		if supply_geo:
			regions = [entry.get("region", "").strip().lower() for entry in supply_geo if entry.get("region")]
			total = len(regions)
			if total > 0:
				loc_counts = Counter(r for r in regions if r)
				high_risk_count = sum(c for loc, c in loc_counts.items() if loc in _HIGH_RISK_LOCATIONS)
				medium_risk_count = sum(c for loc, c in loc_counts.items() if loc in _MEDIUM_RISK_LOCATIONS)
				most_common_loc, most_common_count = loc_counts.most_common(1)[0] if loc_counts else ("", 0)
				if high_risk_count > 0 and most_common_count / total > 0.3:
					criteria["geopolitical_risk"] = {
						"score": 1.0,
						"evidence": f"HIGH_RISK supply concentration: {high_risk_count}/{total} entries in {', '.join(l for l in loc_counts if l in _HIGH_RISK_LOCATIONS)}",
					}
				elif medium_risk_count > 0 or most_common_count / total > 0.5:
					criteria["geopolitical_risk"] = {
						"score": 0.75,
						"evidence": f"Supply concentration in medium-risk or dominant location: '{most_common_loc}' ({most_common_count}/{total})",
					}
				elif total > 0:
					criteria["geopolitical_risk"] = {"score": 0.5, "evidence": f"Supply data present across {len(loc_counts)} locations"}
				else:
					criteria["geopolitical_risk"] = {"score": 0.0, "evidence": "No geographic data"}
			else:
				criteria["geopolitical_risk"] = {"score": 0.0, "evidence": "No geographic data"}
		else:
			criteria["geopolitical_risk"] = {"score": 0.0, "evidence": "No geographic data"}

	# FX market risk reinforcement
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
			criteria["geopolitical_risk"]["evidence"] += " + FX high-risk exposure (Item 7A)"

	# 4. Long lead times (search all text + numeric extraction)
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

	# 5. No substitutes (search all categories + supply_disruption entries)
	no_sub_pattern = re.compile(
		r"cannot\s.*?replace|no\s.*?alternative|sole\s.*?source|only\s.*?supplier|"
		r"irreplaceable|no\s+viable\s+substitute|proprietary\s+process|"
		r"unique\s+capability|no\s+second\s+source|limited\s+alternative",
		re.IGNORECASE,
	)
	no_sub_found = no_sub_pattern.search(all_text_blob) is not None
	# Also check supply_disruption entries as SSD proxy
	ssd_confirmed = ssd_proxy_count > 0
	if no_sub_found and ssd_confirmed:
		criteria["no_substitutes"] = {"score": 0.75, "evidence": "Sole source language + supply_disruption single-source confirmed"}
	elif no_sub_found:
		criteria["no_substitutes"] = {"score": 0.5, "evidence": "Sole source / no substitute language found"}
	else:
		criteria["no_substitutes"] = {"score": 0.0, "evidence": "No sole-source language found"}

	# Commodity market risk reinforcement
	commodity_found = any(
		(mr.get("risk_type") or "").lower() == "commodity" for mr in mrd
	)
	if commodity_found and criteria["no_substitutes"]["score"] > 0:
		ns_score = min(1.0, criteria["no_substitutes"]["score"] + 0.15)
		criteria["no_substitutes"]["score"] = ns_score
		criteria["no_substitutes"]["evidence"] += " + commodity price exposure (Item 7A)"

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
	western_count = 0
	intl_count = 0
	for entry in supply_ents:
		geo = entry.get("supplier_geography", "Unknown")
		if geo == "Western":
			western_count += 1
		elif geo == "International":
			intl_count += 1
	if western_count == 1 and intl_count >= 1 and ssd_proxy_count >= 1:
		sole_western_flag = True

	# Tacit knowledge flags
	tech_transition_flag = any(r.get("type") == "technology_transition" for r in op_risks)
	competitive_risk_flag = any(r.get("type") == "competitive" for r in op_risks)
	demand_ents = supply_chain.get("demand_entities") or []
	demand_concentration_flag = any(
		d.get("concentration_flag") == "captive" for d in demand_ents if isinstance(d, dict)
	)

	filing_date_str = None
	stale_warning = None
	try:
		filing_date_str = sec_sc_data["data"]["filing"]["filing_date"]
		filing_dt = datetime.strptime(filing_date_str, "%Y-%m-%d")
		if (datetime.now() - filing_dt).days > 365:
			stale_warning = "Filing date > 12 months old"
	except (KeyError, TypeError, ValueError):
		pass

	result = {
		"pre_score": pre_score, "pre_score_max": pre_score_max,
		"criteria": criteria, "assessment": assessment,
		"filing_date": filing_date_str, "stale_data_warning": stale_warning,
		"sole_western_flag": sole_western_flag,
		"scoring_guide": {
			"total": "Sum of 5 criteria (max 4.25). Agent evaluates criterion 6 (cost insignificance) separately.",
			"assessment_thresholds": {"strong": ">=3.0", "partial": ">=1.5", "weak": "<1.5"},
			"investable_threshold": "4+/6 with agent's criterion 6 evaluation",
		},
	}
	if tech_transition_flag:
		result["technology_transition_flag"] = True
	if competitive_risk_flag:
		result["competitive_risk_flag"] = True
	if demand_concentration_flag:
		result["demand_concentration_flag"] = True

	return result
