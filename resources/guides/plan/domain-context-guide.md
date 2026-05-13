# 도메인 컨텍스트 파일 생성

`{PROJECT_DIR}/.npd/domain-context.yaml`에 도메인 특화 정보를 생성합니다.
이후 단계에서 `domain-expert` 에이전트 호출 시 이 파일을 프롬프트에 주입하여 도메인 특화 자문을 수행합니다.

**domain-context.yaml 구조:**
```yaml
# 프로젝트 도메인 컨텍스트
# 이 파일은 NPD의 domain-expert 에이전트가 참조하는 도메인 특화 정보입니다.

project: "{project}"
mvp_topic: "{MVP 주제}"
domain:
  name: "{도메인명}"           # 예: healthcare, commerce, fintech, education
  description: "{도메인 설명}"  # 예: 만성질환 환자 건강관리 서비스 도메인

background: |
  {도메인 특화 경력 및 전문성}
  # 예(healthcare): 서울대학교병원 내분비내과 임상연구 코디네이터 경력. 디지털 헬스케어 스타트업 3곳 자문.
  #   만성질환 관리 프로그램 설계 경험. 식약처 디지털 치료기기 인허가 프로세스 숙지.

expertise:
  - "{전문 지식 1}"
  - "{전문 지식 2}"
  - "{전문 지식 3}"

regulations:
  - name: "{규제/표준명}"
    description: "{설명}"
  - name: "{규제/표준명}"
    description: "{설명}"
```

**규칙:**
- 도메인명: `{PROJECT_DIR}/AGENTS.md` 파일의 "## MVP > 비즈니스 도메인"과 동일하게 작성
- MVP 주제: `{PROJECT_DIR}/AGENTS.md` 파일의 "## MVP > MVP 주제"와 동일하게 작성
- 도메인 설명: MVP 주제에 기반하여 도메인 설명 작성 
- 규제/표준은 해당 도메인에서 실제로 적용되는 것만 포함하며 MVP 주제와 밀접한 규제/표준으로 작성  
- background, expertise: 비즈니스 도메인과 MVP 주제와 관련된 내용으로 작성
