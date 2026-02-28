#!/usr/bin/env python3
"""Analyst Estimates and Recommendations aggregating Wall Street consensus for earnings, revenue, and price targets.

Retrieves institutional analyst data including price targets, earnings/revenue estimates, EPS trends and revisions,
growth forecasts, buy/sell/hold recommendations, upgrades/downgrades, and ESG sustainability scores.
Provides multi-analyst consensus data for fundamental analysis and sentiment tracking.

Args:
	symbol (str): Stock ticker symbol (e.g., "AAPL", "MSFT", "GOOGL")
	command (str): One of get-analyst-price-targets, get-earnings-estimate, get-revenue-estimate,
				   get-earnings-history, get-eps-trend, get-eps-revisions, get-growth-estimates,
				   get-recommendations, get-recommendations-summary, get-upgrades-downgrades, get-sustainability

Returns:
	dict: Structure varies by command, typical fields include:
	{
		"analyst_price_targets": {
			"current": float,           # Current price target
			"low": float,               # Lowest analyst target
			"high": float,              # Highest analyst target
			"mean": float,              # Average target
			"median": float             # Median target
		},
		"earnings_estimate": {
			"quarter": str,             # Quarter identifier
			"avg": float,               # Average EPS estimate
			"low": float,               # Low estimate
			"high": float,              # High estimate
			"year_ago_eps": float,      # Prior year EPS
			"number_of_analysts": int   # Analyst count
		},
		"recommendations_summary": {
			"period": str,              # Time period
			"strongBuy": int,           # Strong buy count
			"buy": int,                 # Buy count
			"hold": int,                # Hold count
			"sell": int,                # Sell count
			"strongSell": int           # Strong sell count
		},
		"upgrades_downgrades": [
			{
				"date": str,            # Action date
				"firm": str,            # Analyst firm
				"action": str,          # upgrade/downgrade/init
				"from_grade": str,      # Previous rating
				"to_grade": str         # New rating
			}
		]
	}

Example:
	>>> python analysis.py get-analyst-price-targets AAPL
	{
		"current": 185.50,
		"low": 160.00,
		"high": 220.00,
		"mean": 195.75,
		"median": 195.00
	}
    
	>>> python analysis.py get-recommendations-summary MSFT
	{
		"period": "0m",
		"strongBuy": 25,
		"buy": 18,
		"hold": 5,
		"sell": 0,
		"strongSell": 0
	}

Use Cases:
	- Analyst sentiment tracking: Monitor consensus buy/sell/hold shifts over time
	- Price target analysis: Compare current price to analyst targets for valuation
	- Earnings surprise prediction: Track EPS revisions leading up to earnings
	- Contrarian signals: Extreme consensus (all buy or all sell) often precedes reversals
	- Momentum confirmation: Upgrades/downgrades as confirmation of price moves

Notes:
	- Analyst price targets often lag price action (backward-looking)
	- Consensus "strong buy" ratings cluster at market tops (contrarian indicator)
	- EPS revisions (upgrades) are more reliable than absolute estimates
	- Recommendations skew bullish (more buys than sells across all stocks)
	- Upgrades/downgrades have short-term price impact (1-3 days)
	- Sustainability scores (ESG) increasingly impact institutional fund flows

See Also:
	- putcall_ratio.py: Options-based sentiment vs analyst sentiment
	- sentiment/fear_greed.py: Retail sentiment vs institutional analyst views
	- convergence.py: Combine analyst consensus with technical/macro models
	- divergence.py: Detect when analyst ratings diverge from price action
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf

# Support both standalone execution and module imports
try:
	from ..utils import output_json, safe_run
except ImportError:
	from utils import output_json, safe_run


@safe_run
def cmd_analyst_price_targets(args):
	output_json(yf.Ticker(args.symbol).get_analyst_price_targets())


@safe_run
def cmd_earnings_estimate(args):
	output_json(yf.Ticker(args.symbol).get_earnings_estimate())


@safe_run
def cmd_revenue_estimate(args):
	output_json(yf.Ticker(args.symbol).get_revenue_estimate())


@safe_run
def cmd_earnings_history(args):
	output_json(yf.Ticker(args.symbol).get_earnings_history())


@safe_run
def cmd_eps_trend(args):
	output_json(yf.Ticker(args.symbol).get_eps_trend())


@safe_run
def cmd_eps_revisions(args):
	output_json(yf.Ticker(args.symbol).get_eps_revisions())


@safe_run
def cmd_growth_estimates(args):
	output_json(yf.Ticker(args.symbol).get_growth_estimates())


@safe_run
def cmd_recommendations(args):
	output_json(yf.Ticker(args.symbol).get_recommendations())


@safe_run
def cmd_recommendations_summary(args):
	output_json(yf.Ticker(args.symbol).get_recommendations_summary())


@safe_run
def cmd_upgrades_downgrades(args):
	output_json(yf.Ticker(args.symbol).get_upgrades_downgrades())


@safe_run
def cmd_sustainability(args):
	output_json(yf.Ticker(args.symbol).get_sustainability())


def main():
	parser = argparse.ArgumentParser(description="Analyst estimates and recommendations")
	sub = parser.add_subparsers(dest="command", required=True)

	for name, func in [
		("get-analyst-price-targets", cmd_analyst_price_targets),
		("get-earnings-estimate", cmd_earnings_estimate),
		("get-revenue-estimate", cmd_revenue_estimate),
		("get-earnings-history", cmd_earnings_history),
		("get-eps-trend", cmd_eps_trend),
		("get-eps-revisions", cmd_eps_revisions),
		("get-growth-estimates", cmd_growth_estimates),
		("get-recommendations", cmd_recommendations),
		("get-recommendations-summary", cmd_recommendations_summary),
		("get-upgrades-downgrades", cmd_upgrades_downgrades),
		("get-sustainability", cmd_sustainability),
	]:
		sp = sub.add_parser(name)
		sp.add_argument("symbol")
		sp.set_defaults(func=func)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
