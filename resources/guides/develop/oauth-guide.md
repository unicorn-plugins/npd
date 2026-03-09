# OAuth2 인증 개발 가이드

> 대상: 백엔드(Spring Boot) + 프론트엔드(React / Vue / Flutter) 개발자
> 기준 스택: Spring Boot 3.x, Spring Security OAuth2 Client, React 19, Vue 3, Flutter 3.x

---

## 1. 아키텍처 개요

OAuth 공급자에 따라 두 가지 흐름을 사용함.

### 1-1. GitHub / Google — 백엔드 시작 흐름 (Spring Security OAuth2)

```
사용자 (브라우저 또는 앱)
  │
  ├─ 1. GitHub/Google 버튼 클릭
  │       ↓
  │   {백엔드}/oauth2/authorization/{provider} 로 이동
  │
  ├─ 2. 백엔드(Spring Security) → 인가 서버로 리다이렉트
  │
  ├─ 3. 사용자 로그인 완료
  │       ↓
  │   {백엔드}/login/oauth2/code/{provider} 로 code 전달
  │
  ├─ 4. 백엔드: code 교환 → 사용자 정보 조회 → DB 저장 → JWT 발급
  │       ↓
  │   {프론트엔드}/oauth2/callback?accessToken=...&refreshToken=...
  │
  └─ 5. 프론트엔드: 토큰 저장 → 홈 화면 이동
```

### 1-2. Kakao — 프론트엔드 시작 흐름 (Custom REST Endpoint)

```
사용자 (브라우저 또는 앱)
  │
  ├─ 1. 카카오 버튼 클릭
  │       ↓
  │   https://kauth.kakao.com/oauth/authorize?client_id=...&redirect_uri=...
  │
  ├─ 2. 카카오 로그인 완료
  │       ↓
  │   {프론트엔드}/login?code=... 로 인가 코드 전달
  │
  ├─ 3. 프론트엔드: 코드 추출 → POST {백엔드}/api/v1/auth/kakao
  │
  ├─ 4. 백엔드: code → 카카오 토큰 교환 → 사용자 정보 조회 → DB 저장 → JWT 발급
  │       ↓
  │   { accessToken, memberId, isNewUser, ... } JSON 응답
  │
  └─ 5. 프론트엔드: 토큰 저장 → 홈 화면 이동
```

> **두 흐름의 차이**
> - GitHub/Google: Spring Security가 OAuth 흐름 전체를 처리, 백엔드가 최종 리다이렉트
> - Kakao: 프론트엔드가 카카오 인가 페이지로 직접 이동, 백엔드는 REST API로만 동작

### 플랫폼별 콜백 처리 방식

| 플랫폼 | GitHub / Google 콜백 | Kakao 콜백 |
|--------|---------------------|-----------|
| React / Vue (웹) | `{frontend}/oauth2/callback?accessToken=...` | `{frontend}/login?code=...` |
| Flutter Web | `{frontend}/oauth2/callback?accessToken=...` | `{frontend}/login?code=...` |
| Flutter Mobile | `myapp://oauth2/callback?accessToken=...` | `myapp://login?code=...` |

---

## 2. OAuth App 설정 (최초 1회)

### 2-1. GitHub OAuth App

