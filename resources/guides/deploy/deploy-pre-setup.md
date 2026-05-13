# 배포 사전 준비 가이드

배포 워크플로우(Step 1)에서 참조하는 가이드.
로컬/VM 도구 설치, `~/.ssh/config` 파싱, SSH 접속 테스트, VM 원격 도구 설치의 상세 절차를 정의한다.

- **참조 가이드**: `resources/references/create-vm.md` (VM 생성)

---

## 1-1. CLOUD 판단

프로젝트 루트 `AGENTS.md`의 `## NPD 워크플로우 상태 > ### design` 섹션에서 `CLOUD` 값을 읽는다 (AWS / Azure / GCP).
`CLOUD` 값이 없으면 사용자에게 ASK_USER로 질문한다.

---

## 1-2. 로컬 도구 자동 설치

로컬 환경의 OS를 감지하고, 아래 도구의 설치 여부를 확인한다.
이미 설치된 도구는 스킵하고, 미설치 도구만 자동 설치한다.

### K8s 도구

#### kubectl
**확인**: `kubectl version --client 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"`
- Windows (Powershell):
  ```
  winget install kubectl
  ```
- Mac:
  ```
  brew install kubectl
  ```

#### kubens/kubectx
**확인**: `kubens --help 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"`
- Windows (Git Bash):
  ```
  git clone https://github.com/ahmetb/kubectx.git ~/.kubectx
  ln -sf ~/.kubectx/kubectx /usr/local/bin/kubectx
  ln -sf ~/.kubectx/kubens /usr/local/bin/kubens
  ```
- Mac:
  ```
  brew install kubectx
  ```

#### helm
**확인**: `helm version 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"`
- Windows (Powershell):
  ```
  winget install Helm.Helm
  ```
- Mac:
  ```
  brew install helm
  ```

### Cloud CLI

{CLOUD}에 맞는 CLI만 설치한다.

#### AWS CLI
**확인**: `aws --version`
- Windows (Powershell):
  ```
  msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
  ```
  > 또는 https://awscli.amazonaws.com/AWSCLIV2.msi 를 다운로드하여 실행
- Mac:
  ```
  curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
  sudo installer -pkg AWSCLIV2.pkg -target /
  ```
- 설치 확인:
  ```
  aws --version
  ```

#### Azure CLI
**확인**: `az version`
- Windows (Powershell):
  ```
  winget install --exact --id Microsoft.AzureCLI
  ```
- Mac:
  ```
  brew update && brew install azure-cli
  ```

#### Google Cloud CLI
**확인**: `gcloud version`
- Windows: https://cloud.google.com/sdk/docs/install#windows 에서 설치파일을 다운로드하여 실행
- Mac:
  ```
  # Apple Silicon (M1/M2/M3/M4)
  curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-darwin-arm.tar.gz
  tar -xf google-cloud-cli-darwin-arm.tar.gz
  ./google-cloud-sdk/install.sh
  ```

> **Windows 참고**: `winget`/`msiexec`는 PowerShell/CMD 전용이므로 MINGW(Git Bash) 환경에서는 `powershell.exe -Command` 래핑으로 실행한다.
> **GCP Windows 참고**: GCP SDK는 GUI 설치 프로그램이므로 자동 설치가 불가하다. 설치 URL을 안내하고 사용자에게 수동 설치를 요청한다.

설치 후 각 도구의 버전을 확인하여 결과를 기록한다.

---

## 1-3. Cloud CLI 로그인 확인

{CLOUD} CLI가 설치되어 있으면 로그인 상태를 확인한다.

| CLOUD | 로그인 확인 명령 |
|-------|----------------|
| AWS | `aws sts get-caller-identity` |
| Azure | `az account show` |
| GCP | `gcloud auth list` |

로그인이 안 되어 있으면 ASK_USER로 수동 로그인을 안내한다.

### AWS 로그인

**1) Access Key 방식**
AWS Console에서 IAM > 사용자 > 보안 자격 증명 탭 > 액세스 키 만들기 > CLI 유형 선택으로 Access Key를 생성한다.
```
aws configure
```
프롬프트에 아래 정보를 입력한다. Access Key ID는 'AKIA'로 시작한다.
```
AWS Access Key ID: {Access Key ID}
AWS Secret Access Key: {Secret Access Key}
Default region name: {리전} (예: ap-northeast-2)
Default output format: json
```

**2) SSO 방식**
사전 준비: AWS Console > IAM Identity Center에서 아래 작업을 완료한다.
- IAM Identity Center 활성화
- 사용자 생성 (이메일 초대 → 비밀번호 설정)
- 권한 세트 생성 (예: `AdministratorAccess`)
- AWS 계정에 사용자 + 권한 세트 할당

