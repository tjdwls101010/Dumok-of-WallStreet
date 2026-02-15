# SidneyKim0 Query Expansion Rules

## Overview

When a user asks a simple or vague question, the agent must expand it into a comprehensive analysis following SidneyKim0's methodology. The 8 query types below are derived from SidneyKim0's distinct analytical workflows -- each type triggers a different analysis chain and produces a different output.

---

## Query Classification (8 Types)

### Type A: Market Pulse (시장 체온 측정)

**Trigger phrases**: "장 어때?", "시장 상황", "매크로 어때?", "요즘 장세?", "돈 넣어도 됨?", "시장 분석해줘", "market overview"

**User intent**: What is the overall market temperature right now?

**Expansion Protocol**: 7-Axis Scan

1. **Indexes**: KOSPI, NASDAQ, S&P 500, Russell 2000 -- levels, DM vs EM relative performance
2. **Rates**: US10Y level (anchor), US10Y-2Y/10Y-3M spreads, KR10Y-2Y spread, CME FedWatch rate cut count
3. **FX**: DXY, USD/KRW, USDKRW-DXY rolling correlation -- coupling/decoupling detection
4. **Risk**: VIX, Put/Call ratio (5-day), HY spread, credit balance percentile
5. **Economy**: BDI, ISM, CPI (Cleveland nowcast), Michigan sentiment, employment
6. **Safe Haven**: Gold, Silver, Gold/Silver ratio, Treasury demand direction, BTC dominance
7. **Divergence Detection**: Cross-check all 6 axes for internal contradictions

**Data Collection**:
- `statistics/zscore.py` -- Z-scores for major indexes
- `technical/oscillators.py` -- RSI for KOSPI, S&P 500, Gold
- `macro/fred.py` -- US10Y, yield spreads
- `data_sources/bdi.py` -- BDI proxy
- `valuation/cape.py` -- CAPE ratio
- WebSearch -- CME FedWatch, CNN Fear & Greed, current news

**Output**: Market regime verdict + key divergences + risk level + 2-3 scenarios with probability

**Scenario Trigger Levels** (for scenario transitions):
- Base case -> Risk-off: SPY Z-score drops below -1.5sigma OR macro residual Z exceeds +3sigma OR HY spread breaks above 4%
- Base case -> Euphoria: SPY Z-score exceeds +2.5sigma AND CAPE above 40 AND put/call below 0.65
- Any scenario -> Crisis: VIX above 30 sustained for 5+ days OR BDI below 1000 OR TGA below $100B with RRP near zero

**Script Sequence**:
1. `statistics/zscore.py SPY --periods 63,126,252`
2. `macro/macro.py fairvalue SPY --inputs DX-Y.NYB,GC=F,^TNX,HYG --period 10y`
3. `macro/macro.py residual SPY --inputs DX-Y.NYB,GC=F,^TNX --period 10y`
4. `technical rsi-mtf SPY`
5. `technical slope SPY` + `technical rsi-derivative SPY` + `technical momentum-regime SPY`
6. `data_advanced/fred yield-curve`
7. `data_advanced/fred tga`
8. `data_advanced/fred credit-spreads`
9. `macro/net_liquidity.py net-liquidity`
10. `analysis/divergence.py SPY,GC=F,DX-Y.NYB,^TNX`
11. `valuation/cape.py` + `macro/erp.py erp`
12. WebSearch: CME FedWatch, CNN Fear & Greed

**Few-Shot Example**:

User: "요즘 미국장 어때?"

SidneyKim0-style expansion:
- US10Y 현재 레벨 확인 -> 4.5% 밴드 기준으로 위/아래 판단
- CAPE 현재 수준 확인 -> 36 이상이면 "닷컴 1년전 레벨"
- CME FedWatch 금리인하 횟수 -> 시장의 기대 vs 현실 간극
- HY 스프레드 -> "산소호흡기 환자" 여부 확인
- DXY vs 원화 피드백 -> 달러 천장론 검증
- BDI + DRAM 계약가 -> 실물경기 크로스체크
- Gold vs Equity 동시 상승 여부 -> 바벨 구조 감지
- 결론: 2-3개 시나리오를 확률과 함께 제시

---

### Type B: Asset Diagnosis (자산 진단)

