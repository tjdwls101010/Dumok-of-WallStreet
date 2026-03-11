"""Serenity pipeline command implementations."""

import concurrent.futures
from datetime import datetime, timedelta

from utils import output_json, safe_run

from ._runner import _run_script
from ._health import _extract_health_gates, _build_readiness_codes
from ._bottleneck import _build_l3_bottleneck
from ._valuation import _build_valuation_summary
from ._postprocess import (
	_summarize_insider_transactions, _extract_revenue_trajectory,
	_cap_earnings_dates, _compress_earnings_acceleration, _summarize_holders,
)
from ._macro import _classify_macro_regime
from ._control import (
	_build_materiality_signals, _build_causal_bridge_data,
	_build_priced_in_assessment, _build_institutional_flow, _build_expression_layer,
)
from ._signals import (
	_build_thesis_signals, _check_sop_triggers, _check_trapped_asset_override,
	_auto_classify_taxonomy, _generate_composite_signal,
)
from ._entity import _normalize_entity_name
from ._interpret import _interpret_bottleneck_signal, _interpret_rotation_assessment
from ._multi import _determine_relative_strengths, _parse_mcap_string


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

	# === Control Layer outputs ===
	materiality_signals = _build_materiality_signals(l3_data, l4_results, l5_results, sec_sc_results)
	causal_bridge_data = _build_causal_bridge_data(l1_result, l3_data, l4_results, l5_results, capex_data)
	priced_in_assessment = _build_priced_in_assessment(l4_results, l5_results)
	institutional_flow = _build_institutional_flow(l4_results)
	expression_layer = _build_expression_layer(l4_results, composite_signal)

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
		"materiality_signals": materiality_signals,
		"causal_bridge_data": causal_bridge_data,
		"priced_in_assessment": priced_in_assessment,
		"institutional_flow": institutional_flow,
		"expression_layer": expression_layer,
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

	# Step 7.5: Rotation Assessment
	forward_pe_data = l4_results.get("forward_pe") or {}
	ngv_data = l4_results.get("no_growth_valuation") or {}

	fpe_val = forward_pe_data.get("forward_pe")
	ngv_upside = ngv_data.get("margin_of_safety_pct")

	rotation_flags = []
	if isinstance(fpe_val, (int, float)) and fpe_val > 50:
		rotation_flags.append("extreme_forward_pe")
	if isinstance(ngv_upside, (int, float)) and ngv_upside < -30:
		rotation_flags.append("deep_below_no_growth_floor")
	if isinstance(return_pct, (int, float)) and return_pct > 100:
		rotation_flags.append("position_doubled_check_asymmetry")
	if isinstance(return_pct, (int, float)) and return_pct < -30 and thesis_signals.get("net_direction") == "weakening":
		rotation_flags.append("losing_position_thesis_weakening")

	opportunity_cost_elevated = len(rotation_flags) >= 2

	suggestion = (
		"scan_alternatives" if opportunity_cost_elevated
		else "consider_trim" if len(rotation_flags) == 1
		else "maintain"
	)

	rotation_assessment = {
		"forward_pe": fpe_val,
		"no_growth_upside_pct": ngv_upside,
		"return_since_entry_pct": return_pct,
		"rotation_flags": rotation_flags,
		"opportunity_cost_elevated": opportunity_cost_elevated,
		"suggestion": suggestion,
		"thresholds": "rotation_flags: extreme_forward_pe(>50x) | deep_below_no_growth_floor(<-30%) | position_doubled(>100%) | losing+weakening(<-30%+weakening). suggestion: scan_alternatives(2+flags) | consider_trim(1flag) | maintain(0flags)",
		"interpretation": _interpret_rotation_assessment(rotation_flags, opportunity_cost_elevated, suggestion),
	}

	if opportunity_cost_elevated:
		action_signals.append("OPPORTUNITY_COST_ELEVATED")

	# Step 8: Verdict
	signal_count = len(action_signals)
	if signal_count == 0:
		if opportunity_cost_elevated:
			verdict = "MAINTAIN_BUT_SCAN"
			note = "Position healthy but opportunity cost may be elevated. Scan for better asymmetry."
		else:
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
		"rotation_assessment": rotation_assessment,
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
	skip_macro = getattr(args, "skip_macro", False)
	max_mcap_val = _parse_mcap_string(max_mcap)

	# Lightweight macro stress check (3 scripts only)
	macro_context = None
	if not skip_macro:
		mini_scripts = {
			"vix": ("macro/vix_curve.py", ["analyze"]),
			"fear_greed": ("analysis/sentiment/fear_greed.py", []),
			"net_liq": ("macro/net_liquidity.py", ["net-liquidity", "--limit", "5"]),
		}
		with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
			futs = {k: ex.submit(_run_script, p, a) for k, (p, a) in mini_scripts.items()}
			mini_macro = {k: f.result() for k, f in futs.items()}

		vix_regime = mini_macro.get("vix", {}).get("regime")
		fg_score = mini_macro.get("fear_greed", {}).get("current", {}).get("score")
		net_liq_dir = mini_macro.get("net_liq", {}).get("net_liquidity", {}).get("direction")

		stress_note = None
		if vix_regime in ("elevated", "crisis") or (isinstance(fg_score, (int, float)) and fg_score < 25):
			stress_note = "Market stress detected. Discovery should prioritize defensive/counter-cyclical sectors."
		elif vix_regime == "low" and isinstance(fg_score, (int, float)) and fg_score > 75:
			stress_note = "Euphoria regime. Discovery should check priced-in risk on popular themes."

		macro_context = {
			"vix_regime": vix_regime,
			"fear_greed": fg_score,
			"net_liq_direction": net_liq_dir,
			"stress_note": stress_note,
		}
	else:
		macro_context = {"skipped": True}

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
			"macro_context": macro_context,
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
			"discovery_workflow_note": (
				"WORKFLOW GUIDANCE: This output is candidate pool generation (Step 4 of 5). "
				"Serenity-faithful discovery follows: (1) macro stress check [included above], "
				"(2) supply chain stress mapping [agent WebSearch], (3) bottleneck hypothesis, "
				"(4) candidate generation [this output], (5) validation via analyze."
			),
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
		"macro_context": macro_context,
		"themes": themes,
		"total_themes": len(themes),
		"total_candidates": sum(len(t["candidates"]) for t in themes),
		"filters_applied": {"max_mcap": max_mcap, "top_groups": top_groups},
		"requires_agent_review": True,
		"note": "Automated theme discovery. Agent should evaluate supply chain relevance and apply 6-Criteria Scoring to promising candidates.",
		"discovery_workflow_note": (
			"WORKFLOW GUIDANCE: This output is candidate pool generation (Step 4 of 5). "
			"Serenity-faithful discovery follows: (1) macro stress check [included above], "
			"(2) supply chain stress mapping [agent WebSearch], (3) bottleneck hypothesis, "
			"(4) candidate generation [this output], (5) validation via analyze."
		),
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
			"thresholds": "strong: supplier_ref_pct>=50% AND single_source>0 | moderate: >=50% OR single_source>0 | weak: >=25% | low: <25%",
			"interpretation": _interpret_bottleneck_signal(assessment, supplier_pct, single_source_count),
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
		stable = sum(1 for d in valid_directions if d.lower() == "stable")
		total = len(valid_directions)

		if increasing == total:
			cascade_health = "strong_expansion"
			consistency = "aligned_up"
		elif decreasing == total:
			cascade_health = "contraction"
			consistency = "aligned_down"
		elif stable == total:
			cascade_health = "stable"
			consistency = "aligned_stable"
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
