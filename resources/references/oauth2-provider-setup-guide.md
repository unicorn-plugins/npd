# OAuth2 Provider 앱 등록 가이드

## 목적

OAuth2/OIDC 소셜 로그인 구현 시, 각 Provider에서 앱을 등록하고 Client ID/Secret을 발급받는 절차를 안내한다.

## 필요한 환경변수

| Provider | Client ID 변수 | Client Secret 변수 |
|----------|---------------|-------------------|
| Google | `GOOGLE_CLIENT_ID` | `GOOGLE_CLIENT_SECRET` |
| 카카오 | `KAKAO_CLIENT_ID` | `KAKAO_CLIENT_SECRET` |
| 네이버 | `NAVER_CLIENT_ID` | `NAVER_CLIENT_SECRET` |

> 설계서에 명시된 Provider만 등록하면 된다. 모든 Provider를 등록할 필요 없음.

---

## Google

### 등록 절차

1. [Google Cloud Console](https://console.cloud.google.com/) 접속 → 로그인
2. 프로젝트 선택 (없으면 새 프로젝트 생성)
3. 좌측 메뉴 → **API 및 서비스** → **사용자 인증 정보**
4. **+ 사용자 인증 정보 만들기** → **OAuth 클라이언트 ID**
5. 동의 화면 미설정 시 **OAuth 동의 화면** 먼저 구성:
   - 앱 유형: **외부** (테스트 단계)
   - 앱 이름, 사용자 지원 이메일 입력
   - 범위(Scopes): `openid`, `profile`, `email` 추가
   - 테스트 사용자: 본인 이메일 추가
6. OAuth 클라이언트 ID 생성:
   - 애플리케이션 유형: **웹 애플리케이션**
   - 이름: 프로젝트명
   - **승인된 리디렉션 URI**: `http://localhost:8080/login/oauth2/code/google`
     - `8080` 부분은 인증 서비스 실제 포트로 교체
7. **클라이언트 ID**와 **클라이언트 보안 비밀번호** 복사

### 환경변수 설정

```
GOOGLE_CLIENT_ID=xxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxx
```

### 주의사항

- 동의 화면이 "테스트" 상태이면 등록된 테스트 사용자만 로그인 가능
- 프로덕션 배포 시 Google 검증 절차 필요

---

## 카카오 (Kakao)

### 등록 절차

1. [Kakao Developers](https://developers.kakao.com/) 접속 → 로그인
2. **내 애플리케이션** → **애플리케이션 추가하기**
3. 앱 이름, 사업자명 입력 → 저장
4. 생성된 앱 선택 → **앱 키** 탭에서 **REST API 키** 확인 (= Client ID)
5. **제품 설정** → **카카오 로그인** → **활성화 설정**: ON
6. **동의항목** 설정:
   - 닉네임: 필수 동의
   - 프로필 사진, 이메일: 필요 시 선택 동의
7. **카카오 로그인** → **Redirect URI** 등록:
   - `http://localhost:8080/login/oauth2/code/kakao`
   - `8080` 부분은 인증 서비스 실제 포트로 교체
8. **보안** 탭 → **Client Secret**: 코드 생성 → 활성화 상태로 변경 → 코드 복사

### 환경변수 설정

```
KAKAO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
KAKAO_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 주의사항

- REST API 키가 Client ID 역할 (네이티브 앱 키와 혼동 금지)
- Client Secret은 **보안** 탭에서 별도 생성 필요 (기본 미생성)
- `client-authentication-method: client_secret_post` 필수 (카카오는 POST body 방식)

---

## 네이버 (Naver)

### 등록 절차

1. [Naver Developers](https://developers.naver.com/) 접속 → 로그인
2. **Application** → **애플리케이션 등록**
3. 앱 이름 입력
4. **사용 API**: **네이버 로그인** 선택
5. **제공 정보 선택**: 회원이름(필수), 이메일(선택), 프로필 사진(선택) 등
6. **환경 추가**: **PC웹** 선택
7. **서비스 URL**: `http://localhost:8080`
8. **Callback URL**: `http://localhost:8080/login/oauth2/code/naver`
   - `8080` 부분은 인증 서비스 실제 포트로 교체
9. 등록 완료 후 **Client ID**와 **Client Secret** 확인

### 환경변수 설정

```
NAVER_CLIENT_ID=xxxxxxxxxxxxxxxx
NAVER_CLIENT_SECRET=xxxxxxxxxx
```

### 주의사항

- 네이버는 사용자 정보 응답이 `response` 객체 안에 래핑됨 → `user-name-attribute: response` 설정 필수
- 개발 상태에서는 앱 등록자 계정만 로그인 가능 (검수 완료 전)

---

## `.env` / `.env.example` 반영

발급받은 값을 프로젝트의 `.env`에 추가한다.

```bash
# OAuth2 Provider Credentials
# 설계서에 명시된 Provider만 설정

# Google (설계서에 Google 로그인 있는 경우)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# 카카오 (설계서에 카카오 로그인 있는 경우)
KAKAO_CLIENT_ID=
KAKAO_CLIENT_SECRET=

# 네이버 (설계서에 네이버 로그인 있는 경우)
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
```

> `.env.example`에는 빈 값으로 키 이름만 기재하고, 실제 값은 `.env`에만 작성한다.
> `.env`는 `.gitignore`에 포함하여 저장소에 커밋하지 않는다.

---

## Redirect URI 패턴

Spring Security OAuth2 Client의 기본 Redirect URI 패턴:

```
{baseUrl}/login/oauth2/code/{registrationId}
```

| Provider | registrationId | 로컬 Redirect URI 예시 |
|----------|---------------|----------------------|
| Google | `google` | `http://localhost:8080/login/oauth2/code/google` |
| 카카오 | `kakao` | `http://localhost:8080/login/oauth2/code/kakao` |
| 네이버 | `naver` | `http://localhost:8080/login/oauth2/code/naver` |

- `{baseUrl}`의 포트는 인증을 처리하는 서비스의 실제 포트에 맞춰야 한다
- Gateway를 통해 접근하는 경우 Gateway 포트를 Redirect URI로 등록
