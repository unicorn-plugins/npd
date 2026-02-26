# Container와 Kubernetes 배포를 위한 설치 

- [로컬 설치](#로컬-설치)
  - [kubectl: Powershell에서 수행](#kubectl-powershell에서-수행)
  - [kubens/kubectx](#kubenskubectx)
  - [helm](#helm)
- [VM 생성과 툴 설치](#vm-생성과-툴-설치)
  - [VM 생성](#vm-생성)
  - [Update OS](#update-os)
  - [Cloud CLI 설치](#cloud-cli-설치)
  - [Docker](#docker)
  - [kubectl 설치](#kubectl-설치)
  - [kubens/kubectx](#kubenskubectx-1)
  - [helm](#helm-1)
  - [jdk](#jdk)
  
---
  
## 로컬 설치
### kubectl: Powershell에서 수행
**확인**: `kubectl version --client 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"`
- Window: 
	```
	winget install kubectl
	```
- Mac
	```
	brew install kubectl
	```
	
### kubens/kubectx
**확인**: `kubens --help 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"`
- Window: git bash에서 수행
	```
	git clone https://github.com/ahmetb/kubectx.git ~/.kubectx
	ln -sf ~/.kubectx/kubectx /usr/local/bin/kubectx
	ln -sf ~/.kubectx/kubens /usr/local/bin/kubens

	# 확인
	kubectx --help
	kubens --help
	```
- Mac
	```
	brew install kubectx
  ```
	
### helm
**확인**: `helm version 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"`
- Window: Powershell에서 수행
  ```
	winget install Helm.Helm
  ```
- Mac
	```
	brew install helm
	```
  
---
  	
## VM 생성과 툴 설치 
### VM 생성: 
https://github.com/unicorn-plugins/npd/blob/main/resources/references/create-vm.md
  
### Update OS 
```
sudo apt-get update
```

### Cloud CLI 설치
**확인**: `aws --version 2>/dev/null || az version 2>/dev/null || gcloud version 2>/dev/null`
- AWS
	```
	curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
	unzip awscliv2.zip
	sudo ./aws/install
	
	aws --version
	```

- Azure 
	```
	# 1. Microsoft 서명 키 추가
	curl -sL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null

	# 2. Azure CLI 저장소 추가
	AZ_REPO=$(lsb_release -cs)
	echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $AZ_REPO main" | sudo tee /etc/apt/sources.list.d/azure-cli.list

	# 3. 패키지 리스트 업데이트 및 설치
	sudo apt-get update
	sudo apt-get install -y azure-cli
	
	az version
	```

- GCP
	```
	curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
	tar -xf google-cloud-cli-linux-x86_64.tar.gz
	./google-cloud-sdk/install.sh --quiet --disable-prompts

	source ~/google-cloud-sdk/path.bash.inc

	gcloud version
	```

### Docker
**확인**: `docker --version 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"`

아래 스크립트를 순차적으로 실행한다:
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

# 5. 현재 사용자를 docker 그룹에 추가 (sudo 없이 docker 명령어 사용 가능)
sudo usermod -aG docker $USER

# 6. Docker 서비스 시작
sudo service docker start
```

> **참고**: `usermod -aG docker` 적용을 위해 터미널을 닫고 새 터미널에서 `docker version`으로 확인한다.
> AI 에이전트의 SSH 실행 시에는 매번 새 세션이므로 별도 ssh 호출로 확인하면 된다.

### kubectl 설치
**확인**: `kubectl version --client 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"`
```
sudo snap install kubectl --classic
```

### kubens/kubectx
**확인**: `kubens --help 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"`
```
sudo apt install -y kubectx
```

### helm
**확인**: `helm version 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"`
```
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### jdk
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