1. [github.com/settings/developers](https://github.com/settings/developers) 접속
2. **OAuth Apps** → **New OAuth App**
3. 항목 입력:

| 항목 | 값 |
|------|-----|
| Application name | 프로젝트명 |
| Homepage URL | `http://localhost:3000` |
| Authorization callback URL | `http://localhost:8080/login/oauth2/code/github` |

4. **Register application** → `Client ID`, `Client Secret` 복사
5. `.env` 파일에 설정:

```env
GITHUB_CLIENT_ID=발급받은_CLIENT_ID
GITHUB_CLIENT_SECRET=발급받은_CLIENT_SECRET
```

### 2-2. Google OAuth App

1. [console.cloud.google.com](https://console.cloud.google.com) 접속
2. **API 및 서비스** → **사용자 인증 정보** → **OAuth 2.0 클라이언트 ID** 생성
3. 애플리케이션 유형: **웹 애플리케이션**
4. **승인된 리디렉션 URI** 추가:

```
http://localhost:8080/login/oauth2/code/google
```

5. `Client ID`, `Client Secret` 복사
6. `.env` 파일에 설정:

```env
GOOGLE_CLIENT_ID=발급받은_CLIENT_ID
GOOGLE_CLIENT_SECRET=발급받은_CLIENT_SECRET
```

> **운영 환경 추가 시**: 위 콜백 URL의 `localhost:8080` → 실제 도메인으로 변경 후 추가 등록

### 2-3. Kakao OAuth App

1. [developers.kakao.com](https://developers.kakao.com) 접속 → **내 애플리케이션** → **애플리케이션 추가하기**
2. 앱 아이콘, 앱 이름, 사업자명 입력 → 저장
3. **앱 키** 탭에서 `REST API 키` 복사 (`KAKAO_CLIENT_ID`로 사용)
4. **카카오 로그인** → 활성화 설정 ON
5. **Redirect URI** 등록:

```
http://localhost:3000/login
```

6. **동의항목** → `닉네임`, `카카오계정(이메일)` 수집 동의 설정
7. **보안** 탭 → **Client Secret** 생성 및 복사 (선택, 권장)
8. `.env` 파일에 설정:

```env
KAKAO_CLIENT_ID=발급받은_REST_API_키
KAKAO_CLIENT_SECRET=발급받은_CLIENT_SECRET
KAKAO_REDIRECT_URI=http://localhost:3000/login
```

> **운영 환경 추가 시**: Redirect URI에 실제 프론트엔드 도메인 추가 등록

---

## 3. 백엔드 구현 (Spring Boot)

### 3-1. 의존성 (`build.gradle`)

```groovy
// GitHub / Google (Spring Security OAuth2 Client)
implementation 'org.springframework.boot:spring-boot-starter-oauth2-client'
implementation 'org.springframework.boot:spring-boot-starter-security'

// Kakao (Custom REST Client — Spring Web만 필요)
implementation 'org.springframework.boot:spring-boot-starter-web'
implementation 'org.springframework.boot:spring-boot-starter-validation'
```

### 3-2. application.yml 설정

```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          github:
            client-id: ${GITHUB_CLIENT_ID}
            client-secret: ${GITHUB_CLIENT_SECRET}
            scope: read:user, user:email
          google:
            client-id: ${GOOGLE_CLIENT_ID}
            client-secret: ${GOOGLE_CLIENT_SECRET}
            scope: profile, email

# Kakao 전용 설정 (Spring Security OAuth2 미사용)
kakao:
  oauth:
    client-id: ${KAKAO_CLIENT_ID}
    client-secret: ${KAKAO_CLIENT_SECRET}
    redirect-uri: ${KAKAO_REDIRECT_URI}

cors:
  allowed-origins: ${CORS_ALLOWED_ORIGINS:http://localhost:3000}
```

### 3-3. SecurityConfig

```java
@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    @Value("${cors.allowed-origins:http://localhost:3000}")
    private String allowedOrigins;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(AbstractHttpConfigurer::disable)
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .oauth2Login(oauth2 -> oauth2
                .successHandler(oAuth2SuccessHandler)          // GitHub / Google
            )
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**", "/error").permitAll()
                .requestMatchers(HttpMethod.POST, "/api/v1/auth/kakao").permitAll()  // Kakao
                .anyRequest().authenticated()
            )
            .addFilterBefore(
                new JwtAuthenticationFilter(jwtTokenProvider),
                UsernamePasswordAuthenticationFilter.class
            )
            .build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOriginPatterns(Arrays.asList(allowedOrigins.split(",")));
        config.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"));
        config.setAllowedHeaders(Arrays.asList("Authorization", "Content-Type", "Accept", "Origin"));
        config.setAllowCredentials(true);
        config.setMaxAge(3600L);
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        return source;
    }
}
```

### 3-4. OAuth2SuccessHandler — GitHub/Google JWT 발급 및 프론트엔드 리다이렉트

```java
@Component
public class OAuth2SuccessHandler extends SimpleUrlAuthenticationSuccessHandler {

    @Override
    public void onAuthenticationSuccess(
            HttpServletRequest request,
            HttpServletResponse response,
            Authentication authentication) throws IOException {

        OAuth2UserPrincipal oAuth2User = (OAuth2UserPrincipal) authentication.getPrincipal();

        // 1. DB에서 사용자 조회 또는 신규 생성
        String userId = authService.findOrCreateUser(
            oAuth2User.getEmail(),
            oAuth2User.getRegistrationId().toUpperCase(),
            oAuth2User.getName(),
            oAuth2User.getProfileImageUrl()
        );

        // 2. JWT 발급
        String accessToken = jwtTokenProvider.createAccessToken(userId, oAuth2User.getName());
        String refreshToken = jwtTokenProvider.createRefreshToken(userId);
        authService.saveRefreshToken(userId, refreshToken);

        // 3. 프론트엔드 콜백으로 리다이렉트
        String frontendOrigin = System.getenv("CORS_ALLOWED_ORIGINS") != null
            ? System.getenv("CORS_ALLOWED_ORIGINS").split(",")[0].trim()
            : "http://localhost:3000";

        String redirectUrl = frontendOrigin + "/oauth2/callback"
            + "?accessToken=" + accessToken
            + "&refreshToken=" + refreshToken;

        getRedirectStrategy().sendRedirect(request, response, redirectUrl);
    }
}
```

### 3-5. CustomOAuth2UserService — GitHub/Google 공급자별 사용자 정보 추출

```java
@Service
public class CustomOAuth2UserService extends DefaultOAuth2UserService {

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oAuth2User = super.loadUser(userRequest);
        String registrationId = userRequest.getClientRegistration().getRegistrationId();

        String email, name, profileImageUrl;

        if ("github".equals(registrationId)) {
            email = (String) oAuth2User.getAttributes().get("email");
            name  = (String) oAuth2User.getAttributes().get("login");
            profileImageUrl = (String) oAuth2User.getAttributes().get("avatar_url");
        } else { // google
            email = (String) oAuth2User.getAttributes().get("email");
            name  = (String) oAuth2User.getAttributes().get("name");
            profileImageUrl = (String) oAuth2User.getAttributes().get("picture");
        }

        return new OAuth2UserPrincipal(registrationId, email, name, profileImageUrl, oAuth2User.getAuthorities());
    }
}
```

### 3-6. Kakao OAuth 구현 — Custom REST Client

Kakao는 Spring Security OAuth2 Client를 사용하지 않고,
백엔드가 카카오 API를 직접 호출하는 방식으로 구현.

#### KakaoOAuthConfig.java

```java
@Configuration
public class KakaoOAuthConfig {

    public static final String TOKEN_URI    = "https://kauth.kakao.com/oauth/token";
    public static final String USER_INFO_URI = "https://kapi.kakao.com/v2/user/me";

    @Value("${kakao.oauth.client-id}")
    private String clientId;

    @Value("${kakao.oauth.client-secret}")
    private String clientSecret;

    @Value("${kakao.oauth.redirect-uri}")
    private String redirectUri;

    public String getClientId()     { return clientId; }
    public String getClientSecret() { return clientSecret; }
    public String getRedirectUri()  { return redirectUri; }
}
```

#### KakaoProfile.java (DTO)

```java
@Builder
public record KakaoProfile(
    String kakaoId,    // 카카오 회원 고유 ID
    String email,      // 연동 이메일
    String nickname    // 닉네임
) {}
```

#### KakaoOAuthClient.java

```java
@Component
@RequiredArgsConstructor
public class KakaoOAuthClient {

    private final KakaoOAuthConfig config;
    private final RestTemplate restTemplate;

    /** 인증 코드 → 카카오 액세스 토큰 교환 */
    public String getAccessToken(String authorizationCode) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

        MultiValueMap<String, String> params = new LinkedMultiValueMap<>();
        params.add("grant_type",    "authorization_code");
        params.add("client_id",     config.getClientId());
        params.add("client_secret", config.getClientSecret());
        params.add("redirect_uri",  config.getRedirectUri());
        params.add("code",          authorizationCode);

        ResponseEntity<Map> response = restTemplate.exchange(
            KakaoOAuthConfig.TOKEN_URI,
            HttpMethod.POST,
            new HttpEntity<>(params, headers),
            Map.class
        );

        return (String) response.getBody().get("access_token");
    }

    /** 카카오 액세스 토큰 → 사용자 정보 조회 */
    @SuppressWarnings("unchecked")
    public KakaoProfile getUserProfile(String kakaoAccessToken) {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(kakaoAccessToken);

        ResponseEntity<Map> response = restTemplate.exchange(
            KakaoOAuthConfig.USER_INFO_URI,
            HttpMethod.GET,
            new HttpEntity<>(headers),
            Map.class
        );

        Map<String, Object> body        = response.getBody();
        String              kakaoId     = String.valueOf(body.get("id"));
        Map<String, Object> kakaoAccount = (Map<String, Object>) body.get("kakao_account");

        String email    = null;
        String nickname = "사용자";

        if (kakaoAccount != null) {
            email = (String) kakaoAccount.get("email");
            Map<String, Object> profile = (Map<String, Object>) kakaoAccount.get("profile");
            if (profile != null) nickname = (String) profile.get("nickname");
        }

        return KakaoProfile.builder()
            .kakaoId(kakaoId)
            .email(email)
            .nickname(nickname)
            .build();
    }
}
```

#### KakaoLoginRequest.java / AuthResponse.java

```java
public record KakaoLoginRequest(
    @NotBlank(message = "카카오 인증 코드는 필수입니다.")
    String authorizationCode
) {}
```

```java
@Builder
public record AuthResponse(
    String  accessToken,         // JWT
    String  tokenType,           // "Bearer"
    long    expiresIn,           // 초 단위
    String  memberId,            // UUID
    boolean isNewUser,
    boolean onboardingCompleted,
    String  nickname
) {}
```

#### AuthController.java

```java
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    /**
     * POST /api/v1/auth/kakao
     * 응답: 200 OK (기존 회원) / 201 Created (신규 회원)
     */
    @PostMapping("/kakao")
    public ResponseEntity<AuthResponse> kakaoLogin(
            @Valid @RequestBody KakaoLoginRequest request) {
        AuthResponse response = authService.kakaoLogin(request);
        HttpStatus status = response.isNewUser() ? HttpStatus.CREATED : HttpStatus.OK;
        return ResponseEntity.status(status).body(response);
    }
}
```

#### AuthServiceImpl.java — 카카오 로그인 로직

```java
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final KakaoOAuthClient   kakaoOAuthClient;
    private final MemberRepository   memberRepository;
    private final JwtTokenProvider   jwtTokenProvider;

    @Override
    @Transactional
    public AuthResponse kakaoLogin(KakaoLoginRequest request) {
        // 1. 인증 코드 → 카카오 액세스 토큰
        String kakaoAccessToken = kakaoOAuthClient.getAccessToken(request.authorizationCode());

        // 2. 카카오 액세스 토큰 → 사용자 정보
        KakaoProfile profile = kakaoOAuthClient.getUserProfile(kakaoAccessToken);

        // 3. 기존 회원 조회 또는 신규 생성
        Optional<MemberEntity> existing = memberRepository.findByKakaoId(profile.kakaoId());
        boolean       isNewUser;
        MemberEntity  member;

        if (existing.isPresent()) {
            member    = existing.get();
            isNewUser = false;
        } else {
            member = MemberEntity.builder()
                .memberId(UUID.randomUUID().toString())
                .kakaoId(profile.kakaoId())
                .email(profile.email())
                .nickname(profile.nickname())
                .build();
            memberRepository.save(member);
            isNewUser = true;
        }

        // 4. 자체 JWT 발급
        String accessToken = jwtTokenProvider.createAccessToken(member.getMemberId(), "ROLE_USER");

        return AuthResponse.builder()
            .accessToken(accessToken)
            .tokenType("Bearer")
            .memberId(member.getMemberId())
            .isNewUser(isNewUser)
            .nickname(member.getNickname())
            .build();
    }
}
```

---

## 4. 프론트엔드 구현

### 4-1. React

#### GitHub/Google 로그인 버튼

```typescript
// src/pages/landing/index.tsx
function loginWithProvider(provider: 'github' | 'google') {
  const backendUrl =
    (window as any).__runtime_config__?.BACKEND_URL ?? 'http://localhost:8080'
  window.location.href = `${backendUrl}/oauth2/authorization/${provider}`
}
```

#### GitHub/Google OAuth 콜백 페이지

```typescript
// src/pages/oauth-callback/index.tsx
import { useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'

export default function OAuthCallbackPage() {
  const { setToken } = useAuthStore()

  useEffect(() => {
    const params      = new URLSearchParams(window.location.search)
    const accessToken = params.get('accessToken')
    const refreshToken = params.get('refreshToken')

    if (accessToken) {
      localStorage.setItem('accessToken', accessToken)
      if (refreshToken) localStorage.setItem('refreshToken', refreshToken)
      setToken(accessToken)
      window.location.replace('/home')
    } else {
      window.location.replace('/')
    }
  }, [])

  return <div>로그인 처리 중...</div>
}
```

> `navigate()` 대신 `window.location.replace()` 사용 이유:
> Zustand 상태 업데이트와 React Router의 PrivateRoute 평가 타이밍 불일치 방지

#### Kakao 로그인 버튼 및 콜백 처리

```typescript
// src/pages/login/index.tsx
import { useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'

export default function LoginPage() {
  const { setToken } = useAuthStore()

  function loginWithProvider(provider: 'github' | 'google') {
    const backendUrl =
      (window as any).__runtime_config__?.BACKEND_URL ?? 'http://localhost:8080'
    window.location.href = `${backendUrl}/oauth2/authorization/${provider}`
  }

  // 카카오 리다이렉트 후 URL에 code 파라미터가 붙어서 돌아옴
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code   = params.get('code')
    if (!code) return

    fetch('/api/v1/auth/kakao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ authorizationCode: code }),
    })
      .then(res => res.json())
      .then(data => {
        localStorage.setItem('accessToken', data.accessToken)
        setToken(data.accessToken)
        window.location.replace(data.isNewUser ? '/onboarding' : '/home')
      })
      .catch(() => window.location.replace('/'))
  }, [])

  function loginWithKakao() {
    const KAKAO_CLIENT_ID  =
      (window as any).__runtime_config__?.KAKAO_CLIENT_ID ?? ''
    const REDIRECT_URI     = encodeURIComponent(`${window.location.origin}/login`)
    window.location.href =
      `https://kauth.kakao.com/oauth/authorize?client_id=${KAKAO_CLIENT_ID}&redirect_uri=${REDIRECT_URI}&response_type=code`
  }

  return (
    <div>
      <button onClick={() => loginWithProvider('github')}>GitHub으로 로그인</button>
      <button onClick={() => loginWithProvider('google')}>Google로 로그인</button>
      <button onClick={loginWithKakao} style={{ background: '#FEE500', color: '#191919' }}>
        카카오로 로그인
      </button>
    </div>
  )
}
```

#### 라우터 등록

```typescript
// src/router/index.tsx
{
  element: <AuthLayout />,
  children: [
    { path: '/',               element: <LoginPage /> },         // Kakao 콜백도 이 페이지에서 처리
    { path: '/oauth2/callback', element: <OAuthCallbackPage /> }, // GitHub/Google 콜백
    { path: '/onboarding',     element: <OnboardingPage /> },
  ],
}
```

---

### 4-2. Vue 3

#### GitHub/Google 로그인 버튼

```vue
<!-- src/pages/LoginPage.vue -->
<script setup lang="ts">
function loginWithProvider(provider: 'github' | 'google') {
  const backendUrl = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8080'
  window.location.href = `${backendUrl}/oauth2/authorization/${provider}`
}
</script>
```

#### GitHub/Google OAuth 콜백 페이지

```vue
<!-- src/pages/OAuthCallbackPage.vue -->
<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()

onMounted(() => {
  const params      = new URLSearchParams(window.location.search)
  const accessToken = params.get('accessToken')
  const refreshToken = params.get('refreshToken')

  if (accessToken) {
    localStorage.setItem('accessToken', accessToken)
    if (refreshToken) localStorage.setItem('refreshToken', refreshToken)
    authStore.setToken(accessToken)
    window.location.replace('/home')
  } else {
    window.location.replace('/')
  }
})
</script>

<template>
  <div>로그인 처리 중...</div>
</template>
```

#### Kakao 로그인 버튼 및 콜백 처리

```vue
<!-- src/pages/LoginPage.vue -->
<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const router    = useRouter()
const authStore = useAuthStore()

function loginWithProvider(provider: 'github' | 'google') {
  const backendUrl = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8080'
  window.location.href = `${backendUrl}/oauth2/authorization/${provider}`
}

// 카카오 리다이렉트 후 code 파라미터 자동 처리
onMounted(async () => {
  const params = new URLSearchParams(window.location.search)
  const code   = params.get('code')
  if (!code) return

  try {
    const res  = await fetch('/api/v1/auth/kakao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ authorizationCode: code }),
    })
    const data = await res.json()
    localStorage.setItem('accessToken', data.accessToken)
    authStore.setToken(data.accessToken)
    window.location.replace(data.isNewUser ? '/onboarding' : '/home')
  } catch {
    router.replace('/')
  }
})