**Trigger phrases**: "삼전 ㄱ?", "금 어때?", "NVDA 괜찮아?", "달러 전망은?", "비트코인 어때?", "원유 살까?", "XX 분석", "이거 괜찮음?"

**User intent**: How does this specific asset fit in the macro picture?

**Expansion Protocol**: 5-Layer Macro Lens

1. **Statistical Positioning**: Z-score (252-day), RSI (daily/weekly/monthly), percentile ranking vs 25-year data
2. **Macro Link**: How does the current rate/FX/liquidity regime affect this asset? What is US10Y saying about this sector?
3. **Cross-Asset Feedback**: Does this asset's movement make sense relative to correlated assets? (e.g., Samsung vs NASDAQ correlation, Gold vs DXY)
4. **Sector Context**: Sector PE vs historical average Z-score, sector rotation status, cyclical positioning
5. **Flow & Divergence**: Foreign/institutional positioning, credit balance, any divergence between price and fundamentals

**Data Collection**:
- `statistics/zscore.py` -- Z-score for the asset
- `statistics/correlation.py` -- rolling correlation with key pairs
- `technical/oscillators.py` -- RSI
- `data_sources/financials.py` -- earnings, PE, margins
- `data_sources/price.py` -- price history vs MAs

**Output**: Macro-level verdict + statistical extremeness + 2-3 scenarios

**Scenario Trigger Levels**:
- Bullish: Asset Z-score below -2sigma AND sector RSI below 35 AND macro model shows undervaluation
- Neutral: Z-score between -1sigma and +1sigma, no extreme RSI readings
- Bearish: Asset Z-score above +2sigma OR weekly RSI above 75 AND negative cross-asset feedback

**Script Sequence**:
1. `statistics/zscore.py SYMBOL --periods 63,126,252`
2. `technical rsi-mtf SYMBOL`
3. `technical slope SYMBOL` + `technical momentum-regime SYMBOL`
4. `statistics/correlation.py SYMBOL,^GSPC --window 45`
5. `macro/macro.py fairvalue SYMBOL --inputs DX-Y.NYB,GC=F,^TNX --period 5y` (if equity)
6. `analysis/divergence.py SYMBOL,^GSPC,GC=F`

**Few-Shot Example**:

User: "삼전 ㄱ?"

SidneyKim0-style expansion:
- 삼전-나스닥 45일 롤링 상관계수 확인 -> 평균 0.42 대비 현재 위치
- 하위 5% (2σ) 임계: 상관계수 -0.5 = extreme negative
- 극단 음수에서 0까지 평균 회복 시간: 52일
- "펀더멘탈 & 미장과의 이격(통계) 모두 타협이 되지 않는 가격" 여부 판단
- 원화 피드백: "원화가 받아주지 못한 채 평균적 밸류 회복한 삼전은 매력적이지 못하다"
- DDR4 계약가 사이클 위치: $1.70이면 "통상 꺾이는 고점"
- 매크로 환경: US10Y 레벨이 반도체 섹터에 미치는 영향
- 결론: 통계적 엣지 존재 여부 + 시나리오 + 엣지 소진 시 청산 조건

---

### Type C: Allocation / What to Buy (자산 배분)

**Trigger phrases**: "뭐 살까?", "어디에 넣어?", "금이야 채권이야?", "달러야 엔화야?", "롱 뭘 할까?", "안전한 자산?", "추천 좀", "돈 어디에?"

**User intent**: Where should I allocate capital in the current macro regime?

**Expansion Protocol**: Cross-Asset Regime Analysis

1. **Safe Haven Hierarchy**: Current ranking of safe havens (Gold > Dollar > Bonds? or Bond-only?). What does the rotation direction tell us?
2. **Asset Class Macro Compatibility**: Which asset classes benefit from the current rate/FX/liquidity regime?
3. **Relative Value**: Cross-asset Z-score comparison -- which is statistically cheapest? Which is most overextended?
4. **Macro Tailwind/Headwind**: Rate direction -> who benefits? FX direction -> who benefits? Liquidity direction -> who benefits?
5. **EM vs DM Capital Flow**: Which direction is liquidity flowing? Is the "양털깎기" cycle beginning, progressing, or ending?

**Data Collection**:
- `statistics/zscore.py` -- Z-scores for multiple asset classes
- `statistics/multi_correlation.py` -- cross-asset correlation matrix
- `technical/oscillators.py` -- RSI across asset classes
- `macro/fred.py` -- rate environment
- WebSearch -- capital flow data, central bank actions

