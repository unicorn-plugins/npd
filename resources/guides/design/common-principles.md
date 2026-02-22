# 공통설계원칙

모든 설계 단계에서 공통으로 적용되는 핵심 원칙

## 점진적 구현 원칙
- **MVP → 확장 → 고도화**: 단계별 접근
- **YAGNI 적용**: 꼭 필요한 기능만 구현(YAGNI원칙:You aren't gonna need it)
- **지속적 개선**: 피드백 기반 점진적 발전

---

## 병렬 처리 전략: 의존성 분석 및 병렬 처리

설계 단계에서 복수의 작업 항목(마이크로서비스, 화면, API 등)을 설계할 때, 작업 간 의존성을 분석하여 병렬 처리를 최적화합니다.

**의존성 분석 방법**  

1. **작업 항목 간 의존성 파악**
   - 각 작업 항목이 다른 항목의 산출물을 참조하는지 확인
   - **독립 항목**: 다른 항목의 산출물 없이 단독 수행 가능
   - **의존 항목**: 선행 항목의 산출물이 있어야 수행 가능
   ```
   예시)
   작업 A → 작업 B 참조 (B의 산출물이 A의 입력)
   작업 A → 작업 C 참조
   작업 C: 독립적 (선행 산출물 불필요)
   ```

2. **의존성 기반 그룹화**
   - **독립 항목**끼리 병렬 그룹으로 묶음
   - **의존 체인**(A→B→C)이 있는 항목은 선행 항목부터 순차 처리하는 그룹으로 묶음
   - 순환 의존이 발견되면 경계를 기준으로 끊고 별도 그룹으로 분리
   ```
   예시)
   Group 1 (순차 처리): 작업 B → 작업 A (B 완료 후 A 수행)
   Group 2 (독립 처리): 작업 C
   → Group 1과 Group 2는 병렬 수행
   ```

3. **에이전트 할당 및 병렬 처리**
   - 각 그룹에 에이전트를 1:1로 할당
   - 순차 그룹 내에서는 선행 항목을 먼저 수행한 뒤 후행 항목을 수행
   - 독립 그룹은 다른 그룹과 동시에 병렬 수행
   ```
   예시)
   Agent 1: Group 1 담당
     - 작업 B 수행
     - 작업 A 수행 (작업 B 산출물 참조)

   Agent 2: Group 2 담당
     - 작업 C 수행 (독립적, Agent 1과 병렬 수행)
   ```

---

## 다이어그램 검증: PlantUML 스크립트와 Mermaid 스크립트 생성 후 검증   

### PlantUML 기본 템플릿
```plantuml
@startuml
!theme mono

title [다이어그램 제목]

' 다이어그램 내용
@enduml
```

### 임시 파일 규칙

문법 검사를 위한 임시 다이어그램 파일은 반드시 `.temp/` 디렉토리에 생성한다.
- 산출물 디렉토리(`docs/design/` 등)에 검증용 임시 파일을 직접 생성하지 않는다.
- 검증 완료 후 `.temp/` 내 임시 파일은 삭제한다.

```bash
# 임시 디렉토리 생성 (없으면)
mkdir -p .temp

# 임시 파일 생성 → 검증 → 삭제 패턴
# PlantUML 예시:
cp docs/design/sequence/outer/flow.puml .temp/check.puml
bash tools/diagram/check-plantuml.sh .temp/check.puml
rm -f .temp/check.puml

# Mermaid 예시:
cp docs/design/logical-architecture.mmd .temp/check.mmd
bash tools/diagram/check-mermaid.sh .temp/check.mmd
rm -f .temp/check.mmd
```

### PlantUML 검사 방법

스크립트 파일(`.puml`) 생성 직후 반드시 문법 검사를 수행한다.
**검사용 임시 파일은 `.temp/` 디렉토리에 생성한다.**

```bash
# PlantUML 문법 검증 (Docker 컨테이너 자동 관리)
# 산출물 파일을 .temp/에 복사하여 검증
cp {산출물파일}.puml .temp/check.puml
bash tools/diagram/check-plantuml.sh .temp/check.puml
rm -f .temp/check.puml

# 종료 코드: 0 = 통과, 1 = 오류
```

- 상세 사용법: `{PLUGIN_DIR}/resources/tools/check-plantuml.md` 참조
- **화살표 문법 주의**: sequence diagram에서 `..>` 사용 금지, 비동기는 `->>` 또는 `-->>` 사용

### Mermaid 검사 방법

Mermaid 파일(`.mmd`) 생성 직후 반드시 문법 검사를 수행한다.
**검사용 임시 파일은 `.temp/` 디렉토리에 생성한다.**

```bash
# Mermaid 문법 검증 (Docker 컨테이너 자동 관리)
# 산출물 파일을 .temp/에 복사하여 검증
cp {산출물파일}.mmd .temp/check.mmd
bash tools/diagram/check-mermaid.sh .temp/check.mmd
rm -f .temp/check.mmd

# 종료 코드: 0 = 통과, 1 = 오류
```

- 상세 사용법: `{PLUGIN_DIR}/resources/tools/check-mermaid.md` 참조

---

## `{PLUGIN_DIR}` 결정 
1. `~/.claude/plugins/cache/npd/npd/` 하위에서 최신 버전 디렉토리를 탐색
2. 해당 디렉토리의 절대 경로를 `{PLUGIN_DIR}`에 바인딩
3. 이후 모든 `{PLUGIN_DIR}/resources/...` 경로를 절대 경로로 치환하여 파일을 읽음

**예시**: `{PLUGIN_DIR}/resources/guides/design/common-principles.md`
→ `~/.claude/plugins/cache/npd/npd/0.2.0/resources/guides/design/common-principles.md`
