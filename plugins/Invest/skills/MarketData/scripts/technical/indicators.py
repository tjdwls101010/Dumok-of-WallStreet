#!/usr/bin/env python3
"""Technical indicator calculation functions for market data analysis.

This module provides common technical indicator calculations used across
multiple MarketData scripts including RSI, SMA, EMA, Bollinger Bands, and MACD.

Functions serve as building blocks for oscillators.py, trend.py, and pattern analysis scripts.
All functions accept pandas Series and return pandas Series for composability.

Args:
	For calculate_rsi:
		prices (pd.Series): Price series (typically Close prices)
		period (int): RSI calculation period (default: 14 = standard Wilder period)

	For calculate_sma:
		prices (pd.Series): Price series
		period (int): Moving average window (e.g., 20, 50, 200)

	For calculate_ema:
		prices (pd.Series): Price series
		period (int): EMA span (e.g., 9, 12, 26)

	For calculate_bollinger_bands:
		prices (pd.Series): Price series
		period (int): SMA period for middle band (default: 20)
		std_dev (float): Standard deviation multiplier (default: 2.0)

	For calculate_macd:
		prices (pd.Series): Price series
		fast (int): Fast EMA period (default: 12)
		slow (int): Slow EMA period (default: 26)
		signal (int): Signal line EMA period (default: 9)

Returns:
	For calculate_rsi:
		pd.Series: RSI values (0-100 scale)

	For calculate_sma:
		pd.Series: Simple moving average values

	For calculate_ema:
		pd.Series: Exponential moving average values

	For calculate_bollinger_bands:
		tuple: (sma, upper_band, lower_band) as pd.Series

	For calculate_macd:
		tuple: (macd_line, signal_line, histogram) as pd.Series

Example:
	>>> import yfinance as yf
	>>> data = yf.Ticker("AAPL").history(period="1y")
	>>> prices = data["Close"]
	>>> rsi = calculate_rsi(prices, 14)
	>>> print(rsi.tail(3))
	2026-02-03    72.45
	2026-02-04    68.30
	2026-02-05    65.80
	dtype: float64

	>>> sma_20 = calculate_sma(prices, 20)
	>>> ema_12 = calculate_ema(prices, 12)
	>>> sma, upper, lower = calculate_bollinger_bands(prices, 20, 2.0)
	>>> macd, signal, hist = calculate_macd(prices, 12, 26, 9)

Use Cases:
	- Build custom technical analysis scripts combining multiple indicators
	- Create composite signals (e.g., RSI + MACD + Bollinger Bands)
	- Backtest trading strategies using standardized indicator calculations
	- Generate alerts when indicators reach specific thresholds
	- Compare indicator values across different assets or timeframes

Notes:
	- RSI uses Wilder's smoothing method (exponential moving average with alpha=1/period)
	- All indicators return NaN for initial periods where calculation is impossible
	- EMA gives more weight to recent prices compared to SMA
	- Bollinger Bands assume normal distribution (2σ ≈ 95% confidence interval)
	- MACD histogram = MACD line - Signal line (positive = bullish momentum)
	- Functions are composable: output Series can be input to other functions

See Also:
	- oscillators.py: Command-line interface for RSI and MACD analysis
	- trend.py: Command-line interface for moving averages and Bollinger Bands
	- pattern/helpers.py: Additional utility functions for pattern analysis
"""

import pandas as pd


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
	"""Calculate Relative Strength Index using Wilder's smoothing method.
    
	RSI = 100 - (100 / (1 + RS))
	where RS = Average Gain / Average Loss over the period.
    
	Args:
		prices: Price series (typically Close prices)
		period: RSI calculation period (default: 14)
    
	Returns:
		pd.Series: RSI values on 0-100 scale
	"""
	delta = prices.diff()
	gain = delta.where(delta > 0, 0.0)
	loss = (-delta).where(delta < 0, 0.0)

	# Use exponential moving average (Wilder's smoothing)
	avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
	avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

	rs = avg_gain / avg_loss
	rsi = 100 - (100 / (1 + rs))
	return rsi


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
	"""Calculate Simple Moving Average.
    
	SMA = Sum of prices over period / period
    
	Args:
		prices: Price series
		period: Moving average window
    
	Returns:
		pd.Series: Simple moving average values
	"""
	return prices.rolling(window=period).mean()


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
	"""Calculate Exponential Moving Average.
    
	EMA gives more weight to recent prices using exponential decay.
    
	Args:
		prices: Price series
		period: EMA span (smoothing factor = 2/(period+1))
    
	Returns:
		pd.Series: Exponential moving average values
	"""
	return prices.ewm(span=period, adjust=False).mean()


def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2.0):
	"""Calculate Bollinger Bands.
    
	Middle Band = SMA
	Upper Band = SMA + (std_dev * standard deviation)
	Lower Band = SMA - (std_dev * standard deviation)
    
	Args:
		prices: Price series
		period: SMA period for middle band (default: 20)
		std_dev: Standard deviation multiplier (default: 2.0)
    
	Returns:
		tuple: (sma, upper_band, lower_band) as pd.Series
	"""
	sma = calculate_sma(prices, period)
	std = prices.rolling(window=period).std()
	upper = sma + (std * std_dev)
	lower = sma - (std * std_dev)
	return sma, upper, lower


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
	"""Calculate MACD (Moving Average Convergence Divergence).
    
	MACD Line = Fast EMA - Slow EMA
	Signal Line = EMA of MACD Line
	Histogram = MACD Line - Signal Line
    
	Args:
		prices: Price series
		fast: Fast EMA period (default: 12)
		slow: Slow EMA period (default: 26)
		signal: Signal line EMA period (default: 9)
    
	Returns:
		tuple: (macd_line, signal_line, histogram) as pd.Series
	"""
	ema_fast = calculate_ema(prices, fast)
	ema_slow = calculate_ema(prices, slow)
	macd_line = ema_fast - ema_slow
	signal_line = calculate_ema(macd_line, signal)
	histogram = macd_line - signal_line
	return macd_line, signal_line, histogram
