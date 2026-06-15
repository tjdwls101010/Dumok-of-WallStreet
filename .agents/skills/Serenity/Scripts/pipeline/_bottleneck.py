"""Bottleneck pre-scoring and the SEC supply-chain extraction schema for the
Serenity pipeline.

The schema is an ENUM-FIRST classification preset: every scoring signal is a
top-level bounded enum/bool, so the LLM extraction converges on the SAME verdict
across runs. (An open-ended ``list[Entity]`` whose COUNT drives a score is the
root of non-determinism — two runs return different list lengths and the score
drifts.) Narrative fields only NAME things; the deterministic quantities come
from XBRL. ``_pre_score_bottleneck`` reads those enums — never a list length —
and gates non-physical business models out of the physical bottleneck criteria,
so a stablecoin issuer cannot score like a substrate maker.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# SEC Supply Chain Extraction Schema (enum-first Pydantic preset)
# ---------------------------------------------------------------------------

class SerenitySupplyChain(BaseModel):
	"""A bottleneck-investing verdict extracted from a SEC filing. Classify; do not enumerate."""

	__prompt__: ClassVar[str] = """\
You are a supply-chain analyst reading a SEC filing for a bottleneck-investing methodology.
Your job is to CLASSIFY the company, choosing exactly ONE value for each enum field from the
allowed options. Base every choice strictly on the filing's disclosures. When the filing is
silent or a field does not apply, choose the 'unknown' / 'not_applicable' / 'undisclosed'
option — never guess. The SAME filing must always yield the SAME classification.

Filing company: {company_name}

business_model — what the company fundamentally IS:
  physical_goods       = makes/sells a physical product (chips, hardware, materials, devices)
  resource_extraction  = mines/refines/produces a raw commodity or material
  financial_float      = earns mainly from holding/managing assets or a monetary float (bank, stablecoin issuer, insurer, asset manager)
  platform_marketplace = connects two sides and takes a fee/take-rate (exchange, payment rail, marketplace)
  services_subscription= sells services or software subscriptions, no significant physical product
  other                = none clearly fits

input_dependency — concentration of the company's OWN critical inputs (what it must buy to operate):
  sole_source_critical = depends on a sole/single source for a critical input it cannot easily replace
  concentrated         = a few key suppliers for important inputs
  diversified          = many interchangeable suppliers
  not_applicable       = no meaningful physical input chain (financial/services business)

customer_concentration — how dependent the company is on a few buyers:
  captive       = one customer is >50% of revenue or a sole-contract dependency
  concentrated  = a few named customers are a large share
  diversified   = broad customer base
  undisclosed   = filing does not disclose customer concentration

pricing_posture — pricing power as the filing portrays it:
  raises_prices    = states it has raised / can pass through prices
  has_power_unused = sole/critical position but no evidence it raises prices
  price_taker      = prices set by market/customers/commodity; little power
  unknown          = not discernible

geographic_risk — where its supply/manufacturing physically sits:
  mfg_in_controlled_region        = manufactures inside an export-controlled / high-risk region (e.g. China, Taiwan)
  sources_from_controlled_region  = sources key inputs from such a region but manufactures elsewhere
  geographically_diversified      = spread across regions
  domestic                        = primarily US-based production
  unknown                         = not discernible

designed_out_exposure — risk the company is replaced:
  physical_inevitability    = position rests on physics/no-substitute; very hard to design out
  convenience_substitutable = best option now, but alternatives could be built
  tech_transition_risk      = a technology shift could remove the need
  not_applicable            = no such dependency

regulatory_posture — how regulation bears on the business model:
  enabled_by_regulation   = a law/framework legitimizes or mandates the business (tailwind)
  headwind_from_regulation= regulation constrains/threatens the model
  neutral                 = no material regulatory driver

capacity_constrained — true if the filing discloses capacity constraints, extended lead times, or supply being allocated; else false.

Then NAME (exact names from the filing; lists max 5; empty string/list if not disclosed):
  critical_input        = the single deepest input the company itself depends on (e.g. "6N laser-grade InP feedstock"); "" if none
  critical_input_source = named source of that input, or "undisclosed"
  key_suppliers         = names of sole/critical suppliers only
  key_customers         = names of major/captive customers only
  strategic_backstop    = a named deep-pocketed partner/anchor-customer/government program, or ""
  bottleneck_evidence   = 1-2 sentences quoted from the filing supporting the bottleneck judgment, or ""

Extract from this filing:

