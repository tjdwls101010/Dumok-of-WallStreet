---
name: marketdata
description: Multi-source financial data collection skill for stock prices, macro data, SEC filings, and market analysis. Integrates YFinance, FRED, SEC EDGAR, Finviz, and CFTC data sources.
allowed-tools: Bash, Read
---

# MarketData Collection Skill

Multi-source financial data retrieval system providing comprehensive market analysis capabilities through autonomous data collection. All scripts output JSON to stdout with `{"error": "message"}` for errors.

**Data Sources**: YFinance (stocks), FRED (macro), SEC EDGAR (filings), Finviz (screening), CFTC (futures), YCharts (CAPE), CBOE (IV/options chains/VIX futures)

**Setup**:
```bash
cd skills/MarketData/scripts
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Environment Bootstrap Protocol

### First-time Setup (automatic)
Before running any script, verify the following:
1. Check if `.venv` exists → if not:
   ```bash
   cd skills/MarketData/scripts
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

## Progressive Disclosure Architecture

This skill uses **2-level Progressive Disclosure**:

- **Level 1: SKILL.md** (this file) - Complete function catalog with all categories
- **Level 2: Python Docstrings** - Detailed documentation extracted via `tools/extract_docstring.py`

See **Script Execution Safety Protocol** below for mandatory discovery and execution rules.

### Navigation Flow

```
Need RSI? → SKILL.md Technical section → find oscillators.py → python tools/extract_docstring.py scripts/technical/oscillators.py
```

## Function Catalog

### Core Analysis

#### Statistics

Z-score, percentile, correlation, extremes

| Function | Description | Script |
|----------|-------------|--------|
| `cointegration` | Test cointegration between two symbols using Engle-Granger method for pairs trading | `statistics/cointegration.py` |
| `correlation` | Calculate correlation between two symbols to identify relationship strength and regime changes | `statistics/correlation.py` |
| `distribution` | Calculate distribution statistics for returns to analyze risk, reward, and tail characteristics | `statistics/distribution.py` |
| `extremes` | Find extreme events beyond threshold sigma to identify historical tail risk events | `statistics/extremes.py` |
| `multi_correlation` | Calculate correlation matrix for multiple symbols to identify relationship patterns and pair rankings | `statistics/multi_correlation.py` |
| `multi_extremes` | Multi-Asset Extreme Detection - Identify simultaneous extreme z-scores across multiple assets | `statistics/multi_extremes.py` |
| `percentile` | Calculate percentile rank for stock price or returns to identify relative positioning | `statistics/percentile.py` |
| `zscore` | Calculate z-score for stock price or returns to identify statistical overbought/oversold levels | `statistics/zscore.py` |

#### Technical

RSI, MACD, SMA, EMA, Bollinger Bands, Stage Analysis, RS Ranking, VCP, Base Counting, Volume Analysis, Pocket Pivot, Low Cheat, Tight Closes

| Function | Description | Script |
|----------|-------------|--------|
| `base_count` | Track base number within Stage 2 advance with pattern classification and risk assessment | `technical/base_count.py` |
| `indicators` | Technical indicator calculation functions for market data analysis | `technical/indicators.py` |
| `low_cheat` | Low cheat setup detection: tight consolidation below pivot for reduced-risk entry | `technical/low_cheat.py` |
| `oscillators` | Calculate momentum oscillators including RSI and MACD for overbought/oversold detection | `technical/oscillators.py` |
| `pocket_pivot` | Pocket pivot detection: institutional buying signals within base formations | `technical/pocket_pivot.py` |
| `rs_ranking` | Dual-approach RS ranking: YFinance score calculation (0-99) and Finviz high-RS screening | `technical/rs_ranking.py` |
| `slope` | 20-day rolling price slope normalization and RSI derivative momentum signals | `technical/slope.py` |
| `stage_analysis` | Minervini Stage 1-4 classification with confidence scoring and transition signal detection | `technical/stage_analysis.py` |
| `tight_closes` | Tight close cluster detection (daily/weekly): supply dryup confirmation near pivots | `technical/tight_closes.py` |
| `trend` | Calculate trend-following indicators including SMA, EMA, and Bollinger Bands | `technical/trend.py` |
| `vcp` | VCP detection with Cup & Handle, Power Play, 3C entry point, shakeout grading, relative correction, setup readiness scoring. Supports daily (default) and weekly intervals | `technical/vcp.py` |
| `post_breakout` | Post-breakout monitoring: tennis ball/egg behavior, squat recovery grading, failure reset detection, 20MA sell rule | `technical/post_breakout.py` |
| `volume_analysis` | Institutional accumulation/distribution analysis with A-E grading and breakout confirmation | `technical/volume_analysis.py` |

