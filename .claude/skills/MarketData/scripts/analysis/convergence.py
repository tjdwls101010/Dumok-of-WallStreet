#!/usr/bin/env python3
"""Multi-Model Convergence Analysis - SidneyKim0 methodology.

Analyzes convergence across Technical, Macro, and Valuation models to generate
high-conviction signals when multiple independent models agree.

This implementation uses three independent models:
1. Technical Model: RSI-based momentum (overbought/oversold detection)
2. Macro Model: Fair value z-score from macroeconomic regression
3. Valuation Model: CAPE percentile vs historical extremes (US market only)

When all three models align (convergence), signal conviction is HIGH.
When 2/3 models align, conviction is MODERATE.
When models disagree (divergence), conviction is LOW or NONE.

Args:
	symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY", "^GSPC")
	--models (str): Comma-separated models to run (default: "technical,macro,valuation")
	--macro-inputs (str): Macro model inputs (e.g., "DX-Y.NYB,GC=F,^IXIC") - required for macro model
	--period (str): Historical data period (default: "5y" = 5 years)

Returns:
	dict: {
		"symbol": str,                 # Ticker symbol
		"date": str,                   # Analysis date
		"models": {                    # Individual model results
			"technical": {
				"signal": str,         # BULLISH/BEARISH/NEUTRAL
				"rsi": float,          # RSI value (0-100)
				"threshold": str,      # overbought/oversold/neutral
				"date": str
			},
			"macro": {
				"signal": str,         # BULLISH/BEARISH/NEUTRAL
				"zscore": float,       # Residual z-score
				"interpretation": str, # overvalued/undervalued/fair value
				"r_squared": float     # Model fit quality
			},
			"valuation": {
				"signal": str,         # BULLISH/BEARISH/NEUTRAL
				"cape": float,         # Current CAPE ratio
				"percentile": float,   # Historical percentile (0-100)
				"interpretation": str  # expensive/cheap/fair value
			}
		},
		"convergence": {               # Multi-model consensus
			"bullish_count": int,      # Number of bullish signals
			"bearish_count": int,      # Number of bearish signals
			"neutral_count": int,      # Number of neutral signals
			"total_models": int,       # Total models analyzed
			"conviction": str,         # High/Moderate/Low/None
			"primary_signal": str,     # BULLISH/BEARISH/NEUTRAL
			"interpretation": str      # Human-readable explanation
		}
	}

Example:
	>>> python convergence.py analyze SPY --macro-inputs "DX-Y.NYB,GC=F,^IXIC"
	{
		"symbol": "SPY",
		"convergence": {
			"conviction": "High",
			"primary_signal": "BULLISH",
			"interpretation": "3/3 models bullish - Strong consensus"
		}
	}

Use Cases:
	- High-conviction entry timing: Wait for 3/3 model convergence before entry
	- Exit timing: Reduce position when models diverge (conviction drops to Low)
	- Conviction scoring: Use model agreement as position sizing signal
	- Divergence detection: Identify when models contradict (Low conviction = avoid trade)

Notes:
	- Models are independent: Technical uses price only, Macro uses regression, Valuation uses CAPE
	- US-only limitation: Valuation model (CAPE) only works for US market (^GSPC)
	- Macro model requires --macro-inputs parameter (recommended: DX-Y.NYB,GC=F,^IXIC)
	- Conviction thresholds: High (3/3 or 2/2), Moderate (2/3), Low (mixed), None (1 signal or contradictory)
	- SidneyKim0 methodology: Convergence across uncorrelated models increases signal reliability

See Also:
	- macro/macro.py: Macroeconomic fair value regression model
	- technical/oscillators.py: RSI and other momentum indicators
	- cape.py: Cyclically Adjusted Price-to-Earnings ratio (US market valuation)
	- divergence.py: Detect model disagreements and conflicting signals
"""

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Support both standalone execution and module imports
try:
	from ..utils import output_json, safe_run
except ImportError:
	from utils import output_json, safe_run


