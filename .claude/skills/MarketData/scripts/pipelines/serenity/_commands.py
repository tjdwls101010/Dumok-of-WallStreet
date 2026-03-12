"""Serenity pipeline command implementations."""

import concurrent.futures
from datetime import datetime, timedelta

from utils import output_json, safe_run

from ._runner import _run_script
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
)
from ._signals import (
	_build_thesis_signals, _check_sop_triggers, _check_trapped_asset_override,
	_auto_classify_taxonomy, _generate_composite_signal,
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
			"longBusinessSummary", "currentPrice", "beta",
			"fiftyTwoWeekLow", "fiftyTwoWeekHigh",
			"fiftyDayAverage", "twoHundredDayAverage",
			"sharesOutstanding", "floatShares", "shortPercentOfFloat",
			"priceToSalesTrailing12Months",
			"grossMargins", "operatingMargins",
			"heldPercentInsiders", "heldPercentInstitutions"]),
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

	# Financial Health: debt_structure + margin_tracker
	financial_health = {}
	if not debt.get("error"):
		debt_clean = {k: v for k, v in debt.items()
					  if k not in ("symbol", "grade_interpretation", "error")}
		financial_health["debt"] = debt_clean
	if not margin.get("error"):
		margin_clean = {k: v for k, v in margin.items()
						if k not in ("symbol", "margin_interpretation", "error")}
		financial_health["margins"] = margin_clean

	# Market Structure: institutional_quality + iv_context + insider_transactions
	market_structure = {}
	if not iq.get("error"):
		iq_clean = {k: v for k, v in iq.items()
					if k not in ("symbol", "io_interpretation", "error")}
		market_structure["institutional_quality"] = iq_clean
	if not iv.get("error"):
		iv_clean = {k: v for k, v in iv.items()
					if k not in ("symbol", "current_price", "interpretation", "error")}
		market_structure["iv_context"] = iv_clean
	if insider:
		market_structure["insider_transactions"] = insider

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

	When --sector is provided, uses finviz sector-screen for broader sector-level
	discovery (absorbs former screen subcommand). Runs in parallel with macro
	context and discovery workflow guidance.
	"""
	top_groups = getattr(args, "top_groups", 5)
	max_mcap = getattr(args, "max_mcap", "10B")
	limit = getattr(args, "limit", 10)
	industry = getattr(args, "industry", None)
	sector = getattr(args, "sector", None)
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

	# Direct sector mode — finviz sector-screen (absorbs former cmd_screen)
	if sector:
		fv_result = _run_script("screening/finviz.py",
			["sector-screen", "--sector", sector, "--limit", "50"])

		if fv_result.get("error"):
			output_json({
				"macro_context": macro_context,
				"themes": [], "total_themes": 0, "total_candidates": 0,
				"filters_applied": {"sector": sector, "max_mcap": max_mcap},
				"requires_agent_review": False,
				"note": f"finviz sector-screen failed for '{sector}'.",
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
				"macro_context": macro_context,
				"themes": [], "total_themes": 0, "total_candidates": 0,
				"filters_applied": {"sector": sector, "max_mcap": max_mcap},
				"requires_agent_review": False,
				"note": f"No candidates passed mcap filter for sector '{sector}'.",
			})
			return

		filtered = filtered[:limit]

		with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
			bn_futures = {
				t: executor.submit(validate_ticker, t)
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
				"industry_group": sector,
				"sector": sector,
				"leader_count": None,
				"candidates": candidates,
			}],
			"total_themes": 1,
			"total_candidates": len(candidates),
			"filters_applied": {"sector": sector, "max_mcap": max_mcap},
			"requires_agent_review": True,
			"note": f"Direct sector search for '{sector}'. Agent should evaluate supply chain relevance.",
			"discovery_workflow_note": (
				"WORKFLOW GUIDANCE: This output is candidate pool generation (Step 4 of 5). "
				"Serenity-faithful discovery follows: (1) macro stress check [included above], "
				"(2) supply chain stress mapping [agent WebSearch], (3) bottleneck hypothesis, "
				"(4) candidate generation [this output], (5) validation via analyze."
			),
		})
		return

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
				t: executor.submit(validate_ticker, t)
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
			t: executor.submit(validate_ticker, t)
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
