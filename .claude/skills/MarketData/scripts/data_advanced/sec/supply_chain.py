#!/usr/bin/env python3
"""SEC supply chain intelligence extraction from 10-K/10-Q and 8-K filings.

Extracts supply chain relationships, single-source dependencies, geographic
concentration, and capacity constraints from SEC filings. Uses direct HTTP
calls to SEC EDGAR (no disk I/O). Multi-stage regex + heuristic parsing
with graceful degradation on section extraction failure.

Commands:
	supply-chain: Extract supply chain structure from latest 10-K or 10-Q
	events: Extract supply-chain-related events from recent 8-K filings

Args:
	For supply-chain:
		symbol (str): Stock ticker symbol (e.g., "AAPL", "NVDA")
		--form (str): Filing form type, "10-K" or "10-Q" (default: "10-K")
		--max-chars (int): Max characters per section to process (default: 80000)
		--mode (str): Extraction mode - "llm" (default, langextract+Gemini) or "regex" (free, no API key)

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
					"source_section": str, "confidence": str}]
			},
			"sections_extracted": {
				"item_1_business": bool,
				"item_1a_risk_factors": bool,
				"item_7_mda": bool
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
	- LLM mode uses langextract + Gemini for high-quality extraction
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
# LLM-based extraction (langextract + Gemini)
# ---------------------------------------------------------------------------

_LLM_PROMPT = """\
Extract supply chain entities from this SEC filing text.
For each entity found, classify it into one of these categories:
- supplier: Companies that supply products, materials, or services
- customer: Companies that purchase products or services
- single_source: Sole-source or single-source supplier dependencies
- geographic: Manufacturing, production, or sourcing locations
- capacity_constraint: Production capacity limitations, lead times, backlogs
- supply_chain_risk: Supply disruption risks, tariffs, material shortages

