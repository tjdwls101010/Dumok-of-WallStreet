#!/usr/bin/env python3
"""SEC supply chain intelligence extraction from 10-K/10-Q/20-F and 8-K filings.

Extracts supply chain relationships, single-source dependencies, geographic
concentration, capacity constraints, revenue concentration, geographic revenue
breakdown, purchase obligations, market risk disclosures (Item 7A), and
inventory composition from SEC filings. Uses edgartools for filing discovery
and markdown conversion (tables preserved). Entire filing markdown sent to
Gemini for structured extraction (no section pre-extraction). XBRL structured
data supplements 4 quantitative categories: revenue concentration, geographic
revenue, inventory composition, and purchase obligations.

Commands:
	supply-chain: Extract supply chain structure from latest 10-K, 10-Q, or 20-F
	events: Extract supply-chain-related events from recent 8-K filings

Args:
	For supply-chain:
		symbol (str): Stock ticker symbol (e.g., "AAPL", "NVDA", "TSM")
		--form (str): Filing form type, "10-K", "10-Q", or "20-F" (default: "10-K", auto-fallback to 20-F)
		--max-chars (int): Max characters for entire filing markdown (default: 2000000)

	For events:
		symbol (str): Stock ticker symbol
		--limit (int): Max 8-K filings to check (default: 10)
		--days (int): Lookback window in days (default: 180)

Returns:
	cmd_supply_chain_extract:
	dict: {
		"data": {
			"filing": {
				"form": str,
				"filing_date": str,
				"accession_number": str,
				"filing_url": str
			},
			"supply_chain": {
				"suppliers": [{"entity": str, "relationship": str,
					"context": str, "source_section": str,
					"confidence": str,
					"supplier_geography": str}],
				"customers": [{"entity": str, "relationship": str,
					"context": str, "source_section": str,
					"confidence": str}],
				"single_source_dependencies": [{"component": str,
					"supplier": str, "context": str,
					"source_section": str, "confidence": str,
					"supplier_geography": str}],
				"geographic_concentration": [{"location": str,
					"activity": str, "context": str,
					"source_section": str, "confidence": str}],
				"capacity_constraints": [{"constraint": str,
					"context": str, "source_section": str,
					"confidence": str}],
				"supply_chain_risks": [{"risk": str, "context": str,
					"source_section": str, "confidence": str}],
				"revenue_concentration": [{"entity": str,
					"revenue_pct": float|None, "revenue_amount": str,
					"context": str}],
				"geographic_revenue": [{"region": str,
					"revenue_pct": float|None, "revenue_amount": str,
					"context": str}],
				"purchase_obligations": [{"counterparty": str,
					"obligation_type": str, "amount": str,
					"timeframe": str, "context": str}],
				"market_risk_disclosures": [{"risk_type": str,
					"exposure": str, "sensitivity": str,
					"hedging": str, "context": str}],
				"inventory_composition": [{"category": str,
					"amount": str, "pct_of_total": float|None,
					"context": str}]
			},
			"extraction_stats": {
				"total_matches": int,
				"unique_entities": int,
				"mode": "llm",
				"xbrl_categories": list,
				"xbrl_supplemented": bool
			},
			"data_coverage": {
				"<category>": str
			}
		},
		"metadata": {
			"symbol": str,
			"company_name": str,
			"form": str
		}
	}

	supplier_geography field values:
		- "Western": US, Canada, UK, EU, Australia, Japan, New Zealand
		- "International": Taiwan, China, Hong Kong, South Korea, etc.
		- "Unknown": location not determinable from filing text
	Note: supplier_geography is added to suppliers and single_source_dependencies only.

	data_coverage maps each of the 11 supply chain categories to a status:
		- "extracted": 1+ entries exist with actual entity/data
		- "not_disclosed": empty but SEC boilerplate detected (deliberate non-disclosure)
		- "insufficient_context": empty and no boilerplate detected

	cmd_events:
	dict: {
		"data": [{
			"filing_date": str,
			"accession_number": str,
			"filing_url": str,
			"event_type": str,
			"supply_chain_relevance": str,
			"context": str,
			"confidence": str
		}],
		"metadata": {
			"symbol": str,
			"cik": str,
			"company_name": str,
			"filings_checked": int,
			"supply_chain_events_found": int
		}
	}

Example:
	>>> python supply_chain.py supply-chain AAPL
	>>> python supply_chain.py supply-chain TSM
	>>> python supply_chain.py events NVDA --limit 5 --days 180

Use Cases:
	- Pre-extract supply chain structure for L3 bottleneck analysis
	- Identify single-source dependencies from legal disclosures
	- Detect geographic concentration risk from official filings
	- Monitor 8-K events for supply chain disruptions or material agreements

Notes:
	- Requires edgartools for filing discovery and markdown conversion
	- LLM mode requires GOOGLE_API_KEY in .env file
	- XBRL supplementation adds structured data for 4 quantitative categories
	- Gemini 1M context handles entire filing markdown without section splitting
	- edgartools handles SEC rate limiting automatically

See Also:
	- sec/filings.py: General SEC filings access and MD&A extraction
	- pipelines/serenity.py: Consumes supply chain data in L3 bottleneck layer
"""

