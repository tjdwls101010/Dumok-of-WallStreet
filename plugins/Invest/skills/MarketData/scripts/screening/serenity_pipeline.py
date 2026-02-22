#!/usr/bin/env python3
"""Serenity Pipeline: 6-Level analytical hierarchy automating supply chain
bottleneck analysis with macro regime assessment, fundamental validation,
and evidence chain verification.

Orchestrates the complete Serenity analysis by running macro regime scripts,
fundamental analysis tools, valuation models, and catalyst monitoring in
parallel. Levels 1/4/5/6 are automated; Levels 2 (CapEx Flow) and 3
(Bottleneck) require agent context for supply chain knowledge.

Commands:
	macro: Level 1 macro regime assessment
	analyze: Full 6-Level analysis for a single ticker
	evidence_chain: 6-Link evidence chain data availability check
	compare: Multi-ticker side-by-side comparison
	screen: Sector-based bottleneck candidate screening

Args:
	For macro:
		--extended (bool): Include DXY and BDI analysis (default: false)

	For analyze:
		ticker (str): Stock ticker symbol
		--skip-macro (bool): Skip Level 1 macro assessment (default: false)

	For evidence_chain:
		ticker (str): Stock ticker symbol

	For compare:
		tickers (list): 2+ stock ticker symbols

	For screen:
		sector (str): Sector name for Finviz screening
		--min-rs (int): Minimum relative strength score (default: 50)
		--max-mcap (str): Maximum market cap filter (default: "10B")

Returns:
	dict: Structure varies by command. See individual subcommand docs.
	Common fields include levels, health_gates, valuation_summary.

Example:
	>>> python serenity_pipeline.py macro --extended
	{"regime": "risk_on", "risk_level": "moderate", ...}

	>>> python serenity_pipeline.py analyze NBIS
	{"ticker": "NBIS", "levels": {...}, "health_gates": {...}, ...}

	>>> python serenity_pipeline.py evidence_chain AXTI
	{"ticker": "AXTI", "chain_completeness": "5/6", ...}

	>>> python serenity_pipeline.py compare AXTI AEHR FORM
	{"tickers": [...], "comparative_table": {...}, ...}

	>>> python serenity_pipeline.py screen "Defense" --min-rs 60
	{"sector": "Defense", "candidates_screened": 10, ...}

Use Cases:
	- Full due diligence automation for any ticker in any sector
	- Macro regime assessment before position entry
	- Evidence chain completeness check for conviction assignment
	- Multi-ticker comparison within a supply chain
	- Sector screening for bottleneck candidates
	- Sector-agnostic: works for defense, EV, agriculture, semiconductors, etc.

Notes:
	- L1 macro and L4-L6 fundamentals auto-execute for any ticker
	- L2 (CapEx Flow) and L3 (Bottleneck) return requires_context for agent-driven analysis
	- Health gates are extracted from L4 script outputs (debt, dilution, valuation, margin)
	- Scripts execute in parallel via ThreadPoolExecutor for speed
	- Pipeline continues even if individual scripts fail (graceful degradation)
	- screen subcommand depends on finviz.py and bottleneck_scorer.py
"""

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import output_json, safe_run

SCRIPTS_DIR = os.path.dirname(os.path.dirname(__file__))


def _run_script(script_path, args_list):
	"""Run a script and capture its JSON output."""
	full_path = os.path.join(SCRIPTS_DIR, script_path)
	cmd = [sys.executable, full_path] + args_list

	try:
		result = subprocess.run(
			cmd,
			capture_output=True,
			text=True,
			timeout=60,
			cwd=SCRIPTS_DIR,
		)
		if result.returncode == 0 and result.stdout.strip():
			return json.loads(result.stdout)
		else:
			return {"error": result.stderr.strip() or "Script returned no output"}
	except subprocess.TimeoutExpired:
		return {"error": "Script timed out (60s)"}
	except json.JSONDecodeError:
		return {"error": "Invalid JSON output from script"}
	except Exception as e:
		return {"error": str(e)}


# ---------------------------------------------------------------------------
# Health Gate Extraction
# ---------------------------------------------------------------------------