#### Data Sources

Price, financials, options, actions

| Function | Description | Script |
|----------|-------------|--------|
| `actions` | Corporate actions, earnings dates, calendar, and news | `data_sources/actions.py` |
| `earnings_acceleration` | Code 33 validation, earnings/sales acceleration patterns, surprise history, and analyst revisions | `data_sources/earnings_acceleration.py` |
| `bdi` | Baltic Dry Index (BDI) tracking via BDRY ETF with z-score analysis | `data_sources/bdi.py` |
| `calendars` | Financial calendars: earnings, IPO, economic events, and stock splits | `data_sources/calendars.py` |
| `dxy` | Dollar Index (DXY) tracking with z-score analysis | `data_sources/dxy.py` |
| `financials` | Financial statements retrieval | `data_sources/financials.py` |
| `funds` | YFinance funds data wrapper | `data_sources/funds.py` |
| `holders` | Holder and insider transaction data | `data_sources/holders.py` |
| `info` | Ticker information retrieval | `data_sources/info.py` |
| `market` | Market status and summary data via yfinance | `data_sources/market.py` |
| `multi` | Multi-ticker operations: compare, download, and news | `data_sources/multi.py` |
| `options` | Options data retrieval via yfinance | `data_sources/options.py` |
| `price` | Price data retrieval: history, download, and quote | `data_sources/price.py` |
| `search` | Search, screening, sector and industry data via yfinance | `data_sources/search.py` |

#### Analysis

Statistical analysis, fundamental analysis, and valuation tools

| Function | Description | Script |
|----------|-------------|--------|
| `analysis` | Analyst Estimates and Recommendations aggregating Wall Street consensus for earnings, revenue, and price targets | `analysis/analysis.py` |
| `analysis_utils` | Statistical Analysis Utilities providing reusable functions for multi-asset correlation, z-score, and percentile calculations | `analysis/analysis_utils.py` |
| `position_sizing` | Risk-based position sizing: calculate (entry sizing), pyramid (2%+2%+1% scaling plan), expectation (mathematical expectation with Kelly Criterion) | `analysis/position_sizing.py` |
| `convergence` | Multi-Model Convergence Analysis - SidneyKim0 methodology | `analysis/convergence.py` |
| `divergence` | Multi-Asset Divergence Detection analyzing correlation breakdown between traditionally linked assets | `analysis/divergence.py` |
| `putcall_ratio` | Put/Call Ratio analyzing options market sentiment through put vs call volume imbalance | `analysis/putcall_ratio.py` |
| `sbc_analyzer` | Stock-Based Compensation analysis: SBC amount, % of revenue, real FCF (FCF minus SBC), health flag | `analysis/sbc_analyzer.py` |
| `forward_pe` | Forward P/E calculator from analyst estimates with Walmart benchmark (45x) comparison | `analysis/forward_pe.py` |
| `margin_tracker` | Margin expansion tracker: gross/operating/net margin Q/Q and Y/Y changes with EXPANDING/STABLE/COMPRESSION/COLLAPSE flags | `analysis/margin_tracker.py` |
| `debt_structure` | Balance sheet health analyzer: debt structure, interest coverage, stress testing with rate hike scenarios | `analysis/debt_structure.py` |
| `institutional_quality` | Institutional ownership quality scorer (1-10) classifying holders as PASSIVE/LONG_ONLY/HEDGE/QUANT_MM | `analysis/institutional_quality.py` |
| `no_growth_valuation` | Zero-growth stress test: intrinsic value assuming 0% growth (revenue x margin x 15 P/E) with margin of safety | `analysis/no_growth_valuation.py` |
| `iv_context` | IV Rank/Percentile via CBOE: current IV30, annual high/low, IV Rank, HV30 comparison, cheap/fair/elevated/expensive classification | `analysis/iv_context.py` |
| `leaps_scanner` | LEAPS finder via CBOE options chain: optimal long-dated calls by target delta with breakeven and annualized cost | `analysis/leaps_scanner.py` |
| `csp_yield` | Cash-Secured Put yield calculator via CBOE: annualized yield, breakeven, downside cushion for put selling strategy | `analysis/csp_yield.py` |