import argparse
import os
import re
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils import error_json, output_json, safe_run

# Handle both direct execution and module import
if __name__ == "__main__":
	# Add parent paths for direct execution
	sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
	from data_advanced.sec import SEC_HEADERS, get_cik_from_symbol, get_company_info
else:
	from . import SEC_HEADERS, get_cik_from_symbol, get_company_info


# ---------------------------------------------------------------------------
# edgartools integration
# ---------------------------------------------------------------------------

_MAX_MARKDOWN_CHARS = 2_000_000  # Gemini 1M token context


def _init_edgartools():
	"""edgartools SEC identity initialization."""
	from edgar import set_identity
	from dotenv import load_dotenv
	env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
		os.path.dirname(__file__)))), ".env")
	load_dotenv(env_path)
	identity = os.environ.get("EDGAR_IDENTITY",
	                          "MarketData/1.0 contact@example.com")
	set_identity(identity)


def _get_filing(symbol, form="10-K"):
	"""Search latest filing via edgartools. Auto-fallback 10-K → 20-F.

	Returns:
		tuple: (filing, metadata_dict, company_name)
	Raises:
		ValueError: if no filing found after fallback
	"""
	from edgar import Company
	_init_edgartools()
	company = Company(symbol)

	retries = 3
	last_error = None
	for attempt in range(1, retries + 1):
		try:
			filings = company.get_filings(form=form)
			if len(filings) == 0 and form == "10-K":
				filings = company.get_filings(form="20-F")
				form = "20-F"
			if len(filings) == 0:
				raise ValueError(f"No {form} filing found for {symbol}")
			filing = filings[0]
			metadata = {
				"form": form,
				"filing_date": str(filing.filing_date),
				"accession_number": filing.accession_number,
				"filing_url": filing.filing_url,
			}
			return filing, metadata, company.name
		except ValueError:
			raise
		except Exception as e:
			last_error = e
			print(f"[supply_chain] edgartools attempt {attempt}/{retries} failed: {e}",
			      file=sys.stderr)
			if attempt < retries:
				time.sleep(2 ** attempt)
				continue
	raise RuntimeError(f"edgartools failed after {retries} attempts: {last_error}")


def _get_filing_markdown(filing, max_chars=_MAX_MARKDOWN_CHARS):
	"""Convert filing to markdown with safe truncation."""
	md = filing.markdown()
	if len(md) > max_chars:
		md = md[:max_chars]
	return md


# ---------------------------------------------------------------------------
# XBRL structured data extraction
# ---------------------------------------------------------------------------

