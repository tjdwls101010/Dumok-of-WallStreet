#!/usr/bin/env python3
"""Multi-Asset Divergence Detection analyzing correlation breakdown between traditionally linked assets.

Identifies regime transitions and structural market shifts by monitoring when historically correlated asset pairs
(yields vs equities, safe havens vs risk assets, sectors vs commodities) deviate from expected relationships.
Divergence signals often precede major market turning points and regime changes.

Args:
	--yield-symbol (str): Treasury yield symbol for yield-equity analysis (default: "^TNX")
	--equity-symbol (str): Equity index for yield-equity analysis (default: "SPY")
	--safe-haven (str): Safe haven asset for risk-off analysis (default: "GLD")
	--equity (str): Equity index for safe-haven analysis (default: "SPY")
	--sector (str): Sector ETF for commodity sensitivity analysis (default: "XLB")
	--commodity (str): Commodity ETF for sector analysis (default: "DBC")
	--period (str): Historical data period for correlation analysis (default: "2y")
	--window (int): Rolling correlation window in days (default: 60)

Returns:
	dict: {
		"yield_symbol": str,
		"equity_symbol": str,
		"period": str,
		"window_days": int,
		"correlation_analysis": {
			"current_correlation": float,     # Current rolling correlation (-1 to 1)
			"overall_correlation": float,     # Full period correlation
			"correlation_mean": float,        # Historical mean correlation
			"correlation_std": float,         # Correlation standard deviation
			"correlation_zscore": float       # Z-score of current correlation
		},
		"recent_performance": {
			"yield_change_pct": float,        # Recent yield percentage change
			"equity_change_pct": float        # Recent equity percentage change
		},
		"divergence_type": str,               # CLASSIC DIVERGENCE, INVERSE DIVERGENCE, etc.
		"interpretation": str,                # Correlation z-score interpretation
		"signal": str,                        # RISK-OFF, RISK-ON, or NEUTRAL
		"date": str
	}

Example:
	>>> python divergence.py yield-equity --yield-symbol "^TNX" --equity-symbol "SPY"
	{
		"yield_symbol": "^TNX",
		"equity_symbol": "SPY",
		"correlation_analysis": {
			"current_correlation": -0.45,
			"correlation_zscore": -2.3,
			"correlation_mean": 0.15
		},
		"divergence_type": "CLASSIC DIVERGENCE: Yields rising, equities falling (risk-off)",
		"signal": "RISK-OFF"
	}

Use Cases:
	- Regime transition detection when yield-equity correlation breaks down
	- Safe haven flow monitoring during market stress periods
	- Sector-commodity decoupling signals for supply/demand imbalances
	- Risk-on/risk-off sentiment shifts across asset classes
	- Correlation breakdown as early warning for volatility spikes

Notes:
	- Yield-equity negative correlation is expected; positive correlation signals unusual regime
	- Safe haven assets (gold, treasuries) typically inverse to equities during stress
	- Sector-commodity correlations break down during supply shocks or demand destruction
	- Correlation z-scores >2σ indicate extreme divergence from historical norms
	- Window size affects sensitivity: shorter windows (30d) catch rapid shifts, longer windows (90d) confirm trends

See Also:
	- convergence.py: Multi-model consensus signals for high-conviction trades
	- analysis_utils.py: calculate_rolling_correlation for correlation mechanics
	- macro/macro.py: Fair value models for fundamental divergence analysis
	- technical/__init__.py: RSI for momentum divergence detection
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
import yfinance as yf

# Support both standalone execution and module imports
try:
	from ..utils import output_json, safe_run
except ImportError:
	from utils import output_json, safe_run


def fetch_aligned_prices(symbols: list, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
	"""Fetch and align price data for multiple symbols."""
	data_dict = {}
	for sym in symbols:
		ticker = yf.Ticker(sym.strip())
		hist = ticker.history(period=period, interval=interval)
		if not hist.empty:
			close_series = hist["Close"].copy()
			# Normalize timezone
			if close_series.index.tz is not None:
				close_series.index = close_series.index.tz_localize(None)
			close_series.index = close_series.index.normalize()
			data_dict[sym.strip()] = close_series

	if len(data_dict) < 2:
		return pd.DataFrame()

	df = pd.DataFrame(data_dict)
	df = df.dropna()
	return df


@safe_run
def cmd_yield_equity(args):
	"""Detect yield-equity divergence.

	Analyzes correlation between bond yields (rising = bearish for bonds) and
	equity prices. Divergence indicates shifting risk preferences or regime change.
	"""
	# Fetch data for treasury yield and equity
	# Default: 10Y Treasury yield (^TNX) vs S&P 500 (SPY)
	yield_symbol = args.yield_symbol or "^TNX"
	equity_symbol = args.equity_symbol or "SPY"

	df = fetch_aligned_prices([yield_symbol, equity_symbol], args.period, args.interval)

	if df.empty or len(df) < args.window:
		output_json({"error": "Insufficient data for divergence analysis"})
		return

	# Calculate returns
	yield_returns = df[yield_symbol].pct_change().dropna()
	equity_returns = df[equity_symbol].pct_change().dropna()

	# Overall correlation
	overall_corr = yield_returns.corr(equity_returns)

	# Rolling correlation
	rolling_corr = yield_returns.rolling(window=args.window).corr(equity_returns)
	current_corr = rolling_corr.iloc[-1]

	# Historical correlation stats
	corr_mean = rolling_corr.mean()
	corr_std = rolling_corr.std()
	corr_zscore = (current_corr - corr_mean) / corr_std if corr_std > 0 else 0

	# Recent price changes
	recent_yield_change = (
		(df[yield_symbol].iloc[-1] - df[yield_symbol].iloc[-args.window]) / df[yield_symbol].iloc[-args.window] * 100
	)
	recent_equity_change = (
		(df[equity_symbol].iloc[-1] - df[equity_symbol].iloc[-args.window]) / df[equity_symbol].iloc[-args.window] * 100
	)

	# Divergence interpretation
	if current_corr < -0.3:
		if recent_yield_change > 0 and recent_equity_change < 0:
			divergence_type = "CLASSIC DIVERGENCE: Yields rising, equities falling (risk-off)"
		elif recent_yield_change < 0 and recent_equity_change > 0:
			divergence_type = "INVERSE DIVERGENCE: Yields falling, equities rising (risk-on)"
		else:
			divergence_type = "NEGATIVE CORRELATION: Inverse relationship (expected)"
	elif current_corr > 0.3:
		divergence_type = "SYNCHRONIZED: Yields and equities moving together (unusual)"
	else:
		divergence_type = "NEUTRAL: Low correlation, no clear divergence"

	result = {
		"yield_symbol": yield_symbol,
		"equity_symbol": equity_symbol,
		"period": args.period,
		"window_days": args.window,
		"correlation_analysis": {
			"current_correlation": round(float(current_corr), 4),
			"overall_correlation": round(float(overall_corr), 4),
			"correlation_mean": round(float(corr_mean), 4),
			"correlation_std": round(float(corr_std), 4),
			"correlation_zscore": round(float(corr_zscore), 2),
		},
		"recent_performance": {
			f"{yield_symbol}_change_pct": round(float(recent_yield_change), 2),
			f"{equity_symbol}_change_pct": round(float(recent_equity_change), 2),
		},
		"divergence_type": divergence_type,
		"interpretation": f"Current correlation z-score: {corr_zscore:.2f}σ {'above' if corr_zscore > 0 else 'below'} historical mean",
		"date": str(df.index[-1].date()),
	}
	output_json(result)


@safe_run
def cmd_safe_haven(args):
	"""Detect safe haven divergence.

	Analyzes correlation between safe haven assets (gold, treasuries) and equities.
	Divergence indicates risk-off flows or safe haven unwinding.
	"""
	# Default: Gold (GLD) vs S&P 500 (SPY)
	safe_haven_symbol = args.safe_haven or "GLD"
	equity_symbol = args.equity or "SPY"

	df = fetch_aligned_prices([safe_haven_symbol, equity_symbol], args.period, args.interval)

	if df.empty or len(df) < args.window:
		output_json({"error": "Insufficient data for divergence analysis"})
		return

	# Calculate returns
	safe_haven_returns = df[safe_haven_symbol].pct_change().dropna()
	equity_returns = df[equity_symbol].pct_change().dropna()

	# Overall correlation
	overall_corr = safe_haven_returns.corr(equity_returns)

	# Rolling correlation
	rolling_corr = safe_haven_returns.rolling(window=args.window).corr(equity_returns)
	current_corr = rolling_corr.iloc[-1]

	# Historical correlation stats
	corr_mean = rolling_corr.mean()
	corr_std = rolling_corr.std()
	corr_zscore = (current_corr - corr_mean) / corr_std if corr_std > 0 else 0

	# Recent price changes
	recent_safe_haven_change = (
		(df[safe_haven_symbol].iloc[-1] - df[safe_haven_symbol].iloc[-args.window])
		/ df[safe_haven_symbol].iloc[-args.window]
		* 100
	)
	recent_equity_change = (
		(df[equity_symbol].iloc[-1] - df[equity_symbol].iloc[-args.window]) / df[equity_symbol].iloc[-args.window] * 100
	)

	# Divergence interpretation
	if current_corr < -0.3:
		if recent_safe_haven_change > 0 and recent_equity_change < 0:
			divergence_type = "SAFE HAVEN DEMAND: Gold rising, equities falling (risk-off)"
		elif recent_safe_haven_change < 0 and recent_equity_change > 0:
			divergence_type = "SAFE HAVEN UNWINDING: Gold falling, equities rising (risk-on)"
		else:
			divergence_type = "NEGATIVE CORRELATION: Inverse relationship (expected)"
	elif current_corr > 0.3:
		divergence_type = "SYNCHRONIZED: Safe haven and equities rising together (unusual, possible inflation hedge)"
		if corr_zscore > 2:
			divergence_type += " - EXTREME DIVERGENCE"
	else:
		divergence_type = "NEUTRAL: Low correlation, no clear divergence"

	result = {
		"safe_haven_symbol": safe_haven_symbol,
		"equity_symbol": equity_symbol,
		"period": args.period,
		"window_days": args.window,
		"correlation_analysis": {
			"current_correlation": round(float(current_corr), 4),
			"overall_correlation": round(float(overall_corr), 4),
			"correlation_mean": round(float(corr_mean), 4),
			"correlation_std": round(float(corr_std), 4),
			"correlation_zscore": round(float(corr_zscore), 2),
		},
		"recent_performance": {
			f"{safe_haven_symbol}_change_pct": round(float(recent_safe_haven_change), 2),
			f"{equity_symbol}_change_pct": round(float(recent_equity_change), 2),
		},
		"divergence_type": divergence_type,
		"interpretation": f"Current correlation z-score: {corr_zscore:.2f}σ {'above' if corr_zscore > 0 else 'below'} historical mean",
		"signal": "RISK-OFF"
		if recent_safe_haven_change > 0 and recent_equity_change < 0
		else "RISK-ON"
		if recent_safe_haven_change < 0 and recent_equity_change > 0
		else "NEUTRAL",
		"date": str(df.index[-1].date()),
	}
	output_json(result)


@safe_run
def cmd_sector_divergence(args):
	"""Detect sector-commodity divergence.

	Analyzes correlation between commodity-sensitive sectors (e.g., Materials)
	and underlying commodities. Divergence indicates supply/demand imbalances.
	"""
	# Default: Materials sector (XLB) vs Commodities (DBC)
	sector_symbol = args.sector or "XLB"
	commodity_symbol = args.commodity or "DBC"

	df = fetch_aligned_prices([sector_symbol, commodity_symbol], args.period, args.interval)

	if df.empty or len(df) < args.window:
		output_json({"error": "Insufficient data for divergence analysis"})
		return

	# Calculate returns
	sector_returns = df[sector_symbol].pct_change().dropna()
	commodity_returns = df[commodity_symbol].pct_change().dropna()

	# Overall correlation
	overall_corr = sector_returns.corr(commodity_returns)

	# Rolling correlation
	rolling_corr = sector_returns.rolling(window=args.window).corr(commodity_returns)
	current_corr = rolling_corr.iloc[-1]

	# Historical correlation stats
	corr_mean = rolling_corr.mean()
	corr_std = rolling_corr.std()
	corr_zscore = (current_corr - corr_mean) / corr_std if corr_std > 0 else 0

	# Recent price changes
	recent_sector_change = (
		(df[sector_symbol].iloc[-1] - df[sector_symbol].iloc[-args.window]) / df[sector_symbol].iloc[-args.window] * 100
	)
	recent_commodity_change = (
		(df[commodity_symbol].iloc[-1] - df[commodity_symbol].iloc[-args.window])
		/ df[commodity_symbol].iloc[-args.window]
		* 100
	)

	# Divergence interpretation
	if current_corr < 0.3:
		if corr_zscore < -2:
			divergence_type = "SEVERE DECOUPLING: Sector and commodities diverging significantly"
		else:
			divergence_type = "DECOUPLING: Sector and commodities moving independently"
	elif current_corr > 0.7:
		divergence_type = "STRONG COUPLING: Sector following commodities (expected)"
	else:
		divergence_type = "MODERATE COUPLING: Normal relationship"

	result = {
		"sector_symbol": sector_symbol,
		"commodity_symbol": commodity_symbol,
		"period": args.period,
		"window_days": args.window,
		"correlation_analysis": {
			"current_correlation": round(float(current_corr), 4),
			"overall_correlation": round(float(overall_corr), 4),
			"correlation_mean": round(float(corr_mean), 4),
			"correlation_std": round(float(corr_std), 4),
			"correlation_zscore": round(float(corr_zscore), 2),
		},
		"recent_performance": {
			f"{sector_symbol}_change_pct": round(float(recent_sector_change), 2),
			f"{commodity_symbol}_change_pct": round(float(recent_commodity_change), 2),
		},
		"divergence_type": divergence_type,
		"interpretation": f"Current correlation z-score: {corr_zscore:.2f}σ {'above' if corr_zscore > 0 else 'below'} historical mean",
		"date": str(df.index[-1].date()),
	}
	output_json(result)


def main():
	parser = argparse.ArgumentParser(
		description="Divergence detection tools",
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	sub = parser.add_subparsers(dest="command", help="Subcommands")

	# Yield-equity divergence
	sp = sub.add_parser("yield-equity", help="Detect yield-equity divergence")
	sp.add_argument("--yield-symbol", default="^TNX", help="Treasury yield symbol (default: ^TNX)")
	sp.add_argument("--equity-symbol", default="SPY", help="Equity symbol (default: SPY)")
	sp.add_argument("--period", default="2y", help="Data period (default: 2y)")
	sp.add_argument("--interval", default="1d", help="Data interval (default: 1d)")
	sp.add_argument("--window", type=int, default=60, help="Rolling window (default: 60)")
	sp.set_defaults(func=cmd_yield_equity)

	# Safe haven divergence
	sp = sub.add_parser("safe-haven", help="Detect safe haven divergence")
	sp.add_argument("--safe-haven", default="GLD", help="Safe haven symbol (default: GLD)")
	sp.add_argument("--equity", default="SPY", help="Equity symbol (default: SPY)")
	sp.add_argument("--period", default="2y", help="Data period (default: 2y)")
	sp.add_argument("--interval", default="1d", help="Data interval (default: 1d)")
	sp.add_argument("--window", type=int, default=60, help="Rolling window (default: 60)")
	sp.set_defaults(func=cmd_safe_haven)

	# Sector-commodity divergence
	sp = sub.add_parser("sector-commodity", help="Detect sector-commodity divergence")
	sp.add_argument("--sector", default="XLB", help="Sector ETF symbol (default: XLB)")
	sp.add_argument("--commodity", default="DBC", help="Commodity ETF symbol (default: DBC)")
	sp.add_argument("--period", default="2y", help="Data period (default: 2y)")
	sp.add_argument("--interval", default="1d", help="Data interval (default: 1d)")
	sp.add_argument("--window", type=int, default=60, help="Rolling window (default: 60)")
	sp.set_defaults(func=cmd_sector_divergence)

	args = parser.parse_args()

	if not args.command:
		parser.print_help()
		return

	args.func(args)


if __name__ == "__main__":
	main()
