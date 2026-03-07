#!/usr/bin/env python3
"""SEC supply chain intelligence extraction from 10-K/10-Q/20-F and 8-K filings.

Extracts supply chain relationships, single-source dependencies, geographic
concentration, capacity constraints, revenue concentration, geographic revenue
breakdown, purchase obligations, market risk disclosures (Item 7A), and
inventory composition from SEC filings. Uses direct HTTP calls to SEC EDGAR
(no disk I/O). Multi-stage regex + heuristic parsing with graceful degradation
on section extraction failure. LLM mode additionally extracts Item 7A (market
risk), Item 8 Notes (revenue/segment, commitments, concentration of risk,
inventory) for quantitative supply chain data. Supports 20-F filings for
foreign private issuers (TSMC, ASML, etc.) with auto-fallback from 10-K.

Commands:
	supply-chain: Extract supply chain structure from latest 10-K, 10-Q, or 20-F
	events: Extract supply-chain-related events from recent 8-K filings

Args:
	For supply-chain:
		symbol (str): Stock ticker symbol (e.g., "AAPL", "NVDA", "TSM")
		--form (str): Filing form type, "10-K", "10-Q", or "20-F" (default: "10-K", auto-fallback to 20-F)
		--max-chars (int): Max characters per section to process (default: 500000)
		--mode (str): Extraction mode - "llm" (default, Gemini structured output) or "regex" (free, no API key)

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
					"confidence": str}],
				"customers": [{"entity": str, "relationship": str,
					"context": str, "source_section": str,
					"confidence": str}],
				"single_source_dependencies": [{"component": str,
					"supplier": str, "context": str,
					"source_section": str, "confidence": str}],
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
			"sections_extracted": {
				"item_1_business": bool,
				"item_1a_risk_factors": bool,
				"item_7_mda": bool,
				"item_7a_market_risk": bool,
				"item_8_notes": bool
			},
			"extraction_stats": {
				"total_matches": int,
				"unique_entities": int,
				"sections_found": int,
				"sections_attempted": int
			}
		},
		"metadata": {
			"symbol": str,
			"cik": str,
			"company_name": str,
			"form": str
		}
	}

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
	>>> python supply_chain.py supply-chain NVDA --form 10-Q
	>>> python supply_chain.py events NVDA --limit 5 --days 180

Use Cases:
	- Pre-extract supply chain structure for L3 bottleneck analysis
	- Identify single-source dependencies from legal disclosures
	- Detect geographic concentration risk from official filings
	- Monitor 8-K events for supply chain disruptions or material agreements

Notes:
	- No API key required (public SEC EDGAR access)
	- Rate limiting: 0.15s delay between requests
	- Section extraction uses multi-stage fallback (regex → anchor → keyword → skip)
	- Graceful degradation: returns partial data if some sections fail
	- Filing HTML can be 5-10MB; max-chars parameter limits per-section processing
	- Foreign filers (20-F) use different section numbers; currently graceful degradation
	- LLM mode uses Gemini structured output for high-quality extraction
	- LLM mode requires GOOGLE_API_KEY in .env file
	- LLM mode falls back to regex on failure or missing API key
	- Gemini 1M context handles entire 10-K without section splitting

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
# Keyword patterns for supply chain extraction
# ---------------------------------------------------------------------------

_SUPPLIER_PATTERNS = [
	r"(?:sole|single|primary|key|principal|critical|major)\s+(?:source|supplier|vendor|provider)",
	r"(?:we|the\s+company)\s+(?:rely|relies|depend|depends)\s+on\s+(?:a\s+)?(?:single|sole|limited\s+number\s+of)",
	r"(?:supplied|sourced|purchased|procured)\s+(?:exclusively|primarily|solely)\s+(?:from|by)",
	r"(?:our|the)\s+(?:primary|principal|key)\s+(?:supplier|vendor|source)",
]

_CUSTOMER_PATTERNS = [
	r"(?:largest|major|significant|principal)\s+customer",
	r"accounted\s+for\s+(?:approximately\s+)?\d+%",
	r"(?:our|the)\s+(?:largest|top)\s+\d+\s+customers?\s+(?:accounted|represented|comprised)",
	r"(?:significant|substantial)\s+(?:portion|percentage)\s+of\s+(?:our|total)\s+(?:revenue|sales|net\s+sales)",
]

_SINGLE_SOURCE_PATTERNS = [
	r"sole\s+source",
	r"single\s+source",
	r"no\s+(?:alternative|other)\s+(?:source|supplier|vendor)",
	r"only\s+(?:supplier|source|provider)",
	r"(?:cannot|could\s+not)\s+(?:easily|readily)\s+(?:be\s+)?(?:replaced|substituted)",
	r"limited\s+(?:number|availability)\s+of\s+(?:alternative\s+)?(?:suppliers?|sources?|vendors?)",
]

_GEOGRAPHIC_PATTERNS = [
	r"(?:manufactured|produced|fabricated|assembled|sourced|mined|processed)\s+(?:primarily\s+)?(?:in|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
	r"(?:operations?|facilit(?:y|ies)|plant|factory|factories)\s+(?:in|located\s+in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
	r"(?:China|Taiwan|Japan|Korea|South\s+Korea|Germany|Israel|India|Mexico|Vietnam|Malaysia|Singapore|Thailand|Philippines|Indonesia)(?:\s+and\s+(?:China|Taiwan|Japan|Korea|South\s+Korea|Germany|Israel|India|Mexico|Vietnam|Malaysia|Singapore|Thailand|Philippines|Indonesia))*",
	r"(?:geographically|regionally)\s+concentrated",
]

_CAPACITY_PATTERNS = [
	r"(?:capacity|production)\s+constraint",
	r"lead\s+time(?:s)?\s+of\s+(?:approximately\s+)?\d+",
	r"(?:backlog|order\s+backlog)\s+(?:of|was|totaled|increased)",
	r"(?:limited|constrained|insufficient)\s+(?:manufacturing\s+)?(?:capacity|supply|production)",
	r"(?:expansion|capacity\s+expansion)\s+(?:is\s+)?expected\s+to\s+(?:be\s+)?(?:completed|operational)",
	r"(?:long|extended)\s+lead\s+times?",
]

_RISK_PATTERNS = [
	r"(?:supply\s+chain|supply)\s+(?:disruption|interruption|shortage|risk|constraint)",
	r"(?:tariff|trade\s+restriction|export\s+control|sanction|embargo)",
	r"(?:raw\s+material|critical\s+material|key\s+material)\s+(?:shortage|availability|price\s+(?:increase|volatility))",
	r"(?:natural\s+disaster|pandemic|force\s+majeure|geopolitical)",
	r"(?:could|may|might)\s+(?:significantly\s+)?(?:disrupt|interrupt|delay|impair|adversely\s+affect)\s+(?:our\s+)?(?:supply|operations|production|manufacturing)",
]


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
	# Item 8 Notes (LLM mode only, regex returns empty)
	revenue_concentration: list[RevenueConcentrationEntry] = Field(default_factory=list, description="Customer/segment revenue concentration from Notes to Financial Statements (FASB ASC 280).")
	geographic_revenue: list[GeographicRevenueEntry] = Field(default_factory=list, description="Revenue breakdown by country/region from Notes to Financial Statements.")
	purchase_obligations: list[PurchaseObligationEntry] = Field(default_factory=list, description="Purchase commitments, capacity reservations, take-or-pay contracts from Notes.")
	# Item 7A + Notes: Inventory (LLM mode only, regex returns empty)
	market_risk_disclosures: list[MarketRiskEntry] = Field(default_factory=list, description="Market risk exposures from Item 7A: commodity, FX, and interest rate risks.")
	inventory_composition: list[InventoryCompositionEntry] = Field(default_factory=list, description="Inventory breakdown (raw materials, WIP, finished goods) from Notes to Financial Statements.")


_LLM_PROMPT = """\
You are a financial analyst extracting supply chain intelligence from SEC filings.
Extract entities and relationships exactly as stated in the filing text.

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