def _extract_xbrl_supplements(filing):
	"""Extract 4 quantitative categories from XBRL structured data.

	Categories: revenue_concentration, geographic_revenue,
	inventory_composition, purchase_obligations.
	Returns empty dict if XBRL unavailable.
	"""
	try:
		xbrl = filing.xbrl()
		if xbrl is None:
			return {}
	except Exception:
		return {}

	supplements = {}

	try:
		df = xbrl.instance.facts.reset_index()
	except Exception:
		return {}

	# --- Revenue Concentration ---
	conc = df[df["concept"].astype(str).str.contains(
		"ConcentrationRiskPercentage", case=False, na=False)]
	if len(conc) > 0:
		# Filter to revenue benchmark only (exclude AR, asset-based benchmarks)
		benchmark_col = "us-gaap:ConcentrationRiskByBenchmarkAxis"
		if benchmark_col in conc.columns:
			conc = conc[
				conc[benchmark_col].astype(str).str.contains(
					"Revenue", case=False, na=False)
			]

		# Filter to most recent period only
		if "end_date" in conc.columns and len(conc) > 0:
			latest_date = conc["end_date"].max()
			conc = conc[conc["end_date"] == latest_date]

		entries = []
		seen_entities = set()
		for _, row in conc.iterrows():
			customer = str(row.get("srt:MajorCustomersAxis", ""))
			if not customer or customer == "nan":
				continue
			# Clean member name: "aapl:CustomerOneMember" → "Customer One"
			name = customer.split(":")[-1].replace("Member", "")
			# Add spaces before capitals
			name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)

			# Skip geographic groupings (belongs in geographic_revenue)
			_GEO_KEYWORDS = ("Based End Customers", "Region", "Country",
			                 "Americas", "Europe", "Asia", "Pacific",
			                 "United States", "China", "Japan")
			if any(kw.lower() in name.lower() for kw in _GEO_KEYWORDS):
				continue

			# Deduplicate by entity name within XBRL
			if name in seen_entities:
				continue
			seen_entities.add(name)

			try:
				pct = round(float(row["value"]) * 100, 2)
			except (ValueError, TypeError):
				pct = None
			entries.append({
				"entity": name,
				"revenue_pct": pct,
				"revenue_amount": "",
				"context": f"XBRL: {row['concept']} ({row.get('end_date', '')})",
				"source_section": "xbrl",
				"confidence": "high",
			})
		if entries:
			supplements["revenue_concentration"] = entries

	# --- Geographic Revenue ---
	geo_col = "srt:StatementGeographicalAxis"
	if geo_col in df.columns:
		geo = df[
			(df[geo_col].notna()) &
			(df["concept"].astype(str).str.contains(
				"Revenue", case=False, na=False))
		]
		if len(geo) > 0:
			# Get total revenue for percentage calculation.
			# Multiple rows may exist (quarterly vs annual, segment breakdowns).
			# Filter out TextBlock/Policy rows, convert to numeric, pick the max
			# for the most recent end_date (= annual total).
			# Find total revenue: try specific concept first, then broader
			import pandas as pd
			_rev_patterns = [
				"RevenueFromContractWithCustomer",
				r"^us-gaap:Revenues$",
			]
			total_rev = None
			for _rev_pat in _rev_patterns:
				total_rev_rows = df[
					(df["concept"].astype(str).str.contains(
						_rev_pat, case=False, na=False)) &
					(~df["concept"].astype(str).str.contains(
						"TextBlock|Policy|Description|Period|Percentage|Cost",
						case=False, na=False)) &
					(df[geo_col].isna()) &
					(df["period_type"] == "duration")
				].copy()
				if len(total_rev_rows) > 0:
					try:
						total_rev_rows["_val"] = pd.to_numeric(
							total_rev_rows["value"], errors="coerce")
						total_rev_rows = total_rev_rows.dropna(subset=["_val"])
						if len(total_rev_rows) > 0:
							latest_date = total_rev_rows["end_date"].max()
							latest = total_rev_rows[
								total_rev_rows["end_date"] == latest_date]
							total_rev = float(latest["_val"].max())
							break
					except Exception:
						continue

			entries = []
			seen = set()
			for _, row in geo.iterrows():
				region_raw = str(row[geo_col])
				# "country:US" → "United States", "country:CN" → "China"
				region = region_raw.split(":")[-1].replace("Member", "")
				region = re.sub(r"([a-z])([A-Z])", r"\1 \2", region)
				_COUNTRY_MAP = {
					"US": "United States", "CN": "China", "JP": "Japan",
					"TW": "Taiwan", "KR": "South Korea", "DE": "Germany",
					"GB": "United Kingdom", "IN": "India",
				}
				region = _COUNTRY_MAP.get(region, region)

				try:
					amount = float(row["value"])
				except (ValueError, TypeError):
					continue

				end_date = str(row.get("end_date", ""))
				dedup_key = f"{region}_{end_date}"
				if dedup_key in seen:
					continue
				seen.add(dedup_key)

				pct = round(amount / total_rev * 100, 2) if total_rev else None
				amount_str = f"${amount / 1e9:.1f}B" if amount >= 1e9 else f"${amount / 1e6:.0f}M"
				entries.append({
					"region": region,
					"revenue_pct": pct,
					"revenue_amount": amount_str,
					"context": f"XBRL: {row['concept']} ({end_date})",
					"source_section": "xbrl",
					"confidence": "high",
				})
			if entries:
				# Keep only the most recent period
				entries.sort(key=lambda x: x["context"], reverse=True)
				# Group by unique period (take first batch)
				if entries:
					first_period = entries[0]["context"].split("(")[-1].rstrip(")")
					entries = [e for e in entries
					           if first_period in e["context"]]
				supplements["geographic_revenue"] = entries

	# --- Inventory Composition ---
	inv_concepts = {
		"InventoryRawMaterialsAndSupplies": "raw_materials",
		"InventoryRawMaterials": "raw_materials",
		"InventoryWorkInProcess": "work_in_progress",
		"InventoryFinishedGoods": "finished_goods",
		"InventoryFinishedGoodsAndWorkInProcess": "finished_goods",
	}
	inv_total_row = df[df["concept"].astype(str).str.contains(
		r"^us-gaap:InventoryNet$", case=False, na=False)]
	inv_total = None
	if len(inv_total_row) > 0:
		try:
			inv_total = float(inv_total_row.iloc[0]["value"])
		except (ValueError, TypeError):
			pass

	inv_entries = []
	inv_component_total = 0.0
	for concept_suffix, category in inv_concepts.items():
		rows = df[df["concept"].astype(str).str.contains(
			concept_suffix, case=False, na=False)]
		if len(rows) > 0:
			row = rows.iloc[0]
			try:
				amount = float(row["value"])
			except (ValueError, TypeError):
				continue
			inv_component_total += amount
			amount_str = f"${amount / 1e9:.1f}B" if amount >= 1e9 else f"${amount / 1e6:.0f}M"
			inv_entries.append({
				"category": category,
				"amount": amount_str,
				"_raw_amount": amount,
				"context": f"XBRL: {row['concept']} ({row.get('end_date', '')})",
				"source_section": "xbrl",
				"confidence": "high",
			})
	if inv_entries:
		# Use component sum as denominator if it exceeds InventoryNet (net of reserves)
		denom = inv_total if inv_total and inv_component_total <= inv_total * 1.05 else inv_component_total
		for e in inv_entries:
			raw_amt = e.pop("_raw_amount")
			e["pct_of_total"] = round(raw_amt / denom * 100, 2) if denom else None
		supplements["inventory_composition"] = inv_entries

	# --- Purchase Obligations ---
	po_rows = df[df["concept"].astype(str).str.contains(
		"UnrecordedUnconditionalPurchaseObligation", case=False, na=False)]
	# Filter out text blocks
	po_rows = po_rows[~po_rows["concept"].astype(str).str.contains(
		"TextBlock|Policy", case=False, na=False)]
	if len(po_rows) > 0:
		po_entries = []
		for _, row in po_rows.iterrows():
			concept = str(row["concept"])
			try:
				amount = float(row["value"])
			except (ValueError, TypeError):
				continue
			amount_str = f"${amount / 1e9:.1f}B" if amount >= 1e9 else f"${amount / 1e6:.0f}M"

			# Determine timeframe from concept name
			timeframe = ""
			if "BalanceSheetAmount" in concept:
				timeframe = "total"
			elif "FirstAnniversary" in concept:
				timeframe = "year 1"
			elif "SecondAnniversary" in concept:
				timeframe = "year 2"
			elif "ThirdAnniversary" in concept:
				timeframe = "year 3"
			elif "FourthAnniversary" in concept:
				timeframe = "year 4"
			elif "FifthAnniversary" in concept:
				timeframe = "year 5"
			elif "AfterFiveYears" in concept:
				timeframe = "after year 5"

			po_entries.append({
				"counterparty": "",
				"obligation_type": "unconditional purchase obligation",
				"amount": amount_str,
				"timeframe": timeframe,
				"context": f"XBRL: {concept} ({row.get('end_date', '')})",
				"source_section": "xbrl",
				"confidence": "high",
			})
		if po_entries:
			supplements["purchase_obligations"] = po_entries

	return supplements


