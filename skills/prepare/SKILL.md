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
  {"question":"어떤 범위로 사전준비를 수행할까요?","description":"기획만 수행: Claude Code, OMC, 편의 명령어, MCP 서버만 설치·설정합니다.\n모든 단계 수행: Git, Python, Node.js, JDK, Docker, kubectl, helm, kubens 등 기본 프로그램부터 전체 설치·설정합니다.","type":"radio","options":["기획만 수행","모든 단계 수행"]}
]}
<!--/ASK_USER-->

- **기획만 수행** 선택 시 → Step 1(OS 감지) 후 Step 3~8만 실행
- **모든 단계 수행** 선택 시 → Step 1~8 전체 실행

### Step 1. OS 감지

```bash
uname -s
```

결과에 따라 OS를 판별:
- `Linux` → Linux
- `Darwin` → Mac
- `MINGW*` / `MSYS*` / `CYGWIN*` → Windows (Git Bash)

### Step 2. 기본 프로그램 자동 설치

각 항목을 순서대로 확인하고, 미설치 시 OS에 맞는 명령으로 자동 설치함.
설치 전 반드시 사용자에게 "설치를 진행하겠습니다" 안내 후 실행.

#### 2-0. Homebrew 설치 (Mac 전용)

**설치 확인:**
```bash
brew --version 2>/dev/null
```

미설치 시 자동 설치:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

설치 후 PATH 설정 (Apple Silicon Mac인 경우):
```bash
if [[ $(uname -m) == "arm64" ]]; then
  grep -q '/opt/homebrew/bin/brew' ~/.zshrc || echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi
```

설치 후 PATH 설정 (Intel Mac인 경우):
```bash
if [[ $(uname -m) == "x86_64" ]]; then
  grep -q '/usr/local/bin/brew' ~/.zshrc || echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zshrc
  eval "$(/usr/local/bin/brew shellenv)"
fi
```

#### 2-1. 작업 디렉토리 생성

```bash
mkdir -p ~/workspace
```

#### 2-2. Git 설치 및 설정

**설치 확인:**
```bash
git --version
```

미설치 시 자동 설치:
- **Mac:** `brew install git`
- **Linux(Ubuntu):** `sudo apt-get update && sudo apt-get install -y git`
- **Windows:**
  1. 사용자에게 아래 메시지 출력:
     ```
     Git이 설치되지 않았습니다.
     아래 링크에서 Git for Windows를 다운로드하여 설치해주세요.

     다운로드: https://git-scm.com/downloads

     ⚠️ 중요: 설치 시 "Git Bash" 옵션을 반드시 체크하세요.
     Git Bash는 이후 단계(kubectl, helm, bun 등)에서 필수로 사용됩니다.

     설치가 완료되면 Git Bash를 열고 이 스킬을 다시 실행해주세요.
     ```
  2. 설치 완료 대기: 30초마다 `git --version` 재확인
  3. 최대 10회(5분) 재확인 후에도 미설치 시 스킬 중단하고 안내 메시지 출력
  4. Git 설치 확인되면 다음 단계 진행

**Git 기본 설정** (설치 후 또는 이미 설치된 경우, user.name/email 미설정 시):
```bash
git config --global user.name 을 확인하여 비어 있으면 사용자에게 이름과 이메일 입력 요청 후 설정:
git config --global user.name "{입력받은 이름}"
git config --global user.email "{입력받은 이메일}"
git config --global init.defaultBranch main
git config credential.helper store --global
```

#### 2-3. Python 설치

**설치 확인:**
```bash
python --version 2>/dev/null || python3 --version 2>/dev/null
```

미설치 시 자동 설치:
- **Mac:** `brew install python3`
  - 설치 후 `.zshrc`에 alias 추가: `echo 'alias python=python3' >> ~/.zshrc`
  - 적용: `source ~/.zshrc`
- **Linux(Ubuntu):** `sudo apt-get update && sudo apt-get install -y python3 python3-pip`
  - 설치 후 `.bashrc`에 alias 추가: `echo 'alias python=python3' >> ~/.bashrc`
  - 적용: `source ~/.bashrc`
- **Windows:**
  1. 사용자에게 아래 메시지 출력:
     ```
     Python이 설치되지 않았습니다.
     아래 링크에서 Python을 다운로드하여 설치해주세요.

     다운로드: https://www.python.org/downloads/

     ⚠️ 중요: 설치 시 "Add Python to PATH" 옵션을 반드시 체크하세요.

     설치가 완료되면 새 터미널(Git Bash)을 열고 이 스킬을 다시 실행해주세요.
     ```
  2. 설치 완료 대기: 30초마다 `python --version` 재확인
  3. 최대 10회(5분) 재확인 후에도 미설치 시 스킬 중단하고 안내 메시지 출력
  4. Python 설치 확인되면 다음 단계 진행

