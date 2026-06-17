# Run notes — "지금 뭐 살 만한 거 없어?" (without_skill, raw yfinance only)

Date context: 2026-06-17. Tool: raw yfinance via Minervini venv python (path captured to /tmp/pypath.txt; emoji path mangled by zsh on direct entry, read from file instead). NO skill/SKILL.md/scripts used.

## Data pulled

### Market indices (1y history, close)
- ^GSPC: last 7512.40, MA50 7303.12, MA200 6897.67, 52wHi 7609.78, fromHi -1.3%, above200MA True
- ^IXIC: last 26366.77, MA50 25481.56, MA200 23504.18, 52wHi 27093.90, fromHi -2.7%, above200MA True
- ^DJI: last 52168.99, MA50 49880.18, MA200 48125.29, 52wHi 52168.99, fromHi 0.0% (new high), above200MA True
- ^VIX: last 16.47, MA50 17.81, MA200 18.55 (subdued)
=> Clear uptrend / buy-able regime.

### Screen (42 candidates; Minervini-style trend template + perf3m/perf6m as RS proxy)
Trend-template PASS: MU, MRVL, ARM, DELL, AMD, LRCX, AMAT, KLAC, ASML, DDOG, TSM, HWM, AAPL
Top perf6m: MU +345.5%, MRVL +247.4%, ARM +246.5%, DELL +216.5%, AMD +148.8%, LRCX +140.6%, AMAT +140.3%, KLAC +102.9%, ASML +78%, TSM +52.9%.
Theme: leadership overwhelmingly semis / AI infra.

### Fundamentals + entry context (dist from 50MA, 15d range, growth, margins, PE)
- MU: last 1036, dist50 +44.3%, fromHi -4.8%, 15dRange 25.9%, EPSg 7.56, Revg 1.96, GM 58%, PM 41%, fPE 9.0, tPE 48.8
- MRVL: dist50 +50.5%, EPSg -0.80, Revg 0.28, fPE 47, tPE 100.7
- ARM: dist50 +62.2%, fromHi 0%, EPSg 0.48, Revg 0.20, fPE 137, tPE 506
- DELL: dist50 +50.1%, fromHi -12%, EPSg 2.83, Revg 0.88, fPE 19.4
- AMD: dist50 +28.6%, fromHi -4.8%, 15dRange 21%, EPSg 0.91, Revg 0.38, PM 13%, fPE 39.7
- LRCX: dist50 +32.7%, EPSg 0.41, Revg 0.24, PM 31%, fPE 49
- AMAT: dist50 +40.5%, EPSg 0.34, Revg 0.11, fPE 38
- KLAC: dist50 +28.8%, EPSg 0.12, Revg 0.12, PM 36%, fPE 49
- ASML: dist50 +21.5%, EPSg 0.19, Revg 0.13, fPE 40
- TSM: dist50 +8.4%, fromHi -2.0%, 15dRange 9.3% (tight), EPSg 0.58, Revg 0.35, GM 62%, PM 46.5%, fPE 22.2  <-- best risk/reward
- HWM: dist50 +9.3%, fromHi 0%, 15dRange 13.3%, EPSg 0.71, Revg 0.19, PM 20%, fPE 46 (Industrials)
- AAPL: dist50 +3.9%, fromHi -5.1%, 15dRange 8.5% (tight), EPSg 0.22, Revg 0.17, fPE 31
- ANET: dist50 +5.3%, fromHi -6.7%, EPSg 0.25, Revg 0.35, PM 38%, fPE 37
- VRT: dist50 -2.4%, fromHi -17.1% (failed full trend template)
- PANW: dist50 +27.2%, EPSg None, Revg 0.31

### Earnings dates + liquidity
- TSM: 2026-07-16, avgVol 13.5M, mktCap 2.27T
- AAPL: 2026-07-31, avgVol 47M, 4.39T
- ANET: 2026-08-05, avgVol 9.2M, 209B
- HWM: 2026-08-06, avgVol 2.4M, 112B
- MU: **2026-06-25** (imminent, ~8d), avgVol 51M, 1.17T
- AMD: 2026-08-05; GE: 2026-07-16; NFLX: 2026-07-17; LLY: 2026-08-05

## Logic for the answer
1. Regime = uptrend (indices >200MA, near highs, VIX low) -> ok to buy.
2. Strongest momentum names (MU/MRVL/ARM/AMD/AMAT/LRCX) are extended +28~62% over 50MA => label "do not chase, wait for pullback to 50MA."
3. Buyable-now picks = trend-template pass AND near 50MA AND tight recent range: TSM (top), ANET, AAPL, HWM. MU flagged extra: extended + earnings 6/25.
4. Risk rules: scale in, stop -7/8% or 50MA break, avoid new entries right before earnings, diversify off semis.