SSO 설정:
```
aws configure sso
```
프롬프트에 아래 정보를 입력한다.
SSO start URL은 IAM Identity Center > 설정 > "AWS access portal URL"의 "기본 IPv4 전용" URL이다.
```
SSO session name: {임의 이름} (예: my-sso)
SSO start URL: {AWS access portal URL} (예: https://d-xxxxxxxxxx.awsapps.com/start)
SSO region: {리전} (예: ap-northeast-2)
SSO registration scopes: sso:account:access (기본값 Enter)
```
브라우저가 열리면 SSO 사용자로 로그인하고, 이후 CLI에서 계정/역할을 선택한다.

**Trouble shooting**
인증 실패 시 이전 인증 정보를 삭제하고 다시 한다.
```
rm -rf ~/.aws/credentials
rm -rf ~/.aws/config
aws configure
```

**설정 확인**:
```
aws sts get-caller-identity
```

### Azure 로그인

**1) Mac/Windows**
```
az login
```

**2) Linux**
아래 명령 수행 후 나오는 URL을 브라우저에서 접근하여 코드를 입력하여 로그인한다.
```
az login --use-device-code
```

**Trouble shooting**
인증 실패 시 이전 인증 정보를 삭제하고 다시 한다.
```
az logout
az account clear
az cache purge
```

**Azure 전역 설정**
```
az group list -o table
az configure -d group={리소스그룹} location={Location}
```
설정 확인:
```
az configure -l -o table
```

### Google Cloud 로그인

**1) Mac/Windows**
```
gcloud auth login
```

**2) Linux**
```
gcloud auth login --no-launch-browser
```
출력되는 URL을 브라우저에서 열어 인증 후, 인증 코드를 터미널에 붙여넣기 한다.

**Trouble shooting**
인증 실패 시 이전 인증 정보를 삭제하고 다시 한다.
```
gcloud auth revoke --all
gcloud config configurations delete default
gcloud auth login
```

**Google Cloud 전역 설정**
```
gcloud projects list
gcloud config set project {프로젝트ID}
gcloud config set compute/region {리전}
gcloud config set compute/zone {존}
```
설정 확인:
```
gcloud config list
```

---

## 1-4. VM 생성 안내

사용자에게 VM 준비 여부를 ASK_USER로 확인한다.

**"아직 없음"** 선택 시, {CLOUD}별 VM 생성 가이드 URL을 안내한다:

| CLOUD | VM 생성 가이드 URL |
|-------|-------------------|
| AWS | `https://github.com/unicorn-plugins/npd/blob/main/resources/references/create-vm.md#aws-ec2elastic-compute-cloud-생성` |
| Azure | `https://github.com/unicorn-plugins/npd/blob/main/resources/references/create-vm.md#azure-가상머신-생성` |
| GCP | `https://github.com/unicorn-plugins/npd/blob/main/resources/references/create-vm.md#gcp-가상머신-생성` |

`~/.ssh/config` 등록 안내 (`resources/references/create-vm.md` "VM 접속 Config 파일 생성" 섹션 참조):

```
Host {cloud별 기본 alias}
    HostName {VM Public IP}
    Port 22
    User {OS User}
    IdentityFile {SSH Key 파일 경로}
```

---

## 1-5. ~/.ssh/config 파싱

### 파싱 규칙

1. `~/.ssh/config` 파일을 읽는다.
   - 파일이 없으면: 작성 안내 후 1-4의 완료 대기로 돌아감
2. 파일에서 모든 `Host` 엔트리를 추출한다.
   - `Host *` 와일드카드 엔트리는 제외
   - `Include` 지시자는 미지원 (단일 파일만 파싱)
   - HostName, User, IdentityFile 중 하나라도 없는 엔트리는 제외
3. 사용자에게 배포 대상 VM의 Host alias를 ASK_USER로 선택하게 한다.

### 변수 매핑

선택된 Host 엔트리에서 정보를 추출하여 내부 변수에 저장:

| ssh config 필드 | 내부 변수 | [실행정보] 매핑 |
|----------------|----------|---------------|
| Host | VM_HOST_ALIAS | (신규) VM.HOST |
| HostName | VM_IP | VM.IP |
| User | VM_USER | VM.USERID |
| IdentityFile | VM_KEY | VM.KEY파일 |

---

## 1-6. SSH 접속 테스트

파싱된 정보로 SSH 접속을 테스트한다:

```bash
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new {VM_HOST_ALIAS} exit
```

- **성공** → 1-7로 진행
- **실패** → 에러 메시지 표시 후 ASK_USER로 재시도/건너뛰기 선택

---

## 1-7. VM 원격 도구 설치

SSH로 VM에 접속하여 도구 설치 여부를 확인하고, 미설치 도구를 자동 설치한다.

### 사전 검증

- `ssh {VM_HOST_ALIAS} "sudo -n true"` 로 NOPASSWD sudo 확인
- 실패 시 → 사용자에게 sudo 설정 안내

### OS Update
```
sudo apt-get update
```

### Cloud CLI (VM)
**확인**: `aws --version 2>/dev/null || az version 2>/dev/null || gcloud version 2>/dev/null`

