---
name: prepare
description: Claude Code 사용을 위한 로컬 개발 환경 사전준비 (기본 프로그램 설치 안내, Claude Code + OMC 설치, Claude Code 설정)
type: setup
user-invocable: true
allowed-tools: Read, Bash
---

# Prepare

## 목표

Claude Code와 NPD 플러그인 사용을 위한 로컬 개발 환경을 구성함.
자동화 가능한 항목은 직접 실행하고, 수동 설치가 필요한 항목은 가이드 링크를 안내함.

## 활성화 조건

사용자가 `/npd:prepare` 호출 시 또는 "사전준비", "환경 구성", "개발환경 설정" 키워드 감지 시.

## 워크플로우

### Step 0. 실행 범위 선택

스킬 시작 시 사용자에게 실행 범위를 선택하게 함:

<!--ASK_USER-->
{"title":"사전준비 실행 범위","questions":[
  {"question":"어떤 범위로 사전준비를 수행할까요?","description":"기획만 수행: 기본 설치(Git, Node.js, VS Code 등) 확인 후 Claude Code, OMC, 편의 명령어, MCP 서버를 설치·설정합니다.\n모든 단계 수행: 기본 설치 + 추가 설치(Python, IntelliJ, Docker 등) 확인 후 Claude Code, OMC, 편의 명령어, MCP 서버를 설치·설정합니다.","type":"radio","options":["기획만 수행","모든 단계 수행"]}
]}
<!--/ASK_USER-->

- **기획만 수행** 선택 시 → Step 1(OS 감지) → Step 2(기본 설치 프로그램 확인) → Step 3~8 실행
- **모든 단계 수행** 선택 시 → Step 1(OS 감지) → Step 2(기본+추가 설치 프로그램 확인) → Step 3~8 실행

### Step 1. OS 감지

```bash
uname -s
```

결과에 따라 OS를 판별:
- `Linux` → Linux
- `Darwin` → Mac
- `MINGW*` / `MSYS*` / `CYGWIN*` → Windows (Git Bash)

### Step 2. 사전 설치 프로그램 확인

선택한 범위에 따라 사전에 설치해야 할 프로그램 목록을 안내하고 설치 여부를 확인합니다.
설치 가이드: `resources/guides/setup/prepare.md`

#### 2-1. 범위별 필요 프로그램 안내

**"기획만 수행" 선택 시 — 기본 설치 항목:**

| 프로그램 | 설명 |
|---------|------|
| Git Client | 소스 코드 버전 관리 |
| Window Terminal Git Bash 설정 | Linux 명령어 사용 환경 (Windows만 해당) |
| Node.js | JavaScript 런타임 |
| VS Code | 코드 편집기 |

**"모든 단계 수행" 선택 시 — 기본 설치 + 추가 설치 항목:**

위 기본 설치 항목에 추가로:

| 프로그램 | 설명 |
|---------|------|
| Python | 프로그래밍 언어 |
| IntelliJ | Java IDE |
| Docker Desktop | 컨테이너 실행 환경 |
| GitHub 회원가입 및 토큰 생성 | 소스 코드 저장소 |
| Docker HUB 회원가입 | 컨테이너 이미지 저장소 |
| DBeaver | SQL 클라이언트 (옵션) |

사용자에게 범위에 해당하는 프로그램 목록을 표시하고 아래 설치 가이드 링크를 안내합니다:

📋 설치 가이드: [로컬 개발 환경 구성](https://github.com/unicorn-plugins/npd/blob/main/resources/guides/setup/prepare.md)

위 링크를 우측 마우스 메뉴에서 새탭으로 열어 각 프로그램을 설치해주세요.

#### 2-2. 설치 여부 확인

<!--ASK_USER-->
{"title":"사전 설치 프로그램 확인","questions":[
  {"question":"위 프로그램들을 이미 설치하셨나요?","type":"radio","options":["설치 완료","아직 미설치"]}
]}
<!--/ASK_USER-->

- **설치 완료** 선택 시 → Step 3(Claude Code 설치 확인)으로 진행
- **아직 미설치** 선택 시 → 가이드 링크를 다시 안내하고, 설치 완료 후 `/npd:prepare`를 다시 실행하도록 안내 후 스킬 종료

### Step 3. Claude Code 설치 확인

```bash
claude -v
```

- 버전 출력 → ✅ 설치됨, Step 4로 이동
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

### Step 4. OMC(Oh My ClaudeCode) 설치 확인

`~/.claude/plugins/installed_plugins.json` 파일을 읽어 `oh-my-claudecode` 포함 여부 확인.

- 포함됨 → ✅ 설치됨
- 미포함 → ⚠️ 미설치, 아래 순서로 설치 안내:

Claude Code 프롬프트에서 순차 실행
```
claude plugin marketplace add https://github.com/Yeachan-Heo/oh-my-claudecode
claude plugin install oh-my-claudecode
```

OMC 초기 설정:     
Claude Code 프롬프트창에서 아래 명령 실행 하도록 안내. 단 MCP는 context7만 설치하도록 안내    
```
/oh-my-claudecode:omc-setup
```

### Step 5. Claude Code 설정 안내

편의 명령어(`cc-yolo`, `cc-safe`, `cy`) alias를 자동으로 등록합니다.

**Mac:**
```bash
if ! grep -q 'alias cc-yolo' ~/.zshrc 2>/dev/null; then
  echo '' >> ~/.zshrc
  echo "alias cc-yolo='claude --dangerously-skip-permissions --verbose'" >> ~/.zshrc
  echo "alias cc-safe='claude'" >> ~/.zshrc
  echo "alias cy='cc-yolo'" >> ~/.zshrc
  source ~/.zshrc
fi
```

**Linux:**
```bash
if ! grep -q 'alias cc-yolo' ~/.bashrc 2>/dev/null; then
  echo '' >> ~/.bashrc
  echo "alias cc-yolo='claude --dangerously-skip-permissions --verbose'" >> ~/.bashrc
  echo "alias cc-safe='claude'" >> ~/.bashrc
  echo "alias cy='cc-yolo'" >> ~/.bashrc
  source ~/.bashrc
fi
```

**Windows (Git Bash):**
```bash
if ! grep -q 'alias cc-yolo' ~/.bashrc 2>/dev/null; then
  echo '' >> ~/.bashrc
  echo "alias cc-yolo='claude --dangerously-skip-permissions --verbose'" >> ~/.bashrc
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
  Add-Content $PROFILE "function cc-yolo { claude --dangerously-skip-permissions --verbose @args }"
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

### Step 6. bun 설치

Linux/Mac은 기본 터미널, Windows는 Git Bash에서 수행합니다.
(Windows Terminal 미설치 시: 작업표시줄 돋보기 아이콘 → 'git' 검색 → 'Git Bash' 실행)

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

### Step 7. MCP 설치

`sequential-thinking`과 `playwright` MCP를 `~/.claude.json`에 자동으로 등록합니다.

OS를 감지하여 아래 Python 스크립트를 실행합니다:

```python
import json, os, sys

home = os.path.expanduser('~')
claude_json = os.path.join(home, '.claude.json')

# OS 감지
if sys.platform == 'win32':
    new_servers = {
        "sequential-thinking": {
            "command": "cmd",
            "args": ["/c", "npx", "-y", "@modelcontextprotocol/server-sequential-thinking"]
        },
        "playwright": {
            "command": "cmd",
            "args": ["/c", "npx", "@playwright/mcp@latest"]
        }
    }
else:
    new_servers = {
        "sequential-thinking": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
        },
        "playwright": {
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest"]
        }
    }

# 파일 로드 (없으면 빈 객체)
if os.path.exists(claude_json):
    with open(claude_json, 'r', encoding='utf-8') as f:
        config = json.load(f)
else:
    config = {}

if 'mcpServers' not in config:
    config['mcpServers'] = {}

# 기존 항목 유지, 신규항목만 추가
for name, value in new_servers.items():
    if name not in config['mcpServers']:
        config['mcpServers'][name] = value
        print(f'  ✅ {name} 추가')
    else:
        print(f'  ⏭️ {name} 이미 설정됨')