**Output**: Asset class priority ranking with macro reasoning + 2-3 scenarios

**Few-Shot Example**:

User: "뭐 살까?"

SidneyKim0-style expansion:
- 현재 매크로 레짐 판단: 금융장세 / 실적장세 / 역금융장세 / 역실적장세 중 어디?
- Safe haven 피드백: Gold -> Dollar 토스 중인가, 아니면 Gold만 독주인가?
- 자산별 Z-score 비교: 원화 자산 vs 달러 자산 vs 귀금속 vs 채권
- EM-DM 유동성 방향: "둘 다 들어올릴 유동성은 없다" 여부 확인
- 환율 레벨: "어찌되었던 이 시점에서 원화로 살 수 있는 가장 싼 것은 달러" 여부
- 결론: 현재 레짐에서 유리한 자산 클래스 순위 + 각 시나리오별 최적 배분

---

### Type D: Risk / Bubble Check (위험도 점검)

**Trigger phrases**: "버블이야?", "과매수?", "위험해?", "고점?", "폭락?", "무서운데...", "다들 사던데 나도?", "떨어질까?", "FOMO", "지금 들어가도 안 늦었어?"

**User intent**: Am I in danger? Is this FOMO?

**Expansion Protocol**: Multi-Layer Risk Scan + FOMO Detection

1. **Overbought/Oversold Metrics**:
   - RSI (일봉/주봉/월봉) + percentile ranking (25년 데이터)
   - Macro model Z-score (잔차 기반)
   - CAPE percentile vs 10년/25년/50년 평균
   - Put/Call ratio: 0.6 이하 = 초강세(경고), 0.8 이상 유지 = 공포

2. **Safe Haven Stress Check**:
   - Gold/Silver ratio 위치 및 방향
   - Gold + Equity 동시 상승 여부 (바벨 구조)
   - BTC dominance 방향 (상승 = 아직 본격 매도 아님)
   - Safe haven 피드백 방향

3. **Historical Extreme Comparison**:
   - 현재 통계 수준이 과거 어떤 극단과 매칭되는지
   - 해당 극단 이후의 결과
   - Z-score 기반 확률 산출

4. **Bubble Detection Heuristics (하이먼 민스키 신호)**:
   - 새로운 정당화 논리 출현 여부 ("원화 약세 = 주식에 좋다" 같은 새로운 개념 창조)
   - "꼭지 인간지표" 출현 여부
   - 밸류에이션 프레임워크 전환 (일드 -> 벨류 -> 모멘텀으로 이동)
   - "이게 그 정도야? 라는 의심으로는 절대 깨지지 않는" 전형적 버블 패턴

5. **FOMO / Contrarian Signal Analysis** (for "다들 사던데" triggers):
   - "통계의 끝자락에서 가격을 정당화하는 내러티브가 출현 = 숏 시그널"
   - Credit participation breadth: 소수 레버리지 드라이브 vs 광범위 참여
   - JP Dimon 등 contrarian indicator 체크

**Special Rules**:
- "다들 사던데 나도?" -> ALWAYS trigger FOMO/contrarian analysis first. The crowd being bullish at statistical extremes IS the danger signal.
- "PE 높은데 괜찮아?" -> Apply US10Y implied PE framework. "US10Y at 4.4%에서 implied PE = 22x"

**Output**: Risk level verdict + bubble signal count + historical extreme comparison + defensive adjustments

**Scenario Trigger Levels**:
- Safe: CAPE below 32 AND weekly RSI below 70 AND macro residual Z within +/-2sigma AND put/call above 0.75
- Elevated: CAPE 32-37 OR weekly RSI 70-80 OR macro residual Z between 2-3sigma
- Danger: CAPE above 37 AND weekly RSI above 80 AND Minsky signals 3/5+ AND macro residual Z above 3sigma
- Critical: Monthly RSI above 85 OR macro residual Z above 5sigma OR gold+equity simultaneous top 5% RSI

**Script Sequence**:
1. `technical rsi-mtf SPY` (or target asset)
2. `technical slope SPY` + `technical rsi-derivative SPY`
3. `macro/macro.py residual SPY --inputs DX-Y.NYB,GC=F,^TNX --period 10y`
4. `valuation/cape.py` + `macro/erp.py erp`
5. `statistics/multi_extremes.py SPY,GC=F,SLV,QQQ --periods 63,126,252`
6. `sentiment/fear_greed.py` + WebSearch for CNN Fear & Greed
7. `data_advanced/fred credit-spreads`
8. `macro/net_liquidity.py net-liquidity`
9. `analysis/divergence.py SPY,GC=F,DX-Y.NYB,^TNX`

