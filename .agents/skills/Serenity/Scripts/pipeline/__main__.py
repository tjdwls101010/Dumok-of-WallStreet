#!/usr/bin/env python3
"""Serenity Pipeline v5.8.1 (Pipeline-Complete): 6-Level analytical hierarchy
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
Supports --industry (finviz industry-screen) and --sector (finviz sector-screen).

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
	discover: Candidate comparator (takes ticker list, runs 22 quantitative
		metrics on each in parallel, returns comparison table for agent to
		select analyze candidates)

Args:
	For macro:
		--extended (bool): Include raw DXY and BDI data (default: false)

	For analyze:
		ticker (str): Stock ticker symbol
		--skip-macro (bool): Skip Level 1 macro assessment (default: false)

	For discover:
		tickers (str[]): Ticker symbols to compare (2-30 tickers)

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
		growth_profile (compressed: status flags + 3 recent growth rates),
		sbc_analyzer, forward_pe, debt_structure,
		institutional_quality, no_growth_valuation, margin_tracker,
		iv_context, revenue_trajectory (8-quarter actual revenue).
		L5_catalysts: earnings (merged: next_report + surprise_history with
		nested eps{estimate,actual,surprise_pct,beat,yoy_pct,qoq_pct} and
		revenue{actual,yoy_pct,qoq_pct} sub-objects per quarter, max 8 quarters,
		consecutive_beats, avg_surprise_pct, cockroach_effect),
		analyst_consensus (row-oriented recommendations),
		analyst_price_targets,
		analyst_revisions (by_horizon with nested eps{current,7d_ago,30d_ago,
		90d_ago,low,high,yoy_pct,up_7d,down_7d,up_30d,down_30d} and
		revenue{avg,low,high,yoy_pct} sub-objects per horizon 0q/+1q/0y/+1y,
		trend_direction, net_revisions_7d/30d).
		L3_bottleneck: sec_supply_chain (suppliers, customers,
		single_source_dependencies, geographic_concentration,
		capacity_constraints, supply_chain_risks — trimmed for context),
		sec_events (recent 8-K supply chain events),
		sec_status (SEC_SC_available/partial/unavailable),
		absence_evidence_flags (list of absence type signals),
		bottleneck_pre_score.sole_western_flag (bool).
		L2: cascade_requires_context (agent-driven). L6: requires_llm.

	For discover:
		dict with candidates (list of dicts with 22 fields per ticker),
		thresholds (field interpretation guide), missing_data (fields
		that failed to collect per ticker), metadata (total_candidates,
		execution_time_seconds).

Example:
	>>> python -m pipelines.serenity macro --extended
	{"regime": "risk_on", "risk_level": "moderate", "signals": {...}, ...}

	>>> python -m pipelines.serenity analyze NBIS
	{"ticker": "NBIS", "levels": {"L1_macro": {"regime": ..., "signals": {...}}, ...}, ...}

	>>> python -m pipelines.serenity discover NVDA AAPL MSFT
	{"candidates": [...], "thresholds": {...}, ...}

Use Cases:
	- Full due diligence automation for any ticker in any sector
	- Macro regime assessment before position entry
	- Evidence chain completeness check for conviction assignment
	- Multi-ticker comparison via analyze × N with verdict.causal_bridge
	- Sector/industry discovery for bottleneck candidates
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
	- L1 output contains extracted signals (9 scalars + DXY/BDI when --extended)
	- L4 info uses get-info-fields with 24 essential fields (not full 100+ field info object)
	- L4 insider_transactions: 12-month lookback, summarized (buy/sell aggregates + net_direction + recent 20)
	- L4 revenue_trajectory: extracted from quarterly income statement (8 quarters, TotalRevenue only)
	- L5 earnings_calendar removed (was market-wide, not ticker-specific; earnings_dates covers ticker)
	- L4 holders summarized to top 5 with key fields + total count
	- L4 growth_profile compressed to status flags + 3 most recent growth rates
	- L5 earnings_dates capped at 8 most recent (2 years quarterly)
	- Yield curve limited to 5 observations, net liquidity to 10 observations
"""

import argparse
import os
import sys

# Ensure Scripts/ is on sys.path for module imports
_scripts_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, _scripts_dir)
# Also add modules/ for utils import
sys.path.insert(0, os.path.join(_scripts_dir, "modules"))

from pipeline._commands import cmd_macro, cmd_analyze


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

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