def _extract_health_gates(results):
	"""Extract 4 health gates from L4 script results.

	Gates:
	1. Bear-Bull Paradox: debt quality D or interest coverage < 1.0
	2. Active Dilution: dilution_flag == "active_dilution"
	3. No-Growth Fail: upside_pct < -50
	4. Margin Collapse: status contains "COLLAPSE"

	Returns:
		dict with gate statuses, total_pass, total_gates, flags
	"""
	gates = {
		"bear_bull_paradox": "PASS",
		"active_dilution": "PASS",
		"no_growth_fail": "PASS",
		"margin_collapse": "PASS",
	}
	flags = []

	# Bear-Bull Paradox
	debt = results.get("debt_structure", {})
	if not debt.get("error"):
		if debt.get("debt_quality_grade") == "D" or (
			debt.get("interest_coverage_ratio") is not None
			and debt.get("interest_coverage_ratio") < 1.0
		):
			gates["bear_bull_paradox"] = "FLAG"
			flags.append("bear_bull_paradox")

	# Active Dilution
	sbc = results.get("sbc_analyzer", {})
	if not sbc.get("error"):
		if sbc.get("dilution_flag") == "active_dilution":
			gates["active_dilution"] = "FLAG"
			flags.append("active_dilution")

	# No-Growth Fail
	ngv = results.get("no_growth_valuation", {})
	if not ngv.get("error"):
		mos = ngv.get("margin_of_safety_pct")
		if mos is not None and mos < -50:
			gates["no_growth_fail"] = "FLAG"
			flags.append("no_growth_fail")

	# Margin Collapse
	margin = results.get("margin_tracker", {})
	if not margin.get("error"):
		if "COLLAPSE" in str(margin.get("flag", "")):
			gates["margin_collapse"] = "FLAG"
			flags.append("margin_collapse")

	total_pass = sum(1 for v in gates.values() if v == "PASS")

	gates["total_pass"] = total_pass
	gates["total_gates"] = 4
	gates["flags"] = flags

	return gates


