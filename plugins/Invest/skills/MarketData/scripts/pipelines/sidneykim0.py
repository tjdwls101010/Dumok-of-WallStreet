#!/usr/bin/env python3
"""SidneyKim0 Pipeline: macro-statistical analysis for US markets.

Orchestrates macro regime assessment, cross-asset divergence detection,
historical analog matching, deep-dive indicator analysis, integrated
scenario construction, and dashboard summary. Unlike stock-focused
pipelines (Minervini, TraderLion, Serenity), this pipeline analyzes
the macro environment as a whole — no individual ticker is required.

Commands:
	regime: Macro regime classification with confidence scoring
	divergence: Cross-asset divergence/convergence scan
	analog: Historical analog matching with forward return fan chart
	deep-dive: Deep-dive analysis on a specific indicator or asset
	scenario: Integrated scenario construction (regime + divergence + analog)
	dashboard: Lightweight macro dashboard summary

Args:
	For regime:
		(no arguments required)
		--extended (bool): Include BDI, semiconductor, commodity indices (default: false)

	For divergence:
		--window (int): Rolling correlation window in days (default: 45)

	For analog:
		--target (str): Target asset for pattern matching (default: "^GSPC")
		--window (int): Lookback window in days (default: 150)
		--forward (int): Forward projection days (default: 60)

	For deep-dive:
		indicator (str): Indicator to analyze. One of: "rates", "dollar",
			"gold", "liquidity", "vix", "erp", "cape", "credit"
		--period (str): Historical period (default: "5y")

	For scenario:
		(no arguments required — combines regime + divergence + analog)

	For dashboard:
		(no arguments required)

Returns:
	For regime:
		dict: {
			"regime": str (earnings_cycle|reverse_financial|reverse_earnings|liquidity_flow|grey_zone),
			"regime_confidence": str (HIGH|MEDIUM|LOW),
			"sub_regime": str or null,
			"signals": {
				"rate_regime": dict,
				"dollar": dict,
				"cross_asset": dict,
				"real_economy": dict
			},
			"regime_scores": {regime_name: float},
			"missing_components": [str],
			"hard_gate": {
				"grey_zone": bool,
				"reason": str or null
			}
		}

	For divergence:
		dict: {
			"pairs_analyzed": int,
			"divergences": [
				{
					"pair": str,
					"current_correlation": float,
					"historical_mean": float,
					"zscore": float,
					"status": str (normal|elevated|extreme|critical),
					"direction": str
				}
			],
			"critical_divergences": int,
			"supplementary": dict,
			"regime_implication": str or null,
			"missing_components": [str]
		}

	For analog:
		dict: {
			"target": str,
			"top_analogs": [
				{
					"period": str,
					"correlation": float,
					"forward_mean_return": float,
					"forward_25_75_range": [float, float],
					"forward_10_90_range": [float, float]
				}
			],
			"fan_chart_summary": dict,
			"macro_condition_match": dict,
			"missing_components": [str]
		}

	For deep-dive:
		dict: {
			"indicator": str,
			"current_value": float or dict,
			"historical_percentile": float,
			"zscore": float,
			"trend": str,
			"regime_interpretation": str,
			"components": dict,
			"missing_components": [str]
		}

	For scenario:
		dict: {
			"regime": dict,
			"divergences": dict,
			"analogs": dict,
			"scenarios": [
				{
					"name": str,
					"probability": float,
					"description": str,
					"key_signals": [str],
					"invalidation": str
				}
			],
			"composite_signal": str,
			"confidence": str,
			"missing_components": [str]
		}

	For dashboard:
		dict: {
			"timestamp": str,
			"regime_snapshot": dict,
			"key_levels": dict,
			"critical_signals": [str],
			"missing_components": [str]
		}

Example:
	>>> python sidneykim0.py regime --extended
	{
		"regime": "reverse_financial",
		"regime_confidence": "HIGH",
		"sub_regime": "bad_is_bad",
		"signals": {
			"rate_regime": {"us10y": 4.45, "curve_shape": "bear_steepening", ...},
			"dollar": {"dxy": 104.2, "trend": "rising", ...},
			"cross_asset": {"erp": 0.3, "vix_regime": "anxious", ...},
			"real_economy": {"bdi_zscore": -1.2, ...}
		},
		"regime_scores": {"earnings_cycle": 15, "reverse_financial": 70, ...}
	}

	>>> python sidneykim0.py divergence
	{
		"pairs_analyzed": 3,
		"divergences": [
			{"pair": "Safe Haven (GLD / SPY)", "zscore": 2.8, "status": "critical", ...}
		],
		"critical_divergences": 1
	}

	>>> python sidneykim0.py analog --target ^GSPC --window 150
	{
		"target": "^GSPC",
		"top_analogs": [
			{"period": "1997-10", "correlation": 0.87, "forward_mean_return": -3.2, ...}
		]
	}

	>>> python sidneykim0.py deep-dive rates
	{
		"indicator": "rates",
		"current_value": {"us10y": 4.45, "us2y": 4.22},
		"historical_percentile": 88.5,
		"zscore": 1.7,
		"trend": "rising"
	}

	>>> python sidneykim0.py scenario
	{
		"regime": {...},
		"scenarios": [
			{"name": "Base: Reverse Financial Persists", "probability": 55, ...},
			{"name": "Alt: EM Crisis Triggers Fed Cut", "probability": 30, ...}
		],
		"composite_signal": "CAUTIOUS",
		"confidence": "MEDIUM"
	}

	>>> python sidneykim0.py dashboard
	{
		"timestamp": "2026-02-25T10:30:00",
		"regime_snapshot": {"regime": "reverse_financial", "confidence": "HIGH"},
		"key_levels": {"us10y": 4.45, "dxy": 104.2, "erp": 0.3, ...},
		"critical_signals": ["ERP near zero", "Gold-DXY simultaneous rise"]
	}

Use Cases:
	- Daily macro regime assessment before any individual asset analysis
	- Cross-asset divergence monitoring for regime transition detection
	- Historical analog matching for probabilistic scenario construction
	- Deep-dive into specific macro indicators with Z-score context
	- Integrated scenario generation combining all analytical dimensions
	- Quick macro dashboard for pre-market assessment

Notes:
	- Unlike stock-focused pipelines, no ticker argument is required for most subcommands
	- regime subcommand runs 6-8 parallel macro scripts for speed
	- divergence uses analysis/divergence.py typed subcommands (yield-equity, safe-haven, sector-commodity)
	- analog uses technical/pattern/multi_dtw.py and technical/pattern/fanchart.py
	- deep-dive routes to specific macro scripts based on indicator type
	- scenario combines regime + divergence + analog into weighted scenarios
	- dashboard is a lightweight version of scenario for quick assessment
	- All subcommands use graceful degradation (missing_components reported)
	- Output is compressed: raw data excluded, insights and evidence included
	- Scripts execute in parallel via ThreadPoolExecutor
"""

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import output_json, safe_run

