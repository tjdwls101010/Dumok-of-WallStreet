"""Minervini SEPA pipeline command implementations.

Five subcommands implementing the complete SEPA (Specific Entry Point Analysis)
methodology by Mark Minervini.

All module calls are contained within the pipeline (Pipeline-Complete, Section 2.3).
Each module result is checked for errors and missing modules are tracked
(Graceful Degradation, Section 2.6).
"""

import concurrent.futures
import time

from utils import output_json, safe_run

from ._runner import _run_script
from ._sepa_scorer import compute_sepa_score
from ._risk_gate import compute_risk_assessment
from ._signals import determine_overall_signal
from ._postprocess import postprocess_results


# ---------------------------------------------------------------------------
# Module script definitions
# ---------------------------------------------------------------------------

def _analyze_scripts(ticker):
	"""Return the dict of all module scripts for cmd_analyze."""
	return {
		# Trend qualification
		"trend_template": ("screening/trend_template.py", ["check", ticker]),
		"stage_analysis": ("technical/stage_analysis.py", ["classify", ticker]),
		"rs_ranking": ("technical/rs_ranking.py", ["score", ticker]),
		"base_count": ("technical/base_count.py", ["count", ticker]),
		# Technical setup
		"vcp": ("technical/vcp.py", ["detect", ticker]),
		"entry_patterns": ("technical/entry_patterns.py", ["scan", ticker]),
		"pocket_pivot": ("technical/pocket_pivot.py", ["detect", ticker]),
		"low_cheat": ("technical/low_cheat.py", ["detect", ticker]),
		"tight_closes": ("technical/tight_closes.py", ["daily", ticker]),
		"volume_analysis": ("technical/volume_analysis.py", ["analyze", ticker]),
		"closing_range": ("technical/closing_range.py", ["analyze", ticker]),
		# Fundamentals
		"earnings_acceleration": ("data_sources/earnings_acceleration.py", ["code33", ticker]),
		"earnings_surprise": ("data_sources/earnings_acceleration.py", ["surprise", ticker]),
		"estimate_revisions": ("data_sources/earnings_acceleration.py", ["revisions", ticker]),
		"forward_pe": ("analysis/forward_pe.py", ["calculate", ticker]),
		"margin_tracker": ("analysis/margin_tracker.py", ["track", ticker]),
		"info": ("data_sources/info.py", [
			"get-info-fields", ticker,
			"sector", "industry", "marketCap", "currentPrice", "beta",
			"fiftyTwoWeekLow", "fiftyTwoWeekHigh",
			"fiftyDayAverage", "twoHundredDayAverage",
			"sharesOutstanding", "floatShares", "shortPercentOfFloat",
		]),
		# Risk
		"sell_signals": ("technical/sell_signals.py", ["check", ticker]),
		"stock_character": ("technical/stock_character.py", ["assess", ticker]),
	}


def _fix_rs_12m_null(rs_result):
	"""E.6: Change 12m return from 0 to null when data unavailable."""
	if not rs_result or rs_result.get("error"):
		return rs_result
	result = dict(rs_result)
	period_returns = result.get("period_returns", {})
	if isinstance(period_returns, dict):
		period_returns = dict(period_returns)
		# If data_quality is partial and 12m is 0, it means data unavailable
		if result.get("data_quality") == "partial" or result.get("periods_available", 4) < 4:
			if period_returns.get("12m") == 0:
				period_returns["12m"] = None
		result["period_returns"] = period_returns
	bench_returns = result.get("benchmark_returns", {})
	if isinstance(bench_returns, dict):
		bench_returns = dict(bench_returns)
		if result.get("data_quality") == "partial" or result.get("periods_available", 4) < 4:
			if bench_returns.get("12m") == 0:
				bench_returns["12m"] = None
		result["benchmark_returns"] = bench_returns
	return result


def _strip_null_fields(d):
	"""E.5: Remove null fields from a dict (recursive for nested dicts/lists)."""
	if isinstance(d, dict):
		return {k: _strip_null_fields(v) for k, v in d.items() if v is not None}
	elif isinstance(d, list):
		return [_strip_null_fields(item) for item in d]
	return d


# ---------------------------------------------------------------------------
# cmd_analyze
# ---------------------------------------------------------------------------