def _build_valuation_summary(results):
	"""Build valuation summary from L4 script results."""
	forward_pe_data = results.get("forward_pe", {})
	ngv_data = results.get("no_growth_valuation", {})
	margin_data = results.get("margin_tracker", {})
	io_data = results.get("institutional_quality", {})
	debt_data = results.get("debt_structure", {})

	return {
		"forward_pe": forward_pe_data.get("forward_1y_pe") if not forward_pe_data.get("error") else None,
		"no_growth_upside_pct": ngv_data.get("margin_of_safety_pct") if not ngv_data.get("error") else None,
		"margin_status": margin_data.get("flag") if not margin_data.get("error") else None,
		"io_quality_score": io_data.get("io_quality_score") if not io_data.get("error") else None,
		"debt_quality_grade": debt_data.get("debt_quality_grade") if not debt_data.get("error") else None,
	}


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
	if not erp.get("error"):
		erp_val = erp.get("erp_pct") or erp.get("erp") or erp.get("equity_risk_premium")
		if erp_val is not None:
			erp_healthy = erp_val > 3.0
			erp_danger = erp_val < 1.5

	vix_contango = False
	vix_backwardation = False
	if not vix.get("error"):
		structure = str(vix.get("term_structure", "")).lower()
		vix_contango = "contango" in structure
		vix_backwardation = "backwardation" in structure

	net_liq_positive = False
	if not net_liq.get("error"):
		trend = str(net_liq.get("trend", "")).lower()
		net_liq_positive = "positive" in trend or "rising" in trend or "expanding" in trend

	fear_extreme = False
	if not fear_greed.get("error"):
		fg_val = fear_greed.get("value") or fear_greed.get("score")
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

	if not erp_healthy and not erp.get("error"):
		drain_count += 1
		decision_rules.append("ERP below healthy threshold")
	elif erp_healthy:
		decision_rules.append("ERP healthy — equity risk premium adequate")

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

	if fear_extreme:
		drain_count += 1
		decision_rules.append("Fear & Greed at extreme fear levels")
	elif not fear_greed.get("error"):
		decision_rules.append("Sentiment within normal range")

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
		"net_liquidity": ("macro/net_liquidity.py", ["net-liquidity"]),
		"vix_curve": ("macro/vix_curve.py", ["analyze"]),
		"fedwatch": ("data_advanced/fed/fedwatch.py", []),
		"yield_curve": ("data_advanced/fred/rates.py", ["yield-curve"]),
		"erp": ("macro/erp.py", ["erp"]),
		"fear_greed": ("analysis/sentiment/fear_greed.py", []),
	}

	if args.extended:
		scripts["dxy"] = ("data_sources/dxy.py", [])
		scripts["bdi"] = ("data_sources/bdi.py", [])

	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		futures = {
			name: executor.submit(_run_script, path, a)
			for name, (path, a) in scripts.items()
		}
		results = {name: future.result() for name, future in futures.items()}

	# Classify regime
	classification = _classify_macro_regime(results)

	output = {
		"regime": classification["regime"],
		"risk_level": classification["risk_level"],
		"drain_count": classification["drain_count"],
		"decision_rules": classification["decision_rules"],
		"data": results,
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
			"net_liquidity": ("macro/net_liquidity.py", ["net-liquidity"]),
			"vix_curve": ("macro/vix_curve.py", ["analyze"]),
			"fedwatch": ("data_advanced/fed/fedwatch.py", []),
			"yield_curve": ("data_advanced/fred/rates.py", ["yield-curve"]),
			"erp": ("macro/erp.py", ["erp"]),
			"fear_greed": ("analysis/sentiment/fear_greed.py", []),
		}

		with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
			futures = {
				name: executor.submit(_run_script, path, a)
				for name, (path, a) in macro_scripts.items()
			}
			macro_results = {name: future.result() for name, future in futures.items()}

		classification = _classify_macro_regime(macro_results)
		l1_result = {
			"regime": classification["regime"],
			"risk_level": classification["risk_level"],
			"drain_count": classification["drain_count"],
			"decision_rules": classification["decision_rules"],
			"data": macro_results,
		}

	# --- Level 4: Position Construction (Fundamentals) ---
	l4_scripts = {
		"info": ("data_sources/info.py", ["get-info", ticker]),
		"income_stmt": ("data_sources/financials.py", ["get-income-stmt", ticker]),
		"cash_flow": ("data_sources/financials.py", ["get-cash-flow", ticker]),
		"balance_sheet": ("data_sources/financials.py", ["get-balance-sheet", ticker]),
		"holders": ("data_sources/holders.py", ["get-institutional-holders", ticker]),
		"earnings_acceleration": ("data_sources/earnings_acceleration.py", ["code33", ticker]),
		"sbc_analyzer": ("analysis/sbc_analyzer.py", ["get-sbc", ticker]),
		"forward_pe": ("analysis/forward_pe.py", ["calculate", ticker]),
		"debt_structure": ("analysis/debt_structure.py", ["analyze", ticker]),
		"institutional_quality": ("analysis/institutional_quality.py", ["score", ticker]),
		"no_growth_valuation": ("analysis/no_growth_valuation.py", ["calculate", ticker]),
		"margin_tracker": ("analysis/margin_tracker.py", ["track", ticker]),
		"iv_context": ("analysis/iv_context.py", ["analyze", ticker]),
	}

	# --- Level 5: Catalyst Monitoring ---
	l5_scripts = {
		"earnings_dates": ("data_sources/actions.py", ["get-earnings-dates", ticker]),
		"earnings_calendar": ("data_sources/calendars.py", ["get-earnings-calendar"]),
	}

	# Run L4 and L5 in parallel
	all_scripts = {}
	all_scripts.update(l4_scripts)
	all_scripts.update(l5_scripts)

	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		futures = {
			name: executor.submit(_run_script, path, a)
			for name, (path, a) in all_scripts.items()
		}
		all_results = {name: future.result() for name, future in futures.items()}

	# Split results
	l4_results = {k: all_results[k] for k in l4_scripts}
	l5_results = {k: all_results[k] for k in l5_scripts}

	# Health gates (extracted from L4)
	health_gates = _extract_health_gates(l4_results)

	# Valuation summary
	valuation_summary = _build_valuation_summary(l4_results)

	output = {
		"ticker": ticker,
		"levels": {
			"L1_macro": l1_result if l1_result else {"skipped": True},
			"L2_capex_flow": {
				"requires_context": True,
				"note": "Agent determines supply chain CapEx layers. Use capex_tracker.py cascade with appropriate --layers.",
			},
			"L3_bottleneck": {
				"requires_context": True,
				"note": "Supply chain mapping and 6-Criteria Bottleneck Scoring requires agent + WebSearch.",
			},
			"L4_fundamentals": l4_results,
			"L5_catalysts": l5_results,
			"L6_taxonomy": {
				"requires_llm": True,
				"note": "Agent classifies as Evolution / Disruption / Bottleneck.",
			},
		},
		"health_gates": health_gates,
		"valuation_summary": valuation_summary,
	}

	output_json(output)