def _merge_xbrl_with_llm(llm_supply_chain, xbrl_data):
	"""Merge XBRL supplements into LLM results. Supplement, never override.

	XBRL entries are appended with source_section="xbrl" and confidence="high".
	Both LLM and XBRL data preserved (duplicates allowed for downstream use).
	"""
	if not xbrl_data:
		return llm_supply_chain, []

	xbrl_categories = list(xbrl_data.keys())
	for category, entries in xbrl_data.items():
		if category in llm_supply_chain:
			llm_supply_chain[category].extend(entries)
		else:
			llm_supply_chain[category] = entries

	return llm_supply_chain, xbrl_categories


# ---------------------------------------------------------------------------
# LLM-based extraction (Gemini structured output + Pydantic)
# ---------------------------------------------------------------------------

from typing import Literal

from pydantic import BaseModel, Field


class SupplierEntry(BaseModel):
	entity: str = Field(description="Name of the supplier company. Use exact name from the filing.")
	relationship: str = Field(default="", description="Nature of the supply relationship (e.g., 'sole source supplier', 'key component vendor').")
	context: str = Field(default="", description="Brief relevant excerpt (1-3 sentences) from the filing that supports this supplier relationship.")


class CustomerEntry(BaseModel):
	entity: str = Field(description="Name of the customer company. Use exact name from the filing.")
	relationship: str = Field(default="", description="Nature of the customer relationship (e.g., 'major customer', 'accounted for 35% of revenue').")
	context: str = Field(default="", description="Brief relevant excerpt (1-3 sentences) from the filing that supports this customer relationship.")


class SingleSourceEntry(BaseModel):
	component: str = Field(default="", description="Component or material with single-source dependency (e.g., 'DRAM memory chips').")
	supplier: str = Field(description="Name of the sole-source or single-source supplier.")
	context: str = Field(default="", description="Brief relevant excerpt (1-3 sentences) from the filing describing this dependency.")


class GeographicEntry(BaseModel):
	location: str = Field(description="Country or region name (e.g., 'Taiwan', 'South Korea').")
	activity: str = Field(default="", description="Type of activity at this location (e.g., 'manufacturing', 'assembly').")
	context: str = Field(default="", description="Brief relevant excerpt (1-3 sentences) from the filing describing geographic concentration.")


class CapacityConstraintEntry(BaseModel):
	constraint: str = Field(description="Type of capacity constraint (e.g., 'extended lead times', 'production capacity limitation').")
	context: str = Field(default="", description="Brief relevant excerpt (1-3 sentences) from the filing describing the constraint.")


class SupplyChainRiskEntry(BaseModel):
	risk: str = Field(description="Type of supply chain risk (e.g., 'tariff impact', 'raw material shortage').")
	context: str = Field(default="", description="Brief relevant excerpt (1-3 sentences) from the filing describing this risk.")


class RevenueConcentrationEntry(BaseModel):
	entity: str = Field(description="Customer or segment name from filing.")
	revenue_pct: float | None = Field(default=None, description="% of total revenue (e.g., 35.2).")
	revenue_amount: str = Field(default="", description="Amount if disclosed (e.g., '$5.2 billion').")
	context: str = Field(default="", description="1-3 sentences from Notes.")


class GeographicRevenueEntry(BaseModel):
	region: str = Field(description="Country or region (e.g., 'United States', 'China').")
	revenue_pct: float | None = Field(default=None, description="% of total revenue.")
	revenue_amount: str = Field(default="", description="Amount if disclosed.")
	context: str = Field(default="", description="1-3 sentences from Notes.")


