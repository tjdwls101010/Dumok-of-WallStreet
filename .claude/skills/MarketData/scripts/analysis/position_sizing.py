#!/usr/bin/env python3
"""Position Sizing Calculator: risk-based position sizing for Minervini SEPA methodology.

Calculates optimal position sizes based on account risk parameters, stop-loss levels,
and mathematical expectation. Includes pyramid entry planning and portfolio-level
risk management per Mark Minervini's money management rules.

Commands:
		calculate: Calculate position size based on risk parameters
		pyramid: Generate pyramid entry plan (2% + 2% + 1% scaling)
		expectation: Calculate mathematical expectation of a trading system

Args:
		For calculate:
				--account-size (float): Total account value in dollars
				--risk-per-trade (float): Risk per trade as decimal (default: 0.005 = 0.5%)
				--stop-loss-pct (float): Stop-loss distance as percent (default: 7)
				--entry-price (float): Planned entry price

		For pyramid:
				--account-size (float): Total account value
				--entry-price (float): Initial entry price
				--stop-loss-pct (float): Stop-loss distance percent (default: 7)

		For expectation:
				--win-rate (float): Win rate as decimal (e.g., 0.5 = 50%)
				--avg-gain (float): Average gain per winning trade as percent
				--avg-loss (float): Average loss per losing trade as percent

Returns:
		For calculate:
				dict: {
						"position_size_shares": int,
						"position_value": float,
						"risk_amount": float,
						"stop_loss_price": float,
						"reward_risk_ratio": float,
						"portfolio_pct": float
				}

		For pyramid:
				dict: {
						"pyramid_plan": [
								{"entry": int, "shares": int, "price": float, "cumulative_pct": float}
						],
						"total_shares": int,
						"average_cost": float,
						"total_value": float
				}

		For expectation:
				dict: {
						"mathematical_expectation": float,
						"expectation_per_dollar": float,
						"breakeven_win_rate": float,
						"kelly_fraction": float,
						"system_quality": str
				}

Example:
		>>> python position_sizing.py calculate --account-size 100000 --entry-price 150 --stop-loss-pct 7
		{
				"position_size_shares": 9,
				"position_value": 1350.00,
				"risk_amount": 500.00,
				"stop_loss_price": 139.50,
				"portfolio_pct": 1.35
		}

		>>> python position_sizing.py pyramid --account-size 100000 --entry-price 150
		{
				"pyramid_plan": [
						{"entry": 1, "shares": 13, "price": 150.00, "pct_of_account": 2.0},
						{"entry": 2, "shares": 13, "price": 153.75, "pct_of_account": 2.0},
						{"entry": 3, "shares": 6, "price": 157.59, "pct_of_account": 1.0}
				],
				"total_shares": 32,
				"average_cost": 152.78
		}

		>>> python position_sizing.py expectation --win-rate 0.5 --avg-gain 15 --avg-loss 7
		{
				"mathematical_expectation": 4.0,
				"breakeven_win_rate": 31.82,
				"system_quality": "good"
		}

Use Cases:
		- Calculate position size before entering a SEPA trade
		- Plan pyramid entries for scaling into winning positions
		- Evaluate trading system quality via mathematical expectation
		- Ensure per-trade risk stays within Minervini guidelines

Notes:
		- Minervini recommends 0.5-1.0% risk per trade
		- Maximum stop-loss: 10% (absolute maximum, 7-8% typical)
		- Pyramid: 2% + 2% + 1% of account value scaling
		- Never add to losing positions (no averaging down)
		- 4-6 concentrated positions is ideal, max 20
		- Move stop to breakeven when up 3x stop amount
		- Mathematical expectation must be positive for system validity

See Also:
		- trend_template.py: Entry qualification before position sizing
		- vcp.py: Pivot price for entry point determination
		- base_count.py: Base number affects position size (smaller for late bases)
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import output_json, safe_run


@safe_run
def cmd_calculate(args):
	"""Calculate position size based on risk parameters."""
	account_size = args.account_size
	risk_per_trade = args.risk_per_trade
	stop_loss_pct = args.stop_loss_pct / 100  # Convert to decimal
	entry_price = args.entry_price

	# Risk amount in dollars
	risk_amount = account_size * risk_per_trade

	# Position size (shares)
	risk_per_share = entry_price * stop_loss_pct
	if risk_per_share <= 0:
		output_json({"error": "Stop-loss percentage must be positive"})
		return

	position_shares = int(risk_amount / risk_per_share)
	position_value = round(position_shares * entry_price, 2)
	portfolio_pct = round(position_value / account_size * 100, 2)

	# Stop-loss price
	stop_loss_price = round(entry_price * (1 - stop_loss_pct), 2)

	# Breakeven stop (move stop here when up 3x stop amount)
	breakeven_trigger_price = round(entry_price * (1 + stop_loss_pct * 3), 2)

	# Suggested target based on reward/risk ratios
	target_2r = round(entry_price + (entry_price - stop_loss_price) * 2, 2)
	target_3r = round(entry_price + (entry_price - stop_loss_price) * 3, 2)

	output_json(
		{
			"account_size": account_size,
			"risk_per_trade_pct": round(risk_per_trade * 100, 2),
			"risk_amount": round(risk_amount, 2),
			"entry_price": entry_price,
			"stop_loss_pct": args.stop_loss_pct,
			"stop_loss_price": stop_loss_price,
			"position_size_shares": position_shares,
			"position_value": position_value,
			"portfolio_pct": portfolio_pct,
			"risk_per_share": round(risk_per_share, 2),
			"breakeven_trigger_price": breakeven_trigger_price,
			"targets": {
				"2R_target": target_2r,
				"3R_target": target_3r,
			},
			"rules": {
				"max_stop_loss": "10% absolute maximum",
				"move_stop_to_breakeven": f"When price reaches ${breakeven_trigger_price} (3x stop amount)",
				"never_average_down": True,
			},
		}
	)


@safe_run
def cmd_pyramid(args):
	"""Generate pyramid entry plan (2% + 2% + 1% scaling)."""
	account_size = args.account_size
	entry_price = args.entry_price
	stop_loss_pct = args.stop_loss_pct / 100

	# Pyramid allocation: 2% + 2% + 1% of account
	allocations = [
		{"entry": 1, "pct_of_account": 2.0, "price_advance_pct": 0},
		{"entry": 2, "pct_of_account": 2.0, "price_advance_pct": 2.5},
		{"entry": 3, "pct_of_account": 1.0, "price_advance_pct": 5.0},
	]

	plan = []
	total_shares = 0
	total_cost = 0

	for alloc in allocations:
		price = round(entry_price * (1 + alloc["price_advance_pct"] / 100), 2)
		dollar_amount = account_size * (alloc["pct_of_account"] / 100)
		shares = int(dollar_amount / price)

		if shares > 0:
			plan.append(
				{
					"entry": alloc["entry"],
					"shares": shares,
					"price": price,
					"dollar_amount": round(shares * price, 2),
					"pct_of_account": alloc["pct_of_account"],
					"price_advance_pct": alloc["price_advance_pct"],
				}
			)
			total_shares += shares
			total_cost += shares * price

	average_cost = round(total_cost / total_shares, 2) if total_shares > 0 else 0
	total_value = round(total_cost, 2)
	total_pct = round(total_value / account_size * 100, 2)

	# Stop-loss for full position
	stop_price = round(entry_price * (1 - stop_loss_pct), 2)
	max_loss = round((average_cost - stop_price) * total_shares, 2)
	max_loss_pct = round(max_loss / account_size * 100, 2)

	output_json(
		{
			"account_size": account_size,
			"initial_entry_price": entry_price,
			"stop_loss_pct": args.stop_loss_pct,
			"stop_loss_price": stop_price,
			"pyramid_plan": plan,
			"total_shares": total_shares,
			"average_cost": average_cost,
			"total_value": total_value,
			"total_portfolio_pct": total_pct,
			"max_loss_at_stop": max_loss,
			"max_loss_pct_of_account": max_loss_pct,
			"rules": {
				"only_add_to_winners": "Each entry must be at higher price than previous",
				"never_average_down": True,
				"scale": "2% + 2% + 1% of account value",
				"max_position": "5% of account for full pyramid position",
			},
		}
	)


@safe_run
def cmd_expectation(args):
	"""Calculate mathematical expectation of a trading system."""
	win_rate = args.win_rate
	avg_gain = args.avg_gain
	avg_loss = args.avg_loss

	# Mathematical expectation
	# E = (Win% x Avg Win) - (Loss% x Avg Loss)
	loss_rate = 1 - win_rate
	expectation = (win_rate * avg_gain) - (loss_rate * avg_loss)

	# Expectation per dollar risked
	expectation_per_dollar = round(expectation / avg_loss, 3) if avg_loss > 0 else 0

	# Breakeven win rate (at what win% does E = 0?)
	# 0 = (W * avg_gain) - ((1-W) * avg_loss)
	# W * avg_gain = avg_loss - W * avg_loss
	# W * (avg_gain + avg_loss) = avg_loss
	# W = avg_loss / (avg_gain + avg_loss)
	breakeven_wr = round(avg_loss / (avg_gain + avg_loss) * 100, 2) if (avg_gain + avg_loss) > 0 else 50

	# Kelly Criterion (optimal fraction to bet)
	# f* = (bp - q) / b where b = avg_gain/avg_loss, p = win_rate, q = 1 - win_rate
	b = avg_gain / avg_loss if avg_loss > 0 else 1
	kelly = round((b * win_rate - loss_rate) / b, 4) if b > 0 else 0

	# System quality
	if expectation > 3:
		quality = "excellent"
	elif expectation > 1:
		quality = "good"
	elif expectation > 0:
		quality = "marginal"
	else:
		quality = "negative"

	# Gain/Loss ratio
	gain_loss_ratio = round(avg_gain / avg_loss, 2) if avg_loss > 0 else 0

	# Recovery factor table
	recovery_table = [
		{"loss_pct": 5, "recovery_needed_pct": 5.3},
		{"loss_pct": 10, "recovery_needed_pct": 11.1},
		{"loss_pct": 20, "recovery_needed_pct": 25.0},
		{"loss_pct": 30, "recovery_needed_pct": 42.9},
		{"loss_pct": 40, "recovery_needed_pct": 66.7},
		{"loss_pct": 50, "recovery_needed_pct": 100.0},
		{"loss_pct": 75, "recovery_needed_pct": 300.0},
		{"loss_pct": 90, "recovery_needed_pct": 900.0},
	]

	output_json(
		{
			"win_rate_pct": round(win_rate * 100, 1),
			"avg_gain_pct": avg_gain,
			"avg_loss_pct": avg_loss,
			"gain_loss_ratio": gain_loss_ratio,
			"mathematical_expectation": round(expectation, 2),
			"expectation_per_dollar_risked": expectation_per_dollar,
			"breakeven_win_rate_pct": breakeven_wr,
			"kelly_fraction": kelly,
			"system_quality": quality,
			"interpretation": {
				"expectation": f"On average, you gain {expectation:.2f}% per trade",
				"breakeven": f"You need {breakeven_wr}% win rate to break even with this gain/loss ratio",
				"kelly": f"Kelly suggests risking {kelly * 100:.1f}% per trade (use half-Kelly: {kelly * 50:.1f}%)",
			},
			"geometric_loss_impact": recovery_table,
		}
	)


def main():
	parser = argparse.ArgumentParser(description="Position Sizing Calculator")
	sub = parser.add_subparsers(dest="command", required=True)

	# calculate
	sp = sub.add_parser("calculate", help="Calculate position size")
	sp.add_argument("--account-size", type=float, required=True, help="Account size in dollars")
	sp.add_argument(
		"--risk-per-trade", type=float, default=0.005, help="Risk per trade as decimal (default: 0.005 = 0.5%%)"
	)
	sp.add_argument("--stop-loss-pct", type=float, default=7.0, help="Stop-loss distance %% (default: 7)")
	sp.add_argument("--entry-price", type=float, required=True, help="Entry price")
	sp.set_defaults(func=cmd_calculate)

	# pyramid
	sp = sub.add_parser("pyramid", help="Generate pyramid entry plan")
	sp.add_argument("--account-size", type=float, required=True, help="Account size in dollars")
	sp.add_argument("--entry-price", type=float, required=True, help="Initial entry price")
	sp.add_argument("--stop-loss-pct", type=float, default=7.0, help="Stop-loss distance %% (default: 7)")
	sp.set_defaults(func=cmd_pyramid)

	# expectation
	sp = sub.add_parser("expectation", help="Calculate mathematical expectation")
	sp.add_argument("--win-rate", type=float, required=True, help="Win rate as decimal (e.g., 0.5)")
	sp.add_argument("--avg-gain", type=float, required=True, help="Average gain per winning trade (%%)")
	sp.add_argument("--avg-loss", type=float, required=True, help="Average loss per losing trade (%%)")
	sp.set_defaults(func=cmd_expectation)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
