#!/usr/bin/env python3
"""Serenity Pipeline v5.2.0 (Pipeline-Complete): 6-Level analytical hierarchy
automating supply chain bottleneck analysis with macro regime assessment,
fundamental validation, composite signal generation, and evidence chain
verification.

Orchestrates the complete Serenity analysis by running macro regime scripts,
fundamental analysis tools, valuation models, and catalyst monitoring in
parallel. Pipeline-Complete — all methodology-required module calls are contained
within the pipeline; do not call individual modules to supplement.

L1 macro includes BDI/DXY/real rates always-on; L2 includes hyperscaler CapEx
bridge signal; L3 includes SEC supply chain pre-extraction with 6-Criteria
pre-scoring, absence evidence flags, and sole_western_flag; L4 includes
health gate severity spectrum (PASS/CAUTION/FLAG) with 5 gates (bear_bull,
dilution, no_growth, margin, io_quality), thesis validation signals, SoP
trigger detection, and trapped asset override; L6 includes rule-based
auto-classification. Composite signal generation produces integrated
investment grades with position sizing guidance. Valuation summary includes
dual_valuation (no-growth floor + growth upside).

Commands:
	macro: Level 1 macro regime assessment (10 parallel macro scripts → regime
		classification as risk_on/risk_off/transitional with drain counting.
		BDI/DXY z-scores and real rates always included.
		ERP extracted via erp.current.erp, Fear&Greed via fear_greed.current.score)
	analyze: Full 6-Level analysis for a single ticker (L1 macro + L2 hyperscaler
		CapEx bridge + L3 SEC supply chain pre-scoring + L4 fundamentals with
		health gate severity spectrum + thesis signals + SoP triggers +
		trapped asset override + L5 catalysts + L6 auto-classification +
		composite signal with position sizing)
	recheck: Position monitoring recheck (macro regime + health gates + thesis
		signals against existing position with action signals and verdict)
	discover: Automated theme discovery (sector_leaders + finviz cross-reference
		+ bottleneck_scorer validation, grouped by industry theme)
	cross-chain: Shared supplier detection across multiple tickers via SEC
		supply chain entity normalization and cross-matching, with
		bottleneck_signal scoring (supplier_ref_pct, single_source_count,
		assessment) for each shared entity
	compare: Multi-ticker side-by-side comparison (12 metrics including asymmetry_score)
	screen: Sector-based bottleneck candidate screening
	capex-cascade: Supply chain CapEx cascade tracking across multiple tickers

Args:
	For macro:
		--extended (bool): Include raw DXY and BDI data (default: false)

	For analyze:
		ticker (str): Stock ticker symbol
		--skip-macro (bool): Skip Level 1 macro assessment (default: false)

	For recheck:
		ticker (str): Stock ticker symbol
		--entry-price (str): Entry price for position (required)
		--entry-date (str): Entry date YYYY-MM-DD (informational, optional)

	For discover:
		--top-groups (int): Number of top industry groups (default: 5)
		--max-mcap (str): Maximum market cap filter (default: "10B")
		--limit (int): Maximum candidates per theme (default: 10)
		--industry (str): Direct industry search — skips sector_leaders, goes
			straight to finviz industry-screen (default: None)

	For cross-chain:
		tickers (list): 2+ stock ticker symbols
		--form (str): SEC filing form type (default: "10-K")

	For compare:
		tickers (list): 2+ stock ticker symbols

	For screen:
		sector (str): Sector name for Finviz screening
		--max-mcap (str): Maximum market cap filter, applied post-screen (default: "10B")

	For capex-cascade:
		tickers (list): 2+ stock ticker symbols for CapEx cascade tracking

Returns:
	For macro:
		dict with regime (str: risk_on/risk_off/transitional),
		risk_level (str: low/moderate/elevated/high),
		drain_count (int), decision_rules (list[str] with actual values),
		signals (dict with erp_pct, vix_spot, vix_regime, vix_structure,
		net_liq_direction, net_liq_current, fear_greed,
		fedwatch_next_meeting, fedwatch_probabilities,
		bdi_z_score, bdi_demand, dxy_z_score, dxy_strength, real_rate;
		when --extended: dxy (raw DXY data), bdi (raw BDI data))

	For analyze:
		dict with ticker, levels (L1_macro through L6_taxonomy),
		health_gates (with severity spectrum), thesis_signals,
		sop_triggers, trapped_asset_override, composite_signal
		(with grade, score_breakdown, position_guidance),
		health_gates (bear_bull_paradox, active_dilution, no_growth_fail,
		margin_collapse, io_quality_concern — each PASS/CAUTION/FLAG),
		valuation_summary (includes dual_valuation: no_growth_floor + growth_upside),
		fundamental_readiness_codes (list of standardized audit codes).
		L1_macro: regime classification + signals dict (no raw data).
		L2_capex_flow: company_capex (8-quarter trend auto-included),
		cascade_requires_context (agent-driven supply chain layers).
		L4_fundamentals: info (24 essential fields),
		holders (top 5 summary with total count),
		insider_transactions (summary + recent 20, 12-month lookback),
		earnings_acceleration (compressed: status flags + 3 recent growth rates),
		sbc_analyzer, forward_pe, debt_structure,
		institutional_quality, no_growth_valuation, margin_tracker,
		iv_context, revenue_trajectory (8-quarter actual revenue).
		L5_catalysts: earnings_dates (capped at 8 most recent),
		earnings_surprise (post-ER reaction),
		analyst_recommendations, analyst_price_targets, analyst_revisions.
		L3_bottleneck: sec_supply_chain (suppliers, customers,
		single_source_dependencies, geographic_concentration,
		capacity_constraints, supply_chain_risks — trimmed for context),
		sec_events (recent 8-K supply chain events),
		sec_status (SEC_SC_available/partial/unavailable),
		absence_evidence_flags (list of absence type signals),
		bottleneck_pre_score.sole_western_flag (bool).
		L2: cascade_requires_context (agent-driven). L6: requires_llm.

	For compare:
		dict with tickers, comparative_table (forward_pe,
		no_growth_upside_pct, margin_status, io_quality_score,
		debt_quality_grade, market_cap, revenue_growth_yoy,
		short_interest_pct, 52w_range_position, sbc_flag,
		consecutive_beats, asymmetry_score per ticker),
		health_gates, relative_strengths.

	For screen:
		dict with sector, candidates_screened (int),
		results (list sorted by asymmetry_score desc).

	For capex-cascade:
		dict with tickers, capex_trends (per-ticker 8Q CapEx with
		QoQ/YoY direction and acceleration), cascade_summary (overall
		cascade health and upstream→downstream consistency),
		hyperscaler_signal (aggregate hyperscaler CapEx direction if
		applicable).

Example:
	>>> python serenity.py macro --extended
	{"regime": "risk_on", "risk_level": "moderate", "signals": {...}, ...}

	>>> python serenity.py analyze NBIS
	{"ticker": "NBIS", "levels": {"L1_macro": {"regime": ..., "signals": {...}}, "L2_capex_flow": {"company_capex": {...}, ...}, "L4_fundamentals": {"info": {...}, "insider_transactions": {"summary": {...}, "transactions": [...]}, "revenue_trajectory": {...}, ...}, "L5_catalysts": {"earnings_surprise": {...}, "analyst_recommendations": {...}, ...}}, "health_gates": {...}, ...}

	>>> python serenity.py analyze NBIS --skip-macro
	{"ticker": "NBIS", "levels": {"L1_macro": {"skipped": true}, ...}, ...}

	>>> python serenity.py compare AXTI AEHR FORM
	{"tickers": [...], "comparative_table": {"forward_pe": {...}, "market_cap": {...}, "revenue_growth_yoy": {...}, ...}, ...}

	>>> python serenity.py screen "Defense" --max-mcap 5B
	{"sector": "Defense", "candidates_screened": 10, ...}

Use Cases:
	- Full due diligence automation for any ticker in any sector
	- Macro regime assessment before position entry
	- Evidence chain completeness check for conviction assignment
	- Multi-ticker comparison within a supply chain
	- Sector screening for bottleneck candidates
	- Sector-agnostic: works for defense, EV, agriculture, semiconductors, etc.

Notes:
	- Pipeline-Complete: all methodology-required module calls are contained within subcommands
	- L1 macro and L4-L6 fundamentals auto-execute for any ticker
	- L2 company CapEx auto-included (8-quarter trend); supply chain cascade requires agent context
	- L3 (Bottleneck) returns requires_context for agent-driven analysis
	- Health gates are extracted from L4 script outputs (debt, dilution, valuation, margin)
	- Conditional SEC filing check when active_dilution detected (S-3 form lookup)
	- fundamental_readiness_codes provide audit trail of automated assessment
	- Scripts execute in parallel via ThreadPoolExecutor for speed
	- Pipeline continues even if individual scripts fail (graceful degradation)
	- screen subcommand depends on finviz.py and bottleneck_scorer.py; --max-mcap applied as post-filter
	- L1 output contains extracted signals (9 scalars + DXY/BDI when --extended)
	- L4 info uses get-info-fields with 24 essential fields (not full 100+ field info object)
	- L4 insider_transactions: 12-month lookback, summarized (buy/sell aggregates + net_direction + recent 20)
	- L4 revenue_trajectory: extracted from quarterly income statement (8 quarters, TotalRevenue only)
	- L5 earnings_calendar removed (was market-wide, not ticker-specific; earnings_dates covers ticker)
	- compare uses get-info-fields (5 fields) instead of get-info (100+ fields)
	- compare includes sbc_analyzer (SBC health flag) and earnings_surprise (consecutive beats) for filtering
	- compare uses forward_pe (analyst consensus) for revenue_growth_yoy
	- compare includes asymmetry_score via bottleneck_scorer.py validate per ticker (12 metrics total)
	- capex-cascade tracks 8Q CapEx via capex_tracker.py track per ticker, with cascade health summary
	- L4 holders summarized to top 5 with key fields + total count
	- L4 earnings_acceleration compressed to status flags + 3 most recent growth rates
	- L5 earnings_dates capped at 8 most recent (2 years quarterly)
	- Yield curve limited to 5 observations, net liquidity to 10 observations
"""

import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import output_json, safe_run

SCRIPTS_DIR = os.path.dirname(os.path.dirname(__file__))


def _run_script(script_path, args_list, timeout=60):
	"""Run a script and capture its JSON output."""
	full_path = os.path.join(SCRIPTS_DIR, script_path)
	cmd = [sys.executable, full_path] + args_list

	try:
		result = subprocess.run(
			cmd,
			capture_output=True,
			text=True,
			timeout=timeout,
			cwd=SCRIPTS_DIR,
		)
		if result.returncode == 0 and result.stdout.strip():
			return json.loads(result.stdout)
		else:
			return {"error": result.stderr.strip() or "Script returned no output"}
	except subprocess.TimeoutExpired:
		return {"error": f"Script timed out ({timeout}s)"}
	except json.JSONDecodeError:
		return {"error": "Invalid JSON output from script"}
	except Exception as e:
		return {"error": str(e)}


# ---------------------------------------------------------------------------
# Health Gate Extraction
# ---------------------------------------------------------------------------

