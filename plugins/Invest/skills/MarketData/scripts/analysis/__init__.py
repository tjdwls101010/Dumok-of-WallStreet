"""Analysis module."""

from .analysis import (
	cmd_analyst_price_targets,
	cmd_earnings_estimate,
	cmd_earnings_history,
	cmd_eps_revisions,
	cmd_eps_trend,
	cmd_growth_estimates,
	cmd_recommendations,
	cmd_recommendations_summary,
	cmd_revenue_estimate,
	cmd_sustainability,
	cmd_upgrades_downgrades,
)
from .convergence import cmd_analyze as cmd_convergence_analyze
from .divergence import (
	cmd_safe_haven,
	cmd_sector_divergence,
	cmd_yield_equity,
)

__all__ = [
	# Convergence
	"cmd_convergence_analyze",
	# Divergence
	"cmd_yield_equity",
	"cmd_safe_haven",
	"cmd_sector_divergence",
	# Analysis
	"cmd_analyst_price_targets",
	"cmd_earnings_estimate",
	"cmd_revenue_estimate",
	"cmd_earnings_history",
	"cmd_eps_trend",
	"cmd_eps_revisions",
	"cmd_growth_estimates",
	"cmd_recommendations",
	"cmd_recommendations_summary",
	"cmd_upgrades_downgrades",
	"cmd_sustainability",
]