class PurchaseObligationEntry(BaseModel):
	counterparty: str = Field(default="", description="Supplier name if disclosed.")
	obligation_type: str = Field(description="Type (e.g., 'inventory commitment', 'capacity reservation').")
	amount: str = Field(default="", description="Dollar amount (e.g., '$2.5 billion').")
	timeframe: str = Field(default="", description="Duration (e.g., 'through fiscal 2027').")
	context: str = Field(default="", description="1-3 sentences from Notes.")


class MarketRiskEntry(BaseModel):
	risk_type: Literal["commodity", "fx", "interest_rate"] = Field(description="Type: 'commodity', 'fx', or 'interest_rate'.")
	exposure: str = Field(default="", description="Specific exposure (e.g., 'gold price', 'EUR/USD').")
	sensitivity: str = Field(default="", description="Quantitative impact if disclosed (e.g., '10% increase = $50M COGS impact').")
	hedging: str = Field(default="", description="Hedging strategy if disclosed.")
	context: str = Field(default="", description="1-3 sentences from filing.")


class InventoryCompositionEntry(BaseModel):
	category: Literal["raw_materials", "work_in_progress", "finished_goods"] = Field(description="Category: 'raw_materials', 'work_in_progress', or 'finished_goods'.")
	amount: str = Field(default="", description="Dollar amount if disclosed (e.g., '$1.2 billion').")
	pct_of_total: float | None = Field(default=None, description="% of total inventory.")
	context: str = Field(default="", description="1-3 sentences from Notes (valuation, aging, obsolescence).")


class SupplyChainExtraction(BaseModel):
	suppliers: list[SupplierEntry] = Field(default_factory=list, description="Companies that supply products, materials, or services to the filing company.")
	customers: list[CustomerEntry] = Field(default_factory=list, description="Companies that purchase products or services from the filing company.")
	single_source_dependencies: list[SingleSourceEntry] = Field(default_factory=list, description="Components with sole-source or single-source supplier dependencies.")
	geographic_concentration: list[GeographicEntry] = Field(default_factory=list, description="Locations where manufacturing, production, or sourcing is concentrated.")
	capacity_constraints: list[CapacityConstraintEntry] = Field(default_factory=list, description="Production capacity limitations, extended lead times, or backlogs.")
	supply_chain_risks: list[SupplyChainRiskEntry] = Field(default_factory=list, description="Supply disruption risks including tariffs, shortages, geopolitical risks.")
	revenue_concentration: list[RevenueConcentrationEntry] = Field(default_factory=list, description="Customer/segment revenue concentration from Notes to Financial Statements (FASB ASC 280).")
	geographic_revenue: list[GeographicRevenueEntry] = Field(default_factory=list, description="Revenue breakdown by country/region from Notes to Financial Statements.")
	purchase_obligations: list[PurchaseObligationEntry] = Field(default_factory=list, description="Purchase commitments, capacity reservations, take-or-pay contracts from Notes.")
	market_risk_disclosures: list[MarketRiskEntry] = Field(default_factory=list, description="Market risk exposures from Item 7A: commodity, FX, and interest rate risks.")
	inventory_composition: list[InventoryCompositionEntry] = Field(default_factory=list, description="Inventory breakdown (raw materials, WIP, finished goods) from Notes to Financial Statements.")


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
1. Use exact company names from the filing — do not paraphrase or invent.
2. For context fields, copy 1-3 relevant sentences verbatim from the filing.
3. If a category has no relevant data, return an empty list.
4. Do NOT extract the filing company itself as its own supplier or customer.
5. Focus on factual supply chain relationships — skip generic boilerplate.
6. De facto single-source: If a supplier is described as the PRIMARY or ONLY provider
   for a critical component category (e.g., leading-edge foundry, specific memory type)
   and NO alternative supplier is mentioned for that same category, classify it as
   single_source_dependencies. Use the component field to specify what is single-sourced.
7. Customer extraction: Look for revenue concentration disclosures, named buyers,
   segment customer mentions, and "accounted for X% of revenue" language.
   Companies buying the filing company's primary products should be extracted
   even if described indirectly (e.g., "cloud service providers" when context
   makes the identity clear).
8. Relationship specificity: Use precise relationship descriptions such as
   "sole foundry for leading-edge GPUs", "memory supplier (HBM)",
   "contract manufacturer for server products", "anchor customer >10% revenue".
   Avoid vague descriptions like "supplier" or "customer".
9. Only infer relationships where the filing text provides contextual support.
   Do not fabricate connections or guess identities not supported by the text.
10. Revenue concentration: From Notes to Financial Statements, extract
    customers/segments with specific % of revenue. Include exact percentage
    as revenue_pct (e.g., 35.2 for "35.2%"). Each customer gets its own entry.
11. Geographic revenue: From Notes, extract revenue by country/region with
    exact percentages. Use standardized country names ("United States" not "domestic").
