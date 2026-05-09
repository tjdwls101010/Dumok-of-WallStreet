#!/usr/bin/env python3
"""Minervini SEPA Pipeline v1.4.0 (Pipeline-Complete): SEPA analysis with
composite scoring, risk assessment, signal synthesis, and market discovery.

Orchestrates the complete Minervini SEPA (Specific Entry Point Analysis) by
running trend qualification, technical setup, fundamental validation, and risk
assessment modules in parallel. Pipeline-Complete -- all methodology-required
module calls are contained within the pipeline; do not call individual modules
to supplement.

SEPA composite score (0-100) across 4 dimensions (25 pts each): Trend Quality,
Fundamental Strength, Setup Readiness, Risk Profile. Hard gates: Stage 2 + Trend
Template 8/8 must pass or stock is classified "avoid". Dimensions are always
computed (even on hard_gate_fail) for informational purposes.

Output structure (analyze): ticker, signal (action + sepa_score + classification
+ hard_gates), trend (trend_template, stage_analysis, rs_detail, base_count),
fundamentals (earnings, valuation, margins), setup (vcp, entry_patterns,
institutional_demand, tight_closes, volume_analysis), risk (sell_signals,
stock_character, risk_gate), company, metadata.

stage_analysis output: stage (int), scores (non-zero only), evidences (11 fields
with value + unit + thresholds for full score traceability), max_scores dict.

trend_template output (compressed): passed "N/8", criteria (id, passed, value,
threshold — no description/moving_averages/week52/passed_count/total_count/
overall_pass/score_pct).

Commands:
	analyze: Full SEPA analysis for a single ticker (~18 modules in parallel,
		SEPA composite score 0-100, risk assessment with R:R/position sizing,
		unified entry/exit signals, output grouped as signal, trend,
		fundamentals, setup, risk, company, metadata). Module outputs
		stripped of symbol/date/current_price (top-level ticker is canonical).
		RS ranking integrated as rs_detail in trend. Sell signals canonical
		in risk (active only).
	discover: Market environment + RS leader discovery (market_breadth
		homepage scrape, SPY distribution day count, ibd-rs-rating
		sector_ranking + industry_ranking + industry_top + movers +
		reference + top 20 -> market verdict with breadth + RS-based
		sector/industry rankings and leadership dashboard, ~3s)

Args:
	For analyze:
		ticker (str): Stock ticker symbol

	For discover:
		No required args.

Returns:
	For analyze:
		dict with ticker, signal (action BUY_READY/WATCH/HOLD/REDUCE/SELL,
		sepa_score 0-100, classification, hard_gate_fail, hard_gates,
		entry_signals, exit_signals, volume_confirmation, reasons,
		thresholds),
		trend (dimension_score, trend_template compressed with passed "N/8",
		stage_analysis with stage/scores/evidences/max_scores, rs_detail
		with rs_rating/spy_rs/history, base_count with base_history/
		cross_base_analysis/risk_level),
		fundamentals (dimension_score, earnings with eps_history 8 quarters
		qoq+yoy+surprise / sales_history / acceleration with code33_status /
		forward_growth / revision_breadth, valuation with forward_pe/
		peg_ratio, margins with trajectory 3 quarters + flag),
		setup (dimension_score, vcp with contractions_detail/shakeout/
		volume/pivot_tightness/setup_readiness, entry_patterns,
		institutional_demand, tight_closes max 3 clusters, volume_analysis),
		risk (dimension_score, sell_signals active only with severity,
		stock_character with adr/character_grade, risk_gate with
		risk_reward_ratio/position_sizing),
		company (sector, industry, marketCap, currentPrice, beta,
		sharesOutstanding, floatShares, shortPercentOfFloat),
		metadata (next_earnings_date, missing_components, modules_run,
		execution_time_seconds).

	For discover:
		dict with market_verdict (bull_early/bull_late/correction/bear),
		verdict_evidence (new_highs_vs_lows, distribution_days_25d),
		breadth (new_highs, new_lows, detail with advancing_declining/
		new_high_low/sma50/sma200 each with pct+count),
		rs_leaders (spy_rs, qqq_rs, top_20 with ticker/rs_rating/rs_raw,
		movers_5d with ticker/rs_rating/prev_rating/change),
		sector_ranking (sector/avg_rs/count/rank sorted by avg_rs),
		leadership_dashboard (industry/sector/avg_rs/leader_count/
		leader_tickers/leadership_rank sorted by avg_rs, top 15
		industries enriched with leader_tickers via industry_top),
		thresholds (verdict_rules), metadata (execution_time_seconds).

Example:
	>>> python -m pipelines.minervini analyze NVDA
	{"ticker": "NVDA", "signal": {"action": "BUY_READY", "sepa_score": 72, ...}, ...}

	>>> python -m pipelines.minervini discover
	{"market_verdict": "bull_early", "rs_leaders": {...}, "sector_leaders": {...}, ...}

Use Cases:
	- Full SEPA due diligence for any ticker
	- Market environment assessment for exposure sizing
	- RS leader identification for candidate discovery

Notes:
	- Pipeline-Complete: all methodology-required module calls are contained within subcommands
	- SEPA score hard gates: Stage 2 + Trend Template 8/8 must pass
	- SEPA score dimensions: Trend Quality (25) + Fundamental Strength (25) + Setup Readiness (25) + Risk Profile (25)
	- Dimensions computed even on hard_gate_fail (informational only)
	- Graceful degradation: analysis continues with available data when modules fail
	- SEPA score marked "provisional" if >2 modules failed
	- Scripts execute in parallel via ThreadPoolExecutor for speed
	- stage_analysis: factor-based scoring (Ch.5), 11 evidences with value+unit+thresholds, max S1:80|S2:95|S3:90|S4:100
	- trend_template: compressed to passed "N/8" + criteria without description/moving_averages/week52
	- Discover uses market_breadth homepage scrape + SPY volume + ibd-rs-rating (sector/industry rankings, top, movers)
	- All outputs self-documenting with thresholds dicts (Section 2.8)
	- Module outputs stripped of symbol/date/current_price duplicates
	- Sell signals canonical location: risk.sell_signals (active only)
	- RS ranking canonical location: trend.rs_detail (ibd-rs-rating library)
	- Data compression: tight_closes (3 recent), institutional_demand (summary)
	- Earnings: eps_history 8 quarters with qoq+yoy+surprise, estimate_revisions raw for revision_breadth
	- Valuation: forward_pe + peg_ratio (forward P/E / EPS growth rate)
	- Margins: trajectory 3 quarters with qoq changes, flag (EXPANDING/STABLE/COMPRESSION/COLLAPSE)
"""

import argparse
import os
import sys

# Ensure Scripts/ is on sys.path for module imports
_scripts_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, _scripts_dir)
sys.path.insert(0, os.path.join(_scripts_dir, "modules"))

from pipeline._commands import cmd_analyze, cmd_discover


def main():
	parser = argparse.ArgumentParser(
		description="Minervini SEPA Pipeline: Composite Scoring & Risk Assessment"
	)
	sub = parser.add_subparsers(dest="command", required=True)

	# analyze — Full SEPA analysis for a single ticker
	sp_analyze = sub.add_parser("analyze", help="Full SEPA analysis for a ticker")
	sp_analyze.add_argument("ticker", help="Stock ticker symbol")
	sp_analyze.set_defaults(func=cmd_analyze)

	# discover — Market environment + RS leaders
	sp_discover = sub.add_parser("discover", help="Market environment + RS leader discovery")
	sp_discover.set_defaults(func=cmd_discover)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
