"""Statistical analysis modules for MarketData skill."""

from .cointegration import cmd_cointegration
from .correlation import cmd_correlation, cmd_correlation_fx
from .distribution import cmd_distribution
from .extremes import cmd_extremes
from .multi_correlation import cmd_multi_correlation
from .percentile import cmd_percentile
from .zscore import cmd_zscore

__all__ = [
	"cmd_zscore",
	"cmd_percentile",
	"cmd_correlation",
	"cmd_correlation_fx",
	"cmd_extremes",
	"cmd_distribution",
	"cmd_multi_correlation",
	"cmd_cointegration",
]
