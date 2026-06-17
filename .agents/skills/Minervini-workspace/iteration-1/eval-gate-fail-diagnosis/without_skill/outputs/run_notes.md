# Run Notes — NVDA "지금 사도 돼?" (without_skill)

Date of run: 2026-06-17
Tool: raw yfinance 1.4.1 via `/Users/seongjin/Documents/⭐성진이의 옵시디언/💶Invest/.agents/skills/Minervini/Scripts/.venv/bin/python`
(Note: prompt-specified path `Minervini/.venv` did not exist; actual venv is at `Minervini/Scripts/.venv`. No skill/SKILL.md/scripts loaded — only `import yfinance`.)

## Ticker: NVDA

### yf.Ticker('NVDA').info fields pulled
- currentPrice = 207.2599
- previousClose = 207.41
- open = 208.53 ; dayHigh = 209.21 ; dayLow = 206.74
- fiftyTwoWeekHigh = 236.54
- fiftyTwoWeekLow = 142.03
- fiftyDayAverage = 208.2082
- twoHundredDayAverage = 189.55035
- marketCap = 5,019,804,893,184 (~$5.02T)
- trailingPE = 31.738148
- forwardPE = 16.284094
- priceToSalesTrailing12Months = 19.803629
- trailingEps = 6.53 ; forwardEps = 12.72715
- profitMargins = 0.62966 (62.97%)
- grossMargins = 0.74145 (74.14%)
- returnOnEquity = 1.14288 (114.3%)
- revenueGrowth = 0.852 (85.2%)
- earningsGrowth = 2.145 ; earningsQuarterlyGrowth = 2.106
- recommendationKey = strong_buy
- targetMeanPrice = 298.9322 ; targetMedianPrice = 288.0 ; targetHighPrice = 500.0 ; targetLowPrice = 180.0
- numberOfAnalystOpinions = 59
- beta = 2.202

### yf.Ticker('NVDA').history(period='1y') — 252 rows
- last_close = 207.26 (date 2026-06-17)
- 52w high close = 235.47 ; 52w low close = 143.66
- pct off 52w high (close basis) = -12.0%
- pct above 52w low = +44.3%
- MA50 = 208.6 -> price BELOW (above? False)
- MA150 = 191.43 -> price ABOVE (True)
- MA200 = 189.5 -> price ABOVE (True)
- ret 1m = -6.7% ; ret 3m = +15.0% ; ret 6m = +17.7%
- avg_vol_50d = 158,189,021 ; last_vol = 23,639,966 (partial/early-session bar)

### quarterly_financials (B = USD billions), cols newest->oldest
- Total Revenue: [81.61, 68.13, 57.01, 46.74, 44.06] for [2026-04-30, 2026-01-31, 2025-10-31, 2025-07-31, 2025-04-30]
- Net Income:    [58.32, 42.96, 31.91, 26.42, 18.77] same cols
- Operating Income: [53.54, 44.30, 36.01, 28.44, 21.64] same cols

### calendar
- Dividend Date: 2026-06-26
- Next Earnings Date: 2026-08-27
- Earnings Average est: 2.07925 ; Revenue Average est: ~$91.73B

### Derived (computed by me)
- Revenue YoY (Q 2026-04-30 vs 2025-04-30): 81.61/44.06 -1 = +85.2%
- Net income YoY: 58.32/18.77 -1 = +210.7%
- Sequential rev QoQ over last 4 transitions: +6.1%, +22.0%, +19.5%, +19.8%
- trailing PE 31.7 vs forward PE 16.3 -> market pricing roughly a doubling of forward EPS
- mean target $298.9 vs $207.26 -> ~+44% implied upside

## Answer stance
Qualified yes for long-term holders, scale in (3-4 tranches), prefer reclaim of 50DMA (~$208) for adding. Strong fundamentals (growth still accelerating, ~63% net margin) justify valuation; main caveats = high beta (2.2), elevated P/S (~20), expectations risk into 2026-08-27 earnings, AI-capex cycle dependence. Not for leveraged/short-term money; set stop and cap position size.
