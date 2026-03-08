#!/usr/bin/env python3
"""Benchmark: Gemini thinking level x model comparison for SEC supply chain extraction.

Tests 6 cases: 2 models x 3 thinking levels on AAPL 10-K filing.
Measures: time, extraction quality (total matches, unique entities), token usage.
"""
import json
import os
import sys
import time

from typing import Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic schema (copied from supply_chain.py)
# ---------------------------------------------------------------------------

class SupplierEntry(BaseModel):
    entity: str = Field(description="Name of the supplier company.")
    relationship: str = Field(default="")
    context: str = Field(default="")

class CustomerEntry(BaseModel):
    entity: str = Field(description="Name of the customer company.")
    relationship: str = Field(default="")
    context: str = Field(default="")

class SingleSourceEntry(BaseModel):
    component: str = Field(default="")
    supplier: str = Field(description="Name of the sole-source supplier.")
    context: str = Field(default="")

class GeographicEntry(BaseModel):
    location: str = Field(description="Country or region name.")
    activity: str = Field(default="")
    context: str = Field(default="")

class CapacityConstraintEntry(BaseModel):
    constraint: str = Field(description="Type of capacity constraint.")
    context: str = Field(default="")

class SupplyChainRiskEntry(BaseModel):
    risk: str = Field(description="Type of supply chain risk.")
    context: str = Field(default="")

class RevenueConcentrationEntry(BaseModel):
    entity: str = Field(description="Customer or segment name.")
    revenue_pct: float | None = Field(default=None)
    revenue_amount: str = Field(default="")
    context: str = Field(default="")

class GeographicRevenueEntry(BaseModel):
    region: str = Field(description="Country or region.")
    revenue_pct: float | None = Field(default=None)
    revenue_amount: str = Field(default="")
    context: str = Field(default="")

class PurchaseObligationEntry(BaseModel):
    counterparty: str = Field(default="")
    obligation_type: str = Field(description="Type.")
    amount: str = Field(default="")
    timeframe: str = Field(default="")
    context: str = Field(default="")

class MarketRiskEntry(BaseModel):
    risk_type: Literal["commodity", "fx", "interest_rate"] = Field(description="Type.")
    exposure: str = Field(default="")
    sensitivity: str = Field(default="")
    hedging: str = Field(default="")
    context: str = Field(default="")

class InventoryCompositionEntry(BaseModel):
    category: Literal["raw_materials", "work_in_progress", "finished_goods"] = Field(description="Category.")
    amount: str = Field(default="")
    pct_of_total: float | None = Field(default=None)
    context: str = Field(default="")

class SupplyChainExtraction(BaseModel):
    suppliers: list[SupplierEntry] = Field(default_factory=list)
    customers: list[CustomerEntry] = Field(default_factory=list)
    single_source_dependencies: list[SingleSourceEntry] = Field(default_factory=list)
    geographic_concentration: list[GeographicEntry] = Field(default_factory=list)
    capacity_constraints: list[CapacityConstraintEntry] = Field(default_factory=list)
    supply_chain_risks: list[SupplyChainRiskEntry] = Field(default_factory=list)
    revenue_concentration: list[RevenueConcentrationEntry] = Field(default_factory=list)
    geographic_revenue: list[GeographicRevenueEntry] = Field(default_factory=list)
    purchase_obligations: list[PurchaseObligationEntry] = Field(default_factory=list)
    market_risk_disclosures: list[MarketRiskEntry] = Field(default_factory=list)
    inventory_composition: list[InventoryCompositionEntry] = Field(default_factory=list)


_LLM_PROMPT = """\
You are a financial analyst extracting supply chain intelligence from SEC filings.
Extract entities and relationships exactly as stated in the filing text.

The filing text below is the complete SEC filing in markdown format.
Identify relevant sections by their natural headings:
- Item 1 (Business): suppliers, customers, single-source dependencies
- Item 1A (Risk Factors): supply chain risks, geographic concentration
- Item 7 (MD&A): capacity constraints, operating discussion
- Item 7A (Market Risk): commodity/FX/interest rate exposures
- Item 8 Notes: revenue segments, inventory, commitments, concentration
For 20-F filings, look for equivalent items (Item 4, 3D, 5, 11, 18/19).

Rules:
1. Use exact company names from the filing.
2. For context fields, copy 1-3 relevant sentences verbatim.
3. If a category has no relevant data, return an empty list.
4. Do NOT extract the filing company itself as its own supplier or customer.
5. Focus on factual supply chain relationships.
6. De facto single-source: If a supplier is the PRIMARY or ONLY provider for a critical
   component and NO alternative is mentioned, classify as single_source_dependencies.
7. Customer extraction: Look for revenue concentration, named buyers, segment mentions.
8. Relationship specificity: Use precise descriptions.
9. Only infer relationships where the filing text provides support.
10. Revenue concentration: From Notes, extract customers/segments with specific % of revenue.
11. Geographic revenue: From Notes, extract revenue by country/region with exact percentages.
12. Purchase obligations: From Notes (Commitments), extract purchase commitments.
13. Market risk disclosures: From Item 7A, extract commodity, FX, interest rate risks.
14. Inventory composition: From Notes (Inventory), extract raw materials, WIP, finished goods.

Filing company: {company_name}

Extract all supply chain entities from this SEC filing text:

{filing_text}
"""