SCRIPTS_DIR = os.path.dirname(os.path.dirname(__file__))


def _run_script(script_path, args_list):
	"""Run a script and capture its JSON output.

	If script_path starts with '-m:', use module invocation (python -m module_name).
	Otherwise, run the script file directly.
	"""
	if script_path.startswith("-m:"):
		module_name = script_path[3:]
		cmd = [sys.executable, "-m", module_name] + args_list
		env = os.environ.copy()
		env["PYTHONPATH"] = SCRIPTS_DIR + os.pathsep + env.get("PYTHONPATH", "")
	else:
		full_path = os.path.join(SCRIPTS_DIR, script_path)
		cmd = [sys.executable, full_path] + args_list
		env = None

	try:
		result = subprocess.run(
			cmd,
			capture_output=True,
			text=True,
			timeout=300,
			cwd=SCRIPTS_DIR,
			env=env,
		)
		if result.returncode == 0 and result.stdout.strip():
			return json.loads(result.stdout)
		else:
			return {"error": result.stderr.strip() or "Script returned no output"}
	except subprocess.TimeoutExpired:
		return {"error": "Script timed out (300s)"}
	except json.JSONDecodeError:
		return {"error": "Invalid JSON output from script"}
	except Exception as e:
		return {"error": str(e)}


def _run_parallel(tasks):
	"""Run multiple script tasks in parallel.

	Args:
		tasks: list of (name, script_path, args_list)

	Returns:
		dict: {name: result_dict}
	"""
	results = {}
	with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
		futures = {
			executor.submit(_run_script, path, args): name
			for name, path, args in tasks
		}
		for future in concurrent.futures.as_completed(futures):
			name = futures[future]
			try:
				results[name] = future.result()
			except Exception as e:
				results[name] = {"error": str(e)}
	return results


def _safe_get(data, *keys, default=None):
	"""Safely navigate nested dict."""
	current = data
	for key in keys:
		if isinstance(current, dict):
			current = current.get(key, default)
		else:
			return default
	return current


# ---------------------------------------------------------------------------
# Regime Classification Logic
# ---------------------------------------------------------------------------