12. Purchase obligations: From Notes (Commitments and Contingencies), extract
    purchase commitments, capacity reservations, take-or-pay contracts.
    Include dollar amounts and timeframes when disclosed.
13. Market risk disclosures: From Item 7A, extract commodity price exposures
    (specific commodities named), foreign exchange exposures (currencies and
    country pairs), and interest rate risks. Classify risk_type as "commodity",
    "fx", or "interest_rate". Include quantitative sensitivity data when
    disclosed (e.g., "10% increase in gold prices would impact revenue by
    $X million").
14. Inventory composition: From Notes (Inventory), extract raw materials,
    work-in-progress, and finished goods amounts and percentages. Classify
    category as "raw_materials", "work_in_progress", or "finished_goods".
    Note any inventory obsolescence, write-downs, or valuation adjustments.

Filing company: {company_name}

Extract all supply chain entities from this SEC filing text:

{filing_text}
"""


def _extract_supply_chain_llm(cleaned_text, company_name="", max_chars=None):
	"""Extract supply chain data using Gemini structured output + Pydantic.

	Returns:
		tuple(dict, int, int) or None: (supply_chain, total_matches, unique_entities)
		Returns None on failure.
	"""
	from google import genai
	from dotenv import load_dotenv

	env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
		os.path.dirname(__file__)))), ".env")
	load_dotenv(env_path)
	api_key = os.environ.get("GOOGLE_API_KEY")
	model_id = os.environ.get("GOOGLE_MODEL", "gemini-2.5-flash")
	thinking_level = os.environ.get("GOOGLE_THINKING_LEVEL", "")

	if not api_key:
		return None

	text = cleaned_text
	if max_chars and len(text) > max_chars:
		text = text[:max_chars]

	prompt = _LLM_PROMPT.format(
		company_name=company_name or "Unknown",
		filing_text=text,
	)

	# Build config with optional thinking level
	from google.genai import types

	gen_config = {
		"response_mime_type": "application/json",
		"response_json_schema": SupplyChainExtraction.model_json_schema(),
		"temperature": 0.1,
	}
	if thinking_level and thinking_level.lower() in ("low", "medium", "high", "minimal"):
		gen_config["thinking_config"] = types.ThinkingConfig(
			thinking_level=thinking_level.lower()
		)

	# Retry with backoff
	client = genai.Client(api_key=api_key)
	retries = 3
	extraction = None

	for attempt in range(1, retries + 1):
		try:
			response = client.models.generate_content(
				model=model_id,
				contents=prompt,
				config=gen_config,
			)
			extraction = SupplyChainExtraction.model_validate_json(response.text)
			break
		except Exception as e:
			print(f"[supply_chain] LLM attempt {attempt}/{retries} failed: {e}",
				  file=sys.stderr)
			if attempt < retries:
				time.sleep(2 ** attempt)
				continue
			return None

	# Post-process: convert to dict and add metadata
	supply_chain = {
		"suppliers": [], "customers": [],
		"single_source_dependencies": [], "geographic_concentration": [],
		"capacity_constraints": [], "supply_chain_risks": [],
		"revenue_concentration": [], "geographic_revenue": [],
		"purchase_obligations": [],
		"market_risk_disclosures": [], "inventory_composition": [],
	}
	entities = set()
	_META = {"source_section": "llm_extraction", "confidence": "high"}

	for e in extraction.suppliers:
		entities.add(e.entity)
		supply_chain["suppliers"].append({**e.model_dump(), **_META})
	for e in extraction.customers:
		entities.add(e.entity)
		supply_chain["customers"].append({**e.model_dump(), **_META})
	for e in extraction.single_source_dependencies:
		entities.add(e.supplier)
		supply_chain["single_source_dependencies"].append({**e.model_dump(), **_META})
	for e in extraction.geographic_concentration:
		supply_chain["geographic_concentration"].append({**e.model_dump(), **_META})
	for e in extraction.capacity_constraints:
		supply_chain["capacity_constraints"].append({**e.model_dump(), **_META})
	for e in extraction.supply_chain_risks:
		supply_chain["supply_chain_risks"].append({**e.model_dump(), **_META})
	for e in extraction.revenue_concentration:
		if e.entity:
			entities.add(e.entity)
		supply_chain["revenue_concentration"].append({**e.model_dump(), **_META})
	for e in extraction.geographic_revenue:
		supply_chain["geographic_revenue"].append({**e.model_dump(), **_META})
	for e in extraction.purchase_obligations:
		if e.counterparty:
			entities.add(e.counterparty)
		supply_chain["purchase_obligations"].append({**e.model_dump(), **_META})
	for e in extraction.market_risk_disclosures:
		supply_chain["market_risk_disclosures"].append({**e.model_dump(), **_META})
	for e in extraction.inventory_composition:
		supply_chain["inventory_composition"].append({**e.model_dump(), **_META})

	total_matches = sum(len(v) for v in supply_chain.values())
	return supply_chain, total_matches, len(entities)


# ---------------------------------------------------------------------------
# HTML utility (used by cmd_events only)
# ---------------------------------------------------------------------------

def _strip_html_tags(text):
	"""Remove HTML tags and normalize whitespace."""
	text = re.sub(r"<[^>]+>", " ", text)
	text = re.sub(r"&nbsp;", " ", text)
	text = re.sub(r"&amp;", "&", text)
	text = re.sub(r"&lt;", "<", text)
	text = re.sub(r"&gt;", ">", text)
	text = re.sub(r"&#\d+;", " ", text)
	text = re.sub(r"\s+", " ", text).strip()
	return text


# ---------------------------------------------------------------------------
# 8-K event classification
# ---------------------------------------------------------------------------

_8K_ITEM_TYPES = {
	"1.01": "Material Agreement",
	"1.02": "Termination of Material Agreement",
	"2.01": "Completion of Acquisition/Disposition",
	"2.05": "Costs of Exit/Disposal",
	"2.06": "Material Impairments",
	"7.01": "Regulation FD Disclosure",
	"8.01": "Other Events",
}

_8K_SC_PATTERNS = [
	r"(?:supply|supplier|vendor|procurement)",
	r"(?:material\s+agreement|definitive\s+agreement|purchase\s+agreement)",
	r"(?:acquisition|merger|joint\s+venture|partnership)",
	r"(?:manufacturing|production|capacity|facility)",
	r"(?:tariff|trade|export|import|sanction)",
	r"(?:shortage|disruption|force\s+majeure|allocation)",
	r"(?:contract|offtake|supply\s+agreement|purchase\s+order)",
]


# ---------------------------------------------------------------------------
# Data coverage assessment and geography labeling
# ---------------------------------------------------------------------------

_BOILERPLATE_PATTERNS = [
	re.compile(r"no single customer accounted for", re.IGNORECASE),
	re.compile(r"we are not dependent on any single supplier", re.IGNORECASE),
	re.compile(r"no single supplier is material", re.IGNORECASE),
	re.compile(r"we do not believe.{0,30}dependent on any single", re.IGNORECASE),
	re.compile(r"no (?:material|significant) concentration", re.IGNORECASE),
]


def _assess_data_coverage(supply_chain):
	"""Classify data coverage for each supply chain category.

	Returns dict mapping category -> coverage status:
	- "extracted": 1+ entries exist with actual entity/data
	- "not_disclosed": empty but SEC boilerplate detected indicating deliberate non-disclosure
	- "insufficient_context": empty and no boilerplate detected
	"""
	categories = [
		"suppliers", "customers", "single_source_dependencies",
		"geographic_concentration", "capacity_constraints",
		"supply_chain_risks", "revenue_concentration",
		"geographic_revenue", "purchase_obligations",
		"market_risk_disclosures", "inventory_composition",
	]

	# Collect all context text for boilerplate detection
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


def _label_supplier_geography(supply_chain):
	"""Add geography labels to suppliers and single_source_dependencies.

	Labels each entry with supplier_geography:
	- "Western": US, Canada, UK, EU, Australia, Japan
	- "International": Taiwan, China, HK, South Korea, etc.
	- "Unknown": location not determinable

	Modifies entries in-place.
	"""
	for cat_key in ("suppliers", "single_source_dependencies"):
		for entry in (supply_chain.get(cat_key) or []):
			if not isinstance(entry, dict):
				continue
			# Try to determine geography from context, entity, and relationship text
			text = " ".join([
				entry.get("context", ""),
				entry.get("entity", entry.get("supplier", "")),
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


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@safe_run
def cmd_supply_chain_extract(args):
	"""Extract supply chain structure from 10-K, 10-Q, or 20-F filing."""
	symbol = args.symbol.upper()
	form = args.form.upper() if args.form else "10-K"
	max_chars = args.max_chars

	# Step 1: Get filing via edgartools
	try:
		filing, metadata, company_name = _get_filing(symbol, form)
	except Exception as e:
		output_json({
			"data": None,
			"metadata": {"symbol": symbol, "form": form,
			             "error": f"Filing retrieval failed: {str(e)}"},
		})
		return

	# Step 2: Convert to markdown
	try:
		markdown_text = _get_filing_markdown(filing, max_chars)
	except Exception as e:
		output_json({
			"data": None,
			"metadata": {"symbol": symbol, "company_name": company_name,
			             "form": metadata["form"],
			             "error": f"Markdown conversion failed: {str(e)}"},
		})
		return

	# Step 3: LLM extraction
	llm_result = _extract_supply_chain_llm(
		markdown_text, company_name=company_name, max_chars=None,
	)
	if llm_result is None:
		output_json({
			"data": None,
			"metadata": {"symbol": symbol, "company_name": company_name,
			             "form": metadata["form"],
			             "error": "GOOGLE_API_KEY not set. Use WebSearch to find supply chain information instead."},
		})
		return

	supply_chain, total_matches, unique_entities = llm_result

	# Step 4: XBRL supplementation
	xbrl_data = _extract_xbrl_supplements(filing)
	supply_chain, xbrl_categories = _merge_xbrl_with_llm(supply_chain, xbrl_data)

	# Step 4.5: Data coverage assessment and geography labeling
	_label_supplier_geography(supply_chain)
	data_coverage = _assess_data_coverage(supply_chain)

	# Recount after merge
	total_matches = sum(len(v) for v in supply_chain.values())

	# Step 5: Output
	output_json({
		"data": {
			"filing": metadata,
			"supply_chain": supply_chain,
			"extraction_stats": {
				"total_matches": total_matches,
				"unique_entities": unique_entities,
				"mode": "llm",
				"xbrl_categories": xbrl_categories,
				"xbrl_supplemented": bool(xbrl_categories),
			},
			"data_coverage": data_coverage,
		},
		"metadata": {
			"symbol": symbol,
			"company_name": company_name,
			"form": metadata["form"],
		},
	})


@safe_run
def cmd_events(args):
	"""Extract supply-chain-related events from recent 8-K filings."""
	symbol = args.symbol.upper()
	limit = args.limit
	days = args.days

	cik = get_cik_from_symbol(symbol)
	data = get_company_info(cik)
	company_name = data.get("name", "")

	filings = data.get("filings", {}).get("recent", {})
	if not filings:
		output_json({
			"data": [],
			"metadata": {"symbol": symbol, "cik": cik, "company_name": company_name,
						"filings_checked": 0, "supply_chain_events_found": 0},
		})
		return

	# Find 8-K filings within the date window
	from datetime import datetime, timedelta
	cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

	forms = filings.get("form", [])
	filing_dates = filings.get("filingDate", [])
	accession_numbers = filings.get("accessionNumber", [])
	primary_documents = filings.get("primaryDocument", [])

	eight_k_filings = []
	for i in range(len(forms)):
		if forms[i] == "8-K" and i < len(filing_dates):
			if filing_dates[i] >= cutoff_date:
				accession = accession_numbers[i] if i < len(accession_numbers) else ""
				primary_doc = primary_documents[i] if i < len(primary_documents) else ""
				cik_int = int(cik)
				filing_url = (
					f"https://www.sec.gov/Archives/edgar/data/{cik_int}/"
					f"{accession.replace('-', '')}/{primary_doc}"
				)
				eight_k_filings.append({
					"filing_date": filing_dates[i],
					"accession_number": accession,
					"filing_url": filing_url,
				})
				if len(eight_k_filings) >= limit:
					break

	# Check each 8-K for supply chain relevance
	sc_events = []
	for filing in eight_k_filings:
		time.sleep(0.15)  # Rate limiting
		try:
			resp = requests.get(
				filing["filing_url"], headers=SEC_HEADERS, timeout=30,
			)
			resp.raise_for_status()
			content = _strip_html_tags(resp.text)

			# Check for supply chain relevance
			relevance_matches = []
			for pattern in _8K_SC_PATTERNS:
				if re.search(pattern, content, re.IGNORECASE):
					relevance_matches.append(pattern.replace(r"(?:", "").replace(")", "").replace("|", "/"))

			if relevance_matches:
				# Try to identify 8-K item type
				event_type = "Other"
				for item_num, item_name in _8K_ITEM_TYPES.items():
					if re.search(rf"Item\s+{re.escape(item_num)}", content, re.IGNORECASE):
						event_type = f"{item_num}: {item_name}"
						break

				# Extract a brief context snippet
				for pattern in _8K_SC_PATTERNS:
					m = re.search(pattern, content, re.IGNORECASE)
					if m:
						start = max(0, m.start() - 200)
						end = min(len(content), m.end() + 200)
						context = content[start:end].strip()[:400]
						break
				else:
					context = content[:400]

				confidence = "high" if len(relevance_matches) >= 3 else "medium" if len(relevance_matches) >= 2 else "low"

				sc_events.append({
					"filing_date": filing["filing_date"],
					"accession_number": filing["accession_number"],
					"filing_url": filing["filing_url"],
					"event_type": event_type,
					"supply_chain_relevance": ", ".join(relevance_matches[:5]),
					"context": context,
					"confidence": confidence,
				})

		except Exception:
			continue  # Skip failed filings, check remaining

	output_json({
		"data": sc_events,
		"metadata": {
			"symbol": symbol,
			"cik": cik,
			"company_name": company_name,
			"filings_checked": len(eight_k_filings),
			"supply_chain_events_found": len(sc_events),
		},
	})


# ---------------------------------------------------------------------------
# Standalone CLI entry point
# ---------------------------------------------------------------------------

def main():
	"""CLI dispatcher for direct script execution."""
	parser = argparse.ArgumentParser(description="SEC supply chain intelligence extraction")
	sub = parser.add_subparsers(dest="command", required=True)

	# supply-chain
	sp = sub.add_parser("supply-chain", help="Extract supply chain from 10-K/10-Q/20-F")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--form", default="10-K", help="Form type (10-K, 10-Q, or 20-F)")
	sp.add_argument("--max-chars", type=int, default=2000000, help="Max chars for filing text")
	sp.set_defaults(func=cmd_supply_chain_extract)

	# events
	sp = sub.add_parser("events", help="Extract supply chain events from 8-K filings")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--limit", type=int, default=10, help="Max 8-K filings to check")
	sp.add_argument("--days", type=int, default=180, help="Lookback window in days")
	sp.set_defaults(func=cmd_events)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
