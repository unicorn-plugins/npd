# 프론트엔드설계가이드

## 목적
프로토타입과 백엔드 API 명세서를 기반으로 기술 관점의 프론트엔드 설계서(UI/UX, 스타일가이드, 정보 아키텍처, API 매핑)를 작성한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| UI/UX 설계서 | `docs/plan/design/uiux/uiux.md` | 화면 요구사항 분석 |
| 스타일 가이드 | `docs/plan/design/uiux/style-guide.md` | 디자인 시스템 기반 |
| 프로토타입 | `docs/plan/design/uiux/prototype/` | 화면 분석 |
| API 설계서 | `docs/design/api/` | API 매핑 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| UI/UX 설계서 (기술 관점) | `docs/design/frontend/uiux-design.md` |
| 스타일 가이드 | `docs/design/frontend/style-guide.md` |
| 정보 아키텍처 | `docs/design/frontend/ia.md` |
| API 매핑 설계서 | `docs/design/frontend/api-mapping.md` |

## 방법론

<설계원칙>
- 기술스택: TypeScript 5.5 + React 18.3 + Vite 5.4
- 프로토타입과 동일하게 설계
- 각 백엔드서비스 API명세서와 반드시 일치
- 모바일, 태블릿, 웹 화면 크기에 맞게 반응형으로 디자인

<설계순서>
- 준비:
  - 프로토타입 분석: 'design/prototype' 디렉토리 하위의 프로토타입 분석 및 이해
  - API 분석: "[백엔드시스템]"섹션의 정보를 이용하여 API명세서를 'design/api'에 다운로드하여 분석 및 이해
  - 화면요구사항 분석: "[요구사항]" 섹션을 읽어 화면 요구사항 이해

- 설계:
  - 1. **UI/UX 설계**
    - 1.1 UI프레임워크 선택: MUI, Ant Design, Chakra UI, Mantine, React Bootstrap 등
    - 1.2 화면목록 정의
    - 1.3 화면 간 사용자 플로우 정의
    - 1.4 화면별 상세 설계:
      - 1.4.1 상세기능
      - 1.4.2 UI 구성요소
      - 1.4.3 인터랙션
    - 1.5 화면간 전환 및 네비게이션
    - 1.6 반응형 설계 전략
    - 1.7 접근성 보장 방안
    - 1.8 성능 최적화 방안

  - 2. **스타일가이드 작성**:
    API명세서 분석 결과와 선택한 UI프레임워크 특성을 반영
    - 2.1 브랜드 아이덴티티: 디자인 컨셉 등
    - 2.2 디자인 원칙
    - 2.3 컬러 시스템
    - 2.4 타이포그래피
    - 2.5 간격 시스템
    - 2.6 컴포넌트 스타일
    - 2.7 반응형 브레이크포인트
    - 2.8 대상 서비스 특화 컴포넌트
    - 2.9 인터랙션 패턴

  - 3. **정보 아키텍처 설계**
    - 3.1 사이트맵: 페이지 구조 및 네비게이션 흐름
    - 3.2 프로젝트 구조 설계: 패키지와 파일까지 설계

  - 4. **API매핑설계서**
    - 4.1 API경로 매핑
      public/runtime-env.js파일을 읽어 API그룹과 '"[백엔드시스템]"섹션에 정의된 각 서비스별 HOST를 지정
      예시)
      ```
      window.__runtime_config__ = {
        API_GROUP: "/api/${version:v1}",
        USER_HOST: "http://localhost:8081",
        ORDER_HOST: "http://localhost:8082"
      }
      ```

    - 4.2 **API와 화면 상세기능 매칭**: '1.4.1 상세기능'과 API 매핑
      - 화면, 기능, 백엔드 서비스, API경로, 요청데이터 구조, 응답데이터 구조 명시
      - API 요청데이타와 API 응답데이터 예시

## 출력 형식

- UI/UX 설계서: `design/frontend/uiux-design.md`
- 스타일 가이드: `design/frontend/style-guide.md`
- 정보 아키텍처: `design/frontend/ia.md` (사이트맵 + 프로젝트 구조 트리 포함)
- API 매핑 설계서: `design/frontend/api-mapping.md` (runtime-env.js 설정 + 화면-API 매핑표 포함)

## 품질 기준

- [ ] 프로토타입과 동일하게 설계
- [ ] 백엔드 API 명세서와 일치
- [ ] 반응형 디자인 (모바일, 태블릿, 웹)
- [ ] 구현 코드 미포함

## 주의사항

- 공통 원칙: `common-principles.md` 참조
- 설계서에 구현 코드(컴포넌트 소스 등) 포함 금지 — 설계 명세만 기술
- 프로토타입 화면과 다르게 설계하지 않을 것
- API 매핑 시 백엔드 API 경로, 요청/응답 데이터 구조를 정확히 반영
- UI 프레임워크 선택 후 스타일 가이드와 일관성 유지