{filing_text}
"""

	business_model: Literal["physical_goods", "resource_extraction", "financial_float",
							"platform_marketplace", "services_subscription", "other"]
	input_dependency: Literal["sole_source_critical", "concentrated", "diversified", "not_applicable"]
	customer_concentration: Literal["captive", "concentrated", "diversified", "undisclosed"]
	pricing_posture: Literal["raises_prices", "has_power_unused", "price_taker", "unknown"]
	geographic_risk: Literal["mfg_in_controlled_region", "sources_from_controlled_region",
							 "geographically_diversified", "domestic", "unknown"]
	designed_out_exposure: Literal["physical_inevitability", "convenience_substitutable",
								   "tech_transition_risk", "not_applicable"]
	regulatory_posture: Literal["enabled_by_regulation", "headwind_from_regulation", "neutral"]
	capacity_constrained: bool = False
	critical_input: str = ""
	critical_input_source: str = ""
	key_suppliers: list[str] = Field(default_factory=list)
	key_customers: list[str] = Field(default_factory=list)
	strategic_backstop: str = ""
	bottleneck_evidence: str = ""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Business models that can physically BE a bottleneck. Everything else is gated
# to zero on the five physical criteria (a financial-float / platform /
# services name has no input chain, capacity, or geographic supply risk).
_PHYSICAL_MODELS = {"physical_goods", "resource_extraction"}

# Region risk for XBRL geographic-revenue reinforcement.
_HIGH_RISK_REGIONS = {"taiwan", "china", "hong kong", "mainland china"}

# Mag7 names for contagion-isolation flagging (a direct Mag7 contract insulates
# the filer from intermediary/neocloud credit contagion — V3 financial dimension).
_MAG7_NAMES = {"microsoft", "msft", "google", "alphabet", "googl", "meta",
			   "amazon", "amzn", "apple", "aapl", "nvidia", "nvda"}


# ---------------------------------------------------------------------------
# Bottleneck Pre-Scoring (enum -> 5-criteria framework)
# ---------------------------------------------------------------------------

def _pre_score_bottleneck(classification, xbrl=None, filing=None):
	"""Map the enum-first classification onto the 5-criteria bottleneck framework.

	Each criterion reads a STABLE enum (never a list length), so the score is
	reproducible across extraction runs. The five criterion maxes sum to exactly
	pre_score_max = 4.25 (supply 1.0 + capacity 1.0 + geopolitical 1.0 +
	no_substitutes 0.75 + long_lead_times 0.5). Non-physical business models are
	gated to zero on every physical criterion.

	Output contract (preserved):
	  pre_score, pre_score_max=4.25,
	  criteria{supply_concentration, capacity_constraints, geopolitical_risk,
			   long_lead_times, no_substitutes} each {score, evidence},
	  assessment (strong>=3.0 / partial>=1.5 / weak),
	  filing_date, stale_data_warning, sole_western_flag, scoring_guide,
	  optional technology_transition_flag / competitive_risk_flag / demand_concentration_flag.
	"""
	if not classification or not isinstance(classification, dict):
		return {"error": "No SEC supply chain data available"}

	bm = classification.get("business_model")
	is_physical = bm in _PHYSICAL_MODELS

	inp = classification.get("input_dependency")
	cust = classification.get("customer_concentration")
	pricing = classification.get("pricing_posture")
	geo = classification.get("geographic_risk")
	designed_out = classification.get("designed_out_exposure")
	capacity = bool(classification.get("capacity_constrained"))

	xbrl = xbrl if isinstance(xbrl, dict) else {}
	criteria = {}

	if not is_physical:
		# business_model gate — a non-physical model is structurally not a
		# supply-chain bottleneck no matter what the narrative implies.
		for key, reason in (
			("supply_concentration", "no input chain"),
			("capacity_constraints", "no production capacity"),
			("geopolitical_risk", "no geographic supply risk"),
			("long_lead_times", "no lead times"),
			("no_substitutes", "not a physical chokepoint"),
		):
			criteria[key] = {"score": 0.0, "evidence": f"GATED: non-physical business_model={bm} — {reason}"}
	else:
		# 1. Supply concentration <- input_dependency (+ captive-customer boost).
		# A captive customer (>50% / sole-contract) means the filer is itself a
		# chokepoint that customer cannot replace — reinforce, don't double-weight.
		sc_map = {"sole_source_critical": 1.0, "concentrated": 0.6, "diversified": 0.2, "not_applicable": 0.0}
		sc_score = sc_map.get(inp, 0.0)
		sc_ev = f"input_dependency={inp}"
		if cust == "captive":
			sc_score = min(1.0, sc_score + 0.15) if sc_score > 0 else 0.5
			sc_ev += " + captive customer (filer is an unreplaceable chokepoint, demand-side V3)"
		criteria["supply_concentration"] = {"score": round(sc_score, 2), "evidence": sc_ev}

		# 2. Capacity constraints <- capacity_constrained (+ deterministic XBRL
		# purchase obligations and raw-materials inventory).
		cc_score = 0.6 if capacity else 0.0
		cc_ev = f"capacity_constrained={str(capacity).lower()}"
		po = xbrl.get("purchase_obligations") or []
		if po:
			cc_score = min(1.0, cc_score + 0.4)
			cc_ev += f" + {len(po)} XBRL purchase obligation(s)"
		inv = xbrl.get("inventory_composition") or []
		raw_pct = 0.0
		for e in inv:
			if isinstance(e, dict) and str(e.get("category", "")).lower().startswith("raw"):
				p = e.get("pct_of_total")
				if isinstance(p, (int, float)):
					raw_pct = max(raw_pct, p)
		if raw_pct > 50:
			cc_score = min(1.0, cc_score + 0.15)
			cc_ev += f" + raw-materials inventory {raw_pct:.0f}% (XBRL)"
		criteria["capacity_constraints"] = {"score": round(cc_score, 2), "evidence": cc_ev}

		# 3. Geopolitical risk <- geographic_risk (+ XBRL high-risk-region revenue).
		geo_map = {
			"mfg_in_controlled_region": 1.0,
			"sources_from_controlled_region": 0.75,
			"geographically_diversified": 0.3,
			"domestic": 0.0,
			"unknown": 0.0,
		}
		geo_score = geo_map.get(geo, 0.0)
		geo_ev = f"geographic_risk={geo}"
		hr_pct = 0.0
		for e in (xbrl.get("geographic_revenue") or []):
			if not isinstance(e, dict):
				continue
			region = str(e.get("region", "")).lower()
			pct = e.get("revenue_pct")
			if isinstance(pct, (int, float)) and any(hr in region for hr in _HIGH_RISK_REGIONS):
				hr_pct += pct
		if hr_pct >= 15 and geo_score < 1.0:
			geo_score = min(1.0, geo_score + 0.15)
			geo_ev += f" + {hr_pct:.0f}% revenue from high-risk region (XBRL)"
		criteria["geopolitical_risk"] = {"score": round(geo_score, 2), "evidence": geo_ev}

		# 4. Long lead times <- capacity + pricing power (constrained supply that
		# also prices up is the signature of a real, binding lead time).
		if capacity and pricing in ("raises_prices", "has_power_unused"):
			lt_score, lt_ev = 0.5, f"capacity_constrained + pricing_posture={pricing}"
		elif capacity:
			lt_score, lt_ev = 0.3, "capacity_constrained (lead-time proxy)"
		else:
			lt_score, lt_ev = 0.0, "no capacity/lead-time signal"
		criteria["long_lead_times"] = {"score": lt_score, "evidence": lt_ev}

		# 5. No substitutes <- designed_out_exposure.
		ns_map = {
			"physical_inevitability": 0.75,
			"convenience_substitutable": 0.3,
			"tech_transition_risk": 0.1,
			"not_applicable": 0.0,
		}
		ns_score = ns_map.get(designed_out, 0.0)
		criteria["no_substitutes"] = {"score": ns_score, "evidence": f"designed_out_exposure={designed_out}"}

	pre_score = round(sum(c["score"] for c in criteria.values()), 2)
	pre_score_max = 4.25

	if pre_score >= 3.0:
		assessment = "strong"
	elif pre_score >= 1.5:
		assessment = "partial"
	else:
		assessment = "weak"

	# Flags regenerated from enums.
	# sole_western_flag: a domestic producer with a sole/concentrated input chain
	# is the scarce Western/onshore source in its industry — the reshoring/
	# export-control moat (macro_and_catalyst.md "Made in America moat").
	sole_western_flag = (
		is_physical and geo == "domestic" and inp in ("sole_source_critical", "concentrated")
	)
	tech_transition_flag = designed_out == "tech_transition_risk"
	competitive_risk_flag = designed_out == "convenience_substitutable"
	demand_concentration_flag = cust == "captive"

	# Filing date / staleness.
	filing_date_str = None
	stale_warning = None
	if isinstance(filing, dict):
		filing_date_str = filing.get("filing_date")
		try:
			filing_dt = datetime.strptime(filing_date_str, "%Y-%m-%d")
			if (datetime.now() - filing_dt).days > 365:
				stale_warning = "Filing date > 12 months old"
		except (TypeError, ValueError):
			pass

	result = {
		"pre_score": pre_score, "pre_score_max": pre_score_max,
		"criteria": criteria, "assessment": assessment,
		"business_model": bm,
		"filing_date": filing_date_str, "stale_data_warning": stale_warning,
		"sole_western_flag": sole_western_flag,
		"scoring_guide": {
			"total": "Sum of 5 enum-mapped criteria (max 4.25). Non-physical business models are gated to 0. Agent evaluates criterion 6 (cost insignificance) separately.",
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


# ---------------------------------------------------------------------------
# L3 Bottleneck builder
# ---------------------------------------------------------------------------

def _build_l3_bottleneck(sec_sc_results):
	"""Build the L3 bottleneck output from the enum-first SEC classification,
	XBRL supplement, and recent SEC events.

	Absence/presence evidence flags are regenerated from the enums (geography,
	customer disclosure, Mag7 customers, designed-out risk) rather than from
	keyword scans of free-text lists.
	"""
	sec_sc_raw = sec_sc_results.get("sec_supply_chain", {})
	sec_events_raw = sec_sc_results.get("sec_events", {})

	sc_inner = sec_sc_raw.get("data") if isinstance(sec_sc_raw, dict) else None
	sc_inner = sc_inner or {}
	classification = sc_inner.get("classification") if isinstance(sc_inner, dict) else None
	xbrl = sc_inner.get("xbrl") if isinstance(sc_inner, dict) else None
	filing = sc_inner.get("filing") if isinstance(sc_inner, dict) else None

	has_sc_data = bool(
		classification and isinstance(classification, dict) and classification.get("business_model")
	)
	has_events = bool(
		sec_events_raw
		and not sec_events_raw.get("error")
		and len(sec_events_raw.get("data", [])) > 0
	)

	bottleneck_pre_score = None
	if has_sc_data:
		bottleneck_pre_score = _pre_score_bottleneck(classification, xbrl, filing)

	cleaned_sc = None
	if has_sc_data:
		cleaned_sc = {
			"filing": filing,
			"classification": classification,
			"xbrl": xbrl if isinstance(xbrl, dict) else {},
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

	# Absence / presence evidence flags — regenerated from enums.
	absence_evidence_flags = []
	if has_sc_data:
		bm = classification.get("business_model")
		is_physical = bm in _PHYSICAL_MODELS
		geo = classification.get("geographic_risk")
		cust = classification.get("customer_concentration")
		designed_out = classification.get("designed_out_exposure")
		key_customers = classification.get("key_customers") or []

		if cust == "undisclosed":
			absence_evidence_flags.append({"type": "no_major_customer_disclosed", "signal": "negative"})

		# No recent material SEC event — a selloff here is likely non-fundamental.
		if not has_events:
			absence_evidence_flags.append({"type": "no_fundamental_change_selloff", "signal": "potential_entry"})

		if is_physical and geo in ("mfg_in_controlled_region", "sources_from_controlled_region"):
			absence_evidence_flags.append({"type": "no_domestic_production", "signal": "geopolitical_risk"})
		if is_physical and geo == "domestic":
			absence_evidence_flags.append({
				"type": "domestic_production",
				"signal": "reshoring_beneficiary",
				"thresholds": {"rule": "US-based production = potential reshoring beneficiary", "source": "V3"},
			})

		if designed_out == "tech_transition_risk":
			absence_evidence_flags.append({"type": "technology_transition_risk", "signal": "hype_risk"})

		mag7_matches = [c for c in key_customers if any(m in str(c).lower() for m in _MAG7_NAMES)]
		if mag7_matches:
			absence_evidence_flags.append({
				"type": "mag7_direct_customer",
				"signal": "contagion_isolated",
				"matched": mag7_matches[:5],
				"thresholds": {"rule": "Mag7 direct contract = isolated from intermediary credit contagion", "source": "V3 financial dimension"},
			})

	# Clean bottleneck_pre_score for output.
	cleaned_bn_score = None
	if bottleneck_pre_score and not bottleneck_pre_score.get("error"):
		cleaned_bn_score = {
			"pre_score": bottleneck_pre_score.get("pre_score"),
			"pre_score_max": bottleneck_pre_score.get("pre_score_max"),
			"criteria": bottleneck_pre_score.get("criteria"),
			"assessment": bottleneck_pre_score.get("assessment"),
			"business_model": bottleneck_pre_score.get("business_model"),
			"filing_date": bottleneck_pre_score.get("filing_date"),
			"sole_western_flag": bottleneck_pre_score.get("sole_western_flag"),
			"assessment_thresholds": {"strong": ">=3.0", "partial": ">=1.5", "weak": "<1.5"},
		}
		stale = bottleneck_pre_score.get("stale_data_warning")
		if stale:
			cleaned_bn_score["stale_data_warning"] = stale
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
