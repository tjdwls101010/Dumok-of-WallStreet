# Docstring Enhancement Guidelines

## Core Principles

1. **Preserve Existing Content**: Don't delete good explanations
2. **Augment, Don't Replace**: Add missing sections only
3. **Follow Template**: Use consistent structure
4. **Real Examples**: Use actual ticker symbols, realistic values

## Required Sections (Must Have)

### Args
- Include type hints in parentheses
- Add example values: (e.g., "AAPL", 252)
- Explain defaults: (default: 252 = 1 year)

### Returns
- Show actual JSON structure with comments
- Include all fields with descriptions
- Use realistic values in schema

### Example
- Use executable code format
- Show actual input → output
- Use common tickers (AAPL, SPY, ^GSPC)

## Recommended Sections (Should Have 2+)

### Use Cases
- 2-3 bullet points
- Specific scenarios, not generic
- Include when NOT to use (if relevant)

### Notes
- Edge cases (e.g., market holidays)
- Performance tips (e.g., cache results)
- Data quality issues (e.g., pre-market data)

### See Also
- Related functions in same category
- Alternative approaches in other categories

## Time Estimates

- **Already good docstring** (like gbm.py): 5 minutes
  - Add Example, Use Cases
  - Enhance Returns schema

- **Basic docstring** (like extremes.py): 10 minutes
  - Add Returns, Example
  - Add Use Cases, Notes

- **No docstring**: 15 minutes
  - Write from scratch using template

## Quality Checklist

- [ ] One-line summary is clear and specific
- [ ] Args include example values
- [ ] Returns shows actual JSON structure
- [ ] Example is copy-pasteable
- [ ] Use Cases are specific scenarios (not generic)
- [ ] Cross-references added (See Also)

## Common Patterns by Category

### Statistics (zscore, percentile, correlation)
- Use Cases: Overbought/oversold, mean reversion
- Notes: Lookback window affects sensitivity
- See Also: Cross-reference other statistical functions

### Technical (oscillators, trend)
- Use Cases: Entry/exit signals, trend confirmation
- Notes: Timeframe selection guidance
- See Also: Combine multiple indicators

### Data Sources (price, info, actions)
- Use Cases: Data collection workflows
- Notes: API rate limits, data freshness
- See Also: Related data retrieval functions

### Analysis (convergence, divergence)
- Use Cases: Multi-asset relationships, regime detection
- Notes: When correlations break down
- See Also: Individual indicator functions

### Backtest (conditional, extreme_reversals)
- Use Cases: Strategy validation, parameter tuning
- Notes: Survivorship bias, overfitting risks
- See Also: Related backtesting approaches
