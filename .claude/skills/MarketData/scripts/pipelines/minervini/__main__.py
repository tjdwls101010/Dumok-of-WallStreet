#!/usr/bin/env python3
"""Minervini SEPA Pipeline v1.1.0 (Pipeline-Complete): SEPA analysis with
composite scoring, risk assessment, signal synthesis, and market leadership.

Orchestrates the complete Minervini SEPA (Specific Entry Point Analysis) by
running trend qualification, technical setup, fundamental validation, and risk
assessment modules in parallel. Pipeline-Complete -- all methodology-required
module calls are contained within the pipeline; do not call individual modules
to supplement.

SEPA composite score (0-100) across 4 dimensions (25 pts each): Trend Quality,
Fundamental Strength, Setup Readiness, Risk Profile. Hard gates: Stage 2 + Trend
Template 8/8 must pass or stock is classified "avoid". Dimensions are always
computed (even on hard_gate_fail) for informational purposes.

Commands:
	analyze: Full SEPA analysis for a single ticker (~20 modules in parallel,
		SEPA composite score 0-100, risk assessment with stop-loss/R:R/position
		sizing, unified entry/exit signals, 8-key JSON output grouped as
		trend_qualification, technical_setup, fundamentals, risk_assessment).
		Module outputs stripped of symbol/date/current_price (top-level ticker
		is canonical). RS ranking integrated as rs_detail in trend_qualification.
		Sell signals canonical in risk_assessment (exit_signals has ref only).
	screen: Screen for SEPA candidates using Finviz presets (finviz screen ->
		trend template filter -> Code 33 + RS ranking on passes -> sorted
		candidates with screening scores + thresholds)
	market-leaders: Market leadership assessment (sector_leaders.scan,
		finviz market-breadth, distribution day count -> market environment
		verdict with verdict_evidence and thresholds)
	compare: Compare multiple tickers side-by-side on SEPA criteria (runs
		analyze for each ticker in parallel, extracts SEPA scores and key
		metrics, returns comparison table sorted by SEPA score)
	recheck: Recheck existing position (post_breakout.monitor with entry
		params, sell_signals, current SEPA status -> verdict: HOLD / REDUCE
		/ SELL with reasons, compressed volume_analysis)

Args:
	For analyze:
		ticker (str): Stock ticker symbol

	For screen:
		--preset (str): Finviz preset name (default: minervini_leaders)
		--sector (str): Screen within specific sector
		--industry (str): Screen within specific industry
		--limit (int): Maximum results (default: 50)

	For market-leaders:
		No required args.

	For compare:
		tickers (str[]): Ticker symbols to compare (2+ tickers)

	For recheck:
		ticker (str): Stock ticker symbol
		--entry-price (float): Position entry price (required)
		--entry-date (str): Entry date YYYY-MM-DD (required)
		--stop-loss (float): Stop-loss percentage (default: 7.0)

Returns:
	For analyze:
		dict with ticker, sepa_score (score 0-100, classification, dimensions
		always computed, hard_gate_fail/reasons, thresholds), signal (overall
		BUY_READY/WATCH/HOLD/REDUCE/SELL with thresholds, entry_signals,
		exit_signals as ref-only, volume_confirmation with thresholds, reasons),
		trend_qualification (trend_template, stage_analysis, rs_detail,
		base_count), technical_setup (vcp, entry_patterns, pocket_pivot
		compressed, low_cheat, tight_closes max 3 clusters, volume_analysis,
		closing_range compressed), fundamentals (earnings_acceleration,
		code33_status, earnings_surprise, estimate_revisions, forward_pe,
		margin_tracker, info), risk_assessment (sell_signals active only,
		stock_character, risk_gate with stop_loss/risk_reward_ratio/
		risk_reward_thresholds/position_sizing), metadata (missing_components
		as list, modules_run, execution_time_seconds).

	For screen:
		dict with candidates (list sorted by screen_score with ticker,
		rs_score, tt_score_pct, eps/sales/margin acceleration flags,
		code33_accel_count, screen_score), thresholds, metadata
		(total_screened, tt_pass_count, qualified_count, preset,
		execution_time_seconds).

	For market-leaders:
		dict with market_verdict (bull_early/bull_late/correction/bear),
		verdict_evidence (new_highs_vs_lows, distribution_days_25d,
		leader_stocks_breaking), breadth (new_highs, new_lows, ratio,
		detail), distribution_days_25d, sector_leaders, thresholds
		(verdict_rules), metadata.

	For compare:
		dict with comparison (list sorted by sepa_score with ticker, sepa_score,
		classification, hard_gate_fail, current_stage, tt_pass, rs_score,
		base_number, vcp_detected, pattern_quality, eps/sales_accelerating,
		character_grade, risk_reward_ratio, sector, industry), ranked_by,
		thresholds, metadata.

	For recheck:
		dict with ticker, verdict (HOLD/REDUCE/SELL), reasons, position
		(entry_price, entry_date, current_price, gain_loss_pct,
		days_since_entry), post_breakout (behavior, signal, squat_detected,
		above_20ma, failure_reset), current_status (stage, tt_pass,
		tt_score_pct, rs_score, sell_signals active only, sell_severity),
		volume_analysis (compressed: grade, weighted_ratio_50d,
		cluster_warning, breakout_volume_confirmation), metadata
		(missing_components as list).

Example:
	>>> python -m pipelines.minervini analyze NVDA
	{"ticker": "NVDA", "sepa_score": {"sepa_score": 72, "classification": "actionable", ...}, ...}

	>>> python -m pipelines.minervini screen --preset minervini_leaders
	{"candidates": [...], "thresholds": "...", "metadata": {"total_screened": 50, ...}}

	>>> python -m pipelines.minervini market-leaders
	{"market_verdict": "bull_early", "verdict_evidence": {...}, "breadth": {...}, ...}

	>>> python -m pipelines.minervini compare NVDA PLTR CRWD
	{"comparison": [...], "ranked_by": "sepa_score", ...}

	>>> python -m pipelines.minervini recheck NVDA --entry-price 120 --entry-date 2026-01-15
	{"ticker": "NVDA", "verdict": "HOLD", "reasons": [...], ...}

Use Cases:
	- Full SEPA due diligence for any ticker
	- Preset-based screening with automatic Trend Template + Code 33 filtering
	- Market environment assessment for exposure sizing
	- Side-by-side comparison of SEPA candidates
	- Post-entry position monitoring with disciplined sell rules

Notes:
	- Pipeline-Complete: all methodology-required module calls are contained within subcommands
	- SEPA score hard gates: Stage 2 + Trend Template 8/8 must pass
	- SEPA score dimensions: Trend Quality (25) + Fundamental Strength (25) + Setup Readiness (25) + Risk Profile (25)
	- Dimensions computed even on hard_gate_fail (informational only)
	- Graceful degradation: analysis continues with available data when modules fail
	- SEPA score marked "provisional" if >2 modules failed
	- Scripts execute in parallel via ThreadPoolExecutor for speed
	- Screen uses finviz presets (minervini_leaders default) with TT filter pass-through
	- Market leaders verdict uses new highs/lows ratio + distribution day count + leader breaking status
	- Compare runs full analysis per ticker in parallel
	- Recheck integrates post_breakout.monitor with sell_signals for hold/sell decision
	- All outputs self-documenting with thresholds fields (Section 2.8)
	- Module outputs stripped of symbol/date/current_price duplicates
	- Sell signals canonical location: risk_assessment.sell_signals (active only)
	- RS ranking canonical location: trend_qualification.rs_detail
	- Data compression: tight_closes (3 recent), pocket_pivot (summary), closing_range (ratios only)
"""

