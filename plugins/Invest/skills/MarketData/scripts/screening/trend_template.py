#!/usr/bin/env python3
"""Minervini Trend Template: 8-criteria checklist for Stage 2 qualification.

Evaluates a stock against Mark Minervini's 8 Trend Template criteria to determine
whether it qualifies as a Stage 2 uptrend candidate. Each criterion is individually
scored with pass/fail, and an overall verdict is produced.

Commands:
	check: Run full 8-criteria Trend Template check for a single ticker

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "MSFT")
	--period (str): Historical data period for MA calculation (default: "2y")

Returns:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"criteria": [
			{
				"id": int,
				"description": str,
				"passed": bool,
				"value": float or str,
				"threshold": str
			}
		],
		"passed_count": int,
		"total_count": 8,
		"overall_pass": bool,
		"score_pct": float,
		"moving_averages": {
			"sma50": float,
			"sma150": float,
			"sma200": float,
			"sma200_1mo_ago": float
		}
	}

Example:
	>>> python trend_template.py check NVDA --period 2y
	{
		"symbol": "NVDA",
		"date": "2026-02-07",
		"current_price": 135.50,
		"criteria": [
			{"id": 1, "description": "Price > 150-day MA AND 200-day MA", "passed": true, "value": "135.50 > 120.30 (SMA150) & 110.80 (SMA200)", "threshold": "Price above both MAs"},
			...
		],
		"passed_count": 8,
		"total_count": 8,
		"overall_pass": true,
		"score_pct": 100.0
	}

Use Cases:
	- Quick qualification check for SEPA methodology stock selection
	- Filter universe to only Stage 2 uptrend candidates
	- Monitor existing positions for trend degradation
	- Batch screening when combined with watchlist

Notes:
	- All 8 criteria must pass for a stock to qualify as a Trend Template pass
	- Criterion 8 (RS Ranking >= 70) uses self-calculated relative strength
	  based on weighted multi-period returns vs S&P 500
	- 200-day MA uptrend check uses 1-month lookback minimum
	- Score percentage allows partial assessment (e.g., 6/8 = 75%)

See Also:
	- stage_analysis.py: Detailed Stage 1-4 classification
	- rs_ranking.py: Full RS ranking calculation and screening
	- sepa_pipeline.py: Complete SEPA analysis pipeline
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from technical.indicators import calculate_sma
from technical.rs_ranking import compute_rs_score
from utils import output_json, safe_run


@safe_run
def cmd_check(args):
	"""Run 8-criteria Trend Template check."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=args.period, interval="1d")

	if data.empty or len(data) < 200:
		output_json(
			{
				"error": f"Insufficient data for {symbol}. Need at least 200 trading days.",
				"data_points": len(data),
			}
		)
		return

	closes = data["Close"]
	current_price = float(closes.iloc[-1])
	date_str = str(data.index[-1].date())

	# Calculate moving averages
	sma50 = calculate_sma(closes, 50)
	sma150 = calculate_sma(closes, 150)
	sma200 = calculate_sma(closes, 200)

	current_sma50 = float(sma50.iloc[-1])
	current_sma150 = float(sma150.iloc[-1])
	current_sma200 = float(sma200.iloc[-1])

	# 200-day MA from ~1 month ago (22 trading days)
	sma200_1mo_ago = float(sma200.iloc[-22]) if len(sma200) >= 22 else float(sma200.iloc[0])

	# 52-week high and low
	one_year_data = closes.tail(252) if len(closes) >= 252 else closes
	week52_high = float(one_year_data.max())
	week52_low = float(one_year_data.min())

	# RS Ranking
	rs_score = compute_rs_score(symbol, period=args.period)

	# Evaluate 8 criteria
	criteria = []

	# 1. Price > 150-day MA AND 200-day MA
	c1_pass = current_price > current_sma150 and current_price > current_sma200
	criteria.append(
		{
			"id": 1,
			"description": "Price > 150-day MA AND 200-day MA",
			"passed": c1_pass,
			"value": f"{current_price:.2f} vs SMA150={current_sma150:.2f}, SMA200={current_sma200:.2f}",
			"threshold": "Price above both MAs",
		}
	)

	# 2. 150-day MA > 200-day MA
	c2_pass = current_sma150 > current_sma200
	criteria.append(
		{
			"id": 2,
			"description": "150-day MA > 200-day MA",
			"passed": c2_pass,
			"value": f"SMA150={current_sma150:.2f} vs SMA200={current_sma200:.2f}",
			"threshold": "SMA150 above SMA200",
		}
	)

	# 3. 200-day MA trending up (at least 1 month)
	c3_pass = current_sma200 > sma200_1mo_ago
	c3_change = ((current_sma200 / sma200_1mo_ago) - 1) * 100 if sma200_1mo_ago > 0 else 0
	criteria.append(
		{
			"id": 3,
			"description": "200-day MA trending up (at least 1 month)",
			"passed": c3_pass,
			"value": f"SMA200 now={current_sma200:.2f} vs 1mo ago={sma200_1mo_ago:.2f} ({c3_change:+.2f}%)",
			"threshold": "SMA200 rising over last month",
		}
	)

	# 4. 50-day MA > 150-day MA AND 200-day MA
	c4_pass = current_sma50 > current_sma150 and current_sma50 > current_sma200
	criteria.append(
		{
			"id": 4,
			"description": "50-day MA > 150-day MA AND 200-day MA",
			"passed": c4_pass,
			"value": f"SMA50={current_sma50:.2f} vs SMA150={current_sma150:.2f}, SMA200={current_sma200:.2f}",
			"threshold": "SMA50 above both longer MAs",
		}
	)

	# 5. Price > 50-day MA
	c5_pass = current_price > current_sma50
	criteria.append(
		{
			"id": 5,
			"description": "Price > 50-day MA",
			"passed": c5_pass,
			"value": f"{current_price:.2f} vs SMA50={current_sma50:.2f}",
			"threshold": "Price above SMA50",
		}
	)

	# 6. Price >= 52-week low * 1.30 (at least 30% above)
	low_threshold = week52_low * 1.30
	c6_pass = current_price >= low_threshold
	pct_above_low = ((current_price / week52_low) - 1) * 100 if week52_low > 0 else 0
	criteria.append(
		{
			"id": 6,
			"description": "Price at least 30% above 52-week low",
			"passed": c6_pass,
			"value": f"{current_price:.2f} is {pct_above_low:.1f}% above 52w low {week52_low:.2f}",
			"threshold": f"Price >= {low_threshold:.2f} (52w low * 1.30)",
		}
	)

	# 7. Price within 25% of 52-week high (>= 75% of high)
	high_threshold = week52_high * 0.75
	c7_pass = current_price >= high_threshold
	pct_from_high = ((current_price / week52_high) - 1) * 100 if week52_high > 0 else 0
	criteria.append(
		{
			"id": 7,
			"description": "Price within 25% of 52-week high",
			"passed": c7_pass,
			"value": f"{current_price:.2f} is {pct_from_high:.1f}% from 52w high {week52_high:.2f}",
			"threshold": f"Price >= {high_threshold:.2f} (52w high * 0.75)",
		}
	)

	# 8. RS Ranking >= 70
	c8_pass = rs_score is not None and rs_score >= 70
	criteria.append(
		{
			"id": 8,
			"description": "RS Ranking >= 70",
			"passed": c8_pass,
			"value": f"RS Score = {rs_score}" if rs_score is not None else "RS Score = N/A",
			"threshold": "RS >= 70 (relative to S&P 500)",
		}
	)

	passed_count = sum(1 for c in criteria if c["passed"])

	output_json(
		{
			"symbol": symbol,
			"date": date_str,
			"current_price": round(current_price, 2),
			"criteria": criteria,
			"passed_count": passed_count,
			"total_count": 8,
			"overall_pass": passed_count == 8,
			"score_pct": round(passed_count / 8 * 100, 1),
			"moving_averages": {
				"sma50": round(current_sma50, 2),
				"sma150": round(current_sma150, 2),
				"sma200": round(current_sma200, 2),
				"sma200_1mo_ago": round(sma200_1mo_ago, 2),
			},
			"week52": {
				"high": round(week52_high, 2),
				"low": round(week52_low, 2),
			},
			"rs_score": rs_score,
		}
	)


def main():
	parser = argparse.ArgumentParser(description="Minervini Trend Template 8-criteria check")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("check", help="Run Trend Template check for a ticker")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="2y", help="Data period (default: 2y)")
	sp.set_defaults(func=cmd_check)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
