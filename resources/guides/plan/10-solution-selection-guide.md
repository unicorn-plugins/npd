# 솔루션 선정 가이드

## 목적

아이디어를 투표 방식으로 평가하고 우선순위 매트릭스를 통해 최적의 핵심 솔루션을 선정함.
- 비즈니스 가치와 실현 가능성 두 축으로 객관적 평가
- 핵심 솔루션 3개 이하를 선정하여 이후 비즈니스 모델링의 기반으로 활용

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| 솔루션 후보 | `docs/plan/think/솔루션후보.md` | 투표 및 평가 대상 아이디어 목록으로 활용 |

## 방법론

### 1단계: 우선순위 평가 (투표)

#### 투표 방식
- 각 팀원: 비즈니스 가치(B) 3표, 실현 가능성(F) 3표
- **B (Business)**: 비즈니스 가치가 높은 아이디어에 부여
- **F (Feasibility)**: 실현 가능성이 높은 아이디어에 부여
- 각 아이디어별로 받은 B와 F 투표수를 합산하여 표시

#### 투표 규모
- 참여 팀원: PO, SP, DE, AR, AI, BE, FE, QA, DO (9명)
- B(비즈니스 가치) 투표: 9명 x 3표 = **27표**
- F(실현 가능성) 투표: 9명 x 3표 = **27표**

### 2단계: 솔루션 선정 (우선순위 매트릭스)

#### 축 설정
- **X축**: 실현가능성 (낮음 → 높음)
- **Y축**: 비즈니스 영향도 (낮음 → 높음)

#### 4개 영역

| 영역 | 위치 | 우선순위 |
|------|------|---------|
| **No Brainers** | 실현가능성 높음 + 비즈니스 영향도 높음 | 1순위 (즉시 실행) |
| **Bit Bets** | 실현가능성 낮음 + 비즈니스 영향도 높음 | 2순위 (전략적 투자) |
| **Utilities** | 실현가능성 높음 + 비즈니스 영향도 낮음 | 3순위 (리소스 여유 시) |
| **Unwise** | 실현가능성 낮음 + 비즈니스 영향도 낮음 | 4순위 (보류/폐기) |

#### 매트릭스 작성 지침
- 그래프에는 아이디어 ID만 표시 (예: A1, A2, B1)
- 범례로 아이디어 ID와 아이디어명 매핑 표시
- SVG 파일로 작성

#### 핵심 솔루션 선정 기준
1. **No Brainers** 영역의 아이디어 우선 선정
2. No Brainers가 없으면 **Bit Bets**와 **Utilities** 아이디어도 포함
3. 핵심 솔루션은 **3개 이하**로 선정

### SVG 매트릭스 작성 예시

```xml
<svg width="600" height="500" xmlns="http://www.w3.org/2000/svg">
  <rect width="600" height="500" fill="#f9f9f9"/>
  <line x1="100" y1="400" x2="550" y2="400" stroke="#333" stroke-width="2"/>
  <line x1="100" y1="400" x2="100" y2="50" stroke="#333" stroke-width="2"/>
  <text x="320" y="440" text-anchor="middle" font-size="14">실현가능성</text>
  <text x="50" y="230" text-anchor="middle" font-size="14"
        transform="rotate(-90, 50, 230)">비즈니스 영향도</text>
  <rect x="100" y="50" width="225" height="175" fill="#ffcccc" opacity="0.3"/>
  <rect x="325" y="50" width="225" height="175" fill="#ccffcc" opacity="0.3"/>
  <rect x="100" y="225" width="225" height="175" fill="#ffffcc" opacity="0.3"/>
  <rect x="325" y="225" width="225" height="175" fill="#cce5ff" opacity="0.3"/>
  <text x="210" y="130" text-anchor="middle" font-size="12" font-weight="bold">Bit Bets</text>
  <text x="435" y="130" text-anchor="middle" font-size="12" font-weight="bold">No Brainers</text>
  <text x="210" y="310" text-anchor="middle" font-size="12" font-weight="bold">Unwise</text>
  <text x="435" y="310" text-anchor="middle" font-size="12" font-weight="bold">Utilities</text>
  <circle cx="450" cy="100" r="8" fill="#0066cc"/>
  <text x="465" y="105" font-size="12">A1</text>
  <text x="100" y="470" font-size="11">A1: 아이디어명</text>
</svg>
```

## 출력 형식

```markdown
# 솔루션 평가

## 투표 결과

| 아이디어 제목 | 비즈니스 가치 (B) | 실현 가능성 (F) |
|--------------|------------------|----------------|
| {아이디어} | {B 투표수}/27 | {F 투표수}/27 |

## 우선순위 매트릭스

(SVG 파일: 솔루션우선순위평가.svg)

| 영역 | 해당 아이디어 |
|------|-------------|
| No Brainers | {아이디어 목록} |
| Bit Bets | {아이디어 목록} |
| Utilities | {아이디어 목록} |
| Unwise | {아이디어 목록} |
```

```markdown
# 핵심 솔루션

## 선정 결과

### 핵심 솔루션 1: {솔루션명}
- **선정 근거**: {이유}
- **비즈니스 가치**: {B 투표수}
- **실현 가능성**: {F 투표수}
- **상세 설명**: {설명}

(3개 이하 반복)

## 선정 과정 요약
{투표 → 매트릭스 → 선정 과정 설명}
```

## 품질 기준

### 완료 체크리스트
- [ ] 투표 결과 집계표 포함 (9명 x B3표/F3표)
- [ ] 우선순위 매트릭스 SVG 파일 생성
- [ ] 4개 영역(No Brainers/Bit Bets/Utilities/Unwise) 분류 완료
- [ ] 핵심 솔루션 3개 이하 선정
- [ ] No Brainers 영역 아이디어 우선 선정 원칙 준수
- [ ] 각 핵심 솔루션의 선정 근거 명시
- [ ] 솔루션후보.md의 모든 아이디어가 투표 대상에 포함됨

### 정량 기준
- 투표 규모: B 27표 + F 27표 (9명 x 3표)
- 핵심 솔루션: 3개 이하
- SVG 매트릭스: 1개

## 주의사항

- 투표는 팀원 각자 독립적으로 수행
- 비즈니스 가치와 실현 가능성의 균형 고려
- No Brainers 영역 아이디어 우선 선정
- 핵심 솔루션 3개 이하 선정
- 투표 없이 직감으로 선정 금지
- 팀원들과 검토 및 합의 후 최종 확정
