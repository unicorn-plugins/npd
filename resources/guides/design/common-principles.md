# 공통설계원칙

모든 설계 단계에서 공통으로 적용되는 핵심 원칙

## 병렬 처리 전략: 의존성 분석 및 병렬 처리

### 의존성 분석 방법

1. **서비스 간 의존성 파악**
   ```
   일정 서비스 → 프로파일 서비스 (멤버/여행 정보 조회)
   일정 서비스 → 장소 서비스 (장소 정보 조회)
   장소 서비스: 독립적 (외부 API만 사용)
   ```

2. **의존성 기반 그룹화**
   ```
   Group A (순차 처리): 프로파일 → 일정 서비스
   Group B (독립 처리): 장소 서비스
   ```

3. **에이전트 할당 및 병렬 처리**
   ```
   Agent 1: Group A 담당
     - 프로파일 서비스 설계
     - 일정 서비스 설계 (프로파일 참조)

   Agent 2: Group B 담당
     - 장소 서비스 설계 (독립적)
   ```

## 다이어그램 검증: PlantUML 스크립트와 Mermaid 스크립트 생성 후 검증   

### PlantUML 기본 템플릿
```plantuml
@startuml
!theme mono

title [다이어그램 제목]

' 다이어그램 내용
@enduml
```

### PlantUML 검사 방법

스크립트 파일(`.puml`) 생성 직후 반드시 문법 검사를 수행한다.

```bash
# PlantUML 문법 검증 (Docker 컨테이너 자동 관리)
bash tools/diagram/check-plantuml.sh diagram.puml

# 종료 코드: 0 = 통과, 1 = 오류
```

- 상세 사용법: `resources/tools/check-plantuml.md` 참조
- **화살표 문법 주의**: sequence diagram에서 `..>` 사용 금지, 비동기는 `->>` 또는 `-->>` 사용

### Mermaid 검사 방법

Mermaid 파일(`.mmd`) 생성 직후 반드시 문법 검사를 수행한다.

```bash
# Mermaid 문법 검증 (Docker 컨테이너 자동 관리)
bash tools/diagram/check-mermaid.sh diagram.mmd

# 종료 코드: 0 = 통과, 1 = 오류
```

- 상세 사용법: `resources/tools/check-mermaid.md` 참조
