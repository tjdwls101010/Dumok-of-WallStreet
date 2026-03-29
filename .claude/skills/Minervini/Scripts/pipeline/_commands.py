"""Minervini SEPA pipeline command implementations.

Two subcommands:
- analyze: Full SEPA analysis for a single ticker
- discover: Market environment + RS leader discovery

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


# ---------------------------------------------------------------------------
# Module script definitions
# ---------------------------------------------------------------------------

def _analyze_scripts(ticker):
	"""Return the dict of all module scripts for cmd_analyze."""
	return {
		# Trend qualification
		"trend_template": ("modules/trend_template.py", ["check", ticker]),
		"stage_analysis": ("modules/stage_analysis.py", ["classify", ticker]),
		"rs_ranking": ("modules/rs_ranking.py", ["score", ticker]),
		"base_count": ("modules/base_count.py", ["count", ticker]),
		# Technical setup
		"vcp": ("modules/vcp.py", ["detect", ticker]),
		"entry_patterns": ("modules/entry_patterns.py", ["scan", ticker]),
		"pocket_pivot": ("modules/pocket_pivot.py", ["detect", ticker]),
		"tight_closes": ("modules/tight_closes.py", ["daily", ticker]),
		"volume_analysis": ("modules/volume_analysis.py", ["analyze", ticker]),
		# Fundamentals
		"earnings_acceleration": ("modules/earnings_acceleration.py", ["code33", ticker]),
		"earnings_surprise": ("modules/earnings_acceleration.py", ["surprise", ticker]),
		"estimate_revisions": ("modules/earnings_acceleration.py", ["revisions", ticker]),
		"forward_pe": ("modules/forward_pe.py", ["calculate", ticker]),
		"margin_tracker": ("modules/margin_tracker.py", ["track", ticker]),
		"info": ("modules/info.py", [
			"get-info-fields", ticker,
			"sector", "industry", "marketCap", "currentPrice", "beta",
			"fiftyTwoWeekLow", "fiftyTwoWeekHigh",
			"fiftyDayAverage", "twoHundredDayAverage",
			"sharesOutstanding", "floatShares", "shortPercentOfFloat",
		]),
		# Risk
		"sell_signals": ("modules/sell_signals.py", ["check", ticker]),
		"stock_character": ("modules/stock_character.py", ["assess", ticker]),
	}



def _build_earnings_unified(ea, surprise_data, revisions_data):
	"""Build unified earnings structure from 3 module results.

	Combines earnings_acceleration, earnings_surprise, and estimate_revisions
	into a single earnings dict with eps_history, sales_history, acceleration,
	forward_growth, and revision_breadth.
	"""
	unified = {}

	# eps_history from surprise_history (max 8 quarters)
	if not surprise_data.get("error"):
		history = surprise_data.get("surprise_history", [])
		eps_hist = []
		sales_hist = []
		for h in history[:8]:
			eps_entry = {
				"quarter": h.get("date", ""),
				"eps": h.get("actual"),
				"qoq_growth": h.get("eps_qoq_pct"),
				"yoy_growth": h.get("eps_yoy_pct"),
				"surprise_pct": h.get("surprise_pct"),
			}
			eps_hist.append(eps_entry)
			if h.get("revenue") is not None:
				sales_hist.append({
					"quarter": h.get("date", ""),
					"revenue": h.get("revenue"),
					"qoq_growth": h.get("revenue_qoq_pct"),
					"yoy_growth": h.get("revenue_yoy_pct"),
				})
		unified["eps_history"] = eps_hist
		if sales_hist:
			unified["sales_history"] = sales_hist

		# Beat tracking
		unified["consecutive_beats"] = surprise_data.get("consecutive_beats", 0)
		# Meaningful beats (surprise >= 5%)
		meaningful_count = 0
		for h in history:
			if h.get("surprise_pct") is not None and h["surprise_pct"] >= 5.0:
				meaningful_count += 1
			else:
				break
		unified["consecutive_meaningful_beats"] = meaningful_count
		unified["cockroach_effect"] = surprise_data.get("cockroach_effect")

	# acceleration from earnings_acceleration
	if not ea.get("error"):
		unified["acceleration"] = {
			"eps_accelerating": ea.get("eps_accelerating", False),
			"eps_growth_sufficient": ea.get("eps_growth_sufficient", False),
			"eps_decelerating": ea.get("eps_decelerating", False),
			"sales_accelerating": ea.get("sales_accelerating", False),
			"sales_decelerating": ea.get("sales_decelerating", False),
			"margin_expanding": ea.get("margin_expanding", False),
			"code33_status": ea.get("code33_status", "FAIL"),
			"thresholds": {
				"accelerating": "3 consecutive quarters with increasing YoY growth rate",
				"growth_sufficient": "most recent quarter YoY >= 20% (preferred 30%+)",
				"decelerating": "3 quarters with decreasing growth rate = warning",
				"code33": "EPS + Sales + Margins all accelerating for 3 quarters",
			},
		}

	# forward_growth + revision_breadth from estimate_revisions
	if not revisions_data.get("error"):
		# Forward growth from growth_estimates.stockTrend
		growth_est = revisions_data.get("growth_estimates", {})
		stock_trend = growth_est.get("stockTrend", {}) if isinstance(growth_est, dict) else {}
		if stock_trend:
			fg = {}
			if stock_trend.get("0q") is not None:
				fg["current_quarter_yoy"] = round(stock_trend["0q"] * 100, 1)
			if stock_trend.get("+1q") is not None:
				fg["next_quarter_yoy"] = round(stock_trend["+1q"] * 100, 1)
			if stock_trend.get("0y") is not None:
				fg["current_year_yoy"] = round(stock_trend["0y"] * 100, 1)
			if stock_trend.get("+1y") is not None:
				fg["next_year_yoy"] = round(stock_trend["+1y"] * 100, 1)
			if fg:
				fg["unit"] = "% expected YoY EPS growth"
				fg["thresholds"] = {
					"strong": "current quarter >= 25% AND accelerating",
					"decelerating_warning": "next quarter < current quarter",
				}
				unified["forward_growth"] = fg

		# Revision breadth (from raw eps_revisions)
		raw_revisions = revisions_data.get("eps_revisions", {})
		if isinstance(raw_revisions, dict):
			up_30d = raw_revisions.get("upLast30days", {})
			down_30d = raw_revisions.get("downLast30days", {})
			if isinstance(up_30d, dict) and isinstance(down_30d, dict):
				unified["revision_breadth"] = {
					"current_quarter": {
						"up": up_30d.get("0q", 0),
						"down": down_30d.get("0q", 0),
					},
					"current_year": {
						"up": up_30d.get("0y", 0),
						"down": down_30d.get("0y", 0),
					},
					"unit": "analysts revising up vs down (last 30 days)",
					"thresholds": {
						"bullish": "up >> down",
						"bearish": "down >> up",
					},
				}

	# Thresholds for beats
	unified["thresholds"] = {
		"meaningful_beat": "surprise_pct >= 5%",
		"cockroach_strong": "3+ consecutive meaningful beats",
	}

	return unified if unified else None


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

	# A.4: Use rs_ranking score as canonical — remove rs_score from trend_template
	rs_result = results.get("rs_ranking", {})
	tt_result = results.get("trend_template", {})
	if not tt_result.get("error") and isinstance(tt_result, dict):
		tt_result = dict(tt_result)
		tt_result.pop("rs_score", None)
		results["trend_template"] = tt_result

	# I3.8: Extract next earnings date from calendar
	calendar_result = _run_script("modules/actions.py", ["get-calendar", ticker])
	next_earnings_date = None
	if not calendar_result.get("error"):
		ed = calendar_result.get("Earnings Date")
		if isinstance(ed, list) and ed:
			next_earnings_date = ed[0]
		elif isinstance(ed, str) and ed != "N/A":
			next_earnings_date = ed

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
		pos_result = _run_script("modules/position_sizing.py", [
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

	# SEPA scoring — returns tuple now
	sepa_total, classification, hard_gate_fail, hard_gates, dim_scores = compute_sepa_score(results, risk_data)

	# Signal synthesis — uses new tuple args
	signal = determine_overall_signal(results, sepa_total, classification, hard_gate_fail, hard_gates, risk_data)

	# Save raw estimate_revisions before compression (needed by _build_earnings_unified)
	_raw_revisions = results.get("estimate_revisions", {})

	# Post-processing (compress before output)
	# A.1: Strip symbol/date/current_price from all module outputs
	_STRIP_FIELDS = {"symbol", "date", "current_price", "interval", "benchmark"}
	for key in list(results.keys()):
		r = results[key]
		if isinstance(r, dict) and not r.get("error"):
			results[key] = {k: v for k, v in r.items() if k not in _STRIP_FIELDS}

	# Use compressed/active_only views from each module
	for key in list(results.keys()):
		r = results[key]
		if not isinstance(r, dict) or r.get("error"):
			continue
		if key == "sell_signals" and "active_only" in r:
			results[key] = r["active_only"]
		elif "compressed" in r:
			results[key] = r["compressed"]

	# I4.10: Remove base_stage_assessment from base_count
	bc = results.get("base_count")
	if isinstance(bc, dict):
		bc.pop("base_stage_assessment", None)

	# --- Build SEPA dimension-centric output ---

	# Override TT's RS score with rs_ranking canonical
	rs_data = results.get("rs_ranking", {})
	tt_data = results.get("trend_template")
	if isinstance(tt_data, dict) and isinstance(rs_data, dict) and not rs_data.get("error"):
		canonical_rs = rs_data.get("rs_rating")
		if canonical_rs is not None and "criteria" in tt_data:
			for c in tt_data["criteria"]:
				if c.get("id") == 8:
					c["value"] = f"RS Rating = {canonical_rs}"
					c["passed"] = canonical_rs >= 70

	rs_detail = rs_data if isinstance(rs_data, dict) and not rs_data.get("error") else None

	ea = results.get("earnings_acceleration", {})

	# Build unified earnings structure from 3 modules
	# Use raw revisions data (saved before compression) for forward_growth/revision_breadth
	surprise_data = results.get("earnings_surprise", {})
	earnings_unified = _build_earnings_unified(ea, surprise_data, _raw_revisions)

	elapsed = round(time.time() - start, 1)

	# Merge sepa_verdict into signal
	signal["sepa_score"] = sepa_total
	signal["classification"] = classification
	signal["hard_gate_fail"] = hard_gate_fail
	signal["hard_gates"] = hard_gates

	output = {
		"ticker": ticker,
		"signal": signal,
		"trend": {
			"dimension_score": dim_scores["trend"],
			"trend_template": tt_data,
			"stage_analysis": results.get("stage_analysis"),
			"rs_detail": rs_detail,
			"base_count": results.get("base_count"),
		},
		"fundamentals": {
			"dimension_score": dim_scores["fundamentals"],
			"earnings": earnings_unified,
			"valuation": results.get("forward_pe"),
			"margins": results.get("margin_tracker"),
		},
		"setup": {
			"dimension_score": dim_scores["setup"],
			"vcp": results.get("vcp"),
			"entry_patterns": results.get("entry_patterns"),
			"institutional_demand": results.get("pocket_pivot"),
			"tight_closes": results.get("tight_closes"),
			"volume_analysis": results.get("volume_analysis"),
		},
		"risk": {
			"dimension_score": dim_scores["risk"],
			"sell_signals": results.get("sell_signals"),
			"stock_character": results.get("stock_character"),
			"risk_gate": risk_data,
		},
		"company": results.get("info"),
		"metadata": {
			"next_earnings_date": next_earnings_date,
			"missing_components": missing if missing else [],
			"modules_run": len(scripts) + 1,
			"execution_time_seconds": elapsed,
		},
	}

	output_json(output)



# ---------------------------------------------------------------------------
# cmd_market_leaders
# ---------------------------------------------------------------------------

@safe_run
def cmd_discover(args):
	"""Market environment + RS leader discovery.

	Assesses market health (breadth, distribution days) and identifies
	RS leaders (sector/industry rankings, top stocks, movers) for
	candidate discovery using the ibd-rs-rating library.
	"""
	start = time.time()

	from rs_rating import RS
	_rs = RS()

	# Single executor: RS calls complete in ~1s, finviz market-breadth ~20-30s.
	# Submit industry_top as soon as industry_ranking completes (overlaps with
	# market-breadth wait, so adds zero wall-clock time).
	with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
		f_breadth = executor.submit(_run_script, "modules/market_breadth.py", ["breadth"])
		f_spy = executor.submit(_run_script, "modules/volume_analysis.py", ["analyze", "SPY"])
		f_rs_ref = executor.submit(lambda: _rs.reference())
		f_rs_top = executor.submit(lambda: _rs.top(20))
		f_sector_rank = executor.submit(lambda: _rs.sector_ranking())
		f_industry_rank = executor.submit(lambda: _rs.industry_ranking())
		f_movers = executor.submit(lambda: _rs.movers(days=5, n=20, direction="up"))

		# Wait for industry_ranking first (~0.8s) then submit industry_top
		# while market-breadth is still running (~20-30s remaining)
		try:
			industry_rank = f_industry_rank.result() or []
		except Exception:
			industry_rank = []

		industry_futures = {}
		for ind in industry_rank[:15]:
			ind_name = ind.get("industry", "")
			if ind_name:
				f = executor.submit(lambda name=ind_name: _rs.industry_top(name, n=5))
				industry_futures[f] = ind

		# Collect remaining Phase 1 results (market-breadth is the bottleneck)
		breadth_result = f_breadth.result()
		spy_vol = f_spy.result()

		# RS data (graceful on failure)
		try:
			rs_ref = f_rs_ref.result()
		except Exception:
			rs_ref = []
		try:
			rs_top = f_rs_top.result()
		except Exception:
			rs_top = []
		try:
			sector_rank = f_sector_rank.result() or []
		except Exception:
			sector_rank = []
		try:
			movers_result = f_movers.result() or []
		except Exception:
			movers_result = []

		# Collect industry_top results (already completed during breadth wait)
		for f in concurrent.futures.as_completed(industry_futures):
			ind = industry_futures[f]
			try:
				tickers = f.result() or []
				ind["leader_tickers"] = [t["ticker"] for t in tickers]
				ind["leader_count"] = len(ind["leader_tickers"])
			except Exception:
				ind["leader_tickers"] = []
				ind["leader_count"] = 0

	# Assign leadership ranks
	for i, ind in enumerate(industry_rank):
		ind["leadership_rank"] = i + 1

	# Distribution day count from SPY volume analysis
	dist_days = 0
	if not spy_vol.get("error"):
		clusters = spy_vol.get("distribution_clusters", {})
		dist_days = clusters.get("dist_days_25d", 0)
		if dist_days == 0:
			dist_days = spy_vol.get("distribution_clusters", {}).get("clusters_found", 0)

	# Market breadth
	new_highs = 0
	new_lows = 0
	if not breadth_result.get("error"):
		hl = breadth_result.get("new_high_low", {})
		new_highs = hl.get("new_high", {}).get("count", 0)
		new_lows = hl.get("new_low", {}).get("count", 0)

	# Verdict logic
	highs_lows_ratio = round(new_highs / max(new_lows, 1), 2)

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

	verdict_evidence = {
		"new_highs_vs_lows": highs_lows_ratio,
		"distribution_days_25d": dist_days,
	}

	# Build RS leaders section
	spy_rs = None
	qqq_rs = None
	for ref in (rs_ref or []):
		if ref.get("ticker") == "SPY":
			spy_rs = ref.get("rs_rating")
		elif ref.get("ticker") == "QQQ":
			qqq_rs = ref.get("rs_rating")

	rs_leaders = {
		"spy_rs": spy_rs,
		"qqq_rs": qqq_rs,
		"top_20": rs_top[:20] if rs_top else [],
		"movers_5d": movers_result[:20],
	}

	# Add rank to sector_ranking
	for i, s in enumerate(sector_rank):
		s["rank"] = i + 1

	elapsed = round(time.time() - start, 1)

	output_json({
		"market_verdict": verdict,
		"verdict_evidence": verdict_evidence,
		"breadth": {
			"new_highs": new_highs,
			"new_lows": new_lows,
			"detail": breadth_result if not breadth_result.get("error") else None,
		},
		"rs_leaders": rs_leaders,
		"sector_ranking": sector_rank,
		"leadership_dashboard": industry_rank,
		"thresholds": {
			"verdict_rules": {
				"bull_early": "highs > lows*2 AND dist_days < 4",
				"bull_late": "highs > lows AND dist_days >= 4",
				"correction": "lows > highs",
				"bear": "lows > highs*2 AND dist_days >= 6",
			},
		},
		"metadata": {
			"execution_time_seconds": elapsed,
		},
	})