def _extract_health_gates(results):
	"""Extract 4 health gates from L4 script results with 3-level severity.

	Severity levels: PASS (1.0), CAUTION (0.5), FLAG (0.0)

	Gates:
	1. Bear-Bull Paradox: debt grade + interest coverage
	2. Active Dilution: shares change percentage
	3. No-Growth Fail: margin of safety percentage
	4. Margin Collapse: margin trajectory

	Returns:
		dict with gate statuses, severity_score (0-4.0), total_pass, total_gates, flags
	"""
	gates = {
		"bear_bull_paradox": "PASS",
		"active_dilution": "PASS",
		"no_growth_fail": "PASS",
		"margin_collapse": "PASS",
	}
	severity = {
		"bear_bull_paradox": 1.0,
		"active_dilution": 1.0,
		"no_growth_fail": 1.0,
		"margin_collapse": 1.0,
	}
	flags = []

	# Bear-Bull Paradox: PASS (A-B + coverage > 3x), CAUTION (C OR 1-3x), FLAG (D OR < 1x)
	debt = results.get("debt_structure", {})
	bbp_detail = {}
	if not debt.get("error"):
		grade = str(debt.get("debt_quality_grade", "")).upper()[:1]
		coverage = debt.get("interest_coverage_ratio")
		bbp_detail = {
			"debt_quality_grade": debt.get("debt_quality_grade"),
			"interest_coverage_ratio": coverage,
			"total_debt": debt.get("total_debt"),
			"cash_and_equivalents": debt.get("cash_and_equivalents"),
			"net_debt": debt.get("net_debt"),
			"debt_to_equity": debt.get("debt_to_equity"),
			"thresholds": "FLAG: grade D or coverage < 1x | CAUTION: grade C or 1-3x | PASS: grade A-B and coverage > 3x",
		}
		if grade == "D" or (coverage is not None and coverage < 1.0):
			gates["bear_bull_paradox"] = "FLAG"
			severity["bear_bull_paradox"] = 0.0
			flags.append("bear_bull_paradox")
		elif grade == "C" or (coverage is not None and 1.0 <= coverage <= 3.0):
			gates["bear_bull_paradox"] = "CAUTION"
			severity["bear_bull_paradox"] = 0.5

	# Active Dilution: PASS (< 1%), CAUTION (1-2%), FLAG (> 2%)
	sbc = results.get("sbc_analyzer", {})
	ad_detail = {}
	if not sbc.get("error"):
		shares_change = sbc.get("shares_change_qoq_pct")
		ad_detail = {
			"shares_change_qoq_pct": shares_change,
			"dilution_flag": sbc.get("dilution_flag"),
			"sbc_pct_revenue": sbc.get("sbc_pct_revenue"),
			"total_dilution_annual_pct": sbc.get("total_dilution_annual_pct"),
			"thresholds": "FLAG: > 2% or active_dilution | CAUTION: 1-2% | PASS: < 1%",
		}
		if isinstance(shares_change, (int, float)):
			if shares_change > 2:
				gates["active_dilution"] = "FLAG"
				severity["active_dilution"] = 0.0
				flags.append("active_dilution")
			elif shares_change > 1:
				gates["active_dilution"] = "CAUTION"
				severity["active_dilution"] = 0.5
		elif sbc.get("dilution_flag") == "active_dilution":
			gates["active_dilution"] = "FLAG"
			severity["active_dilution"] = 0.0
			flags.append("active_dilution")

	# No-Growth Fail: PASS (MoS > 20%), CAUTION (0-20%), FLAG (< 0%)
	ngv = results.get("no_growth_valuation", {})
	ngf_detail = {}
	if not ngv.get("error"):
		mos = ngv.get("margin_of_safety_pct")
		ngf_detail = {
			"margin_of_safety_pct": mos,
			"no_growth_fair_value": ngv.get("no_growth_fair_value"),
			"current_market_cap": ngv.get("current_market_cap"),
			"implied_earnings": ngv.get("implied_earnings"),
			"net_margin_pct": ngv.get("net_margin_pct"),
			"thresholds": "FLAG: MoS < 0% | CAUTION: 0-20% | PASS: > 20%",
		}
		if mos is not None:
			if mos < 0:
				gates["no_growth_fail"] = "FLAG"
				severity["no_growth_fail"] = 0.0
				flags.append("no_growth_fail")
			elif mos <= 20:
				gates["no_growth_fail"] = "CAUTION"
				severity["no_growth_fail"] = 0.5

	# Margin Collapse: PASS (expanding), CAUTION (stable/compression), FLAG (collapse)
	margin = results.get("margin_tracker", {})
	mc_detail = {}
	if not margin.get("error"):
		margin_flag = str(margin.get("flag", "")).upper()
		latest_q = margin.get("latest_quarter", {})
		mc_detail = {
			"flag": margin.get("flag"),
			"gross_margin": latest_q.get("gross_margin") if isinstance(latest_q, dict) else None,
			"operating_margin": latest_q.get("operating_margin") if isinstance(latest_q, dict) else None,
			"net_margin": latest_q.get("net_margin") if isinstance(latest_q, dict) else None,
			"gross_margin_qoq_change": margin.get("gross_margin_qoq_change"),
			"operating_margin_qoq_change": margin.get("operating_margin_qoq_change"),
			"thresholds": "FLAG: collapse | CAUTION: stable/compression/contracting | PASS: expanding",
		}
		if "COLLAPSE" in margin_flag:
			gates["margin_collapse"] = "FLAG"
			severity["margin_collapse"] = 0.0
			flags.append("margin_collapse")
		elif "COMPRESSION" in margin_flag or "CONTRACTING" in margin_flag or "STABLE" in margin_flag:
			gates["margin_collapse"] = "CAUTION"
			severity["margin_collapse"] = 0.5

	# IO Quality: CAUTION only (never FLAG) — H2/H8 TacitKnowledge Audit
	gates["io_quality_concern"] = "PASS"
	severity["io_quality_concern"] = 1.0
	iq_detail = {}
	io_data = results.get("institutional_quality", {})
	if not io_data.get("error"):
		io_score = io_data.get("io_quality_score")
		quant_mm_pct = io_data.get("quant_mm_pct")
		iq_detail = {
			"io_quality_score": io_score,
			"quant_mm_pct": quant_mm_pct,
			"thresholds": "CAUTION: quant_mm_pct > 30% or io_score <= 3 | PASS: otherwise | never FLAG",
		}
		if (isinstance(quant_mm_pct, (int, float)) and quant_mm_pct > 30) or \
		   (isinstance(io_score, (int, float)) and io_score <= 3):
			gates["io_quality_concern"] = "CAUTION"
			severity["io_quality_concern"] = 0.5

	severity_score = sum(severity.values())
	total_pass = sum(1 for k, v in gates.items()
		if v == "PASS" and k not in ("total_pass", "total_gates", "flags", "severity", "severity_score", "detail"))

	gates["total_pass"] = total_pass
	gates["total_gates"] = 5
	gates["flags"] = flags
	gates["severity"] = severity
	gates["severity_score"] = severity_score
	gates["detail"] = {
		"bear_bull_paradox": bbp_detail,
		"active_dilution": ad_detail,
		"no_growth_fail": ngf_detail,
		"margin_collapse": mc_detail,
		"io_quality_concern": iq_detail,
	}

	return gates


def _build_valuation_summary(results):
	"""Build valuation summary from L4 script results.

	Includes dual_valuation object combining no-growth floor and growth upside
	(TacitKnowledge Audit H4: Dual-Valuation Anchor).
	"""
	forward_pe_data = results.get("forward_pe", {})
	ngv_data = results.get("no_growth_valuation", {})
	margin_data = results.get("margin_tracker", {})
	io_data = results.get("institutional_quality", {})
	debt_data = results.get("debt_structure", {})

	# Dual-Valuation: no-growth floor + growth upside (H4)
	dual_valuation = {}
	if not ngv_data.get("error"):
		dual_valuation["no_growth_floor"] = {
			"fair_value": ngv_data.get("no_growth_fair_value"),
			"market_cap": ngv_data.get("current_market_cap"),
			"margin_of_safety_pct": ngv_data.get("margin_of_safety_pct"),
		}
	if not forward_pe_data.get("error"):
		dual_valuation["growth_upside"] = {
			"forward_1y_pe": forward_pe_data.get("forward_1y_pe"),
			"forward_2y_pe": forward_pe_data.get("forward_2y_pe"),
			"revenue_based_fair_value_low": forward_pe_data.get("revenue_based_fair_value_low"),
			"revenue_based_fair_value_high": forward_pe_data.get("revenue_based_fair_value_high"),
			"primary_valuation_method": forward_pe_data.get("primary_valuation_method"),
			"assessment": forward_pe_data.get("assessment"),
		}

	return {
		"forward_pe": forward_pe_data.get("forward_1y_pe") if not forward_pe_data.get("error") else None,
		"no_growth_upside_pct": ngv_data.get("margin_of_safety_pct") if not ngv_data.get("error") else None,
		"margin_status": margin_data.get("flag") if not margin_data.get("error") else None,
		"io_quality_score": io_data.get("io_quality_score") if not io_data.get("error") else None,
		"debt_quality_grade": debt_data.get("debt_quality_grade") if not debt_data.get("error") else None,
		"dual_valuation": dual_valuation,
	}


# ---------------------------------------------------------------------------
# Post-Processing Helpers
# ---------------------------------------------------------------------------

def _summarize_insider_transactions(data):
	"""Summarize insider transactions: aggregate buy/sell counts and amounts,
	determine net direction, and keep only the most recent 20 transactions.

	Args:
		data: Raw insider transactions output (list or dict with transactions key)

	Returns:
		dict with summary (buy_count, sell_count, buy_amount, sell_amount,
		net_direction) and transactions (most recent 20)
	"""
	transactions = data if isinstance(data, list) else data.get("transactions", [])
	if not isinstance(transactions, list):
		return data

	buy_count = 0
	sell_count = 0
	buy_amount = 0.0
	sell_amount = 0.0

	for txn in transactions:
		if not isinstance(txn, dict):
			continue
		txn_type = str(txn.get("type", "") or txn.get("transaction", "")).lower()
		value = txn.get("value") or txn.get("amount") or 0
		try:
			value = float(value)
		except (ValueError, TypeError):
			value = 0.0

		if "buy" in txn_type or "purchase" in txn_type:
			buy_count += 1
			buy_amount += value
		elif "sale" in txn_type or "sell" in txn_type:
			sell_count += 1
			sell_amount += value

	if buy_amount > sell_amount * 1.2:
		net_direction = "net_buying"
	elif sell_amount > buy_amount * 1.2:
		net_direction = "net_selling"
	else:
		net_direction = "mixed"

	return {
		"summary": {
			"total_transactions": len(transactions),
			"buy_count": buy_count,
			"sell_count": sell_count,
			"buy_amount": round(buy_amount, 2),
			"sell_amount": round(sell_amount, 2),
			"net_direction": net_direction,
		},
		"transactions": transactions[:20],
	}


def _extract_revenue_trajectory(financials_data):
	"""Extract quarterly revenue trajectory from income statement data.

	Args:
		financials_data: Raw income statement output from financials.py

	Returns:
		dict with revenue_by_quarter (list of {quarter, revenue} dicts, max 8)
	"""
	revenue_by_quarter = []

	# financials.py returns data in various formats; handle common structures
	if isinstance(financials_data, dict):
		# Try "data" key first (common wrapper)
		records = financials_data.get("data", financials_data)
		if isinstance(records, dict):
			# Column-oriented: {"TotalRevenue": {"2025-Q3": 203000000, ...}}
			rev_data = records.get("TotalRevenue") or records.get("Total Revenue")
			if isinstance(rev_data, dict):
				for quarter, revenue in list(rev_data.items())[:8]:
					revenue_by_quarter.append({
						"quarter": str(quarter),
						"revenue": revenue,
					})
			else:
				# Row-oriented: {date: {field: value, ...}, ...}
				for date_key, row in list(records.items())[:8]:
					if isinstance(row, dict):
						rev = row.get("TotalRevenue") or row.get("Total Revenue")
						if rev is not None:
							revenue_by_quarter.append({
								"quarter": str(date_key),
								"revenue": rev,
							})
	elif isinstance(financials_data, list):
		for record in financials_data[:8]:
			if isinstance(record, dict):
				quarter = record.get("quarter") or record.get("date") or record.get("period")
				rev = record.get("TotalRevenue") or record.get("Total Revenue") or record.get("revenue")
				if quarter and rev is not None:
					revenue_by_quarter.append({
						"quarter": str(quarter),
						"revenue": rev,
					})

	return {"revenue_by_quarter": revenue_by_quarter}


def _cap_earnings_dates(data, limit=8):
	"""Cap earnings_dates to the most recent N entries.

	yfinance get_earnings_dates may ignore the limit parameter,
	so this trims each column dict to the first `limit` entries
	(most recent dates first).

	Args:
		data: Raw earnings_dates output (dict-of-dicts from actions.py)
		limit: Maximum number of entries to keep (default 8)

	Returns:
		dict with each column trimmed to `limit` entries
	"""
	if not isinstance(data, dict) or data.get("error"):
		return data
	trimmed = {}
	for col, values in data.items():
		if isinstance(values, dict):
			trimmed[col] = dict(list(values.items())[:limit])
		else:
			trimmed[col] = values
	return trimmed


def _compress_earnings_acceleration(data):
	"""Compress earnings_acceleration output to essential metrics.

	Retains pass/fail status flags and trims growth rate arrays
	to most recent 3 values.

	Args:
		data: Raw earnings_acceleration code33 output dict

	Returns:
		dict with symbol, code33_status, acceleration booleans,
		trimmed growth rates (3 most recent), and data_quality
	"""
	if not isinstance(data, dict) or data.get("error"):
		return data
	return {
		"symbol": data.get("symbol"),
		"code33_status": data.get("code33_status"),
		"eps_accelerating": data.get("eps_accelerating"),
		"sales_accelerating": data.get("sales_accelerating"),
		"margin_expanding": data.get("margin_expanding"),
		"eps_growth_rates": data.get("eps_growth_rates", [])[:3],
		"sales_growth_rates": data.get("sales_growth_rates", [])[:3],
		"data_quality": data.get("data_quality"),
	}


def _summarize_holders(data):
	"""Summarize institutional holders to top 5 with key fields only.

	Retains holder name, shares, and pctHeld. Drops date, value, and
	pctChange columns for token efficiency.

	Args:
		data: Raw institutional holders output (dict-of-lists format from holders.py)

	Returns:
		dict with top_holders (list of 5 dicts) and total_reported count
	"""
	if not isinstance(data, dict) or data.get("error"):
		return data

	holders_list = []
	holder_names = data.get("Holder", {})
	pct_held = data.get("pctHeld", {})
	shares = data.get("Shares", {})

	if holder_names:
		for idx in sorted(holder_names.keys(), key=lambda x: int(x))[:5]:
			holders_list.append({
				"holder": holder_names.get(idx),
				"pctHeld": pct_held.get(idx),
				"shares": shares.get(idx),
			})

	return {
		"top_holders": holders_list,
		"total_reported": len(holder_names),
	}


