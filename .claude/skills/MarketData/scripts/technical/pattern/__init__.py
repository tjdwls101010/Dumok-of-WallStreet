#!/usr/bin/env python3
"""Historical pattern matching and similarity analysis for SidneyKim0 methodology."""

import argparse

from .fanchart import cmd_analogue, cmd_fanchart
from .multi_dtw import cmd_multi_dtw
from .regime import cmd_regime
from .similarity import cmd_dtw_similarity, cmd_similarity


def main():
	parser = argparse.ArgumentParser(description="Historical pattern matching analysis")
	sub = parser.add_subparsers(dest="command", required=True)

	# Similarity
	sp = sub.add_parser("similarity", help="Find similar historical patterns")
	sp.add_argument("symbol")
	sp.add_argument("--window", type=int, default=140, help="Pattern window size in days")
	sp.add_argument("--period", default="10y", help="Data period for history")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.add_argument("--top-n", type=int, default=10, help="Number of top patterns to return")
	sp.set_defaults(func=cmd_similarity)

	# Fan Chart
	sp = sub.add_parser("fanchart", help="Generate fan chart probability distribution")
	sp.add_argument("symbol")
	sp.add_argument("--window", type=int, default=140, help="Pattern window size")
	sp.add_argument("--period", default="10y", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.add_argument("--top-n", type=int, default=10, help="Number of patterns to base on")
	sp.add_argument("--forward-days", default="30,60,90", help="Forward days for returns")
	sp.set_defaults(func=cmd_fanchart)

	# Analogue
	sp = sub.add_parser("analogue", help="Compare with specific historical period")
	sp.add_argument("symbol")
	sp.add_argument("target_date", help="Target date to compare (YYYY-MM-DD)")
	sp.add_argument("--window", type=int, default=140, help="Comparison window")
	sp.add_argument("--period", default="max", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.set_defaults(func=cmd_analogue)

	# Regime
	sp = sub.add_parser("regime", help="Detect current market regime")
	sp.add_argument("symbols", help="Comma-separated symbols (e.g., GC=F,DX-Y.NYB,SPY)")
	sp.add_argument("--lookback", type=int, default=20, help="Lookback period for regime")
	sp.add_argument("--period", default="6mo", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.set_defaults(func=cmd_regime)

	# DTW Similarity (SidneyKim0 methodology)
	sp = sub.add_parser("dtw-similarity", help="Find similar patterns using Dynamic Time Warping")
	sp.add_argument("symbol")
	sp.add_argument("--window", type=int, default=60, help="Pattern window size in days")
	sp.add_argument("--period", default="15y", help="Data period for history")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.add_argument("--top-n", type=int, default=10, help="Number of top patterns to return")
	sp.add_argument("--threshold", type=float, default=2.0, help="DTW distance threshold (lower = stricter)")
	sp.add_argument("--use-slope", action="store_true", help="Use slope-based pattern matching")
	sp.set_defaults(func=cmd_dtw_similarity)

	# Multi-Feature DTW (SidneyKim0 methodology - price+RSI+slope+vol+D2H)
	sp = sub.add_parser("multi-dtw", help="Multi-feature DTW pattern matching")
	sp.add_argument("symbol")
	sp.add_argument("--features", default="price,rsi,slope,vol,d2h", help="Comma-separated features")
	sp.add_argument("--weights", default="1.0,0.5,0.3,0.3,0.3", help="Comma-separated feature weights")
	sp.add_argument("--window", type=int, default=60, help="Pattern window size in days")
	sp.add_argument("--period", default="15y", help="Data period for history")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.add_argument("--top-n", type=int, default=5, help="Number of top patterns to return")
	sp.add_argument("--threshold", type=float, default=3.0, help="Max weighted DTW distance")
	sp.set_defaults(func=cmd_multi_dtw)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