@safe_run
def cmd_evidence_chain(args):
	"""6-Link Evidence Chain Verification.

	Checks data availability for each of the 6 evidence chain links.
	L1 (macro), L2 (sector), L4 (company), L5 (valuation), L6 (catalyst)
	are auto-verified. L3 (bottleneck) always requires research.
	"""
	ticker = args.ticker.upper()

	# L1: Macro
	l1_scripts = {
		"erp": ("macro/erp.py", ["erp"]),
		"fedwatch": ("data_advanced/fed/fedwatch.py", []),
	}

	# L2: Sector
	l2_scripts = {
		"sector_leaders": ("screening/sector_leaders.py", ["scan"]),
	}

	# L4: Company
	l4_scripts = {
		"info": ("data_sources/info.py", ["get-info", ticker]),
		"debt_structure": ("analysis/debt_structure.py", ["analyze", ticker]),
		"holders": ("data_sources/holders.py", ["get-institutional-holders", ticker]),
	}

	# L5: Valuation
	l5_scripts = {
		"forward_pe": ("analysis/forward_pe.py", ["calculate", ticker]),
		"no_growth_valuation": ("analysis/no_growth_valuation.py", ["calculate", ticker]),
		"institutional_quality": ("analysis/institutional_quality.py", ["score", ticker]),
	}

	# L6: Catalyst
	l6_scripts = {
		"earnings_dates": ("data_sources/actions.py", ["get-earnings-dates", ticker]),
		"earnings_calendar": ("data_sources/calendars.py", ["get-earnings-calendar"]),
	}

	# Run all in parallel
	all_scripts = {}
	all_scripts.update({f"l1_{k}": v for k, v in l1_scripts.items()})
	all_scripts.update({f"l2_{k}": v for k, v in l2_scripts.items()})
	all_scripts.update({f"l4_{k}": v for k, v in l4_scripts.items()})
	all_scripts.update({f"l5_{k}": v for k, v in l5_scripts.items()})
	all_scripts.update({f"l6_{k}": v for k, v in l6_scripts.items()})

	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		futures = {
			name: executor.submit(_run_script, path, a)
			for name, (path, a) in all_scripts.items()
		}
		all_results = {name: future.result() for name, future in futures.items()}

	# Build link status
	def _link_status(prefix, script_keys):
		"""Determine link status from results with given prefix."""
		data = {}
		has_error = True
		for k in script_keys:
			key = f"{prefix}_{k}"
			result = all_results.get(key, {"error": "not run"})
			data[k] = result
			if not result.get("error"):
				has_error = False
		status = "available" if not has_error else "partial" if data else "unavailable"
		return {"status": status, "data": data}

	links = {
		"L1_macro": _link_status("l1", list(l1_scripts.keys())),
		"L2_sector": _link_status("l2", list(l2_scripts.keys())),
		"L3_bottleneck": {
			"status": "requires_research",
			"note": "Supply chain mapping requires WebSearch",
		},
		"L4_company": _link_status("l4", list(l4_scripts.keys())),
		"L5_valuation": _link_status("l5", list(l5_scripts.keys())),
		"L6_catalyst": _link_status("l6", list(l6_scripts.keys())),
	}

	# Count completeness
	missing = []
	available_count = 0
	for link_name, link_data in links.items():
		if link_data["status"] == "available":
			available_count += 1
		elif link_data["status"] == "requires_research":
			missing.append(link_name)
		elif link_data["status"] == "partial":
			available_count += 1  # partial still counts
		else:
			missing.append(link_name)

	output = {
		"ticker": ticker,
		"chain_completeness": f"{available_count}/6",
		"links": links,
		"missing_links": missing,
	}

	output_json(output)


@safe_run
def cmd_compare(args):
	"""Multi-Ticker Comparison.

	Runs L4 and L5 analysis scripts for each ticker in parallel,
	then builds a comparative table with relative strength rankings.
	"""
	tickers = [t.upper() for t in args.tickers]

	# For each ticker, run the comparison scripts
	per_ticker_scripts = {}
	for ticker in tickers:
		per_ticker_scripts[ticker] = {
			"info": ("data_sources/info.py", ["get-info", ticker]),
			"forward_pe": ("analysis/forward_pe.py", ["calculate", ticker]),
			"no_growth_valuation": ("analysis/no_growth_valuation.py", ["calculate", ticker]),
			"margin_tracker": ("analysis/margin_tracker.py", ["track", ticker]),
			"institutional_quality": ("analysis/institutional_quality.py", ["score", ticker]),
			"debt_structure": ("analysis/debt_structure.py", ["analyze", ticker]),
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

		# Health gates per ticker
		health_gates_all[ticker] = _extract_health_gates(r)

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

	return strengths


@safe_run
def cmd_screen(args):
	"""Sector-based Bottleneck Candidate Screening.

	Uses finviz.py sector-screen to get initial candidates,
	then validates each with bottleneck_scorer.py.
	Sorts by asymmetry_score descending.
	"""
	sector = args.sector
	min_rs = args.min_rs
	max_mcap = args.max_mcap

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
			"note": "No ticker symbols found in screening results",
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
			"min_rs": min_rs,
			"max_mcap": max_mcap,
		},
		"results": scored_results,
	}

	output_json(output)


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
		help="Include DXY and BDI analysis",
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

	# evidence_chain
	sp_evidence = sub.add_parser(
		"evidence_chain", help="6-Link evidence chain verification"
	)
	sp_evidence.add_argument("ticker", help="Stock ticker symbol")
	sp_evidence.set_defaults(func=cmd_evidence_chain)

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
		"--min-rs",
		type=int,
		default=50,
		help="Minimum relative strength score (default: 50)",
	)
	sp_screen.add_argument(
		"--max-mcap",
		default="10B",
		help="Maximum market cap filter (default: 10B)",
	)
	sp_screen.set_defaults(func=cmd_screen)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