# ---------------------------------------------------------------------------
# Fundamental Readiness Codes
# ---------------------------------------------------------------------------

def _build_readiness_codes(health_gates, valuation_summary, l4_results, l5_results=None, sec_result=None, sec_sc_results=None, bottleneck_pre_score=None, composite_signal=None):
	"""Build standardized fundamental readiness codes for auditability.

	Returns:
		list of str codes summarizing automated assessment
	"""
	codes = []

	# Health gates
	codes.append(f"HEALTH_GATES_{health_gates['total_pass']}_{health_gates['total_gates']}")

	# Health severity score
	sev_score = health_gates.get("severity_score")
	if sev_score is not None:
		codes.append(f"HEALTH_SEVERITY_{sev_score}")

	# Dilution status
	sbc = l4_results.get("sbc_analyzer", {})
	if sec_result and not sec_result.get("error"):
		codes.append("DILUTION_sec_confirmed_atm")
	elif not sbc.get("error"):
		dilution = sbc.get("dilution_flag", "clean")
		codes.append(f"DILUTION_{dilution}")

	# Valuation floor
	upside = valuation_summary.get("no_growth_upside_pct")
	if upside is not None:
		codes.append(f"VALUATION_FLOOR_{upside:.0f}PCT")

	# Forward PE
	fpe = valuation_summary.get("forward_pe")
	if fpe is not None:
		codes.append(f"FWD_PE_{fpe:.1f}")

	# Margin trajectory
	margin = valuation_summary.get("margin_status")
	if margin:
		codes.append(f"MARGIN_{margin}")

	# Debt quality
	debt = valuation_summary.get("debt_quality_grade")
	if debt:
		codes.append(f"DEBT_GRADE_{debt}")

	# IO quality
	io = valuation_summary.get("io_quality_score")
	if io is not None:
		codes.append(f"IO_QUALITY_{io}")

	# Code 33 status
	ea = l4_results.get("earnings_acceleration", {})
	if not ea.get("error"):
		c33 = ea.get("code33_status")
		if c33 is not None:
			codes.append(f"CODE33_{str(c33).upper()}")

	# Consecutive beats
	if l5_results:
		es = l5_results.get("earnings_surprise", {})
		if not es.get("error"):
			beats = es.get("consecutive_beats")
			if beats is not None:
				codes.append(f"BEATS_{beats}")

	# SBC health
	if not sbc.get("error"):
		sbc_flag = sbc.get("flag")
		if sbc_flag:
			codes.append(f"SBC_{sbc_flag}")

	# CapEx direction (from L2 company_capex if available)
	# capex_data is passed separately as it's popped from l4_results

	# SEC supply chain data availability
	if sec_sc_results:
		sc_data = sec_sc_results.get("sec_supply_chain", {})
		if sc_data and not sc_data.get("error") and sc_data.get("data"):
			matches = sc_data["data"].get("extraction_stats", {}).get("total_matches", 0)
			if matches > 0:
				codes.append("SEC_SC_available")
			else:
				codes.append("SEC_SC_partial")
		else:
			codes.append("SEC_SC_unavailable")

	# Bottleneck pre-score
	if bottleneck_pre_score and not bottleneck_pre_score.get("error"):
		bn_score = bottleneck_pre_score.get("pre_score", 0)
		bn_max = bottleneck_pre_score.get("pre_score_max", 4.25)
		codes.append(f"BOTTLENECK_PRE_{bn_score}_{bn_max}")

	# Composite signal grade
	if composite_signal and not composite_signal.get("error"):
		grade = composite_signal.get("grade")
		score = composite_signal.get("composite_score")
		if grade:
			codes.append(f"COMPOSITE_{grade}_{score}")

	return codes


# ---------------------------------------------------------------------------
# SEC Supply Chain Post-processing (L3)
# ---------------------------------------------------------------------------

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
	}


def _build_thesis_signals(l4_results, l5_results):
	"""Map L4/L5 results to thesis strengthening/weakening signals."""
	l4 = l4_results or {}
	l5 = l5_results or {}
	strengthening = []
	weakening = []

	margin_tracker = l4.get("margin_tracker") or {}
	earnings_acc = l4.get("earnings_acceleration") or {}
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
		rev_dir = analyst_rev.get("revisions_direction", "")
		if isinstance(rev_dir, str) and rev_dir.lower() == "up":
			strengthening.append("street_catching_up")
		else:
			for key in ("current_quarter", "next_quarter", "current_year", "next_year"):
				val = analyst_rev.get(key)
				if isinstance(val, dict):
					val = val.get("change") or val.get("revision")
				if isinstance(val, (int, float)) and val > 0:
					strengthening.append("street_catching_up")
					break
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
		"revisions_direction": analyst_rev.get("revisions_direction") if not analyst_rev.get("error") else None,
		"io_quality_score": io_score,
		"sbc_flag": sbc.get("flag") or sbc.get("dilution_flag"),
	}

	return {"strengthening": strengthening, "weakening": weakening, "net_direction": net_direction, "conviction_delta": s_count - w_count, "detail": detail}


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
	earnings_acc = l4.get("earnings_acceleration") or {}
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

	return {"classification": classification, "confidence": confidence, "evidence": evidence, "requires_llm": True,
		"note": "Rule-based pre-classification. Agent should verify and may override."}


def _parse_days_to_earnings(l5_results):
	"""Parse L5 earnings_dates and return days until the nearest future date."""
	if not isinstance(l5_results, dict):
		return None
	ed = l5_results.get("earnings_dates")
	if not isinstance(ed, dict) or ed.get("error"):
		return None
	dates_col = ed.get("Earnings Date", {})
	if not isinstance(dates_col, dict):
		return None
	now = datetime.now()
	min_days = None
	for _idx, date_str in dates_col.items():
		if not isinstance(date_str, str):
			continue
		for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%b %d, %Y"):
			try:
				dt = datetime.strptime(date_str.strip(), fmt)
				delta = (dt - now).days
				if delta >= 0 and (min_days is None or delta < min_days):
					min_days = delta
				break
			except ValueError:
				continue
	return min_days


def _generate_composite_signal(l1_result, l4_results, l5_results, health_severity_score,
	bottleneck_pre_score, thesis_signals, auto_classification, trapped_asset_override):
	"""Generate integrated investment grade from all pipeline data."""
	score_breakdown = {}
	total_score = 0.0

	l1 = l1_result if isinstance(l1_result, dict) else {}
	regime = l1.get("regime", "transitional")

	# Component 1: Bottleneck (30 pts)
	bn = bottleneck_pre_score if isinstance(bottleneck_pre_score, dict) and not (bottleneck_pre_score or {}).get("error") else {}
	bn_raw = bn.get("pre_score", 0) if bn else 0
	if not isinstance(bn_raw, (int, float)):
		bn_raw = 0
	bn_max = bn.get("pre_score_max", 4.25) if bn else 4.25
	bn_points = (bn_raw / bn_max) * 30.0
	score_breakdown["bottleneck"] = {"raw": bn_raw if bn else None, "max": bn_max, "points": round(bn_points, 2)}
	total_score += bn_points

	# Component 2: Health severity (25 pts) — 5 gates (4 original + io_quality_concern)
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

	# Component 4: Catalyst proximity (10 pts)
	days = _parse_days_to_earnings(l5_results)
	cat_points = 10.0 if (days is not None and days <= 30) else 5.0 if (days is not None and days <= 60) else 0.0
	score_breakdown["catalyst"] = {"days_to_earnings": days, "points": round(cat_points, 2)}
	total_score += cat_points

	# Component 5: Taxonomy (10 pts)
	ac = auto_classification if isinstance(auto_classification, dict) else {}
	ac_class = ac.get("classification", "unclassified")
	tax_points = 10.0 if ac_class in ("bottleneck", "disruption") else 7.0 if ac_class == "evolution" else 5.0
	score_breakdown["taxonomy"] = {"classification": ac_class, "points": round(tax_points, 2)}
	total_score += tax_points

	# Component 6: Valuation MoS (10 pts)
	l4 = l4_results if isinstance(l4_results, dict) else {}
	ngv = l4.get("no_growth_valuation") or {}
	if isinstance(ngv, dict) and ngv.get("error"):
		ngv = {}
	mos_pct = ngv.get("margin_of_safety_pct")
	if isinstance(mos_pct, (int, float)):
		val_points = 10.0 if mos_pct > 20 else 5.0 if mos_pct >= 0 else 0.0
		score_breakdown["valuation"] = {"mos_pct": round(mos_pct, 2), "points": round(val_points, 2)}
	else:
		val_points = 0.0
		score_breakdown["valuation"] = {"mos_pct": None, "points": 0.0, "note": "unavailable"}
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

	# Position sizing
	pos_table = {
		"STRONG_BUY": ("High", "5-7%", "1.5%"), "BUY": ("Medium", "2-4%", "1.0%"),
		"ACCUMULATE": ("Low", "1-2%", "0.5%"), "HOLD": (None, "hold_existing", None),
		"AVOID": (None, "no_entry", None), "MOONSHOT": ("Special", "max_5%", "2.5%"),
	}
	conviction, size, max_loss = pos_table.get(grade, (None, "no_entry", None))
	regime_adj = "risk_off_0.5x" if regime == "risk_off" else "transitional_0.75x" if regime == "transitional" else "none"

	return {
		"composite_score": total_score, "grade": grade, "score_breakdown": score_breakdown,
		"position_guidance": {"conviction_tier": conviction, "suggested_size_pct": size, "max_loss_pct": max_loss, "regime_adjustment": regime_adj},
		"regime_cap_applied": regime_cap_applied, "trapped_asset_override_applied": trapped_override_applied,
		"requires_agent_review": True, "note": "Automated composite signal. Agent must review before final rating assignment.",
	}


# ---------------------------------------------------------------------------
# Sector Matching (for theme discovery)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Entity Normalization (for cross-chain analysis)
# ---------------------------------------------------------------------------

_ENTITY_SUFFIXES = re.compile(
	r",?\s*\b(?:Inc\.?|Corp\.?|Corporation|LLC|Ltd\.?|Limited|Co\.?|Company|"
	r"Group|Holdings|Plc\.?|SE|N\.?V\.?|S\.?A\.?|A\.?G\.?|GmbH|KK|"
	r"Kabushiki\s+Kaisha)\b\.?\s*$",
	re.IGNORECASE,
)

_ENTITY_ALIAS_MAP = {
	"tsmc": "taiwan semiconductor manufacturing",
	"taiwan semiconductor manufacturing company": "taiwan semiconductor manufacturing",
	"taiwan semiconductor": "taiwan semiconductor manufacturing",
	"foxconn": "hon hai precision industry",
	"hon hai": "hon hai precision industry",
	"ibm": "international business machines",
	"sk hynix inc": "sk hynix",
	"micron technology inc": "micron technology",
	"samsung electronics co": "samsung electronics",
	"alphabet": "google",
	"alphabet inc": "google",
	"meta platforms": "meta",
	"meta platforms inc": "meta",
	"advanced micro devices": "amd",
	"broadcom inc": "broadcom",
	"texas instruments incorporated": "texas instruments",
	"applied materials inc": "applied materials",
	"lam research corp": "lam research",
	"asml holding": "asml",
	"tokyo electron": "tokyo electron",
}


def _normalize_entity_name(name):
	"""Normalize a company/entity name for fuzzy matching."""
	if not name or not isinstance(name, str):
		return ""
	normalized = name.strip()
	# Remove suffixes (up to 3 iterations for nested suffixes)
	for _ in range(3):
		prev = normalized
		normalized = _ENTITY_SUFFIXES.sub("", normalized).strip()
		if normalized == prev:
			break
	# Lowercase + whitespace normalization
	normalized = re.sub(r"\s+", " ", normalized.lower().strip()).rstrip(".,;:")
	# Apply alias mapping
	return _ENTITY_ALIAS_MAP.get(normalized, normalized)


# ---------------------------------------------------------------------------
# Macro Regime Classification
# ---------------------------------------------------------------------------