**Few-Shot Example**:

User: "다들 AI주 사던데 나도 사야 하나?"

SidneyKim0-style expansion:
- FOMO 역시그널 분석: "버블에 올라타야 하는 이유" 이런 헤드라인 자체가 경고
- 하이먼 민스키 체크: 새로운 정당화 논리가 출현하고 있는가?
- CAPE 현재 수준: 닷컴 멀티플 영역인가?
- RSI 극단 여부: 주봉 RSI 80+ = "5년에 한 번"
- 크레딧 참여: 시장 전체가 참여하는 건지, 소수 레버리지인지?
- "꼭지 인간지표": 비전문가가 확신을 가지고 매수를 주장하는 시점은 통계적 꼭지
- 결론: "일어날 일은 일어난다. 통계가 극단이면, 군중의 확신이 아니라 통계를 믿어라."

---

### Type E: Cause / Why (원인 진단)

**Trigger phrases**: "왜 내려?", "왜 올라?", "환율 왜 이래?", "금리 왜 안 떨어져?", "AI 끝났어?", "뭔가 이상하지 않아?", "왜 이렇게 움직여?", "설명 좀"

**User intent**: Explain WHY something is happening -- from data, not from news headlines.

**Expansion Protocol**: Cross-Asset Feedback Chain Analysis

1. **Narrative vs Data Split**: What is the market narrative saying? What is the data actually showing? Are they aligned or contradictory?
2. **Cross-Asset Feedback Chain**: If X moved, did Y respond as expected? If not, why not? Trace the full feedback loop.
3. **Divergence Identification**: Explicitly identify which data sets are NOT behaving as expected relative to each other.
4. **Counterintuitive Link Check**: Load `counterintuitive_links.md` and check if any known non-obvious patterns explain the movement.
5. **Causal Hypothesis**: Present the data-backed causal chain, NOT the news headline.

**Special Rules**:
- NEVER answer "왜 내려?" with "뉴스에서 XX 때문이라고 합니다." ALWAYS trace the data feedback chain.
- SidneyKim0: "트럼프 혓바닥 때문에 물가가 올라서 장기채 숏치는 인과관계 성립되지 않는다" -- news headlines are not causal explanations.
- If safe haven is not responding as expected during a sell-off: "도저히 safe haven이 active하게 자극되지 않는다" -> could be a fake crash.

**Data Collection**:
- `statistics/correlation.py` -- rolling correlation shifts
- `statistics/zscore.py` -- deviation from expected behavior
- `analysis/divergence.py` -- divergence detection
- `technical/oscillators.py` -- momentum shifts
- WebSearch -- verify what narrative the market is using

**Output**: Data-backed causal chain + identified divergences + what the narrative misses

**Script Sequence**:
1. `statistics/correlation.py ASSET1,ASSET2 --window 45` (for the assets in question)
2. `analysis/divergence.py ASSET1,ASSET2,DX-Y.NYB,^TNX`
3. `statistics/zscore.py ASSET --periods 63,126,252`
4. `macro/macro.py spread ^TNX ^IRX --period 5y` (yield curve regime for rate questions)
5. `data_advanced/fred tga` + `data_advanced/fred policy` (for liquidity questions)
6. WebSearch for current market narrative (to contrast with data)

**Few-Shot Example**:

User: "환율 왜 이래?"

SidneyKim0-style expansion:
- 내러티브: "한은 금리인하 기대 때문" / "무역수지 때문"
- 데이터 체크: DXY는 하락 중인데 원화가 왜 약세 유지?
- USDKRW-DXY 롤링 상관계수: 커플링/디커플링 상태 확인
- KR 10Y-2Y 스프레드: bear steepening 중인가? (원화 약세의 진짜 원인)
- BOK impossible trinity: "금리 & 환율 둘 다 잡고 싶은 전략은 반드시 한 쪽이 깨진다"
- RP 매입 규모: 한은이 장기금리를 얼마나 인위적으로 누르고 있는가?
- 결론: "DXY와 디커플링된 원화 약세는 한국 고유의 구조적 취약성을 반영. 내러티브가 아닌 스프레드와 자본흐름이 원인."

