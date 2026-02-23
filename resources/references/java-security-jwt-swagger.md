# Java Security, JWT, Swagger 설정 예제

## SecurityConfig

```java
/**
 * Spring Security 설정
 * JWT 기반 인증 및 API 보안 설정
 */
@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtTokenProvider jwtTokenProvider;

    @Value("${cors.allowed-origins:http://localhost:3000,http://localhost:8080,http://localhost:8081,http://localhost:8082,http://localhost:8083,http://localhost:8084}")
    private String allowedOrigins;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
                .csrf(AbstractHttpConfigurer::disable)
                .cors(cors -> cors.configurationSource(corsConfigurationSource()))
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(auth -> auth
                        // Actuator endpoints
                        .requestMatchers("/actuator/**").permitAll()
                        // Swagger UI endpoints - context path와 상관없이 접근 가능하도록 설정
                        .requestMatchers("/swagger-ui/**", "/swagger-ui.html", "/v3/api-docs/**", "/swagger-resources/**", "/webjars/**").permitAll()
                        // Health check
                        .requestMatchers("/health").permitAll()
                        // All other requests require authentication
                        .anyRequest().authenticated()
                )
                .addFilterBefore(new JwtAuthenticationFilter(jwtTokenProvider),
                                UsernamePasswordAuthenticationFilter.class)
                .build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();

        // 환경변수에서 허용할 Origin 패턴 설정
        String[] origins = allowedOrigins.split(",");
        configuration.setAllowedOriginPatterns(Arrays.asList(origins));

        // 허용할 HTTP 메소드
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"));

        // 허용할 헤더
        configuration.setAllowedHeaders(Arrays.asList(
            "Authorization", "Content-Type", "X-Requested-With", "Accept",
            "Origin", "Access-Control-Request-Method", "Access-Control-Request-Headers"
        ));

        // 자격 증명 허용
        configuration.setAllowCredentials(true);

        // Pre-flight 요청 캐시 시간
        configuration.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}
```

## JWT 인증처리

### JwtAuthenticationFilter

```java
/**
 * JWT 인증 필터
 * HTTP 요청에서 JWT 토큰을 추출하여 인증을 수행
 */
@Slf4j
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtTokenProvider jwtTokenProvider;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                  HttpServletResponse response,
                                  FilterChain filterChain) throws ServletException, IOException {

        String token = jwtTokenProvider.resolveToken(request);

        if (StringUtils.hasText(token) && jwtTokenProvider.validateToken(token)) {
            String userId = jwtTokenProvider.getUserId(token);
            String username = null;
            String authority = null;

            try {
                username = jwtTokenProvider.getUsername(token);
            } catch (Exception e) {
                log.debug("JWT에 username 클레임이 없음: {}", e.getMessage());
            }

            try {
                authority = jwtTokenProvider.getAuthority(token);
            } catch (Exception e) {
                log.debug("JWT에 authority 클레임이 없음: {}", e.getMessage());
            }

            if (StringUtils.hasText(userId)) {
                // UserPrincipal 객체 생성 (username과 authority가 없어도 동작)
                UserPrincipal userPrincipal = UserPrincipal.builder()
                    .userId(userId)
                    .username(username != null ? username : "unknown")
                    .authority(authority != null ? authority : "USER")
                    .build();

                UsernamePasswordAuthenticationToken authentication =
                    new UsernamePasswordAuthenticationToken(
                        userPrincipal,
                        null,
                        Collections.singletonList(new SimpleGrantedAuthority(authority != null ? authority : "USER"))
                    );

                authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(authentication);

                log.debug("인증된 사용자: {} ({})", userPrincipal.getUsername(), userId);
            }
        }

        filterChain.doFilter(request, response);
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        return path.startsWith("/actuator") ||
               path.startsWith("/swagger-ui") ||
               path.startsWith("/v3/api-docs") ||
               path.equals("/health");
    }
}
```

### JwtTokenProvider