def _classify_macro_regime(macro_results):
	"""Classify macro regime based on combined signals.

	Returns:
		dict with regime, risk_level, drain_count, decision_rules
	"""
	erp = macro_results.get("erp", {})
	vix = macro_results.get("vix_curve", {})
	net_liq = macro_results.get("net_liquidity", {})
	fear_greed = macro_results.get("fear_greed", {})
	fedwatch = macro_results.get("fedwatch", {})
	yield_curve = macro_results.get("yield_curve", {})

	# Signal extraction
	erp_healthy = False
	erp_danger = False
	erp_val = None
	if not erp.get("error"):
		erp_val = erp.get("current", {}).get("erp")
		if erp_val is not None:
			erp_healthy = erp_val > 3.0
			erp_danger = erp_val < 1.5

	vix_contango = False
	vix_backwardation = False
	if not vix.get("error"):
		structure = str(vix.get("structure_type", "")).lower()
		vix_contango = "contango" in structure
		vix_backwardation = "backwardation" in structure

	net_liq_positive = False
	if not net_liq.get("error"):
		net_liq_data = net_liq.get("net_liquidity", {})
		trend = str(net_liq_data.get("direction", "")).lower()
		net_liq_positive = "positive" in trend or "rising" in trend or "expanding" in trend

	fear_extreme = False
	fg_val = None
	if not fear_greed.get("error"):
		fg_val = fear_greed.get("current", {}).get("score")
		if fg_val is not None:
			try:
				fear_extreme = float(fg_val) < 25
			except (ValueError, TypeError):
				pass

	# Regime classification
	risk_on_signals = [erp_healthy, vix_contango, net_liq_positive]
	risk_off_signals = [erp_danger, vix_backwardation, fear_extreme]

	risk_on_count = sum(1 for s in risk_on_signals if s)
	risk_off_count = sum(1 for s in risk_off_signals if s)

	if risk_on_count >= 2 and risk_off_count == 0:
		regime = "risk_on"
	elif risk_off_count >= 2 and risk_on_count == 0:
		regime = "risk_off"
	else:
		regime = "transitional"

	# Count negative macro signals (drains)
	drain_count = 0
	decision_rules = []

	if erp.get("error"):
		decision_rules.append("ERP unavailable (script error)")
	elif erp_val is None:
		decision_rules.append("ERP data unavailable")
	elif not erp_healthy:
		drain_count += 1
		decision_rules.append(f"ERP at {erp_val:.2f}% — below healthy threshold (>3%)")
	else:
		decision_rules.append(f"ERP healthy at {erp_val:.2f}%")

	if vix_backwardation:
		drain_count += 1
		decision_rules.append("VIX in backwardation — elevated near-term fear")
	elif vix_contango:
		decision_rules.append("VIX contango — normal risk appetite")

	if not net_liq_positive and not net_liq.get("error"):
		drain_count += 1
		decision_rules.append("Net liquidity contracting or neutral")
	elif net_liq_positive:
		decision_rules.append("Net liquidity expanding — supportive for risk assets")

	if fear_greed.get("error"):
		decision_rules.append("Fear & Greed unavailable (script error)")
	elif fg_val is None:
		decision_rules.append("Fear & Greed data unavailable")
	elif fear_extreme:
		drain_count += 1
		decision_rules.append(f"Fear & Greed at {float(fg_val):.0f} — extreme fear levels (<25)")
	else:
		decision_rules.append(f"Sentiment at {float(fg_val):.0f} — within normal range")

	if not fedwatch.get("error"):
		decision_rules.append("Fed rate path data available for context")

	if not yield_curve.get("error"):
		inversion = yield_curve.get("inverted") or yield_curve.get("spread_10y_2y")
		if inversion is not None:
			if isinstance(inversion, bool) and inversion:
				drain_count += 1
				decision_rules.append("Yield curve inverted — recession signal")
			elif isinstance(inversion, (int, float)) and inversion < 0:
				drain_count += 1
				decision_rules.append(f"Yield curve inverted (10Y-2Y spread: {inversion:.2f}%)")
			else:
				decision_rules.append("Yield curve normal")

	# BDI signal (always included in v4.0)
	bdi = macro_results.get("bdi", {})
	if not bdi.get("error"):
		bdi_z = bdi.get("statistics", {}).get("z_score")
		if isinstance(bdi_z, (int, float)):
			if bdi_z < -2:
				drain_count += 1
				decision_rules.append(f"BDI z-score {bdi_z:.2f} — extreme shipping demand weakness")
			elif bdi_z < -1:
				decision_rules.append(f"BDI z-score {bdi_z:.2f} — below-average shipping demand")
			else:
				decision_rules.append(f"BDI z-score {bdi_z:.2f} — shipping demand normal/elevated")

	# DXY signal (always included in v4.0)
	dxy = macro_results.get("dxy", {})
	if not dxy.get("error"):
		dxy_z = dxy.get("statistics", {}).get("z_score")
		if isinstance(dxy_z, (int, float)):
			if dxy_z > 2:
				drain_count += 1
				decision_rules.append(f"DXY z-score {dxy_z:.2f} — extremely strong dollar pressures risk assets")
			elif dxy_z > 1:
				decision_rules.append(f"DXY z-score {dxy_z:.2f} — strong dollar")
			else:
				decision_rules.append(f"DXY z-score {dxy_z:.2f} — dollar within normal range")

	# Real rates signal
	real_rate = macro_results.get("real_rate")
	if isinstance(real_rate, (int, float)):
		if real_rate < 0:
			decision_rules.append(f"Real rate {real_rate:.2f}% — negative, liquidity supportive")
		else:
			decision_rules.append(f"Real rate {real_rate:.2f}% — positive, tighter conditions")

	# Risk level
	if drain_count == 0:
		risk_level = "low"
	elif drain_count <= 1:
		risk_level = "moderate"
	elif drain_count <= 3:
		risk_level = "elevated"
	else:
		risk_level = "high"

	return {
		"regime": regime,
		"risk_level": risk_level,
		"drain_count": drain_count,
		"decision_rules": decision_rules,
	}


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@safe_run
def cmd_macro(args):
	"""Level 1 Macro Regime Assessment.

	Runs macro scripts in parallel to assess the current risk environment.
	Classifies regime as risk_on, risk_off, or transitional.
	"""
	scripts = {
		"net_liquidity": ("macro/net_liquidity.py", ["net-liquidity", "--limit", "10"]),
		"vix_curve": ("macro/vix_curve.py", ["analyze"]),
		"fedwatch": ("data_advanced/fed/fedwatch.py", []),
		"yield_curve": ("data_advanced/fred/rates.py", ["yield-curve", "--limit", "5"]),
		"erp": ("macro/erp.py", ["erp"]),
		"fear_greed": ("analysis/sentiment/fear_greed.py", []),
		"dxy": ("data_sources/dxy.py", []),
		"bdi": ("data_sources/bdi.py", []),
		"breakeven_inflation": ("data_advanced/fred/inflation.py", ["breakeven-inflation", "--maturity", "10y", "--limit", "5"]),
		"nominal_rates": ("data_advanced/fred/rates.py", ["yield-curve", "--maturities", "10y", "--limit", "5"]),
	}

	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		futures = {
			name: executor.submit(_run_script, path, a)
			for name, (path, a) in scripts.items()
		}
		results = {name: future.result() for name, future in futures.items()}

	# Compute real rate from nominal - breakeven inflation (before regime classification)
	real_rate = None
	nominal_data = results.get("nominal_rates", {})
	breakeven_data = results.get("breakeven_inflation", {})
	try:
		nominal_series = nominal_data.get("data", {})
		breakeven_series = breakeven_data.get("data", {})
		nominal_val = None
		for _sid, vals in nominal_series.items():
			if isinstance(vals, dict) and not vals.get("error"):
				for _date, v in sorted(vals.items(), reverse=True):
					if v is not None:
						nominal_val = v
						break
				break
		breakeven_val = None
		for _sid, vals in breakeven_series.items():
			if isinstance(vals, dict) and not vals.get("error"):
				for _date, v in sorted(vals.items(), reverse=True):
					if v is not None:
						breakeven_val = v
						break
				break
		if isinstance(nominal_val, (int, float)) and isinstance(breakeven_val, (int, float)):
			real_rate = round(nominal_val - breakeven_val, 4)
			results["real_rate"] = real_rate
	except Exception:
		pass

	# Classify regime (after real_rate is available in results)
	classification = _classify_macro_regime(results)

	signals = {
		"erp_pct": results.get("erp", {}).get("current", {}).get("erp"),
		"vix_spot": results.get("vix_curve", {}).get("vix_spot"),
		"vix_regime": results.get("vix_curve", {}).get("regime"),
		"vix_structure": results.get("vix_curve", {}).get("structure_type"),
		"net_liq_direction": results.get("net_liquidity", {})
			.get("net_liquidity", {}).get("direction"),
		"net_liq_current": results.get("net_liquidity", {})
			.get("net_liquidity", {}).get("current"),
		"fear_greed": results.get("fear_greed", {}).get("current", {}).get("score"),
		"fedwatch_next_meeting": results.get("fedwatch", {}).get("next_meeting"),
		"fedwatch_probabilities": results.get("fedwatch", {}).get("probabilities"),
	}

	# BDI/DXY always included (v4.0)
	bdi = results.get("bdi", {})
	if not bdi.get("error"):
		signals["bdi_z_score"] = bdi.get("statistics", {}).get("z_score")
		signals["bdi_demand"] = bdi.get("shipping_demand")
		if args.extended:
			signals["bdi"] = bdi
	dxy = results.get("dxy", {})
	if not dxy.get("error"):
		signals["dxy_z_score"] = dxy.get("statistics", {}).get("z_score")
		signals["dxy_strength"] = dxy.get("dollar_strength")
		if args.extended:
			signals["dxy"] = dxy

	# Real rate
	if real_rate is not None:
		signals["real_rate"] = real_rate

	output = {
		"regime": classification["regime"],
		"risk_level": classification["risk_level"],
		"drain_count": classification["drain_count"],
		"decision_rules": classification["decision_rules"],
		"signals": signals,
	}

	output_json(output)