function loginWithKakao() {
  const kakaoClientId = import.meta.env.VITE_KAKAO_CLIENT_ID ?? ''
  const redirectUri   = encodeURIComponent(`${window.location.origin}/login`)
  window.location.href =
    `https://kauth.kakao.com/oauth/authorize?client_id=${kakaoClientId}&redirect_uri=${redirectUri}&response_type=code`
}
</script>

<template>
  <button @click="loginWithProvider('github')">GitHub으로 로그인</button>
  <button @click="loginWithProvider('google')">Google로 로그인</button>
  <button @click="loginWithKakao" class="kakao-btn">카카오로 로그인</button>
</template>

<style scoped>
.kakao-btn { background: #FEE500; color: #191919; }
</style>
```

#### Pinia Store (authStore)

```typescript
// src/stores/authStore.ts
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('accessToken') ?? null as string | null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  actions: {
    setToken(token: string) { this.token = token },
    logout() {
      this.token = null
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
    },
  },
})
```

#### 라우터 등록

```typescript
// src/router/index.ts
const routes = [
  { path: '/',                component: LoginPage },         // Kakao 콜백도 이 페이지에서 처리
  { path: '/oauth2/callback', component: OAuthCallbackPage }, // GitHub/Google 콜백
  { path: '/home',            component: HomePage, meta: { requiresAuth: true } },
]
```

---

### 4-3. Flutter

Flutter는 플랫폼(Web / Mobile)에 따라 OAuth 처리 방식이 다름.

#### 의존성 추가 (`pubspec.yaml`)

```yaml
dependencies:
  flutter_web_auth_2: ^4.0.0       # 인앱 브라우저 + 콜백 캡처 (Mobile)
  flutter_secure_storage: ^9.0.0   # 토큰 안전 저장
  go_router: ^14.0.0               # 라우팅
  http: ^1.2.0                     # HTTP 클라이언트