@safe_run
def cmd_analyze(args):
	"""Full SEPA analysis for a single ticker.

	Runs ~20 modules in parallel, computes SEPA composite score (0-100),
	risk assessment, and unified entry/exit signals.
	"""
	ticker = args.ticker.upper()
	start = time.time()

	scripts = _analyze_scripts(ticker)

	# Run all modules in parallel
	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		futures = {
			name: executor.submit(_run_script, path, a)
			for name, (path, a) in scripts.items()
		}
		results = {name: future.result() for name, future in futures.items()}

	# Track missing components
	missing = [k for k, v in results.items() if isinstance(v, dict) and v.get("error")]

	# E.6: Fix rs_ranking 12m null
	if "rs_ranking" in results:
		results["rs_ranking"] = _fix_rs_12m_null(results["rs_ranking"])

	# A.4: Use rs_ranking score as canonical — remove rs_score from trend_template
	rs_result = results.get("rs_ranking", {})
	tt_result = results.get("trend_template", {})
	if not tt_result.get("error") and isinstance(tt_result, dict):
		tt_result = dict(tt_result)
		tt_result.pop("rs_score", None)
		results["trend_template"] = tt_result

	# Position sizing (uses info for current price, VCP for stop)
	info = results.get("info", {})
	current_price = info.get("currentPrice")
	vcp = results.get("vcp", {})
	stop_pct = 7.0
	if not vcp.get("error") and vcp.get("vcp_detected") and vcp.get("pivot_price"):
		corrections = vcp.get("correction_depths", [])
		if corrections:
			stop_pct = min(corrections[-1], 10.0)

	if current_price and stop_pct > 0:
		pos_result = _run_script("analysis/position_sizing.py", [
			"calculate",
			"--account-size", "100000",
			"--entry-price", str(current_price),
			"--stop-loss-pct", str(stop_pct),
		])
		results["position_sizing"] = pos_result
	else:
		results["position_sizing"] = {"error": "missing current_price or stop_pct"}

	# Risk assessment (before postprocess so sell_signals raw is available)
	risk_data = compute_risk_assessment(results)

	# SEPA scoring (before postprocess)
	sepa_score = compute_sepa_score(results, risk_data)

	# Signal synthesis (before postprocess)
	signal = determine_overall_signal(results, sepa_score, risk_data)

	# Post-processing (compress before output)
	results = postprocess_results(results, mode="analyze")

	# --- Build output ---
	# D.1: Move rs_ranking into trend_qualification as rs_detail
	rs_data = results.get("rs_ranking", {})
	rs_detail = None
	if not isinstance(rs_data, dict) or not rs_data.get("error"):
		rs_detail = rs_data

	# A.4: Override TT's RS score with rs_ranking's canonical score
	tt_data = results.get("trend_template")
	if isinstance(tt_data, dict) and isinstance(rs_data, dict) and not rs_data.get("error"):
		canonical_rs = rs_data.get("rs_score")
		if canonical_rs is not None and "criteria" in tt_data:
			for c in tt_data["criteria"]:
				if c.get("id") == 8:
					c["value"] = f"RS Score = {canonical_rs}"
					c["passed"] = canonical_rs >= 70

	trend_qualification = {
		"trend_template": tt_data,
		"stage_analysis": results.get("stage_analysis"),
		"rs_detail": rs_detail,
		"base_count": results.get("base_count"),
	}

	technical_setup = {
		"vcp": results.get("vcp"),
		"entry_patterns": results.get("entry_patterns"),
		"pocket_pivot": results.get("pocket_pivot"),
		"low_cheat": results.get("low_cheat"),
		"tight_closes": results.get("tight_closes"),
		"volume_analysis": results.get("volume_analysis"),
		"closing_range": results.get("closing_range"),
	}

	# E.1: Map earnings_surprise and estimate_revisions to fundamentals
	# E.2: Map code33_status correctly
	ea = results.get("earnings_acceleration", {})
	code33_status = None
	if isinstance(ea, dict) and not ea.get("error"):
		code33_status = ea.get("code33_status")

	# Remove duplicate code33_status — keep it only inside earnings_acceleration
	fundamentals = {
		"earnings_acceleration": ea,
		"earnings_surprise": results.get("earnings_surprise") if not (results.get("earnings_surprise", {}) or {}).get("error") else None,
		"estimate_revisions": results.get("estimate_revisions") if not (results.get("estimate_revisions", {}) or {}).get("error") else None,
		"forward_pe": results.get("forward_pe"),
		"margin_tracker": results.get("margin_tracker"),
		"info": results.get("info"),
	}

	# D.2: risk_assessment contains sell_signals (active only, canonical), risk_gate, stock_character
	risk_assessment = {
		"sell_signals": results.get("sell_signals"),
		"stock_character": results.get("stock_character"),
		"risk_gate": risk_data,
	}

	elapsed = round(time.time() - start, 1)

	# E.3: missing_components as empty list, not null
	output = {
		"ticker": ticker,
		"sepa_score": sepa_score,
		"signal": signal,
		"trend_qualification": trend_qualification,
		"technical_setup": technical_setup,
		"fundamentals": fundamentals,
		"risk_assessment": risk_assessment,
		"metadata": {
			"missing_components": missing if missing else [],
			"modules_run": len(scripts) + 1,  # +1 for position_sizing
			"execution_time_seconds": elapsed,
		},
	}

	output_json(output)


