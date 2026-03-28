"""Supply chain intelligence preset for SEC filings.

Extracts supply entities, demand entities, geographic exposure,
operational risks, purchase obligations, market risk disclosures,
and inventory composition from 10-K/10-Q/20-F filings.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field


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
