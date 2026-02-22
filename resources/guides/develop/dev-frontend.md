# 프론트엔드 개발 가이드

## 목적
UI/UX설계서, 스타일가이드, 정보아키텍처, API매핑설계서를 기반으로 프론트엔드를 개발한다. 기술스택 결정부터 공통 컴포넌트 구축, 각 페이지별 구현까지 3단계로 진행하며, 각 단계 완료 후 사용자 확인을 거친다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| UI/UX 설계서 | `docs/design/frontend/uiux-design.md` | 화면 구현 기준 |
| 스타일가이드 | `docs/design/frontend/style-guide.md` | 스타일 시스템 구축 |
| 정보아키텍처 | `docs/design/frontend/ia.md` | 라우팅 및 폴더 구조 기준 |
| API 매핑설계서 | `docs/design/frontend/api-mapping.md` | API 연동 매핑 |
| API 명세서 | `docs/design/api/*.json` | API 연동 |
| 프로토타입 | `docs/design/prototype/*` | 화면 분석 |
| 유저스토리 | `docs/design/userstory.md` | 페이지별 기능 파악 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| 프론트엔드 코드 | `frontend/src/` |

## 방법론

### 개발원칙
- UI/UX설계서, 스타일가이드, 정보아키텍처, API매핑설계서를 기반으로 개발
- API명세서와 반드시 일치

### 개발순서

**단계 구분:**
- '0. 준비'를 수행하고 완료 후 다음 단계 진행여부를 사용자에게 확인
- '1. 기술스택 결정 ~ 5. 공통 컴포넌트 개발'까지 수행하고 완료 후 다음 단계 진행여부를 사용자에게 확인
- '6. 각 페이지별 구현'은 사용자와 함께 각 페이지를 개발

**0. 준비**
- UI/UX설계서, 스타일가이드, 정보아키텍처, API매핑설계서 분석 및 이해
- API명세서 분석 및 이해
- 프로토타입을 웹브라우저에서 모바일사이즈로 열어 각 화면 분석(playwright MCP 이용)

**1. 기술스택 결정**
사용자가 제공한 기술스택을 우선 고려. 미제공 시 팀원들과 검토하여 결정.
- 개발 프레임워크
- UI라이브러리와 버전 선택
- 상태 관리 라이브러리 선택
  - 클라이언트 상태 관리: Redux/Zustand/Context API 중 선택
  - 서버 상태 관리: React Query/SWR/Apollo 중 선택
- 라우팅 라이브러리와 버전 선택
- API통신 라이브러리와 버전 선택
- 스타일링 라이브러리와 버전 선택
- 빌드 도구 선택: Vite/Webpack/Create React App 중 선택
- 개발 서버 포트: 3000

**2. 프로젝트 초기 설정**

2.1 프로젝트 생성 및 구조 설정
- 프로젝트 설정 확인
  - 현재 디렉토리를 프로젝트 루트로 사용
  - 현재 존재하는 디렉토리/파일은 그대로 유지하면서 작업
  - package.json 파일 존재 확인
  - TypeScript 설정 확인 및 완료 (TypeScript 사용시)
  - ESLint/Prettier 설정 확인 및 완료
- 폴더 구조 생성: 정보아키텍처대로 작성
- 설정 파일 생성
  - vite.config.ts/webpack.config.js
  - tsconfig.json (TypeScript 사용시)
  - .env.example

2.2 의존성 설치 및 설정
- 핵심 의존성 설치
  - 프레임워크 관련: 예) react, react-dom
  - 라우팅: 예) react-router-dom
  - 상태 관리: 예) @reduxjs/toolkit, react-redux
  - API 통신: 예) axios, react-query
  - UI 라이브러리: 예) @mui/material
- 개발 의존성 설치
  - TypeScript 사용시: typescript, @types/react
  - 린팅: eslint, @typescript-eslint/parser
  - 스타일링: styled-components/emotion
- 설정 완료 검증
  - npm run dev 실행 성공
  - 브라우저에서 기본 페이지 로딩 확인

**3. 기반 시스템 구축**

3.1 스타일 시스템 구축: '스타일가이드'대로 구축
- CSS 변수 시스템 구축
  - /src/styles/variables.css 생성
  - 컬러 팔레트 CSS 변수 정의
  - 타이포그래피 변수 정의
  - 간격(spacing) 시스템 정의
- 테마 설정
  - 기본 테마 객체 생성
  - 컬러/타이포그래피 커스터마이징
  - 반응형 브레이크포인트 설정
- 글로벌 스타일 적용
  - CSS Reset/Normalize
  - 기본 폰트 및 색상 적용
  - 반응형 기본 설정

3.2 라우팅 시스템 구축: '정보아키텍처' 참조
- 기본 라우터 설정
  - BrowserRouter/HashRouter 설정
  - 기본 라우트 구조 정의
  - 404 페이지 설정