# ---------------------------------------------------------------------------
# cmd_screen
# ---------------------------------------------------------------------------

@safe_run
def cmd_screen(args):
	"""Screen for SEPA candidates using Finviz presets.

	Screens stocks via Finviz, checks Trend Template on results, then
	runs Code 33 and RS ranking on TT-pass stocks. Returns sorted
	candidates with SEPA qualification scores.
	"""
	preset = getattr(args, "preset", "minervini_leaders")
	sector = getattr(args, "sector", None)
	industry = getattr(args, "industry", None)
	limit = getattr(args, "limit", 50)
	start = time.time()

	# Step 1: Finviz screen
	if industry:
		screen_result = _run_script("screening/finviz.py", [
			"industry-screen", "--industry", industry, "--limit", str(limit),
		])
	elif sector:
		screen_result = _run_script("screening/finviz.py", [
			"sector-screen", "--sector", sector, "--limit", str(limit),
		])
	else:
		screen_result = _run_script("screening/finviz.py", [
			"screen", "--preset", preset, "--limit", str(limit),
		])

	if screen_result.get("error"):
		output_json({"error": screen_result["error"], "stage": "finviz_screen"})
		return

	screened = screen_result.get("data", [])
	if not screened:
		output_json({"candidates": [], "metadata": {"total_screened": 0}})
		return

	tickers = [row.get("Ticker") for row in screened if row.get("Ticker")]

	# Step 2: Run trend_template.check on each in parallel
	def _check_tt(t):
		return t, _run_script("screening/trend_template.py", ["check", t])

	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		tt_results = dict(executor.map(lambda t: _check_tt(t), tickers))

	tt_pass = [t for t, r in tt_results.items()
				if not r.get("error") and r.get("overall_pass")]

	# Step 3: For TT-pass stocks, run Code 33 + RS ranking in parallel
	def _run_fundamentals(t):
		code33 = _run_script("data_sources/earnings_acceleration.py", ["code33", t])
		rs = _run_script("technical/rs_ranking.py", ["score", t])
		return t, code33, rs

	candidates = []
	if tt_pass:
		with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
			fund_futures = {t: executor.submit(_run_fundamentals, t) for t in tt_pass}
			for t, future in fund_futures.items():
				_, code33, rs = future.result()

				rs_score = rs.get("rs_score", 0) if not rs.get("error") else 0
				eps_accel = code33.get("eps_accelerating", False) if not code33.get("error") else False
				sales_accel = code33.get("sales_accelerating", False) if not code33.get("error") else False
				margin_exp = code33.get("margin_expanding", False) if not code33.get("error") else False

				# Simple screening score
				accel_count = sum([eps_accel, sales_accel, margin_exp])
				tt = tt_results.get(t, {})
				tt_score_pct = tt.get("score_pct", 0)
				screen_score = rs_score + (accel_count * 10)

				candidates.append({
					"ticker": t,
					"rs_score": rs_score,
					"tt_score_pct": tt_score_pct,
					"eps_accelerating": eps_accel,
					"sales_accelerating": sales_accel,
					"margin_expanding": margin_exp,
					"code33_accel_count": accel_count,
					"screen_score": screen_score,
				})

	# Sort by screen_score descending
	candidates.sort(key=lambda x: x.get("screen_score", 0), reverse=True)

	elapsed = round(time.time() - start, 1)

	output_json({
		"candidates": candidates,
		"thresholds": "screen_score = rs_score(0-99) + code33_accel_count(0-3) * 10",
		"metadata": {
			"total_screened": len(tickers),
			"tt_pass_count": len(tt_pass),
			"qualified_count": len(candidates),
			"preset": preset,
			"sector": sector,
			"industry": industry,
			"execution_time_seconds": elapsed,
		},
	})


