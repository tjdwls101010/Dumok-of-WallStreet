#!/usr/bin/env python3
"""Calendar Bias: Trading Day of Week (TDW) and Trading Day of Month (TDM) analysis.

Returns the current day's calendar-based trading bias using historical TDW and
TDM patterns. TDW identifies which weekdays have historically stronger or weaker
performance, while TDM captures month-start and month-end effects driven by
institutional fund flows.

Commands:
	today: Return today's TDW and TDM bias assessment

Args:
	(none - today command takes no arguments)

Returns:
	dict: {
		"date": str,
		"day_of_week": str,
		"trading_day_of_week": int,
		"trading_day_of_month": int,
		"tdw_bias": str,
		"tdm_bias": str,
		"tdw_note": str,
		"tdm_note": str,
		"combined_bias": str
	}

Example:
	>>> python calendar_bias.py today
	{
		"date": "2026-03-02",
		"day_of_week": "Monday",
		"trading_day_of_week": 1,
		"trading_day_of_month": 1,
		"tdw_bias": "bullish",
		"tdm_bias": "bullish",
		"tdw_note": "Monday historically bullish for S&P; strong open tendency",
		"tdm_note": "Month-start effect: institutional inflows, fund deployment",
		"combined_bias": "bullish"
	}

Use Cases:
	- Filter breakout entries by favorable calendar days
	- Avoid opening new positions on historically weak days
	- Combine with ATR breakout levels for day-filtered entries
	- Assess daily directional bias before market open

Notes:
	- TDW bias is based on S&P 500 historical data (1982-2011)
	- S&P 500 TDW Performance: Monday +$91/trade, Tuesday +$59/trade,
	  Wednesday -$27/trade, Thursday -$10/trade, Friday +$134/trade (1982-1998)
	- Electronic era update (1998-2011): Monday +$45, Tuesday +$56,
	  Wednesday -$27, Thursday -$37, Friday +$109
	- Cumulative TDW (volatility breakout, 2000-2011): Monday $50,000,
	  Tuesday $30,000, Wednesday -$22,000
	- TDM: Month start (TDM 1-4) and month end (TDM 19-22) show bullish bias
	- TDM 21 is the strongest: $945 avg profit/trade (1982-1998),
	  confirmed $297 avg/trade (1998-2011)
	- Best TDMs for buying: 8, 18, 19, 20, 21, 22

See Also:
	- atr_breakout.py: ATR-based volatility breakout levels
	- williams_r.py: Williams %R momentum oscillator
"""

import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import output_json, safe_run

# Trading Day of Week bias lookup (1=Monday through 5=Friday)
TDW_BIAS = {
	1: {"bias": "bullish", "note": "Monday historically bullish for S&P; strong open tendency"},
	2: {"bias": "bullish", "note": "Tuesday continues Monday momentum; second strongest day"},
	3: {"bias": "neutral", "note": "Wednesday mixed; mid-week consolidation typical"},
	4: {"bias": "bearish", "note": "Thursday historically weakest day; profit-taking common"},
	5: {"bias": "neutral", "note": "Friday mixed; position squaring before weekend"},
}

# Day name lookup
DAY_NAMES = {
	0: "Monday",
	1: "Tuesday",
	2: "Wednesday",
	3: "Thursday",
	4: "Friday",
	5: "Saturday",
	6: "Sunday",
}


def _tdm_bias(day):
	"""Determine Trading Day of Month bias.

	Args:
		day: Calendar day of month (1-31)

	Returns:
		dict: {"bias": str, "note": str}
	"""
	if day <= 3:
		return {"bias": "bullish", "note": "Month-start effect: institutional inflows, fund deployment"}
	elif day >= 25:
		return {"bias": "bullish", "note": "Month-end effect: window dressing, fund inflows"}
	elif 10 <= day <= 18:
		return {"bias": "bearish", "note": "Mid-month weakness: tax payments, low institutional activity"}
	else:
		return {"bias": "neutral", "note": "Transition zone; no strong historical bias"}


def _combine_bias(tdw_bias, tdm_bias):
	"""Combine TDW and TDM biases into a single assessment.

	Scoring: bullish=+1, bearish=-1, neutral=0
	Combined: >=2 bullish, 1 slightly_bullish, -1 slightly_bearish, <=-2 bearish, 0 neutral

	Args:
		tdw_bias: TDW bias string
		tdm_bias: TDM bias string

	Returns:
		str: Combined bias assessment
	"""
	score = 0
	if tdw_bias == "bullish":
		score += 1
	elif tdw_bias == "bearish":
		score -= 1
	if tdm_bias == "bullish":
		score += 1
	elif tdm_bias == "bearish":
		score -= 1

	if score >= 2:
		return "bullish"
	elif score == 1:
		return "slightly_bullish"
	elif score == -1:
		return "slightly_bearish"
	elif score <= -2:
		return "bearish"
	return "neutral"


def _trading_day_of_week(dt):
	"""Get the trading day of the week (1=Monday, 5=Friday).

	For weekends, returns the nearest trading day equivalent.

	Args:
		dt: datetime.date object

	Returns:
		int: Trading day of week (1-5)
	"""
	weekday = dt.weekday()  # 0=Monday, 6=Sunday
	if weekday <= 4:
		return weekday + 1  # 1=Monday through 5=Friday
	# Weekend: Saturday->5 (Friday equivalent), Sunday->1 (Monday equivalent)
	return 5 if weekday == 5 else 1


def _trading_day_of_month(dt):
	"""Get the calendar day of the month.

	Args:
		dt: datetime.date object

	Returns:
		int: Day of month (1-31)
	"""
	return dt.day


@safe_run
def cmd_today(args):
	"""Return today's TDW and TDM calendar bias."""
	today = datetime.date.today()

	tdw = _trading_day_of_week(today)
	tdm = _trading_day_of_month(today)

	day_name = DAY_NAMES.get(today.weekday(), "Unknown")

	# Look up biases
	tdw_info = TDW_BIAS.get(tdw, {"bias": "neutral", "note": "No data for this day"})
	tdm_info = _tdm_bias(tdm)

	combined = _combine_bias(tdw_info["bias"], tdm_info["bias"])

	output_json({
		"date": str(today),
		"day_of_week": day_name,
		"trading_day_of_week": tdw,
		"trading_day_of_month": tdm,
		"tdw_bias": tdw_info["bias"],
		"tdm_bias": tdm_info["bias"],
		"tdw_note": tdw_info["note"],
		"tdm_note": tdm_info["note"],
		"combined_bias": combined,
	})


def main():
	parser = argparse.ArgumentParser(description="TDW/TDM Calendar Bias Analysis")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("today", help="Return today's TDW and TDM bias")
	sp.set_defaults(func=cmd_today)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
