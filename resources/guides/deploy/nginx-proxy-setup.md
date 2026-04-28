# Nginx Web Server Proxy 설정 가이드

> 본 가이드는 `skills/deploy/SKILL.md > Phase 5 / Step 3`에서 호출됨.
> K8s Ingress 배포 후 외부 HTTPS 접근을 위한 Nginx Proxy 설정 절차를 정의.

## 입력

- `{VM.HOST}` (Phase 1 / Step 5에서 수집, 컨테이너 실행 VM = Web Server VM 동일 전제)
- `{K8S_NAMESPACE}` (Phase 2 / Step 5에서 결정)
- 배포된 K8s Ingress (Phase 5 / Step 2 산출물)
- Web Server VM에 설치된 Nginx + certbot

## 모드 분기

> **이 Step은 배포 스킬(SKILL.md) 레벨에서 실행된다.** 사용자에게 묻는 작업(Step 3-1)은 Agent가 아닌 스킬이 직접 수행한다.

> **자동 진행 모드 동작**: 아래 사용자 확인 단계(Step 3-1)의 `<!--ASK_USER-->`를 생략하고 자동 처리한다.
> - **3-1a Web Server 설치 확인**: `ssh {VM.HOST} 'nginx -v'`로 자동 확인 → 미설치면 에러 중단
> - **3-1b VM 접속 정보**: `{VM.HOST}`를 `{WEB_SERVER_SSH_HOST}`로 재사용 (동일 VM 전제)
> - **3-1c SSL 도메인**: `ssh {WEB_SERVER_SSH_HOST}`로 `/etc/nginx/sites-available/default`의 `server_name` 값을 읽어 자동 사용 → 감지 실패 시 에러 중단

---

## Step 3-1. 사용자 확인 (스킬이 직접 수행, 자동 진행 모드에서는 위 규칙으로 대체)

### 3-1a. Web Server 설치 확인

<!--ASK_USER-->
{"title":"Web Server 설치 확인","questions":[
  {"question":"K8s 관리 VM에 Nginx Web Server가 설치되어 있나요?\n\n미설치 시 참고: https://github.com/unicorn-plugins/npd/blob/main/resources/references/create-k8s.md > Web서버 설치","type":"radio","options":["설치 완료","아직 없음"]}
]}
<!--/ASK_USER-->

**"아직 없음"** 선택 시: 가이드 링크를 안내하고 설치 완료 대기.

### 3-1b. VM 접속 정보

Phase 1 / Step 5에서 수집한 `{VM.HOST}`를 `{WEB_SERVER_SSH_HOST}`로 재사용한다 (컨테이너 실행 VM = Web Server VM 동일 전제).

### 3-1c. SSL 도메인 확인

선택한 VM에 SSH 접속하여 `/etc/nginx/sites-available/default`의 `server_name` 값을 읽은 후 사용자에게 확인:

<!--ASK_USER-->
{"title":"SSL 도메인 확인","questions":[
  {"question":"Web Server의 SSL 도메인을 확인합니다.\n\n감지된 server_name: `{감지된 server_name}`\n\n이 도메인이 맞습니까?","type":"radio","options":["맞음","직접 입력"]}
]}
<!--/ASK_USER-->

**"직접 입력"** 선택 시: 사용자에게 SSL 도메인을 입력받음 (예: `mydomain.com`, `app.example.co.kr`, `{ID}.{VM Public IP}.nip.io` 등). 확인된 값을 `{SSL_DOMAIN}`으로 저장.

---

## Step 3-2. Ingress 주소 + SSL 인증서 (자동 실행, Agent 위임 가능)

### 3-2a. Ingress ADDRESS 확인

`kubectl get ing -n {K8S_NAMESPACE}`로 Ingress ADDRESS 취득.

### 3-2b. API 도메인 SSL 인증서 발급

K8s Ingress는 프론트엔드(`{SSL_DOMAIN}`)와 백엔드 API(`api.{SSL_DOMAIN}`)를 별도 Host로 분리하므로, API 도메인용 SSL 인증서도 필요하다.

```bash
ssh {WEB_SERVER_SSH_HOST} "sudo certbot certonly --nginx -d api.{SSL_DOMAIN} --non-interactive --agree-tos --email noreply@example.com"
```

> 이미 `api.{SSL_DOMAIN}` 인증서가 존재하면 이 단계는 건너뛴다.

---

## Step 3-3. Nginx 구성

### 3-3a. Nginx conf 생성 (Frontend + API 두 server 블록)

Web Server VM(`{WEB_SERVER_SSH_HOST}`)에서 Nginx conf를 **프론트엔드 + API 두 개 server 블록**으로 재생성한다.

```bash
ssh {WEB_SERVER_SSH_HOST} 'SERVER_NAME="{SSL_DOMAIN}"
API_SERVER_NAME="api.{SSL_DOMAIN}"
PROXY_TARGET="http://{INGRESS_ADDRESS}"

cat << EOF | sudo tee /etc/nginx/sites-available/default
# 80 → 443 리다이렉트 (Frontend)
server {
  listen 80;
  server_name ${SERVER_NAME};
  return 301 https://\$host\$request_uri;
}
# 80 → 443 리다이렉트 (API)
server {
  listen 80;
  server_name ${API_SERVER_NAME};
  return 301 https://\$host\$request_uri;
}
# 443 Frontend Proxy
server {
  listen 443 ssl;
  server_name ${SERVER_NAME};
  ssl_certificate /etc/letsencrypt/live/${SERVER_NAME}/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/${SERVER_NAME}/privkey.pem;
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers HIGH:!aNULL:!MD5;
  root /var/www/html;
  index index.html;
  location / {
    proxy_pass ${PROXY_TARGET};
    proxy_ssl_verify off;
    proxy_buffer_size 64k;
    proxy_buffers 4 64k;
    proxy_busy_buffers_size 64k;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_read_timeout 60s;
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
  }
}
# 443 API Proxy
server {
  listen 443 ssl;
  server_name ${API_SERVER_NAME};
  ssl_certificate /etc/letsencrypt/live/${API_SERVER_NAME}/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/${API_SERVER_NAME}/privkey.pem;
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers HIGH:!aNULL:!MD5;
  location / {
    proxy_pass ${PROXY_TARGET};
    proxy_ssl_verify off;
    proxy_buffer_size 64k;
    proxy_buffers 4 64k;
    proxy_busy_buffers_size 64k;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_read_timeout 60s;
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
  }
}
EOF'
```

> 두 server 블록 모두 동일한 Ingress ADDRESS로 `proxy_pass`하되, `Host` 헤더를 `$host`로 전달하여 Ingress Controller가 Host 기반 라우팅을 수행한다.

### 3-3b. Nginx 재시작 + 동작 검증

```bash
sudo nginx -t && sudo systemctl reload nginx
```

### 3-3c. CORS 확인

공통 ConfigMap의 `CORS_ALLOWED_ORIGINS`에 `https://{SSL_DOMAIN}` 포함 여부 확인.

---

## 산출물

- Web Server VM의 `/etc/nginx/sites-available/default` 갱신 (Frontend + API 두 server 블록 + 80→443 리다이렉트)
- `api.{SSL_DOMAIN}` 도메인의 SSL 인증서 (`/etc/letsencrypt/live/api.{SSL_DOMAIN}/`)
- 외부 HTTPS 접근 가능 (`https://{SSL_DOMAIN}`, `https://api.{SSL_DOMAIN}`)