@safe_run
def cmd_analyze(args):
	"""Full 6-Level Analysis for a single ticker.

	Auto-executes L1 (macro), L4 (fundamentals), L5 (catalysts).
	L2 (CapEx Flow) and L3 (Bottleneck) require agent context.
	L6 (Taxonomy) requires LLM classification.
	Extracts health gates from L4 results.
	"""
	ticker = args.ticker.upper()

	# --- Level 1: Macro Regime ---
	l1_result = None
	if not args.skip_macro:
		macro_scripts = {
			"net_liquidity": ("macro/net_liquidity.py", ["net-liquidity", "--limit", "10"]),
			"vix_curve": ("macro/vix_curve.py", ["analyze"]),
			"fedwatch": ("data_advanced/fed/fedwatch.py", []),
			"yield_curve": ("data_advanced/fred/rates.py", ["yield-curve", "--limit", "5"]),
			"erp": ("macro/erp.py", ["erp"]),
			"fear_greed": ("analysis/sentiment/fear_greed.py", []),
			"dxy": ("data_sources/dxy.py", []),
			"bdi": ("data_sources/bdi.py", []),
			"breakeven_inflation": ("data_advanced/fred/inflation.py", ["breakeven-inflation", "--maturity", "10y", "--limit", "5"]),
			"nominal_rates": ("data_advanced/fred/rates.py", ["yield-curve", "--maturities", "10y", "--limit", "5"]),
		}

		with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
			futures = {
				name: executor.submit(_run_script, path, a)
				for name, (path, a) in macro_scripts.items()
			}
			macro_results = {name: future.result() for name, future in futures.items()}

		# Compute real rate from nominal - breakeven inflation
		real_rate = None
		nominal_data = macro_results.get("nominal_rates", {})
		breakeven_data = macro_results.get("breakeven_inflation", {})
		try:
			nominal_series = nominal_data.get("data", {})
			breakeven_series = breakeven_data.get("data", {})
			nominal_val = None
			for _sid, vals in nominal_series.items():
				if isinstance(vals, dict) and not vals.get("error"):
					for _date, v in sorted(vals.items(), reverse=True):
						if v is not None:
							nominal_val = v
							break
					break
			breakeven_val = None
			for _sid, vals in breakeven_series.items():
				if isinstance(vals, dict) and not vals.get("error"):
					for _date, v in sorted(vals.items(), reverse=True):
						if v is not None:
							breakeven_val = v
							break
					break
			if isinstance(nominal_val, (int, float)) and isinstance(breakeven_val, (int, float)):
				real_rate = round(nominal_val - breakeven_val, 4)
				macro_results["real_rate"] = real_rate
		except Exception:
			pass

		classification = _classify_macro_regime(macro_results)
		signals = {
			"erp_pct": macro_results.get("erp", {}).get("current", {}).get("erp"),
			"vix_spot": macro_results.get("vix_curve", {}).get("vix_spot"),
			"vix_regime": macro_results.get("vix_curve", {}).get("regime"),
			"vix_structure": macro_results.get("vix_curve", {}).get("structure_type"),
			"net_liq_direction": macro_results.get("net_liquidity", {})
				.get("net_liquidity", {}).get("direction"),
			"net_liq_current": macro_results.get("net_liquidity", {})
				.get("net_liquidity", {}).get("current"),
			"fear_greed": macro_results.get("fear_greed", {}).get("current", {}).get("score"),
			"fedwatch_next_meeting": macro_results.get("fedwatch", {}).get("next_meeting"),
			"fedwatch_probabilities": macro_results.get("fedwatch", {}).get("probabilities"),
		}
		bdi = macro_results.get("bdi", {})
		if not bdi.get("error"):
			signals["bdi_z_score"] = bdi.get("statistics", {}).get("z_score")
			signals["bdi_demand"] = bdi.get("shipping_demand")
		dxy = macro_results.get("dxy", {})
		if not dxy.get("error"):
			signals["dxy_z_score"] = dxy.get("statistics", {}).get("z_score")
			signals["dxy_strength"] = dxy.get("dollar_strength")
		if real_rate is not None:
			signals["real_rate"] = real_rate
		l1_result = {
			"regime": classification["regime"],
			"risk_level": classification["risk_level"],
			"drain_count": classification["drain_count"],
			"decision_rules": classification["decision_rules"],
			"signals": signals,
		}

	# --- Level 4: Position Construction (Fundamentals) ---
	insider_start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
	l4_scripts = {
		"info": ("data_sources/info.py", ["get-info-fields", ticker,
			"sector", "industry", "marketCap", "enterpriseValue",
			"fullTimeEmployees", "longBusinessSummary", "financialCurrency",
			"fiftyTwoWeekLow", "fiftyTwoWeekHigh", "beta",
			"currentPrice", "forwardPE", "priceToSalesTrailing12Months",
			"sharesOutstanding", "floatShares", "shortPercentOfFloat",
			"previousClose", "fiftyDayAverage", "twoHundredDayAverage",
			"grossMargins", "operatingMargins",
			"heldPercentInsiders", "heldPercentInstitutions"]),
		"holders": ("data_sources/holders.py", ["get-institutional-holders", ticker]),
		"insider_transactions": ("data_sources/holders.py", [
			"get-insider-transactions", ticker, "--exclude-grants",
			"--start", insider_start]),
		"earnings_acceleration": ("data_sources/earnings_acceleration.py", ["code33", ticker]),
		"sbc_analyzer": ("analysis/sbc_analyzer.py", ["get-sbc", ticker]),
		"forward_pe": ("analysis/forward_pe.py", ["calculate", ticker]),
		"debt_structure": ("analysis/debt_structure.py", ["analyze", ticker]),
		"institutional_quality": ("analysis/institutional_quality.py", ["score", ticker]),
		"no_growth_valuation": ("analysis/no_growth_valuation.py", ["calculate", ticker]),
		"margin_tracker": ("analysis/margin_tracker.py", ["track", ticker]),
		"iv_context": ("analysis/iv_context.py", ["analyze", ticker]),
		"capex_trend": ("analysis/capex_tracker.py", ["track", ticker, "--quarters", "8"]),
		"quarterly_financials": ("data_sources/financials.py", [
			"get-income-stmt", ticker, "--freq", "quarterly"]),
	}

	# --- Level 5: Catalyst Monitoring ---
	l5_scripts = {
		"earnings_dates": ("data_sources/actions.py", ["get-earnings-dates", ticker, "--limit", "8"]),
		"earnings_surprise": ("data_sources/earnings_acceleration.py", ["surprise", ticker]),
		"analyst_recommendations": ("analysis/analysis.py", ["get-recommendations-summary", ticker]),
		"analyst_price_targets": ("analysis/analysis.py", ["get-analyst-price-targets", ticker]),
		"analyst_revisions": ("data_sources/earnings_acceleration.py", ["revisions", ticker]),
	}

	# --- SEC Supply Chain Intelligence (L3 pre-extraction) ---
	sec_sc_scripts = {
		"sec_supply_chain": ("data_advanced/sec/supply_chain.py", ["supply-chain", ticker], 120),
		"sec_events": ("data_advanced/sec/supply_chain.py", ["events", ticker, "--limit", "5", "--days", "180"], 120),
	}

	# --- Hyperscaler CapEx Bridge (L2) ---
	hyperscaler_tickers = ["MSFT", "GOOG", "META", "AMZN"]
	hs_scripts = {
		f"hs_capex_{t}": ("analysis/capex_tracker.py", ["track", t, "--quarters", "4"])
		for t in hyperscaler_tickers
	}

	# Run L4, L5, SEC supply chain, and Hyperscaler CapEx in parallel
	all_scripts = {}
	all_scripts.update(l4_scripts)
	all_scripts.update(l5_scripts)
	all_scripts.update(sec_sc_scripts)
	all_scripts.update(hs_scripts)

	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		futures = {}
		for name, spec in all_scripts.items():
			path, a = spec[0], spec[1]
			t = spec[2] if len(spec) > 2 else 60
			futures[name] = executor.submit(_run_script, path, a, t)
		all_results = {name: future.result() for name, future in futures.items()}

	# Split results
	l4_results = {k: all_results[k] for k in l4_scripts}
	l5_results = {k: all_results[k] for k in l5_scripts}
	sec_sc_results = {k: all_results[k] for k in sec_sc_scripts}

	# Build Hyperscaler CapEx Bridge Signal (Change J)
	hyperscaler_signal = None
	hs_directions = []
	for t in hyperscaler_tickers:
		hs_result = all_results.get(f"hs_capex_{t}", {})
		if not hs_result.get("error"):
			symbols_data = hs_result.get("symbols", [])
			sym_data = symbols_data[0] if symbols_data else {}
			direction = sym_data.get("direction", "unknown")
			if direction and direction != "unknown":
				hs_directions.append(direction)
	if hs_directions:
		hs_inc = sum(1 for d in hs_directions if d.lower() in ("increasing", "up", "accelerating"))
		hyperscaler_signal = {
			"aggregate_direction": "increasing" if hs_inc > len(hs_directions) / 2 else "decreasing" if hs_inc == 0 else "mixed",
			"increasing_count": hs_inc,
			"total_count": len(hs_directions),
		}

	# Post-process: insider transactions summary
	insider_raw = l4_results.get("insider_transactions")
	if insider_raw and not (isinstance(insider_raw, dict) and insider_raw.get("error")):
		l4_results["insider_transactions"] = _summarize_insider_transactions(insider_raw)

	# Post-process: extract revenue trajectory from quarterly financials
	financials_raw = l4_results.pop("quarterly_financials", None)
	if financials_raw and not (isinstance(financials_raw, dict) and financials_raw.get("error")):
		l4_results["revenue_trajectory"] = _extract_revenue_trajectory(financials_raw)

	# Post-process: compress earnings_acceleration
	ea_raw = l4_results.get("earnings_acceleration")
	if ea_raw and not (isinstance(ea_raw, dict) and ea_raw.get("error")):
		l4_results["earnings_acceleration"] = _compress_earnings_acceleration(ea_raw)

	# Post-process: summarize holders
	holders_raw = l4_results.get("holders")
	if holders_raw and not (isinstance(holders_raw, dict) and holders_raw.get("error")):
		l4_results["holders"] = _summarize_holders(holders_raw)

	# Post-process: cap earnings_dates to 8 most recent
	ed_raw = l5_results.get("earnings_dates")
	if ed_raw and not (isinstance(ed_raw, dict) and ed_raw.get("error")):
		l5_results["earnings_dates"] = _cap_earnings_dates(ed_raw)

	# Post-process: move capex_trend from L4 to L2
	capex_data = l4_results.pop("capex_trend", None)

	# Health gates (extracted from L4)
	health_gates = _extract_health_gates(l4_results)

	# Conditional SEC filing check for active dilution
	sec_filing_result = None
	if "active_dilution" in health_gates.get("flags", []):
		sec_filing_result = _run_script(
			"data_advanced/sec/filings.py",
			[ticker, "--form", "S-3", "--limit", "5"]
		)
		if sec_filing_result and not sec_filing_result.get("error"):
			l4_results["sec_dilution_check"] = sec_filing_result

	# Valuation summary
	valuation_summary = _build_valuation_summary(l4_results)

	# L3 Bottleneck (call before output to get pre_score for downstream)
	l3_data = _build_l3_bottleneck(sec_sc_results)
	bottleneck_pre_score = l3_data.get("bottleneck_pre_score")

	# Thesis signals (Change D)
	thesis_signals = _build_thesis_signals(l4_results, l5_results)

	# SoP triggers (Change E)
	sop_triggers = _check_sop_triggers(l4_results)

	# Trapped asset override (Change F)
	trapped_asset_override = _check_trapped_asset_override(l4_results, bottleneck_pre_score, sec_sc_results)

	# L6 auto-classification (Change G)
	auto_classification = _auto_classify_taxonomy(l4_results, bottleneck_pre_score)

	# Composite signal + position sizing (Change H+I)
	composite_signal = _generate_composite_signal(
		l1_result, l4_results, l5_results,
		health_gates.get("severity_score"),
		bottleneck_pre_score, thesis_signals,
		auto_classification, trapped_asset_override,
	)

	# Fundamental readiness codes
	readiness_codes = _build_readiness_codes(
		health_gates, valuation_summary, l4_results,
		l5_results=l5_results, sec_result=sec_filing_result,
		sec_sc_results=sec_sc_results,
		bottleneck_pre_score=bottleneck_pre_score,
		composite_signal=composite_signal,
	)

	output = {
		"ticker": ticker,
		"levels": {
			"L1_macro": l1_result if l1_result else {"skipped": True},
			"L2_capex_flow": {
				"company_capex": capex_data,
				"hyperscaler_signal": hyperscaler_signal,
				"cascade_requires_context": True,
				"note": "Company CapEx and Hyperscaler CapEx bridge signal auto-included. Supply chain cascade requires agent context.",
			},
			"L3_bottleneck": l3_data,
			"L4_fundamentals": l4_results,
			"L5_catalysts": l5_results,
			"L6_taxonomy": auto_classification,
		},
		"health_gates": health_gates,
		"thesis_signals": thesis_signals,
		"sop_triggers": sop_triggers,
		"trapped_asset_override": trapped_asset_override,
		"composite_signal": composite_signal,
		"valuation_summary": valuation_summary,
		"fundamental_readiness_codes": readiness_codes,
	}

	output_json(output)


@safe_run
def cmd_recheck(args):
	"""Position Monitoring Recheck.

	Runs macro regime, health gates, and thesis signal checks against an
	existing position. Compares current state to expected healthy conditions
	and generates action signals with a verdict.
	"""
	ticker = args.ticker.upper()
	entry_price = float(args.entry_price)

	# Step 1: Get current price and 52W range
	price_result = _run_script(
		"data_sources/info.py",
		["get-info-fields", ticker, "currentPrice",
		 "fiftyTwoWeekLow", "fiftyTwoWeekHigh"],
	)

	current_price = None
	fifty_two_low = None
	fifty_two_high = None
	if not price_result.get("error"):
		current_price = price_result.get("currentPrice")
		fifty_two_low = price_result.get("fiftyTwoWeekLow")
		fifty_two_high = price_result.get("fiftyTwoWeekHigh")

	# Step 2: Run macro + L4/L5 scripts in parallel
	macro_scripts = {
		"erp": ("macro/erp.py", ["erp"]),
		"vix_curve": ("macro/vix_curve.py", ["analyze"]),
		"fear_greed": ("analysis/sentiment/fear_greed.py", []),
		"net_liquidity": ("macro/net_liquidity.py", ["net-liquidity", "--limit", "10"]),
		"fedwatch": ("data_advanced/fed/fedwatch.py", []),
		"yield_curve": ("data_advanced/fred/rates.py", ["yield-curve", "--limit", "5"]),
	}

	l4_scripts = {
		"debt_structure": ("analysis/debt_structure.py", ["analyze", ticker]),
		"sbc_analyzer": ("analysis/sbc_analyzer.py", ["get-sbc", ticker]),
		"no_growth_valuation": ("analysis/no_growth_valuation.py", ["calculate", ticker]),
		"margin_tracker": ("analysis/margin_tracker.py", ["track", ticker]),
		"forward_pe": ("analysis/forward_pe.py", ["calculate", ticker]),
		"earnings_acceleration": ("data_sources/earnings_acceleration.py", ["code33", ticker]),
		"institutional_quality": ("analysis/institutional_quality.py", ["score", ticker]),
	}

	l5_scripts = {
		"earnings_surprise": ("data_sources/earnings_acceleration.py", ["surprise", ticker]),
		"analyst_revisions": ("data_sources/earnings_acceleration.py", ["revisions", ticker]),
	}

	all_scripts = {}
	all_scripts.update(macro_scripts)
	all_scripts.update(l4_scripts)
	all_scripts.update(l5_scripts)

	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		futures = {}
		for name, spec in all_scripts.items():
			path, a = spec[0], spec[1]
			t = spec[2] if len(spec) > 2 else 60
			futures[name] = executor.submit(_run_script, path, a, t)
		all_results = {name: future.result() for name, future in futures.items()}

	macro_results = {k: all_results[k] for k in macro_scripts}
	l4_results = {k: all_results[k] for k in l4_scripts}
	l5_results = {k: all_results[k] for k in l5_scripts}

	# Step 3: Classify macro regime
	macro_classification = _classify_macro_regime(macro_results)

	# Step 4: Extract health gates
	health_gates = _extract_health_gates(l4_results)

	# Step 5: Build thesis signals
	thesis_signals = _build_thesis_signals(l4_results, l5_results)

	# Step 6: Calculate return and 52W position
	return_pct = None
	if isinstance(current_price, (int, float)) and entry_price > 0:
		return_pct = round((current_price - entry_price) / entry_price * 100, 2)

	position_52w = None
	if (
		isinstance(current_price, (int, float))
		and isinstance(fifty_two_low, (int, float))
		and isinstance(fifty_two_high, (int, float))
		and fifty_two_high > fifty_two_low
	):
		position_52w = round(
			(current_price - fifty_two_low) / (fifty_two_high - fifty_two_low) * 100,
			1,
		)

	# Step 7: Detect action signals
	action_signals = []

	if macro_classification.get("regime") == "risk_off":
		action_signals.append("MACRO_REGIME_RISK_OFF")

	for gate_name in ("bear_bull_paradox", "active_dilution",
					  "no_growth_fail", "margin_collapse"):
		if health_gates.get(gate_name) == "FLAG":
			action_signals.append(f"{gate_name.upper()}_DEGRADED")

	if thesis_signals.get("net_direction") == "weakening":
		action_signals.append("THESIS_WEAKENING")

	if len(health_gates.get("flags", [])) >= 2:
		action_signals.append("MULTIPLE_GATES_FLAGGED")

	# Step 8: Verdict
	signal_count = len(action_signals)
	if signal_count == 0:
		verdict = "MAINTAIN"
		note = "No concerns detected. Position health is good."
	elif signal_count == 1:
		verdict = "HOLD_MONITOR"
		note = f"1 concern detected: {action_signals[0]}. Monitor for further deterioration."
	elif signal_count == 2:
		verdict = "HOLD_REDUCE"
		note = f"2 concerns detected: {', '.join(action_signals)}. Consider reducing position size."
	else:
		verdict = "CONSIDER_EXIT"
		note = (f"{signal_count} concerns detected: {', '.join(action_signals)}. "
				"Strongly consider exiting or hedging the position.")

	entry_date = getattr(args, "entry_date", None)
	output_json({
		"ticker": ticker,
		"entry_price": entry_price,
		"entry_date": entry_date,
		"current_price": current_price,
		"return_pct": return_pct,
		"position_52w": position_52w,
		"macro_regime": {
			"regime": macro_classification.get("regime"),
			"risk_level": macro_classification.get("risk_level"),
			"drain_count": macro_classification.get("drain_count"),
		},
		"health_gates": health_gates,
		"thesis_signals": thesis_signals,
		"action_signals": action_signals,
		"verdict": verdict,
		"note": note,
	})