#### Backtest

Conditional probability, event returns

| Function | Description | Script |
|----------|-------------|--------|
| `conditional` | Calculate conditional probability of reaching a target given a condition event | `backtest/conditional.py` |
| `event_returns` | Calculate forward return statistics after condition trigger events | `backtest/event_returns.py` |
| `extreme_reversals` | Detect extreme price events and measure mean reversion characteristics | `backtest/extreme_reversals.py` |
| `helpers` | Core helper functions for backtest analysis | `backtest/helpers.py` |
| `rate_cut_precedent` | Analyze historical Fed rate cut cycles and S&P 500 forward returns | `backtest/rate_cut_precedent.py` |
| `ratio` | Calculate and analyze asset price ratios for relative value assessment | `backtest/ratio.py` |

#### Macro

GBM fair value, multi-factor models

| Function | Description | Script |
|----------|-------------|--------|
| `erp` | Equity Risk Premium (ERP) = Earnings Yield - US10Y for valuation danger detection | `macro/erp.py` |
| `gbm` | Geometric Brownian Motion (GBM) Fair Value Model | `macro/gbm.py` |
| `macro` | Macro model and fair value analysis for SidneyKim0 methodology | `macro/macro.py` |
| `macro_utils` | Macro analysis utility functions for MarketData skill | `macro/macro_utils.py` |
| `net_liquidity` | Fed Net Liquidity composite (Balance Sheet - TGA - RRP) for systemic liquidity tracking | `macro/net_liquidity.py` |
| `vix_curve` | VIX Futures Curve analyzer via CBOE: VX1-VX9 term structure, contango/backwardation, regime classification (complacent/normal/anxious/panic) | `macro/vix_curve.py` |

### Specialized Analysis

#### Convergence

Multi-model convergence (SidneyKim0)

| Function | Description | Script |
|----------|-------------|--------|
| `convergence` | Multi-Model Convergence Analysis - SidneyKim0 methodology | `analysis/convergence.py` |

#### Divergence

Model divergence detection

| Function | Description | Script |
|----------|-------------|--------|
| `divergence` | Multi-Asset Divergence Detection analyzing correlation breakdown between traditionally linked assets | `analysis/divergence.py` |

#### Sentiment

Fear & Greed Index

| Function | Description | Script |
|----------|-------------|--------|
| `fear_greed` | CNN Fear & Greed Index tracking market sentiment through 7-indicator composite scoring system | `analysis/sentiment/fear_greed.py` |

#### Pattern

Technical patterns, regime detection

| Function | Description | Script |
|----------|-------------|--------|
| `fanchart` | Fan chart visualization | `technical/pattern/fanchart.py` |
| `helpers` | Pattern analysis helper functions for DTW, correlation, and forward return calculations | `technical/pattern/helpers.py` |
| `multi_dtw` | Multi-feature DTW pattern matching using price+RSI+slope+volatility+D2H vectors | `technical/pattern/multi_dtw.py` |
| `regime` | Market regime detection | `technical/pattern/regime.py` |
| `similarity` | Pattern similarity analysis | `technical/pattern/similarity.py` |

#### Valuation

CAPE ratio, dividend yield

| Function | Description | Script |
|----------|-------------|--------|
| `cape` | CAPE (Cyclically Adjusted Price-to-Earnings) Ratio data from YCharts | `valuation/cape.py` |
| `cape_historical` | Historical CAPE data from Robert Shiller dataset | `valuation/cape_historical.py` |
| `dividend_yield` | S&P 500 dividend yield calculation | `valuation/dividend_yield.py` |