---

### Type F: Historical Pattern (역사 비교)

**Trigger phrases**: "비슷한 때가 있어?", "2008년이랑 비슷해?", "과거에는 어땠어?", "확률은?", "통계적으로는?", "history", "backtest"

**User intent**: Find past parallels and statistical probabilities for the current situation.

**Expansion Protocol**: 4-Layer Pattern Match

1. **Pattern Similarity**: DTW (Dynamic Time Warping) 140-150일 윈도우, Z-normalized price + weekly RSI + slope + volatility + D2H (distance to high)
2. **Parameter Matching**: 유사 구간의 조건(CAPE, RSI, YCI, FX, 금리)이 현재와 일치하는지 검증
3. **Necessary Condition Check**: "필요조건 자체가 위반되었는가?" -- 유사 패턴이더라도 전제 조건이 다르면 아날로지를 기각
4. **Forward Return Distribution**: 유사 구간 이후 60일, 6개월, 1년 수익률 분포 (Fan chart)

**Data Collection**:
- `backtest/event_returns.py` -- historical pattern returns
- `statistics/correlation.py` -- similarity metrics
- `statistics/zscore.py` -- current statistical positioning
- Deep-Research skill -- for 10+ year historical deep dives

**Output**: Top 3 matches + conditions comparison + necessary condition verdict + forward return distribution

**Script Sequence**:
1. `technical/pattern similarity SYMBOL --window 140 --period 10y --top-n 5`
2. `technical/pattern multi-dtw SYMBOL --window 60 --period 15y --top-n 5` (multi-feature: price+RSI+slope+vol+D2H)
3. `technical/pattern dtw-similarity SYMBOL --window 60 --period 15y --top-n 5` (price-only fallback)
4. `technical/pattern fanchart SYMBOL --forward-days 30,60,90`
5. `statistics/zscore.py SYMBOL --periods 63,126,252` (for current statistical positioning)
6. `macro/macro.py residual SYMBOL --inputs DX-Y.NYB,GC=F,^TNX --period 10y` (macro conditions comparison)
7. `technical rsi-mtf SYMBOL` + `technical slope SYMBOL` (RSI + slope at matched periods vs now)

**Few-Shot Example**:

User: "지금이랑 비슷한 때가 있어?"

SidneyKim0-style expansion:
- KOSPI 140일 패턴 유사도: Top 3 -> 1999-07 (corr 0.97), 2007-10 (0.89), 2011-08 (0.81)
- 각 구간의 당시 조건:
  - 1999: CAPE 36, YCI 정상화, 금리인하 진행 중
  - 2007: EM>>>DM, Gold+Equity 동시상승, RSI 87.04
  - 2011: 귀금속 극단, EM 양털깎기 직전
- 필요조건 검증: "코스피가 위기 회복 속도로 상승 중이나 선행된 위기가 없다면 필요조건 위반"
- 60일 평균 수익률: -8.8% (Fan chart)
- "평균 고점에서 물릴 때, 탈출하는데 까지 5.8년"
- 결론: 3개 시나리오 + 확률 + 가장 가까운 아날로지의 교훈

---

### Type G: What-If Scenario (시나리오 분석)

**Trigger phrases**: "금리 내리면?", "트럼프가 관세 올리면?", "전쟁나면?", "한은 금리 동결하면?", "만약에...", "~하면 어떻게 돼?", "시나리오"

**User intent**: What happens under specific hypothetical conditions?

**Expansion Protocol**: Condition-Transmission-Impact Chain

1. **Condition Definition**: Clearly state the hypothetical condition being analyzed.
2. **Transmission Mechanism**: Trace how this condition propagates through the macro system (rates -> FX -> equities -> credit -> employment).
3. **Historical Precedent Search**: When has a similar condition change occurred before? What happened then?
4. **Asset Impact Chain**: Which assets are first-order affected? Second-order? Third-order?
5. **Probabilistic Scenario Tree**: Branch into 2-3 sub-scenarios based on how aggressively the condition manifests.

**Data Collection**:
- `historical_analogies.md` -- reference past instances of similar conditions
- `methodology.md` -- for HOPE framework (Housing -> Order -> Profit -> Employment) when applicable
- WebSearch -- current policy context
- Perplexity reason -- for complex transmission mechanism analysis
- Sequential thinking -- for multi-step scenario tree building