import argparse
import os
import sys

# Ensure scripts/ is on sys.path for utils import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from pipelines.minervini._commands import (
	cmd_analyze, cmd_screen, cmd_market_leaders, cmd_compare, cmd_recheck,
)


def main():
	parser = argparse.ArgumentParser(
		description="Minervini SEPA Pipeline: Composite Scoring & Risk Assessment"
	)
	sub = parser.add_subparsers(dest="command", required=True)

	# analyze
	sp_analyze = sub.add_parser("analyze", help="Full SEPA analysis for a ticker")
	sp_analyze.add_argument("ticker", help="Stock ticker symbol")
	sp_analyze.set_defaults(func=cmd_analyze)

	# screen
	sp_screen = sub.add_parser("screen", help="Screen for SEPA candidates")
	sp_screen.add_argument("--preset", default="minervini_leaders",
						   help="Finviz preset name (default: minervini_leaders)")
	sp_screen.add_argument("--sector", default=None, help="Screen within sector")
	sp_screen.add_argument("--industry", default=None, help="Screen within industry")
	sp_screen.add_argument("--limit", type=int, default=50, help="Max results")
	sp_screen.set_defaults(func=cmd_screen)

	# market-leaders
	sp_leaders = sub.add_parser("market-leaders", help="Market leadership assessment")
	sp_leaders.set_defaults(func=cmd_market_leaders)

	# compare
	sp_compare = sub.add_parser("compare", help="Compare tickers on SEPA criteria")
	sp_compare.add_argument("tickers", nargs="+", help="Ticker symbols to compare")
	sp_compare.set_defaults(func=cmd_compare)

	# recheck
	sp_recheck = sub.add_parser("recheck", help="Recheck existing position")
	sp_recheck.add_argument("ticker", help="Stock ticker symbol")
	sp_recheck.add_argument("--entry-price", type=float, required=True,
							help="Position entry price")
	sp_recheck.add_argument("--entry-date", required=True,
							help="Entry date YYYY-MM-DD")
	sp_recheck.add_argument("--stop-loss", type=float, default=7.0,
							help="Stop-loss percentage (default: 7.0)")
	sp_recheck.set_defaults(func=cmd_recheck)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
