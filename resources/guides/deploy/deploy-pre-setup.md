# 배포 사전 준비 가이드

배포 워크플로우(Step 1)에서 참조하는 가이드.
로컬/VM 도구 설치, `~/.ssh/config` 파싱, SSH 접속 테스트, VM 원격 도구 설치의 상세 절차를 정의한다.

- **참조 가이드**: `resources/guides/setup/prepare-deploy.md` (설치 명령 레시피), `resources/guides/setup/prepare.md` (Cloud CLI 설치), `resources/references/create-vm.md` (VM 생성)

---

## 1-1. CLOUD 판단

프로젝트 루트 `CLAUDE.md`의 `## NPD 워크플로우 상태 > ### design` 섹션에서 `CLOUD` 값을 읽는다 (AWS / Azure / GCP).
`CLOUD` 값이 없으면 사용자에게 ASK_USER로 질문한다.

---

## 1-2. 로컬 도구 자동 설치

로컬 환경의 OS를 감지하고, 아래 도구의 설치 여부를 확인한다.
이미 설치된 도구는 스킵하고, 미설치 도구만 자동 설치한다.

### K8s 도구

`resources/guides/setup/prepare-deploy.md` "로컬 설치" 섹션 참조.

| 도구 | 확인 명령 | Windows 설치 | Mac 설치 |
|------|----------|-------------|----------|
| kubectl | `which kubectl` | `powershell.exe -Command "winget install kubectl"` | `brew install kubectl` |
| kubens/kubectx | `which kubens` | git clone + symlink (Git Bash에서 실행) | `brew install kubectx` |
| helm | `which helm` | `powershell.exe -Command "winget install Helm.Helm"` | `brew install helm` |

### Cloud CLI

`resources/guides/setup/prepare.md` "Cloud CLI 설치 및 로그인" 섹션 참조. {CLOUD}에 맞는 CLI만 설치한다.

| CLOUD | 확인 명령 | Windows 설치 | Mac 설치 |
|-------|----------|-------------|----------|
| AWS | `aws --version` | `powershell.exe -Command 'msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi'` | `curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg" && sudo installer -pkg AWSCLIV2.pkg -target /` |
| Azure | `az version` | `powershell.exe -Command "winget install --exact --id Microsoft.AzureCLI"` | `brew update && brew install azure-cli` |
| GCP | `gcloud version` | GCP SDK 설치 파일 다운로드 안내 (자동 설치 불가, URL 제공) | `curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-darwin-arm.tar.gz && tar -xf google-cloud-cli-darwin-arm.tar.gz && ./google-cloud-sdk/install.sh --quiet` |

> **Windows 참고**: `winget`/`msiexec`는 PowerShell/CMD 전용이므로 MINGW(Git Bash) 환경에서는 `powershell.exe -Command` 래핑으로 실행한다.
> **GCP Windows 참고**: GCP SDK는 GUI 설치 프로그램이므로 자동 설치가 불가하다. 설치 URL(`https://cloud.google.com/sdk/docs/install#windows`)을 안내하고 사용자에게 수동 설치를 요청한다.

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
참고 URL: `https://github.com/unicorn-plugins/npd/blob/main/resources/guides/setup/prepare.md#cloud-cli-설치-및-로그인`

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
`resources/guides/setup/prepare-deploy.md`의 "VM 생성과 툴 설치" 섹션을 참조한다.

### 사전 검증

- `ssh {VM_HOST_ALIAS} "sudo -n true"` 로 NOPASSWD sudo 확인
- 실패 시 → 사용자에게 sudo 설정 안내

### 설치 순서 및 확인 명령

| 순서 | 도구 | 확인 명령 | CLOUD 조건 |
|------|------|----------|-----------|
| 1 | OS update | (항상 수행) | 공통 |
| 2 | Cloud CLI | `aws --version` / `az version` / `gcloud version` | {CLOUD}에 맞는 것만 |
| 3 | Docker | `docker --version` | 공통 |
| 4 | kubectl | `kubectl version --client` | 공통 |
| 5 | kubens/kubectx | `kubens --help` | 공통 |
| 6 | helm | `helm version` | 공통 |
| 7 | JDK | `java -version` | 공통 |

### 실행 방식

- 각 도구별로 `ssh {VM_HOST_ALIAS} "command -v {tool}"` 로 설치 여부 확인
- 미설치 도구만 prepare-deploy.md의 해당 섹션 명령을 `ssh {VM_HOST_ALIAS} "{설치 명령}"` 형태로 실행
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