def _classify_regime(signals):
	"""Classify macro regime from collected signals.

	Returns:
		dict with regime, regime_confidence, sub_regime, regime_scores, hard_gate
	"""
	scores = {
		"earnings_cycle": 0,
		"reverse_financial": 0,
		"reverse_earnings": 0,
		"liquidity_flow": 0,
	}

	# Rate regime signals
	rate = signals.get("rate_regime", {})
	if not rate.get("error"):
		erp = rate.get("erp_pct")
		if erp is not None:
			if erp > 2.0:
				scores["earnings_cycle"] += 20
			elif erp > 0.5:
				scores["earnings_cycle"] += 10
			elif erp > 0:
				scores["reverse_financial"] += 15
			else:
				scores["reverse_financial"] += 25

		vix_regime = rate.get("vix_regime", "")
		if vix_regime == "complacent":
			scores["earnings_cycle"] += 10
		elif vix_regime == "normal":
			scores["earnings_cycle"] += 5
		elif vix_regime == "anxious":
			scores["reverse_financial"] += 10
		elif vix_regime == "panic":
			scores["reverse_earnings"] += 15

		net_liq = rate.get("net_liq_direction", "")
		if net_liq == "expanding":
			scores["earnings_cycle"] += 10
		elif net_liq == "contracting":
			scores["reverse_financial"] += 10
			scores["reverse_earnings"] += 5

	# Dollar signals
	dollar = signals.get("dollar", {})
	if not dollar.get("error"):
		dxy_trend = dollar.get("trend", "")
		if dxy_trend == "rising":
			scores["liquidity_flow"] += 15
			scores["reverse_financial"] += 5
		elif dxy_trend == "falling":
			scores["earnings_cycle"] += 10

		dxy_zscore = dollar.get("zscore", 0)
		if dxy_zscore > 1.5:
			scores["liquidity_flow"] += 10

	# Cross-asset signals
	cross = signals.get("cross_asset", {})
	if not cross.get("error"):
		fear_greed = cross.get("fear_greed_score")
		if fear_greed is not None:
			if fear_greed > 70:
				scores["earnings_cycle"] += 10
			elif fear_greed < 30:
				scores["reverse_earnings"] += 10
				scores["reverse_financial"] += 5

		putcall = cross.get("putcall_ratio")
		if putcall is not None:
			if putcall < 0.6:
				scores["earnings_cycle"] += 5
			elif putcall > 1.0:
				scores["reverse_earnings"] += 10

	# Real economy signals
	real = signals.get("real_economy", {})
	if not real.get("error"):
		bdi_zscore = real.get("bdi_zscore", 0)
		if bdi_zscore < -1.5:
			scores["reverse_earnings"] += 15
		elif bdi_zscore > 1.0:
			scores["earnings_cycle"] += 10

	# Determine regime
	max_score = max(scores.values())
	regime_name = max(scores, key=scores.get)

	# Confidence assessment
	sorted_scores = sorted(scores.values(), reverse=True)
	gap = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else 0

	if gap >= 20 and max_score >= 40:
		confidence = "HIGH"
	elif gap >= 10 and max_score >= 25:
		confidence = "MEDIUM"
	else:
		confidence = "LOW"

	# Grey zone hard gate
	hard_gate = {"grey_zone": False, "reason": None}
	if confidence == "LOW" or max_score < 20:
		hard_gate["grey_zone"] = True
		hard_gate["reason"] = f"Mixed signals: top regime '{regime_name}' scored only {max_score}, gap to second is {gap}"
		regime_name = "grey_zone"

	# Sub-regime detection
	sub_regime = None
	if regime_name == "earnings_cycle":
		if rate.get("erp_pct") and rate["erp_pct"] > 2.0:
			sub_regime = "good_is_good"
		else:
			sub_regime = "bad_is_good"
	elif regime_name == "reverse_financial":
		if rate.get("vix_regime") in ("panic", "anxious") and rate.get("erp_pct", 1) < 0.5:
			sub_regime = "bad_is_bad_broken"
		else:
			sub_regime = "higher_for_longer"

	return {
		"regime": regime_name,
		"regime_confidence": confidence,
		"sub_regime": sub_regime,
		"regime_scores": scores,
		"hard_gate": hard_gate,
	}


def _determine_composite_signal(regime_data, divergence_count, analog_direction):
	"""Determine composite signal from integrated analysis."""
	regime = regime_data.get("regime", "grey_zone")
	confidence = regime_data.get("regime_confidence", "LOW")

	if regime == "grey_zone":
		return "NEUTRAL"

	if regime == "earnings_cycle" and confidence == "HIGH" and divergence_count == 0:
		return "RISK_ON"
	elif regime == "reverse_financial" and confidence == "HIGH":
		return "CAUTIOUS"
	elif regime == "reverse_earnings":
		return "RISK_OFF"
	elif regime == "liquidity_flow":
		return "US_OVERWEIGHT"
	elif divergence_count >= 2:
		return "TRANSITION_WATCH"
	else:
		return "NEUTRAL"


# ---------------------------------------------------------------------------
# Subcommand: regime
# ---------------------------------------------------------------------------