```

#### Mobile — Custom URL Scheme 콜백

**AndroidManifest.xml** (`android/app/src/main/AndroidManifest.xml`)

```xml
<!-- GitHub/Google 콜백: myapp://oauth2/callback -->
<activity android:name="com.linusu.flutter_web_auth_2.CallbackActivity"
          android:exported="true">
  <intent-filter android:label="flutter_web_auth_2_oauth2">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="myapp" android:host="oauth2" />
  </intent-filter>
  <!-- Kakao 콜백: myapp://login -->
  <intent-filter android:label="flutter_web_auth_2_kakao">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="myapp" android:host="login" />
  </intent-filter>
</activity>
```

**Info.plist** (`ios/Runner/Info.plist`)

```xml
<key>CFBundleURLTypes</key>
<array>
  <dict>
    <key>CFBundleURLSchemes</key>
    <array>
      <string>myapp</string>
    </array>
  </dict>
</array>
```

#### AuthService (`lib/services/auth_service.dart`)

```dart
import 'dart:convert';
import 'package:flutter_web_auth_2/flutter_web_auth_2.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class AuthService {
  static const _storage      = FlutterSecureStorage();
  static const _backendUrl   = 'http://localhost:8080';
  static const _frontendUrl  = 'http://localhost:3000';
  static const _callbackScheme = 'myapp';

  // ── GitHub / Google (백엔드 시작 흐름) ──────────────────────────────────────
  Future<bool> loginWithProvider(String provider) async {
    final url = '$_backendUrl/oauth2/authorization/$provider';
    try {
      final result = await FlutterWebAuth2.authenticate(
        url: url,
        callbackUrlScheme: _callbackScheme,
      );
      // 백엔드가 myapp://oauth2/callback?accessToken=...&refreshToken=... 로 리다이렉트
      final uri          = Uri.parse(result);
      final accessToken  = uri.queryParameters['accessToken'];
      final refreshToken = uri.queryParameters['refreshToken'];
      if (accessToken == null) return false;
      await _storage.write(key: 'accessToken',  value: accessToken);
      if (refreshToken != null) {
        await _storage.write(key: 'refreshToken', value: refreshToken);
      }
      return true;
    } catch (_) {
      return false;
    }
  }

  // ── Kakao (프론트엔드 시작 흐름) ────────────────────────────────────────────
  Future<Map<String, dynamic>?> loginWithKakao(String kakaoClientId) async {
    // 모바일은 myapp://login 으로 콜백 받아야 flutter_web_auth_2가 캡처 가능
    // Kakao Developers → Redirect URI 에 'myapp://login' 등록 필수
    const mobileRedirectUri = '$_callbackScheme://login';
    final redirectUri       = Uri.encodeComponent(mobileRedirectUri);
    final kakaoAuthUrl      =
        'https://kauth.kakao.com/oauth/authorize'
        '?client_id=$kakaoClientId'
        '&redirect_uri=$redirectUri'
        '&response_type=code';

    try {
      // 인앱 브라우저로 카카오 인가 페이지 열기
      // 카카오가 myapp://login?code=... 으로 리다이렉트 → 앱이 캡처
      final result = await FlutterWebAuth2.authenticate(
        url: kakaoAuthUrl,
        callbackUrlScheme: _callbackScheme,
      );

      final uri  = Uri.parse(result);
      final code = uri.queryParameters['code'];
      if (code == null) return null;

      // 백엔드 REST API로 인가 코드 전달
      final response = await http.post(
        Uri.parse('$_backendUrl/api/v1/auth/kakao'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'authorizationCode': code}),
      );

      if (response.statusCode != 200 && response.statusCode != 201) return null;

      final data        = jsonDecode(response.body) as Map<String, dynamic>;
      final accessToken = data['accessToken'] as String?;
      if (accessToken == null) return null;

      await _storage.write(key: 'accessToken', value: accessToken);
      return data;
    } catch (_) {
      return null;
    }
  }

  Future<String?> getAccessToken() => _storage.read(key: 'accessToken');
  Future<void>    logout()         => _storage.deleteAll();
}
```

> **Kakao Mobile 콜백 URL**: `KAKAO_REDIRECT_URI`를 `myapp://login` 형태로 설정하거나,
> Kakao Developer Console에 `myapp://login` 추가 등록 필요