def get_technical_signal(symbol: str, period: str = "1y") -> dict:
	"""Get Technical model signal based on RSI."""
	script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "technical", "__init__.py")
	try:
		result = subprocess.run(
			[sys.executable, script_path, "rsi", symbol, "--period", period],
			capture_output=True,
			text=True,
			timeout=30,
		)
		if result.returncode != 0:
			return {"error": f"Technical analysis failed: {result.stderr}"}

		data = json.loads(result.stdout)
		if "error" in data:
			return data

		rsi = data.get("current_rsi")
		if rsi is None:
			return {"error": "RSI calculation failed"}

		# Signal logic: RSI > 70 → BEARISH, RSI < 30 → BULLISH, else NEUTRAL
		if rsi >= 70:
			signal = "BEARISH"
			threshold = "overbought"
		elif rsi <= 30:
			signal = "BULLISH"
			threshold = "oversold"
		else:
			signal = "NEUTRAL"
			threshold = "neutral"

		return {
			"signal": signal,
			"rsi": rsi,
			"threshold": threshold,
			"date": data.get("date"),
		}
	except Exception as e:
		return {"error": f"Technical analysis error: {str(e)}"}


def get_macro_signal(symbol: str, inputs: str, period: str = "5y") -> dict:
	"""Get Macro model signal based on fair value residual z-score."""
	script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "macro", "macro.py")
	try:
		result = subprocess.run(
			[
				sys.executable,
				script_path,
				"fairvalue",
				symbol,
				"--inputs",
				inputs,
				"--period",
				period,
			],
			capture_output=True,
			text=True,
			timeout=30,
		)
		if result.returncode != 0:
			return {"error": f"Macro analysis failed: {result.stderr}"}

		data = json.loads(result.stdout)
		if "error" in data:
			return data

		# Extract z-score from current_analysis object
		current_analysis = data.get("current_analysis", {})
		zscore = current_analysis.get("residual_zscore")
		if zscore is None:
			return {"error": "Macro z-score calculation failed"}

		# Signal logic: zscore > 1 → BEARISH (overvalued), zscore < -1 → BULLISH (undervalued)
		if zscore > 1:
			signal = "BEARISH"
			interpretation = "overvalued vs macro model"
		elif zscore < -1:
			signal = "BULLISH"
			interpretation = "undervalued vs macro model"
		else:
			signal = "NEUTRAL"
			interpretation = "fair value range"

		# Extract r_squared from model object
		model_data = data.get("model", {})
		r_squared = model_data.get("r_squared")

		return {
			"signal": signal,
			"zscore": round(zscore, 2),
			"interpretation": interpretation,
			"r_squared": r_squared,
		}
	except Exception as e:
		return {"error": f"Macro analysis error: {str(e)}"}


def get_valuation_signal() -> dict:
	"""Get Valuation model signal based on CAPE percentile (US market only)."""
	script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cape.py")
	try:
		result = subprocess.run(
			[sys.executable, script_path, "get-percentile"],
			capture_output=True,
			text=True,
			timeout=30,
		)
		if result.returncode != 0:
			return {"error": f"CAPE analysis failed: {result.stderr}"}

		data = json.loads(result.stdout)
		if "error" in data:
			return data

		percentile = data.get("percentile")
		cape = data.get("current_cape")
		if percentile is None or cape is None:
			return {"error": "CAPE percentile calculation failed"}

		# Signal logic: percentile > 75 → BEARISH (expensive), percentile < 25 → BULLISH (cheap)
		if percentile > 75:
			signal = "BEARISH"
			interpretation = f"expensive (top {100 - percentile:.0f}% historically)"
		elif percentile < 25:
			signal = "BULLISH"
			interpretation = f"cheap (bottom {percentile:.0f}% historically)"
		else:
			signal = "NEUTRAL"
			interpretation = "fair value range"

		return {
			"signal": signal,
			"cape": cape,
			"percentile": round(percentile, 1),
			"interpretation": interpretation,
		}
	except Exception as e:
		return {"error": f"Valuation analysis error: {str(e)}"}


