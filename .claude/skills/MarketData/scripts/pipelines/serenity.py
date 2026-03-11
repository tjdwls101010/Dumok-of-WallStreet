#!/usr/bin/env python3
"""Serenity Pipeline v5.3.1 (Pipeline-Complete): 6-Level analytical hierarchy
automating supply chain bottleneck analysis with macro regime assessment,
fundamental validation, composite signal generation, control layer outputs,
and evidence chain verification.

Orchestrates the complete Serenity analysis by running macro regime scripts,
fundamental analysis tools, valuation models, and catalyst monitoring in
parallel. Pipeline-Complete — all methodology-required module calls are contained
within the pipeline; do not call individual modules to supplement.

L1 macro includes BDI/DXY/real rates always-on; L2 includes hyperscaler CapEx
bridge signal; L3 includes SEC supply chain pre-extraction with 6-Criteria
pre-scoring, absence evidence flags, and sole_western_flag; L4 includes
health gate severity spectrum (PASS/CAUTION/FLAG) with 5 gates (bear_bull,
dilution, no_growth, margin, io_quality), thesis validation signals, SoP
trigger detection, and trapped asset override; L6 includes rule-based
auto-classification. Composite signal generation produces integrated
investment grades with position sizing guidance. Valuation summary includes
dual_valuation (no-growth floor + growth upside).

Control layer outputs (analyze): materiality_signals (supply chain exposure,
margin sensitivity, earnings materiality, SEC events), causal_bridge_data
(macro→supply chain→financials→valuation pre-filled chain),
priced_in_assessment (8-signal composite score 0-100 + 3-tier verdict),
institutional_flow (insider direction, IO quality, IV signal, flow assessment),
expression_layer (IV regime × conviction → recommended vehicle).

Discover includes lightweight macro stress check (VIX, Fear&Greed, net
liquidity) with stress/euphoria detection and discovery workflow guidance note.
Recheck includes rotation_assessment (forward PE risk, no-growth check,
opportunity cost flag, MAINTAIN_BUT_SCAN verdict).

Commands:
	macro: Level 1 macro regime assessment (10 parallel macro scripts → regime
		classification as risk_on/risk_off/transitional with drain counting.
		BDI/DXY z-scores and real rates always included.
		ERP extracted via erp.current.erp, Fear&Greed via fear_greed.current.score)
	analyze: Full 6-Level analysis for a single ticker (L1 macro + L2 hyperscaler
		CapEx bridge + L3 SEC supply chain pre-scoring + L4 fundamentals with
		health gate severity spectrum + thesis signals + SoP triggers +
		trapped asset override + L5 catalysts + L6 auto-classification +
		composite signal with position sizing + control layer:
		materiality_signals, causal_bridge_data, priced_in_assessment,
		institutional_flow, expression_layer)
	recheck: Position monitoring recheck (macro regime + health gates + thesis
		signals + rotation_assessment against existing position with action
		signals and verdict including MAINTAIN_BUT_SCAN)
	discover: Automated theme discovery (lightweight macro stress check +
		sector_leaders + finviz cross-reference + bottleneck_scorer validation,
		grouped by industry theme, with macro_context and discovery workflow note)
	cross-chain: Shared supplier detection across multiple tickers via SEC
		supply chain entity normalization and cross-matching, with
		bottleneck_signal scoring (supplier_ref_pct, single_source_count,
		assessment) for each shared entity
	compare: Multi-ticker side-by-side comparison (12 metrics including asymmetry_score)
	screen: Sector-based bottleneck candidate screening
	capex-cascade: Supply chain CapEx cascade tracking across multiple tickers

Args:
	For macro:
		--extended (bool): Include raw DXY and BDI data (default: false)

	For analyze:
		ticker (str): Stock ticker symbol
		--skip-macro (bool): Skip Level 1 macro assessment (default: false)

	For recheck:
		ticker (str): Stock ticker symbol
		--entry-price (str): Entry price for position (required)
		--entry-date (str): Entry date YYYY-MM-DD (informational, optional)

	For discover:
		--top-groups (int): Number of top industry groups (default: 5)
		--max-mcap (str): Maximum market cap filter (default: "10B")
		--limit (int): Maximum candidates per theme (default: 10)
		--industry (str): Direct industry search — skips sector_leaders, goes
			straight to finviz industry-screen (default: None)
		--skip-macro (bool): Skip lightweight macro stress check (default: false)

	For cross-chain:
		tickers (list): 2+ stock ticker symbols
		--form (str): SEC filing form type (default: "10-K")

	For compare:
		tickers (list): 2+ stock ticker symbols

	For screen:
		sector (str): Sector name for Finviz screening
		--max-mcap (str): Maximum market cap filter, applied post-screen (default: "10B")

	For capex-cascade:
		tickers (list): 2+ stock ticker symbols for CapEx cascade tracking

Returns:
	For macro:
		dict with regime (str: risk_on/risk_off/transitional),
		risk_level (str: low/moderate/elevated/high),
		drain_count (int), decision_rules (list[str] with actual values),
		signals (dict with erp_pct, vix_spot, vix_regime, vix_structure,
		net_liq_direction, net_liq_current, fear_greed,
		fedwatch_next_meeting, fedwatch_probabilities,
		bdi_z_score, bdi_demand, dxy_z_score, dxy_strength, real_rate;
		when --extended: dxy (raw DXY data), bdi (raw BDI data))

	For analyze:
		dict with ticker, levels (L1_macro through L6_taxonomy),
		materiality_signals (supply_chain_exposure, margin_sensitivity,
		earnings_materiality, recent_sec_events, exposure_summary),
		causal_bridge_data (macro_context, supply_chain_position,
		financial_transmission, valuation_gap),
		priced_in_assessment (signals with 8 fields, risk_score 0-100,
		assessment: fully_priced_in/partially_priced_in/not_priced_in),
		institutional_flow (insider_net_direction, io_quality_score,
		iv_percentile, flow_assessment: positive/negative/neutral),
		expression_layer (iv_percentile, iv_regime, recommended_vehicle:
		shares/leaps/csp/covered_calls, reasoning),
		health_gates (with severity spectrum), thesis_signals,
		sop_triggers, trapped_asset_override, composite_signal
		(with grade, score_breakdown, position_guidance),
		health_gates (bear_bull_paradox, active_dilution, no_growth_fail,
		margin_collapse, io_quality_concern — each PASS/CAUTION/FLAG),
		valuation_summary (includes dual_valuation: no_growth_floor + growth_upside),
		fundamental_readiness_codes (list of standardized audit codes).
		L1_macro: regime classification + signals dict (no raw data).
		L2_capex_flow: company_capex (8-quarter trend auto-included),
		cascade_requires_context (agent-driven supply chain layers).
		L4_fundamentals: info (24 essential fields),
		holders (top 5 summary with total count),
		insider_transactions (summary + recent 20, 12-month lookback),
		earnings_acceleration (compressed: status flags + 3 recent growth rates),
		sbc_analyzer, forward_pe, debt_structure,
		institutional_quality, no_growth_valuation, margin_tracker,
		iv_context, revenue_trajectory (8-quarter actual revenue).
		L5_catalysts: earnings_dates (capped at 8 most recent),
		earnings_surprise (post-ER reaction),
		analyst_recommendations, analyst_price_targets, analyst_revisions.
		L3_bottleneck: sec_supply_chain (suppliers, customers,
		single_source_dependencies, geographic_concentration,
		capacity_constraints, supply_chain_risks — trimmed for context),
		sec_events (recent 8-K supply chain events),
		sec_status (SEC_SC_available/partial/unavailable),
		absence_evidence_flags (list of absence type signals),
		bottleneck_pre_score.sole_western_flag (bool).
		L2: cascade_requires_context (agent-driven). L6: requires_llm.

	For recheck:
		dict with ticker, entry_price, current_price, return_pct,
		position_52w, macro_regime, health_gates, thesis_signals,
		rotation_assessment (forward_pe, no_growth_upside_pct,
		return_since_entry_pct, rotation_flags, opportunity_cost_elevated,
		suggestion: scan_alternatives/consider_trim/maintain),
		action_signals, verdict (MAINTAIN/MAINTAIN_BUT_SCAN/HOLD_MONITOR/
		HOLD_REDUCE/CONSIDER_EXIT), note.

	For discover:
		dict with macro_context (vix_regime, fear_greed, net_liq_direction,
		stress_note — skipped when --skip-macro), themes (list of
		industry_group with candidates sorted by asymmetry_score),
		total_themes, total_candidates, filters_applied,
		requires_agent_review, discovery_workflow_note.

	For cross-chain:
		dict with tickers, shared_supplier_nodes (list of shared entities
		with bottleneck_signal: supplier_ref_count, supplier_ref_pct,
		single_source_count, assessment, thresholds, interpretation),
		per_ticker_suppliers (per-ticker supplier_count, total_entities,
		unique_to_ticker), supply_chain_overlap_pct,
		total_unique_entities, shared_entity_count, note.

	For compare:
		dict with tickers, comparative_table (forward_pe,
		no_growth_upside_pct, margin_status, io_quality_score,
		debt_quality_grade, market_cap, revenue_growth_yoy,
		short_interest_pct, 52w_range_position, sbc_flag,
		consecutive_beats, asymmetry_score per ticker),
		health_gates, relative_strengths.

	For screen:
		dict with sector, candidates_screened (int),
		results (list sorted by asymmetry_score desc).

	For capex-cascade:
		dict with tickers, capex_trends (per-ticker 8Q CapEx with
		QoQ/YoY direction and acceleration), cascade_summary (overall
		cascade health and upstream→downstream consistency),
		hyperscaler_signal (aggregate hyperscaler CapEx direction if
		applicable).

Example:
	>>> python serenity.py macro --extended
	{"regime": "risk_on", "risk_level": "moderate", "signals": {...}, ...}

	>>> python serenity.py analyze NBIS
	{"ticker": "NBIS", "levels": {"L1_macro": {"regime": ..., "signals": {...}}, "L2_capex_flow": {"company_capex": {...}, ...}, "L4_fundamentals": {"info": {...}, "insider_transactions": {"summary": {...}, "transactions": [...]}, "revenue_trajectory": {...}, ...}, "L5_catalysts": {"earnings_surprise": {...}, "analyst_recommendations": {...}, ...}}, "health_gates": {...}, ...}

	>>> python serenity.py analyze NBIS --skip-macro
	{"ticker": "NBIS", "levels": {"L1_macro": {"skipped": true}, ...}, ...}

	>>> python serenity.py compare AXTI AEHR FORM
	{"tickers": [...], "comparative_table": {"forward_pe": {...}, "market_cap": {...}, "revenue_growth_yoy": {...}, ...}, ...}

	>>> python serenity.py screen "Defense" --max-mcap 5B
	{"sector": "Defense", "candidates_screened": 10, ...}

Use Cases:
	- Full due diligence automation for any ticker in any sector
	- Macro regime assessment before position entry
	- Evidence chain completeness check for conviction assignment
	- Multi-ticker comparison within a supply chain
	- Sector screening for bottleneck candidates
	- Sector-agnostic: works for defense, EV, agriculture, semiconductors, etc.

Notes:
	- Pipeline-Complete: all methodology-required module calls are contained within subcommands
	- L1 macro and L4-L6 fundamentals auto-execute for any ticker
	- L2 company CapEx auto-included (8-quarter trend); supply chain cascade requires agent context
	- L3 (Bottleneck) returns requires_context for agent-driven analysis
	- Health gates are extracted from L4 script outputs (debt, dilution, valuation, margin)
	- Conditional SEC filing check when active_dilution detected (S-3 form lookup)
	- fundamental_readiness_codes provide audit trail of automated assessment
	- Scripts execute in parallel via ThreadPoolExecutor for speed
	- Pipeline continues even if individual scripts fail (graceful degradation)
	- screen subcommand depends on finviz.py and bottleneck_scorer.py; --max-mcap applied as post-filter
	- L1 output contains extracted signals (9 scalars + DXY/BDI when --extended)
	- L4 info uses get-info-fields with 24 essential fields (not full 100+ field info object)
	- L4 insider_transactions: 12-month lookback, summarized (buy/sell aggregates + net_direction + recent 20)
	- L4 revenue_trajectory: extracted from quarterly income statement (8 quarters, TotalRevenue only)
	- L5 earnings_calendar removed (was market-wide, not ticker-specific; earnings_dates covers ticker)
	- compare uses get-info-fields (5 fields) instead of get-info (100+ fields)
	- compare includes sbc_analyzer (SBC health flag) and earnings_surprise (consecutive beats) for filtering
	- compare uses forward_pe (analyst consensus) for revenue_growth_yoy
	- compare includes asymmetry_score via bottleneck_scorer.py validate per ticker (12 metrics total)
	- capex-cascade tracks 8Q CapEx via capex_tracker.py track per ticker, with cascade health summary
	- L4 holders summarized to top 5 with key fields + total count
	- L4 earnings_acceleration compressed to status flags + 3 most recent growth rates
	- L5 earnings_dates capped at 8 most recent (2 years quarterly)
	- Yield curve limited to 5 observations, net liquidity to 10 observations
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from serenity._commands import (
	cmd_macro, cmd_analyze, cmd_recheck, cmd_discover,
	cmd_cross_chain, cmd_compare, cmd_screen, cmd_capex_cascade,
)


def main():
	parser = argparse.ArgumentParser(
		description="Serenity Pipeline: 6-Level Analytical Hierarchy"
	)
	sub = parser.add_subparsers(dest="command", required=True)

	# macro
	sp_macro = sub.add_parser("macro", help="Level 1 macro regime assessment")
	sp_macro.add_argument(
		"--extended",
		action="store_true",
		default=False,
		help="Include raw DXY and BDI data in output",
	)
	sp_macro.set_defaults(func=cmd_macro)

	# analyze
	sp_analyze = sub.add_parser("analyze", help="Full 6-Level analysis for a ticker")
	sp_analyze.add_argument("ticker", help="Stock ticker symbol")
	sp_analyze.add_argument(
		"--skip-macro",
		action="store_true",
		default=False,
		help="Skip Level 1 macro assessment",
	)
	sp_analyze.set_defaults(func=cmd_analyze)

	# compare
	sp_compare = sub.add_parser(
		"compare", help="Multi-ticker side-by-side comparison"
	)
	sp_compare.add_argument(
		"tickers", nargs="+", help="2 or more stock ticker symbols"
	)
	sp_compare.set_defaults(func=cmd_compare)

	# screen
	sp_screen = sub.add_parser(
		"screen", help="Sector-based bottleneck candidate screening"
	)
	sp_screen.add_argument("sector", help="Sector name for Finviz screening")
	sp_screen.add_argument(
		"--max-mcap",
		default="10B",
		help="Maximum market cap filter (default: 10B)",
	)
	sp_screen.set_defaults(func=cmd_screen)

	# capex-cascade
	sp_capex = sub.add_parser(
		"capex-cascade", help="Supply chain CapEx cascade tracking"
	)
	sp_capex.add_argument(
		"tickers", nargs="+", help="2 or more stock ticker symbols"
	)
	sp_capex.set_defaults(func=cmd_capex_cascade)

	# recheck
	sp_recheck = sub.add_parser(
		"recheck", help="Position monitoring recheck"
	)
	sp_recheck.add_argument("ticker", help="Stock ticker symbol")
	sp_recheck.add_argument(
		"--entry-price", required=True, help="Entry price for position"
	)
	sp_recheck.add_argument(
		"--entry-date", default=None, help="Entry date (YYYY-MM-DD, informational)"
	)
	sp_recheck.set_defaults(func=cmd_recheck)

	# discover
	sp_discover = sub.add_parser(
		"discover", help="Automated theme discovery with bottleneck candidates"
	)
	sp_discover.add_argument(
		"--top-groups", type=int, default=5,
		help="Number of top industry groups to surface (default: 5)",
	)
	sp_discover.add_argument(
		"--max-mcap", default="10B",
		help="Maximum market cap filter (default: 10B)",
	)
	sp_discover.add_argument(
		"--limit", type=int, default=10,
		help="Maximum candidates per theme (default: 10)",
	)
	sp_discover.add_argument(
		"--industry", default=None,
		help="Direct industry search (skips sector_leaders). Partial name match supported.",
	)
	sp_discover.add_argument(
		"--skip-macro", action="store_true", default=False,
		help="Skip lightweight macro stress check (default: false)",
	)
	sp_discover.set_defaults(func=cmd_discover)

	# cross-chain
	sp_cross = sub.add_parser(
		"cross-chain", help="Shared supplier detection across tickers"
	)
	sp_cross.add_argument(
		"tickers", nargs="+", help="2 or more stock ticker symbols"
	)
	sp_cross.add_argument(
		"--form", default="10-K", help="SEC filing form type (default: 10-K, auto-fallback to 20-F)"
	)
	sp_cross.set_defaults(func=cmd_cross_chain)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