Use exact text from the filing for extraction_text.
Include the entity name and relationship details as attributes.
Do not extract the filing company itself as a supplier or customer.
"""


def _get_llm_examples():
	"""Return few-shot examples for langextract. Imported lazily."""
	import langextract as lx

	return [
		lx.data.ExampleData(
			text=(
				"We rely on Samsung Electronics Co., Ltd. as our sole source "
				"supplier for DRAM memory chips used in our products. "
				"Apple Inc. accounted for approximately 35% of our net revenue "
				"for fiscal year 2024. Our manufacturing facilities are located "
				"primarily in Taiwan and South Korea. We have experienced "
				"extended lead times of 26 weeks for certain key components. "
				"Tariffs on goods imported from China could adversely affect "
				"our supply chain costs."
			),
			extractions=[
				lx.data.Extraction(
					extraction_class="supplier",
					extraction_text="Samsung Electronics Co., Ltd.",
					attributes={"relationship": "sole source supplier",
								"component": "DRAM memory chips"},
				),
				lx.data.Extraction(
					extraction_class="single_source",
					extraction_text="Samsung Electronics Co., Ltd. as our sole source supplier for DRAM memory chips",
					attributes={"component": "DRAM memory chips",
								"supplier": "Samsung Electronics Co., Ltd."},
				),
				lx.data.Extraction(
					extraction_class="customer",
					extraction_text="Apple Inc.",
					attributes={"revenue_pct": "35%",
								"relationship": "major customer"},
				),
				lx.data.Extraction(
					extraction_class="geographic",
					extraction_text="Taiwan and South Korea",
					attributes={"activity": "manufacturing",
								"locations": "Taiwan, South Korea"},
				),
				lx.data.Extraction(
					extraction_class="capacity_constraint",
					extraction_text="extended lead times of 26 weeks",
					attributes={"constraint_type": "lead time",
								"duration": "26 weeks"},
				),
				lx.data.Extraction(
					extraction_class="supply_chain_risk",
					extraction_text="Tariffs on goods imported from China",
					attributes={"risk_type": "tariff",
								"affected_region": "China"},
				),
			],
		)
	]


def _extract_supply_chain_llm(cleaned_text, company_name="", max_chars=None):
	"""Extract supply chain data from filing text using langextract + Gemini.

	Returns:
		tuple(dict, int, int) or None: (supply_chain, total_matches, unique_entities)
		Returns None on failure (caller should fallback to regex).
	"""
	try:
		import langextract as lx
	except ImportError:
		return None

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

	additional_context = ""
	if company_name:
		additional_context = (
			f"The filing company is '{company_name}'. "
			"Do not extract it as a supplier or customer of itself."
		)

	try:
		result = lx.extract(
			text_or_documents=text,
			prompt_description=_LLM_PROMPT,
			examples=_get_llm_examples(),
			model_id=model_id,
			api_key=api_key,
			additional_context=additional_context,
			max_char_buffer=500_000,
			max_workers=5,
			show_progress=False,
			fetch_urls=False,
		)
	except Exception:
		return None

	supply_chain = {
		"suppliers": [],
		"customers": [],
		"single_source_dependencies": [],
		"geographic_concentration": [],
		"capacity_constraints": [],
		"supply_chain_risks": [],
	}
	entities = set()

	extractions = result.extractions if hasattr(result, "extractions") else []

	class_map = {
		"supplier": "suppliers",
		"customer": "customers",
		"single_source": "single_source_dependencies",
		"geographic": "geographic_concentration",
		"capacity_constraint": "capacity_constraints",
		"supply_chain_risk": "supply_chain_risks",
	}

	for ext in extractions:
		category = class_map.get(ext.extraction_class)
		if not category:
			continue
		attrs = ext.attributes or {}
		entity_name = (
			attrs.get("supplier", "") or attrs.get("entity", "")
			or ext.extraction_text
		)
		context = ext.extraction_text

		if category == "suppliers":
			entities.add(entity_name)
			supply_chain["suppliers"].append({
				"entity": entity_name,
				"relationship": attrs.get("relationship", ""),
				"context": context,
				"source_section": "llm_extraction",
				"confidence": "high",
			})
		elif category == "customers":
			entities.add(entity_name)
			supply_chain["customers"].append({
				"entity": entity_name,
				"relationship": attrs.get("relationship", ""),
				"context": context,
				"source_section": "llm_extraction",
				"confidence": "high",
			})
		elif category == "single_source_dependencies":
			supplier_name = attrs.get("supplier", entity_name)
			entities.add(supplier_name)
			supply_chain["single_source_dependencies"].append({
				"component": attrs.get("component", ""),
				"supplier": supplier_name,
				"context": context,
				"source_section": "llm_extraction",
				"confidence": "high",
			})
		elif category == "geographic_concentration":
			supply_chain["geographic_concentration"].append({
				"location": attrs.get("locations", "") or attrs.get("location", ""),
				"activity": attrs.get("activity", ""),
				"context": context,
				"source_section": "llm_extraction",
				"confidence": "high",
			})
		elif category == "capacity_constraints":
			supply_chain["capacity_constraints"].append({
				"constraint": attrs.get("constraint_type", ""),
				"context": context,
				"source_section": "llm_extraction",
				"confidence": "high",
			})
		elif category == "supply_chain_risks":
			supply_chain["supply_chain_risks"].append({
				"risk": attrs.get("risk_type", ""),
				"context": context,
				"source_section": "llm_extraction",
				"confidence": "high",
			})

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
	# Normalize whitespace
	text = re.sub(r"\s+", " ", text)
	return text


def _extract_section(content, start_patterns, end_patterns, max_chars):
	"""Multi-stage section extraction with fallback.

	Operates on pre-cleaned plain text (HTML already stripped).
	Stage 1: Regex for section header markers
	Stage 2: Broader keyword fallback
	"""
	# Stage 1: Direct regex match on cleaned text
	# Try all matches of each pattern — skip ToC entries (short sections)
	for pattern in start_patterns:
		for match in re.finditer(pattern, content, re.IGNORECASE):
			start = match.start()
			# Find end
			for end_pattern in end_patterns:
				end_match = re.search(end_pattern, content[start + 200:], re.IGNORECASE)
				if end_match:
					end = start + 200 + end_match.start()
					section = content[start:end]
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
		cleaned_text = _prepare_content(content)
		llm_result = _extract_supply_chain_llm(
			cleaned_text, company_name=company_name, max_chars=max_chars,
		)
		if llm_result is not None:
			supply_chain, total_matches, unique_entities = llm_result
			output_json({
				"data": {
					"filing": target_filing,
					"supply_chain": supply_chain,
					"sections_extracted": {
						"item_1_business": True,
						"item_1a_risk_factors": True,
						"item_7_mda": True,
					},
					"extraction_stats": {
						"total_matches": total_matches,
						"unique_entities": unique_entities,
						"sections_found": 3,
						"sections_attempted": 3,
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
				"sections_attempted": 3,
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
	sp.add_argument("--form", default="10-K", help="Form type (10-K or 10-Q)")
	sp.add_argument("--max-chars", type=int, default=80000, help="Max chars per section")
	sp.add_argument("--mode", choices=["regex", "llm"], default="llm",
					help="Extraction mode: 'llm' (default, langextract+Gemini) or 'regex' (free, no API key)")
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