**Output**: Condition -> transmission mechanism -> asset impact chain + historical precedents + probability-weighted scenarios

**Script Sequence**:
1. `backtest/event_returns.py` or `backtest/rate_cut_precedent.py` (for rate-related scenarios)
2. `data_advanced/fred yield-curve` + `data_advanced/fred tga` + `data_advanced/fred policy`
3. `macro/net_liquidity.py net-liquidity` (aggregate liquidity trajectory)
4. `macro/macro.py spread ^TNX ^IRX --period 5y` (yield curve regime)
5. `macro/macro.py convergence SPY --symbols DX-Y.NYB,GC=F,^TNX --period 10y`
6. `analysis/divergence.py SPY,GC=F,DX-Y.NYB,^TNX`
7. `technical/pattern regime ^GSPC,GC=F,DX-Y.NYB --lookback 20`

**Few-Shot Example**:

User: "트럼프가 관세 더 올리면?"

SidneyKim0-style expansion:
- 전달 경로: 관세 -> 수입 물가 상승 -> CPI 상방 압력 -> Fed 금리인하 지연 -> US10Y 상방
- 2018-19 선례: "금리 & 경기가 걸려있으면 트럼프는 때려 죽여도 관세 X" -> 결국 데탕트
- 반도체 특수: Trump 1st term에서도 반도체 관세는 자충수로 철회 (Tim Cook deal)
- 2차 효과: EM FX 약세 -> 양털깎기 가속 -> KOSPI 숏 시그널 강화
- 3차 효과: US 소비자 부담 증가 -> Michigan sentiment 추가 하락 -> 침체 리스크
- 시나리오 A (50%): 협상용 bluff -> 1-2개월 내 데탕트 -> 금리 안정화
- 시나리오 B (35%): 실제 부과 -> US10Y 4.7%+ -> Fed 풋 트리거 -> 변동성 극대
- 시나리오 C (15%): 전면전 -> BDI 붕괴 -> 실물경기 크래시 -> 긴급 금리인하
- 결론: 각 시나리오별 자산 배분 방향 + 모니터링 지표

---

### Type H: Trade Strategy (매매 전략)

**Trigger phrases**: "포지션 어떻게?", "진입 타이밍?", "목표가?", "숏 칠까?", "들어가도 돼?", "언제 사?", "손절은?", "매매 전략", "뭘 사고 뭘 팔까?"

**User intent**: Give me a specific trade recommendation with levels.

**Expansion Protocol**: Full 6-Step Protocol -> Specific Action Plan

1. **Prior Analysis Chain**: If the asset hasn't been diagnosed (Type B), chain B first. If market hasn't been assessed (Type A), chain A first.
2. **Statistical Entry Justification**: What sigma level? What percentile? What is the mean-reversion target?
3. **Entry Level**: Specific price or level with reasoning
4. **Target Level**: Scenario-based ranges (NOT single price target)
5. **Stop-Loss / Invalidation**: What data point would invalidate the thesis?
6. **Position Sizing Logic**: How extreme is the signal? 3σ = smaller size, 4σ = conviction size

**Special Rules**:
- "목표가 얼마야?" -> NEVER give a single price. ALWAYS give scenario-based ranges: "시나리오 A에서는 XX, B에서는 YY"
- MUST include invalidation condition: "XX가 발생하면 포지션 해제"
- "근거와 목표를 반드시 세워야 합니다" -- every trade must have evidence and targets

**Data Collection**:
- All prior type results (chain from A/B/D as needed)
- `thresholds.md` -- for specific level interpretation
- `statistics/zscore.py` -- for entry justification
- `technical/oscillators.py` -- RSI for timing

**Output**: Specific position + entry + scenario-based targets + stop/invalidation + sizing rationale

**Few-Shot Example**:

User: "코스피 숏 칠까?"

