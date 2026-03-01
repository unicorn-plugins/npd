# Container와 Kubernetes 배포를 위한 설치 
  	
- [Container와 Kubernetes 배포를 위한 설치](#container와-kubernetes-배포를-위한-설치)
	- [VM 생성](#vm-생성)
- [Cloud CLI 설치 및 로그인](#cloud-cli-설치-및-로그인)
	- [AWS](#aws)
		- [설치](#설치)
		- [로그인](#로그인)
		- [설정 확인](#설정-확인)
	- [Azure](#azure)
		- [설치](#설치-1)
		- [로그인](#로그인-1)
		- [전역 환경 설정](#전역-환경-설정)
	- [Google Cloud](#google-cloud)
		- [설치](#설치-2)
		- [로그인](#로그인-2)
		- [전역 환경 설정](#전역-환경-설정-1)

---
  
## VM 생성
https://github.com/unicorn-plugins/npd/blob/main/resources/references/create-vm.md
  
---

# Cloud CLI 설치 및 로그인 
사용할 Cloud별 CLI를 설치하고 로그인합니다.   
기획, 설계, 개발 단계까지는 불필요하며 배포 단계에서만 사용됩니다.    
	 
## AWS
AWS Cloud 사용 시 설치합니다.

### 설치  
**1)Windows**   
Powershell에서 수행  
```
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
```
> 또는 https://awscli.amazonaws.com/AWSCLIV2.msi 를 다운로드하여 실행

**2)Mac**
```
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

**3)Linux**
```
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**4)설치 확인**
```
aws --version
```

### 로그인
**1)Access Key 방식**
AWS Console에서 IAM > 사용자 > 사용자 선택 > 보안 자격 증명 탭 > 액세스 키 만들기 > CLI 유형 선택으로 Access Key를 생성합니다.
```
aws configure
```
프롬프트에 아래 정보를 입력합니다.
Access Key ID는 'AKIA'로 시작합니다.   
```
AWS Access Key ID: {Access Key ID}
AWS Secret Access Key: {Secret Access Key}
Default region name: {리전} (예: ap-northeast-2)
Default output format: json
```

**2)SSO 방식**
사전 준비: AWS Console > IAM Identity Center에서 아래 작업을 완료합니다.
- IAM Identity Center 활성화
- 사용자 생성 (이메일 초대 → 비밀번호 설정)
- 권한 세트 생성 (예: `AdministratorAccess`)
- AWS 계정에 사용자 + 권한 세트 할당

SSO 설정을 시작합니다.
```
aws configure sso
```
프롬프트에 아래 정보를 입력합니다.
SSO start URL은 IAM Identity Center > 설정 > "AWS access portal URL"의 "기본 IPv4 전용" URL입니다.
```
SSO session name: {임의 이름} (예: my-sso)
SSO start URL: {AWS access portal URL} (예: https://d-xxxxxxxxxx.awsapps.com/start)
SSO region: {리전} (예: ap-northeast-2)
SSO registration scopes: sso:account:access (기본값 Enter)
```
브라우저가 열리면 SSO 사용자로 로그인하고, 이후 CLI에서 계정/역할을 선택합니다.
```
CLI default client Region: {리전} (예: ap-northeast-2)
CLI default output format: json
CLI profile name: {프로필 이름} (예: my-sso-profile)
```

**3)Trouble shooting**  
인증 실패 시 이전 인증 정보를 삭제하고 다시 합니다.
```
rm -rf ~/.aws/credentials
rm -rf ~/.aws/config
aws configure
```

### 설정 확인
```
aws sts get-caller-identity
```
  
---
   
##  Azure
Azure Cloud 사용 시 설치합니다.   

### 설치
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

### 로그인       
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

### 전역 환경 설정 
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
  
---
  
## Google Cloud
Google Cloud 사용 시 설치합니다.

### 설치    
**1)Windows**   
https://cloud.google.com/sdk/docs/install#windows 에서 설치파일을 다운로드하여 실행합니다.
또는 PowerShell에서:
```
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe
```

**2)Mac**
```
# Apple Silicon (M1/M2/M3/M4)
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-darwin-arm.tar.gz
tar -xf google-cloud-cli-darwin-arm.tar.gz
./google-cloud-sdk/install.sh

# Intel
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-darwin-x86_64.tar.gz
tar -xf google-cloud-cli-darwin-x86_64.tar.gz
./google-cloud-sdk/install.sh
```

**3)Linux**
```
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
tar -xf google-cloud-cli-linux-x86_64.tar.gz
./google-cloud-sdk/install.sh
```

설치 후 셸을 재시작하거나 아래 명령을 수행합니다.
```
source ~/google-cloud-sdk/path.bash.inc
```

**4)설치 확인**
```
gcloud version
```
 
### 로그인  
**1)Mac/Windows**  
```
gcloud auth login
```

**2)Linux**
```
gcloud auth login --no-launch-browser
```
출력되는 URL을 브라우저에서 열어 인증 후, 인증 코드를 터미널에 붙여넣기 합니다.

**3)Trouble shooting**  
인증 실패 시 이전 인증 정보를 삭제하고 다시 합니다.
```
gcloud auth revoke --all
gcloud config configurations delete default
gcloud auth login
```

### 전역 환경 설정  
프로젝트와 리전을 기본값으로 설정합니다.

프로젝트 목록 확인:
```
gcloud projects list
```

기본값 설정:
```
gcloud config set project {프로젝트ID}
gcloud config set compute/region {리전}
gcloud config set compute/zone {존}
```
예시)
```
gcloud config set project my-project-123
gcloud config set compute/region asia-northeast3
gcloud config set compute/zone asia-northeast3-a
```

설정된 값을 확인합니다.
```
gcloud config list
```
  
---

