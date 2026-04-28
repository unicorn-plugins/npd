---
name: prepare
description: Claude Code 사용을 위한 로컬 개발 환경 사전준비 (기본 프로그램 설치 안내, Claude Code + OMC 설치, Claude Code 설정)
type: setup
user-invocable: true
---

# Prepare

## 목표

Claude Code와 NPD 플러그인 사용을 위한 로컬 개발 환경을 구성함.
자동화 가능한 항목은 직접 실행하고, 수동 설치가 필요한 항목은 가이드 링크를 안내함.

## 활성화 조건

사용자가 `/npd:prepare` 호출 시 또는 "사전준비", "환경 구성", "개발환경 설정" 키워드 감지 시.

## 작업 환경 변수 로드
AGENTS.md 파일에서 `## 환경변수` 섹션의 환경변수 로딩.
로딩 실패 시 사용자에게 `/npd:create`을 먼저 수행하라고 안내하고 종료.

## 진행상황 업데이트 및 재개
`{PROJECT_DIR}/AGENTS.md`에 각 Phase 완료 시 저장. 최종 완료 시 `Done`으로 표기.

```md
## 워크플로우 진행상황
- {skill-name}: Phase3
```

진행상황 정보가 있는 경우 마지막 완료 단계 이후부터 자동 재개.

## 워크플로우

### Phase 0. 체크 범위 선택
#### Step1: 설치 범위 안내  
설치 가이드(`{NPD_PLUGIN_DIR}/resources/guides/setup/prepare.md`)의   
'공통 필수 설치', '설계 단계를 위한 추가 설치', '개발/배포 단계를 위한 추가 설치'의 정보를 읽어 사용자에게 설치 프로그램 안내      
```
[공통 필수 설치]
| 프로그램 | 설명 |

[설계 단계를 위한 추가 설치]
| 프로그램 | 설명 |

[개발/배포 단계를 위한 추가 설치]
| 프로그램 | 설명 |
```

#### Step2: 사전준비 체크 범위 선택  
<!--ASK_USER-->
{"title":"사전준비 체크 범위","questions":[
  {"question":"어떤 범위로 사전준비를 체크할까요?","description":"체크 범위에 따라 사전 프로그램 설치 여부를 검사합니다.","type":"radio","options":["공통 필수만 체크", "설계 단계까지 체크", "개발/배포 단계까지 체크", "사전 프로그램 미설치"]}
]}
<!--/ASK_USER-->