### Data & Screening

#### Info

Company information

| Function | Description | Script |
|----------|-------------|--------|
| `info` | Ticker information retrieval | `data_sources/info.py` |

#### Screening

Finviz stock screener

| Function | Description | Script |
|----------|-------------|--------|
| `finviz` | Finviz stock screening, sector/industry group analysis, and market breadth (new 52W highs/lows by exchange) | `screening/finviz.py` |
| `finviz_presets` | Finviz screening preset definitions (includes Minervini SEPA presets) | `screening/finviz_presets.py` |
| `sector_leaders` | Bottom-up sector leadership dashboard: leader count by industry group with performance enrichment | `screening/sector_leaders.py` |
| `sepa_pipeline` | Full SEPA pipeline with hard-gate safety layer, signal reason codes, provisional watchlist mode, composite scoring, earnings proximity detection, and company category hint | `screening/sepa_pipeline.py` |
| `trend_template` | Minervini Trend Template 8-criteria checklist for Stage 2 qualification screening | `screening/trend_template.py` |

#### CFTC

Futures commitment of traders

| Function | Description | Script |
|----------|-------------|--------|
| `cftc` | CFTC Commitment of Traders (COT) data retrieval | `data_advanced/cftc/cftc.py` |

### Advanced Data Sources

#### FRED

Fed Funds, yield curve, inflation, policy

| Function | Description | Script |
|----------|-------------|--------|
| `inflation` | Federal Reserve Economic Data (FRED) inflation indicators and expectations data | `data_advanced/fred/inflation.py` |
| `policy` | Federal Reserve Economic Data (FRED) monetary policy and liquidity indicators | `data_advanced/fred/policy.py` |
| `rates` | Federal Reserve Economic Data (FRED) interest rate and yield curve data access | `data_advanced/fred/rates.py` |
| `series` | Federal Reserve Economic Data (FRED) generic series access utility | `data_advanced/fred/series.py` |

#### Fed

FedWatch Tool, FOMC calendar

| Function | Description | Script |
|----------|-------------|--------|
| `fedwatch` | CME FedWatch Tool - FOMC rate change probabilities from Fed Funds futures | `data_advanced/fed/fedwatch.py` |
| `fomc_calendar` | FOMC meeting calendar with official Federal Reserve meeting schedule | `data_advanced/fed/fomc_calendar.py` |

#### SEC

Filings, insider trades, 13F, FTD

| Function | Description | Script |
|----------|-------------|--------|
| `filings` | SEC company filings access and Management Discussion & Analysis (MD&A) extraction | `data_advanced/sec/filings.py` |
| `ftd` | SEC Failures to Deliver (FTD) and litigation releases data | `data_advanced/sec/ftd.py` |
| `insider` | SEC Form 4 insider trading activity tracking | `data_advanced/sec/insider.py` |
| `institutions` | SEC 13F filing lookup by company CIK (investment managers only, not stock ownership) | `data_advanced/sec/institutions.py` |

## How to Use

**Step 1**: Find the script you need in the catalog above.

**Step 2**: Discover exact subcommands via `extract_docstring.py` (see Safety Protocol below).

**Step 3**: Run the script: `$VENV $SCRIPTS/{path} {subcommand} {args}`

All scripts return JSON. Error format: `{"error": "message"}` with exit code 1.

## Script Execution Safety Protocol

### [HARD] Mandatory Batch Discovery Rule

Before executing ANY scripts in parallel, run `extract_docstring.py` ONCE with ALL scripts you plan to use. This is not optional.

**Why**: Wrong subcommand names cause cascading failures -- one bad call cancels ALL parallel sibling tool calls ("Sibling tool call errored"), wasting the entire round-trip. This catalog (Level 1) provides script file names only, NOT subcommand names. For example, `info.py` has subcommands `get-fast-info` and `get-info`, NOT `get`. You cannot guess these from the catalog.