#### 2-4. Node.js 설치 및 npm-global 경로 설정

**설치 확인:**
```bash
node --version
```

미설치 시 자동 설치:
- **Mac:** `brew install node`
- **Linux(Ubuntu):**
  ```bash
  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
  sudo apt-get install -y nodejs
  ```
- **Windows:**
  1. 사용자에게 아래 메시지 출력:
     ```
     Node.js가 설치되지 않았습니다.
     아래 링크에서 Node.js LTS 버전을 다운로드하여 설치해주세요.

     다운로드: https://nodejs.org/en/

     ⚠️ 중요: 설치 시 모든 기본 옵션을 그대로 사용하세요.

     설치가 완료되면 새 터미널(Git Bash)을 열고 이 스킬을 다시 실행해주세요.
     ```
  2. 설치 완료 대기: 30초마다 `node --version` 재확인
  3. 최대 10회(5분) 재확인 후에도 미설치 시 스킬 중단하고 안내 메시지 출력
  4. Node.js 설치 확인되면 다음 단계 진행

**npm-global 경로 설정** (OS 공통, 설치 후 수행):
```bash
mkdir -p ~/.npm-global
npm config set prefix "~/.npm-global"
npm config set cache "~/.npm-global"
```

PATH 추가 (미설정 시):
- **Mac:** `grep -q 'npm-global' ~/.zshrc || echo 'export PATH=~/.npm-global:$PATH' >> ~/.zshrc`
- **Linux/Windows Git Bash:** `grep -q 'npm-global' ~/.bashrc || echo 'export PATH=~/.npm-global:$PATH' >> ~/.bashrc`

#### 2-5. JDK 설치

**설치 확인:**
```bash
java -version 2>&1
```

미설치 시 자동 설치:
- **Mac:** `brew install openjdk@21 && sudo ln -sfn $(brew --prefix)/opt/openjdk@21/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-21.jdk`
- **Linux(Ubuntu):**
  ```bash
  sudo apt-get update && sudo apt-get install -y openjdk-21-jdk
  ```
- **Windows (Git Bash에서 실행):**
  ```bash
  JDK_URL="https://download.java.net/java/GA/jdk21/fd2272bbf8e04c3dbaee13770090416c/35/GPL/openjdk-21_windows-x64_bin.zip"
  JDK_ZIP="$HOME/openjdk-21.zip"
  JDK_DIR="C:/jdk21"

  curl -L -o "$JDK_ZIP" "$JDK_URL"
  mkdir -p "$JDK_DIR"
  unzip -q "$JDK_ZIP" -d "$JDK_DIR"

  # 압축 해제 후 실제 디렉토리명 확인 (jdk-21 등)
  JDK_HOME=$(ls -d "$JDK_DIR"/jdk-* 2>/dev/null | head -1 | sed 's|/|\\|g')

  # PowerShell로 사용자 환경변수 영구 등록
  powershell.exe -Command "
    [System.Environment]::SetEnvironmentVariable('JAVA_HOME', '$JDK_HOME', 'User')
    \$path = [System.Environment]::GetEnvironmentVariable('PATH', 'User')
    if (\$path -notlike '*$JDK_HOME\\bin*') {
      [System.Environment]::SetEnvironmentVariable('PATH', \$path + ';$JDK_HOME\bin', 'User')
    }
  "
  rm -f "$JDK_ZIP"
  echo "JDK 21 설치 완료: $JDK_HOME"
  ```
  설치 후 새 터미널을 열어 `java -version`으로 확인합니다.

#### 2-6. Docker 설치

**설치 확인:**
```bash
docker --version 2>/dev/null
```

미설치 시 자동 설치:
- **Mac:** `brew install --cask docker && open -a docker`
- **Linux(Ubuntu):**
  ```bash
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl gnupg lsb-release
  sudo mkdir -p /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo usermod -aG docker $USER
  newgrp docker
  ```