def count_extraction(extraction):
    """Count total matches and unique entities from extraction."""
    total = 0
    entities = set()
    for e in extraction.suppliers:
        total += 1; entities.add(e.entity)
    for e in extraction.customers:
        total += 1; entities.add(e.entity)
    for e in extraction.single_source_dependencies:
        total += 1; entities.add(e.supplier)
    for e in extraction.geographic_concentration:
        total += 1
    for e in extraction.capacity_constraints:
        total += 1
    for e in extraction.supply_chain_risks:
        total += 1
    for e in extraction.revenue_concentration:
        total += 1
        if e.entity: entities.add(e.entity)
    for e in extraction.geographic_revenue:
        total += 1
    for e in extraction.purchase_obligations:
        total += 1
        if e.counterparty: entities.add(e.counterparty)
    for e in extraction.market_risk_disclosures:
        total += 1
    for e in extraction.inventory_composition:
        total += 1
    return total, entities


def category_breakdown(extraction):
    return {
        "suppliers": len(extraction.suppliers),
        "customers": len(extraction.customers),
        "single_source": len(extraction.single_source_dependencies),
        "geo_conc": len(extraction.geographic_concentration),
        "cap_constr": len(extraction.capacity_constraints),
        "sc_risks": len(extraction.supply_chain_risks),
        "rev_conc": len(extraction.revenue_concentration),
        "geo_rev": len(extraction.geographic_revenue),
        "purch_obl": len(extraction.purchase_obligations),
        "mkt_risk": len(extraction.market_risk_disclosures),
        "inv_comp": len(extraction.inventory_composition),
    }


def run_benchmark():
    from google import genai
    from google.genai import types
    from edgar import Company, set_identity
    from dotenv import load_dotenv

    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(__file__)))), ".env")
    load_dotenv(env_path)
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # --- Step 1: Get AAPL filing (once) ---
    print("=" * 70)
    print("Loading AAPL 10-K filing via edgartools...")
    identity = os.environ.get("EDGAR_IDENTITY", "MarketData/1.0 contact@example.com")
    set_identity(identity)

    t0 = time.time()
    company = Company("AAPL")
    filings = company.get_filings(form="10-K")
    filing = filings[0]
    md_text = filing.markdown()
    t_load = time.time() - t0

    print(f"Filing loaded: {len(md_text):,} chars in {t_load:.1f}s")
    print(f"Company: {company.name}, Date: {filing.filing_date}")
    print("=" * 70)

    prompt = _LLM_PROMPT.format(
        company_name=company.name or "Unknown",
        filing_text=md_text,
    )
    print(f"Prompt length: {len(prompt):,} chars")
    print()

    # --- Step 2: Define test cases ---
    models = ["gemini-3.1-flash-lite-preview", "gemini-3-flash-preview"]
    thinking_levels = ["low", "medium", "high"]

    results = []

    for model_id in models:
        for level in thinking_levels:
            label = f"{model_id} / thinking={level}"
            print(f"--- Running: {label} ---")

            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=SupplyChainExtraction.model_json_schema(),
                temperature=0.1,
                thinking_config=types.ThinkingConfig(thinking_level=level),
            )

            t_start = time.time()
            error_msg = None
            extraction = None
            usage = {}

            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config=config,
                )
                elapsed = time.time() - t_start

                extraction = SupplyChainExtraction.model_validate_json(response.text)

                um = response.usage_metadata
                usage = {
                    "prompt_tokens": getattr(um, "prompt_token_count", None),
                    "output_tokens": getattr(um, "candidates_token_count", None),
                    "thinking_tokens": getattr(um, "thoughts_token_count", None),
                    "total_tokens": getattr(um, "total_token_count", None),
                }

            except Exception as e:
                elapsed = time.time() - t_start
                error_msg = str(e)[:300]

            total_matches = 0
            unique_entities = 0
            cats = {}
            if extraction:
                total_matches, ents = count_extraction(extraction)
                unique_entities = len(ents)
                cats = category_breakdown(extraction)

            result = {
                "model": model_id,
                "thinking_level": level,
                "time_sec": round(elapsed, 1),
                "total_matches": total_matches,
                "unique_entities": unique_entities,
                "error": error_msg,
                **usage,
            }
            if cats:
                result["categories"] = cats
            results.append(result)

            if error_msg:
                print(f"  ERROR ({elapsed:.1f}s): {error_msg}")
            else:
                print(f"  Time: {elapsed:.1f}s | Matches: {total_matches} | Entities: {unique_entities}")
                print(f"  Tokens - prompt: {usage.get('prompt_tokens')}, output: {usage.get('output_tokens')}, thinking: {usage.get('thinking_tokens')}")
                print(f"  Categories: {cats}")
            print()

    # --- Summary table ---
    print("=" * 70)
    print("BENCHMARK SUMMARY (AAPL 10-K)")
    print("=" * 70)
    header = f"{'Model':<35} {'Think':>6} {'Time':>7} {'Match':>6} {'Ent':>5} {'Think_T':>8} {'Out_T':>7}"
    print(header)
    print("-" * len(header))
    for r in results:
        if r["error"]:
            print(f"{r['model']:<35} {r['thinking_level']:>6} {r['time_sec']:>6.1f}s {'ERR':>6}")
        else:
            tt = r.get('thinking_tokens', '-')
            ot = r.get('output_tokens', '-')
            print(f"{r['model']:<35} {r['thinking_level']:>6} {r['time_sec']:>6.1f}s {r['total_matches']:>6} {r['unique_entities']:>5} {tt:>8} {ot:>7}")
    print()

    out_path = os.path.join(os.path.dirname(__file__), "_benchmark_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Detailed results saved to: {out_path}")


if __name__ == "__main__":
    run_benchmark()