#### 로그인 화면 (`lib/screens/login_screen.dart`)

```dart
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../services/auth_service.dart';

class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  static const _kakaoClientId = String.fromEnvironment('KAKAO_CLIENT_ID');

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(
              onPressed: () => _login(context, 'github'),
              child: const Text('GitHub으로 로그인'),
            ),
            ElevatedButton(
              onPressed: () => _login(context, 'google'),
              child: const Text('Google로 로그인'),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFFEE500),
                foregroundColor: const Color(0xFF191919),
              ),
              onPressed: () => _loginWithKakao(context),
              child: const Text('카카오로 로그인'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _login(BuildContext context, String provider) async {
    final ok = await AuthService().loginWithProvider(provider);
    if (ok && context.mounted) context.go('/home');
  }

  Future<void> _loginWithKakao(BuildContext context) async {
    final data = await AuthService().loginWithKakao(_kakaoClientId);
    if (data == null || !context.mounted) return;
    context.go(data['isNewUser'] == true ? '/onboarding' : '/home');
  }
}
```

#### Flutter Web — 브라우저 리다이렉트 방식

```dart
// lib/screens/login_screen_web.dart
import 'dart:html' as html;
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;

class LoginScreenWeb extends StatefulWidget {
  const LoginScreenWeb({super.key});
  @override
  State<LoginScreenWeb> createState() => _LoginScreenWebState();
}

class _LoginScreenWebState extends State<LoginScreenWeb> {
  static const _storage    = FlutterSecureStorage();
  static const _backendUrl = 'http://localhost:8080';

  @override
  void initState() {
    super.initState();
    _handleKakaoCallback();
  }

  Future<void> _handleKakaoCallback() async {
    final uri  = Uri.parse(html.window.location.href);
    final code = uri.queryParameters['code'];
    if (code == null) return;

    final response = await http.post(
      Uri.parse('$_backendUrl/api/v1/auth/kakao'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'authorizationCode': code}),
    );
    if (response.statusCode != 200 && response.statusCode != 201) return;

    final data        = jsonDecode(response.body) as Map<String, dynamic>;
    final accessToken = data['accessToken'] as String?;
    if (accessToken == null) return;

    await _storage.write(key: 'accessToken', value: accessToken);
    if (mounted) {
      context.go(data['isNewUser'] == true ? '/onboarding' : '/home');
    }
  }

  void _loginWithProvider(String provider) {
    html.window.location.href = '$_backendUrl/oauth2/authorization/$provider';
  }

  void _loginWithKakao() {
    const kakaoClientId = String.fromEnvironment('KAKAO_CLIENT_ID');
    final redirectUri   = Uri.encodeComponent('${html.window.location.origin}/login');
    html.window.location.href =
        'https://kauth.kakao.com/oauth/authorize'
        '?client_id=$kakaoClientId'
        '&redirect_uri=$redirectUri'
        '&response_type=code';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(
              onPressed: () => _loginWithProvider('github'),
              child: const Text('GitHub으로 로그인'),
            ),
            ElevatedButton(
              onPressed: () => _loginWithProvider('google'),
              child: const Text('Google으로 로그인'),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFFEE500),
                foregroundColor: const Color(0xFF191919),
              ),
              onPressed: _loginWithKakao,
              child: const Text('카카오로 로그인'),
            ),
          ],
        ),
      ),
    );
  }
}
```