- **Windows:**
  1. 사용자에게 아래 메시지 출력:
     ```
     Docker가 설치되지 않았습니다.
     아래 링크에서 Docker Desktop for Windows를 다운로드하여 설치해주세요.

     다운로드: https://docs.docker.com/desktop/install/windows-install/

     ⚠️ 중요:
     - WSL 2 백엔드를 사용하도록 설정하세요.
     - 설치 후 시스템 재시작이 필요할 수 있습니다.

     설치가 완료되고 Docker Desktop이 실행되면 이 스킬을 다시 실행해주세요.
     ```
  2. 설치 완료 대기: 30초마다 `docker --version` 재확인
  3. 최대 10회(5분) 재확인 후에도 미설치 시 스킬 중단하고 안내 메시지 출력
  4. Docker 설치 확인되면 다음 단계 진행

#### 2-7. kubectl 설치

**설치 확인:**
```bash
kubectl version --client 2>/dev/null
```

미설치 시 자동 설치:
- **Mac:** `brew install kubectl`
- **Linux(Ubuntu):** `sudo snap install kubectl --classic`
- **Windows (Git Bash):**
  ```bash
  curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/windows/amd64/kubectl.exe"
  mkdir -p ~/.local/bin
  mv kubectl.exe ~/.local/bin/
  chmod +x ~/.local/bin/kubectl.exe
  grep -q '.local/bin' ~/.bashrc || echo 'export PATH=~/.local/bin:$PATH' >> ~/.bashrc
  ```

kubectl alias 설정 (모든 OS):
- **Mac:** `grep -q 'alias k=kubectl' ~/.zshrc || echo 'alias k=kubectl' >> ~/.zshrc`
- **Linux/Windows:** `grep -q 'alias k=kubectl' ~/.bashrc || echo 'alias k=kubectl' >> ~/.bashrc`

#### 2-8. helm 설치

**설치 확인:**
```bash
helm version 2>/dev/null
```

미설치 시 자동 설치:
- **Mac:** `brew install helm`
- **Linux(Ubuntu):**
  ```bash
  mkdir -p ~/install/helm && cd ~/install/helm
  wget https://get.helm.sh/helm-v3.16.4-linux-amd64.tar.gz
  tar xvf helm-v3.16.4-linux-amd64.tar.gz
  sudo cp linux-amd64/helm /usr/local/bin
  ```
- **Windows (Git Bash):**
  ```bash
  mkdir -p ~/.local/bin
  curl -LO https://get.helm.sh/helm-v3.12.0-windows-amd64.zip
  unzip helm-v3.12.0-windows-amd64.zip
  mv windows-amd64/helm.exe ~/.local/bin/
  ```

#### 2-9. kubens/kubectx 설치

**설치 확인:**
```bash
kubens --help 2>/dev/null
```

미설치 시 자동 설치 (Mac/Linux/Windows 공통):
```bash
git clone https://github.com/ahmetb/kubectx.git ~/.kubectx
```

PATH 추가:
- **Mac:** `grep -q 'kubectx' ~/.zshrc || echo 'export PATH=$PATH:~/.kubectx' >> ~/.zshrc`
- **Linux/Windows:** `grep -q 'kubectx' ~/.bashrc || echo 'export PATH=$PATH:~/.kubectx' >> ~/.bashrc`

Mac/Linux의 경우 심볼릭 링크 추가:
```bash
sudo ln -sf ~/.kubectx/kubectx /usr/local/bin/kubectx
sudo ln -sf ~/.kubectx/kubens /usr/local/bin/kubens
```

#### 2-10. PATH 설정 적용

모든 설치 완료 후 설정 파일 재적용:
- **Mac:** `source ~/.zshrc`
- **Linux/Windows Git Bash:** `source ~/.bashrc`

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

### 기본 프로그램
- Homebrew (Mac만): ✅ 4.x.x  /  ⚠️ 미설치 → 설치 명령 참조
- Python:  ✅ 3.x.x  /  ⚠️ 미설치 → [설치 가이드](링크)
- Git:     ✅ 2.x.x  /  ⚠️ 미설치 → [설치 가이드](링크)
- Node.js: ✅ v20.x  /  ⚠️ 미설치 → [설치 가이드](링크)
- JDK:     ✅ 21.x   /  ⚠️ 미설치 → [설치 가이드](링크)
- Docker:  ✅ 24.x   /  ⚠️ 미설치 → [설치 가이드](링크)
- kubectl: ✅ v1.x   /  ⚠️ 미설치 → [설치 가이드](링크)
- bun:     ✅ 1.x.x  /  ⚠️ 미설치 → 설치 명령 참조

### Claude Code
- Claude Code: ✅ 1.x.x  /  ⚠️ 미설치 → 설치 명령 참조

### OMC (Oh My ClaudeCode)
- oh-my-claudecode: ✅ 설치됨  /  ⚠️ 미설치 → 설치 명령 참조