# ---------------------------------------------------------------------------
# cmd_market_leaders
# ---------------------------------------------------------------------------

@safe_run
def cmd_market_leaders(args):
	"""Market leadership assessment.

	Runs sector_leaders.scan, Finviz market-breadth, and counts distribution
	days inline to produce a market environment verdict.
	"""
	start = time.time()

	# Run sector leaders + market breadth in parallel
	with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
		f_leaders = executor.submit(_run_script, "screening/sector_leaders.py", ["scan"])
		f_breadth = executor.submit(_run_script, "screening/finviz.py", ["market-breadth"])
		# SPY volume/price data for distribution day counting
		f_spy = executor.submit(_run_script, "technical/volume_analysis.py", ["analyze", "SPY"])

		leaders_result = f_leaders.result()
		breadth_result = f_breadth.result()
		spy_vol = f_spy.result()

	# Distribution day count from SPY volume analysis
	dist_days = 0
	if not spy_vol.get("error"):
		clusters = spy_vol.get("distribution_clusters", {})
		dist_days = clusters.get("dist_days_25d", 0)
		if dist_days == 0:
			# Fallback: try alternate key
			dist_days = spy_vol.get("distribution_clusters", {}).get("clusters_found", 0)

	# Market breadth
	new_highs = 0
	new_lows = 0
	if not breadth_result.get("error"):
		total = breadth_result.get("total", {})
		new_highs = total.get("new_highs", 0)
		new_lows = total.get("new_lows", 0)

	# Verdict logic
	highs_lows_ratio = round(new_highs / max(new_lows, 1), 2)
	leader_breaking = False

	# Check if leaders are breaking down from sector data
	if not leaders_result.get("error"):
		sectors = leaders_result.get("sectors", leaders_result.get("sector_dashboard", {}))
		if isinstance(sectors, dict):
			# Count sectors with deteriorating leaders
			deteriorating = 0
			total_sectors = 0
			for sector_name, sector_data in sectors.items():
				if isinstance(sector_data, dict):
					total_sectors += 1
					leaders_list = sector_data.get("leaders", [])
					if isinstance(leaders_list, list) and len(leaders_list) == 0:
						deteriorating += 1
			if total_sectors > 0 and deteriorating > total_sectors * 0.5:
				leader_breaking = True

	if new_highs > new_lows * 2 and dist_days < 4:
		verdict = "bull_early"
	elif new_highs > new_lows and dist_days >= 4:
		verdict = "bull_late"
	elif new_lows > new_highs * 2 and dist_days >= 6:
		verdict = "bear"
	elif new_lows > new_highs:
		verdict = "correction"
	else:
		verdict = "bull_early" if dist_days < 4 else "bull_late"

	# B.3: verdict_evidence
	verdict_evidence = {
		"new_highs_vs_lows": highs_lows_ratio,
		"distribution_days_25d": dist_days,
		"leader_stocks_breaking": leader_breaking,
	}

	# E.5: Strip ALL null fields from sector dashboard (recursive)
	sector_output = leaders_result if not leaders_result.get("error") else {"error": leaders_result.get("error")}
	if isinstance(sector_output, dict) and not sector_output.get("error"):
		sector_output = _strip_null_fields(sector_output)

	elapsed = round(time.time() - start, 1)

	output_json({
		"market_verdict": verdict,
		"verdict_evidence": verdict_evidence,
		"breadth": {
			"new_highs": new_highs,
			"new_lows": new_lows,
			"highs_lows_ratio": highs_lows_ratio,
			"breadth_detail": breadth_result if not breadth_result.get("error") else None,
		},
		"distribution_days_25d": dist_days,
		"sector_leaders": sector_output,
		"thresholds": {
			"verdict_rules": (
				"bull_early: highs > lows*2 AND dist_days < 4 | "
				"bull_late: highs > lows AND dist_days >= 4 | "
				"correction: lows > highs | "
				"bear: lows > highs*2 AND dist_days >= 6"
			),
		},
		"metadata": {
			"execution_time_seconds": elapsed,
		},
	})