```bash
# Discover subcommands for ALL scripts BEFORE parallel execution
$VENV ../tools/extract_docstring.py scripts/data_sources/info.py scripts/analysis/forward_pe.py scripts/analysis/sbc_analyzer.py

# Single script discovery
$VENV ../tools/extract_docstring.py scripts/technical/oscillators.py
```

Then use the discovered subcommands in your parallel calls with confidence.

### [HARD] Never Read Code Files Directly

Always use `extract_docstring.py` for function details. Direct `.py` file Read is severe token waste -- the docstring extractor provides the same information efficiently.

### Progressive Disclosure Alignment

- **Level 1 (SKILL.md catalog)**: Script file names and descriptions only
- **Level 2 (extract_docstring.py)**: Exact subcommand names, arguments, and usage examples
- Never guess subcommand names from Level 1 alone. Always escalate to Level 2 before execution.

### Skip Condition

If you have already successfully discovered a script's subcommands in the current session, you may reuse them without re-discovery.

### [HARD] Output Integrity Rule

Never pipe script output through `head`, `tail`, or any truncation command. Always capture and use full output. Partial data leads to incorrect analysis.

## Integration Notes

**Token Budget**: 2-level Progressive Disclosure keeps token load minimal. This file serves as the complete catalog; use `extract_docstring.py` only when you need detailed function signatures.

**Workflow**: Chain commands for comprehensive analysis (technical → macro → valuation → probability).

**Environment**: FRED API key is hardcoded. All data sources work out of the box.

**Rate Limits**: FRED 120/min, SEC 10/sec recommended.

**Tools:**
- `extract_docstring.py` - Extract function docstrings for Level 2 documentation

## Error Handling & Fallback Guide

### Dependency Failures

If a script fails with `ModuleNotFoundError` or import errors:

1. Activate the virtual environment: `cd skills/MarketData/scripts && python -m venv .venv && .venv/bin/pip install -r requirements.txt`
2. For individual packages: `.venv/bin/pip install <package-name>`
3. Common missing packages: `finvizfinance`, `fredapi`, `sec-api`

### Finviz 403 / Rate Limit Errors

Finviz may block requests with 403 errors due to rate limiting or bot detection. Follow this 3-stage fallback:

1. **Automatic retry**: `finviz.py` includes built-in retry with exponential backoff (up to 3 attempts with increasing delay)
2. **ETF-based sector analysis**: Use `sector_leaders.py scan --fallback etf` for sector-level leadership via 11 sector ETFs (XLK, XLV, XLF, etc.). Provides sector-level RS ranking but cannot identify individual stock leaders.
3. **YFinance-only analysis**: For individual stocks, all core SEPA scripts work without Finviz:
   - `stage_analysis.py classify` for stage identification
   - `rs_ranking.py score` for RS scoring (uses YFinance data)
   - `trend_template.py check` for Trend Template (uses YFinance data)
   - `earnings_acceleration.py` for earnings analysis (uses YFinance data)

### Data Insufficiency

When YFinance returns insufficient data for a specific ticker:

- **Price data < 200 days**: Stage analysis and Trend Template require 200+ trading days. Try `--period 3y` for tickers with short listing history.
- **No quarterly financials**: Some tickers (ETFs, ADRs, newly listed) lack income statement data. Use `earnings_acceleration.py surprise` (uses earnings_dates which has broader coverage) as fallback for EPS data.
- **Missing metrics**: If a specific income statement metric is not found (e.g., DilutedEPS), the scripts automatically try alternative metric names (BasicEPS, NetIncome, etc.).

### Script-Level Fallback Chain

| Primary Script | Fallback 1 | Fallback 2 |
|---------------|-----------|-----------|
| `sepa_pipeline.py analyze` | Run individual scripts separately | Manual analysis from price/financials data |
| `finviz.py screen` | `sector_leaders.py scan --fallback etf` | `rs_ranking.py screen` (YFinance-based RS) |
| `finviz.py groups` | `sector_leaders.py scan --fallback etf` | Manual ETF comparison |
| `earnings_acceleration.py code33` | `earnings_acceleration.py acceleration` | `financials.py get-income-stmt --freq quarterly` |
| `stage_analysis.py classify` | Infer from Trend Template results | Manual MA analysis via `trend.py sma` |