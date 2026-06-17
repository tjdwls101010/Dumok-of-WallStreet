# Run notes — MU entry question (without_skill)

Tool: raw yfinance only, via Minervini venv python. No skill/scripts loaded.
As-of: 2026-06-17 close (queried 2026-06-18).

## Ticker: MU

### Price / MA (history period=2y, auto_adjust=True)
- Last close: 1037.23 (info currentPrice 1036.62)
- 52w high: 1087.99 (also info fiftyTwoWeekHigh 1110.40)
- 52w low: 104.73 (info fiftyTwoWeekLow 103.38)
- Pct off 52w high: -4.7%
- Pct above 52w low: +890.4%
- MA10: 976.05 (+6.3%), MA20: 945.18 (+9.7%), MA50: 718.13 (+44.4%), MA150: 466.08 (+122.5%), MA200: 395.51 (+162.2%)
- info fiftyDayAverage 704.94, twoHundredDayAverage 391.05

### Recent 10 sessions (Close): showed extreme whipsaw
- 6/4 996.00, 6/5 864.01 (-13%, vol 77M >> ~50M avg), 6/8 949.28, 6/9 935.89, 6/10 891.88,
  6/11 995.87, 6/12 981.61, 6/15 1087.99 (+11%), 6/16 1020.76 (-7%), 6/17 1037.23
- avgVolume ~51.3M; 50d avg vol ~48-50M
- Up-volume days (>1.5x 50d): 5/11, 5/12, 5/26, 6/5

### Volatility / RS
- 20d realized vol (annualized): 118.5%
- 14d avg (H-L)/C: 6.9% (ATR-ish)
- 6m return MU +346.2% vs SPY +11.0%
- 3m return MU +133.4% vs SPY +13.8%
- 1m return MU +48.4% vs SPY +2.1%

### Fundamentals (info)
- marketCap 1.169T, trailingPE 48.83, forwardPE 9.05, priceToBook 16.14, pegRatio 0.32
- trailingEps 21.23, forwardEps 114.59
- revenueGrowth 1.963 (196%), earningsGrowth 7.56, earningsQuarterlyGrowth 7.708
- grossMargins 58.4%, operatingMargins 67.6%, profitMargins 41.5%, ROE 39.8%
- totalRevenue 58.1B, totalDebt 10.8B, totalCash 14.6B, freeCashflow 2.89B
- recommendationKey strong_buy, targetMeanPrice 879.1 (BELOW spot), 40 analysts
- sharesOutstanding 1.128B, sharesShort 37.5M

### Earnings calendar (KEY)
- Next earnings date: 2026-06-25 (~1 week out)
- EPS estimate range Low 7.53 / Avg 19.72 / High 24.08 (very wide -> uncertain)
- Revenue est Low 19.68B / Avg 34.52B / High 40.07B

### Quarterly trend (financials, $B)
- Total Revenue: 8.05 (Feb25) -> 9.30 -> 11.32 -> 13.64 -> 23.86 (Feb26)  [accelerating]
- Net Income: 1.58 -> 1.88 -> 3.20 -> 5.24 -> 13.78  [exploding]
- Operating Income: 1.77 -> 2.17 -> 3.69 -> 6.14 -> 16.14

## Judgment encoded in answer
- Trend/RS: elite leader, confirmed.
- Entry: NO — extended (+44% over 50MA, +162% over 200MA), ~10x off low, 118% vol, ATR ~7%.
- Timing blocker: earnings 6/25 (~1wk) — do not initiate before event.
- Plan: wait through earnings; if good -> buy first pullback to 10/21MA or 50MA, or new-base breakout on volume; stop -7/-8%, half size, pyramid only when in profit.
