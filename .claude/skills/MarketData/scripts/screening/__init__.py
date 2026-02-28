"""Screening module - Finviz stock screener.

This module provides stock screening functionality using Finviz data sources.
It includes predefined screening presets and sector/industry group analysis.

Available Commands:
- cmd_screen: Screen stocks using predefined presets
- cmd_groups: Get sector/industry group performance comparison
- cmd_presets: List available screening presets
- cmd_sector_screen: Screen stocks within a specific sector

Available Data:
- PRESETS: Predefined screening filter configurations
- SECTOR_FILTERS: Sector filter mappings for finvizfinance screener
- GROUPS_DICT: Group mappings for finvizfinance
"""

from .finviz import (
	GROUPS_DICT,
	SECTOR_FILTERS,
	cmd_groups,
	cmd_presets,
	cmd_screen,
	cmd_sector_screen,
)
from .finviz_presets import PRESETS

__all__ = [
	# Commands
	"cmd_screen",
	"cmd_groups",
	"cmd_presets",
	"cmd_sector_screen",
	# Data
	"PRESETS",
	"SECTOR_FILTERS",
	"GROUPS_DICT",
]