```java
/**
 * JWT 토큰 제공자
 * JWT 토큰의 생성, 검증, 파싱을 담당
 */
@Slf4j
@Component
public class JwtTokenProvider {

    private final SecretKey secretKey;
    private final long tokenValidityInMilliseconds;

    public JwtTokenProvider(@Value("${jwt.secret}") String secret,
                           @Value("${jwt.access-token-validity:3600}") long tokenValidityInSeconds) {
        this.secretKey = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.tokenValidityInMilliseconds = tokenValidityInSeconds * 1000;
    }

    /**
     * HTTP 요청에서 JWT 토큰 추출
     */
    public String resolveToken(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }

    /**
     * JWT 토큰 유효성 검증
     */
    public boolean validateToken(String token) {
        try {
            Jwts.parser()
                .setSigningKey(secretKey)
                .build()
                .parseClaimsJws(token);
            return true;
        } catch (SecurityException | MalformedJwtException e) {
            log.debug("Invalid JWT signature: {}", e.getMessage());
        } catch (ExpiredJwtException e) {
            log.debug("Expired JWT token: {}", e.getMessage());
        } catch (UnsupportedJwtException e) {
            log.debug("Unsupported JWT token: {}", e.getMessage());
        } catch (IllegalArgumentException e) {
            log.debug("JWT token compact of handler are invalid: {}", e.getMessage());
        }
        return false;
    }

    /**
     * JWT 토큰에서 사용자 ID 추출
     */
    public String getUserId(String token) {
        Claims claims = Jwts.parser()
            .setSigningKey(secretKey)
            .build()
            .parseClaimsJws(token)
            .getBody();

        return claims.getSubject();
    }

    /**
     * JWT 토큰에서 사용자명 추출
     */
    public String getUsername(String token) {
        Claims claims = Jwts.parser()
            .setSigningKey(secretKey)
            .build()
            .parseClaimsJws(token)
            .getBody();

        return claims.get("username", String.class);
    }

    /**
     * JWT 토큰에서 권한 정보 추출
     */
    public String getAuthority(String token) {
        Claims claims = Jwts.parser()
            .setSigningKey(secretKey)
            .build()
            .parseClaimsJws(token)
            .getBody();

        return claims.get("authority", String.class);
    }

    /**
     * 토큰 만료 시간 확인
     */
    public boolean isTokenExpired(String token) {
        try {
            Claims claims = Jwts.parser()
                .setSigningKey(secretKey)
                .build()
                .parseClaimsJws(token)
                .getBody();

            return claims.getExpiration().before(new Date());
        } catch (Exception e) {
            return true;
        }
    }

    /**
     * 토큰에서 만료 시간 추출
     */
    public Date getExpirationDate(String token) {
        Claims claims = Jwts.parser()
            .setSigningKey(secretKey)
            .build()
            .parseClaimsJws(token)
            .getBody();

        return claims.getExpiration();
    }
}
```

### UserPrincipal

```java
/**
 * 인증된 사용자 정보
 * JWT 토큰에서 추출된 사용자 정보를 담는 Principal 객체
 */
@Getter
@Builder
@RequiredArgsConstructor
public class UserPrincipal {

    /**
     * 사용자 고유 ID
     */
    private final String userId;

    /**
     * 사용자명
     */
    private final String username;

    /**
     * 사용자 권한
     */
    private final String authority;

    /**
     * 사용자 ID 반환 (별칭)
     */
    public String getName() {
        return userId;
    }

    /**
     * 관리자 권한 여부 확인
     */
    public boolean isAdmin() {
        return "ADMIN".equals(authority);
    }

    /**
     * 일반 사용자 권한 여부 확인
     */
    public boolean isUser() {
        return "USER".equals(authority) || authority == null;
    }
}
```

## SwaggerConfig (OpenAPI Configuration)

```java
/**
 * Swagger/OpenAPI 설정
 * AI Service API 문서화를 위한 설정
 */
@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI openAPI() {
        return new OpenAPI()
                .info(apiInfo())
                .addServersItem(new Server()
                        .url("http://localhost:8084")
                        .description("Local Development"))
                .addServersItem(new Server()
                        .url("{protocol}://{host}:{port}")
                        .description("Custom Server")
                        .variables(new io.swagger.v3.oas.models.servers.ServerVariables()
                                .addServerVariable("protocol", new io.swagger.v3.oas.models.servers.ServerVariable()
                                        ._default("http")
                                        .description("Protocol (http or https)")
                                        .addEnumItem("http")
                                        .addEnumItem("https"))
                                .addServerVariable("host", new io.swagger.v3.oas.models.servers.ServerVariable()
                                        ._default("localhost")
                                        .description("Server host"))
                                .addServerVariable("port", new io.swagger.v3.oas.models.servers.ServerVariable()
                                        ._default("8084")
                                        .description("Server port"))))
                .addSecurityItem(new SecurityRequirement().addList("Bearer Authentication"))
                .components(new Components()
                        .addSecuritySchemes("Bearer Authentication", createAPIKeyScheme()));
    }

    private Info apiInfo() {
        return new Info()
                .title("AI Service API")
                .description("AI 기반 시간별 상세 일정 생성 및 장소 추천 정보 API")
                .version("1.0.0")
                .contact(new Contact()
                        .name("TripGen Development Team")
                        .email("dev@tripgen.com"));
    }

    private SecurityScheme createAPIKeyScheme() {
        return new SecurityScheme()
                .type(SecurityScheme.Type.HTTP)
                .bearerFormat("JWT")
                .scheme("bearer");
    }
}
```

## 참조
- 이 파일은 `resources/guides/develop/backend-api-dev.md`에서 참조됩니다.
