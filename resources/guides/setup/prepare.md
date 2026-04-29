# 로컬 개발 환경 구성

- [로컬 개발 환경 구성](#로컬-개발-환경-구성)
- [공통 필수 설치](#공통-필수-설치)
  - [Git Client 설치](#git-client-설치)
    - [설치](#설치)
    - [기존 인증정보 삭제](#기존-인증정보-삭제)
    - [Git 사용법](#git-사용법)
  - [GitHub CLI (gh) 설치](#github-cli-gh-설치)
    - [설치](#설치-1)
    - [인증](#인증)
    - [설치 확인](#설치-확인)
  - [Window Terminal의 Git Bash 설정(Windows Only)](#window-terminal의-git-bash-설정windows-only)
  - [Node.js 설치](#nodejs-설치)
  - [Microsoft Visual Studio Code 설치](#microsoft-visual-studio-code-설치)
    - [설치](#설치-2)
    - [설정](#설정)
  - [Claude Code 설치](#claude-code-설치)
    - [설치](#설치-3)
    - [`~/.local/bin` 추가](#localbin-추가)
    - [설치확인](#설치확인)
    - [참고](#참고)
      - [npm 버전 EOS](#npm-버전-eos)
      - [Claude Desktop에 Claude Code 추가](#claude-desktop에-claude-code-추가)
  - [Oh My ClaudeCode (OMC) 설치](#oh-my-claudecode-omc-설치)
  - [AI툴 설치](#ai툴-설치)
  - [필수 MCP 설치](#필수-mcp-설치)
  - [Claude Code 편의 명령어 설정](#claude-code-편의-명령어-설정)
  - [NPD 플러그인 추가](#npd-플러그인-추가)
    - [작업 디렉토리 생성 및 NPD 플러그인 다운로드](#작업-디렉토리-생성-및-npd-플러그인-다운로드)
    - [플러그인 추가](#플러그인-추가)
    - [플러그인 추가 확인](#플러그인-추가-확인)
  - [Python 설치](#python-설치)
- [설계 단계를 위한 추가 설치](#설계-단계를-위한-추가-설치)
  - [Docker Desktop 설치](#docker-desktop-설치)
  - [GitHub 회원가입 및 토큰 생성](#github-회원가입-및-토큰-생성)
    - [회원가입](#회원가입)
    - [접근 토큰 생성](#접근-토큰-생성)
  - [Docker HUB 회원가입](#docker-hub-회원가입)
- [개발/배포 단계를 위한 추가 설치](#개발배포-단계를-위한-추가-설치)
  - [IntelliJ 설치](#intellij-설치)
    - [설치](#설치-4)
    - [IntelliJ 환경 설정](#intellij-환경-설정)

---

# 공통 필수 설치   
기본적으로 설치해야 하는 공통 필수 설치    

## Git Client 설치
### 설치
`git -v` 명령으로 설치여부 검사하여 미설치 시   
[Git Client 설치하기](https://git-scm.com/downloads)에 접속하여 설치파일을 다운로드 받아 설치합니다.   
  
### 기존 인증정보 삭제  
다른 사람의 PC를 사용한다면 기존 사용자의 Git 인증정보가 있을 수 있습니다.    
처음 Git Client를 설치했거나 본인 PC를 사용하고 있다면 수행할 필요 없습니다.    
```
git credential-cache exit
git credential reject  
```

Window 사용자는 자격증명 관리자에서 삭제하는게 제일 확실합니다.   
```
Windows 자격 증명 관리자에서 Git credential 삭제
1. 자격 증명 관리자 열기
Win + R → control /name Microsoft.CredentialManager
또는 제어판 → 사용자 계정 → 자격 증명 관리자

1. Windows 자격 증명 탭에서 찾기
Git 관련 항목들을 찾아보세요:

git:https://github.com
git:https://gitlab.com
LegacyGeneric:target=git:https://github.com

3. 삭제
해당 항목 클릭 → 제거 버튼
```

### Git 사용법
https://happycloud-lee.tistory.com/93

| [Top](#로컬-개발-환경-구성) |

---

## GitHub CLI (gh) 설치
GitHub CLI는 터미널에서 GitHub 레포지토리 생성, PR, Issue 등을 관리할 수 있는 도구입니다.

### 설치
`gh --version` 명령으로 설치 여부를 확인하여 미설치 시 아래 방법으로 설치합니다.

**Windows: Powershell에서 수행**
```
winget install --id GitHub.cli
```

**Mac**
```
brew install gh
```

**Linux**
```
(type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
  && sudo mkdir -p -m 755 /etc/apt/keyrings \
  && out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  && cat $out | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
  && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
  && sudo apt update \
  && sudo apt install gh -y
```

### 인증
```
gh auth login
```
프롬프트 안내에 따라 GitHub.com > HTTPS > 브라우저 인증을 선택합니다.

### 설치 확인
```
gh --version
gh auth status
```

| [Top](#로컬-개발-환경-구성) |

---

## Window Terminal의 Git Bash 설정(Windows Only)
최근 제품/서비스들은 Linux 위주로 가이드하는 것들이 많습니다.        
Git Bash 터미널에선 Linux의 명령을 사용할 수 있어 매우 유용합니다.        

- Window Terminal 실행
  하단 검색바에서 '터미널'을 입력하고 '터미널'앱을 클릭    
  ![](images/2026-02-20-14-54-58.png)  

- Window Terminal 설정 클릭    
  ![](images/2026-02-20-11-26-28.png)
  
- Git Bash 프로필 추가   
  좌측에서 '새 프로필 추가'를 클릭하고 아래와 같이 입력한 후 저장합니다.   
  ![](images/2026-02-20-11-26-44.png)   
  명령줄의 '찾아보기'를 클릭하여 `C:\Program Files\Git\bin\bash.exe`가 없으면 Git Client를 먼저 설치해야 합니다.   
  
- 기본 프로필 지정    
  좌측에서 '시작' 메뉴 클릭 후, 기본 프로필을 'Git Bash'로 변경합니다.   
  ![](images/2026-02-20-11-26-53.png)

- 확인  
  설정 후 Window Terminal에서 새창열기에 'Git Bash'가 보여야 합니다.  
  ![](images/2026-02-20-11-27-07.png)

  새 창을 열면 기본이 Git Bash로 나오면 됩니다.  


| [Top](#로컬-개발-환경-구성) |

---

## Node.js 설치
Node.js는 서버 프로그램을 만들수 있는 Javascript 기반 언어입니다.  
Node.js Runtime엔진을 설치합니다.   

- Node.js 설치  
  [Node.js 설치하기](https://nodejs.org/en/)페이지로 접속하여  
  설치파일을 다운로드 받아 설치합니다.   

- 테스트 
  ```
  npm -v
  ```

| [Top](#로컬-개발-환경-구성) |

---

## Microsoft Visual Studio Code 설치 
### 설치   
Microsoft Visual Studio Code(vscode라고 많이 부름)는 주로 Javascript, Python과 같은   
Interpreter 언어를 개발할 때 사용하는 IDE(Integrated Development Environment)입니다.  
> **Interpreter 언어**: 통역가라는 직역처럼 별도의 실행파일을 만들지 않고 소스를 바로 실행하는 언어   

다운로드 페이지에 접속하여 설치파일을 다운로드하여 설치: [vscode설치](https://code.visualstudio.com/download) 

### 설정 
- 디렉토리 중첩 표시를 해제 합니다.  
  ![](images/2026-02-20-11-39-06.png)

- Markdown Preview Enhanced 플러그인 설치   
  ![](images/2026-02-20-11-39-20.png)

  맥에서는 cmd-shift-v, Windows에서는 ctrl-shift-v로 마크다운 파일을 미리보기 할 수 있습니다.   

| [Top](#로컬-개발-환경-구성) |

---

## Claude Code 설치  
### 설치
**Linux/Mac**     
```bash
# macOS/Linux
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows**     
PowerShell에서 수행합니다.   
```
irm https://claude.ai/install.ps1 | iex
```

### `~/.local/bin` 추가   
Claude가 설치된 경로를 추가해야 실행할 수 있습니다.  

**1)Window**     
```
code ~/.bashrc
```

아래 추가
```
export PATH=~/.local/bin:$PATH
```

설정 적용
```
source ~/.bashrc
```

PowerShell에서도 동작하도록 경로 추가: PowerShell 터미널을 열고 아래 명령 수행  
```
$localBin = "$env:USERPROFILE\.local\bin"
$currentPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
[System.Environment]::SetEnvironmentVariable("PATH", $currentPath + ";" + $localBin, "User")
Write-Host "완료: $localBin 추가됨. PowerShell 재시작 필요."
```

**2)Mac**     
```
code ~/.zshrc
```

아래 추가
```
export PATH=~/.local/bin:$PATH
```

저장 후 아래 명령으로 적용   
```
source ~/.zshrc
```

### 설치확인   
Claude Pro 이상 구독시에만 수행    
```
claude 
```

### 참고 

#### npm 버전 EOS
2026년 2월부터 Claude Code는 npm을 이용하지 않고 독립적인 런타임 엔진을 사용
기존 설치한 사람은 아래 명령으로 기존 claude를 삭제하고 재설치 바람 
**삭제**   
```
# 강제 언인스톨
npm uninstall -g @anthropic-ai/claude-code --force
# 확인
where claude
만약, 위 명령 결과가 나오면 아래 수행하여 삭제   
rm -rf {위 결과 파일 경로}
# 캐시 정리
npm cache clean --force
```
**설치**
```
claude install 
```

#### Claude Desktop에 Claude Code 추가   
2026년 4월 15일부터 Claude Desktop에 Claude Code가 추가되어 훨씬 편한 UI/UX로 사용할 수 있게 됨  
아래 [Claude CoWork 설치](#ai툴-설치)를 참고하여 Claude CoWork를 설치하면 자동으로 설치됩니다.   
![](images/2026-04-16-13-22-32.png)   

YOLO모드(매번 사용자 확인없이 AI가 자율적으로 수행)를 사용하려면 '설정'에서 아래 권한우회모드를 활성화해야 합니다.     
![](images/2026-04-16-13-35-05.png)  

권한우회 모드를 활성화하고 대화창에서 '권한 건너뛰기'를 선택하면 YOLO모드로 수행됩니다.   
![](images/2026-04-16-13-35-57.png)  


| [Top](#로컬-개발-환경-구성) |

---

## Oh My ClaudeCode (OMC) 설치
OMC는 Claude Code를 더 잘 사용하기 위한 플러그인입니다.    
아래 명령 수행하여 설치     
```
claude plugin marketplace add https://github.com/Yeachan-Heo/oh-my-claudecode
claude plugin install oh-my-claudecode
```

아래 명령으로 셋업 수행. Setup 시 MCP는 Skip 하십시오.    
Claude Code Pro 이상 구독한 경우 Claude Code 실행 후 수행하고,   
Cursor 구독한 경우 Cursor 실행 수 수행하세요.      
```
/omc-setup
```

| [Top](#로컬-개발-환경-구성) |

---

## AI툴 설치  

**1)Claude CoWork 설치**    
Claude CoWork는 Claude Web과 유사한 기능을 로컬에서 사용하기 위한 로컬 Claude툴입니다.  
Claude Code도 CoWork과 동일하게 로컬에 설치하는 Claude 툴입니다.   
차이는 CoWork는 로컬의 가상환경 내에서 수행되고 Code는 로컬에서 직접 수행된다는 것입니다.   
CoWork는 가상환경 내에서 수행되기 때문에 외부 API과 같은 일부 기능이 제약됩니다.   
Claude Pro 구독 시에만 설치합니다.     

![](images/2026-04-13-16-39-25.png)   
   
![](images/2026-04-13-16-43-01.png)
  
**2)Cursor 설치**        
아래 사이트에서 설치 프로그램 다운로드해서 설치하세요.   
https://cursor.com/

| [Top](#로컬-개발-환경-구성) |

**3)Cursor 환경설정**        
- Cursor 가입: 위 Cursor 사이트에서 회원가입 및 Pro 구독   
- 로그인
  ![](images/2026-04-13-22-16-09.png)    
- Auto-Run Mode 활성화: 작업 시 매번 승인 안 물어보게 셋팅
  ![](images/2026-04-13-22-17-18.png)

---


## 필수 MCP 설치   

https://github.com/unicorn-plugins/npd/blob/main/resources/guides/setup/install-mcp.md

---

## Claude Code 편의 명령어 설정    
Claude Code의 CLI인 'claude'의 단축어를 등록합니다.   
이때 '--dangerously-skip-permissions'라는 옵션을 지정한 단축어 'cy'를 등록하면 매우 편합니다.    
이 옵션은 로컬의 파일 변경 등 중요 작업 시 매번 사용자에게 묻지 않게 하는 옵션입니다. 
위험하기 때문에 로컬에서만 사용하셔야 합니다. VM과 같은 곳에 Claude Code 설치하여 사용할 땐 하지 마십시오.     
Linux/Mac사용자는 기본 터미널에서 수행하고, Window사용자는 Window Terminal의 Git Bash에서 수행합니다.   
 
**1.시작 스크립트 파일 열기**      
Linux/Window   
```
code ~/.bashrc
```

Mac   
```
code ~/.zshrc
```

**2.Alias 등록**  
맨 아래에 아래 Alias를 등록합니다.    
```
alias cc-yolo='claude --dangerously-skip-permissions --verbose'
alias cc-safe='claude'
alias cy='cc-yolo'
```

Window 사용자는 Powershell에서도 사용할 수 있도록 아래 작업을 더 합니다.    
Window Terminal에서 Powershell창을 열고 아래를 수행하세요.   

```
code $PROFILE
```

아래와 같이 Alias를 등록합니다.   
```
function cc-yolo { claude --dangerously-skip-permissions --verbose @args }
function cc-safe { claude @args }
function cy { cc-yolo @args }
```

---

**3.사용방법**     
- cc-yolo: YOLO Mode로 Claude Code 실행. Think과정도 표시.   
- cc-safe: Safe Mode로 Claude Code 실행
- cy: cc-yolo와 동일함. 기본값을 바꾸고 싶으면 alias설정을 변경하면 됨      

편의 명령을 설정한 터미널을 모두 닫고 새 터미널을 열어 명령이 동작하는지 확인합니다.

---

## NPD 플러그인 추가
### 작업 디렉토리 생성 및 NPD 플러그인 다운로드 
```
mkdir -p ~/plugins
cd ~/plugins
 
git clone https://github.com/unicorn-plugins/npd.git
cd npd 
```

### 플러그인 추가  
플러그인 추가는 마켓플레이스를 추가한 후 그 마켓플레이스의 플러그인을 install하는 방식으로 설치합니다.    
```
# Marketplace 추가 
cy plugin marketplace add ./

# Plugin 추가
cy plugin install npd@npd
```

### 플러그인 추가 확인
npd 플러그인이 추가되었는지 확인합니다.   
```
claude plugin list
```

Claude Code를 수행하고 설치되었는지 확인합니다.    
Claude Code Pro 이상 구독 시에만 수행   
![](images/2026-02-20-16-14-23.png)   
  
| [Top](#로컬-개발-환경-구성) |
    
---

## Python 설치
최신 버전을 설치하세요.  

**Window: **  
https://www.python.org/downloads/windows/  
![](images/2026-03-26-16-32-02.png)

**Mac:**    
https://www.python.org/downloads/macos/  
![](images/2026-03-26-16-32-56.png) 
  

(중요) 설치 시 'Add python.exe to PATH'를 반드시 체크하고 설치   
![](images/2026-04-13-16-35-19.png)

  
| [Top](#로컬-개발-환경-구성) |

---

# 설계 단계를 위한 추가 설치  

## Docker Desktop 설치
- 설치파일 다운로드: 
  - [Docker Desktop for Window](https://docs.docker.com/desktop/install/windows-install/)로 접근하여 다운로드 
  - [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/)로 접근하여 다운로드    
- 다운로드한 파일을 실행하여 설치: 기본 옵션 그대로 설치   

| [Top](#로컬-개발-환경-구성) |

---

## GitHub 회원가입 및 토큰 생성  
### 회원가입
https://github.com을 여시고 회원 가입을 하십시오.   

### 접근 토큰 생성
Git Repository에 소스를 업로드할 때 사용할 토큰을 생성 하십시오. 
토큰은 잊어 버리지 않게 잘 보관해 놓으십시오.   

우측 상단의 프로파일 이미지를 클릭하고 'Settings'선택
![](images/alt%20text.png)

좌측 메뉴에서 맨 아래에 있는 Developer settings 선택
![alt text](images/image.png)

좌측 메뉴에서 'Personal access tokens'를 펼치고 Tokens(classic) 선택
오른쪽에서 'Generate new token' 클릭하고 두번째 것 선택
![](images/2026-02-20-14-15-48.png)

Note(토큰이름: 적절히 지정)를 입력하고 Expiration 기간을 지정한 후 'repo'와 'workflow'를 체크함
![](images/2026-02-20-14-16-37.png)

| [Top](#로컬-개발-환경-구성) |

---

## Docker HUB 회원가입   
Docker Hub는 컨테이너 이미지를 내려받고 저장할 공개된 이미지 저장소입니다.   
https://hub.docker.com 으로 접근하여 회원가입을 하십시오.   

| [Top](#로컬-개발-환경-구성) |

---

# 개발/배포 단계를 위한 추가 설치
모든 과정을 진행하기 위한 추가 설치입니다. 
개발과 배포 과정까지 진행하려면 추가 설치하세요.    

## IntelliJ 설치
IntelliJ는 통합개발환경(IDE:Integrated Development Environment) 도구의 하나입니다.   
### 설치
- 설치 파일 다운로드
  [JetBrain의 IDE페이지](https://www.jetbrains.com/idea/download)를 열고 설치 

- 실행: 실행 시 IntelliJ 환경설정을 불러들일 위치를 묻는데 그냥 OK클릭   
  ![](images/2026-02-20-13-50-00.png)

### IntelliJ 환경 설정
- Lombok설치
  Lombok은 클래스의 생성자, Getter(프라퍼티값을 읽는 메소드), Setter(프라퍼티값을 변경하는 메소드)등을    
  자동으로 작성해 주는 라이브러리입니다.    
  Lombok을 사용하면 어노테이션만 지정하면 이러한 메소드들을    
  자동으로 만들어 주기 때문에 편하고 코드도 깔끔해집니다.    

  ![](images/2026-02-20-13-50-40.png)

- 라이브러리 자동 import 옵션    
  첫번째 옵션은 코드 작성 중 필요한 라이브러리를 자동 import해 주는 것이고,   
  두번째 옵션은 불필요한 라이브러리 import를 자동으로 제거해 주는 옵션입니다.   
  ![](images/2026-02-20-13-51-08.png)

- 오타 검사 옵션 비활성화  
  코드나 주석에 오타를 체크해 주는 옵션입니다.   
  활성화 되어 있으면 컴파일 Warning갯수가 자꾸 보여서 눈에 거슬립니다.   
  ![](images/2026-02-20-13-51-21.png) 
  
| [Top](#로컬-개발-환경-구성) |

---