- 보호된 라우트 구현 (인증 필요시)
  - PrivateRoute 컴포넌트 생성
  - 인증 상태 체크 로직
  - 로그인 리다이렉트 처리
- 네비게이션 컴포넌트
  - Header/Sidebar 네비게이션
  - 모바일 네비게이션 (필요시)
  - 활성 상태 표시

3.3 상태 관리 시스템 구축
- 스토어 초기 설정
  - 루트 스토어 생성
  - 기본 슬라이스 생성 (auth, ui 등)
  - 미들웨어 설정 (redux-thunk 등)
- 타입 정의
  - RootState 타입 정의
  - AppDispatch 타입 정의
  - 각 슬라이스별 State 타입 정의
- Provider 설정
  - App 컴포넌트에 Provider 래핑
  - 개발 도구 설정 (Redux DevTools)

**4. API 연동 시스템 구축: 'API명세서'와 'API매핑설계서' 참조**

4.1 API 기본 설정
- 환경 설정 파일 생성
  - public/runtime-env.js (런타임 설정)
  - .env 파일 설정
  - API 기본 URL 설정
- API 설정 모듈 생성
  - /src/services/api/config.ts
  - 각 서비스별 BASE_URL 정의
  - 공통 헤더/타임아웃 설정
- Axios 클라이언트 생성
  - /src/services/api/client.ts
  - 서비스별 클라이언트 인스턴스 생성
  - 공통 설정 적용

4.2 API 인터셉터 구현
- 요청 인터셉터
  - 인증 토큰 자동 추가
  - 공통 헤더 설정
  - 요청 로깅 (개발 환경)
- 응답 인터셉터
  - 공통 에러 처리
  - 토큰 만료 처리
  - 응답 데이터 정규화
- 에러 처리
  - 네트워크 오류 처리
  - HTTP 상태 코드별 처리
  - 사용자 친화적 에러 메시지

4.3 API 서비스 함수 구현
- 타입 정의
  - API 요청/응답 인터페이스 정의
  - /src/types/api.ts
  - 각 도메인별 타입 파일 생성
- 서비스 함수 구현
  - /src/services/[domain]/[domain]Api.ts
  - CRUD 기본 함수들 구현
  - 에러 처리 포함
- React Query 훅 구현
  - /src/hooks/use[Domain].ts
  - 캐싱 전략 설정
  - 로딩/에러 상태 관리

**5. 공통 컴포넌트 개발: '프로토타입' 참조**
- UI 기본 컴포넌트
  - Button, Input, Modal 등
  - Loading, Error 컴포넌트
  - Layout 컴포넌트
- 비즈니스 공통 컴포넌트
  - Header, Footer, Sidebar
  - 인증 관련 컴포넌트
  - 에러 바운더리
- 폼 관리 컴포넌트
  - React Hook Form 설정
  - 유효성 검사 스키마
  - 공통 폼 컴포넌트

**6. 각 페이지별 구현: 'UI/UX설계서'의 '2. 화면 목록 정의'에 정의된 순서로 아래 단계로 개발**
- 사용자가 제공한 페이지 관련된 유저스토리 파악
- 구현할 페이지의 프로토타입을 웹브라우저에서 모바일 사이즈로 재확인(playwright MCP 이용)
- 사용자가 제공한 정보를 이용하여 API의 요청과 응답 데이터 파악
- API와 연동하여 페이지 개발
- 빌드 및 에러 해결
- 사용자에게 페이지 테스트 요청
- 에러 해결 및 개선 사항 적용

## 출력 형식

- 프론트엔드 코드: `frontend/src/` 하위에 기능별 폴더 구조로 작성
- 각 도메인별 API 서비스: `frontend/src/services/[domain]/[domain]Api.ts`
- 각 도메인별 훅: `frontend/src/hooks/use[Domain].ts`
- 타입 정의: `frontend/src/types/api.ts`

## 품질 기준

- [ ] 기술스택 결정 → 프로젝트 초기 설정 → 기반 시스템 구축 → API 연동 순서 준수
- [ ] 반응형 UI 구현
- [ ] 백엔드 API 없이 완성 처리 금지
- [ ] API명세서와 반드시 일치하는 연동 구현
- [ ] 각 단계 완료 후 사용자 확인 수행

## 주의사항

- UI/UX설계서, 스타일가이드, 정보아키텍처, API매핑설계서를 기반으로 개발
- API명세서와 반드시 일치
- 각 개발 단계 완료 후 사용자에게 진행 여부 확인
- 프로토타입 화면 분석 시 playwright MCP를 이용하여 모바일 사이즈로 확인
- 기존 디렉토리/파일은 그대로 유지하면서 작업
