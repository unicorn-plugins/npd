# 비즈니스 모델 설계 가이드 (Lean Canvas)

## 목적

Lean Canvas 프레임워크를 사용하여 체계적인 비즈니스 모델을 설계함.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 핵심 솔루션 | `docs/plan/think/핵심솔루션.md` | Lean Canvas의 Solution 영역 기반 |
| 고객 분석 | `docs/plan/define/고객분석.md` | Customer Segments 영역에 활용 |
| 문제 가설 | `docs/plan/define/문제가설.md` | Problem 영역에 활용 |
| 시장 조사 | `docs/plan/define/시장조사.md` | TAM/SAM/SOM → Revenue Streams 근거, 경쟁사 → 경쟁 매트릭스, SWOT → Unfair Advantage |
| 문제해결 방향성 | `docs/plan/think/문제해결방향성.md` | Needs Statement → UVP 기반으로 활용 |
| 비즈니스 가치 | `docs/plan/define/비즈니스가치.md` | 측정 지표 → Key Metrics에 활용 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 비즈니스 모델 | `docs/plan/think/비즈니스모델.md` |

## 방법론

### 이전 산출물 매핑

| Lean Canvas 영역 | 출처 산출물 | 활용 방법 |
|-----------------|-----------|----------|
| Problem | 문제가설.md | 검증된 핵심 문제 3개를 Problem으로 전환 |
| Customer Segments | 고객분석.md | 타겟 세그먼트를 Customer Segments로 활용 |
| UVP | 문제해결방향성.md | Needs Statement를 UVP의 기반으로 활용 |
| Solution | 핵심솔루션.md | 선정된 핵심 솔루션을 Solution으로 기술 |
| Channels | 시장조사.md | 시장 진입 전략의 채널을 Channels로 활용 |
| Revenue Streams | 시장조사.md | TAM/SAM/SOM을 수익 추정 근거로 활용 |
| Cost Structure | (신규 추정) | 솔루션 구현 비용 기반 추정 |
| Key Metrics | 비즈니스가치.md | 비즈니스 가치의 측정 지표를 Key Metrics로 활용 |
| Unfair Advantage | 시장조사.md | SWOT의 Strength + 경쟁 분석에서 도출 |

### Lean Canvas 9개 영역

#### 1. Problem (문제)
- 해결해야 할 주요 문제 Top 3
- 현재 대안 (Existing Alternatives) 및 한계

#### 2. Customer Segments (고객 세그먼트)
- **Primary Target**: 주요 타겟 고객
- **Early Adopters**: 얼리어답터 특성 (니즈, 이유)
- **Customer Jobs**: 고객이 달성하려는 Job

#### 3. Unique Value Proposition (고유 가치 제안)
- **핵심 가치**: 한 문장으로 표현
- **High-level Concept**: "Y for X" 형식 (예: "도시락을 위한 Spotify")

#### 4. Solution (솔루션)
- 각 문제에 대한 Top 3 솔루션
- 핵심 기능 목록

#### 5. Channels (채널)
- **Acquisition Channels**: 고객을 찾는 방법
- **Delivery Channels**: 제품을 전달하는 방법
- **Retention Channels**: 고객을 유지하는 방법

#### 6. Revenue Streams (수익 흐름)
- **수익 모델**: 구독, 거래 수수료, 광고, 프리미엄 등
- **가격 전략**: 가격, 결제 주기, 책정 근거
- **LTV (Life Time Value)**: 예상 고객 생애 가치 및 산정 근거
- **수익 전망** (3개년):

| 항목 | 1년차 | 2년차 | 3년차 |
|-----|------|------|------|
| 사용자 수 | {수} | {수} | {수} |
| ARPU | {금액} | {금액} | {금액} |
| 총 수익 | {금액} | {금액} | {금액} |

#### 7. Cost Structure (비용 구조)
- **고정비용**: 인건비, 사무실, 인프라
- **변동비용**: 마케팅, 서버 비용, 고객 지원
- **예상 초기 투자**
- **BEP (손익분기점)**: 월 BEP, 도달 시기, BEP 사용자 수

#### 8. Key Metrics (핵심 지표) — AARRR
- **Acquisition**: CAC, 가입자 수
- **Activation**: 첫 사용률
- **Retention**: 재방문율, 이탈률 (Churn)
- **Revenue**: ARPU, MRR
- **Referral**: 바이럴 계수

#### 9. Unfair Advantage (경쟁우위)
- 복제하기 어려운 차별화 요소
- 고유 기술, 네트워크 효과, 전문성 등

### 추가 분석