{CLOUD}에 맞는 CLI만 설치한다.

- **AWS**:
  ```
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  unzip awscliv2.zip
  sudo ./aws/install
  aws --version
  ```

- **Azure**:
  ```
  curl -sL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null
  AZ_REPO=$(lsb_release -cs)
  echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $AZ_REPO main" | sudo tee /etc/apt/sources.list.d/azure-cli.list
  sudo apt-get update
  sudo apt-get install -y azure-cli
  az version
  ```

- **GCP**:
  ```
  curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
  tar -xf google-cloud-cli-linux-x86_64.tar.gz
  ./google-cloud-sdk/install.sh --quiet --disable-prompts
  source ~/google-cloud-sdk/path.bash.inc
  gcloud version
  ```

### Docker (VM)
**확인**: `docker --version 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"`

```bash
# 1. 필요한 패키지 설치
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# 2. Docker GPG key 추가
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 3. Docker repository 설정
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Docker 엔진 설치
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 5. 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 6. Docker 서비스 시작
sudo service docker start
```

> **참고**: `usermod -aG docker` 적용을 위해 터미널을 닫고 새 터미널에서 `docker version`으로 확인한다.
> AI 에이전트의 SSH 실행 시에는 매번 새 세션이므로 별도 ssh 호출로 확인하면 된다.

### kubectl (VM)
**확인**: `kubectl version --client 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"`
```
sudo snap install kubectl --classic
```

### kubens/kubectx (VM)
**확인**: `kubens --help 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"`
```
sudo apt install -y kubectx
```

### helm (VM)
**확인**: `helm version 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"`
```
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### JDK (VM)
**확인**: `java -version 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"`
```
# 1. 설치
sudo apt update && sudo apt install -y openjdk-21-jdk && \

# 2. JAVA_HOME 자동 탐지 후 /etc/environment 등록
JAVA_HOME_PATH=$(dirname $(dirname $(readlink -f $(which java)))) && \
echo "JAVA_HOME=\"$JAVA_HOME_PATH\"" | sudo tee -a /etc/environment && \

# 3. 즉시 적용 및 확인
source /etc/environment && \
echo "JAVA_HOME=$JAVA_HOME" && \
java -version
```

### 설치 순서 요약

| 순서 | 도구 | CLOUD 조건 |
|------|------|-----------|
| 1 | OS update | 공통 |
| 2 | Cloud CLI | {CLOUD}에 맞는 것만 |
| 3 | Docker | 공통 |
| 4 | kubectl | 공통 |
| 5 | kubens/kubectx | 공통 |
| 6 | helm | 공통 |
| 7 | JDK | 공통 |

### 실행 방식

- 각 도구별로 `ssh {VM_HOST_ALIAS} "command -v {tool}"` 로 설치 여부 확인
- 미설치 도구만 위 해당 섹션의 명령을 `ssh {VM_HOST_ALIAS} "{설치 명령}"` 형태로 실행
- 모든 apt 명령에 `-y` 플래그, GCP install.sh에 `--quiet --disable-prompts` 플래그 필수
- **AWS CLI install 스크립트(`./aws/install`)는 quiet 플래그를 지원하지 않으므로 플래그 없이 실행**
- Docker 설치 후 `usermod -aG docker` 적용: AI 에이전트는 매 ssh 호출이 새 세션이므로 재접속 없이 별도 ssh 명령으로 `docker version` 확인만 수행
- 각 도구 설치 후 버전 확인 명령으로 성공 여부 검증
- 도구별 설치 실패 시: 에러 로그 표시 + 사용자에게 재시도/수동 설치/계속 진행 선택 요청

---

## 1-8. 완료 보고

아래 템플릿으로 사용자에게 보고한다:

```
## 배포 사전 준비 완료

### 로컬 도구
| 도구 | 상태 | 버전 |
|------|------|------|
| kubectl | {설치됨/이미 있음} | {버전} |
| kubens/kubectx | {설치됨/이미 있음} | {버전} |
| helm | {설치됨/이미 있음} | {버전} |
| {CLOUD} CLI | {설치됨/이미 있음/수동 설치 안내} | {버전} |

### VM 도구 ({VM_HOST_ALIAS})
| 도구 | 상태 | 버전 |
|------|------|------|
| {CLOUD} CLI | {설치됨/이미 있음} | {버전} |
| Docker | {설치됨/이미 있음} | {버전} |
| kubectl | {설치됨/이미 있음} | {버전} |
| kubens/kubectx | {설치됨/이미 있음} | {버전} |
| helm | {설치됨/이미 있음} | {버전} |
| JDK | {설치됨/이미 있음} | {버전} |

### VM 접속 정보
- Host alias: {VM_HOST_ALIAS}
- 접속 명령: ssh {VM_HOST_ALIAS}
- IP: {HostName}
- User: {User}
- Key: {IdentityFile}
```
