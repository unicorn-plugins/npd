# 로컬 개발 환경 구성

- [로컬 개발 환경 구성](#로컬-개발-환경-구성)
- [기본 설치](#기본-설치)
  - [Git Client 설치](#git-client-설치)
    - [설치](#설치)
    - [기존 인증정보 삭제](#기존-인증정보-삭제)
    - [Git 사용법](#git-사용법)
  - [Window Terminal의 Git Bash 설정(Windows Only)](#window-terminal의-git-bash-설정windows-only)
  - [Node.js 설치](#nodejs-설치)
  - [Microsoft Visual Studio Code 설치](#microsoft-visual-studio-code-설치)
    - [설치](#설치-1)
    - [설정](#설정)
  - [Claude Code 설치](#claude-code-설치)
  - [Oh My ClaudeCode (OMC) 설치](#oh-my-claudecode-omc-설치)
  - [DMAP 빌더 설치(권장)](#dmap-빌더-설치권장)
    - [플러그인 설치](#플러그인-설치)
    - [웹에서 실행](#웹에서-실행)
  - [NPD 플러그인 추가](#npd-플러그인-추가)
    - [플러그인 추가](#플러그인-추가)
    - [플러그인 추가 확인](#플러그인-추가-확인)
- [추가 설치](#추가-설치)
  - [Python 설치](#python-설치)
  - [IntelliJ 설치](#intellij-설치)
    - [설치](#설치-2)
    - [IntelliJ 환경 설정](#intellij-환경-설정)
  - [Docker Desktop 설치](#docker-desktop-설치)
  - [GitHub 회원가입 및 토큰 생성](#github-회원가입-및-토큰-생성)
    - [회원가입](#회원가입)
    - [접근 토큰 생성](#접근-토큰-생성)
  - [Docker HUB 회원가입](#docker-hub-회원가입)
  - [DBeaver 설치(옵션)](#dbeaver-설치옵션)
- [Cloud CLI 설치](#cloud-cli-설치)
  - [Azure CLI 설치](#azure-cli-설치)

---

# 기본 설치
기획과정만 수행할 때 최소한의 설치입니다. 

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

설치 후 초기 구성:

```bash
claude 
```
  
| [Top](#로컬-개발-환경-구성) |

---

## Oh My ClaudeCode (OMC) 설치
OMC는 Claude Code를 더 잘 사용하기 위한 플러그인입니다.    
  
Claude Code 실행 후 프롬프트에서 순차 수행:
```
claude
```

아래 명령 수행  
```
/plugin marketplace add https://github.com/Yeachan-Heo/oh-my-claudecode
/plugin install oh-my-claudecode
```

아래 명령으로 셋업 수행. Setup 시 MCP는 context7만 설치  
```
/oh-my-claudecode:omc-setup
```

| [Top](#로컬-개발-환경-구성) |

---

## DMAP 빌더 설치(권장)
DMAP 빌더는 Claude Code 터미널이 아닌 웹페이지에서 NPD 플러그인을 사용하기 위해 설치합니다.   
Claude Code를 이용할 때는 설치 안해도 됩니다.   

작업 디렉토리 작성       
Linux/Mac 사용자는 터미널에서 수행하고 Window 사용자는 Window Terminal의 Git Bash 터미널에서 수행합니다.      
Window 사용자는 특별히 언급이 없으면 Git Bash 터미널을 사용합니다.    
```
mkdir -p ~/workspace
```
> Tip: 위 명령에서 `-p'는 이미 해당 디렉토리가 있어도 에러를 안내는 옵션이고 '~'는 사용자의 홈디렉토리를 의미합니다.      
  
### 플러그인 설치   
```bash
claude plugin marketplace add unicorn-plugins/dmap
claude plugin install dmap@unicorn
```
  
### 웹에서 실행   
PC에 DMAP을 클론하고 웹 앱을 실행하면 브라우저에서 DMAP 빌더를 사용할 수 있음.
**1. DMAP 클론**    
```bash
cd ~/workspace
git clone https://github.com/unicorn-plugins/dmap.git
cd dmap
```

**2. DMAP 웹 실행**    
```bash
cd dmap-web
npm install
npm run dev
```
  
**3. 브라우저에서 확인**    
http://localhost:5173 

**4.NPD플러그인 추가**     
'unicorn-plugins/npd'를 입력하여 추가합니다.   
![](images/2026-02-20-16-07-32.png)  

메뉴관리 아이콘을 누르고 '[AI 추천]'버튼을 눌러 메뉴명을 추천 받습니다.    
필요 시 메뉴를 drag & drop으로 순서를 바꿉니다.   
![](images/2026-02-20-16-08-58.png)
   
| [Top](#로컬-개발-환경-구성) |

---

## NPD 플러그인 추가
### 플러그인 추가  
'## DMAP 빌더 설치(권장)'를 수행하였다면 이미 추가되었으니 스킵합니다.   

### 플러그인 추가 확인
npd 플러그인이 추가되었는지 확인합니다.   
```
claude plugin list
```

Claude Code를 수행하고 설치되었는지 확인합니다.    
![](images/2026-02-20-16-14-23.png)   
  
| [Top](#로컬-개발-환경-구성) |
    
---

# 추가 설치
전 과정을 진행하기 위한 추가 설치입니다. 
   
## Python 설치
최신 버전을 설치하세요.  
https://www.python.org/downloads/


| [Top](#로컬-개발-환경-구성) |

---

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

## DBeaver 설치(옵션)
DBeaver는 SQL Client 프로그램의 하나입니다.   
Database를 관리하고 SQL로 테이블과 데이터를 처리할 수 있습니다.    

- 설치하기 
  - 설치파일 다운로드: [설치파일 다운로드](https://dbeaver.io/download/) 링크를 열어 OS에 맞는 파일을 다운로드    
  - 파일을 실행하여 설치합니다. 기본 옵션 그대로 설치합니다.   
- 테스트   
  - DBeaver를 실행합니다.  최초 실행 시 Connection생성 창은 닫으세요.   
    ![](images/2026-02-20-14-09-33.png)  
          
  - 테스트로 MySQL Database를 컨테이너로 실행합니다.  
    Windows 사용자는 MobaXTerm, Mac사용자는 터미널에서 실행     
    ```
    docker run -d --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=P@ssw0rd$ mysql
    ```     

  - 아래와 같이 DB를 연결 합니다.: Root암호는 P@ssw0rd$임(MySQL 컨테이너 실행 시 옵션으로 지정)  
    ![](images/2026-02-20-14-09-58.png)
    ![](images/2026-02-20-14-10-04.png)  
    ![](images/2026-02-20-14-11-06.png)  
  - Driver파일을 다운로드 한 후 아래와 같이 경고가 나오면  아래를 수행합니다.  
    ![](images/2026-02-20-14-11-30.png)  
    ![](images/2026-02-20-14-11-39.png)    
    
  - 아래와 같이 DB가 연결되면 성공!   
    ![](images/2025-02-23-19-05-24.png)  
   
  - SQL편집기를 테스트 해 봅니다.   
    ![](images/2026-02-20-14-11-59.png)
    ![](images/2026-02-20-14-12-07.png)
      
| [Top](#목차) |

---

# Cloud CLI 설치
사용할 Cloud별 CLI를 설치합니다.  

##  Azure CLI 설치    
Azure Cloud 사용 시 설치합니다.   

**1.설치**   
**1)Windows**   
```
winget install --exact --id Microsoft.AzureCLI
```

**2)Mac**    
```
brew update && brew install azure-cli
```

**3)Linux**   
```
# 1. Microsoft 서명 키 추가
curl -sL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null

# 2. Azure CLI 저장소 추가
AZ_REPO=$(lsb_release -cs)
echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $AZ_REPO main" | sudo tee /etc/apt/sources.list.d/azure-cli.list

# 3. 패키지 리스트 업데이트 및 설치
sudo apt-get update
sudo apt-get install azure-cli
```

**2.Azure Login**       
**1)Mac/Windows**
```
az login
```

**2)Linux**
아래 명령 수행 후 나오는 URL을 브라우저에서 접근하여 URL옆에 있는 코드를 입력하여 로그인 합니다.  
로그인 후 콘솔로 돌아오면 Subscription선택하는 화면이 나옵니다.  
Subscription 번호를 입력하여 로그인을 완료 합니다.     
```
az login --use-device-code
```

**3)Trouble shooting**    
만약, 인증 실패 시 이전 인증 정보를 삭제하고 다시 합니다.   
```
az logout
az account clear
az cache purge
```

**3.Azure 전역 설정**    
명령어에서 반복적으로 사용할 Resource Group과 Location값을 기본 설정에 셋팅합니다.   
Azure resource group을 확인합니다.  
```
az group list -o table
```

```
az configure -d group={리소스그룹} location={Location}
```
예시)
```
az configure -d group=tiu-dgga-rg location=koreacentral
```

설정된 값을 확인합니다.
```
az configure -l -o table
```

| [Top](#로컬-개발-환경-구성) |