Section tags in the text: [ITEM_1_BUSINESS] = Item 1, [ITEM_1A_RISK_FACTORS] = Item 1A,
[ITEM_7_MDA] = Item 7/MD&A, [ITEM_7A_MARKET_RISK] = Item 7A (market risk),
[ITEM_8_NOTES_*] = Notes to Financial Statements (revenue, commitments, concentration, inventory).

Filing company: {company_name}

Extract all supply chain entities from this SEC filing text:

{filing_text}
"""


def _extract_supply_chain_llm(cleaned_text, company_name="", max_chars=None):
	"""Extract supply chain data using Gemini structured output + Pydantic.

	Returns:
		tuple(dict, int, int) or None: (supply_chain, total_matches, unique_entities)
		Returns None on failure (caller falls back to regex).
	"""
	from google import genai
	from dotenv import load_dotenv

	env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
		os.path.dirname(__file__)))), ".env")
	load_dotenv(env_path)
	api_key = os.environ.get("GOOGLE_API_KEY")
	model_id = os.environ.get("GOOGLE_MODEL", "gemini-2.5-flash")

	if not api_key:
		return None

	text = cleaned_text
	if max_chars and len(text) > max_chars:
		text = text[:max_chars]

	prompt = _LLM_PROMPT.format(
		company_name=company_name or "Unknown",
		filing_text=text,
	)

	# Retry with backoff — regex is the absolute last resort
	client = genai.Client(api_key=api_key)
	retries = 3
	extraction = None

	for attempt in range(1, retries + 1):
		try:
			response = client.models.generate_content(
				model=model_id,
				contents=prompt,
				config={
					"response_mime_type": "application/json",
					"response_json_schema": SupplyChainExtraction.model_json_schema(),
					"temperature": 0.1,
				},
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
# Section extraction from 10-K/10-Q HTML
# ---------------------------------------------------------------------------

def _clean_html(text):
	"""Remove HTML tags and normalize whitespace."""
	text = re.sub(r"<[^>]+>", " ", text)
	text = re.sub(r"&nbsp;", " ", text)
	text = re.sub(r"&amp;", "&", text)
	text = re.sub(r"&lt;", "<", text)
	text = re.sub(r"&gt;", ">", text)
	text = re.sub(r"&#\d+;", " ", text)
	text = re.sub(r"\s+", " ", text).strip()
	return text


def _prepare_content(raw_html):
	"""Pre-process HTML content: normalize entities, strip tags, normalize whitespace.

	Returns cleaned plain text suitable for section boundary detection and
	keyword matching. Must be called ONCE before section extraction.
	"""
	text = raw_html
	# Normalize HTML entities
	text = text.replace("&#160;", " ")
	text = text.replace("&nbsp;", " ")
	text = text.replace("\xa0", " ")
	text = text.replace("&#8217;", "'")
	text = text.replace("&#8216;", "'")
	text = text.replace("&#8220;", '"')
	text = text.replace("&#8221;", '"')
	text = text.replace("&amp;", "&")
	text = text.replace("&lt;", "<")
	text = text.replace("&gt;", ">")
	text = re.sub(r"&#\d+;", " ", text)
	# Strip HTML tags
	text = re.sub(r"<[^>]+>", " ", text)
	# ── XBRL artifact cleaning ──
	# 1. DEI (Document and Entity Information) block removal
	text = re.sub(
		r"(?:Entity\s+(?:Registrant\s+Name|Central\s+Index\s+Key|"
		r"File\s+Number|Tax\s+Identification|"
		r"Incorporation,?\s+State|Address.*?(?:Zip|Code)|"
		r"Current\s+Reporting\s+Status|Filer\s+Category|"
		r"(?:Public\s+)?Float|Common\s+Stock.*?Outstanding|"
		r"Well.?known\s+Seasoned|Shell\s+Company|"
		r"Voluntary\s+Filer|Emerging\s+Growth|"
		r"Interactive\s+Data|Smaller\s+Reporting)\s*"
		r"[^\n]{0,200})",
		" ", text, flags=re.IGNORECASE,
	)
	# 2. Amendment/document metadata removal
	text = re.sub(
		r"(?:Amendment\s+Flag|Document\s+(?:Period|Type|Fiscal\s+"
		r"(?:Year|Period))|Current\s+Fiscal\s+Year\s+End)\s*"
		r"[^\n]{0,100}",
		" ", text, flags=re.IGNORECASE,
	)
	# 3. Orphaned CIK / long numeric sequences (10+ digits)
	text = re.sub(r"(?<!\$)(?<!\d[,.])\b\d{10,}\b", " ", text)
	# 4. XBRL namespace prefix residues
	text = re.sub(
		r"\b(?:dei|us-gaap|srt|country|stpr|exch):[A-Za-z]+\b",
		" ", text,
	)
	# Normalize whitespace
	text = re.sub(r"\s+", " ", text)
	return text


def _extract_section(content, start_patterns, end_patterns, max_chars):
	"""Multi-stage section extraction with fallback.

	Operates on pre-cleaned plain text (HTML already stripped).
	Tries all regex matches per pattern, skipping ToC entries (< 500 chars).
	"""
	for pattern in start_patterns:
		for match in re.finditer(pattern, content, re.IGNORECASE):
			start = match.start()
			# Search for end marker starting just past the matched header text
			search_offset = start + len(match.group(0))
			best_end = None
			for end_pattern in end_patterns:
				end_match = re.search(end_pattern, content[search_offset:], re.IGNORECASE)
				if end_match:
					candidate = search_offset + end_match.start()
					if best_end is None or candidate < best_end:
						best_end = candidate
			if best_end is not None:
				section = content[start:best_end]
				# Skip ToC entries — real sections are > 500 chars
				if len(section) < 500:
					continue
				if len(section) > max_chars:
					section = section[:max_chars]
				return section.strip()

			# No end found — take max_chars from start (likely last section)
			section = content[start:start + max_chars]
			if len(section.strip()) > 500:
				return section.strip()

	return None


def _extract_item8_notes(raw_html, max_chars, form="10-K"):
	"""Extract targeted Notes from Financial Statements (Item 8 for 10-K, Item 18/19 for 20-F).

	Extracts specific Note sections relevant to supply chain quantitative
	data: revenue/segment info, commitments/obligations, concentration
	of risk, and inventory composition. Returns dict: note_name -> text.
	Empty dict on failure.
	"""
	content = _prepare_content(raw_html)

	# Step 1: Financial Statements 시작 찾기 (form-dependent)
	if form == "20-F":
		item8_patterns = [
			r"Item\s+18\.?\s*(?:—|–|-)?\s*Financial\s+Statements",
			r"Item\s+19\.?\s*(?:—|–|-)?\s*(?:Exhibits|Financial\s+Statements)",
		]
	else:
		item8_patterns = [
			r"Item\s+8\.?\s*(?:—|–|-)?\s*Financial\s+Statements",
			r"Item\s+8\.?\s*(?:—|–|-)?\s*Consolidated\s+Financial",
		]
	item8_start = None
	for pat in item8_patterns:
		for m in re.finditer(pat, content, re.IGNORECASE):
			if len(content[m.start():m.start() + 1000]) > 500:  # Skip ToC
				item8_start = m.start()
				break
		if item8_start:
			break
	if item8_start is None:
		return {}

	# Step 2: "Notes to Financial Statements" 시작 찾기
	search_region = content[item8_start:item8_start + 500000]
	notes_match = re.search(
		r"Notes?\s+to\s+(?:the\s+)?(?:Consolidated\s+)?Financial\s+Statements",
		search_region, re.IGNORECASE,
	)
	if not notes_match:
		return {}
	notes_start = item8_start + notes_match.start()

	# Step 3: 끝 범위 결정 (form-dependent)
	if form == "20-F":
		end_match = re.search(r"Item\s+19\.?\s|SIGNATURES", content[notes_start:], re.IGNORECASE)
	else:
		end_match = re.search(r"Item\s+9\.?\s", content[notes_start:], re.IGNORECASE)
	notes_end = notes_start + end_match.start() if end_match else min(notes_start + max_chars * 3, len(content))
	notes_text = content[notes_start:notes_end]

	# Step 4: 타겟 Note 추출
	note_patterns = {
		"revenue_segment": [
			r"(?:Note\s+\d+\s*[-—–:.]?\s*)?(?:Revenue|Segment\s+Information|Operating\s+Segments?|Disaggregation\s+of\s+Revenue)",
		],
		"commitments": [
			r"(?:Note\s+\d+\s*[-—–:.]?\s*)?(?:Commitments?\s+and\s+Contingenc|Purchase\s+Obligations?|Purchase\s+Commitments?)",
		],
		"concentration": [
			r"(?:Note\s+\d+\s*[-—–:.]?\s*)?(?:Concentration\s+of\s+(?:Credit\s+)?Risk|Significant\s+Customers?|Customer\s+Concentration)",
		],
		"inventory": [
			r"(?:Note\s+\d+\s*[-—–:.]?\s*)?(?:Inventor(?:y|ies)\b)",
		],
	}
	result = {}
	for name, patterns in note_patterns.items():
		section = _extract_section(notes_text, patterns,
			[r"Note\s+\d+\s*[-—–:.]"], max_chars)
		if section:
			result[name] = section
	return result


def _extract_10k_sections(raw_html, max_chars):
	"""Extract Item 1, Item 1A, and Item 7 from a 10-K filing."""
	# Pre-clean HTML once — all patterns work on plain text
	content = _prepare_content(raw_html)
	sections = {}

	# Item 1: Business (patterns work on cleaned text, no HTML tags)
	sections["item_1_business"] = _extract_section(
		content,
		start_patterns=[
			r"Item\s+1\.?\s*(?:—|–|-)?\s*Business",
			r"PART\s+I\s+Item\s+1",
		],
		end_patterns=[
			r"Item\s+1A\.?\s",
			r"Item\s+1B\.?\s",
			r"Item\s+2\.?\s",
		],
		max_chars=max_chars,
	)

	# Item 1A: Risk Factors
	sections["item_1a_risk_factors"] = _extract_section(
		content,
		start_patterns=[
			r"Item\s+1A\.?\s*(?:—|–|-)?\s*Risk\s+Factors",
		],
		end_patterns=[
			r"Item\s+1B\.?\s",
			r"Item\s+2\.?\s",
		],
		max_chars=max_chars,
	)

	# Item 7: MD&A
	sections["item_7_mda"] = _extract_section(
		content,
		start_patterns=[
			r"Item\s+7\.?\s*(?:—|–|-)?\s*Management'?s?\s+Discussion",
		],
		end_patterns=[
			r"Item\s+7A\.?\s",
			r"Item\s+8\.?\s",
		],
		max_chars=max_chars,
	)

	# Item 7A: Quantitative and Qualitative Disclosures About Market Risk
	sections["item_7a_market_risk"] = _extract_section(
		content,
		[r"Item\s+7A\.?\s*(?:—|–|-)?\s*Quantitative\s+and\s+Qualitative",
		 r"Item\s+7A\.?\s*(?:—|–|-)?\s*Market\s+Risk"],
		[r"Item\s+8\.?\s", r"Item\s+9\.?\s"],
		max_chars,
	)

	return sections


def _extract_10q_sections(raw_html, max_chars):
	"""Extract relevant sections from a 10-Q filing."""
	content = _prepare_content(raw_html)
	sections = {}

	# Item 1A: Risk Factors (optional in 10-Q, but often included)
	sections["item_1a_risk_factors"] = _extract_section(
		content,
		start_patterns=[
			r"Item\s+1A\.?\s*(?:—|–|-)?\s*Risk\s+Factors",
		],
		end_patterns=[
			r"Item\s+2\.?\s",
			r"Item\s+5\.?\s",
		],
		max_chars=max_chars,
	)

	# Item 2: MD&A (10-Q version)
	sections["item_7_mda"] = _extract_section(
		content,
		start_patterns=[
			r"Item\s+2\.?\s*(?:—|–|-)?\s*Management'?s?\s+Discussion",
		],
		end_patterns=[
			r"Item\s+3\.?\s",
			r"Item\s+4\.?\s",
		],
		max_chars=max_chars,
	)

	# No Item 1 Business in 10-Q typically
	sections["item_1_business"] = None

	return sections


def _extract_20f_sections(raw_html, max_chars):
	"""Extract supply chain sections from 20-F (Foreign Private Issuer).

	Maps to 10-K equivalent keys for downstream compatibility.
	20-F structures vary widely (TSM, ASML, Samsung). Patterns ordered
	from most specific to broadest fallback.
	"""
	content = _prepare_content(raw_html)
	sections = {}

	# Item 4/4B (Business Overview) → item_1_business
	sections["item_1_business"] = _extract_section(content,
		[r"Item\s+4\.?\s*(?:B\.?)?\s*(?:—|–|-)?\s*(?:Information\s+on\s+the\s+Company|Business\s+Overview)",
		 r"Item\s+4\.?\s*(?:—|–|-)?\s*Information\s+on\s+the\s+Company",
		 r"Item\s+4\b[^0-9]"],
		[r"Item\s+4A\.?\s", r"Item\s+4C\.?\s", r"Item\s+5\.?\s"], max_chars)

	# Item 3D (Risk Factors) → item_1a_risk_factors
	# TSM uses "Item 3. Key Information ... D. Risk Factors" with text between 3 and D
	sections["item_1a_risk_factors"] = _extract_section(content,
		[r"Item\s+3\.?\s*D\.?\s*(?:—|–|-)?\s*Risk\s+Factors",
		 r"Item\s+3D\.?\s*(?:—|–|-)?\s*Risk\s+Factors",
		 r"D\.\s*Risk\s+Factors"],
		[r"Item\s+4\.?\s", r"Item\s+4A\.?\s"], max_chars)

	# Item 5 (Operating and Financial Review) → item_7_mda
	sections["item_7_mda"] = _extract_section(content,
		[r"Item\s+5\.?\s*(?:—|–|-)?\s*Operating\s+and\s+Financial\s+Review",
		 r"Item\s+5\b[^0-9]"],
		[r"Item\s+6\.?\s", r"Item\s+7\.?\s"], max_chars)

	# Item 11 (Market Risk) → item_7a_market_risk
	sections["item_7a_market_risk"] = _extract_section(content,
		[r"Item\s+11\.?\s*(?:—|–|-)?\s*Quantitative\s+and\s+Qualitative",
		 r"Item\s+11\b[^0-9]"],
		[r"Item\s+12\.?\s"], max_chars)

	return sections


# ---------------------------------------------------------------------------
# Keyword matching and context extraction
# ---------------------------------------------------------------------------

def _extract_matches(text, patterns, source_section, context_window=350):
	"""Find pattern matches and extract surrounding context."""
	matches = []
	seen_contexts = set()

	for pattern in patterns:
		for m in re.finditer(pattern, text, re.IGNORECASE):
			start = max(0, m.start() - context_window)
			end = min(len(text), m.end() + context_window)
			context = text[start:end].strip()

			# Dedup by checking overlap
			context_key = context[:100]
			if context_key in seen_contexts:
				continue
			seen_contexts.add(context_key)

			# Determine confidence
			has_number = bool(re.search(r"\d+%|\$\d+|\d+\s+(?:million|billion)", context, re.IGNORECASE))
			has_entity = bool(re.search(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", context))

			if has_number and has_entity:
				confidence = "high"
			elif has_number or has_entity:
				confidence = "medium"
			else:
				confidence = "low"

			matches.append({
				"matched_text": m.group(0)[:100],
				"context": context[:400],
				"source_section": source_section,
				"confidence": confidence,
			})

	return matches


def _extract_entity_from_context(context):
	"""Try to extract a named entity from context text."""
	# Look for company-like names (capitalized multi-word or known patterns)
	patterns = [
		r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+(?:\s+(?:Inc|Corp|Ltd|LLC|Co|Company|Group|Limited))\.?)",
		r"([A-Z]{2,}(?:\s+[A-Z]{2,})*(?:\s+(?:Inc|Corp|Ltd|LLC))?\.?)",
	]
	for pat in patterns:
		match = re.search(pat, context)
		if match:
			return match.group(1).strip()
	return ""


def _build_supply_chain_data(sections):
	"""Extract structured supply chain data from filing sections."""
	supply_chain = {
		"suppliers": [],
		"customers": [],
		"single_source_dependencies": [],
		"geographic_concentration": [],
		"capacity_constraints": [],
		"supply_chain_risks": [],
		"revenue_concentration": [],
		"geographic_revenue": [],
		"purchase_obligations": [],
		"market_risk_disclosures": [],
		"inventory_composition": [],
	}
	total_matches = 0
	entities = set()

	for section_name, text in sections.items():
		if not text:
			continue

		# Suppliers
		matches = _extract_matches(text, _SUPPLIER_PATTERNS, section_name)
		for m in matches:
			entity = _extract_entity_from_context(m["context"])
			if entity:
				entities.add(entity)
			supply_chain["suppliers"].append({
				"entity": entity,
				"relationship": m["matched_text"],
				"context": m["context"],
				"source_section": m["source_section"],
				"confidence": m["confidence"],
			})
		total_matches += len(matches)

		# Customers
		matches = _extract_matches(text, _CUSTOMER_PATTERNS, section_name)
		for m in matches:
			entity = _extract_entity_from_context(m["context"])
			if entity:
				entities.add(entity)
			supply_chain["customers"].append({
				"entity": entity,
				"relationship": m["matched_text"],
				"context": m["context"],
				"source_section": m["source_section"],
				"confidence": m["confidence"],
			})
		total_matches += len(matches)

		# Single source dependencies
		matches = _extract_matches(text, _SINGLE_SOURCE_PATTERNS, section_name)
		for m in matches:
			entity = _extract_entity_from_context(m["context"])
			if entity:
				entities.add(entity)
			supply_chain["single_source_dependencies"].append({
				"component": m["matched_text"],
				"supplier": entity,
				"context": m["context"],
				"source_section": m["source_section"],
				"confidence": m["confidence"],
			})
		total_matches += len(matches)

		# Geographic concentration
		matches = _extract_matches(text, _GEOGRAPHIC_PATTERNS, section_name)
		for m in matches:
			# Try to extract location
			loc_match = re.search(
				r"(?:China|Taiwan|Japan|Korea|South\s+Korea|Germany|Israel|India|"
				r"Mexico|Vietnam|Malaysia|Singapore|Thailand|Philippines|Indonesia|"
				r"United\s+States|U\.S\.|Europe|Asia|Southeast\s+Asia)",
				m["context"], re.IGNORECASE,
			)
			location = loc_match.group(0) if loc_match else ""
			supply_chain["geographic_concentration"].append({
				"location": location,
				"activity": m["matched_text"],
				"context": m["context"],
				"source_section": m["source_section"],
				"confidence": m["confidence"],
			})
		total_matches += len(matches)

		# Capacity constraints
		matches = _extract_matches(text, _CAPACITY_PATTERNS, section_name)
		for m in matches:
			supply_chain["capacity_constraints"].append({
				"constraint": m["matched_text"],
				"context": m["context"],
				"source_section": m["source_section"],
				"confidence": m["confidence"],
			})
		total_matches += len(matches)

		# Supply chain risks
		matches = _extract_matches(text, _RISK_PATTERNS, section_name)
		for m in matches:
			supply_chain["supply_chain_risks"].append({
				"risk": m["matched_text"],
				"context": m["context"],
				"source_section": m["source_section"],
				"confidence": m["confidence"],
			})
		total_matches += len(matches)

	return supply_chain, total_matches, len(entities)


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
# Commands
# ---------------------------------------------------------------------------

@safe_run
def cmd_supply_chain_extract(args):
	"""Extract supply chain structure from 10-K or 10-Q filing."""
	symbol = args.symbol.upper()
	form = args.form.upper() if args.form else "10-K"
	max_chars = args.max_chars
	mode = getattr(args, "mode", "regex")

	# Get CIK and company info
	cik = get_cik_from_symbol(symbol)
	data = get_company_info(cik)
	company_name = data.get("name", "")

	filings = data.get("filings", {}).get("recent", {})
	if not filings:
		output_json({
			"data": None,
			"metadata": {"symbol": symbol, "cik": cik, "company_name": company_name,
						"form": form, "error": "No filings found"},
		})
		return

	# Find the most recent matching filing
	forms = filings.get("form", [])
	filing_dates = filings.get("filingDate", [])
	accession_numbers = filings.get("accessionNumber", [])
	primary_documents = filings.get("primaryDocument", [])

	target_filing = None
	for i in range(len(forms)):
		if forms[i] == form:
			accession = accession_numbers[i] if i < len(accession_numbers) else ""
			primary_doc = primary_documents[i] if i < len(primary_documents) else ""
			cik_int = int(cik)
			filing_url = (
				f"https://www.sec.gov/Archives/edgar/data/{cik_int}/"
				f"{accession.replace('-', '')}/{primary_doc}"
			)
			target_filing = {
				"form": form,
				"filing_date": filing_dates[i] if i < len(filing_dates) else None,
				"accession_number": accession,
				"filing_url": filing_url,
			}
			break

	# Auto-fallback: 10-K not found → try 20-F for foreign filers
	if not target_filing and form == "10-K":
		for i in range(len(forms)):
			if forms[i] == "20-F":
				accession = accession_numbers[i]
				primary_doc = primary_documents[i]
				cik_int = int(cik)
				filing_url = (
					f"https://www.sec.gov/Archives/edgar/data/{cik_int}/"
					f"{accession.replace('-', '')}/{primary_doc}"
				)
				target_filing = {
					"form": "20-F", "filing_date": filing_dates[i],
					"accession_number": accession, "filing_url": filing_url,
				}
				form = "20-F"  # Update for downstream routing
				break

	if not target_filing:
		output_json({
			"data": None,
			"metadata": {"symbol": symbol, "cik": cik, "company_name": company_name,
						"form": form, "error": f"No {form} filing found"},
		})
		return

	# Fetch filing HTML
	time.sleep(0.15)  # Rate limiting
	try:
		resp = requests.get(
			target_filing["filing_url"], headers=SEC_HEADERS, timeout=120,
		)
		resp.raise_for_status()
		content = resp.text
	except Exception as e:
		output_json({
			"data": None,
			"metadata": {"symbol": symbol, "cik": cik, "company_name": company_name,
						"form": form, "error": f"Failed to fetch filing: {str(e)}"},
		})
		return

	# Extract supply chain data based on mode
	if mode == "llm":
		# Section-focused extraction: extract Item 1, 1A, 7, 7A + Notes separately
		# then send ALL sections to Gemini. Gemini 2.5 Flash handles 1M tokens;
		# typical 4-section text + Notes (~400K chars ≈ 100K tokens) is well
		# within capacity. Per-section guard (default 500K) prevents edge cases.
		if form == "10-Q":
			section_extractor = _extract_10q_sections
		elif form == "20-F":
			section_extractor = _extract_20f_sections
		else:
			section_extractor = _extract_10k_sections
		sections = section_extractor(content, max_chars)
		sections_extracted = {k: v is not None for k, v in sections.items()}
		sections_found = sum(1 for v in sections.values() if v is not None)

		# Extract Notes (10-K/20-F only, LLM mode only)
		item8_notes = {} if form == "10-Q" else _extract_item8_notes(content, max_chars, form=form)
		sections_extracted["item_8_notes"] = bool(item8_notes)

		if sections_found > 0:
			section_keys = ["item_1_business", "item_1a_risk_factors", "item_7_mda", "item_7a_market_risk"]
			section_parts = [
				f"[{key.upper()}]\n{sections[key]}"
				for key in section_keys if sections.get(key)
			]
			for note_name, note_text in item8_notes.items():
				section_parts.append(f"[ITEM_8_NOTES_{note_name.upper()}]\n{note_text}")
			focused_text = "\n\n".join(section_parts)
		else:
			focused_text = _prepare_content(content)

		llm_result = _extract_supply_chain_llm(
			focused_text, company_name=company_name, max_chars=None,
		)
		if llm_result is not None:
			supply_chain, total_matches, unique_entities = llm_result
			output_json({
				"data": {
					"filing": target_filing,
					"supply_chain": supply_chain,
					"sections_extracted": sections_extracted,
					"extraction_stats": {
						"total_matches": total_matches,
						"unique_entities": unique_entities,
						"sections_found": sections_found,
						"sections_attempted": 4,
						"mode": "llm",
					},
				},
				"metadata": {
					"symbol": symbol,
					"cik": cik,
					"company_name": company_name,
					"form": form,
				},
			})
			return
		# LLM failed — fallback to regex
		mode = "regex"

	# Regex mode (default)
	if form == "10-Q":
		sections = _extract_10q_sections(content, max_chars)
	elif form == "20-F":
		sections = _extract_20f_sections(content, max_chars)
	else:
		sections = _extract_10k_sections(content, max_chars)

	sections_extracted = {k: v is not None for k, v in sections.items()}
	sections_found = sum(1 for v in sections.values() if v is not None)

	supply_chain, total_matches, unique_entities = _build_supply_chain_data(sections)

	output_json({
		"data": {
			"filing": target_filing,
			"supply_chain": supply_chain,
			"sections_extracted": sections_extracted,
			"extraction_stats": {
				"total_matches": total_matches,
				"unique_entities": unique_entities,
				"sections_found": sections_found,
				"sections_attempted": 4,
				"mode": "regex",
			},
		},
		"metadata": {
			"symbol": symbol,
			"cik": cik,
			"company_name": company_name,
			"form": form,
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
			content = _clean_html(resp.text)

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
	sp = sub.add_parser("supply-chain", help="Extract supply chain from 10-K/10-Q")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--form", default="10-K", help="Form type (10-K, 10-Q, or 20-F)")
	sp.add_argument("--max-chars", type=int, default=500000, help="Max chars per section")
	sp.add_argument("--mode", choices=["regex", "llm"], default="llm",
					help="Extraction mode: 'llm' (default, Gemini structured output) or 'regex' (free, no API key)")
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