# ---------------------------------------------------------------------------
# cmd_compare
# ---------------------------------------------------------------------------

@safe_run
def cmd_compare(args):
	"""Compare multiple tickers side-by-side on SEPA criteria.

	Runs cmd_analyze for each ticker in parallel, extracts SEPA scores
	and key metrics, and returns a comparison table sorted by SEPA score.
	"""
	tickers = [t.upper() for t in args.tickers]
	start = time.time()

	def _analyze_single(ticker):
		scripts = _analyze_scripts(ticker)
		with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
			futures = {
				name: executor.submit(_run_script, path, a)
				for name, (path, a) in scripts.items()
			}
			results = {name: future.result() for name, future in futures.items()}

		# Position sizing placeholder
		results["position_sizing"] = {"error": "skipped_for_compare"}

		risk_data = compute_risk_assessment(results)
		sepa_data = compute_sepa_score(results, risk_data)

		info = results.get("info", {})
		tt = results.get("trend_template", {})
		stage = results.get("stage_analysis", {})
		rs = results.get("rs_ranking", {})
		vcp = results.get("vcp", {})
		base = results.get("base_count", {})
		code33 = results.get("earnings_acceleration", {})
		char = results.get("stock_character", {})

		return {
			"ticker": ticker,
			"sepa_score": sepa_data.get("sepa_score", 0),
			"classification": sepa_data.get("classification"),
			"hard_gate_fail": sepa_data.get("hard_gate_fail"),
			"current_stage": stage.get("current_stage") if not stage.get("error") else None,
			"tt_pass": tt.get("overall_pass") if not tt.get("error") else None,
			"tt_score_pct": tt.get("score_pct") if not tt.get("error") else None,
			"rs_score": rs.get("rs_score") if not rs.get("error") else None,
			"base_number": base.get("current_base_number") if not base.get("error") else None,
			"vcp_detected": vcp.get("vcp_detected") if not vcp.get("error") else None,
			"pattern_quality": vcp.get("pattern_quality") if not vcp.get("error") else None,
			"eps_accelerating": code33.get("eps_accelerating") if not code33.get("error") else None,
			"sales_accelerating": code33.get("sales_accelerating") if not code33.get("error") else None,
			"character_grade": char.get("character_grade") if not char.get("error") else None,
			"risk_reward_ratio": risk_data.get("risk_reward_ratio"),
			"sector": info.get("sector") if not info.get("error") else None,
			"industry": info.get("industry") if not info.get("error") else None,
		}

	# Run analysis for all tickers in parallel
	with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tickers), 5)) as executor:
		compare_futures = {t: executor.submit(_analyze_single, t) for t in tickers}
		comparisons = [compare_futures[t].result() for t in tickers]

	# Sort by SEPA score descending
	comparisons.sort(key=lambda x: x.get("sepa_score", 0), reverse=True)

	elapsed = round(time.time() - start, 1)

	output_json({
		"comparison": comparisons,
		"ranked_by": "sepa_score",
		"thresholds": "prime: >=80 | actionable: 60-79 | developing: 40-59 | not_ready: 20-39 | avoid: <20 or hard_gate_fail",
		"metadata": {
			"tickers_compared": len(tickers),
			"execution_time_seconds": elapsed,
		},
	})


# ---------------------------------------------------------------------------
# cmd_recheck
# ---------------------------------------------------------------------------

