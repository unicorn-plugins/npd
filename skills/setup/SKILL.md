---
name: setup
description: NPD 플러그인 초기 설정 (MCP 서버 설치, GitHub 토큰 설정)
type: setup
user-invocable: true
allowed-tools: Read, Write, Bash
---

# Setup

[NPD Setup 활성화]

## 목표

NPD 플러그인이 정상 동작하기 위한 환경을 구성함.
`gateway/install.yaml`을 읽어 필요한 MCP 서버와 커스텀 도구를 설치하고,
GitHub 토큰 등 필수 설정을 완료함.

## 활성화 조건

사용자가 `/npd:setup` 호출 시 또는 "NPD 설정", "플러그인 초기화" 키워드 감지 시.

## 워크플로우

### Step 1. 설치 매니페스트 읽기

`gateway/install.yaml`을 읽어 설치 대상 목록 파악.

### Step 2. MCP 서버 설치

`install.yaml`의 `mcp_servers` 항목을 순서대로 처리:

| 서버 | 설치 명령 | 필수 여부 |
|------|----------|----------|
| context7 | `claude mcp add-json context7 '{"command":"npx","args":["-y","@upstash/context7-mcp"]}'` | 선택 |

설치 전 이미 등록되어 있는지 확인 후 중복 설치 방지.

### Step 3. GitHub 토큰 설정

`create_repo` 도구 사용을 위한 GitHub Personal Access Token(PAT)을 환경변수로 등록합니다.

#### 3-1. 기존 토큰 확인

```bash
echo $GITHUB_TOKEN
```

- 값이 출력되면 → ✅ 이미 설정됨, Step 4로 이동
- 비어 있으면 → 3-2로 진행

#### 3-2. PAT 입력 요청

<!--ASK_USER-->
{"title":"GitHub Personal Access Token","questions":[
  {"question":"GitHub PAT를 입력해주세요. (토큰 생성: GitHub → Settings → Developer settings → Personal access tokens → Tokens(classic) → Generate new token, 권한: repo, workflow 체크)","type":"text"}
]}
<!--/ASK_USER-->

#### 3-3. 환경변수 등록

입력받은 PAT를 `GITHUB_TOKEN` 환경변수로 영구 등록합니다.

**Mac:**
```bash
grep -q 'GITHUB_TOKEN' ~/.zshrc || echo 'export GITHUB_TOKEN="{입력받은 PAT}"' >> ~/.zshrc
source ~/.zshrc
```

**Linux / Windows Git Bash:**
```bash
grep -q 'GITHUB_TOKEN' ~/.bashrc || echo 'export GITHUB_TOKEN="{입력받은 PAT}"' >> ~/.bashrc
source ~/.bashrc
```

등록 확인:
```bash
echo $GITHUB_TOKEN
```

- 값이 출력되면 → ✅ 등록 완료
- 비어 있으면 → ⚠️ 등록 실패, 수동 설정 안내

**주의:** 토큰을 파일(`.dmap/secrets/` 등)에 직접 저장하지 않습니다.

### Step 4. 설정 완료 보고

설치 결과를 사용자에게 요약 보고:
```
## NPD 설정 완료

### 설치된 도구
- context7 MCP: ✅ / ⚠️ (선택)

### GitHub 토큰
- GITHUB_TOKEN: ✅ 등록됨  /  ⚠️ 미등록 → PAT 설정 참조

### 다음 단계
`/npd:create` 로 새 프로젝트를 시작하세요.
```

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | `gateway/install.yaml` 을 반드시 읽어 설치 대상을 파악할 것 |
| 2 | 설치 전 기존 설치 여부를 확인하여 중복 설치를 방지할 것 |
| 3 | 설정 완료 후 다음 단계(`/npd:create`) 안내를 포함할 것 |

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | GitHub 토큰을 파일(`.dmap/secrets/` 등)에 직접 저장하지 않을 것 (shell rc 환경변수만 사용) |
| 2 | 필수(required: true) 도구 설치 실패 시 완료 처리하지 않을 것 |

## 검증 체크리스트

- [ ] `gateway/install.yaml` 읽기 성공
- [ ] context7 MCP 설치 또는 이미 설치됨 확인
- [ ] GITHUB_TOKEN 기존 설정 여부가 확인되는가
- [ ] 미설정 시 사용자에게 PAT 입력을 요청하는가
- [ ] 입력받은 PAT가 shell rc 파일에 환경변수로 등록되는가
- [ ] 등록 후 `echo $GITHUB_TOKEN`으로 확인되는가
- [ ] 다음 단계 안내 포함