with open(claude_json, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print('\n~/.claude.json 저장 완료')
```

설치 확인:
```bash
claude mcp list
```

`sequential-thinking`, `playwright` 두 항목이 목록에 표시되면 완료입니다.

### Step 8. 사전준비 결과 보고

```
## 사전준비 결과

### 사전 설치 프로그램
- 실행 범위: {기획만 수행 / 모든 단계 수행}
- 사전 설치: ✅ 설치 완료 확인됨

### Claude Code
- Claude Code: ✅ 1.x.x  /  ⚠️ 미설치 → 설치 명령 참조

### OMC (Oh My ClaudeCode)
- oh-my-claudecode: ✅ 설치됨  /  ⚠️ 미설치 → 설치 명령 참조

### 편의 명령어
- cc-yolo / cc-safe / cy: ✅ 등록됨  /  ⚠️ 미등록 → alias 설정 참조

### bun
- bun: ✅ 1.x.x  /  ⚠️ 미설치 → 설치 명령 참조

### MCP 서버
- sequential-thinking: ✅ 등록됨  /  ⚠️ 미등록 → MCP 설치 참조
- playwright:          ✅ 등록됨  /  ⚠️ 미등록 → MCP 설치 참조

### 다음 단계
모든 설치가 완료되면 `/npd:setup` 으로 NPD 플러그인 환경을 설정하세요.
```

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | 스킬 시작 시 반드시 '기획만 수행' / '모든 단계 수행' 중 하나를 선택하게 할 것 |
| 2 | 범위 선택 후 해당 범위의 사전 설치 프로그램 목록을 표시하고 설치 가이드 링크를 안내할 것 |
| 3 | '기획만 수행' 선택 시 기본 설치 항목(Git, Git Bash, Node.js, VS Code)만 안내할 것 |
| 4 | '모든 단계 수행' 선택 시 기본 설치 + 추가 설치 항목을 모두 안내할 것 |
| 5 | 사전 설치 프로그램 설치 여부를 반드시 사용자에게 확인할 것 |
| 6 | '아직 미설치' 선택 시 가이드 링크를 다시 안내하고 스킬을 종료할 것 |
| 7 | '설치 완료' 선택 시 Step 3(Claude Code)부터 진행할 것 |
| 8 | OS를 먼저 감지하여 OS별 설치 명령을 분기할 것 |
| 9 | PATH 추가 시 중복 여부를 확인(`grep -q`)하여 중복 추가하지 않을 것 |
| 10 | bun 설치 후 OS에 맞는 shell rc 파일에 PATH를 추가하고 source를 수행할 것 |
| 11 | 편의 명령어(cc-yolo, cc-safe, cy) alias는 중복 여부를 확인 후 등록하고 source를 수행할 것 |
| 12 | Windows에서 편의 명령어는 Git Bash(`~/.bashrc`)와 PowerShell(`$PROFILE`) 양쪽에 등록할 것 |
| 13 | MCP 등록 시 기존 `mcpServers` 항목을 유지하고 미등록 서버만 추가할 것 |
| 14 | 결과 보고 후 반드시 다음 단계(`/npd:setup`) 안내를 포함할 것 |

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | 사전 설치 프로그램(Git, Node.js, Python 등)을 스킬에서 직접 자동 설치하지 않을 것 (가이드 안내만 할 것) |
| 2 | 사전 설치 프로그램 미설치 상태에서 이후 단계를 진행하지 않을 것 |
| 3 | Claude Code 설치 명령을 사용자 확인 없이 실행하지 않을 것 |
| 4 | PATH 설정을 중복으로 추가하지 않을 것 |
| 5 | 이미 등록된 MCP 서버를 덮어쓰지 않을 것 |
| 6 | 이미 등록된 alias를 중복 추가하지 않을 것 |

## 검증 체크리스트

- [ ] 스킬 시작 시 '기획만 수행' / '모든 단계 수행' 선택지가 제공되는가
- [ ] 범위에 따른 사전 설치 프로그램 목록이 정확히 표시되는가
- [ ] 설치 가이드 링크(prepare.md)가 안내되는가
- [ ] 사전 설치 프로그램 설치 여부를 사용자에게 확인하는가
- [ ] '아직 미설치' 선택 시 가이드 링크 재안내 후 스킬이 종료되는가
- [ ] '설치 완료' 선택 시 Step 3부터 정상 진행되는가
- [ ] OS 감지 후 OS별 설치 명령이 분기되는가
- [ ] Claude Code 설치 여부가 확인되는가
- [ ] OMC 설치 여부가 확인되는가
- [ ] 편의 명령어(cc-yolo, cc-safe, cy)가 중복 없이 등록되는가
- [ ] Windows에서 편의 명령어가 Git Bash와 PowerShell 양쪽에 등록되는가
- [ ] bun 설치 여부가 확인되고 PATH가 설정되는가
- [ ] MCP(sequential-thinking, playwright)가 기존 설정을 유지하며 등록되는가
- [ ] 다음 단계(`/npd:setup`) 안내가 포함되는가