@safe_run
def cmd_recheck(args):
	"""Recheck an existing position for hold/sell decision.

	Runs post_breakout.monitor with entry params, sell_signals detection,
	and current SEPA status. Returns verdict: HOLD / REDUCE / SELL.
	"""
	ticker = args.ticker.upper()
	entry_price = args.entry_price
	entry_date = args.entry_date
	stop_loss = getattr(args, "stop_loss", 7.0)
	start = time.time()

	# Build recheck scripts
	scripts = {
		"post_breakout": ("technical/post_breakout.py", [
			"monitor", ticker,
			"--entry-price", str(entry_price),
			"--entry-date", entry_date,
			"--stop-loss", str(stop_loss),
		]),
		"sell_signals": ("technical/sell_signals.py", ["check", ticker]),
		"stage_analysis": ("technical/stage_analysis.py", ["classify", ticker]),
		"trend_template": ("screening/trend_template.py", ["check", ticker]),
		"rs_ranking": ("technical/rs_ranking.py", ["score", ticker]),
		"volume_analysis": ("technical/volume_analysis.py", ["analyze", ticker]),
	}

	with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
		futures = {
			name: executor.submit(_run_script, path, a)
			for name, (path, a) in scripts.items()
		}
		results = {name: future.result() for name, future in futures.items()}

	missing = [k for k, v in results.items() if isinstance(v, dict) and v.get("error")]

	# Post breakout verdict
	post = results.get("post_breakout", {})
	sell = results.get("sell_signals", {})
	stage = results.get("stage_analysis", {})
	tt = results.get("trend_template", {})
	rs = results.get("rs_ranking", {})

	# E.6: Fix rs_ranking 12m null
	if "rs_ranking" in results:
		results["rs_ranking"] = _fix_rs_12m_null(results["rs_ranking"])
		rs = results["rs_ranking"]

	# Determine verdict
	reasons = []

	post_signal = post.get("hold_sell_signal", "hold") if not post.get("error") else "hold"
	sell_severity = sell.get("severity", "healthy") if not sell.get("error") else "healthy"
	current_stage = stage.get("current_stage") if not stage.get("error") else None
	tt_pass = tt.get("overall_pass") if not tt.get("error") else None

	# SELL conditions
	if post_signal == "sell":
		verdict = "SELL"
		reasons.append("post_breakout sell signal")
	elif sell_severity == "critical":
		verdict = "SELL"
		reasons.append("critical sell signals active")
	elif current_stage and current_stage >= 4:
		verdict = "SELL"
		reasons.append(f"stage {current_stage} decline detected")
	# REDUCE conditions
	elif post_signal == "reduce":
		verdict = "REDUCE"
		reasons.append("post_breakout reduce signal")
	elif sell_severity == "warning":
		verdict = "REDUCE"
		reasons.append("warning-level sell signals")
	elif tt_pass is False:
		verdict = "REDUCE"
		reasons.append("trend template no longer passing")
	# HOLD
	else:
		verdict = "HOLD"
		if post_signal == "watch":
			reasons.append("post_breakout watch — monitor closely")
		elif sell_severity == "caution":
			reasons.append("minor caution signals — hold with awareness")
		else:
			reasons.append("position healthy — continue holding")

	# C.3: Filter inactive sell signals for current_status
	active_signals = []
	if not sell.get("error"):
		raw_signals = sell.get("signals", {})
		for sig_name, sig_data in raw_signals.items():
			if isinstance(sig_data, dict) and sig_data.get("active"):
				active_signals.append(sig_name)

	# C.6: Compress volume for recheck
	vol_result = results.get("volume_analysis", {})
	compressed_vol = None
	if not vol_result.get("error"):
		clusters = vol_result.get("distribution_clusters", {})
		compressed_vol = {
			"grade": vol_result.get("accumulation_distribution_rating"),
			"weighted_ratio_50d": vol_result.get("up_down_volume_ratio_50d"),
			"cluster_warning": clusters.get("cluster_warning") if isinstance(clusters, dict) else None,
			"breakout_volume_confirmation": vol_result.get("breakout_volume_confirmation"),
		}

	elapsed = round(time.time() - start, 1)

	output_json({
		"ticker": ticker,
		"verdict": verdict,
		"reasons": reasons,
		"position": {
			"entry_price": entry_price,
			"entry_date": entry_date,
			"current_price": post.get("current_price") if not post.get("error") else None,
			"gain_loss_pct": post.get("gain_loss_pct") if not post.get("error") else None,
			"days_since_entry": post.get("days_since_entry") if not post.get("error") else None,
		},
		"post_breakout": {
			"behavior": post.get("behavior") if not post.get("error") else None,
			"signal": post_signal,
			"squat_detected": post.get("squat_detected") if not post.get("error") else None,
			"above_20ma": post.get("above_20ma") if not post.get("error") else None,
			"failure_reset": post.get("failure_reset") if not post.get("error") else None,
		},
		"current_status": {
			"stage": current_stage,
			"tt_pass": tt_pass,
			"tt_score_pct": tt.get("score_pct") if not tt.get("error") else None,
			"rs_score": rs.get("rs_score") if not rs.get("error") else None,
			"sell_signals": active_signals,
			"sell_severity": sell_severity,
		},
		"volume_analysis": compressed_vol,
		"metadata": {
			"missing_components": missing if missing else [],
			"execution_time_seconds": elapsed,
		},
	})