#### 라우터 등록 (`lib/router.dart`)

```dart
final router = GoRouter(
  routes: [
    GoRoute(path: '/',            builder: (_, __) => const LoginScreen()),
    GoRoute(path: '/oauth2/callback', builder: (_, __) => const OAuthCallbackScreen()), // GitHub/Google
    GoRoute(path: '/home',        builder: (_, __) => const HomeScreen()),
    GoRoute(path: '/onboarding',  builder: (_, __) => const OnboardingScreen()),
  ],
);
```

---

## 5. 환경변수 정리

### 백엔드

| 변수명 | 예시값 | 설명 |
|--------|--------|------|
| `GITHUB_CLIENT_ID` | `Ov23libzfSr2VFmfT2Ar` | GitHub OAuth App Client ID |
| `GITHUB_CLIENT_SECRET` | `ed378a1...` | GitHub OAuth App Client Secret |
| `GOOGLE_CLIENT_ID` | `377875895536-8jpq...` | Google OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | `GOCSPX-...` | Google OAuth Client Secret |
| `KAKAO_CLIENT_ID` | `abc123def456...` | Kakao REST API 키 |
| `KAKAO_CLIENT_SECRET` | `xyz789...` | Kakao Client Secret (선택, 권장) |
| `KAKAO_REDIRECT_URI` | `http://localhost:3000/login` | 카카오 인가 후 리다이렉트 URI |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | 프론트엔드 Origin |
| `JWT_SECRET` | `dev-jwt-secret-key-...` | JWT 서명 키 |

