#!/usr/bin/env python3
"""Finviz screening preset definitions and criteria filter sets.

This module contains predefined filter configurations for stock screening using finvizfinance.
Each preset represents a specific investment strategy or screening methodology.

Preset Categories:
- Value Investing: buffet_like, cheap_dividend, value_stocks
- Growth Investing: canslim, growth_stocks
- Technical Analysis: golden_cross, large_cap_rsi20, large_cap_rsi80
- Minervini SEPA: minervini_leaders, minervini_breakout, minervini_stage2
- Serenity Supply Chain: serenity_bottleneck, serenity_neocloud

Criteria Filters:
- CRITERIA_FILTERS dict: Reusable filter sets for sector-screen and industry-screen commands
- Categories: growth, value, momentum, dividend, quality
"""

# Preset filter definitions for finvizfinance
# Keys must match finvizfinance's expected filter names exactly
PRESETS = {
	"buffet_like": {
		"description": "Buffet-style value investing: low debt, high ROI, positive growth",
		"filters": {
			"Market Cap.": "+Mid (over $2bln)",
			"Dividend Yield": "Positive (>0%)",
			"EPS growthnext 5 years": "Positive (>0%)",
			"Debt/Equity": "Under 0.5",
			"Price/Free Cash Flow": "Under 50",
			"Sales growthpast 5 years": "Positive (>0%)",
			"Return on Investment": "Over +15%",
			"P/B": "Under 3",
		},
	},
	"canslim": {
		"description": "CAN SLIM growth stocks: high EPS growth, strong technicals",
		"filters": {
			"Average Volume": "Over 200K",
			"Float": "Under 50M",
			"EPS growththis year": "Over 20%",
			"EPS growthnext year": "Over 20%",
			"EPS growthqtr over qtr": "Over 20%",
			"Sales growthqtr over qtr": "Over 20%",
			"EPS growthpast 5 years": "Over 20%",
			"Gross Margin": "Positive (>0%)",
			"Return on Equity": "Positive (>0%)",
			"InstitutionalOwnership": "Over 20%",
			"20-Day Simple Moving Average": "Price above SMA20",
			"50-Day Simple Moving Average": "Price above SMA50",
			"200-Day Simple Moving Average": "Price above SMA200",
			"52-Week High/Low": "0-10% below High",
		},
	},
	"golden_cross": {
		"description": "Golden cross: 50-day SMA crosses above 200-day SMA",
		"filters": {
			"50-Day Simple Moving Average": "SMA50 crossed SMA200 above",
		},
	},
	"cheap_dividend": {
		"description": "Cheap dividend stocks: oversold with high yield and low P/E",
		"filters": {
			"Dividend Yield": "Over 3%",
			"P/E": "Under 10",
			"P/B": "Under 2",
		},
		"signal": "Oversold",
	},
	"large_cap_rsi20": {
		"description": "Large cap oversold: Market cap >$10B with RSI under 20",
		"filters": {
			"Market Cap.": "+Large (over $10bln)",
			"RSI (14)": "Oversold (20)",
		},
	},
	"large_cap_rsi80": {
		"description": "Large cap overbought: Market cap >$10B with RSI over 80",
		"filters": {
			"Market Cap.": "+Large (over $10bln)",
			"RSI (14)": "Overbought (80)",
		},
	},
	"growth_stocks": {
		"description": "Growth stocks: high EPS growth, low debt, strong momentum",
		"filters": {
			"Market Cap.": "+Micro (over $50mln)",
			"Average Volume": "Over 300K",
			"Country": "USA",
			"Price": "Over $10",
			"EPS growthnext 5 years": "Over 15%",
			"Debt/Equity": "Under 0.5",
			"PEG": "Under 2",
			"EPS growththis year": "Over 15%",
			"EPS growthqtr over qtr": "Over 15%",
			"EPS growthpast 5 years": "Over 15%",
			"20-Day Simple Moving Average": "SMA20 above SMA200",
			"50-Day Simple Moving Average": "SMA50 above SMA200",
		},
	},
	"value_stocks": {
		"description": "Value stocks: low P/B, low P/E, with dividends",
		"filters": {
			"P/B": "Under 2",
			"P/E": "Under 10",
			"Dividend Yield": "Over 2%",
			"EPS growthpast 5 years": "Over 15%",
			"PEG": "Low (<1)",
		},
	},
	"minervini_leaders": {
		"description": "Minervini SEPA leaders: strong yearly/quarterly performance near 52W high with EPS growth",
		"filters": {
			"Performance": "Year +20%",
			"Performance 2": "Quarter +10%",
			"52-Week High/Low": "0-10% below High",
			"EPS growthqtr over qtr": "Over 25%",
			"Average Volume": "Over 200K",
			"200-Day Simple Moving Average": "Price above SMA200",
		},
	},
	"minervini_breakout": {
		"description": "Minervini breakout candidates: new highs with volume surge and EPS growth",
		"filters": {
			"52-Week High/Low": "New High",
			"Average Volume": "Over 200K",
			"EPS growthqtr over qtr": "Over 20%",
			"20-Day Simple Moving Average": "Price above SMA20",
			"50-Day Simple Moving Average": "Price above SMA50",
			"200-Day Simple Moving Average": "Price above SMA200",
		},
		"signal": "New High",
	},
	"minervini_stage2": {
		"description": "Minervini Stage 2 candidates: price above all key MAs with positive RS",
		"filters": {
			"200-Day Simple Moving Average": "Price above SMA200",
			"50-Day Simple Moving Average": "SMA50 above SMA200",
			"20-Day Simple Moving Average": "Price above SMA20",
			"Performance": "Year +20%",
			"Average Volume": "Over 200K",
			"EPS growththis year": "Over 20%",
		},
	},
	"serenity_bottleneck": {
		"description": "Serenity supply chain bottleneck: high margin, high growth, mid-cap+",
		"filters": {
			"Market Cap.": "+Small (over $300mln)",
			"Gross Margin": "Over 50%",
			"Sales growthqtr over qtr": "Over 30%",
			"EPS growthqtr over qtr": "Over 20%",
			"InstitutionalOwnership": "Over 30%",
			"Average Volume": "Over 200K",
		},
	},
	"serenity_neocloud": {
		"description": "Serenity neocloud/AI infra: high growth + high margin tech",
		"filters": {
			"Market Cap.": "+Small (over $300mln)",
			"Sector": "Technology",
			"Gross Margin": "Over 60%",
			"Sales growthqtr over qtr": "Over 50%",
			"Average Volume": "Over 300K",
			"200-Day Simple Moving Average": "Price above SMA200",
		},
	},
}

# Criteria filter sets for sector-screen and industry-screen commands.
# Each criteria maps to a dict of finvizfinance filter key-value pairs.
# Used by finviz.py cmd_sector_screen and cmd_industry_screen.
CRITERIA_FILTERS = {
	"growth": {
		"EPS growththis year": "Over 20%",
		"EPS growthnext year": "Over 10%",
		"Sales growthqtr over qtr": "Over 10%",
	},
	"value": {
		"P/E": "Under 20",
		"P/B": "Under 3",
		"PEG": "Low (<1)",
	},
	"momentum": {
		"20-Day Simple Moving Average": "Price above SMA20",
		"50-Day Simple Moving Average": "Price above SMA50",
		"52-Week High/Low": "0-10% below High",
	},
	"dividend": {
		"Dividend Yield": "Over 2%",
		"Payout Ratio": "Under 50%",
	},
	"quality": {
		"Return on Equity": "Over +15%",
		"Debt/Equity": "Under 1",
		"EPS growthpast 5 years": "Positive (>0%)",
	},
}