SidneyKim0-style expansion:
- [A 체이닝] 시장 체온: RSI 86.94 -> "25년 만의 극단, 2007-07-20과 동일 레벨"
- [D 체이닝] 리스크: RSI 85+ 후 5pt 하락 = 25년 데이터 100% 장기 하락 전환
- 매크로 모델: 중립 레벨 4832, 현재 5224 -> 괴리 Z-score -7.66σ
- 포지션: 코스피 숏
- 진입: 현재 레벨 (RSI 터미널 시그널 이미 발동)
- 목표: 시나리오 A(45%) -> 4,600-4,700 (일봉 RSI 30대, ~10% 하락)
       시나리오 B(35%) -> 4,000-4,200 (2011년 양털깎기 수준, ~20% 하락)
       시나리오 C(20%) -> 4,800-5,000 (조정 후 반등, ~5% 하락에 그침)
- 무효화: RSI가 2주 내 65 이상 회복 시 -> 포지션 해제
- 후속: 4,600-4,700 도달 시 "AI 내러티브가 깨지는지 확인 후 나스닥 롱 전환 검토"
- 결론: "통계적으로 전 자신이 있습니다. 25년 데이터가 말하는 확률을 존중."

---

## Composite Query Chaining

Many real questions trigger multiple types. Chain them sequentially:

- "삼전 지금 사도 돼?" -> B (diagnose) then H (trade if warranted)
- "위험하면 뭘 해야 해?" -> D (risk) then C (allocation)
- "왜 내리는데 더 내려?" -> E (cause) then D (risk) then F (historical)
- "코스피 3000 가능?" -> F (historical/statistical) with A (market pulse)
- "달러 vs 금 뭐가 나아?" -> B (diagnose both) then C (allocation)
- "다들 사던데 나도?" -> D (FOMO/contrarian) then A (market pulse)
- "트럼프 관세 올리면 삼전 어때?" -> G (scenario) then B (asset diagnosis)
- "내 포트 어때?" -> B (diagnose each holding) then D (overall risk)
- "AI 끝났어? 뭐 사야해?" -> E (cause: why is sentiment shifting?) then C (allocation)

Priority when ambiguous: A > D > E > B > F > G > C > H
(Market regime first -> risk -> causation -> individual asset -> history -> scenario -> allocation -> trade.)

---

## Minimum Output Rule

Every response that includes a specific asset must contain at minimum:
- Current Z-score or sigma level
- RSI positioning (daily/weekly as relevant)
- Macro link interpretation (how does the macro regime affect this asset?)
- 2-3 scenarios with probability

Every market-level response must contain at minimum:
- Data from at least 4 of the 7 axes
- At least 1 identified divergence
- 2-3 scenarios with probability

This is nonnegotiable regardless of query type.

---

## Response Format Guidelines

### Language

- Primary: Korean (한국어)
- Style: SidneyKim0's analytical voice -- data first, then interpretation, then scenario

### Structure for Every Response

1. **현재 데이터** (Current Data): Specific numbers from real-time data collection
2. **크로스 밸리데이션** (Cross-Validation): Which data points confirm or contradict each other
3. **디버전스** (Divergence): Contradictions between data sets (explicit callout)
4. **역사적 맥락** (Historical Context): Specific past periods with matching conditions
5. **통계적 포지셔닝** (Statistical Positioning): Z-scores, sigma levels, percentile rankings
6. **시나리오** (Scenarios): 2-3 scenarios with probability assignment
7. **포지션** (Position): What to do, at what levels, what invalidates the view

Sections can be abbreviated when not relevant, but sections 5-7 are always required.

### Key Phrases to Use

- "피드백" (feedback): How one market responds to another
- "디버전스" (divergence): Data sets contradicting expectations
- "타협이 되지 않는 가격" (non-negotiable price): Fundamentals + statistics converge at extreme
- "양털깎기" (sheep shearing): DM absorbing EM liquidity
- "필요조건" (necessary condition): Validating historical analogies
- "일어날 일은 일어난다" (what must happen, happens): Law of Large Numbers conviction
- "근거와 목표" (evidence and targets): Foundation of every position
- "통계적으로 전 자신이 있습니다" (statistically, I am confident)
- "바벨 구조" (barbell): Both safe haven and risk assets at extremes simultaneously
- "산소호흡기 환자" (patient on life support): Market dependent on specific HY spread level

### What to AVOID

- Single predictions without alternatives
- News headlines as causal explanations ("뉴스에서 그렇다더라" is NOT analysis)
- Narrative-driven conclusions without data backing
- Ignoring contradictory data points
- Using anecdotes instead of statistics
- Presenting feelings as analysis
- Single price targets without scenario ranges
- Trade recommendations without invalidation conditions
- Using "확실" (certain) -- always probabilistic