@safe_run
def cmd_discover(args):
	"""Automated Theme Discovery — surface top industry groups with bottleneck candidates.

	Phase 1: Runs sector_leaders scan to identify top industry groups by leader_count.
	Phase 2: Runs finviz industry-screen for each top group in parallel to get
	candidates with exact industry matching.
	Phase 3: Applies max_mcap filter, then validates each candidate with
	bottleneck_scorer. Groups results by theme/industry_group sorted by
	asymmetry_score.

	When --industry is provided, skips Phase 1 (sector_leaders) and directly
	runs finviz industry-screen for the specified industry. Useful for thematic
	discovery where the agent already knows the target industry.
	"""
	top_groups = getattr(args, "top_groups", 5)
	max_mcap = getattr(args, "max_mcap", "10B")
	limit = getattr(args, "limit", 10)
	industry = getattr(args, "industry", None)
	max_mcap_val = _parse_mcap_string(max_mcap)

	# Direct industry mode — skip sector_leaders, go straight to finviz
	if industry:
		fv_result = _run_script("screening/finviz.py",
			["industry-screen", "--industry", industry, "--limit", "30"])

		if fv_result.get("error"):
			output_json({
				"themes": [], "total_themes": 0, "total_candidates": 0,
				"filters_applied": {"industry": industry, "max_mcap": max_mcap},
				"requires_agent_review": False,
				"note": f"finviz industry-screen failed for '{industry}'.",
				"degraded": True,
			})
			return

		raw_candidates = fv_result.get("data", [])
		filtered = []
		for row in raw_candidates:
			t = row.get("Ticker") or row.get("ticker")
			if not t:
				continue
			raw_mcap = row.get("Market Cap") or row.get("market_cap")
			mcap_str = str(int(round(float(raw_mcap)))) if raw_mcap else None
			if max_mcap_val is not None and mcap_str:
				row_mcap = _parse_mcap_string(mcap_str)
				if row_mcap is not None and row_mcap > max_mcap_val:
					continue
			filtered.append((t, mcap_str))

		if not filtered:
			output_json({
				"themes": [], "total_themes": 0, "total_candidates": 0,
				"filters_applied": {"industry": industry, "max_mcap": max_mcap},
				"requires_agent_review": False,
				"note": f"No candidates passed mcap filter for '{industry}'.",
			})
			return

		filtered = filtered[:limit]

		with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
			bn_futures = {
				t: executor.submit(_run_script, "analysis/bottleneck_scorer.py",
					["validate", t, "--bottleneck-score", "5"])
				for t, _ in filtered
			}
			bn_results = {t: f.result() for t, f in bn_futures.items()}

		candidates = []
		for t, mcap_str in filtered:
			validation = bn_results.get(t, {})
			candidate = {"ticker": t, "market_cap": mcap_str}
			if not validation.get("error"):
				candidate["asymmetry_score"] = validation.get("asymmetry_score")
				candidate["health_gates"] = validation.get("health_gates", {})
			else:
				candidate["asymmetry_score"] = None
				candidate["health_gates"] = {"error": validation.get("error", "Validation failed")}
			candidates.append(candidate)

		candidates.sort(
			key=lambda c: c.get("asymmetry_score") if c.get("asymmetry_score") is not None else -999,
			reverse=True,
		)

		output_json({
			"themes": [{
				"industry_group": industry,
				"sector": "Direct Search",
				"leader_count": None,
				"candidates": candidates,
			}],
			"total_themes": 1,
			"total_candidates": len(candidates),
			"filters_applied": {"industry": industry, "max_mcap": max_mcap},
			"requires_agent_review": True,
			"note": f"Direct industry search for '{industry}'. Agent should evaluate supply chain relevance.",
		})
		return

	# Phase 1: Run sector_leaders scan
	leaders_result = _run_script("screening/sector_leaders.py", ["scan"])
	leaders_degraded = bool(leaders_result.get("error"))

	# Extract top industry groups by leader_count
	top_industry_groups = []
	if not leaders_degraded:
		leaders_list = leaders_result.get("leadership_dashboard", [])
		leaders_list.sort(
			key=lambda g: g.get("leader_count", 0) if isinstance(g.get("leader_count"), (int, float)) else 0,
			reverse=True,
		)
		top_industry_groups = leaders_list[:top_groups]

	if not top_industry_groups:
		output_json({
			"themes": [], "total_themes": 0, "total_candidates": 0,
			"filters_applied": {"max_mcap": max_mcap, "top_groups": top_groups},
			"requires_agent_review": False,
			"note": "sector_leaders scan returned no groups." if leaders_degraded else "No industry groups found.",
			"degraded": leaders_degraded,
		})
		return

	# Phase 2: Run finviz industry-screen for each top group in parallel
	with concurrent.futures.ThreadPoolExecutor(max_workers=len(top_industry_groups)) as executor:
		fv_futures = {
			group["industry_group"]: executor.submit(
				_run_script, "screening/finviz.py",
				["industry-screen", "--industry", group["industry_group"], "--limit", "30"],
			)
			for group in top_industry_groups
		}
		finviz_results = {name: f.result() for name, f in fv_futures.items()}

	# Phase 3: Build theme candidates with mcap filter
	theme_candidates = []
	for group in top_industry_groups:
		group_name = group["industry_group"]
		leader_count = group.get("leader_count", 0)
		leader_tickers = group.get("leader_tickers", [])

		fv_result = finviz_results.get(group_name, {})
		if fv_result.get("error"):
			# Fallback to leader_tickers from sector_leaders
			raw_candidates = [{"Ticker": t} for t in leader_tickers] if leader_tickers else []
		else:
			raw_candidates = fv_result.get("data", [])

		# Apply mcap filter
		filtered = []
		for row in raw_candidates:
			t = row.get("Ticker") or row.get("ticker")
			if not t:
				continue
			raw_mcap = row.get("Market Cap") or row.get("market_cap")
			mcap_str = str(int(round(float(raw_mcap)))) if raw_mcap else None
			if max_mcap_val is not None and mcap_str:
				row_mcap = _parse_mcap_string(mcap_str)
				if row_mcap is not None and row_mcap > max_mcap_val:
					continue
			filtered.append((t, mcap_str))

		if filtered:
			theme_candidates.append({
				"industry_group": group_name,
				"sector": group.get("sector", "Unknown"),
				"leader_count": leader_count,
				"raw_tickers": filtered,
			})

	# Apply per-theme limit (--limit is per theme, not global)
	all_tickers = []
	seen = set()
	for idx, theme in enumerate(theme_candidates):
		count = 0
		for t, mcap_str in theme["raw_tickers"]:
			if t not in seen and count < limit:
				all_tickers.append((idx, t, mcap_str))
				seen.add(t)
				count += 1

	if not all_tickers:
		output_json({
			"themes": [], "total_themes": 0, "total_candidates": 0,
			"filters_applied": {"max_mcap": max_mcap, "top_groups": top_groups},
			"requires_agent_review": False,
			"note": "No candidates passed mcap filter.",
		})
		return

	# Phase 4: Validate with bottleneck_scorer in parallel
	ticker_list = [entry[1] for entry in all_tickers]
	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		bn_futures = {
			t: executor.submit(_run_script, "analysis/bottleneck_scorer.py", ["validate", t, "--bottleneck-score", "5"])
			for t in ticker_list
		}
		bn_results = {t: f.result() for t, f in bn_futures.items()}

	# Phase 5: Group results by theme and sort by asymmetry_score
	group_candidates = {}
	for group_idx, t, mcap_str in all_tickers:
		validation = bn_results.get(t, {})
		candidate = {"ticker": t, "market_cap": mcap_str}
		if not validation.get("error"):
			candidate["asymmetry_score"] = validation.get("asymmetry_score")
			candidate["health_gates"] = validation.get("health_gates", {})
		else:
			candidate["asymmetry_score"] = None
			candidate["health_gates"] = {"error": validation.get("error", "Validation failed")}
		group_candidates.setdefault(group_idx, []).append(candidate)

	for idx in group_candidates:
		group_candidates[idx].sort(
			key=lambda c: c.get("asymmetry_score") if c.get("asymmetry_score") is not None else -999,
			reverse=True,
		)

	themes = []
	for idx, theme in enumerate(theme_candidates):
		candidates = group_candidates.get(idx, [])
		if candidates:
			themes.append({
				"industry_group": theme["industry_group"],
				"sector": theme["sector"],
				"leader_count": theme["leader_count"],
				"candidates": candidates,
			})

	output = {
		"themes": themes,
		"total_themes": len(themes),
		"total_candidates": sum(len(t["candidates"]) for t in themes),
		"filters_applied": {"max_mcap": max_mcap, "top_groups": top_groups},
		"requires_agent_review": True,
		"note": "Automated theme discovery. Agent should evaluate supply chain relevance and apply 6-Criteria Scoring to promising candidates.",
	}

	output_json(output)


