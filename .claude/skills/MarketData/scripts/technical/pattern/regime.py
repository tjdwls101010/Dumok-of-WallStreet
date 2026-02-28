#!/usr/bin/env python3
"""Identify current market regime based on multi-asset price movements and correlations.

Market regime detection analyzes relationships between assets (equities, gold, dollar, bonds)
to classify the current environment (risk-on, risk-off, safe haven, inflation hedge, etc.).

Args:
	symbols (str): Comma-separated asset symbols (e.g., "^GSPC,GC=F,DX-Y.NYB,^TNX")
		- ^GSPC or SPY: S&P 500 equity index
		- GC=F or GLD: Gold futures or ETF
		- DX-Y.NYB: US Dollar Index
		- ^TNX: 10-Year Treasury Yield
	--period (str): Historical data period (default: "6mo" = 6 months)
	--interval (str): Data interval (default: "1d" = daily)
	--lookback (int): Lookback period for recent changes (default: 30 days)

Returns:
	dict: {
		"symbols": list,                   # Asset symbols analyzed
		"lookback_days": int,              # Analysis period
		"period_changes": {
			"^GSPC": float,                # S&P 500 % change over lookback
			"GC=F": float,                 # Gold % change
			"DX-Y.NYB": float,             # Dollar % change
			"^TNX": float                  # Treasury yield change (basis points)
		},
		"detected_regime": str,            # Classified market regime
		"regime_signals": list,            # Supporting signals for classification
		"date": str                        # Analysis date
	}

Regime Classifications:
	- "Safe Haven (Fear)": Gold ↑ + Dollar ↑ (flight to safety, risk aversion)
	- "Inflation Hedge": Gold ↑ + Dollar ↓ (inflation concerns, weak currency)
	- "Risk-On Rally": Equity ↑ + Gold ↓ (growth optimism, risk appetite)
	- "Risk-Off / Deleveraging": Equity ↓↓ + Gold ↑ (panic selling, safe haven bid)
	- "Dollar Strength": Dollar ↑ + Gold ↓ (USD appreciation, commodity pressure)
	- "Unknown": No clear regime pattern detected

Example:
	>>> python regime.py regime "^GSPC,GC=F,DX-Y.NYB" --lookback 30
	{
		"symbols": ["^GSPC", "GC=F", "DX-Y.NYB"],
		"lookback_days": 30,
		"period_changes": {
			"^GSPC": -8.5,
			"GC=F": 5.2,
			"DX-Y.NYB": 3.1
		},
		"detected_regime": "Risk-Off / Deleveraging",
		"regime_signals": [
			"Equity -8.5%",
			"Gold +5.2% + Dollar +3.1%"
		],
		"date": "2026-02-05"
	}

	>>> python regime.py regime "SPY,GLD,DX-Y.NYB" --lookback 60
	{
		"symbols": ["SPY", "GLD", "DX-Y.NYB"],
		"period_changes": {
			"SPY": 12.3,
			"GLD": -3.5,
			"DX-Y.NYB": 2.1
		},
		"detected_regime": "Risk-On Rally",
		"regime_signals": [
			"Equity +12.3%"
		]
	}

Use Cases:
	- Identify macro environment shifts for portfolio allocation adjustments
	- Detect risk-off regimes early to reduce equity exposure
	- Confirm inflation hedge environments for commodities/real assets allocation
	- Track safe haven flows for defensive positioning
	- Validate trading strategies against current regime (trend-following in risk-on, mean reversion in risk-off)
	- Monitor regime transitions for tactical rebalancing opportunities

Notes:
	- Regime detection uses heuristic rules based on asset correlations and directional moves
	- Gold + Dollar both up typically indicates fear/flight to safety
	- Gold up + Dollar down suggests inflation concerns
	- Equity declines >5% trigger risk-off classification regardless of other assets
	- Lookback period affects regime sensitivity: shorter = more reactive, longer = more stable
	- Asset selection matters: include equities, gold, dollar, and yields for robust detection
	- Regime classifications are probabilistic, not deterministic (context still required)

See Also:
	- oscillators.py: RSI multi-timeframe analysis for regime momentum confirmation
	- pattern/similarity.py: Historical regime pattern matching
	- macro/cftc_cot.py: COT positioning data for regime validation
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pandas as pd
import yfinance as yf
from utils import output_json, safe_run


@safe_run
def cmd_regime(args):
	"""Identify current market regime based on multiple asset movements."""
	# Fetch multiple assets
	symbols = args.symbols.split(",")
	data_dict = {}

	for sym in symbols:
		ticker = yf.Ticker(sym.strip())
		hist = ticker.history(period=args.period, interval=args.interval)
		if not hist.empty:
			data_dict[sym.strip()] = hist["Close"]

	if len(data_dict) < 2:
		output_json({"error": "Need at least 2 symbols with data"})
		return

	# Create aligned DataFrame
	df = pd.DataFrame(data_dict)
	df = df.dropna()

	if len(df) < args.lookback:
		output_json({"error": "Insufficient overlapping data"})
		return

	# Calculate recent changes
	recent = df.tail(args.lookback)
	changes = {}
	for col in df.columns:
		start_price = recent[col].iloc[0]
		end_price = recent[col].iloc[-1]
		changes[col] = round((end_price - start_price) / start_price * 100, 2)

	# Determine regime based on common patterns
	regime = "Unknown"
	regime_signals = []

	# Check for common regime patterns
	gold_sym = next((s for s in symbols if "GC" in s or "GLD" in s.upper()), None)
	dollar_sym = next((s for s in symbols if "DX" in s), None)
	equity_sym = next((s for s in symbols if "^" in s or "SPY" in s.upper()), None)

	if gold_sym and dollar_sym:
		gold_chg = changes.get(gold_sym, 0)
		dollar_chg = changes.get(dollar_sym, 0)

		if gold_chg > 2 and dollar_chg > 1:
			regime = "Safe Haven (Fear)"
			regime_signals.append(f"Gold +{gold_chg}% + Dollar +{dollar_chg}%")
		elif gold_chg > 2 and dollar_chg < -1:
			regime = "Inflation Hedge"
			regime_signals.append(f"Gold +{gold_chg}% + Dollar {dollar_chg}%")
		elif gold_chg < -2 and dollar_chg > 1:
			regime = "Risk-On / Dollar Strength"
			regime_signals.append(f"Gold {gold_chg}% + Dollar +{dollar_chg}%")

	if equity_sym:
		equity_chg = changes.get(equity_sym, 0)
		if equity_chg < -5:
			regime = "Risk-Off / Deleveraging"
			regime_signals.append(f"Equity {equity_chg}%")
		elif equity_chg > 5 and regime == "Unknown":
			regime = "Risk-On Rally"
			regime_signals.append(f"Equity +{equity_chg}%")

	result = {
		"symbols": symbols,
		"lookback_days": args.lookback,
		"period_changes": changes,
		"detected_regime": regime,
		"regime_signals": regime_signals,
		"date": str(df.index[-1].date()),
	}
	output_json(result)
