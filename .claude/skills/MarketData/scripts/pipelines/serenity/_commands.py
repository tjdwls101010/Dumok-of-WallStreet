"""Serenity pipeline command implementations."""

import concurrent.futures
from datetime import datetime, timedelta

from utils import output_json, safe_run

from pipelines._runner import _run_script
from ._health import _extract_health_gates, _build_readiness_codes
from ._bottleneck import _build_l3_bottleneck
from ._valuation import _build_valuation_frame
from ._postprocess import (
	_summarize_insider_transactions, _extract_revenue_trajectory,
	_cap_earnings_dates, _compress_earnings_acceleration, _summarize_holders,
	_merge_earnings, _reformat_analyst_recommendations, _clean_analyst_revisions,
)
from ._macro import _classify_macro_regime
from ._control import (
	_build_materiality_signals, _build_causal_bridge,
	_build_priced_in_assessment, _build_institutional_flow, _build_expression_layer,
	_classify_iv_tier,
)
from ._signals import (
	_build_thesis_signals, _check_sop_triggers, _check_trapped_asset_override,
	_auto_classify_taxonomy, _generate_composite_signal,
	_detect_short_squeeze_risk, _classify_dilution,
)
from ._multi import _parse_mcap_string
from ._scorer import validate_ticker


@safe_run
def cmd_macro(args):
	"""Level 1 Macro Regime Assessment.

	Runs macro scripts in parallel to assess the current risk environment.
	Classifies regime as risk_on, risk_off, or transitional.
	"""
	scripts = {
		"net_liquidity": ("macro/net_liquidity.py", ["net-liquidity", "--limit", "10"]),
		"vix_curve": ("macro/vix_curve.py", ["analyze"]),
		"fedwatch": ("data_advanced/fred/fedwatch.py", []),
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
			"fedwatch": ("data_advanced/fred/fedwatch.py", []),
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
	l4_scripts = {
		"info": ("data_sources/info.py", ["get-info-fields", ticker,
			"sector", "industry", "marketCap", "enterpriseValue",
			"longBusinessSummary", "currentPrice", "beta",
			"fiftyTwoWeekLow", "fiftyTwoWeekHigh",
			"fiftyDayAverage", "twoHundredDayAverage",
			"sharesOutstanding", "floatShares", "shortPercentOfFloat",
			"priceToSalesTrailing12Months",
			"grossMargins", "operatingMargins",
			"heldPercentInsiders", "heldPercentInstitutions"]),
		"insider_transactions": ("data_sources/holders.py", [
			"get-insider-transactions", ticker]),
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
		"earnings_estimate": ("analysis/analysis.py", ["get-earnings-estimate", ticker]),
		"revenue_estimate": ("analysis/analysis.py", ["get-revenue-estimate", ticker]),
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

	# --- Build Hyperscaler CapEx Bridge Signal ---
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

	# --- Post-processing ---
	# Insider transactions summary
	insider_raw = l4_results.get("insider_transactions")
	if insider_raw and not (isinstance(insider_raw, dict) and insider_raw.get("error")):
		l4_results["insider_transactions"] = _summarize_insider_transactions(insider_raw)

	# Revenue trajectory from quarterly financials
	financials_raw = l4_results.pop("quarterly_financials", None)
	if financials_raw and not (isinstance(financials_raw, dict) and financials_raw.get("error")):
		l4_results["revenue_trajectory"] = _extract_revenue_trajectory(financials_raw)

	# Compress earnings_acceleration (remove symbol, code33_status)
	ea_raw = l4_results.get("earnings_acceleration")
	if ea_raw and not (isinstance(ea_raw, dict) and ea_raw.get("error")):
		l4_results["earnings_acceleration"] = _compress_earnings_acceleration(ea_raw)

	# Move capex_trend from L4 to L2
	capex_data = l4_results.pop("capex_trend", None)

	# --- L2: Flatten capex data ---
	l2_capex_flow = {}
	if capex_data and not capex_data.get("error"):
		symbols_list = capex_data.get("symbols") or []
		if symbols_list:
			sym = symbols_list[0]
			l2_capex_flow["quarters"] = sym.get("quarters", [])
			l2_capex_flow["direction"] = sym.get("direction")
			l2_capex_flow["latest_capex"] = sym.get("latest_capex")
			l2_capex_flow["avg_capex"] = sym.get("avg_capex")
	l2_capex_flow["hyperscaler_signal"] = hyperscaler_signal
	capex_direction = l2_capex_flow.get("direction")

	# --- L3: Bottleneck ---
	l3_data = _build_l3_bottleneck(sec_sc_results)
	bottleneck_pre_score = l3_data.get("bottleneck_pre_score")

	# --- Health gates (from L4) ---
	health_gates = _extract_health_gates(l4_results)

	# Conditional SEC filing check for active dilution
	sec_filing_result = None
	gate_flags = []
	for gate_name in ("bear_bull_paradox", "active_dilution", "no_growth_fail", "margin_collapse", "io_quality_concern"):
		if health_gates.get(gate_name) == "FLAG":
			gate_flags.append(gate_name)
	if "active_dilution" in gate_flags:
		sec_filing_result = _run_script(
			"data_advanced/sec/filings.py",
			[ticker, "--form", "S-3", "--limit", "5"]
		)
		if sec_filing_result and not sec_filing_result.get("error"):
			l4_results["sec_dilution_check"] = sec_filing_result

	# --- Derived signals ---
	thesis_signals = _build_thesis_signals(l4_results, l5_results)
	sop_triggers = _check_sop_triggers(l4_results)
	trapped_asset_override = _check_trapped_asset_override(l4_results, bottleneck_pre_score, sec_sc_results)
	auto_classification = _auto_classify_taxonomy(l4_results, bottleneck_pre_score)

	composite_signal = _generate_composite_signal(
		l1_result, l4_results, l5_results,
		health_gates.get("severity_score"),
		bottleneck_pre_score, thesis_signals,
		auto_classification, trapped_asset_override,
	)

	# Materiality signals
	materiality = _build_materiality_signals(l3_data, l4_results, l5_results)
	priced_in = _build_priced_in_assessment(l4_results, l5_results)
	inst_flow = _build_institutional_flow(l4_results)
	expression = _build_expression_layer(l4_results, composite_signal)
	valuation_frame = _build_valuation_frame(l4_results)

	# Causal bridge (flat dashboard)
	causal_bridge = _build_causal_bridge(
		l1_result, l3_data, l4_results, l5_results,
		capex_direction, materiality, thesis_signals,
	)
	causal_bridge["L4_health_severity"] = health_gates.get("severity_score")
	causal_bridge["L6_classification"] = auto_classification.get("classification")

	# SoP triggered flag
	composite_signal["sop_triggered"] = sop_triggers.get("triggered", False)

	# --- Build L3 materiality into L3 output ---
	l3_data["materiality"] = {
		"supply_chain_verdict": materiality.get("supply_chain_verdict"),
		"sec_events_verdict": materiality.get("sec_events_verdict"),
	}

	# === L4: Build 5-cluster structure ===
	info = l4_results.get("info") or {}
	fpe = l4_results.get("forward_pe") or {}
	ngv = l4_results.get("no_growth_valuation") or {}
	ea = l4_results.get("earnings_acceleration") or {}
	sbc = l4_results.get("sbc_analyzer") or {}
	debt = l4_results.get("debt_structure") or {}
	margin = l4_results.get("margin_tracker") or {}
	iq = l4_results.get("institutional_quality") or {}
	iv = l4_results.get("iv_context") or {}
	rev_traj = l4_results.get("revenue_trajectory") or {}
	insider = l4_results.get("insider_transactions") or {}

	# Profile: key info fields (deduplicated)
	profile = {}
	for field in ("sector", "industry", "marketCap", "enterpriseValue",
				  "longBusinessSummary", "currentPrice", "beta",
				  "fiftyTwoWeekLow", "fiftyTwoWeekHigh",
				  "fiftyDayAverage", "twoHundredDayAverage",
				  "sharesOutstanding", "floatShares", "shortPercentOfFloat",
				  "priceToSalesTrailing12Months"):
		if field in info:
			profile[field] = info[field]

	# Valuation: forward_pe + no_growth_valuation (remove symbol, duplicates)
	valuation_cluster = {}
	if not fpe.get("error"):
		for k, v in fpe.items():
			if k not in ("symbol", "current_price", "valuation_gap", "gross_margin_pct", "error"):
				valuation_cluster[k] = v
	if not ngv.get("error"):
		ngv_clean = {}
		for k, v in ngv.items():
			if k not in ("symbol", "error"):
				ngv_clean[k] = v
		valuation_cluster["no_growth"] = ngv_clean

	# Earnings Growth: earnings_acceleration + revenue_trajectory + sbc
	earnings_growth = {}
	if not ea.get("error"):
		ea_clean = {k: v for k, v in ea.items() if k not in ("symbol", "code33_status", "error")}
		earnings_growth.update(ea_clean)
	if rev_traj:
		earnings_growth["revenue_trajectory"] = rev_traj
	if not sbc.get("error"):
		sbc_clean = {}
		for k, v in sbc.items():
			if k not in ("symbol", "sbc_interpretation", "shares_outstanding_current",
						  "shares_change_qoq_pct", "error"):
				sbc_clean[k] = v
		earnings_growth["sbc"] = sbc_clean

	# Financial Health: debt_structure + margin_tracker + dilution classification
	financial_health = {}
	if not debt.get("error"):
		debt_clean = {k: v for k, v in debt.items()
					  if k not in ("symbol", "grade_interpretation", "error")}
		financial_health["debt"] = debt_clean
	if not margin.get("error"):
		margin_clean = {k: v for k, v in margin.items()
						if k not in ("symbol", "margin_interpretation", "error")}
		financial_health["margins"] = margin_clean
	dilution_class = _classify_dilution(l4_results)
	if dilution_class.get("classification") != "unknown":
		financial_health["dilution"] = dilution_class

	# Market Structure: institutional_quality + iv_context + insider_transactions + short_squeeze + superinvestor
	market_structure = {}
	# Superinvestor (Dataroma) — via neutral module
	si_data = _run_script("data_sources/superinvestor.py", ["get-superinvestor-info", ticker])
	if isinstance(si_data, dict) and not si_data.get("error") and si_data.get("manager_count", 0) > 0:
		market_structure["superinvestor"] = si_data
	if not iq.get("error"):
		iq_clean = {k: v for k, v in iq.items()
					if k not in ("symbol", "io_interpretation", "error")}
		market_structure["institutional_quality"] = iq_clean
	if not iv.get("error"):
		iv_clean = {k: v for k, v in iv.items()
					if k not in ("symbol", "current_price", "interpretation", "error")}
		iv_tier = _classify_iv_tier(iv)
		iv_clean["iv_tier"] = iv_tier.get("iv_tier")
		iv_clean["iv_regime_shift"] = iv_tier.get("iv_regime_shift")
		iv_clean["iv_tier_thresholds"] = iv_tier.get("thresholds")
		market_structure["iv_context"] = iv_clean
	if insider:
		market_structure["insider_transactions"] = insider
	short_squeeze = _detect_short_squeeze_risk(l4_results)
	if short_squeeze.get("squeeze_risk") != "unknown":
		market_structure["short_squeeze"] = short_squeeze

	# L4 Assessment: health_gates + market_positioning
	l4_assessment = {
		"health_gates": health_gates,
		"market_positioning": {
			"priced_in": priced_in,
			"institutional_flow": inst_flow,
			"expression": expression,
		},
		"margin_materiality": materiality.get("margin_materiality"),
		"earnings_materiality": materiality.get("earnings_materiality"),
	}

	l4_fundamentals = {
		"profile": profile,
		"valuation": valuation_cluster,
		"earnings_growth": earnings_growth,
		"financial_health": financial_health,
		"market_structure": market_structure,
		"assessment": l4_assessment,
	}

	# === L5: Build cleaned catalysts ===
	# Merge earnings_dates + earnings_surprise
	earnings = _merge_earnings(
		l5_results.get("earnings_dates"),
		l5_results.get("earnings_surprise"),
	)

	# Analyst consensus (row-oriented)
	analyst_consensus = _reformat_analyst_recommendations(
		l5_results.get("analyst_recommendations"),
	)

	# Clean analyst_revisions (enriched with forward estimates)
	analyst_revisions = _clean_analyst_revisions(
		l5_results.get("analyst_revisions"),
		earnings_estimate=l5_results.get("earnings_estimate"),
		revenue_estimate=l5_results.get("revenue_estimate"),
	)

	# Analyst price targets (pass through)
	analyst_price_targets = l5_results.get("analyst_price_targets")

	l5_catalysts = {
		"earnings": earnings,
		"analyst_consensus": analyst_consensus,
		"analyst_price_targets": analyst_price_targets,
		"analyst_revisions": analyst_revisions,
		"assessment": {
			"thesis_signals": thesis_signals,
		},
	}

	# === Verdict ===
	verdict = {
		"composite_signal": composite_signal,
		"valuation_frame": valuation_frame,
		"causal_bridge": causal_bridge,
	}

	# === Final Output: 8 top-level keys ===
	output = {
		"ticker": ticker,
		"L1_macro": l1_result if l1_result else {"skipped": True},
		"L2_capex_flow": l2_capex_flow,
		"L3_bottleneck": l3_data,
		"L4_fundamentals": l4_fundamentals,
		"L5_catalysts": l5_catalysts,
		"L6_taxonomy": auto_classification,
		"verdict": verdict,
	}

	output_json(output)


def _extract_discover_metrics(ticker, script_results, si_data):
	"""Extract 22 discover comparator fields from script results."""
	info = script_results.get("info", {})
	rs = script_results.get("rs", {})
	code33 = script_results.get("code33", {})
	surprise = script_results.get("surprise", {})
	earnings_dates = script_results.get("earnings_dates", {})
	fwd_pe = script_results.get("forward_pe", {})
	no_growth = script_results.get("no_growth", {})
	sbc = script_results.get("sbc", {})
	debt = script_results.get("debt", {})
	iv = script_results.get("iv", {})
	insider = script_results.get("insider", {})

	# price_vs_52w_high
	current = info.get("currentPrice")
	high52 = info.get("fiftyTwoWeekHigh")
	price_vs_high = round((current / high52 - 1) * 100, 1) if current and high52 else None

	# eps_growth_pct from code33 growth rates
	growth_rates = code33.get("eps_growth_rates", [])
	eps_growth = growth_rates[0] if growth_rates else None

	# revenue_growth_pct — try code33 sales first, fallback to forward_pe
	sales_rates = code33.get("sales_growth_rates", [])
	rev_growth = sales_rates[0] if sales_rates else fwd_pe.get("revenue_growth_yoy")

	# operating_margin
	op_margin = info.get("operatingMargins")
	if isinstance(op_margin, (int, float)):
		op_margin = round(op_margin * 100, 2) if abs(op_margin) < 1 else round(op_margin, 2)

	# forward_pe
	fpe = fwd_pe.get("forward_1y_pe")

	# margin_of_safety_pct
	mos = no_growth.get("margin_of_safety_pct")

	# sbc
	sbc_pct = sbc.get("sbc_pct_revenue")

	# net_cash
	cash = debt.get("cash_and_equivalents")
	total_debt = debt.get("total_debt")
	net_cash_val = None
	if isinstance(cash, (int, float)) and isinstance(total_debt, (int, float)):
		net_cash_val = cash - total_debt

	# consecutive_beats & avg_surprise_pct & avg_er_gap
	history = surprise.get("history") or surprise.get("surprise_history") or []
	beats = surprise.get("consecutive_beats")
	avg_surp = surprise.get("avg_surprise_pct")
	er_gaps = [h.get("post_er_gap") for h in history if isinstance(h.get("post_er_gap"), (int, float))]
	avg_gap = round(sum(er_gaps) / len(er_gaps), 2) if er_gaps else None

	# days_to_earnings — find first future date from EPS Estimate keys
	days_to_er = None
	if isinstance(earnings_dates, dict) and not earnings_dates.get("error"):
		eps_est = earnings_dates.get("EPS Estimate", {})
		if isinstance(eps_est, dict):
			_now = datetime.now()
			for date_str in eps_est:
				try:
					er_date = datetime.fromisoformat(str(date_str))
					delta = (er_date.replace(tzinfo=None) - _now).days
					if delta >= 0:
						days_to_er = delta
						break
				except (ValueError, TypeError):
					continue

	# insider
	insider_summary = insider if isinstance(insider, dict) else {}
	if isinstance(insider_summary.get("summary"), dict):
		insider_dir = insider_summary["summary"].get("net_direction", "unknown")
	elif isinstance(insider, list):
		# Raw list from module — summarize
		filtered = [r for r in insider if isinstance(r, dict) and r.get("transaction") in ("Sale", "Buy")]
		buy_amt = sum(r.get("value", 0) or 0 for r in filtered if r.get("transaction") == "Buy")
		sell_amt = sum(r.get("value", 0) or 0 for r in filtered if r.get("transaction") == "Sale")
		if buy_amt > sell_amt * 1.2:
			insider_dir = "net_buying"
		elif sell_amt > buy_amt * 1.2:
			insider_dir = "net_selling"
		else:
			insider_dir = "mixed"
	else:
		insider_dir = "unknown"

	# superinvestor
	si = si_data.get(ticker, {})

	return {
		"ticker": ticker,
		"industry": info.get("industry"),
		"market_cap": info.get("marketCap"),
		"rs_score": rs.get("rs_rating"),
		"price_vs_52w_high_pct": price_vs_high,
		"eps_growth_pct": eps_growth,
		"revenue_growth_pct": rev_growth,
		"eps_accelerating": code33.get("eps_accelerating"),
		"operating_margin": op_margin,
		"forward_pe": fpe,
		"margin_of_safety_pct": mos,
		"sbc_pct_revenue": sbc_pct,
		"net_cash": net_cash_val,
		"consecutive_beats": beats,
		"avg_surprise_pct": avg_surp,
		"avg_er_gap": avg_gap,
		"days_to_earnings": days_to_er,
		"iv_rank": iv.get("iv_rank"),
		"insider_net_direction": insider_dir,
		"superinvestor_count": si.get("manager_count", 0),
		"superinvestor_adding": si.get("adding_count", 0),
		"superinvestor_reducing": si.get("reducing_count", 0),
		"superinvestor_avg_pct": si.get("avg_portfolio_pct", 0),
	}


def _collect_ticker_scripts(ticker):
	"""Run all discover metric scripts for a single ticker in parallel."""
	scripts = {
		"info": ("data_sources/info.py", [
			"get-info-fields", ticker,
			"industry", "marketCap", "currentPrice", "fiftyTwoWeekHigh", "operatingMargins"]),
		"rs": ("technical/rs_ranking.py", ["score", ticker]),
		"code33": ("data_sources/earnings_acceleration.py", ["code33", ticker]),
		"surprise": ("data_sources/earnings_acceleration.py", ["surprise", ticker]),
		"earnings_dates": ("data_sources/actions.py", ["get-earnings-dates", ticker, "--limit", "1"]),
		"forward_pe": ("analysis/forward_pe.py", ["calculate", ticker]),
		"no_growth": ("analysis/no_growth_valuation.py", ["calculate", ticker]),
		"sbc": ("analysis/sbc_analyzer.py", ["get-sbc", ticker]),
		"debt": ("analysis/debt_structure.py", ["analyze", ticker]),
		"iv": ("analysis/iv_context.py", ["analyze", ticker]),
		"insider": ("data_sources/holders.py", ["get-insider-transactions", ticker]),
	}
	with concurrent.futures.ThreadPoolExecutor(max_workers=len(scripts)) as ex:
		futs = {k: ex.submit(_run_script, p, a) for k, (p, a) in scripts.items()}
		return {k: f.result() for k, f in futs.items()}


@safe_run
def cmd_discover(args):
	"""Candidate Comparator — compare multiple tickers across 22 quantitative metrics.

	Takes a list of ticker symbols and runs key analysis modules on each in
	parallel, returning a comparison table for the agent to select analyze
	candidates. Superinvestor data loaded from Dataroma cache.

	All 22 fields are computed per ticker:
	industry, market_cap, rs_score, price_vs_52w_high_pct, eps_growth_pct,
	revenue_growth_pct, eps_accelerating, operating_margin, forward_pe,
	margin_of_safety_pct, sbc_pct_revenue, net_cash, consecutive_beats,
	avg_surprise_pct, avg_er_gap, days_to_earnings, iv_rank,
	insider_net_direction, superinvestor_count, superinvestor_adding,
	superinvestor_reducing, superinvestor_avg_pct.
	"""
	import time
	start_time = time.time()
	tickers = args.tickers

	# Load superinvestor data once (Dataroma cache)
	si_map = {}
	try:
		si_result = _run_script("data_sources/superinvestor.py", ["get-superinvestor-info", tickers[0]])
		# We need bulk load — run for all tickers
		with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tickers), 10)) as ex:
			si_futs = {t: ex.submit(_run_script, "data_sources/superinvestor.py", ["get-superinvestor-info", t]) for t in tickers}
			for t, f in si_futs.items():
				result = f.result()
				if isinstance(result, dict) and not result.get("error"):
					si_map[t] = result
	except Exception:
		pass

	# Run all metric scripts for all tickers in parallel
	with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tickers), 10)) as ex:
		ticker_futs = {t: ex.submit(_collect_ticker_scripts, t) for t in tickers}
		ticker_results = {t: f.result() for t, f in ticker_futs.items()}

	# Extract 22 fields per ticker
	candidates = []
	missing_data = {}
	for t in tickers:
		metrics = _extract_discover_metrics(t, ticker_results.get(t, {}), si_map)
		candidates.append(metrics)
		# Track missing fields
		missing = [k for k, v in metrics.items() if v is None and k not in ("industry",)]
		if missing:
			missing_data[t] = missing

	elapsed = round(time.time() - start_time, 1)

	output_json({
		"candidates": candidates,
		"thresholds": {
			"rs_score": "0-99, higher = stronger relative performance",
			"price_vs_52w_high_pct": "0 = at high, -50 = 50% below high",
			"eps_growth_pct": "latest quarterly EPS YoY %. null = no data",
			"revenue_growth_pct": "latest quarterly revenue YoY %",
			"operating_margin": "latest quarter %. negative = unprofitable",
			"forward_pe": "forward 1Y P/E. null = unprofitable",
			"margin_of_safety_pct": "no-growth fair value vs market cap (fail: <0% | caution: 0-20% | pass: >20%)",
			"sbc_pct_revenue": "SBC as % of revenue (healthy: <10% | warning: 10-30% | toxic: >30%)",
			"net_cash": "cash - total debt. positive = net cash, negative = net debt",
			"avg_er_gap": "average post-earnings gap %. high surprise + low gap = priced in",
			"iv_rank": "0-100 (compressed: <25 | elevated: >75)",
			"insider_net_direction": "net_buying | net_selling | mixed (buy > sell x 1.2)",
			"superinvestor_count": "Dataroma 81 tracked managers currently holding",
			"superinvestor_adding": "managers with Buy or Add activity in latest quarter",
			"superinvestor_reducing": "managers with Sell or Reduce activity in latest quarter",
			"superinvestor_avg_pct": "average portfolio % among holding managers (higher = more conviction)",
		},
		"missing_data": missing_data if missing_data else None,
		"metadata": {
			"total_candidates": len(candidates),
			"execution_time_seconds": elapsed,
		},
	})
