#!/usr/bin/env python3
"""TraderLion Pipeline: full S.N.I.P.E. analysis integrating volume edges, stage/trend,
growth, setup quality, and volume confirmation.

Orchestrates the complete S.N.I.P.E. (Search-Narrow-Identify-Plan-Execute) analysis by running
Volume Edge Detection, Trend Template, Stage Analysis, RS Ranking, Earnings Acceleration,
VCP Detection, Base Counting, Volume Analysis, Closing Range, and Position Sizing in sequence.
Produces a SNIPE Composite Score and actionable signal.

Commands:
	analyze: Full S.N.I.P.E. analysis for a single ticker
	watchlist: Batch S.N.I.P.E. analysis for multiple tickers

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
		"snipe_composite_score": float,
		"signal": str,
		"signal_reason_codes": [str],
		"hard_gate_result": {
			"blocked": bool,
			"blockers": [str],
			"soft_penalties": [{"code": str, "penalty": int}],
			"total_soft_penalty": int
		},
		"analysis_mode": "full" | "provisional",
		"edge_detection": {
			"edge_count": int,
			"edges_present": [str],
			"hv_edge_count": int
		},
		"trend_template": dict,
		"stage_analysis": dict,
		"rs_ranking": dict,
		"earnings": dict,
		"vcp": dict,
		"base_count": dict,
		"volume": dict,
		"volume_edge": dict,
		"closing_range": dict,
		"position_sizing": dict,
		"earnings_proximity": {
			"is_near": bool,
			"days_until": int or None,
			"next_date": str or None
		},
		"winning_characteristics": {
			"score": int,
			"max": 12,
			"items": [{"name": str, "present": bool}]
		},
		"tigers_summary": dict,
		"recommendation_text": str
	}

Example:
	>>> python traderlion.py analyze NVDA --account-size 100000
	{
		"symbol": "NVDA",
		"snipe_composite_score": 82.5,
		"signal": "AGGRESSIVE",
		"edge_detection": {"edge_count": 3, "edges_present": ["HV1", "RS", "N-FACTOR"]},
		"position_sizing": {"edge_count": 3, "position_pct": 17.5},
		"recommendation_text": "NVDA: SNIPE Score 82.5/100 — Signal: AGGRESSIVE | Edges: 3 (HV1, RS, N-FACTOR)"
	}

Use Cases:
	- Complete stock evaluation using TraderLion's S.N.I.P.E. methodology
	- Batch screening of watchlist for actionable setups
	- Edge-based position sizing automation
	- Volume edge and institutional footprint detection
	- Systematic comparison of multiple candidates

Notes:
	- SNIPE Score weights: Edge Detection 30, Stage/Trend 20, Growth 15, Setup Quality 15, Volume Confirmation 10, Winning Characteristics 10
	- Signals: AGGRESSIVE 80+, STANDARD 65-79, REDUCED 50-64, MONITOR 35-49, AVOID <35
	- Hard gates block AGGRESSIVE/STANDARD: Stage 3/4, TT<5/8, no volume edges + RS<50, distribution cluster + constructive ratio <0.35
	- Edge-based sizing: 10% base + 2.5% per edge, max 4 edges = 20%
	- EARNINGS_PROXIMITY signal code: appended when next earnings within 5 trading days
	- Pipeline continues even if individual components fail (graceful degradation)
	- Scripts execute in parallel via ThreadPoolExecutor for ~50-70% speedup
	- Each script runs in independent subprocess (no shared state)
	- Watchlist mode remains sequential per-ticker with lighter-weight analysis
	- Provisional mode: AGGRESSIVE capped to STANDARD, missing_components listed

See Also:
	- volume_edge.py: HVE/HVIPO/HV1/Increasing Average Volume detection
	- closing_range.py: Constructive/Non-constructive bar classification
	- trend_template.py: Trend Template 8-criteria check
	- stage_analysis.py: Stage 1-4 classification
	- rs_ranking.py: Relative strength scoring
	- earnings_acceleration.py: Code 33 and earnings analysis
	- vcp.py: Volatility Contraction Pattern detection
	- base_count.py: Base counting within Stage 2
	- volume_analysis.py: Accumulation/distribution rating
	- position_sizing.py: Risk-based position sizing
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
# Edge counting
# ---------------------------------------------------------------------------

def _count_edges(volume_edge, rs, earnings):
	"""Count TraderLion edges present for position sizing.

	Edges (max 6):
	1. HVE (Highest Volume Ever)
	2. HVIPO (Highest Volume Since IPO)
	3. HV1 (Highest Volume in 1 Year)
	4. Increasing Average Volume
	5. RS edge (RS score >= 70)
	6. N-Factor (approximated from earnings surprises + acceleration)

	Returns:
		dict with edge_count, edges_present, hv_edge_count
	"""
	edges = []
	hv_count = 0

	# Volume edges from volume_edge.py detect
	if not volume_edge.get("error"):
		if volume_edge.get("hve", {}).get("detected"):
			edges.append("HVE")
			hv_count += 1
		if volume_edge.get("hvipo", {}).get("detected"):
			edges.append("HVIPO")
			hv_count += 1
		if volume_edge.get("hv1", {}).get("detected"):
			edges.append("HV1")
			hv_count += 1
		if volume_edge.get("increasing_avg_volume", {}).get("detected"):
			edges.append("INCREASING_AVG_VOL")

	# RS edge
	if not rs.get("error"):
		rs_score = rs.get("rs_score", 0) or 0
		if rs_score >= 70:
			edges.append("RS")

	# N-Factor proxy (earnings-based)
	if not earnings.get("error"):
		eps_acc = earnings.get("eps_accelerating", False)
		surprise_pct = 0
		surprises = earnings.get("surprise_history", [])
		if surprises and isinstance(surprises, list):
			recent = [s for s in surprises if isinstance(s, dict)]
			if recent:
				surprise_pct = recent[-1].get("surprise_pct", 0) or 0
		if eps_acc and surprise_pct > 10:
			edges.append("N-FACTOR")

	return {
		"edge_count": len(edges),
		"edges_present": edges,
		"hv_edge_count": hv_count,
	}


# ---------------------------------------------------------------------------
# Winning Characteristics (0-12)
# ---------------------------------------------------------------------------

def _count_winning_characteristics(volume_edge, rs, earnings, vcp, tt, stage, closing_range):
	"""Count Winning Characteristics score (0-12).

	Fundamental (6): Theme, N-Factor, EPS>25%, Sales>25%, Surprises, Forward est.
	Technical  (6): HV edge, IncAvgVol, RS uptrend, RS days, MA maint, Setup
	"""
	count = 0

	# -- Fundamental --
	# 1. Theme alignment: agent-level only, skip
	# 2. N-Factor
	if not earnings.get("error"):
		surprises = earnings.get("surprise_history", [])
		if surprises and isinstance(surprises, list):
			recent = [s for s in surprises if isinstance(s, dict)]
			if recent and earnings.get("eps_accelerating") and (recent[-1].get("surprise_pct", 0) or 0) > 10:
				count += 1

	# 3. EPS growth > 25%
	if not earnings.get("error"):
		eps_growth = earnings.get("eps_quarterly_growth", [])
		if eps_growth and isinstance(eps_growth, list):
			latest = eps_growth[-1] if eps_growth else {}
			if isinstance(latest, dict) and (latest.get("growth_pct", 0) or 0) > 25:
				count += 1

	# 4. Sales growth > 25%
	if not earnings.get("error") and earnings.get("sales_accelerating"):
		count += 1

	# 5. EPS/Revenue surprises (2 of last 3 positive)
	if not earnings.get("error"):
		surprises = earnings.get("surprise_history", [])
		if surprises and isinstance(surprises, list):
			recent = [s for s in surprises[-3:] if isinstance(s, dict)]
			if sum(1 for s in recent if (s.get("surprise_pct", 0) or 0) > 0) >= 2:
				count += 1

	# 6. Strong forward estimates (Code 33 as proxy)
	if not earnings.get("error") and earnings.get("code33_status") == "PASS":
		count += 1

	# -- Technical --
	# 7. HV edge present
	if not volume_edge.get("error"):
		if any([
			volume_edge.get("hve", {}).get("detected"),
			volume_edge.get("hvipo", {}).get("detected"),
			volume_edge.get("hv1", {}).get("detected"),
		]):
			count += 1

	# 8. Increasing average volume
	if not volume_edge.get("error") and volume_edge.get("increasing_avg_volume", {}).get("detected"):
		count += 1

	# 9. RS line uptrend / new highs
	if not rs.get("error") and (rs.get("rs_score", 0) or 0) >= 70:
		count += 1

	# 10. RS days > 60% (proxy: RS >= 80 implies strong RS days)
	if not rs.get("error") and (rs.get("rs_score", 0) or 0) >= 80:
		count += 1

	# 11. MA maintenance (from Trend Template)
	if not tt.get("error") and (tt.get("overall_pass") or tt.get("score_pct", 0) >= 75):
		count += 1

	# 12. Actionable setup formation
	if not vcp.get("error") and vcp.get("vcp_detected"):
		count += 1

	return count


def _build_winning_characteristics_detail(volume_edge, rs, earnings, vcp, tt, stage, closing_range):
	"""Build detailed winning characteristics list with per-item status."""
	items = []

	# 1. Theme alignment
	items.append({"name": "Theme Alignment", "present": False, "note": "Agent-level assessment required"})

	# 2. Innovation / N-Factor
	n_factor = False
	if not earnings.get("error"):
		surprises = earnings.get("surprise_history", [])
		if surprises and isinstance(surprises, list):
			recent = [s for s in surprises if isinstance(s, dict)]
			if recent and earnings.get("eps_accelerating") and (recent[-1].get("surprise_pct", 0) or 0) > 10:
				n_factor = True
	items.append({"name": "Innovation / N-Factor", "present": n_factor})

	# 3. EPS growth > 25%
	eps_strong = False
	if not earnings.get("error"):
		eps_growth = earnings.get("eps_quarterly_growth", [])
		if eps_growth and isinstance(eps_growth, list):
			latest = eps_growth[-1] if eps_growth else {}
			if isinstance(latest, dict) and (latest.get("growth_pct", 0) or 0) > 25:
				eps_strong = True
	items.append({"name": "EPS Growth >25% YoY", "present": eps_strong})

	# 4. Sales growth > 25%
	sales_strong = not earnings.get("error") and earnings.get("sales_accelerating", False)
	items.append({"name": "Sales Growth >25% YoY", "present": sales_strong})

	# 5. EPS/Revenue surprises
	surprises_strong = False
	if not earnings.get("error"):
		surprises = earnings.get("surprise_history", [])
		if surprises and isinstance(surprises, list):
			recent = [s for s in surprises[-3:] if isinstance(s, dict)]
			if sum(1 for s in recent if (s.get("surprise_pct", 0) or 0) > 0) >= 2:
				surprises_strong = True
	items.append({"name": "EPS/Revenue Surprises", "present": surprises_strong})

	# 6. Strong forward estimates
	forward = not earnings.get("error") and earnings.get("code33_status") == "PASS"
	items.append({"name": "Strong Forward Estimates", "present": forward})

	# 7. HV edge
	hv = False
	if not volume_edge.get("error"):
		hv = any([
			volume_edge.get("hve", {}).get("detected"),
			volume_edge.get("hvipo", {}).get("detected"),
			volume_edge.get("hv1", {}).get("detected"),
		])
	items.append({"name": "HV Edge Present", "present": hv})

	# 8. Increasing avg vol
	inc_vol = not volume_edge.get("error") and volume_edge.get("increasing_avg_volume", {}).get("detected", False)
	items.append({"name": "Increasing Average Volume", "present": inc_vol})

	# 9. RS uptrend
	rs_up = not rs.get("error") and (rs.get("rs_score", 0) or 0) >= 70
	items.append({"name": "RS Line Uptrend / New Highs", "present": rs_up})

	# 10. RS days > 60%
	rs_days = not rs.get("error") and (rs.get("rs_score", 0) or 0) >= 80
	items.append({"name": "RS Days >60%", "present": rs_days})

	# 11. MA maintenance
	ma_ok = not tt.get("error") and (tt.get("overall_pass") or tt.get("score_pct", 0) >= 75)
	items.append({"name": "MA Maintenance", "present": ma_ok})

	# 12. Actionable setup
	setup = not vcp.get("error") and vcp.get("vcp_detected", False)
	items.append({"name": "Actionable Setup Formation", "present": setup})

	return items


# ---------------------------------------------------------------------------
# SNIPE Composite Score
# ---------------------------------------------------------------------------

def _calc_snipe_score(volume_edge, tt, stage, rs, earnings, vcp, base, volume, closing_range, edge_info):
	"""Calculate weighted SNIPE Composite Score (0-100).

	Weights:
	- Edge Detection: 30 (institutional footprint — most important in TraderLion)
	- Stage/Trend: 20 (technical health)
	- Growth: 15 (fundamental driver)
	- Setup Quality: 15 (entry timing)
	- Volume Confirmation: 10 (accumulation evidence)
	- Winning Characteristics: 10 (composite quality)
	"""
	score = 0.0

	# === Edge Detection (30 points) ===
	edge_score = 0.0

	# Volume edges (0-15)
	if not volume_edge.get("error"):
		if volume_edge.get("hve", {}).get("detected"):
			edge_score += 8
		if volume_edge.get("hvipo", {}).get("detected"):
			edge_score += 6
		if volume_edge.get("hv1", {}).get("detected"):
			edge_score += 4
		if volume_edge.get("increasing_avg_volume", {}).get("detected"):
			edge_score += 3
		edge_score = min(edge_score, 15)

	# RS edge (0-10)
	if not rs.get("error"):
		rs_score = rs.get("rs_score", 0) or 0
		if rs_score >= 85:
			edge_score += 10
		elif rs_score >= 70:
			edge_score += 7
		elif rs_score >= 55:
			edge_score += 4
		elif rs_score >= 40:
			edge_score += 2

	# N-Factor proxy (0-5)
	if not earnings.get("error"):
		n_pts = 0
		if earnings.get("eps_accelerating"):
			n_pts += 2
		surprises = earnings.get("surprise_history", [])
		if surprises and isinstance(surprises, list):
			recent = [s for s in surprises if isinstance(s, dict)]
			if recent and (recent[-1].get("surprise_pct", 0) or 0) > 10:
				n_pts += 3
			elif recent and (recent[-1].get("surprise_pct", 0) or 0) > 0:
				n_pts += 1
		edge_score += min(n_pts, 5)

	score += min(edge_score, 30)

	# === Stage/Trend (20 points) ===
	# Trend Template (0-12)
	if not tt.get("error"):
		tt_pct = tt.get("score_pct", 0)
		score += tt_pct / 100 * 12

	# Stage Analysis (0-8)
	if not stage.get("error"):
		current_stage = stage.get("current_stage", 0)
		confidence = stage.get("stage_confidence", 50)
		if current_stage == 2:
			score += confidence / 100 * 8
		elif current_stage == 1:
			score += 3

	# === Growth (15 points) ===
	if not earnings.get("error"):
		growth_score = 0
		if earnings.get("eps_accelerating"):
			growth_score += 6
		if earnings.get("sales_accelerating"):
			growth_score += 5
		if earnings.get("margin_expanding"):
			growth_score += 2
		if earnings.get("code33_status") == "PASS":
			growth_score += 2
		elif earnings.get("eps_accelerating"):
			growth_score += 1
		score += min(growth_score, 15)

	# === Setup Quality (15 points) ===
	setup_score = 0.0

	# VCP (0-8)
	if not vcp.get("error"):
		if vcp.get("vcp_detected"):
			quality = vcp.get("pattern_quality", "none")
			if quality == "high":
				setup_score += 8
			elif quality == "moderate":
				setup_score += 5
			elif quality == "low":
				setup_score += 3
		else:
			setup_score += 1  # Base credit for analysis available

	# Base count (0-4)
	if not base.get("error"):
		base_num = base.get("current_base_number", 0)
		if base_num == 1:
			setup_score += 4
		elif base_num == 2:
			setup_score += 3
		elif base_num == 3:
			setup_score += 2
		elif base_num >= 4:
			setup_score += 1

	# Closing range constructive ratio (0-3)
	if not closing_range.get("error"):
		cr_ratio = closing_range.get("constructive_ratio", 0) or 0
		if cr_ratio > 0.7:
			setup_score += 3
		elif cr_ratio > 0.5:
			setup_score += 2
		elif cr_ratio > 0.35:
			setup_score += 1

	score += min(setup_score, 15)

	# === Volume Confirmation (10 points) ===
	if not volume.get("error"):
		vol_score = 0
		grade = volume.get("accumulation_distribution_rating", "C")
		base_scores = {"A+": 5, "A": 4, "B+": 3, "B": 2, "C": 1, "D": 0, "E": 0}
		vol_score = base_scores.get(grade, 1)

		# Distribution cluster penalty (-2)
		clusters = volume.get("distribution_clusters", {})
		if clusters.get("cluster_warning"):
			vol_score -= 2

		# Pullback quality bonus (+2)
		if volume.get("pullback_volume_declining") is True:
			vol_score += 2

		# 20d up/down volume ratio (+2 or -2)
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

	# === Winning Characteristics (10 points) ===
	wc_count = _count_winning_characteristics(volume_edge, rs, earnings, vcp, tt, stage, closing_range)
	score += wc_count / 12 * 10

	return round(score, 1)


# ---------------------------------------------------------------------------
# Hard Gates
# ---------------------------------------------------------------------------

def _evaluate_hard_gates(tt, stage, volume_edge, rs, volume, closing_range):
	"""Evaluate 4 TraderLion hard gates + soft penalties.

	Hard gates (any triggered = blocked):
	- HG-1: Stage 3/4 → blocked
	- HG-2: TT < 5/8 → blocked
	- HG-3: 0 volume edges AND RS < 50 → blocked ("기관 발자국 없음")
	- HG-4: Distribution cluster + constructive bar ratio < 0.35 → blocked
	"""
	blockers = []
	soft_penalties = []

	# HG-1: Stage 3 or 4
	current_stage = stage.get("current_stage", 0) if not stage.get("error") else 0
	if current_stage in (3, 4):
		blockers.append(f"HG1_STAGE_{current_stage}_BLOCKED")

	# HG-2: Trend Template < 5/8
	if not tt.get("error"):
		passed = tt.get("passed_count", 0)
		if passed < 5:
			blockers.append(f"HG2_TT_INSUFFICIENT_{passed}_8")

	# HG-3: No volume edges AND RS < 50
	has_vol_edge = False
	if not volume_edge.get("error"):
		has_vol_edge = any([
			volume_edge.get("hve", {}).get("detected"),
			volume_edge.get("hvipo", {}).get("detected"),
			volume_edge.get("hv1", {}).get("detected"),
		])
	rs_score = rs.get("rs_score", 0) or 0 if not rs.get("error") else 0
	if not has_vol_edge and rs_score < 50:
		blockers.append("HG3_NO_INSTITUTIONAL_FOOTPRINT")

	# HG-4: Distribution cluster + constructive ratio < 0.35
	has_dist_cluster = False
	if not volume.get("error"):
		clusters = volume.get("distribution_clusters", {})
		has_dist_cluster = clusters.get("cluster_warning", False)

	cr_ratio = 0.5  # default neutral
	if not closing_range.get("error"):
		cr_ratio = closing_range.get("constructive_ratio", 0.5) or 0.5

	if has_dist_cluster and cr_ratio < 0.35:
		blockers.append("HG4_DISTRIBUTION_WEAK_CONSTRUCTION")

	# --- Soft Penalties ---

	# SP-1: No increasing average volume (-3)
	if not volume_edge.get("error") and not volume_edge.get("increasing_avg_volume", {}).get("detected"):
		soft_penalties.append({"code": "NO_INCREASING_AVG_VOL", "penalty": -3})

	# SP-2: Weak constructive ratio without cluster (-3)
	if cr_ratio < 0.5 and not has_dist_cluster:
		soft_penalties.append({"code": "WEAK_CONSTRUCTIVE_RATIO", "penalty": -3})

	# SP-3: Excessive 200MA extension (-3)
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

	return {
		"blocked": len(blockers) > 0,
		"blockers": blockers,
		"soft_penalties": soft_penalties,
		"total_soft_penalty": total_soft_penalty,
	}


# ---------------------------------------------------------------------------
# Signal Determination
# ---------------------------------------------------------------------------

def _determine_signal(snipe_score, hard_gate_blocked):
	"""Determine signal based on SNIPE score and hard-gate status.

	AGGRESSIVE: 80+  (strong entry candidate)
	STANDARD:   65-79 (actionable with standard sizing)
	REDUCED:    50-64 (cautious, watch for improvement)
	MONITOR:    35-49 (watchlist only)
	AVOID:      <35   (do not trade)
	"""
	if hard_gate_blocked:
		if snipe_score >= 50:
			return "MONITOR"
		else:
			return "AVOID"

	if snipe_score >= 80:
		return "AGGRESSIVE"
	elif snipe_score >= 65:
		return "STANDARD"
	elif snipe_score >= 50:
		return "REDUCED"
	elif snipe_score >= 35:
		return "MONITOR"
	else:
		return "AVOID"


# ---------------------------------------------------------------------------
# Edge-Based Position Sizing
# ---------------------------------------------------------------------------

def _calc_edge_based_sizing(edge_count, signal, account_size, entry_price, stop_pct=5.0):
	"""Calculate edge-based position sizing.

	Base: 10% + 2.5% per edge, max 4 edges = 20%.
	Market adjustment (Weak=5%/Normal=10%/Strong=15% base) applied at agent level.
	"""
	if signal in ("AVOID", "MONITOR"):
		return {
			"status": "not_applicable",
			"reason": f"Signal is {signal} — position sizing requires STANDARD or AGGRESSIVE signal",
			"edge_count": edge_count,
		}

	if signal == "REDUCED":
		return {
			"status": "reduced",
			"reason": "REDUCED signal — use minimum sizing (5-10%) until re-qualification",
			"edge_count": edge_count,
			"suggested_pct": 5.0,
			"suggested_amount": round(account_size * 0.05, 2),
		}

	capped_edges = min(edge_count, 4)
	position_pct = 10.0 + (capped_edges * 2.5)
	position_amount = account_size * (position_pct / 100)

	shares = 0
	if entry_price > 0:
		shares = int(position_amount / entry_price)

	risk_amount = position_amount * (stop_pct / 100)
	risk_pct_of_account = risk_amount / account_size * 100 if account_size > 0 else 0

	return {
		"status": "calculated",
		"edge_count": capped_edges,
		"base_pct": 10.0,
		"per_edge_pct": 2.5,
		"position_pct": position_pct,
		"position_amount": round(position_amount, 2),
		"shares_at_entry": shares,
		"entry_price": entry_price,
		"stop_pct": stop_pct,
		"risk_amount": round(risk_amount, 2),
		"risk_pct_of_account": round(risk_pct_of_account, 2),
		"note": "Market adjustment (Weak=5%/Normal=10%/Strong=15% base) applied at agent level",
	}


# ---------------------------------------------------------------------------
# Signal Reason Codes
# ---------------------------------------------------------------------------

def _build_signal_reason_codes(signal, tt, stage, rs, earnings, vcp, volume, volume_edge, closing_range, base, edge_info, hard_gate_result):
	"""Build human-readable reason codes explaining the signal determination."""
	codes = []

	# Edge summary
	if edge_info["edge_count"] > 0:
		codes.append(f"EDGES_{edge_info['edge_count']}_{'+'.join(edge_info['edges_present'])}")
	else:
		codes.append("EDGES_NONE")

	# Trend Template
	if not tt.get("error"):
		passed = tt.get("passed_count", 0)
		codes.append(f"TT_{passed}_8")

	# Stage
	if not stage.get("error"):
		s = stage.get("current_stage", 0)
		conf = stage.get("stage_confidence", 0)
		codes.append(f"STAGE_{s}_CONF_{int(conf)}")

	# RS
	if not rs.get("error"):
		rs_val = rs.get("rs_score", 0) or 0
		if rs_val >= 80:
			codes.append("RS_LEADER")
		elif rs_val >= 70:
			codes.append("RS_STRONG")
		elif rs_val >= 50:
			codes.append("RS_MODERATE")
		else:
			codes.append("RS_WEAK")

	# Volume edges
	if not volume_edge.get("error"):
		for edge_key, code in [("hve", "HVE"), ("hvipo", "HVIPO"), ("hv1", "HV1")]:
			if volume_edge.get(edge_key, {}).get("detected"):
				codes.append(code)
		if volume_edge.get("increasing_avg_volume", {}).get("detected"):
			codes.append("INCREASING_AVG_VOL")
		codes.append(f"CONVICTION_{volume_edge.get('conviction_level', 'unknown').upper()}")

	# VCP
	if not vcp.get("error"):
		if vcp.get("vcp_detected"):
			codes.append(f"VCP_{vcp.get('pattern_quality', 'unknown').upper()}")
		else:
			codes.append("VCP_NONE")

	# Volume grade
	if not volume.get("error"):
		grade = volume.get("accumulation_distribution_rating", "N/A")
		codes.append(f"VOL_GRADE_{grade}")
		if volume.get("distribution_clusters", {}).get("cluster_warning"):
			codes.append("DIST_CLUSTER_WARNING")

	# Closing range
	if not closing_range.get("error"):
		cr = closing_range.get("constructive_ratio", 0)
		if cr:
			codes.append(f"CR_RATIO_{int(cr * 100)}PCT")

	# Base
	if not base.get("error"):
		codes.append(f"BASE_{base.get('current_base_number', 0)}")

	# Hard gates
	if hard_gate_result["blocked"]:
		for b in hard_gate_result["blockers"]:
			codes.append(f"HARD_GATE:{b}")

	return codes


# ---------------------------------------------------------------------------
# Earnings Proximity
# ---------------------------------------------------------------------------

def _check_earnings_proximity(earnings_dates_result):
	"""Check if next earnings date is within 5 trading days."""
	from datetime import datetime, timedelta

	if earnings_dates_result.get("error"):
		return False, None, None

	dates = earnings_dates_result.get("earnings_dates", [])
	if not dates:
		return False, None, None

	today = datetime.now().date()

	for entry in dates:
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

		# Count business days
		days_until = 0
		current = today
		while current < earn_date:
			current += timedelta(days=1)
			if current.weekday() < 5:
				days_until += 1

		if days_until <= 5:
			return True, days_until, str(earn_date)
		else:
			return False, days_until, str(earn_date)

	return False, None, None


# ---------------------------------------------------------------------------
# TIGERS Summary
# ---------------------------------------------------------------------------

def _build_tigers_summary(tt, stage, rs, earnings, vcp, volume_edge):
	"""Build TIGERS criteria summary for agent-level interpretation."""
	tigers = {}

	# T — Theme (agent-level)
	tigers["T_theme"] = {"status": "agent_required", "note": "Theme assessment requires agent-level inference"}

	# I — Innovation (N-Factor proxy)
	i_status = "unknown"
	if not earnings.get("error"):
		if earnings.get("code33_status") == "PASS" and earnings.get("eps_accelerating"):
			i_status = "strong_growth_innovation"
		elif earnings.get("eps_accelerating"):
			i_status = "possible_catalyst"
	tigers["I_innovation"] = {"status": i_status}

	# G — Growth
	g_status = "unknown"
	if not earnings.get("error"):
		if earnings.get("eps_accelerating") and earnings.get("sales_accelerating"):
			g_status = "accelerating"
		elif earnings.get("eps_accelerating") or earnings.get("sales_accelerating"):
			g_status = "growing"
		else:
			g_status = "flat_or_declining"
	tigers["G_growth"] = {
		"status": g_status,
		"code33": earnings.get("code33_status") if not earnings.get("error") else "N/A",
	}

	# E — Edges
	edge_list = []
	if not volume_edge.get("error"):
		if volume_edge.get("hve", {}).get("detected"):
			edge_list.append("HVE")
		if volume_edge.get("hvipo", {}).get("detected"):
			edge_list.append("HVIPO")
		if volume_edge.get("hv1", {}).get("detected"):
			edge_list.append("HV1")
		if volume_edge.get("increasing_avg_volume", {}).get("detected"):
			edge_list.append("IncAvgVol")
	tigers["E_edges"] = {"volume_edges": edge_list}

	# R — Relative Strength
	r_status = "unknown"
	if not rs.get("error"):
		rs_score = rs.get("rs_score", 0) or 0
		if rs_score >= 85:
			r_status = "leader"
		elif rs_score >= 70:
			r_status = "strong"
		elif rs_score >= 50:
			r_status = "moderate"
		else:
			r_status = "weak"
	tigers["R_relative_strength"] = {
		"status": r_status,
		"rs_score": rs.get("rs_score") if not rs.get("error") else "N/A",
	}

	# S — Setup
	s_status = "none"
	if not vcp.get("error") and vcp.get("vcp_detected"):
		s_status = f"VCP_{vcp.get('pattern_quality', 'unknown')}"
	tigers["S_setup"] = {"status": s_status}

	return tigers


# ---------------------------------------------------------------------------
# Recommendation Text
# ---------------------------------------------------------------------------

def _generate_recommendation(symbol, signal, snipe_score, edge_info, tt, stage, rs, vcp, volume, volume_edge):
	"""Generate human-readable recommendation text."""
	parts = [f"{symbol}: SNIPE Score {snipe_score}/100 — Signal: {signal}"]

	# Edges
	if edge_info["edge_count"] > 0:
		parts.append(f"Edges: {edge_info['edge_count']} ({', '.join(edge_info['edges_present'])})")
	else:
		parts.append("Edges: None detected")

	# TT
	if not tt.get("error"):
		parts.append(f"TT: {tt.get('passed_count', 0)}/8")

	# Stage
	if not stage.get("error"):
		parts.append(f"Stage: {stage.get('current_stage')} ({stage.get('stage_name', 'Unknown')})")

	# RS
	if not rs.get("error"):
		parts.append(f"RS: {rs.get('rs_score', 'N/A')}")

	# Volume edges
	if not volume_edge.get("error"):
		ve_flags = []
		if volume_edge.get("hve", {}).get("detected"):
			ve_flags.append("HVE")
		if volume_edge.get("hvipo", {}).get("detected"):
			ve_flags.append("HVIPO")
		if volume_edge.get("hv1", {}).get("detected"):
			ve_flags.append("HV1")
		if volume_edge.get("increasing_avg_volume", {}).get("detected"):
			ve_flags.append("IncAvgVol")
		if ve_flags:
			parts.append(f"Vol Edges: {', '.join(ve_flags)}")

	# VCP
	if not vcp.get("error"):
		if vcp.get("vcp_detected"):
			parts.append(f"VCP: {vcp.get('pattern_quality', 'N/A')}")
		else:
			parts.append("VCP: Not detected")

	# Volume grade
	if not volume.get("error"):
		parts.append(f"Volume: {volume.get('accumulation_distribution_rating', 'N/A')}")

	return " | ".join(parts)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@safe_run
def cmd_analyze(args):
	"""Full S.N.I.P.E. analysis for a single ticker."""
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
		"volume_edge": ("technical/volume_edge.py", ["detect", symbol]),
		"closing_range": ("technical/closing_range.py", ["analyze", symbol]),
		"earnings_dates": ("data_sources/actions.py", ["get-earnings-dates", symbol, "--limit", "4"]),
	}

	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		futures = {name: executor.submit(_run_script, path, a) for name, (path, a) in scripts.items()}
		results = {name: future.result() for name, future in futures.items()}

	tt = results["tt"]
	stage = results["stage"]
	rs = results["rs"]
	earnings = results["earnings"]
	vcp_result = results["vcp_result"]
	base = results["base"]
	volume = results["volume"]
	vol_edge = results["volume_edge"]
	cr = results["closing_range"]

	# Count edges
	edge_info = _count_edges(vol_edge, rs, earnings)

	# Calculate SNIPE composite score
	snipe_score = _calc_snipe_score(vol_edge, tt, stage, rs, earnings, vcp_result, base, volume, cr, edge_info)

	# Evaluate hard gates
	hard_gate_result = _evaluate_hard_gates(tt, stage, vol_edge, rs, volume, cr)

	# Apply soft penalties to score
	if hard_gate_result["total_soft_penalty"] != 0:
		snipe_score = max(0, round(snipe_score + hard_gate_result["total_soft_penalty"], 1))

	# Determine signal
	signal = _determine_signal(snipe_score, hard_gate_result["blocked"])

	# Build signal reason codes
	signal_reason_codes = _build_signal_reason_codes(
		signal, tt, stage, rs, earnings, vcp_result, volume, vol_edge, cr, base, edge_info, hard_gate_result
	)

	# Earnings proximity check
	earnings_dates = results["earnings_dates"]
	is_near, days_until, next_date = _check_earnings_proximity(earnings_dates)
	if is_near:
		signal_reason_codes.append(f"EARNINGS_PROXIMITY_{days_until}D")

	# Winning characteristics
	wc_count = _count_winning_characteristics(vol_edge, rs, earnings, vcp_result, tt, stage, cr)
	wc_items = _build_winning_characteristics_detail(vol_edge, rs, earnings, vcp_result, tt, stage, cr)

	# Position sizing
	entry_price = tt.get("current_price") or stage.get("current_price") or 0
	pos_sizing = _calc_edge_based_sizing(edge_info["edge_count"], signal, args.account_size, entry_price)

	# Recommendation
	recommendation = _generate_recommendation(
		symbol, signal, snipe_score, edge_info, tt, stage, rs, vcp_result, volume, vol_edge
	)

	# TIGERS summary
	tigers = _build_tigers_summary(tt, stage, rs, earnings, vcp_result, vol_edge)

	output_json({
		"symbol": symbol,
		"snipe_composite_score": snipe_score,
		"signal": signal,
		"signal_reason_codes": signal_reason_codes,
		"hard_gate_result": hard_gate_result,
		"analysis_mode": "full",
		"edge_detection": edge_info,
		"trend_template": tt,
		"stage_analysis": stage,
		"rs_ranking": rs,
		"earnings": earnings,
		"vcp": vcp_result,
		"base_count": base,
		"volume": volume,
		"volume_edge": vol_edge,
		"closing_range": cr,
		"position_sizing": pos_sizing,
		"earnings_proximity": {
			"is_near": is_near,
			"days_until": days_until,
			"next_date": next_date,
		},
		"winning_characteristics": {
			"score": wc_count,
			"max": 12,
			"items": wc_items,
		},
		"tigers_summary": tigers,
		"recommendation_text": recommendation,
	})


@safe_run
def cmd_watchlist(args):
	"""Batch S.N.I.P.E. analysis for multiple tickers."""
	results = []

	for symbol in args.symbols:
		symbol = symbol.upper()

		# Core checks for batch mode (lighter weight)
		tt = _run_script("screening/trend_template.py", ["check", symbol])
		stage = _run_script("technical/stage_analysis.py", ["classify", symbol])
		rs = _run_script("technical/rs_ranking.py", ["score", symbol])
		earnings = _run_script("data_sources/earnings_acceleration.py", ["code33", symbol])
		volume = _run_script("technical/volume_analysis.py", ["analyze", symbol])
		vol_edge = _run_script("technical/volume_edge.py", ["detect", symbol])

		# Skipped in batch
		vcp_result = {"error": "skipped_for_batch"}
		base = {"error": "skipped_for_batch"}
		cr = {"error": "skipped_for_batch"}

		# Edge count
		edge_info = _count_edges(vol_edge, rs, earnings)

		# Simplified score
		snipe_score = _calc_snipe_score(vol_edge, tt, stage, rs, earnings, vcp_result, base, volume, cr, edge_info)

		# Hard gates (no closing_range in batch)
		hard_gate_result = _evaluate_hard_gates(tt, stage, vol_edge, rs, volume, cr)

		# Apply soft penalties
		if hard_gate_result["total_soft_penalty"] != 0:
			snipe_score = max(0, round(snipe_score + hard_gate_result["total_soft_penalty"], 1))

		# Signal
		signal = _determine_signal(snipe_score, hard_gate_result["blocked"])

		# Provisional mode: cap AGGRESSIVE to STANDARD
		if signal == "AGGRESSIVE":
			signal = "STANDARD"

		results.append({
			"symbol": symbol,
			"snipe_score": snipe_score,
			"signal": signal,
			"analysis_mode": "provisional",
			"missing_components": ["vcp", "base_count", "closing_range"],
			"edge_count": edge_info["edge_count"],
			"edges_present": edge_info["edges_present"],
			"tt_score": f"{tt.get('passed_count', 0)}/{tt.get('total_count', 8)}" if not tt.get("error") else "N/A",
			"stage": stage.get("current_stage", "N/A") if not stage.get("error") else "N/A",
			"rs_score": rs.get("rs_score", "N/A") if not rs.get("error") else "N/A",
			"volume_grade": volume.get("accumulation_distribution_rating", "N/A") if not volume.get("error") else "N/A",
			"hard_gate_blocked": hard_gate_result["blocked"],
		})

	# Sort by SNIPE score descending
	results.sort(key=lambda x: x.get("snipe_score", 0), reverse=True)

	output_json({
		"watchlist_results": results,
		"count": len(results),
		"signal_summary": {
			"AGGRESSIVE": sum(1 for r in results if r["signal"] == "AGGRESSIVE"),
			"STANDARD": sum(1 for r in results if r["signal"] == "STANDARD"),
			"REDUCED": sum(1 for r in results if r["signal"] == "REDUCED"),
			"MONITOR": sum(1 for r in results if r["signal"] == "MONITOR"),
			"AVOID": sum(1 for r in results if r["signal"] == "AVOID"),
		},
	})


def main():
	parser = argparse.ArgumentParser(description="SNIPE Pipeline: Full TraderLion S.N.I.P.E. Analysis")
	sub = parser.add_subparsers(dest="command", required=True)

	# analyze
	sp = sub.add_parser("analyze", help="Full S.N.I.P.E. analysis for a ticker")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--account-size", type=float, default=100000, help="Account size (default: 100000)")
	sp.set_defaults(func=cmd_analyze)

	# watchlist
	sp = sub.add_parser("watchlist", help="Batch S.N.I.P.E. analysis for multiple tickers")
	sp.add_argument("symbols", nargs="+", help="Ticker symbols")
	sp.add_argument("--account-size", type=float, default=100000, help="Account size (default: 100000)")
	sp.set_defaults(func=cmd_watchlist)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