@safe_run
def cmd_regime(args):
	"""Macro regime classification with confidence scoring."""
	tasks = [
		("erp", "macro/erp.py", ["erp"]),
		("vix_curve", "macro/vix_curve.py", ["analyze"]),
		("net_liquidity", "macro/net_liquidity.py", ["net-liquidity"]),
		("fear_greed", "analysis/sentiment/fear_greed.py", []),
		("putcall", "analysis/putcall_ratio.py", ["SPY"]),
		("cape", "valuation/cape.py", ["get-current"]),
	]

	if args.extended:
		tasks.extend([
			("bdi", "data_sources/bdi.py", []),
			("dxy", "data_sources/dxy.py", []),
		])

	raw = _run_parallel(tasks)
	missing = [k for k, v in raw.items() if v.get("error")]

	# Build signal structure
	signals = {
		"rate_regime": {},
		"dollar": {},
		"cross_asset": {},
		"real_economy": {},
	}

	# Rate regime
	erp_data = raw.get("erp", {})
	if not erp_data.get("error"):
		signals["rate_regime"]["erp_pct"] = _safe_get(erp_data, "current", "erp")
		signals["rate_regime"]["us10y"] = _safe_get(erp_data, "current", "us10y")
		signals["rate_regime"]["earnings_yield"] = _safe_get(erp_data, "current", "earnings_yield")

	vix_data = raw.get("vix_curve", {})
	if not vix_data.get("error"):
		signals["rate_regime"]["vix_spot"] = vix_data.get("vix_spot")
		signals["rate_regime"]["vix_regime"] = vix_data.get("regime")
		signals["rate_regime"]["vix_structure"] = vix_data.get("term_structure")

	liq_data = raw.get("net_liquidity", {})
	if not liq_data.get("error"):
		signals["rate_regime"]["net_liq_direction"] = _safe_get(liq_data, "net_liquidity", "direction")
		signals["rate_regime"]["net_liq_current"] = _safe_get(liq_data, "net_liquidity", "current")

	cape_data = raw.get("cape", {})
	if not cape_data.get("error"):
		signals["cross_asset"]["cape"] = cape_data.get("cape")

	# Cross-asset
	fg_data = raw.get("fear_greed", {})
	if not fg_data.get("error"):
		signals["cross_asset"]["fear_greed_score"] = _safe_get(fg_data, "current", "score")

	pc_data = raw.get("putcall", {})
	if not pc_data.get("error"):
		signals["cross_asset"]["putcall_ratio"] = pc_data.get("put_call_ratio")

	# Dollar
	dxy_data = raw.get("dxy", {})
	if not dxy_data.get("error") and dxy_data:
		dxy_zscore = _safe_get(dxy_data, "statistics", "z_score", default=0)
		signals["dollar"]["dxy_value"] = dxy_data.get("current_value")
		signals["dollar"]["zscore"] = dxy_zscore
		signals["dollar"]["trend"] = "rising" if dxy_zscore > 0.5 else ("falling" if dxy_zscore < -0.5 else "neutral")

	# Real economy
	bdi_data = raw.get("bdi", {})
	if not bdi_data.get("error") and bdi_data:
		signals["real_economy"]["bdi_zscore"] = _safe_get(bdi_data, "statistics", "z_score", default=0)
		signals["real_economy"]["bdi_value"] = bdi_data.get("current_value")

	# Classify regime
	classification = _classify_regime(signals)

	output_json({
		"regime": classification["regime"],
		"regime_confidence": classification["regime_confidence"],
		"sub_regime": classification["sub_regime"],
		"signals": signals,
		"regime_scores": classification["regime_scores"],
		"hard_gate": classification["hard_gate"],
		"missing_components": missing,
	})


# ---------------------------------------------------------------------------
# Subcommand: divergence
# ---------------------------------------------------------------------------

@safe_run
def cmd_divergence(args):
	"""Cross-asset divergence/convergence scan using typed subcommands."""
	window = str(args.window)

	tasks = [
		("yield_equity", "analysis/divergence.py", ["yield-equity", "--window", window]),
		("safe_haven", "analysis/divergence.py", ["safe-haven", "--window", window]),
		("sector_commodity", "analysis/divergence.py", ["sector-commodity", "--window", window]),
		("vix_zscore", "statistics/zscore.py", ["^VIX"]),
		("gold_zscore", "statistics/zscore.py", ["GC=F"]),
		("dxy_data", "data_sources/dxy.py", []),
	]

	raw = _run_parallel(tasks)
	missing = [k for k, v in raw.items() if v.get("error")]

	DIVERGENCE_LABELS = {
		"yield_equity": "Yield vs Equity (^TNX / SPY)",
		"safe_haven": "Safe Haven (GLD / SPY)",
		"sector_commodity": "Sector vs Commodity (XLB / DBC)",
	}

	divergences = []
	critical_count = 0

	for key in ["yield_equity", "safe_haven", "sector_commodity"]:
		result = raw.get(key, {})
		if result.get("error"):
			continue

		corr = result.get("correlation_analysis", {})
		zscore = corr.get("correlation_zscore", 0)
		current_corr = corr.get("current_correlation", 0)
		hist_mean = corr.get("correlation_mean", 0)
		div_type = result.get("divergence_type", "unknown")

		abs_z = abs(zscore) if zscore else 0
		if abs_z >= 3:
			status = "critical"
			critical_count += 1
		elif abs_z >= 2:
			status = "extreme"
		elif abs_z >= 1.5:
			status = "elevated"
		else:
			status = "normal"

		divergences.append({
			"pair": DIVERGENCE_LABELS.get(key, key),
			"current_correlation": round(current_corr, 3) if current_corr else None,
			"historical_mean": round(hist_mean, 3) if hist_mean else None,
			"zscore": round(zscore, 2) if zscore else None,
			"status": status,
			"direction": div_type,
		})

	# Sort by absolute Z-score descending
	divergences.sort(key=lambda x: abs(x.get("zscore") or 0), reverse=True)

	# Supplementary context from z-score modules
	supplementary = {}
	vix_z = raw.get("vix_zscore", {})
	if not vix_z.get("error"):
		supplementary["vix_zscore"] = vix_z.get("z_score")

	gold_z = raw.get("gold_zscore", {})
	if not gold_z.get("error"):
		supplementary["gold_zscore"] = gold_z.get("z_score")

	dxy = raw.get("dxy_data", {})
	if not dxy.get("error"):
		supplementary["dxy_value"] = dxy.get("current_value")
		supplementary["dxy_zscore"] = _safe_get(dxy, "statistics", "z_score")

	regime_implication = None
	if critical_count >= 2:
		regime_implication = "Multiple critical divergences suggest regime transition in progress"
	elif critical_count == 1:
		regime_implication = "Single critical divergence detected — monitor for spread to other pairs"

	output_json({
		"pairs_analyzed": 3,
		"divergences": divergences,
		"critical_divergences": critical_count,
		"supplementary": supplementary,
		"regime_implication": regime_implication,
		"missing_components": missing,
	})