### 프론트엔드 (React / Vue)

| 변수명 | 예시값 | 설명 |
|--------|--------|------|
| `VITE_BACKEND_URL` | `http://localhost:8080` | 백엔드 API 기본 URL |
| `VITE_KAKAO_CLIENT_ID` | `abc123def456...` | Kakao REST API 키 (프론트에서 인가 URL 생성 시 사용) |

---

## 6. 콜백 URL 요약

| 공급자 | 등록 위치 | 등록할 URL |
|--------|----------|-----------|
| GitHub | GitHub OAuth App → Authorization callback URL | `http://localhost:8080/login/oauth2/code/github` |
| Google | Google Cloud Console → 승인된 리디렉션 URI | `http://localhost:8080/login/oauth2/code/google` |
| Kakao (웹) | Kakao Developers → Redirect URI | `http://localhost:3000/login` |
| Kakao (Mobile) | Kakao Developers → Redirect URI | `myapp://login` |

> **운영 환경**: `localhost` 포트 → 실제 도메인으로 변경 후 각 콘솔에 추가 등록

---

## 7. 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| GitHub: "The redirect_uri is not associated" | GitHub App에 콜백 URL 미등록 | `http://localhost:8080/login/oauth2/code/github` 등록 |
| Google: "400 redirect_uri_mismatch" | Google Console에 콜백 URL 미등록 | `http://localhost:8080/login/oauth2/code/google` 등록 |
| Kakao: "KOE006 redirect_uri mismatch" | Kakao Developers에 Redirect URI 미등록 | `http://localhost:3000/login` 등록 확인 |
| Kakao: "KOE101 invalid client_id" | KAKAO_CLIENT_ID 오류 | REST API 키 재확인 (앱 키 탭) |
| Kakao: 이메일이 null | 동의항목 미설정 | Kakao Developers 동의항목에서 이메일 수집 활성화 |
| 콜백 후 Whitelabel Error (8080) | `OAuth2SuccessHandler` 상대경로 리다이렉트 | `frontendOrigin + "/oauth2/callback"` 절대 URL로 수정 |
| React: 콜백 후 `/` 로 리다이렉트 (토큰 있음) | React Router PrivateRoute 타이밍 이슈 | `window.location.replace('/home')` 사용 |
| Vue: 콜백 후 store 인증 상태 미반영 | Pinia store 초기화 타이밍 이슈 | `window.location.replace('/home')` 사용 |
| Flutter Mobile: 콜백 URL 캡처 안 됨 | Custom URL Scheme 미등록 | AndroidManifest.xml / Info.plist에 `myapp` scheme 등록 |
| Flutter Mobile: FlutterWebAuth2 예외 발생 | Redirect URI scheme 불일치 | Kakao Developers에 `myapp://login` 등록 확인 |
| 백엔드 코드 수정 후 미반영 | 서비스 재시작 필요 | `python3 tools/run-backend.py user-service --config-dir .` |