@safe_run
def cmd_cross_chain(args):
	"""Cross-analyze SEC supply chain data across multiple tickers to find shared suppliers.

	Extracts supplier, customer, and single-source dependency entities from SEC
	filings for each ticker, normalizes entity names, and identifies shared
	entities referenced by 2+ tickers. Calculates supply chain overlap metrics.
	Each shared entity is scored for bottleneck potential via bottleneck_signal
	(supplier_ref_count, supplier_ref_pct, single_source_count, assessment).
	Results sorted by supplier_ref_count descending.
	"""
	tickers = [t.upper() for t in args.tickers]
	form_type = getattr(args, "form", "10-K")

	# Step 1: Run SEC supply_chain extraction for each ticker
	# Sequential to respect Gemini API rate limits (TPM)
	sec_results = {}
	for t in tickers:
		sec_results[t] = _run_script(
			"data_advanced/sec/supply_chain.py",
			["supply-chain", t, "--form", form_type],
			300,
		)

	# Step 2: Extract and normalize entities from each ticker
	entity_map = {}
	per_ticker_stats = {}
	failed_tickers = []

	for t in tickers:
		result = sec_results[t]
		if result.get("error"):
			per_ticker_stats[t] = {"error": "SEC data unavailable"}
			failed_tickers.append(t)
			continue

		try:
			supply_chain = result["data"]["supply_chain"]
		except (KeyError, TypeError):
			per_ticker_stats[t] = {"error": "SEC data unavailable"}
			failed_tickers.append(t)
			continue

		ticker_entities = {}

		for category, role in [("suppliers", "supplier"), ("single_source_dependencies", "single_source"), ("customers", "customer"), ("revenue_concentration", "customer_concentrated")]:
			entries = supply_chain.get(category) or []
			for entry in entries:
				if isinstance(entry, str):
					name = entry
				elif isinstance(entry, dict):
					name = entry.get("entity", "") or entry.get("supplier", "") or entry.get("name", "")
				else:
					continue
				norm = _normalize_entity_name(name)
				if not norm:
					continue
				if norm not in ticker_entities:
					ticker_entities[norm] = {"roles": set(), "original_names": set()}
				ticker_entities[norm]["roles"].add(role)
				ticker_entities[norm]["original_names"].add(name.strip())
				# Store revenue_pct for customer_concentrated entries
				if category == "revenue_concentration" and isinstance(entry, dict) and entry.get("revenue_pct"):
					ticker_entities[norm]["revenue_pct"] = entry["revenue_pct"]

		supplier_count = len([n for n, info in ticker_entities.items() if "supplier" in info["roles"] or "single_source" in info["roles"]])
		per_ticker_stats[t] = {"supplier_count": supplier_count, "total_entities": len(ticker_entities)}

		for norm, info in ticker_entities.items():
			if norm not in entity_map:
				entity_map[norm] = {}
			entity_map[norm][t] = {"roles": info["roles"], "original_names": info["original_names"]}

	# Step 2.5: Merge similar entity names across tickers (token-based)
	merged = {}
	all_norms = list(entity_map.keys())
	for i, a in enumerate(all_norms):
		canonical = merged.get(a, a)
		tokens_a = set(canonical.split())
		for b in all_norms[i + 1:]:
			if b in merged:
				continue
			tokens_b = set(b.split())
			overlap = len(tokens_a & tokens_b)
			min_len = min(len(tokens_a), len(tokens_b))
			if min_len > 0 and overlap / min_len >= 0.8:
				merged[b] = canonical
				for t, info in entity_map[b].items():
					if t not in entity_map[canonical]:
						entity_map[canonical][t] = info
					else:
						entity_map[canonical][t]["roles"] |= info["roles"]
						entity_map[canonical][t]["original_names"] |= info["original_names"]

	for old_name in merged:
		if old_name in entity_map and old_name != merged[old_name]:
			del entity_map[old_name]

	# Step 3: Find shared entities (referenced by 2+ tickers)
	shared_entities = []
	for norm_name, ticker_refs in entity_map.items():
		if len(ticker_refs) >= 2:
			referenced_by = {}
			for ref_ticker, ref_info in ticker_refs.items():
				roles = sorted(ref_info["roles"])
				confidence = "high" if "single_source" in roles or "supplier" in roles else "medium"
				referenced_by[ref_ticker] = {"roles": roles, "confidence": confidence}
			shared_entities.append({"entity": norm_name, "referenced_by": referenced_by})

	# Step 3.5: Score each shared entity for bottleneck potential
	total_tickers = len(tickers) - len(failed_tickers)
	for entity in shared_entities:
		refs = entity["referenced_by"]
		supplier_refs = {}
		for t, r in refs.items():
			roles = r.get("roles", [])
			if isinstance(roles, set):
				roles = list(roles)
			if any(role in ("supplier", "single_source") for role in roles):
				supplier_refs[t] = r
		supplier_count = len(supplier_refs)
		single_source_count = sum(
			1 for r in supplier_refs.values()
			if "single_source" in (r.get("roles", []) if isinstance(r.get("roles", []), list) else list(r.get("roles", [])))
		)
		supplier_pct = round(supplier_count / total_tickers * 100, 1) if total_tickers > 0 else 0.0

		if supplier_pct >= 50 and single_source_count > 0:
			assessment = "strong_bottleneck_signal"
		elif supplier_pct >= 50 or single_source_count > 0:
			assessment = "moderate_bottleneck_signal"
		elif supplier_pct >= 25:
			assessment = "weak_signal"
		else:
			assessment = "low_signal"

		# Collect customer concentration % from revenue_concentration data
		max_rev_pct = None
		for t, r in refs.items():
			roles = r.get("roles", [])
			if isinstance(roles, set):
				roles = list(roles)
			if "customer_concentrated" in roles:
				# Look up revenue_pct from entity_map
				emap_entry = entity_map.get(entity["entity"], {}).get(t, {})
				rpct = emap_entry.get("revenue_pct")
				if rpct and (max_rev_pct is None or rpct > max_rev_pct):
					max_rev_pct = rpct

		signal = {
			"supplier_ref_count": supplier_count,
			"supplier_ref_pct": supplier_pct,
			"single_source_count": single_source_count,
			"assessment": assessment,
		}
		if max_rev_pct is not None:
			signal["customer_concentration_pct"] = max_rev_pct
		entity["bottleneck_signal"] = signal

	shared_entities.sort(
		key=lambda e: (
			e.get("bottleneck_signal", {}).get("supplier_ref_count", 0),
			e.get("bottleneck_signal", {}).get("single_source_count", 0),
		),
		reverse=True,
	)

	# Step 4: Calculate overlap metrics
	total_unique = len(entity_map)
	shared_count = len(shared_entities)
	overlap_pct = round((shared_count / total_unique) * 100, 1) if total_unique > 0 else 0.0

	for t in tickers:
		if t in failed_tickers:
			continue
		unique_count = sum(1 for refs in entity_map.values() if t in refs and len(refs) == 1)
		per_ticker_stats[t]["unique_to_ticker"] = unique_count

	output_json({
		"tickers": tickers,
		"shared_supplier_nodes": shared_entities,
		"per_ticker_suppliers": per_ticker_stats,
		"supply_chain_overlap_pct": overlap_pct,
		"total_unique_entities": total_unique,
		"shared_entity_count": shared_count,
		"note": "Cross-chain analysis based on SEC filing disclosures. Entity matching is name-based. Agent should verify shared relationships via WebSearch.",
	})


@safe_run
def cmd_compare(args):
	"""Multi-Ticker Comparison (12 metrics including asymmetry_score).

	Runs L4 and L5 analysis scripts for each ticker in parallel,
	then builds a comparative table with relative strength rankings.
	Includes bottleneck_scorer validation for asymmetry scoring.
	"""
	tickers = [t.upper() for t in args.tickers]

	# For each ticker, run the comparison scripts
	per_ticker_scripts = {}
	for ticker in tickers:
		per_ticker_scripts[ticker] = {
			"info": ("data_sources/info.py", ["get-info-fields", ticker,
				"marketCap", "currentPrice", "fiftyTwoWeekLow",
				"fiftyTwoWeekHigh", "shortPercentOfFloat"]),
			"forward_pe": ("analysis/forward_pe.py", ["calculate", ticker]),
			"no_growth_valuation": ("analysis/no_growth_valuation.py", ["calculate", ticker]),
			"margin_tracker": ("analysis/margin_tracker.py", ["track", ticker]),
			"institutional_quality": ("analysis/institutional_quality.py", ["score", ticker]),
			"debt_structure": ("analysis/debt_structure.py", ["analyze", ticker]),
			"sbc_analyzer": ("analysis/sbc_analyzer.py", ["get-sbc", ticker]),
			"earnings_surprise": ("data_sources/earnings_acceleration.py", ["surprise", ticker]),
			"bottleneck_scorer": ("analysis/bottleneck_scorer.py", ["validate", ticker]),
		}

	# Run all scripts across all tickers in parallel
	all_futures = {}
	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		for ticker, scripts in per_ticker_scripts.items():
			for name, (path, a) in scripts.items():
				key = f"{ticker}__{name}"
				all_futures[key] = executor.submit(_run_script, path, a)

		all_results = {key: future.result() for key, future in all_futures.items()}

	# Organize results per ticker
	ticker_results = {}
	for ticker in tickers:
		ticker_results[ticker] = {
			name: all_results[f"{ticker}__{name}"]
			for name in per_ticker_scripts[ticker]
		}

	# Build comparative table
	comparative_table = {
		"forward_pe": {},
		"no_growth_upside_pct": {},
		"margin_status": {},
		"io_quality_score": {},
		"debt_quality_grade": {},
		"market_cap": {},
		"revenue_growth_yoy": {},
		"short_interest_pct": {},
		"52w_range_position": {},
		"sbc_flag": {},
		"consecutive_beats": {},
		"asymmetry_score": {},
	}

	health_gates_all = {}

	for ticker in tickers:
		r = ticker_results[ticker]

		# Forward PE
		fpe = r.get("forward_pe", {})
		comparative_table["forward_pe"][ticker] = (
			fpe.get("forward_1y_pe") if not fpe.get("error") else None
		)

		# No-growth upside
		ngv = r.get("no_growth_valuation", {})
		comparative_table["no_growth_upside_pct"][ticker] = (
			ngv.get("margin_of_safety_pct") if not ngv.get("error") else None
		)

		# Margin status
		mt = r.get("margin_tracker", {})
		comparative_table["margin_status"][ticker] = (
			mt.get("flag") if not mt.get("error") else None
		)

		# IO quality score
		io = r.get("institutional_quality", {})
		comparative_table["io_quality_score"][ticker] = (
			io.get("io_quality_score") if not io.get("error") else None
		)

		# Debt quality grade
		ds = r.get("debt_structure", {})
		comparative_table["debt_quality_grade"][ticker] = (
			ds.get("debt_quality_grade") if not ds.get("error") else None
		)

		# Market cap
		info = r.get("info", {})
		comparative_table["market_cap"][ticker] = (
			info.get("marketCap") if not info.get("error") else None
		)

		# Revenue growth YoY (from forward_pe analyst consensus)
		comparative_table["revenue_growth_yoy"][ticker] = (
			fpe.get("revenue_growth_yoy") if not fpe.get("error") else None
		)

		# Short interest
		comparative_table["short_interest_pct"][ticker] = (
			info.get("shortPercentOfFloat") if not info.get("error") else None
		)

		# 52-week range position
		pos_52w = None
		if not info.get("error"):
			low = info.get("fiftyTwoWeekLow")
			high = info.get("fiftyTwoWeekHigh")
			current = info.get("currentPrice")
			if all(v is not None for v in [low, high, current]) and high != low:
				pos_52w = round((current - low) / (high - low) * 100, 1)
		comparative_table["52w_range_position"][ticker] = pos_52w

		# SBC flag
		sbc = r.get("sbc_analyzer", {})
		comparative_table["sbc_flag"][ticker] = (
			sbc.get("flag") if not sbc.get("error") else None
		)

		# Consecutive earnings beats
		es = r.get("earnings_surprise", {})
		comparative_table["consecutive_beats"][ticker] = (
			es.get("consecutive_beats") if not es.get("error") else None
		)

		# Asymmetry score (from bottleneck_scorer)
		bs = r.get("bottleneck_scorer", {})
		comparative_table["asymmetry_score"][ticker] = (
			bs.get("asymmetry_score") if not bs.get("error") else None
		)

		# Health gates per ticker (integrate bottleneck flags)
		hg = _extract_health_gates(r)
		# Add bottleneck-related flags from bottleneck_scorer if available
		if not bs.get("error"):
			bs_gates = bs.get("health_gates", {})
			for gate_name, gate_val in bs_gates.items():
				if gate_val == "FLAG" and gate_name in hg:
					hg[gate_name] = "FLAG"
		health_gates_all[ticker] = hg

	# Determine relative strengths
	relative_strengths = _determine_relative_strengths(tickers, comparative_table)

	output = {
		"tickers": tickers,
		"comparative_table": comparative_table,
		"health_gates": health_gates_all,
		"relative_strengths": relative_strengths,
	}

	output_json(output)


def _determine_relative_strengths(tickers, table):
	"""Determine best ticker for each metric from comparative table."""
	strengths = {}

	# Best valuation = lowest positive forward PE
	fpe_vals = {
		t: v for t, v in table["forward_pe"].items()
		if v is not None and isinstance(v, (int, float)) and v > 0
	}
	if fpe_vals:
		strengths["best_valuation"] = min(fpe_vals, key=fpe_vals.get)
	else:
		strengths["best_valuation"] = None

	# Best margin trajectory = EXPANDING preferred, else highest margin status
	margin_priority = {
		"EXPANDING": 4,
		"STABLE": 3,
		"COMPRESSION": 2,
		"CONTRACTING": 1,
		"COLLAPSE": 0,
	}
	margin_vals = {}
	for t in tickers:
		status = table["margin_status"].get(t)
		if status is not None:
			# Check each priority keyword
			best_priority = -1
			for keyword, priority in margin_priority.items():
				if keyword in str(status).upper():
					best_priority = max(best_priority, priority)
			if best_priority >= 0:
				margin_vals[t] = best_priority
	if margin_vals:
		strengths["best_margin_trajectory"] = max(margin_vals, key=margin_vals.get)
	else:
		strengths["best_margin_trajectory"] = None

	# Best IO quality = highest quality score
	io_vals = {
		t: v for t, v in table["io_quality_score"].items()
		if v is not None and isinstance(v, (int, float))
	}
	if io_vals:
		strengths["best_io_quality"] = max(io_vals, key=io_vals.get)
	else:
		strengths["best_io_quality"] = None

	# Best balance sheet = grade A > B > C > D
	grade_priority = {"A": 4, "B": 3, "C": 2, "D": 1}
	grade_vals = {}
	for t in tickers:
		grade = table["debt_quality_grade"].get(t)
		if grade is not None:
			# Take the first character as the grade letter
			grade_letter = str(grade).strip()[0].upper() if grade else ""
			grade_vals[t] = grade_priority.get(grade_letter, 0)
	if grade_vals:
		strengths["best_balance_sheet"] = max(grade_vals, key=grade_vals.get)
	else:
		strengths["best_balance_sheet"] = None

	# Best revenue growth = highest YoY revenue growth
	rev_vals = {
		t: v for t, v in table.get("revenue_growth_yoy", {}).items()
		if v is not None and isinstance(v, (int, float))
	}
	if rev_vals:
		strengths["best_revenue_growth"] = max(rev_vals, key=rev_vals.get)
	else:
		strengths["best_revenue_growth"] = None

	# Best 52-week position = highest position (closest to 52w high)
	pos_vals = {
		t: v for t, v in table.get("52w_range_position", {}).items()
		if v is not None and isinstance(v, (int, float))
	}
	if pos_vals:
		strengths["best_52w_position"] = max(pos_vals, key=pos_vals.get)
	else:
		strengths["best_52w_position"] = None

	# Best SBC health = healthy > warning > toxic
	sbc_priority = {"healthy": 3, "warning": 2, "toxic": 1}
	sbc_vals = {}
	for t in tickers:
		flag = table.get("sbc_flag", {}).get(t)
		if flag is not None:
			sbc_vals[t] = sbc_priority.get(str(flag).lower(), 0)
	if sbc_vals:
		strengths["best_sbc_health"] = max(sbc_vals, key=sbc_vals.get)
	else:
		strengths["best_sbc_health"] = None

	# Best earnings momentum = most consecutive beats
	beat_vals = {
		t: v for t, v in table.get("consecutive_beats", {}).items()
		if v is not None and isinstance(v, (int, float))
	}
	if beat_vals:
		strengths["best_earnings_momentum"] = max(beat_vals, key=beat_vals.get)
	else:
		strengths["best_earnings_momentum"] = None

	# Best asymmetry = highest bottleneck asymmetry score
	asym_vals = {
		t: v for t, v in table.get("asymmetry_score", {}).items()
		if v is not None and isinstance(v, (int, float))
	}
	if asym_vals:
		strengths["best_asymmetry"] = max(asym_vals, key=asym_vals.get)
	else:
		strengths["best_asymmetry"] = None

	return strengths