def calculate_convergence(models: dict) -> dict:
	"""Calculate convergence score from multiple models."""
	signals = []
	model_details = []

	for model_name, model_data in models.items():
		if "error" in model_data:
			continue
		signal = model_data.get("signal")
		if signal:
			signals.append(signal)
			model_details.append(f"{model_name} ({signal})")

	if not signals:
		return {
			"conviction": "None",
			"primary_signal": "UNKNOWN",
			"interpretation": "No valid model signals available",
		}

	bullish_count = signals.count("BULLISH")
	bearish_count = signals.count("BEARISH")
	neutral_count = signals.count("NEUTRAL")
	total_models = len(signals)

	# Determine primary signal and conviction
	if bullish_count == total_models:
		conviction = "High"
		primary_signal = "BULLISH"
		interpretation = f"{total_models}/{total_models} models bullish - Strong consensus"
	elif bearish_count == total_models:
		conviction = "High"
		primary_signal = "BEARISH"
		interpretation = f"{total_models}/{total_models} models bearish - Strong consensus"
	elif bullish_count >= 2 and bearish_count == 0:
		conviction = "Moderate"
		primary_signal = "BULLISH"
		interpretation = (
			f"{bullish_count}/{total_models} models bullish ({', '.join([m for m in model_details if 'BULLISH' in m])})"
		)
	elif bearish_count >= 2 and bullish_count == 0:
		conviction = "Moderate"
		primary_signal = "BEARISH"
		interpretation = (
			f"{bearish_count}/{total_models} models bearish ({', '.join([m for m in model_details if 'BEARISH' in m])})"
		)
	elif bullish_count > bearish_count:
		conviction = "Low"
		primary_signal = "BULLISH"
		interpretation = f"Mixed signals (Bullish: {bullish_count}, Bearish: {bearish_count}, Neutral: {neutral_count})"
	elif bearish_count > bullish_count:
		conviction = "Low"
		primary_signal = "BEARISH"
		interpretation = f"Mixed signals (Bullish: {bullish_count}, Bearish: {bearish_count}, Neutral: {neutral_count})"
	else:
		conviction = "None"
		primary_signal = "NEUTRAL"
		interpretation = f"No consensus (Bullish: {bullish_count}, Bearish: {bearish_count}, Neutral: {neutral_count})"

	return {
		"bullish_count": bullish_count,
		"bearish_count": bearish_count,
		"neutral_count": neutral_count,
		"total_models": total_models,
		"conviction": conviction,
		"primary_signal": primary_signal,
		"interpretation": interpretation,
	}


@safe_run
def cmd_analyze(args):
	"""Analyze multi-model convergence for a symbol."""
	models_to_run = [m.strip().lower() for m in args.models.split(",")]
	results = {"symbol": args.symbol, "date": None, "models": {}, "convergence": {}}

	# Run requested models
	if "technical" in models_to_run:
		technical_result = get_technical_signal(args.symbol, args.period)
		results["models"]["technical"] = technical_result
		if "date" in technical_result and results["date"] is None:
			results["date"] = technical_result["date"]

	if "macro" in models_to_run:
		if not args.macro_inputs:
			results["models"]["macro"] = {"error": "Macro inputs required (use --macro-inputs)"}
		else:
			macro_result = get_macro_signal(args.symbol, args.macro_inputs, args.period)
			results["models"]["macro"] = macro_result

	if "valuation" in models_to_run:
		valuation_result = get_valuation_signal()
		results["models"]["valuation"] = valuation_result

	# Calculate convergence
	results["convergence"] = calculate_convergence(results["models"])

	# Set date if not already set
	if results["date"] is None:
		from datetime import datetime

		results["date"] = datetime.now().strftime("%Y-%m-%d")

	output_json(results)


def main():
	parser = argparse.ArgumentParser(
		description="Multi-Model Convergence Analysis",
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	sub = parser.add_subparsers(dest="command", help="Subcommands")

	# Analyze command
	sp = sub.add_parser("analyze", help="Analyze multi-model convergence")
	sp.add_argument("symbol", help="Stock ticker symbol")
	sp.add_argument(
		"--models",
		default="technical,macro,valuation",
		help="Comma-separated models to run (default: technical,macro,valuation)",
	)
	sp.add_argument(
		"--macro-inputs",
		default="",
		help="Macro model inputs (e.g., 'DX-Y.NYB,GC=F,^IXIC')",
	)
	sp.add_argument("--period", default="5y", help="Data period (default: 5y)")
	sp.set_defaults(func=cmd_analyze)

	args = parser.parse_args()

	if not args.command:
		parser.print_help()
		return

	args.func(args)


if __name__ == "__main__":
	main()
