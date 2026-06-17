# Run notes — MU vs AAPL (without_skill)

Tool: raw yfinance 1.4.1 via venv at
`.agents/skills/Minervini/Scripts/.venv/bin/python`
(NOTE: the venv path given in the task prompt, `.../Minervini/.venv/bin/python`, did NOT exist;
the actual venv is under `.../Minervini/Scripts/.venv/`. Located via `find`.)

Only raw yfinance used. No skills/SKILL.md/scripts loaded.

## Data pulled

### Ticker.info fields (MU / AAPL)
- currentPrice: 1036.95 / 299.20
- marketCap: 1.169T / 4.395T
- trailingPE: 48.84 / 36.23
- forwardPE: 9.05 / 31.19
- priceToBook: 16.14 / 41.22
- pegRatio: 0.32 / 2.42
- trailingEps: 21.23 / 8.26
- forwardEps: 114.59 / 9.59
- revenueGrowth: 1.963 (196%) / 0.166 (17%)
- earningsGrowth: 7.56 / 0.218
- earningsQuarterlyGrowth: 7.708 / 0.194
- grossMargins: 0.584 / 0.479
- operatingMargins: 0.676 / 0.323
- profitMargins: 0.415 / 0.272
- returnOnEquity: 0.398 / 1.415
- debtToEquity: 14.90 / 79.55
- totalCash: 14.59B / 68.51B
- totalDebt: 10.80B / 84.71B
- freeCashflow: 2.89B / 101.09B
- operatingCashflow: 30.65B / 140.22B
- dividendYield: None / 0.36
- fiftyTwoWeekHigh: 1110.40 / 317.40
- fiftyTwoWeekLow: 103.38 / 195.07
- fiftyDayAverage: 704.94 / 287.11
- twoHundredDayAverage: 391.05 / 267.53
- targetMeanPrice: 879.10 / 312.72  (MU target BELOW current price)
- recommendationKey: strong_buy / buy
- numberOfAnalystOpinions: 40 / 43
- beta: 2.173 / 1.086
- sector/industry: Technology/Semiconductors ; Technology/Consumer Electronics

### Price history (period=1y, Close), incl. ^GSPC benchmark
- MU: last 1036.5; 1y +763.4%; 6mo +346.2%; 3mo +133.4%; 1mo +48.3%;
      52wH 1087.99 (-4.7% off); 52wL 104.73 (+889.7%); 50dMA 718.12; 200dMA 395.51;
      vs50d +44.3%; vs200d +162.1%
- AAPL: last 299.14; 1y +53.5%; 6mo +9.1%; 3mo +20.3%; 1mo +0.1%;
      52wH 315.2 (-5.1% off); 52wL 194.87 (+53.5%); 50dMA 287.91; 200dMA 267.46;
      vs50d +3.9%; vs200d +11.8%
- ^GSPC: last 7513.77; 1y +25.6%; 6mo +10.5%; 3mo +13.7%; 1mo +2.2%; -1.3% off high

### Quarterly financials (most recent first)
- MU Total Revenue (B): 23.86, 13.64, 11.32, 9.30, 8.05
- MU Net Income (B): 13.78, 5.24, 3.20, 1.88, 1.58
- AAPL Total Revenue (B): 111.18, 143.76, 102.47, 94.04, 95.36
- AAPL Net Income (B): 29.58, 42.10, 27.47, 23.43, 24.78

### Risk metrics (computed from 1y daily returns)
- Annualized vol: MU 70.8% / AAPL 22.6%
- Max drawdown 1y: MU -30.3% / AAPL -13.8%

## Interpretation feeding the answer
- MU = memory super-cycle (HBM/AI), explosive earnings accel, forwardPE 9 vs trailingPE 49
  (classic cyclical-peak low-PE warning), +763% 1y, +162% above 200dMA, vol 71%, analyst
  target below price, RS leadership extreme but extended/late-cycle entry risk.
- AAPL = mature compounder, huge FCF (101B), steady 17%/22% growth, but PER 31-36 / PEG 2.42
  (not cheap), low vol/beta, shallow drawdowns.
- Both ~5% off 52w high → neither is a "cheap" entry. Verdict framed by investor profile:
  AAPL = risk-adjusted "easier buy"; MU = upside bet = cycle trade w/ high timing risk.
  Recommended scaled entry + hard stops for either.