def _parse_mcap_string(mcap_str):
	"""Parse market cap string like '1.5B', '500M', '10B' to a numeric value.

	Returns:
		float or None if parsing fails
	"""
	if not mcap_str or not isinstance(mcap_str, str):
		return None
	mcap_str = mcap_str.strip().upper()
	multipliers = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}
	for suffix, mult in multipliers.items():
		if mcap_str.endswith(suffix):
			try:
				return float(mcap_str[:-1]) * mult
			except ValueError:
				return None
	try:
		return float(mcap_str)
	except ValueError:
		return None


@safe_run
def cmd_screen(args):
	"""Sector-based Bottleneck Candidate Screening.

	Uses finviz.py sector-screen to get initial candidates,
	filters by --max-mcap, then validates each with bottleneck_scorer.py.
	Sorts by asymmetry_score descending.
	"""
	sector = args.sector
	max_mcap = args.max_mcap
	max_mcap_val = _parse_mcap_string(max_mcap)

	# Step 1: Get candidates from finviz sector-screen
	screen_args = ["sector-screen", "--sector", sector, "--limit", "50"]
	screen_result = _run_script("screening/finviz.py", screen_args)

	if screen_result.get("error"):
		output_json({
			"sector": sector,
			"error": f"Finviz screening failed: {screen_result['error']}",
			"candidates_screened": 0,
			"results": [],
		})
		return

	# Extract tickers from screen result
	candidates = screen_result.get("data", [])
	if not candidates:
		output_json({
			"sector": sector,
			"candidates_screened": 0,
			"results": [],
			"note": "No candidates returned from Finviz screening",
		})
		return

	# Apply --max-mcap filter
	if max_mcap_val is not None:
		filtered = []
		for row in candidates:
			raw_mcap = row.get("Market Cap") or row.get("market_cap")
			row_mcap = _parse_mcap_string(str(raw_mcap)) if raw_mcap else None
			if row_mcap is None or row_mcap <= max_mcap_val:
				filtered.append(row)
		candidates = filtered

	# Extract ticker symbols (limit to 10)
	ticker_list = []
	for row in candidates[:10]:
		ticker = row.get("Ticker") or row.get("ticker")
		if ticker:
			ticker_list.append(ticker)

	if not ticker_list:
		output_json({
			"sector": sector,
			"candidates_screened": 0,
			"results": [],
			"note": "No candidates passed filters",
		})
		return

	# Step 2: Run bottleneck_scorer.py validate on each ticker (sequential to avoid rate limits)
	scored_results = []
	for ticker in ticker_list:
		validation = _run_script(
			"analysis/bottleneck_scorer.py", ["validate", ticker]
		)

		# Get market cap from screening data
		market_cap = None
		for row in candidates:
			row_ticker = row.get("Ticker") or row.get("ticker")
			if row_ticker == ticker:
				market_cap = row.get("Market Cap") or row.get("market_cap")
				break

		entry = {
			"ticker": ticker,
			"market_cap": market_cap,
			"asymmetry_score": (
				validation.get("asymmetry_score")
				if not validation.get("error")
				else None
			),
			"health_gates": (
				validation.get("health_gates")
				if not validation.get("error")
				else {"error": validation.get("error")}
			),
		}

		if validation.get("error"):
			entry["error"] = validation["error"]

		scored_results.append(entry)

	# Sort by asymmetry_score descending (None values last)
	scored_results.sort(
		key=lambda x: x.get("asymmetry_score") if x.get("asymmetry_score") is not None else -999,
		reverse=True,
	)

	output = {
		"sector": sector,
		"candidates_screened": len(scored_results),
		"filters_applied": {
			"max_mcap": max_mcap,
		},
		"results": scored_results,
	}

	output_json(output)


@safe_run
def cmd_capex_cascade(args):
	"""Supply chain CapEx cascade tracking across multiple tickers.

	Tracks 8-quarter CapEx trends for each ticker in parallel, then
	summarizes cascade health (upstream→downstream direction consistency)
	and hyperscaler signal (if applicable).

	Args:
		tickers (list): 2+ stock ticker symbols

	Returns:
		dict: {
			"tickers": list[str],
			"capex_trends": dict (per-ticker 8Q CapEx with direction),
			"cascade_summary": dict (overall cascade health),
			"hyperscaler_signal": dict or None (aggregate hyperscaler direction)
		}
	"""
	tickers = [t.upper() for t in args.tickers]

	# Run capex_tracker.py track for each ticker in parallel
	with concurrent.futures.ThreadPoolExecutor(max_workers=len(tickers)) as executor:
		futures = {
			ticker: executor.submit(
				_run_script,
				"analysis/capex_tracker.py",
				["track", ticker, "--quarters", "8"],
			)
			for ticker in tickers
		}
		capex_results = {ticker: future.result() for ticker, future in futures.items()}

	# Build capex_trends per ticker
	# capex_tracker.py track returns: {"command":"track", "symbols":[{"symbol":"X", "quarters":[...], "direction":"...", "latest_capex":...}]}
	capex_trends = {}
	directions = []
	for ticker in tickers:
		result = capex_results[ticker]
		if not result.get("error"):
			# Extract from nested symbols array
			symbols_data = result.get("symbols", [])
			sym_data = symbols_data[0] if symbols_data else {}
			direction = sym_data.get("direction", "unknown")
			# Get latest QoQ/YoY from the most recent quarter
			quarters = sym_data.get("quarters", [])
			latest_q = quarters[0] if quarters else {}
			capex_trends[ticker] = {
				"direction": direction,
				"qoq_change": latest_q.get("qoq_change_pct"),
				"yoy_change": latest_q.get("yoy_change_pct"),
				"latest_capex": sym_data.get("latest_capex"),
				"avg_capex": sym_data.get("avg_capex"),
				"quarters_count": len(quarters),
			}
			directions.append(direction)
		else:
			capex_trends[ticker] = {"error": result["error"]}

	# Cascade summary: check direction consistency
	valid_directions = [d for d in directions if d and d != "unknown"]
	if valid_directions:
		increasing = sum(1 for d in valid_directions if d.lower() in ("increasing", "up", "accelerating"))
		decreasing = sum(1 for d in valid_directions if d.lower() in ("decreasing", "down", "decelerating"))
		total = len(valid_directions)

		if increasing == total:
			cascade_health = "strong_expansion"
			consistency = "aligned_up"
		elif decreasing == total:
			cascade_health = "contraction"
			consistency = "aligned_down"
		elif increasing > decreasing:
			cascade_health = "mixed_expansion"
			consistency = "mostly_up"
		elif decreasing > increasing:
			cascade_health = "mixed_contraction"
			consistency = "mostly_down"
		else:
			cascade_health = "mixed"
			consistency = "divergent"
	else:
		cascade_health = "insufficient_data"
		consistency = "unknown"

	cascade_summary = {
		"cascade_health": cascade_health,
		"direction_consistency": consistency,
		"tickers_increasing": sum(1 for d in valid_directions if d.lower() in ("increasing", "up", "accelerating")),
		"tickers_decreasing": sum(1 for d in valid_directions if d.lower() in ("decreasing", "down", "decelerating")),
		"tickers_total": len(tickers),
		"tickers_with_data": len(valid_directions),
	}

	# Hyperscaler signal: check if any of the known hyperscalers are in the list
	hyperscalers = {"AMZN", "GOOG", "GOOGL", "MSFT", "META"}
	hs_in_list = [t for t in tickers if t in hyperscalers]
	hyperscaler_signal = None
	if hs_in_list:
		hs_directions = []
		for t in hs_in_list:
			trend = capex_trends.get(t, {})
			if not trend.get("error"):
				hs_directions.append(trend.get("direction", "unknown"))
		if hs_directions:
			hs_increasing = sum(1 for d in hs_directions if d and d.lower() in ("increasing", "up", "accelerating"))
			hyperscaler_signal = {
				"hyperscalers_tracked": hs_in_list,
				"direction": "increasing" if hs_increasing > len(hs_directions) / 2 else "decreasing" if hs_increasing == 0 else "mixed",
				"increasing_count": hs_increasing,
				"total_count": len(hs_directions),
			}

	output_json({
		"tickers": tickers,
		"capex_trends": capex_trends,
		"cascade_summary": cascade_summary,
		"hyperscaler_signal": hyperscaler_signal,
	})


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
	parser = argparse.ArgumentParser(
		description="Serenity Pipeline: 6-Level Analytical Hierarchy"
	)
	sub = parser.add_subparsers(dest="command", required=True)

	# macro
	sp_macro = sub.add_parser("macro", help="Level 1 macro regime assessment")
	sp_macro.add_argument(
		"--extended",
		action="store_true",
		default=False,
		help="Include raw DXY and BDI data in output",
	)
	sp_macro.set_defaults(func=cmd_macro)

	# analyze
	sp_analyze = sub.add_parser("analyze", help="Full 6-Level analysis for a ticker")
	sp_analyze.add_argument("ticker", help="Stock ticker symbol")
	sp_analyze.add_argument(
		"--skip-macro",
		action="store_true",
		default=False,
		help="Skip Level 1 macro assessment",
	)
	sp_analyze.set_defaults(func=cmd_analyze)

	# compare
	sp_compare = sub.add_parser(
		"compare", help="Multi-ticker side-by-side comparison"
	)
	sp_compare.add_argument(
		"tickers", nargs="+", help="2 or more stock ticker symbols"
	)
	sp_compare.set_defaults(func=cmd_compare)

	# screen
	sp_screen = sub.add_parser(
		"screen", help="Sector-based bottleneck candidate screening"
	)
	sp_screen.add_argument("sector", help="Sector name for Finviz screening")
	sp_screen.add_argument(
		"--max-mcap",
		default="10B",
		help="Maximum market cap filter (default: 10B)",
	)
	sp_screen.set_defaults(func=cmd_screen)

	# capex-cascade
	sp_capex = sub.add_parser(
		"capex-cascade", help="Supply chain CapEx cascade tracking"
	)
	sp_capex.add_argument(
		"tickers", nargs="+", help="2 or more stock ticker symbols"
	)
	sp_capex.set_defaults(func=cmd_capex_cascade)

	# recheck
	sp_recheck = sub.add_parser(
		"recheck", help="Position monitoring recheck"
	)
	sp_recheck.add_argument("ticker", help="Stock ticker symbol")
	sp_recheck.add_argument(
		"--entry-price", required=True, help="Entry price for position"
	)
	sp_recheck.add_argument(
		"--entry-date", default=None, help="Entry date (YYYY-MM-DD, informational)"
	)
	sp_recheck.set_defaults(func=cmd_recheck)

	# discover
	sp_discover = sub.add_parser(
		"discover", help="Automated theme discovery with bottleneck candidates"
	)
	sp_discover.add_argument(
		"--top-groups", type=int, default=5,
		help="Number of top industry groups to surface (default: 5)",
	)
	sp_discover.add_argument(
		"--max-mcap", default="10B",
		help="Maximum market cap filter (default: 10B)",
	)
	sp_discover.add_argument(
		"--limit", type=int, default=10,
		help="Maximum candidates per theme (default: 10)",
	)
	sp_discover.add_argument(
		"--industry", default=None,
		help="Direct industry search (skips sector_leaders). Partial name match supported.",
	)
	sp_discover.set_defaults(func=cmd_discover)

	# cross-chain
	sp_cross = sub.add_parser(
		"cross-chain", help="Shared supplier detection across tickers"
	)
	sp_cross.add_argument(
		"tickers", nargs="+", help="2 or more stock ticker symbols"
	)
	sp_cross.add_argument(
		"--form", default="10-K", help="SEC filing form type (default: 10-K, auto-fallback to 20-F)"
	)
	sp_cross.set_defaults(func=cmd_cross_chain)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