# ---------------------------------------------------------------------------
# Subcommand: analog
# ---------------------------------------------------------------------------

@safe_run
def cmd_analog(args):
	"""Historical analog matching with forward return fan chart."""
	target = args.target
	window = str(args.window)
	forward = str(args.forward)

	tasks = [
		("pattern", "-m:technical.pattern", [
			"multi-dtw", target, "--window", window, "--top-n", "5"
		]),
		("fanchart", "-m:technical.pattern", [
			"fanchart", target, "--window", window, "--forward-days", forward
		]),
	]

	raw = _run_parallel(tasks)
	missing = [k for k, v in raw.items() if v.get("error")]

	top_analogs = []
	pattern_data = raw.get("pattern", {})
	if not pattern_data.get("error"):
		matches = pattern_data.get("top_similar_patterns", [])
		for match in matches[:5]:
			top_analogs.append({
				"period": match.get("window_start", "unknown"),
				"correlation": round(match.get("similarity_score", 0), 3),
				"features_used": match.get("features", []),
			})

	fan_chart = {}
	fc_data = raw.get("fanchart", {})
	if not fc_data.get("error"):
		fc_period = _safe_get(fc_data, "fan_chart", f"{forward}d", default={})
		fan_chart = {
			"forward_days": int(forward),
			"mean_return": fc_period.get("mean"),
			"median_return": fc_period.get("median"),
			"p25_return": fc_period.get("p25"),
			"p75_return": fc_period.get("p75"),
			"p10_return": fc_period.get("p10"),
			"p90_return": fc_period.get("p90"),
		}

	output_json({
		"target": target,
		"window": int(window),
		"top_analogs": top_analogs,
		"fan_chart_summary": fan_chart,
		"missing_components": missing,
	})


# ---------------------------------------------------------------------------
# Subcommand: deep-dive
# ---------------------------------------------------------------------------

@safe_run
def cmd_deep_dive(args):
	"""Deep-dive analysis on a specific indicator."""
	indicator = args.indicator.lower()

	INDICATOR_MAP = {
		"rates": [
			("rates", "data_advanced/fred/rates.py", ["yield-curve", "--maturities", "2y,10y,30y", "--limit", "5"]),
			("fedwatch", "data_advanced/fed/fedwatch.py", []),
			("erp", "macro/erp.py", ["erp"]),
		],
		"dollar": [
			("dxy", "data_sources/dxy.py", []),
			("dxy_zscore", "statistics/zscore.py", ["DX-Y.NYB"]),
		],
		"gold": [
			("gold_zscore", "statistics/zscore.py", ["GC=F"]),
			("gold_percentile", "statistics/percentile.py", ["GC=F"]),
			("silver_zscore", "statistics/zscore.py", ["SI=F"]),
		],
		"liquidity": [
			("net_liq", "macro/net_liquidity.py", ["net-liquidity"]),
		],
		"vix": [
			("vix_curve", "macro/vix_curve.py", ["analyze"]),
			("vix_zscore", "statistics/zscore.py", ["^VIX"]),
		],
		"erp": [
			("erp", "macro/erp.py", ["erp"]),
			("cape", "valuation/cape.py", ["get-current"]),
		],
		"cape": [
			("cape", "valuation/cape.py", ["get-current"]),
			("cape_hist", "valuation/cape_historical.py", ["get-current"]),
			("div_yield", "valuation/dividend_yield.py", ["sp500-yield"]),
		],
		"credit": [
			("fear_greed", "analysis/sentiment/fear_greed.py", []),
			("putcall", "analysis/putcall_ratio.py", ["SPY"]),
		],
	}

	if indicator not in INDICATOR_MAP:
		output_json({"error": f"Unknown indicator '{indicator}'. Valid: {list(INDICATOR_MAP.keys())}"})
		return

	tasks = INDICATOR_MAP[indicator]
	raw = _run_parallel(tasks)
	missing = [k for k, v in raw.items() if v.get("error")]

	# Extract primary value and Z-score
	current_value = None
	zscore = None
	percentile = None
	trend = None

	if indicator == "rates":
		erp_data = raw.get("erp", {})
		if not erp_data.get("error"):
			current_value = {
				"us10y": _safe_get(erp_data, "current", "us10y"),
				"erp": _safe_get(erp_data, "current", "erp"),
			}
		rates_data = raw.get("rates", {})
		if not rates_data.get("error"):
			if current_value is None:
				current_value = {}
			# Supplement with yield curve data (FRED series: DGS2, DGS10, DGS30)
			dgs2 = _safe_get(rates_data, "data", "DGS2", default={})
			if dgs2 and current_value.get("us2y") is None:
				current_value["us2y"] = list(dgs2.values())[-1] if dgs2 else None
			dgs30 = _safe_get(rates_data, "data", "DGS30", default={})
			if dgs30:
				current_value["us30y"] = list(dgs30.values())[-1] if dgs30 else None
	elif indicator == "dollar":
		dxy_data = raw.get("dxy", {})
		dxy_z = raw.get("dxy_zscore", {})
		if not dxy_data.get("error"):
			current_value = dxy_data.get("current_value")
		if not dxy_z.get("error"):
			zscore = dxy_z.get("z_score")
	elif indicator == "gold":
		gold_z = raw.get("gold_zscore", {})
		gold_p = raw.get("gold_percentile", {})
		if not gold_z.get("error"):
			current_value = gold_z.get("current_value")
			zscore = gold_z.get("z_score")
		if not gold_p.get("error"):
			percentile = gold_p.get("percentile_rank")
	elif indicator == "liquidity":
		liq = raw.get("net_liq", {})
		if not liq.get("error"):
			current_value = _safe_get(liq, "net_liquidity", "current")
			trend = _safe_get(liq, "net_liquidity", "direction")
	elif indicator == "vix":
		vix_c = raw.get("vix_curve", {})
		vix_z = raw.get("vix_zscore", {})
		if not vix_c.get("error"):
			current_value = vix_c.get("vix_spot")
			trend = vix_c.get("regime")
		if not vix_z.get("error"):
			zscore = vix_z.get("z_score")
	elif indicator == "erp":
		erp = raw.get("erp", {})
		if not erp.get("error"):
			current_value = _safe_get(erp, "current", "erp")
	elif indicator == "cape":
		cape = raw.get("cape", {})
		if not cape.get("error"):
			current_value = cape.get("cape")
	elif indicator == "credit":
		fg = raw.get("fear_greed", {})
		if not fg.get("error"):
			current_value = _safe_get(fg, "current", "score")

	output_json({
		"indicator": indicator,
		"current_value": current_value,
		"historical_percentile": percentile,
		"zscore": zscore,
		"trend": trend,
		"components": {k: v for k, v in raw.items() if not v.get("error")},
		"missing_components": missing,
	})