#### 경쟁 분석 및 포지셔닝
| 경쟁사 | 가격 | 기능 | UX | 우리의 차별화 |
|-------|-----|------|-----|-------------|

#### Go-to-Market 전략
- **Pre-launch** (론칭 전): 사전 마케팅 활동
- **Launch** (론칭): 런칭 전략
- **Post-launch** (론칭 후): 성장 전략

#### 재무 계획
##### 예상 손익계산서 (3개년)
| 항목 | 1년차 | 2년차 | 3년차 |
|-----|------|------|------|
| 수익 | {금액} | {금액} | {금액} |
| 비용 | {금액} | {금액} | {금액} |
| 영업이익 | {금액} | {금액} | {금액} |

##### 자금 조달 계획
- Seed / Series A 규모
- 자금 사용처 비율 (제품 개발, 마케팅, 인력, 운영)

## 출력 형식

```markdown
# 비즈니스 모델

## 1. Lean Canvas

### Problem (문제)
- {문제 1}
- {문제 2}
- {문제 3}
- **현재 대안**: {대안 및 한계}

### Customer Segments (고객 세그먼트)
- **Primary Target**: {주요 타겟}
- **Early Adopters**: {얼리어답터}
- **Customer Jobs**: {JTBD}

### Unique Value Proposition (고유 가치 제안)
- **핵심 가치**: {한 문장}
- **High-level Concept**: {Y for X 형식}

### Solution (솔루션)
- {솔루션 1}: {설명}
- {솔루션 2}: {설명}
- {솔루션 3}: {설명}

### Channels (채널)
- **Acquisition**: {고객 획득 채널}
- **Delivery**: {제품 전달 채널}
- **Retention**: {고객 유지 채널}

### Revenue Streams (수익 흐름)
- **수익 모델**: {모델}
- **가격 전략**: {가격, 주기, 근거}
- **LTV**: {고객 생애 가치}

| 항목 | 1년차 | 2년차 | 3년차 |
|-----|------|------|------|
| 사용자 수 | {수} | {수} | {수} |
| ARPU | {금액} | {금액} | {금액} |
| 총 수익 | {금액} | {금액} | {금액} |

### Cost Structure (비용 구조)
- **고정비용**: {항목}
- **변동비용**: {항목}
- **BEP**: 월 {금액}, {시점} 도달, BEP 사용자 수 {수}

### Key Metrics (AARRR)

| 지표 | 측정 항목 | 목표치 |
|------|---------|-------|
| Acquisition | CAC, 가입자 수 | {목표} |
| Activation | 첫 사용률 | {목표} |
| Retention | 재방문율, Churn | {목표} |
| Revenue | ARPU, MRR | {목표} |
| Referral | 바이럴 계수 | {목표} |

### Unfair Advantage (경쟁우위)
{차별화 요소}

## 2. 가격 전략 및 수익 전망
{상세}

## 3. 비용 구조
{고정비/변동비 테이블, BEP 산정}

## 4. Key Metrics 상세
{AARRR 상세}

## 5. 경쟁 매트릭스

| 경쟁사 | 가격 | 기능 | UX | 차별화 |
|-------|-----|------|-----|-------|

## 6. Go-to-Market 전략
- **Pre-launch**: {사전 마케팅}
- **Launch**: {런칭 전략}
- **Post-launch**: {성장 전략}

## 7. 재무 계획

### 3개년 손익계산서

| 항목 | 1년차 | 2년차 | 3년차 |
|-----|------|------|------|
| 수익 | {금액} | {금액} | {금액} |
| 비용 | {금액} | {금액} | {금액} |
| 영업이익 | {금액} | {금액} | {금액} |

### 자금 조달 계획
{규모 및 사용처}
```

## 품질 기준

### 완료 체크리스트
- [ ] Lean Canvas 9영역 모두 작성
- [ ] 3개년 수익 전망 포함
- [ ] BEP(손익분기점) 산정 포함
- [ ] Key Metrics(AARRR) 정의
- [ ] 경쟁 매트릭스 포함
- [ ] Go-to-Market 전략 포함
- [ ] 이전 산출물 매핑이 올바름 (Problem←문제가설, Solution←핵심솔루션 등)

### 정량 기준
- Lean Canvas: 9영역 모두
- 수익 전망: 3개년
- Key Metrics: AARRR 5개 지표
- 경쟁사: 3개 이상

## 주의사항

- Lean Canvas 9개 영역 모두 작성
- 수익 모델은 구체적이고 측정 가능하게
- 비용 구조는 현실적으로
- BEP는 구체적 시점 명시
- Key Metrics는 AARRR 기반
- Unfair Advantage는 진짜 차별화 요소만
- Unit Economics 고려
- 확장 가능성 계획
