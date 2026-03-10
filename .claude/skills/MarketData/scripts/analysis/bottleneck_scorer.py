#!/usr/bin/env python3
"""Bottleneck Scorer: Sector-agnostic financial validation of supply chain bottleneck candidates.

After qualitative bottleneck identification (LLM+WebSearch), this script automates the
quantitative financial validation. Runs health gates, computes an asymmetry score, and
ranks candidates by supply dominance. Works for ANY sector's bottleneck candidates.

Commands:
	validate: Financial validation suite for a single bottleneck candidate
	batch: Batch validation for multiple candidates sorted by asymmetry score
	rank: Priority ranking using Supply Dominance formula

Args:
	For validate:
		ticker (str): Stock ticker symbol
		--bottleneck-score (int): Qualitative bottleneck score 1-6 from agent assessment (default: 5)
		--nested-bottleneck (flag): This candidate is a nested bottleneck (bottleneck's bottleneck)
		--sole-western (flag): This candidate is the sole Western alternative supplier

	For batch:
		tickers (list): Stock ticker symbols
		--bottleneck-scores (str): Comma-separated bottleneck scores matching ticker order (default: all 5)
		--nested-bottleneck (str): Comma-separated boolean flags (true/false) for nested bottleneck per ticker
		--sole-western (str): Comma-separated boolean flags (true/false) for sole Western per ticker

	For rank:
		tickers (list): Stock ticker symbols
		--bottleneck-scores (str): Required. Comma-separated bottleneck scores matching ticker order
		--nested-bottleneck (str): Comma-separated boolean flags (true/false) for nested bottleneck per ticker
		--sole-western (str): Comma-separated boolean flags (true/false) for sole Western per ticker

Returns:
	dict: {
		"ticker": str,
		"health_gates": {
			"bear_bull_paradox": "PASS" | "FLAG",
			"active_dilution": "PASS" | "FLAG",
			"no_growth_fail": "PASS" | "FLAG",
			"margin_collapse": "PASS" | "FLAG"
		},
		"financial_validation": {
			"debt_to_equity": float,
			"interest_coverage": float,
			"sbc_pct_revenue": float,
			"shares_change_qoq_pct": float,
			"no_growth_value": float,
			"forward_pe": float,
			"peg_ratio": float,
			"io_pct": float,
			"gross_margin": float,
			"operating_margin": float,
			"margin_trend": str
		},
		"asymmetry_score": float,
		"nested_bottleneck_detected": bool,
		"sole_western_alternative": bool,
		"composite": {
			"health_gate_passes": int,
			"health_gate_total": 4,
			"flags": [str]
		}
	}

Example:
	>>> python bottleneck_scorer.py validate NBIS --bottleneck-score 5
	{...}

	>>> python bottleneck_scorer.py validate NBIS --bottleneck-score 5 --nested-bottleneck --sole-western
	{...}

	>>> python bottleneck_scorer.py batch NBIS AXTI LPTH --bottleneck-scores "5,6,4"
	{...}

	>>> python bottleneck_scorer.py batch NBIS AXTI LPTH --bottleneck-scores "5,6,4" --nested-bottleneck "true,false,true"
	{...}

	>>> python bottleneck_scorer.py rank NBIS AXTI LPTH --bottleneck-scores "5,6,4"
	{...}

	>>> python bottleneck_scorer.py rank NBIS AXTI LPTH --bottleneck-scores "5,6,4" --sole-western "false,true,false"
	{...}

Use Cases:
	- Validate financial health of bottleneck candidates after qualitative screening
	- Compare asymmetry across supply chain chokepoint companies
	- Rank candidates by supply dominance and balance sheet quality
	- Filter out "great tech, bad balance sheet" traps (Bear-Bull Paradox)

Notes:
	- Health gates are binary PASS/FLAG; any FLAG reduces conviction
	- Asymmetry score combines financial health (40%), valuation upside (30%), bottleneck score (30%)
	- Nested bottleneck flag adds +5pts to asymmetry score (capped at 100)
	- Sole Western alternative flag adds +3pts to asymmetry score (capped at 100)
	- These flags are pass-through inputs from the pipeline/agent; the module does not detect them
	- Works for any sector: defense, EV, agriculture, semiconductors, etc.
	- Data comes entirely from yfinance; no sector-specific assumptions
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf

# Support both standalone execution and module imports
try:
	from ..utils import error_json, output_json, safe_run
except ImportError:
	from utils import error_json, output_json, safe_run

NO_GROWTH_PE = 15


# ---------------------------------------------------------------------------
# Private helpers: data extraction
# ---------------------------------------------------------------------------


def _safe_float(val):
	"""Convert a value to float, returning None if NaN or None."""
	if val is None:
		return None
	try:
		f = float(val)
		if f != f:  # NaN check
			return None
		return f
	except (ValueError, TypeError):
		return None


def _get_field(df, names):
	"""Try multiple row names to extract the most recent value from a financial statement."""
	if df is None or df.empty:
		return None
	col = df.columns[0]  # Most recent period
	for name in names:
		if name in df.index:
			val = df.loc[name, col]
			if val is not None and val == val:  # not NaN
				return val
	return None


def _get_field_col(df, col, names):
	"""Try multiple row names to extract a value from a specific column."""
	if df is None or df.empty:
		return None
	for name in names:
		if name in df.index:
			val = df.loc[name, col]
			if val is not None and val == val:
				return val
	return None


def _get_io_pct(ticker):
	"""Get institutional ownership percentage from ticker.info."""
	info = ticker.info or {}
	# yfinance provides heldPercentInstitutions as a decimal (0.0 - 1.0)
	held = info.get("heldPercentInstitutions")
	if held is not None:
		val = _safe_float(held)
		if val is not None:
			return round(val * 100, 2)
	return None


def _get_shares_change_qoq(ticker):
	"""Compute Q/Q share count change from quarterly balance sheet.

	Returns (change_pct, note) where note explains any fallback.
	"""
	try:
		qbs = ticker.quarterly_balance_sheet
		if qbs is None or qbs.empty:
			return None, "quarterly_balance_sheet_unavailable"
		for name in ["OrdinarySharesNumber", "ShareIssued", "CommonStockSharesOutstanding"]:
			if name in qbs.index and len(qbs.columns) >= 2:
				current = _safe_float(qbs.loc[name].iloc[0])
				prior = _safe_float(qbs.loc[name].iloc[1])
				if current is not None and prior is not None and prior > 0:
					change_pct = round((current - prior) / prior * 100, 2)
					return change_pct, None
	except Exception:
		pass
	return None, "shares_data_unavailable"


def _get_margin_trend(ticker):
	"""Determine operating margin trend from quarterly income statements.

	Returns (gross_margin, operating_margin, trend_label, yoy_change_pp).
	trend_label: "expanding" | "stable" | "compression" | "collapse" | "insufficient_data"
	"""
	try:
		stmt = ticker.get_income_stmt(freq="quarterly")
		if stmt is None or stmt.empty:
			return None, None, "insufficient_data", None

		cols = list(stmt.columns)

		# Latest quarter gross/operating margin
		latest_revenue = _get_field_col(stmt, cols[0], ["TotalRevenue", "Total Revenue", "Revenue"])
		latest_gross_profit = _get_field_col(stmt, cols[0], ["GrossProfit", "Gross Profit"])
		latest_op_income = _get_field_col(
			stmt, cols[0], ["OperatingIncome", "Operating Income", "EBIT"]
		)

		latest_revenue_f = _safe_float(latest_revenue)
		gross_margin = None
		operating_margin = None

		if latest_revenue_f and latest_revenue_f > 0:
			gp = _safe_float(latest_gross_profit)
			if gp is not None:
				gross_margin = round(gp / latest_revenue_f * 100, 2)
			oi = _safe_float(latest_op_income)
			if oi is not None:
				operating_margin = round(oi / latest_revenue_f * 100, 2)

		# Y/Y comparison (4 quarters back)
		yoy_change = None
		trend = "insufficient_data"
		if len(cols) >= 5:
			yoy_revenue = _safe_float(
				_get_field_col(stmt, cols[4], ["TotalRevenue", "Total Revenue", "Revenue"])
			)
			yoy_op_income = _safe_float(
				_get_field_col(
					stmt, cols[4], ["OperatingIncome", "Operating Income", "EBIT"]
				)
			)
			if yoy_revenue and yoy_revenue > 0 and yoy_op_income is not None:
				yoy_op_margin = yoy_op_income / yoy_revenue * 100
				if operating_margin is not None:
					yoy_change = round(operating_margin - yoy_op_margin, 2)
					if yoy_change > 5:
						trend = "expanding"
					elif yoy_change >= -2:
						trend = "stable"
					elif yoy_change >= -5:
						trend = "compression"
					else:
						trend = "collapse"

		return gross_margin, operating_margin, trend, yoy_change

	except Exception:
		return None, None, "insufficient_data", None


def _get_sbc_pct_revenue(ticker):
	"""Get SBC as a percentage of revenue."""
	try:
		cashflow = ticker.get_cashflow()
		income = ticker.get_income_stmt()

		sbc = None
		if cashflow is not None and not cashflow.empty and "StockBasedCompensation" in cashflow.index:
			sbc = _safe_float(cashflow.loc["StockBasedCompensation"].iloc[0])

		revenue = None
		if income is not None and not income.empty:
			for label in ["TotalRevenue", "Total Revenue", "Revenue"]:
				if label in income.index:
					revenue = _safe_float(income.loc[label].iloc[0])
					if revenue is not None:
						break

		if sbc is not None and revenue is not None and revenue > 0:
			return round(abs(sbc) / revenue * 100, 2)
	except Exception:
		pass
	return None


def _get_forward_pe_and_peg(ticker):
	"""Get forward P/E and PEG ratio from ticker info and earnings estimates."""
	info = ticker.info or {}

	forward_pe = _safe_float(info.get("forwardPE"))

	# PEG ratio from info
	peg_ratio = _safe_float(info.get("pegRatio"))

	# If forwardPE missing, try computing from earnings estimates
	if forward_pe is None:
		try:
			current_price = _safe_float(info.get("currentPrice"))
			if current_price is None:
				current_price = _safe_float(getattr(ticker.fast_info, "last_price", None))
			earnings_est = ticker.get_earnings_estimate()
			if (
				current_price is not None
				and earnings_est is not None
				and not earnings_est.empty
			):
				for period in ["+1y", "0y"]:
					if period in earnings_est.index and "avg" in earnings_est.columns:
						eps = _safe_float(earnings_est.loc[period, "avg"])
						if eps is not None and eps > 0:
							forward_pe = round(current_price / eps, 2)
							break
		except Exception:
			pass

	return forward_pe, peg_ratio


# ---------------------------------------------------------------------------
# Core: build full validation for a single ticker
# ---------------------------------------------------------------------------


def _build_validation(symbol, bottleneck_score, nested_bottleneck=False, sole_western=False):
	"""Build complete financial validation for a single bottleneck candidate."""
	ticker = yf.Ticker(symbol)
	info = ticker.info or {}

	market_cap = _safe_float(info.get("marketCap"))
	total_debt = _safe_float(info.get("totalDebt"))
	total_revenue = _safe_float(info.get("totalRevenue"))
	operating_margins = _safe_float(info.get("operatingMargins"))  # decimal

	# --- Bear-Bull Paradox ---
	# Interest coverage = operating income / interest expense
	interest_coverage = None
	try:
		inc = ticker.get_income_stmt()
		operating_income = _safe_float(
			_get_field(inc, ["EBIT", "OperatingIncome", "Operating Income"])
		)
		interest_expense = _safe_float(
			_get_field(
				inc,
				[
					"InterestExpense",
					"Interest Expense",
					"InterestExpenseNonOperating",
					"Interest Expense Non Operating",
				],
			)
		)
		if operating_income is not None and interest_expense is not None and interest_expense != 0:
			interest_coverage = round(operating_income / abs(interest_expense), 2)
	except Exception:
		pass

	debt_to_equity = _safe_float(info.get("debtToEquity"))
	# debtToEquity from yfinance is often as percentage (e.g. 150 = 1.5x), normalize
	if debt_to_equity is not None and debt_to_equity > 10:
		debt_to_equity = round(debt_to_equity / 100, 4)

	bear_bull_flag = False
	bear_bull_reason = None
	if total_debt is not None and market_cap is not None and market_cap > 0:
		if total_debt > 2 * market_cap:
			bear_bull_flag = True
			bear_bull_reason = f"total_debt ({total_debt:.0f}) > 2x market_cap ({market_cap:.0f})"
	if interest_coverage is not None and interest_coverage < 1.0:
		bear_bull_flag = True
		reason = f"interest_coverage ({interest_coverage}) < 1.0"
		bear_bull_reason = reason if bear_bull_reason is None else f"{bear_bull_reason}; {reason}"
	# No debt = auto pass
	if total_debt is not None and total_debt == 0:
		bear_bull_flag = False
		bear_bull_reason = None

	# --- Active Dilution ---
	shares_change_qoq, shares_note = _get_shares_change_qoq(ticker)
	dilution_flag = False
	dilution_reason = None
	if shares_change_qoq is not None and shares_change_qoq > 2.0:
		dilution_flag = True
		dilution_reason = f"shares_change_qoq ({shares_change_qoq}%) > 2%"

	# --- No-Growth Floor ---
	no_growth_value = None
	no_growth_flag = False
	no_growth_reason = None
	if total_revenue is not None and operating_margins is not None:
		no_growth_value = total_revenue * operating_margins * NO_GROWTH_PE
		# Handle negative operating margins: no_growth_value will be negative
		if no_growth_value < 0:
			no_growth_value = 0.0
		no_growth_value = round(no_growth_value, 0)
		if market_cap is not None and market_cap > 0:
			if no_growth_value < 0.5 * market_cap:
				no_growth_flag = True
				no_growth_reason = (
					f"no_growth_value ({no_growth_value:.0f}) < 0.5x market_cap ({market_cap:.0f})"
				)

	# --- Margin Collapse ---
	gross_margin, operating_margin, margin_trend, margin_yoy_change = _get_margin_trend(ticker)
	margin_collapse_flag = False
	margin_collapse_reason = None
	if margin_yoy_change is not None and margin_yoy_change < -5:
		margin_collapse_flag = True
		margin_collapse_reason = f"operating_margin declined {margin_yoy_change}pp YoY"

	# --- SBC % of Revenue ---
	sbc_pct_revenue = _get_sbc_pct_revenue(ticker)

	# --- Forward PE and PEG ---
	forward_pe, peg_ratio = _get_forward_pe_and_peg(ticker)

	# --- IO% ---
	io_pct = _get_io_pct(ticker)

	# --- Health Gates Summary ---
	flags = []
	if bear_bull_flag:
		flags.append(f"bear_bull_paradox: {bear_bull_reason}")
	if dilution_flag:
		flags.append(f"active_dilution: {dilution_reason}")
	if no_growth_flag:
		flags.append(f"no_growth_fail: {no_growth_reason}")
	if margin_collapse_flag:
		flags.append(f"margin_collapse: {margin_collapse_reason}")

	health_gates = {
		"bear_bull_paradox": "FLAG" if bear_bull_flag else "PASS",
		"active_dilution": "FLAG" if dilution_flag else "PASS",
		"no_growth_fail": "FLAG" if no_growth_flag else "PASS",
		"margin_collapse": "FLAG" if margin_collapse_flag else "PASS",
	}

	# Add notes for skipped checks
	if shares_note is not None:
		health_gates["active_dilution_note"] = shares_note

	# Raw data + classification thresholds for each gate
	mos_pct = None
	if no_growth_value is not None and market_cap is not None and market_cap > 0:
		mos_pct = round((no_growth_value / market_cap - 1) * 100, 1)

	health_gates["detail"] = {
		"bear_bull_paradox": {
			"total_debt": total_debt,
			"market_cap": market_cap,
			"interest_coverage": interest_coverage,
			"debt_to_equity": debt_to_equity,
			"thresholds": "FLAG: debt > 2x mcap OR coverage < 1x | PASS: otherwise",
		},
		"active_dilution": {
			"shares_change_qoq_pct": shares_change_qoq,
			"thresholds": "FLAG: > 2% | PASS: <= 2%",
		},
		"no_growth_fail": {
			"no_growth_value": no_growth_value,
			"market_cap": market_cap,
			"margin_of_safety_pct": mos_pct,
			"thresholds": "FLAG: ngv < 0.5x mcap | PASS: ngv >= 0.5x mcap",
		},
		"margin_collapse": {
			"gross_margin": gross_margin,
			"operating_margin": operating_margin,
			"margin_trend": margin_trend,
			"margin_yoy_change_pp": margin_yoy_change,
			"thresholds": "FLAG: yoy_change < -5pp | PASS: yoy_change >= -5pp",
		},
	}

	gate_passes = sum(1 for k, v in health_gates.items() if v == "PASS" and k not in ("detail", "active_dilution_note"))

	# --- Asymmetry Score (0-100) ---
	# Financial Health: 40 points = gate_passes * 10
	health_score = gate_passes * 10  # max 40

	# Valuation Upside: 30 points based on no_growth_value / market_cap ratio
	valuation_score = 0.0
	if no_growth_value is not None and market_cap is not None and market_cap > 0:
		ratio = no_growth_value / market_cap
		# ratio >= 1.0 means stock is cheap on zero-growth basis = full 30 points
		# ratio 0.5 = 15 points, ratio 0.0 = 0 points
		valuation_score = min(30.0, max(0.0, ratio * 30.0))

	# Bottleneck Quality: 30 points = bottleneck_score / 6 * 30
	bottleneck_quality = (bottleneck_score / 6.0) * 30.0

	asymmetry_score = round(health_score + valuation_score + bottleneck_quality, 1)

	# --- Nested Bottleneck & Sole Western adjustments ---
	nested_bottleneck_detected = nested_bottleneck
	sole_western_alternative = sole_western

	if nested_bottleneck:
		asymmetry_score = min(100.0, asymmetry_score + 5.0)
	if sole_western:
		asymmetry_score = min(100.0, asymmetry_score + 3.0)

	return {
		"ticker": symbol.upper(),
		"health_gates": health_gates,
		"financial_validation": {
			"debt_to_equity": debt_to_equity,
			"interest_coverage": interest_coverage,
			"sbc_pct_revenue": sbc_pct_revenue,
			"shares_change_qoq_pct": shares_change_qoq,
			"no_growth_value": no_growth_value,
			"forward_pe": forward_pe,
			"peg_ratio": peg_ratio,
			"io_pct": io_pct,
			"gross_margin": gross_margin,
			"operating_margin": operating_margin,
			"margin_trend": margin_trend,
			"margin_yoy_change_pp": margin_yoy_change,
		},
		"asymmetry_score": asymmetry_score,
		"nested_bottleneck_detected": nested_bottleneck_detected,
		"sole_western_alternative": sole_western_alternative,
		"composite": {
			"health_gate_passes": gate_passes,
			"health_gate_total": 4,
			"flags": flags,
			"score_breakdown": {
				"health_points": round(health_score, 1),
				"valuation_points": round(valuation_score, 1),
				"bottleneck_points": round(bottleneck_quality, 1),
			},
		},
	}


# ---------------------------------------------------------------------------
# Rank helper: Supply Dominance formula
# ---------------------------------------------------------------------------


def _classify_balance_sheet(result):
	"""Classify balance sheet health for ranking formula.

	Returns factor: 1.0 (healthy), 0.5 (warning), 0.0 (toxic).
	"""
	flags = result["composite"]["flags"]
	gate_passes = result["composite"]["health_gate_passes"]

	if gate_passes == 4:
		return 1.0
	if gate_passes >= 3:
		return 0.5
	return 0.0


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def _parse_bool_flags(flags_str, count):
	"""Parse comma-separated boolean flags string.

	Converts 'true,false,true' to [True, False, True].
	Returns [False]*count if flags_str is None or malformed.
	"""
	if not flags_str:
		return [False] * count
	parts = [s.strip().lower() in ("true", "1", "yes") for s in flags_str.split(",")]
	if len(parts) != count:
		return [False] * count  # fallback: ignore malformed input
	return parts


@safe_run
def cmd_validate(args):
	result = _build_validation(
		args.ticker, args.bottleneck_score,
		nested_bottleneck=args.nested_bottleneck,
		sole_western=args.sole_western,
	)
	output_json(result)


@safe_run
def cmd_batch(args):
	tickers = args.tickers
	scores_str = args.bottleneck_scores

	# Parse bottleneck scores
	if scores_str:
		scores = [int(s.strip()) for s in scores_str.split(",")]
		if len(scores) != len(tickers):
			error_json(
				f"Bottleneck scores count ({len(scores)}) does not match "
				f"tickers count ({len(tickers)})"
			)
	else:
		scores = [5] * len(tickers)

	nested_flags = _parse_bool_flags(args.nested_bottleneck, len(tickers))
	western_flags = _parse_bool_flags(args.sole_western, len(tickers))

	results = []
	for ticker_sym, score, nested, western in zip(tickers, scores, nested_flags, western_flags):
		try:
			result = _build_validation(ticker_sym, score, nested_bottleneck=nested, sole_western=western)
			results.append(result)
		except SystemExit:
			raise
		except Exception as e:
			results.append({
				"ticker": ticker_sym.upper(),
				"error": f"{type(e).__name__}: {e}",
				"asymmetry_score": 0,
			})

	# Sort by asymmetry_score descending
	results.sort(key=lambda r: r.get("asymmetry_score", 0), reverse=True)

	output_json({
		"count": len(results),
		"sorted_by": "asymmetry_score_desc",
		"results": results,
	})


@safe_run
def cmd_rank(args):
	tickers = args.tickers
	scores_str = args.bottleneck_scores

	if not scores_str:
		error_json("--bottleneck-scores is required for rank command")

	scores = [int(s.strip()) for s in scores_str.split(",")]
	if len(scores) != len(tickers):
		error_json(
			f"Bottleneck scores count ({len(scores)}) does not match "
			f"tickers count ({len(tickers)})"
		)

	nested_flags = _parse_bool_flags(args.nested_bottleneck, len(tickers))
	western_flags = _parse_bool_flags(args.sole_western, len(tickers))

	rankings = []
	for ticker_sym, bn_score, nested, western in zip(tickers, scores, nested_flags, western_flags):
		try:
			result = _build_validation(ticker_sym, bn_score, nested_bottleneck=nested, sole_western=western)

			# Supply Dominance = bottleneck_score x revenue
			revenue = _safe_float(
				(result.get("financial_validation") or {}).get("no_growth_value")
			)
			# Use total revenue from yfinance info as a better proxy
			tk = yf.Ticker(ticker_sym)
			info = tk.info or {}
			total_revenue = _safe_float(info.get("totalRevenue"))
			market_cap = _safe_float(info.get("marketCap"))

			supply_dominance = bn_score * (total_revenue if total_revenue else 0)

			# Balance Sheet Factor
			bs_factor = _classify_balance_sheet(result)

			# IO%
			io_pct = (result.get("financial_validation") or {}).get("io_pct")
			io_decimal = (io_pct / 100.0) if io_pct is not None else 0.5  # assume 50% if unknown

			# Priority = (Supply Dominance / Market Cap) x Balance Sheet Factor x (1 - IO%)
			priority = 0.0
			if market_cap and market_cap > 0:
				priority = (supply_dominance / market_cap) * bs_factor * (1.0 - io_decimal)

			rankings.append({
				"ticker": ticker_sym.upper(),
				"bottleneck_score": bn_score,
				"supply_dominance": round(supply_dominance, 0),
				"market_cap": market_cap,
				"balance_sheet_factor": bs_factor,
				"io_pct": io_pct,
				"priority_score": round(priority, 6),
				"asymmetry_score": result.get("asymmetry_score", 0),
				"health_gates": result.get("health_gates"),
				"flags": result.get("composite", {}).get("flags", []),
			})
		except SystemExit:
			raise
		except Exception as e:
			rankings.append({
				"ticker": ticker_sym.upper(),
				"error": f"{type(e).__name__}: {e}",
				"priority_score": 0,
			})

	# Sort by priority_score descending
	rankings.sort(key=lambda r: r.get("priority_score", 0), reverse=True)

	output_json({
		"count": len(rankings),
		"sorted_by": "priority_score_desc",
		"formula": "(supply_dominance / market_cap) x balance_sheet_factor x (1 - io_pct)",
		"rankings": rankings,
	})


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main():
	parser = argparse.ArgumentParser(
		description="Bottleneck Scorer: sector-agnostic financial validation of bottleneck candidates"
	)
	sub = parser.add_subparsers(dest="command", required=True)

	# validate
	sp_validate = sub.add_parser("validate", help="Financial validation suite for a single candidate")
	sp_validate.add_argument("ticker", help="Stock ticker symbol")
	sp_validate.add_argument(
		"--bottleneck-score",
		type=int,
		default=5,
		choices=range(1, 7),
		metavar="1-6",
		help="Qualitative bottleneck score 1-6 from agent assessment (default: 5)",
	)
	sp_validate.add_argument(
		"--nested-bottleneck",
		action="store_true",
		default=False,
		help="Flag: this candidate is a nested bottleneck (bottleneck's bottleneck)",
	)
	sp_validate.add_argument(
		"--sole-western",
		action="store_true",
		default=False,
		help="Flag: this candidate is the sole Western alternative supplier",
	)
	sp_validate.set_defaults(func=cmd_validate)

	# batch
	sp_batch = sub.add_parser("batch", help="Batch validation sorted by asymmetry score")
	sp_batch.add_argument("tickers", nargs="+", help="Stock ticker symbols")
	sp_batch.add_argument(
		"--bottleneck-scores",
		type=str,
		default=None,
		help="Comma-separated bottleneck scores matching ticker order (default: all 5)",
	)
	sp_batch.add_argument(
		"--nested-bottleneck",
		type=str,
		default=None,
		help="Comma-separated boolean flags (true/false) for nested bottleneck per ticker",
	)
	sp_batch.add_argument(
		"--sole-western",
		type=str,
		default=None,
		help="Comma-separated boolean flags (true/false) for sole Western per ticker",
	)
	sp_batch.set_defaults(func=cmd_batch)

	# rank
	sp_rank = sub.add_parser("rank", help="Priority ranking using Supply Dominance formula")
	sp_rank.add_argument("tickers", nargs="+", help="Stock ticker symbols")
	sp_rank.add_argument(
		"--bottleneck-scores",
		type=str,
		required=True,
		help="Required. Comma-separated bottleneck scores matching ticker order",
	)
	sp_rank.add_argument(
		"--nested-bottleneck",
		type=str,
		default=None,
		help="Comma-separated boolean flags (true/false) for nested bottleneck per ticker",
	)
	sp_rank.add_argument(
		"--sole-western",
		type=str,
		default=None,
		help="Comma-separated boolean flags (true/false) for sole Western per ticker",
	)
	sp_rank.set_defaults(func=cmd_rank)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