# ---------------------------------------------------------------------------
# Subcommand: scenario
# ---------------------------------------------------------------------------

@safe_run
def cmd_scenario(args):
	"""Integrated scenario construction combining regime + divergence + analog."""
	# Run regime + divergence + analog all in parallel
	tasks = [
		# Regime
		("erp", "macro/erp.py", ["erp"]),
		("vix_curve", "macro/vix_curve.py", ["analyze"]),
		("net_liquidity", "macro/net_liquidity.py", ["net-liquidity"]),
		("fear_greed", "analysis/sentiment/fear_greed.py", []),
		("putcall", "analysis/putcall_ratio.py", ["SPY"]),
		("cape", "valuation/cape.py", ["get-current"]),
		("dxy", "data_sources/dxy.py", []),
		("bdi", "data_sources/bdi.py", []),
		# Divergence (3 typed subcommands)
		("div_yield_equity", "analysis/divergence.py", ["yield-equity", "--window", "45"]),
		("div_safe_haven", "analysis/divergence.py", ["safe-haven", "--window", "45"]),
		("div_sector_commodity", "analysis/divergence.py", ["sector-commodity", "--window", "45"]),
		# Analog
		("pattern", "-m:technical.pattern", [
			"multi-dtw", "^GSPC", "--window", "150", "--top-n", "5"
		]),
		("fanchart", "-m:technical.pattern", [
			"fanchart", "^GSPC", "--window", "150", "--forward-days", "60"
		]),
	]

	# Execute all in parallel
	raw = _run_parallel(tasks)
	missing = [k for k, v in raw.items() if v.get("error")]

	# Build regime signals
	signals = {"rate_regime": {}, "dollar": {}, "cross_asset": {}, "real_economy": {}}

	erp_data = raw.get("erp", {})
	if not erp_data.get("error"):
		signals["rate_regime"]["erp_pct"] = _safe_get(erp_data, "current", "erp")
		signals["rate_regime"]["us10y"] = _safe_get(erp_data, "current", "us10y")

	vix_data = raw.get("vix_curve", {})
	if not vix_data.get("error"):
		signals["rate_regime"]["vix_regime"] = vix_data.get("regime")
		signals["rate_regime"]["vix_spot"] = vix_data.get("vix_spot")

	liq_data = raw.get("net_liquidity", {})
	if not liq_data.get("error"):
		signals["rate_regime"]["net_liq_direction"] = _safe_get(liq_data, "net_liquidity", "direction")

	fg_data = raw.get("fear_greed", {})
	if not fg_data.get("error"):
		signals["cross_asset"]["fear_greed_score"] = _safe_get(fg_data, "current", "score")

	pc_data = raw.get("putcall", {})
	if not pc_data.get("error"):
		signals["cross_asset"]["putcall_ratio"] = pc_data.get("put_call_ratio")

	cape_data = raw.get("cape", {})
	if not cape_data.get("error"):
		signals["cross_asset"]["cape"] = cape_data.get("cape")

	dxy_data = raw.get("dxy", {})
	if not dxy_data.get("error"):
		dxy_zscore = _safe_get(dxy_data, "statistics", "z_score", default=0)
		signals["dollar"]["dxy_value"] = dxy_data.get("current_value")
		signals["dollar"]["zscore"] = dxy_zscore
		signals["dollar"]["trend"] = "rising" if dxy_zscore > 0.5 else ("falling" if dxy_zscore < -0.5 else "neutral")

	bdi_data = raw.get("bdi", {})
	if not bdi_data.get("error"):
		signals["real_economy"]["bdi_zscore"] = _safe_get(bdi_data, "statistics", "z_score", default=0)

	# Classify regime
	regime_result = _classify_regime(signals)

	# Process divergences
	divergences = []
	critical_divs = 0
	for key in ["div_yield_equity", "div_safe_haven", "div_sector_commodity"]:
		val = raw.get(key, {})
		if val.get("error"):
			continue
		corr = val.get("correlation_analysis", {})
		z = corr.get("correlation_zscore", 0)
		abs_z = abs(z) if z else 0
		if abs_z >= 2:
			divergences.append({
				"pair": key.replace("div_", "").replace("_", " "),
				"zscore": round(z, 2),
				"status": "critical" if abs_z >= 3 else "extreme",
			})
			if abs_z >= 3:
				critical_divs += 1

	# Process analogs
	analogs = []
	pattern_data = raw.get("pattern", {})
	if not pattern_data.get("error"):
		for m in (pattern_data.get("top_similar_patterns", []))[:3]:
			analogs.append({
				"period": m.get("window_start", "unknown"),
				"correlation": round(m.get("similarity_score", 0), 3),
			})

	fan_chart = {}
	fc_data = raw.get("fanchart", {})
	if not fc_data.get("error"):
		fc_period = _safe_get(fc_data, "fan_chart", "60d", default={})
		fan_chart["mean_return"] = fc_period.get("mean")
		fan_chart["p25_75"] = [fc_period.get("p25"), fc_period.get("p75")]

	# Build scenarios (agent will refine these)
	analog_direction = fan_chart.get("mean_return", 0)
	analog_dir_label = "positive" if (analog_direction or 0) > 0 else "negative"

	scenarios = []
	regime = regime_result["regime"]

	if regime == "earnings_cycle":
		scenarios = [
			{
				"name": "Base: Earnings Cycle Continues",
				"probability": 60,
				"description": "Earnings growth supports current multiples. Rates stable.",
				"key_signals": ["ERP positive", "HY spreads tight", "Breadth expanding"],
				"invalidation": "ERP turns negative or credit spreads widen sharply",
			},
			{
				"name": "Alt: Transition to Reverse Financial",
				"probability": 30,
				"description": "Inflation re-accelerates, forcing higher-for-longer.",
				"key_signals": ["CPI above consensus", "FedWatch repricing fewer cuts"],
				"invalidation": "CPI continues declining and Fed signals cuts",
			},
		]
	elif regime == "reverse_financial":
		scenarios = [
			{
				"name": "Base: Higher-for-Longer Persists",
				"probability": 55,
				"description": "Rates remain elevated. Multiple compression continues.",
				"key_signals": ["ERP near zero", "CAPE > 35", "FedWatch: no cuts"],
				"invalidation": "Inflation drops sharply, enabling rate cuts",
			},
			{
				"name": "Alt: Crisis Triggers Fed Cut",
				"probability": 30,
				"description": "EM crisis or credit event forces emergency easing.",
				"key_signals": ["EM FX volatility spike", "HY spreads > 500bp"],
				"invalidation": "EM stabilizes without contagion",
			},
		]
	elif regime == "reverse_earnings":
		scenarios = [
			{
				"name": "Base: Earnings Recession",
				"probability": 50,
				"description": "Double compression — rates AND earnings disappoint.",
				"key_signals": ["Credit spreads widening", "Earnings cuts accelerating"],
				"invalidation": "Earnings stabilize and credit tightens",
			},
			{
				"name": "Alt: Policy Rescue",
				"probability": 35,
				"description": "Aggressive Fed action stabilizes markets.",
				"key_signals": ["Emergency rate cut", "Fiscal stimulus"],
				"invalidation": "Inflation prevents policy response",
			},
		]
	elif regime == "liquidity_flow":
		scenarios = [
			{
				"name": "Base: Wool-Shearing Continues",
				"probability": 55,
				"description": "US absorbs global liquidity. EM underperforms.",
				"key_signals": ["DXY rising", "EM FX weakening", "US rates higher than EM"],
				"invalidation": "DXY breaks below 100 and EM FX stabilizes",
			},
			{
				"name": "Alt: EM Stabilization",
				"probability": 25,
				"description": "EM policy response halts outflows.",
				"key_signals": ["EM central bank intervention", "Carry trade stabilizes"],
				"invalidation": "EM FX volatility continues rising",
			},
		]
	else:
		scenarios = [
			{
				"name": "Grey Zone: Await Resolution",
				"probability": 50,
				"description": "Signals mixed. No clear regime. Wait for resolution.",
				"key_signals": ["Watch credit spreads", "Watch DXY direction", "Watch VIX term structure"],
				"invalidation": "Clear regime emerges from signal convergence",
			},
		]

	composite = _determine_composite_signal(regime_result, critical_divs, analog_dir_label)

	output_json({
		"regime": {
			"classification": regime_result["regime"],
			"confidence": regime_result["regime_confidence"],
			"sub_regime": regime_result["sub_regime"],
			"scores": regime_result["regime_scores"],
		},
		"divergences": {
			"critical_count": critical_divs,
			"items": divergences,
		},
		"analogs": {
			"top_matches": analogs,
			"fan_chart": fan_chart,
		},
		"scenarios": scenarios,
		"composite_signal": composite,
		"confidence": regime_result["regime_confidence"],
		"missing_components": missing,
	})