- **공통 필수만 체크** 선택 시: Phase 1(OS 감지) → Phase 2 실행 → Phase5 실행
- **설계 단계까지 체크** 선택 시: Phase 1(OS 감지) → Phase 2 실행 → Phase 3 실행 → Phase5 실행
- **개발/배포 단계까지 체크** 선택 시: Phase 1(OS 감지) → Phase 2 실행 → Phase 3 실행 → Phase4 실행 → Phase5 실행
- **사전 프로그램 미설치** 선택 시: 설치 가이드 링크를 안내하고 수행 중단 
설치 가이드: [로컬 개발 환경 구성](https://github.com/unicorn-plugins/npd/blob/main/resources/guides/setup/prepare.md)

### Phase 1. OS 감지

```bash
uname -s
```

결과에 따라 OS를 판별:
- `Linux` → Linux
- `Darwin` → Mac
- `MINGW*` / `MSYS*` / `CYGWIN*` → Windows (Git Bash)

### Phase 2. 공통 필수 설치 체크

#### Step1: Git Client 
설치 여부 확인:
```bash
git -v 2>/dev/null
```
미 설치 시 `{NOT_INSTALLED}` 변수에 'Git Client' 추가  

#### Step2. GitHub CLI 설치

GitHub와의 인터페이스를 지원하는 CLI를 자동으로 설치합니다.

설치 여부 확인:
```bash
gh --version 2>/dev/null
```

- 버전 출력 → ✅ 설치됨
- 오류 발생 → ⚠️ 미설치, OS에 따라 자동 설치:

**Mac:**
```bash
# Homebrew 설치 여부 확인
if ! command -v brew &>/dev/null; then
  echo "⚠️ Homebrew 미설치. 설치를 시작합니다..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Apple Silicon Mac PATH 설정
  if [[ $(uname -m) == "arm64" ]]; then
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi
fi

brew install gh
```

**Windows (Git Bash):**
```bash
# winget PATH 확인 및 등록
WINGET_PATH="$LOCALAPPDATA/Microsoft/WindowsApps"

if ! echo "$PATH" | tr ':' '\n' | grep -qx "$WINGET_PATH"; then
  echo "" >> ~/.bashrc
  echo "# winget PATH" >> ~/.bashrc
  echo "export PATH=\"\$PATH:$WINGET_PATH\"" >> ~/.bashrc
  export PATH="$PATH:$WINGET_PATH"
fi

# GitHub CLI 설치
winget install --id GitHub.cli --accept-source-agreements --accept-package-agreements
```

**Linux:**
```bash
(type -p wget >/dev/null || sudo apt-get install wget -y) \
  && sudo mkdir -p -m 755 /etc/apt/keyrings \
  && out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  && cat $out | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
  && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
  && sudo apt update \
  && sudo apt install gh -y
```

설치 후 인증 상태 확인:
```bash
gh auth status 2>&1
```

- 인증됨 → ✅ 인증 완료
- 미인증 → 사용자에게 `gh auth login` 실행을 안내하고 인증 완료 후 진행

---

#### Step3. Node.js 
설치 여부 확인:
```bash
node -v 2>/dev/null
```
미 설치 시 `{NOT_INSTALLED}` 변수에 'Node.js' 추가 

---

#### Step4. vscode
설치 여부 확인:
```bash
code -v 2>/dev/null
```
미 설치 시 `{NOT_INSTALLED}` 변수에 'vscode' 추가 

---

#### Step5. Claude Code

```bash
claude -v
```

- 버전 출력 → ✅ 설치됨
- 오류 발생 → ⚠️ 미설치, 아래 설치 명령 안내:

**Mac/Linux:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://claude.ai/install.ps1 | iex
```

PATH 설정(Linux/Mac):
```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
export PATH=~/.local/bin:$PATH
```

PATH 설정(Windows Git Bash):
```bash
# ~/.bashrc에 추가
export PATH=~/.npm-global:$PATH
```

터미널에서 Claude Code를 수행하여 최초 셋업을 수행하도록 안내    
```bash
claude
```

편의 명령어(`cc-yolo`, `cc-safe`, `cy`) alias를 자동으로 등록합니다.

**Mac:**
```bash
if ! grep -q 'alias cc-yolo' ~/.zshrc 2>/dev/null; then
  echo '' >> ~/.zshrc
  echo "alias cc-yolo='claude --dangerously-skip-permissions'" >> ~/.zshrc
  echo "alias cc-safe='claude'" >> ~/.zshrc
  echo "alias cy='cc-yolo'" >> ~/.zshrc
  source ~/.zshrc
fi
```

**Linux:**
```bash
if ! grep -q 'alias cc-yolo' ~/.bashrc 2>/dev/null; then
  echo '' >> ~/.bashrc
  echo "alias cc-yolo='claude --dangerously-skip-permissions'" >> ~/.bashrc
  echo "alias cc-safe='claude'" >> ~/.bashrc
  echo "alias cy='cc-yolo'" >> ~/.bashrc
  source ~/.bashrc
fi
```

**Windows (Git Bash):**
```bash
if ! grep -q 'alias cc-yolo' ~/.bashrc 2>/dev/null; then
  echo '' >> ~/.bashrc
  echo "alias cc-yolo='claude --dangerously-skip-permissions'" >> ~/.bashrc
  echo "alias cc-safe='claude'" >> ~/.bashrc
  echo "alias cy='cc-yolo'" >> ~/.bashrc
  source ~/.bashrc
fi
```

**Windows (PowerShell):**
```powershell
$profileDir = Split-Path $PROFILE
if (!(Test-Path $profileDir)) { New-Item -ItemType Directory -Path $profileDir -Force }
if (!(Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force }
if (!(Select-String -Path $PROFILE -Pattern 'cc-yolo' -Quiet 2>$null)) {
  Add-Content $PROFILE ""
  Add-Content $PROFILE "function cc-yolo { claude --dangerously-skip-permissions @args }"
  Add-Content $PROFILE "function cc-safe { claude @args }"
  Add-Content $PROFILE "function cy { cc-yolo @args }"
}
```

사용자에게 편의 명령어 사용 방법 안내:
```
아래와 같이 편의 명령이 등록되었습니다. 
위험 모드로 수행하면 사용자의 승인 없이 파일 수정/삭제가 가능하니 주의해서 사용하세요.
실용적으로 위험모드로 수행하는 것이 사용자 승인 없이 작업하여 편리합니다.    
- 위험 모드로 수행: cy
- 안전 모드로 수행: cc-safe  
```

---

#### Step6. OMC(Oh My Claude Code)

`~/.claude/plugins/installed_plugins.json` 파일을 읽어 `oh-my-claudecode` 포함 여부 확인.

- 포함됨 → ✅ 설치됨
- 미포함 → ⚠️ 미설치, 아래 순서로 설치 안내:

Claude Code 프롬프트에서 순차 실행
```
claude plugin marketplace add https://github.com/Yeachan-Heo/oh-my-claudecode
claude plugin install oh-my-claudecode
```

OMC 초기 설정:     
Claude Code 프롬프트창에서 아래 명령 실행 하도록 안내. 단 MCP 설치는 Skip하도록 안내    
```
/omc-setup
```

---

#### Step7. MCP

`sequential-thinking`, `context7`, `playwright` MCP를 `~/.claude.json`에 자동으로 등록합니다.
`claude mcp list` 명령으로 확인하여 미설치 시에만 설치합니다.  

OS를 감지하여 아래 CLI명령 실행합니다:
Windows:   
```
claude mcp add-json context7 '{"command":"cmd","args":["/c","npx","-y","@upstash/context7-mcp@latest"]}' --scope user
claude mcp add-json sequential-thinking '{"command":"cmd","args":["/c","npx","-y","@modelcontextprotocol/server-sequential-thinking"]}' --scope user
claude mcp add-json pw '{"command":"cmd","args":["/c","npx","@playwright/mcp@latest","--allow-unrestricted-file-access"]}' --scope user
```

Mac/Linux:   
```
claude mcp add-json context7 '{"command":"npx","args":["-y","@upstash/context7-mcp@latest"]}' --scope user
claude mcp add-json sequential-thinking '{"command":"npx","args":["-y","@modelcontextprotocol/server-sequential-thinking"]}' --scope user
claude mcp add-json pw '{"command":"npx","args":["-y","@playwright/mcp@latest","--allow-unrestricted-file-access"]}' --scope user
```

설치 확인:
```bash
claude mcp list
```

---

#### Step8. Python
설치 여부 확인:
```bash
python --version 2>/dev/null
```
미 설치 시 `{NOT_INSTALLED}` 변수에 'Python' 추가 

---


#### Step9. bun

bun 설치 여부 확인:
```bash
bun --version 2>/dev/null
```

미설치 시 자동 설치:
```bash
curl -fsSL https://bun.sh/install | bash
```

PATH 설정 (중복 방지):
- **Mac:**
  ```bash
  grep -q 'bun/bin' ~/.zshrc || echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.zshrc
  source ~/.zshrc
  ```
- **Linux / Windows GitBash:**
  ```bash
  grep -q 'bun/bin' ~/.bashrc || echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.bashrc
  source ~/.bashrc
  ```

---

### Phase 3. 설계 단계 설치 체크
#### Step1. Docker
설치 여부 확인:
```bash
docker -v 2>/dev/null
```
미 설치 시 `{NOT_INSTALLED}` 변수에 'Docker' 추가 

---

### Phase 4. 개발/배포 단계 설치 체크
#### Step1. IntelliJ
IntelliJ 설치 여부 확인: 
미 설치 시 `{NOT_INSTALLED}` 변수에 'IntelliJ' 추가 

---

### Phase 5. 사전준비 결과 보고

```
## 사전준비 결과

### 사전 설치 프로그램
- 체크 범위: {'공통 필수 설치', '설계 단계를 위한 추가 설치', '개발/배포 단계를 위한 추가 설치'}
- 사전 설치 확인: 
  아래 표 형식으로 설치 결과 표시.  
  ```
  | 프로그램 | 설치 여부 | 자동 설치 | 
  ```
- 미설치: `{NOT_INSTALLED}` 변수에 있는 리스트 표시  
  아래 표 형식으로 설치 결과 표시.  
  ```
  | 프로그램 | 설명 | 
  ```

### 다음 단계
모든 설치가 완료되면 `/npd:plan`으로 기획을 시작하세요.  
```

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | 스킬 시작 시 반드시 설치 체크 범위 중 하나를 선택하게 할 것 |
| 2 | OS를 먼저 감지하여 OS별 설치 명령을 분기할 것 |
| 3 | PATH 추가 시 중복 여부를 확인(`grep -q`)하여 중복 추가하지 않을 것 |
| 4 | bun 설치 후 OS에 맞는 shell rc 파일에 PATH를 추가하고 source를 수행할 것 |
| 5 | 편의 명령어(cc-yolo, cc-safe, cy) alias는 중복 여부를 확인 후 등록하고 source를 수행할 것 |
| 6 | Windows에서 편의 명령어는 Git Bash(`~/.bashrc`)와 PowerShell(`$PROFILE`) 양쪽에 등록할 것 |
| 7 | MCP 등록 시 기존 `mcpServers` 항목을 유지하고 미등록 서버만 추가할 것 |
| 8 | GitHub CLI(gh) 설치 여부를 확인하고 미설치 시 OS에 맞는 명령으로 자동 설치할 것 |
| 9 | GitHub CLI 설치 후 인증 상태를 확인하고 미인증 시 `gh auth login` 안내할 것 |
| 10 | 결과 보고 후 반드시 다음 단계(`/npd:setup`) 안내를 포함할 것 |
| 11 | `<!--ASK_USER-->` 발견 시 AskUserQuestion 도구를 호출할 것 (텍스트 출력 금지) |

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | 사전 설치 프로그램(Git, Node.js, Python 등)을 스킬에서 직접 자동 설치하지 않을 것 (가이드 안내만 할 것) |
| 2 | 사전 설치 프로그램 미설치 상태에서 이후 단계를 진행하지 않을 것 |
| 3 | PATH 설정을 중복으로 추가하지 않을 것 |
| 4 | 이미 등록된 MCP 서버를 덮어쓰지 않을 것 |
| 5 | 이미 등록된 alias를 중복 추가하지 않을 것 |

