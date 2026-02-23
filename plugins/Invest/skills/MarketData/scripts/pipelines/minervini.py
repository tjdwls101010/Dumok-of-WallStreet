#!/usr/bin/env python3
"""SEPA Pipeline: full Minervini SEPA analysis integrating all individual scripts.

Orchestrates the complete Specific Entry Point Analysis by running Trend Template,
Stage Analysis, RS Ranking, Earnings Acceleration, VCP Detection, Base Counting,
Volume Analysis, and Position Sizing in sequence. Produces a composite score
and actionable signal.

Commands:
	analyze: Full SEPA analysis for a single ticker
	watchlist: Batch SEPA analysis for multiple tickers

Args:
	For analyze:
		symbol (str): Ticker symbol (e.g., "AAPL", "NVDA")
		--account-size (float): Account size for position sizing (default: 100000)

	For watchlist:
		symbols (list): List of ticker symbols
		--account-size (float): Account size for position sizing (default: 100000)

Returns:
	dict: {
		"symbol": str,
		"sepa_composite_score": float,
		"signal": str,
		"signal_reason_codes": [str],
		"hard_gate_result": {
			"blocked": bool,
			"blockers": [str],
			"soft_penalties": [{"code": str, "penalty": int}],
			"total_soft_penalty": int
		},
		"analysis_mode": "full" | "provisional",
		"trend_template": dict,
		"stage_analysis": dict,
		"rs_ranking": dict,
		"earnings": dict,
		"vcp": dict,
		"base_count": dict,
		"volume": dict,
		"position_sizing": dict,
		"earnings_proximity": {
			"is_near": bool,
			"days_until": int or None,
			"next_date": str or None
		},
		"category_hint": str,
		"recommendation_text": str,
		"risk_assessment": dict
	}

Example:
	>>> python sepa_pipeline.py analyze NVDA --account-size 100000
	{
		"symbol": "NVDA",
		"sepa_composite_score": 85.0,
		"signal": "BUY",
		"trend_template": {"overall_pass": true, "score_pct": 100.0},
		"stage_analysis": {"current_stage": 2, "stage_confidence": 82.0},
		"rs_ranking": {"rs_score": 92},
		"earnings": {"code33_status": "PASS"},
		"recommendation_text": "Strong SEPA candidate..."
	}

Use Cases:
	- Complete stock evaluation using Minervini's SEPA methodology
	- Batch screening of watchlist for actionable setups
	- Pre-trade checklist automation
	- Systematic comparison of multiple candidates

Notes:
	- Weights: TT 25, Stage 15, RS 15, Earnings 15, VCP 10, Base 10, Vol 10
	- Alt entry bonus: PP +1, tight closes +1, low cheat +1 (max +3)
	- Vol scoring: grade 0-5, cluster -2, pullback +2, ratio +/-2, climactic +1
	- Signals: STRONG_BUY 80+, BUY 65-79, HOLD 50-64, WATCH 35-49, AVOID <35
	- Hard gates block BUY/STRONG_BUY: TT<6/8, Stage 3/4, distribution+weak volume
	- Soft gates apply score penalties: VCP undetected -5, no breakout vol -5, excessive correction -5
	- Watchlist mode outputs provisional signals (STRONG_BUY capped to BUY, missing_components listed)
	- Pipeline continues even if individual components fail (graceful degradation)
	- New scripts (pocket_pivot, tight_closes, low_cheat) skipped in watchlist batch mode
	- Agent can override pipeline signal based on market context
	- Scripts execute in parallel via ThreadPoolExecutor for ~50-70% speedup
	- Each script runs in independent subprocess (no shared state)
	- Watchlist mode remains sequential per-ticker (batch parallelization would overload)
	- SG-4: 200MA extension graduated levels: >80% ELEVATED (informational), >100% EXTREME (penalty -3)
	- EARNINGS_PROXIMITY signal code: appended when next earnings within 5 trading days
	- category_hint: earnings-pattern-based company category inference aid (hint only, not definitive)

See Also:
	- trend_template.py: Trend Template 8-criteria check
	- stage_analysis.py: Stage 1-4 classification
	- rs_ranking.py: Relative strength scoring
	- earnings_acceleration.py: Code 33 and earnings analysis
	- vcp.py: Volatility Contraction Pattern detection (includes Cup & Handle, Power Play, setup readiness)
	- base_count.py: Base counting within Stage 2
	- volume_analysis.py: Accumulation/distribution rating
	- position_sizing.py: Risk-based position sizing
	- pocket_pivot.py: Pocket pivot detection for alternative entry signals
	- tight_closes.py: Tight close cluster detection for supply dryup confirmation
	- low_cheat.py: Low cheat setup detection for reduced-risk entry
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


def _calc_composite_score(tt, stage, rs, earnings, vcp, base, volume):
	"""Calculate weighted composite SEPA score (0-100).

	Weights:
	- Trend Template: 25 (most important - must pass for SEPA)
	- Stage Analysis: 15 (must be Stage 2)
	- RS Ranking: 15 (relative strength)
	- Earnings: 15 (fundamental driver)
	- VCP: 10 (entry timing)
	- Base Count: 10 (base stage risk)
	- Volume: 10 (institutional confirmation)
	"""
	score = 0

	# Trend Template (25 points)
	if not tt.get("error"):
		tt_pct = tt.get("score_pct", 0)
		score += tt_pct / 100 * 25

	# Stage Analysis (15 points)
	if not stage.get("error"):
		current_stage = stage.get("current_stage", 0)
		if current_stage == 2:
			confidence = stage.get("stage_confidence", 50)
			score += confidence / 100 * 15
		elif current_stage == 1:
			score += 5  # Partial credit for Stage 1 (potential)

	# RS Ranking (15 points)
	if not rs.get("error"):
		rs_score = rs.get("rs_score", 0) or 0
		score += min(rs_score / 99 * 15, 15)

	# Earnings (15 points)
	if not earnings.get("error"):
		eps_acc = earnings.get("eps_accelerating", False)
		sales_acc = earnings.get("sales_accelerating", False)
		margin_exp = earnings.get("margin_expanding", False)
		code33 = earnings.get("code33_status") == "PASS"

		if code33:
			score += 15
		else:
			if eps_acc:
				score += 6
			if sales_acc:
				score += 5
			if margin_exp:
				score += 4

	# VCP (10 points)
	if not vcp.get("error"):
		if vcp.get("vcp_detected"):
			quality = vcp.get("pattern_quality", "none")
			if quality == "high":
				score += 10
			elif quality == "moderate":
				score += 7
			elif quality == "low":
				score += 4
		else:
			score += 2  # Base credit for analysis available

	# Base Count (10 points)
	if not base.get("error"):
		base_num = base.get("current_base_number", 0)
		if base_num == 1:
			score += 10
		elif base_num == 2:
			score += 8
		elif base_num == 3:
			score += 5
		elif base_num >= 4:
			score += 2

	# Volume (10 points) - multi-factor scoring
	if not volume.get("error"):
		grade = volume.get("accumulation_distribution_rating", "C")
		# Base score from grade (max 5)
		base_scores = {"A+": 5, "A": 4, "B+": 3, "B": 2, "C": 1, "D": 0, "E": 0}
		vol_score = base_scores.get(grade, 1)

		# Distribution cluster penalty (-2)
		clusters = volume.get("distribution_clusters", {})
		if clusters.get("cluster_warning"):
			vol_score -= 2

		# Pullback quality bonus (+2)
		if volume.get("pullback_volume_declining") is True:
			vol_score += 2

		# 20d/50d ratio divergence (+2 or -2)
		ratio_20d = volume.get("up_down_volume_ratio_20d", 1.0)
		if ratio_20d > 1.3:
			vol_score += 2
		elif ratio_20d < 0.5:
			vol_score -= 2

		# Net climactic signal (+1)
		climactic = volume.get("climactic_volume", {})
		if climactic.get("net_climactic", 0) > 0:
			vol_score += 1

		score += max(0, min(10, vol_score))

	return round(score, 1)


def _evaluate_hard_gates(tt, stage, volume, vcp, base):
	"""Evaluate hard-gate and soft-gate conditions for signal safety.

	Hard gates: if ANY is true, BUY/STRONG_BUY is blocked regardless of score.
	Soft gates: apply additional score penalties (-5 to -10).

	Returns dict with blocked status, blocker reasons, and soft penalties.
	"""
	blockers = []
	soft_penalties = []

	# --- Hard Gates ---

	# HG-1: Trend Template insufficient (less than 6 of 8 criteria)
	if not tt.get("error"):
		passed = tt.get("passed_count", 0)
		if passed < 6:
			blockers.append(f"TT_INSUFFICIENT_{passed}_8")

	# HG-2: Stage 3 or 4 (already in _determine_signal, but explicit here)
	current_stage = stage.get("current_stage", 0) if not stage.get("error") else 0
	if current_stage in (3, 4):
		blockers.append(f"STAGE_{current_stage}_DISQUALIFIED")

	# HG-3: Distribution cluster + weak short-term volume
	if not volume.get("error"):
		clusters = volume.get("distribution_clusters", {})
		ratio_20d = volume.get("up_down_volume_ratio_20d", 1.0)
		if clusters.get("cluster_warning") and ratio_20d < 0.7:
			blockers.append("DISTRIBUTION_CLUSTER_WITH_WEAK_VOLUME")

	# --- Soft Gates (score penalties) ---

	# SG-1: VCP not detected (-5)
	if not vcp.get("error") and not vcp.get("vcp_detected"):
		soft_penalties.append({"code": "VCP_NOT_DETECTED", "penalty": -5})

	# SG-2: Breakout volume not confirmed (-5)
	if not volume.get("error") and not volume.get("breakout_volume_confirmation", False):
		soft_penalties.append({"code": "BREAKOUT_VOLUME_UNCONFIRMED", "penalty": -5})

	# SG-3: Excessive relative correction in latest base (-5)
	if not base.get("error"):
		base_history = base.get("base_history", [])
		if base_history:
			latest = base_history[-1]
			if latest.get("correction_severity") == "excessive":
				soft_penalties.append({"code": "EXCESSIVE_RELATIVE_CORRECTION", "penalty": -5})

	# SG-4: Extreme extension above 200MA (-3)
	if not tt.get("error"):
		current_price = tt.get("current_price", 0)
		sma200 = tt.get("moving_averages", {}).get("sma200", 0)
		if current_price > 0 and sma200 > 0:
			extension_pct = (current_price - sma200) / sma200 * 100
			if extension_pct > 100:
				soft_penalties.append(
					{"code": "EXTREME_200MA_EXTENSION", "penalty": -3, "detail": f"{extension_pct:.1f}% above 200MA"}
				)

	total_soft_penalty = sum(p["penalty"] for p in soft_penalties)
	blocked = len(blockers) > 0

	return {
		"blocked": blocked,
		"blockers": blockers,
		"soft_penalties": soft_penalties,
		"total_soft_penalty": total_soft_penalty,
	}


def _build_signal_reason_codes(signal, tt, stage, rs, earnings, vcp, volume, base, hard_gate_result):
	"""Build human-readable reason codes explaining the signal determination."""
	codes = []

	# Trend Template
	if not tt.get("error"):
		passed = tt.get("passed_count", 0)
		total = tt.get("total_count", 8)
		codes.append(f"TT_PASS_{passed}_{total}")

	# Stage
	if not stage.get("error"):
		s = stage.get("current_stage", 0)
		conf = stage.get("stage_confidence", 0)
		codes.append(f"STAGE_{s}_CONF_{int(conf)}")

	# RS
	if not rs.get("error"):
		rs_val = rs.get("rs_score", 0)
		if rs_val and rs_val >= 80:
			codes.append("RS_LEADER")
		elif rs_val and rs_val >= 70:
			codes.append("RS_STRONG")
		else:
			codes.append("RS_WEAK")

	# Earnings
	if not earnings.get("error"):
		if earnings.get("code33_status") == "PASS":
			codes.append("CODE33_PASS")
		else:
			codes.append("CODE33_FAIL")

	# VCP
	if not vcp.get("error"):
		if vcp.get("vcp_detected"):
			codes.append(f"VCP_DETECTED_{vcp.get('pattern_quality', 'unknown').upper()}")
		else:
			codes.append("VCP_NOT_DETECTED")

	# Volume
	if not volume.get("error"):
		clusters = volume.get("distribution_clusters", {})
		if clusters.get("cluster_warning"):
			codes.append("DISTRIBUTION_CLUSTER_WARNING")
		if volume.get("breakout_volume_confirmation"):
			codes.append("BREAKOUT_VOL_CONFIRMED")

	# Base
	if not base.get("error"):
		bn = base.get("current_base_number", 0)
		codes.append(f"BASE_{bn}")
		base_history = base.get("base_history", [])
		if base_history and base_history[-1].get("correction_severity") == "excessive":
			codes.append("CORRECTION_EXCESSIVE")

	# 200MA Extension (graduated levels)
	if not tt.get("error"):
		price = tt.get("current_price", 0)
		sma200 = tt.get("moving_averages", {}).get("sma200", 0)
		if price > 0 and sma200 > 0:
			ext = (price - sma200) / sma200 * 100
			if ext > 100:
				codes.append(f"EXTENDED_200MA_{int(ext)}PCT")
			elif ext > 80:
				codes.append(f"ELEVATED_200MA_{int(ext)}PCT")

	# Hard gate
	if hard_gate_result["blocked"]:
		for b in hard_gate_result["blockers"]:
			codes.append(f"HARD_GATE:{b}")

	return codes


def _determine_signal(composite_score, tt_pass, stage):
	"""Determine signal based on composite score and key criteria."""
	current_stage = stage.get("current_stage", 0) if not stage.get("error") else 0

	# Hard disqualifiers
	if current_stage == 4:
		return "AVOID"
	if current_stage == 3:
		return "WATCH" if composite_score >= 50 else "AVOID"

	if composite_score >= 80 and tt_pass:
		return "STRONG_BUY"
	elif composite_score >= 65 and tt_pass:
		return "BUY"
	elif composite_score >= 50:
		return "HOLD"
	elif composite_score >= 35:
		return "WATCH"
	else:
		return "AVOID"


def _generate_recommendation(symbol, signal, tt, stage, rs, earnings, vcp, base, volume, composite):
	"""Generate human-readable recommendation text."""
	parts = [f"{symbol}: SEPA Score {composite}/100 - Signal: {signal}"]

	# Trend Template
	if not tt.get("error"):
		passed = tt.get("passed_count", 0)
		total = tt.get("total_count", 8)
		parts.append(f"Trend Template: {passed}/{total} criteria passed")

	# Stage
	if not stage.get("error"):
		parts.append(f"Stage: {stage.get('current_stage')} ({stage.get('stage_name', 'Unknown')})")

	# RS
	if not rs.get("error"):
		parts.append(f"RS Score: {rs.get('rs_score', 'N/A')}")

	# Earnings
	if not earnings.get("error"):
		code33 = earnings.get("code33_status", "N/A")
		parts.append(f"Code 33: {code33}")

	# VCP
	if not vcp.get("error"):
		if vcp.get("vcp_detected"):
			vcp_info = f"VCP: Detected ({vcp.get('pattern_type', 'N/A')}, {vcp.get('technical_footprint', 'N/A')})"
			# Shakeout info
			shakeout = vcp.get("shakeout", {})
			if shakeout.get("has_constructive_shakeout"):
				vcp_info += f", shakeout: {shakeout.get('last_shakeout_location', 'N/A')}"
			# Pivot tightness
			tightness = vcp.get("pivot_tightness", {})
			if tightness.get("is_tight"):
				vcp_info += ", tight pivot"
			# Time compression warning
			time_sym = vcp.get("time_symmetry", {})
			if time_sym.get("time_compressed"):
				vcp_info += f", WARNING: {time_sym.get('right_side_quality', 'compressed')}"
			parts.append(vcp_info)
		else:
			parts.append("VCP: Not detected")

	# Base
	if not base.get("error"):
		parts.append(f"Base: #{base.get('current_base_number', 'N/A')} ({base.get('risk_level', 'N/A')} risk)")

	# Volume
	if not volume.get("error"):
		parts.append(
			f"Volume: {volume.get('accumulation_distribution_rating', 'N/A')} ({volume.get('volume_trend', 'N/A')})"
		)

	return " | ".join(parts)


def _check_earnings_proximity(earnings_dates_result):
	"""Check if next earnings date is within 5 trading days.

	Scans get-earnings-dates result for the first future date with no Reported EPS
	(i.e., upcoming earnings). Counts weekdays from today to that date.

	Returns:
		tuple: (is_near: bool, days_until: int or None, next_date: str or None)
	"""
	from datetime import datetime, timedelta

	if earnings_dates_result.get("error"):
		return False, None, None

	dates = earnings_dates_result.get("earnings_dates", [])
	if not dates:
		return False, None, None

	today = datetime.now().date()

	for entry in dates:
		# Future earnings: Reported EPS is null/None
		if entry.get("Reported EPS") is not None:
			continue
		date_str = entry.get("Earnings Date")
		if not date_str:
			continue
		try:
			earn_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
		except (ValueError, TypeError):
			continue

		if earn_date < today:
			continue

		# Count business days (weekdays only)
		days_until = 0
		current = today
		while current < earn_date:
			current += timedelta(days=1)
			if current.weekday() < 5:  # Mon-Fri
				days_until += 1

		if days_until <= 5:
			return True, days_until, str(earn_date)
		else:
			return False, days_until, str(earn_date)

	return False, None, None


def _infer_category_hint(earnings):
	"""Infer company category hint from earnings acceleration patterns.

	This is a hint only -- final classification requires agent-level inference
	(industry rank, prior cycle RS, P/E pattern, and other qualitative data
	that scripts cannot evaluate).

	Returns:
		str: Category hint - one of "turnaround_candidate",
			"growth_leader_candidate", "top_competitor_candidate",
			"institutional_favorite_candidate", "insufficient_data",
			or "unclassified".
	"""
	if earnings.get("error"):
		return "insufficient_data"

	data_quality = earnings.get("data_quality", "")
	if data_quality == "minimal":
		return "insufficient_data"

	code33 = earnings.get("code33_status") == "PASS"
	eps_history = earnings.get("eps_quarterly_growth", [])
	# Detect turnaround: recent 2+ quarters of strong improvement from negative base
	if len(eps_history) >= 2:
		recent = eps_history[-2:]
		has_negative_base = any(q.get("previous", 0) < 0 for q in recent if isinstance(q, dict))
		has_strong_growth = all(
			(q.get("growth_pct", 0) or 0) > 100
			for q in recent
			if isinstance(q, dict) and q.get("growth_pct") is not None
		)
		if has_negative_base and has_strong_growth:
			return "turnaround_candidate"

	# Count consecutive quarters of 20%+ EPS growth
	consecutive_20plus = 0
	if eps_history:
		for q in reversed(eps_history):
			if isinstance(q, dict) and (q.get("growth_pct", 0) or 0) >= 20:
				consecutive_20plus += 1
			else:
				break

	if consecutive_20plus >= 3 and code33:
		return "growth_leader_candidate"
	elif consecutive_20plus >= 3 and not code33:
		return "top_competitor_candidate"

	# Stable 10-20% growth for 3+ quarters
	consecutive_stable = 0
	if eps_history:
		for q in reversed(eps_history):
			g = q.get("growth_pct", 0) or 0 if isinstance(q, dict) else 0
			if 10 <= g < 20:
				consecutive_stable += 1
			else:
				break
	if consecutive_stable >= 3:
		return "institutional_favorite_candidate"

	return "unclassified"


@safe_run
def cmd_analyze(args):
	"""Full SEPA analysis for a single ticker."""
	symbol = args.symbol.upper()

	# Run all analysis scripts in parallel
	scripts = {
		"tt": ("screening/trend_template.py", ["check", symbol]),
		"stage": ("technical/stage_analysis.py", ["classify", symbol]),
		"rs": ("technical/rs_ranking.py", ["score", symbol]),
		"earnings": ("data_sources/earnings_acceleration.py", ["code33", symbol]),
		"vcp_result": ("technical/vcp.py", ["detect", symbol]),
		"base": ("technical/base_count.py", ["count", symbol]),
		"volume": ("technical/volume_analysis.py", ["analyze", symbol]),
		"pocket_pivot": ("technical/pocket_pivot.py", ["detect", symbol]),
		"tight_closes": ("technical/tight_closes.py", ["daily", symbol]),
		"low_cheat": ("technical/low_cheat.py", ["detect", symbol]),
		"earnings_dates": ("data_sources/actions.py", ["get-earnings-dates", symbol, "--limit", "4"]),
	}

	with concurrent.futures.ThreadPoolExecutor(max_workers=11) as executor:
		futures = {name: executor.submit(_run_script, path, args) for name, (path, args) in scripts.items()}
		results = {name: future.result() for name, future in futures.items()}

	tt = results["tt"]
	stage = results["stage"]
	rs = results["rs"]
	earnings = results["earnings"]
	vcp_result = results["vcp_result"]
	base = results["base"]
	volume = results["volume"]
	pocket_pivot = results["pocket_pivot"]
	tight_closes = results["tight_closes"]
	low_cheat = results["low_cheat"]

	# Calculate composite score
	composite = _calc_composite_score(tt, stage, rs, earnings, vcp_result, base, volume)

	# VCP bonus scoring from alternative entry patterns (+1 each, max +3)
	pattern_bonus = 0
	if not pocket_pivot.get("error") and pocket_pivot.get("pocket_pivot_count", 0) > 0:
		recent_pp = pocket_pivot.get("most_recent_pp", {})
		if recent_pp.get("quality") in ("high", "moderate"):
			pattern_bonus += 1
	if not tight_closes.get("error"):
		if tight_closes.get("signal_strength") in ("strong", "moderate"):
			pattern_bonus += 1
	if not low_cheat.get("error") and low_cheat.get("low_cheat_detected"):
		pattern_bonus += 1
	composite = min(100, round(composite + pattern_bonus, 1))

	# Evaluate hard gates before signal determination
	hard_gate_result = _evaluate_hard_gates(tt, stage, volume, vcp_result, base)

	# Apply soft-gate penalties to composite score
	if hard_gate_result["total_soft_penalty"] != 0:
		composite = max(0, round(composite + hard_gate_result["total_soft_penalty"], 1))

	# Determine signal
	tt_pass = tt.get("overall_pass", False) if not tt.get("error") else False
	signal = _determine_signal(composite, tt_pass, stage)

	# Hard-gate override: block BUY/STRONG_BUY if any hard gate triggered
	if hard_gate_result["blocked"] and signal in ("BUY", "STRONG_BUY"):
		signal = "WATCH"

	# Build signal reason codes
	signal_reason_codes = _build_signal_reason_codes(
		signal, tt, stage, rs, earnings, vcp_result, volume, base, hard_gate_result
	)

	# Earnings proximity check
	earnings_dates = results["earnings_dates"]
	is_near, days_until, next_date = _check_earnings_proximity(earnings_dates)
	if is_near:
		signal_reason_codes.append(f"EARNINGS_PROXIMITY_{days_until}D")

	# Company category hint (agent-level inference aid)
	category_hint = _infer_category_hint(earnings)

	# Position sizing (only if BUY or STRONG_BUY)
	pos_sizing = {}
	if signal in ("BUY", "STRONG_BUY"):
		entry_price = tt.get("current_price") or stage.get("current_price") or 0
		if entry_price > 0:
			pos_sizing = _run_script(
				"analysis/position_sizing.py",
				[
					"calculate",
					"--account-size",
					str(args.account_size),
					"--entry-price",
					str(entry_price),
					"--stop-loss-pct",
					"7",
				],
			)
	else:
		pos_sizing = {
			"status": "not_applicable",
			"reason": f"Signal is {signal} - position sizing requires BUY or STRONG_BUY signal",
			"tip": "Use position_sizing.py calculate with --entry-price for hypothetical entry modeling",
		}

	# Generate recommendation
	recommendation = _generate_recommendation(
		symbol, signal, tt, stage, rs, earnings, vcp_result, base, volume, composite
	)

	# Add alternative entry info to recommendation
	alt_entries = []
	if not pocket_pivot.get("error") and pocket_pivot.get("pocket_pivot_count", 0) > 0:
		pp = pocket_pivot.get("most_recent_pp", {})
		alt_entries.append(f"Pocket Pivot: {pp.get('quality', 'N/A')} ({pp.get('days_ago', '?')}d ago)")
	if not tight_closes.get("error") and tight_closes.get("signal_strength") != "none":
		alt_entries.append(f"Tight Closes: {tight_closes.get('signal_strength', 'N/A')}")
	if not low_cheat.get("error") and low_cheat.get("low_cheat_detected"):
		entry_info = low_cheat.get("entry_analysis", {})
		alt_entries.append(
			f"Low Cheat: entry ${entry_info.get('low_cheat_entry', 'N/A')}, risk {entry_info.get('risk_pct', 'N/A')}%"
		)
	if alt_entries:
		recommendation += " | Alt Entries: " + ", ".join(alt_entries)

	# Risk assessment
	risk = {
		"base_risk": base.get("risk_level", "unknown") if not base.get("error") else "unknown",
		"volume_confirmation": (
			volume.get("breakout_volume_confirmation", False) if not volume.get("error") else False
		),
		"tt_pass": tt_pass,
		"stage_2": (stage.get("current_stage") == 2) if not stage.get("error") else False,
	}

	output_json(
		{
			"symbol": symbol,
			"sepa_composite_score": composite,
			"signal": signal,
			"signal_reason_codes": signal_reason_codes,
			"hard_gate_result": hard_gate_result,
			"analysis_mode": "full",
			"recommendation_text": recommendation,
			"trend_template": tt,
			"stage_analysis": stage,
			"rs_ranking": rs,
			"earnings": earnings,
			"vcp": vcp_result,
			"base_count": base,
			"volume": volume,
			"pocket_pivot": pocket_pivot,
			"tight_closes": tight_closes,
			"low_cheat": low_cheat,
			"position_sizing": pos_sizing,
			"earnings_proximity": {
				"is_near": is_near,
				"days_until": days_until,
				"next_date": next_date,
			},
			"category_hint": category_hint,
			"risk_assessment": risk,
		}
	)


@safe_run
def cmd_watchlist(args):
	"""Batch SEPA analysis for multiple tickers."""
	results = []

	for symbol in args.symbols:
		symbol = symbol.upper()

		# Run core checks only (lighter weight for batch)
		tt = _run_script("screening/trend_template.py", ["check", symbol])
		stage = _run_script("technical/stage_analysis.py", ["classify", symbol])
		rs = _run_script("technical/rs_ranking.py", ["score", symbol])
		earnings = _run_script("data_sources/earnings_acceleration.py", ["code33", symbol])

		# Lighter-weight analysis for batch
		vcp_result = {"error": "skipped_for_batch"}
		base = {"error": "skipped_for_batch"}
		volume = _run_script("technical/volume_analysis.py", ["analyze", symbol])

		composite = _calc_composite_score(tt, stage, rs, earnings, vcp_result, base, volume)
		tt_pass = tt.get("overall_pass", False) if not tt.get("error") else False
		signal = _determine_signal(composite, tt_pass, stage)

		# Provisional mode: cap STRONG_BUY to BUY when key components are skipped
		if signal == "STRONG_BUY":
			signal = "BUY"

		results.append(
			{
				"symbol": symbol,
				"sepa_score": composite,
				"signal": signal,
				"analysis_mode": "provisional",
				"missing_components": ["vcp", "base_count"],
				"tt_pass": tt_pass,
				"tt_score": f"{tt.get('passed_count', 0)}/{tt.get('total_count', 8)}" if not tt.get("error") else "N/A",
				"stage": stage.get("current_stage", "N/A") if not stage.get("error") else "N/A",
				"rs_score": rs.get("rs_score", "N/A") if not rs.get("error") else "N/A",
				"code33": earnings.get("code33_status", "N/A") if not earnings.get("error") else "N/A",
				"volume_grade": volume.get("accumulation_distribution_rating", "N/A")
				if not volume.get("error")
				else "N/A",
			}
		)

	# Sort by composite score descending
	results.sort(key=lambda x: x.get("sepa_score", 0), reverse=True)

	output_json(
		{
			"watchlist_results": results,
			"count": len(results),
			"signal_summary": {
				"STRONG_BUY": sum(1 for r in results if r["signal"] == "STRONG_BUY"),
				"BUY": sum(1 for r in results if r["signal"] == "BUY"),
				"HOLD": sum(1 for r in results if r["signal"] == "HOLD"),
				"WATCH": sum(1 for r in results if r["signal"] == "WATCH"),
				"AVOID": sum(1 for r in results if r["signal"] == "AVOID"),
			},
		}
	)


def main():
	parser = argparse.ArgumentParser(description="SEPA Pipeline: Full Minervini Analysis")
	sub = parser.add_subparsers(dest="command", required=True)

	# analyze
	sp = sub.add_parser("analyze", help="Full SEPA analysis for a ticker")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--account-size", type=float, default=100000, help="Account size (default: 100000)")
	sp.set_defaults(func=cmd_analyze)

	# watchlist
	sp = sub.add_parser("watchlist", help="Batch SEPA analysis for multiple tickers")
	sp.add_argument("symbols", nargs="+", help="Ticker symbols")
	sp.add_argument("--account-size", type=float, default=100000, help="Account size (default: 100000)")
	sp.set_defaults(func=cmd_watchlist)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