# ---------------------------------------------------------------------------
# Subcommand: dashboard
# ---------------------------------------------------------------------------

@safe_run
def cmd_dashboard(args):
	"""Lightweight macro dashboard summary."""
	tasks = [
		("erp", "macro/erp.py", ["erp"]),
		("vix_curve", "macro/vix_curve.py", ["analyze"]),
		("cape", "valuation/cape.py", ["get-current"]),
		("fear_greed", "analysis/sentiment/fear_greed.py", []),
		("putcall", "analysis/putcall_ratio.py", ["SPY"]),
	]

	raw = _run_parallel(tasks)
	missing = [k for k, v in raw.items() if v.get("error")]

	# Build key levels
	key_levels = {}
	erp = raw.get("erp", {})
	if not erp.get("error"):
		key_levels["us10y"] = _safe_get(erp, "current", "us10y")
		key_levels["erp"] = _safe_get(erp, "current", "erp")
		key_levels["earnings_yield"] = _safe_get(erp, "current", "earnings_yield")

	vix = raw.get("vix_curve", {})
	if not vix.get("error"):
		key_levels["vix_spot"] = vix.get("vix_spot")
		key_levels["vix_regime"] = vix.get("regime")

	cape = raw.get("cape", {})
	if not cape.get("error"):
		key_levels["cape"] = cape.get("cape")

	fg = raw.get("fear_greed", {})
	if not fg.get("error"):
		key_levels["fear_greed"] = _safe_get(fg, "current", "score")

	pc = raw.get("putcall", {})
	if not pc.get("error"):
		key_levels["putcall_ratio"] = pc.get("put_call_ratio")

	# Critical signals
	critical = []
	if key_levels.get("erp") is not None and key_levels["erp"] < 0.5:
		critical.append(f"ERP at {key_levels['erp']:.1f}% — near zero, multiple compression risk")
	if key_levels.get("cape") is not None and key_levels["cape"] > 35:
		critical.append(f"CAPE at {key_levels['cape']:.1f} — in rejection zone (>35)")
	if key_levels.get("vix_regime") == "panic":
		critical.append(f"VIX in panic regime — elevated tail risk")
	if key_levels.get("putcall_ratio") is not None and key_levels["putcall_ratio"] < 0.6:
		critical.append(f"Put/Call at {key_levels['putcall_ratio']:.2f} — extreme bullish sentiment")
	if key_levels.get("fear_greed") is not None and key_levels["fear_greed"] < 25:
		critical.append(f"Fear & Greed at {key_levels['fear_greed']} — extreme fear")

	# Quick regime snapshot
	signals = {"rate_regime": {}, "dollar": {}, "cross_asset": {}, "real_economy": {}}
	if key_levels.get("erp") is not None:
		signals["rate_regime"]["erp_pct"] = key_levels["erp"]
	if key_levels.get("vix_regime"):
		signals["rate_regime"]["vix_regime"] = key_levels["vix_regime"]
	if key_levels.get("fear_greed") is not None:
		signals["cross_asset"]["fear_greed_score"] = key_levels["fear_greed"]
	if key_levels.get("putcall_ratio") is not None:
		signals["cross_asset"]["putcall_ratio"] = key_levels["putcall_ratio"]

	regime = _classify_regime(signals)

	output_json({
		"timestamp": datetime.now().isoformat(),
		"regime_snapshot": {
			"regime": regime["regime"],
			"confidence": regime["regime_confidence"],
			"sub_regime": regime["sub_regime"],
		},
		"key_levels": key_levels,
		"critical_signals": critical,
		"missing_components": missing,
	})


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
	parser = argparse.ArgumentParser(description="SidneyKim0 Macro-Statistical Pipeline")
	subparsers = parser.add_subparsers(dest="command", help="Pipeline subcommand")

	# regime
	p_regime = subparsers.add_parser("regime", help="Macro regime classification")
	p_regime.add_argument("--extended", action="store_true", help="Include BDI, DXY, commodities")

	# divergence
	p_div = subparsers.add_parser("divergence", help="Cross-asset divergence scan")
	p_div.add_argument("--window", type=int, default=45, help="Rolling correlation window (days)")

	# analog
	p_analog = subparsers.add_parser("analog", help="Historical analog matching")
	p_analog.add_argument("--target", type=str, default="^GSPC", help="Target asset")
	p_analog.add_argument("--window", type=int, default=150, help="Lookback window (days)")
	p_analog.add_argument("--forward", type=int, default=60, help="Forward projection (days)")

	# deep-dive
	p_dd = subparsers.add_parser("deep-dive", help="Deep-dive on specific indicator")
	p_dd.add_argument("indicator", type=str, help="rates|dollar|gold|liquidity|vix|erp|cape|credit")
	p_dd.add_argument("--period", type=str, default="5y", help="Historical period")

	# scenario
	p_scenario = subparsers.add_parser("scenario", help="Integrated scenario construction")

	# dashboard
	p_dash = subparsers.add_parser("dashboard", help="Lightweight macro dashboard")

	args = parser.parse_args()

	if args.command == "regime":
		cmd_regime(args)
	elif args.command == "divergence":
		cmd_divergence(args)
	elif args.command == "analog":
		cmd_analog(args)
	elif args.command == "deep-dive":
		cmd_deep_dive(args)
	elif args.command == "scenario":
		cmd_scenario(args)
	elif args.command == "dashboard":
		cmd_dashboard(args)
	else:
		parser.print_help()
		sys.exit(1)


if __name__ == "__main__":
	main()