### 편의 명령어
- cc-yolo / cc-safe / cy: ✅ 등록됨  /  ⚠️ 미등록 → alias 설정 참조

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
| 2 | '기획만 수행' 선택 시 Step 3(Claude Code) ~ Step 8(결과보고)만 실행할 것 |
| 3 | '모든 단계 수행' 선택 시 Step 1 ~ Step 8 전체를 실행할 것 |
| 4 | OS를 먼저 감지하여 OS별 설치 명령을 분기할 것 |
| 5 | Mac 사용자는 Homebrew를 제일 먼저 확인하고 미설치 시 설치할 것 |
| 6 | 각 항목 설치 여부를 실제 명령 실행으로 확인한 후 미설치 시에만 설치 진행할 것 |
| 7 | 설치 전 반드시 사용자에게 "설치를 진행하겠습니다" 안내 후 실행할 것 |
| 8 | Git user.name/email 미설정 시 사용자에게 값을 입력받아 설정할 것 |
| 9 | PATH 추가 시 중복 여부를 확인(`grep -q`)하여 중복 추가하지 않을 것 |
| 10 | Windows에서 수동 설치가 필요한 항목(Git, Python, Node.js, Docker)은 설치 링크를 안내하고 30초마다 설치 완료를 확인하며 최대 5분(10회) 대기할 것 |
| 11 | Windows 설치 대기 중 5분 초과 시 스킬을 중단하고 사용자에게 재실행 안내를 출력할 것 |
| 12 | bun 설치 후 OS에 맞는 shell rc 파일에 PATH를 추가하고 source를 수행할 것 |
| 13 | 편의 명령어(cc-yolo, cc-safe, cy) alias는 중복 여부를 확인 후 등록하고 source를 수행할 것 |
| 14 | Windows에서 편의 명령어는 Git Bash(`~/.bashrc`)와 PowerShell(`$PROFILE`) 양쪽에 등록할 것 |
| 15 | MCP 등록 시 기존 `mcpServers` 항목을 유지하고 미등록 서버만 추가할 것 |
| 16 | 결과 보고 후 반드시 다음 단계(`/npd:setup`) 안내를 포함할 것 |

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | 이미 설치된 항목을 다시 설치하지 않을 것 |
| 2 | Claude Code 설치 명령을 사용자 확인 없이 실행하지 않을 것 |
| 3 | PATH 설정을 중복으로 추가하지 않을 것 |
| 4 | 이미 등록된 MCP 서버를 덮어쓰지 않을 것 |
| 5 | 이미 등록된 alias를 중복 추가하지 않을 것 |

## 검증 체크리스트

- [ ] 스킬 시작 시 '기획만 수행' / '모든 단계 수행' 선택지가 제공되는가
- [ ] '기획만 수행' 선택 시 Step 3~8만 실행되는가 (기본 프로그램 설치 생략)
- [ ] '모든 단계 수행' 선택 시 Step 1~8 전체가 실행되는가
- [ ] OS 감지 후 OS별 설치 명령이 분기되는가
- [ ] Mac 사용자는 Homebrew가 제일 먼저 확인되고 미설치 시 설치되는가
- [ ] Homebrew 설치 후 Apple Silicon/Intel 아키텍처에 맞게 PATH가 설정되는가
- [ ] 각 프로그램 설치 여부가 실제 명령 실행으로 확인되는가
- [ ] 미설치 항목만 선별적으로 설치되는가
- [ ] Windows에서 Git 설치 안내 시 "Git Bash 포함" 체크를 강조하는가
- [ ] Windows에서 수동 설치가 필요한 항목(Git, Python, Node.js, Docker)에 대해 설치 완료 대기 로직이 작동하는가
- [ ] Windows 설치 대기 시 30초마다 재확인하며 최대 10회(5분) 대기하는가
- [ ] 5분 초과 시 스킺이 중단되고 재실행 안내 메시지가 출력되는가
- [ ] Git user.name/email 설정이 완료되는가
- [ ] npm-global PATH가 중복 없이 추가되는가
- [ ] bun 설치 여부가 확인되고 PATH가 설정되는가
- [ ] Claude Code 설치 여부가 확인되는가
- [ ] OMC 설치 여부가 확인되는가
- [ ] 편의 명령어(cc-yolo, cc-safe, cy)가 중복 없이 등록되는가
- [ ] Windows에서 편의 명령어가 Git Bash와 PowerShell 양쪽에 등록되는가
- [ ] MCP(sequential-thinking, playwright)가 기존 설정을 유지하며 등록되는가
- [ ] 다음 단계(`/npd:setup`) 안내가 포함되는가
