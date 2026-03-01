# CLOUD별 VM 생성

- [CLOUD별 VM 생성](#cloud별-vm-생성)
  - [AWS: EC2(Elastic Compute Cloud) 생성](#aws-ec2elastic-compute-cloud-생성)
    - [시작](#시작)
    - [입력](#입력)
    - [출력: 생성된 EC2 클릭하여 확인](#출력-생성된-ec2-클릭하여-확인)
    - [테스트](#테스트)
    - [방화벽 오픈](#방화벽-오픈)
    - [고정 IP 지정](#고정-ip-지정)
    - [EC2 삭제](#ec2-삭제)
  - [Azure: 가상머신 생성](#azure-가상머신-생성)
    - [시작](#시작-1)
    - [입력](#입력-1)
    - [출력: 생성된 VM 클릭하여 확인](#출력-생성된-vm-클릭하여-확인)
    - [테스트](#테스트-1)
    - [방화벽 오픈](#방화벽-오픈-1)
    - [가상머신 삭제](#가상머신-삭제)
  - [GCP: 가상머신 생성](#gcp-가상머신-생성)
    - [시작](#시작-2)
    - [입력](#입력-2)
    - [출력: 생성된 VM 확인](#출력-생성된-vm-확인)

---

## AWS: EC2(Elastic Compute Cloud) 생성
### 시작
- http://console.aws.amazon.com/ 로그인 
- 상단 검색바에 'EC2'입력 
- '인스턴스 시작' 버튼 클릭 
### 입력
- OS: Ubuntu
- 인스턴스 유형: t3a.xlarge(4vcpu, 16G, 0.1872$/h) 또는 t3a.2xlarge(8vcpu, 32G, 0.3744$/h)
  컨테이너 수가 4개 이상이면 t3a.2xlarge 선택
- 키페어: 반드시 생성 선택하여 파일 다운로드. 이 파일이 VM 접근 SSH Key임 
- 스토리지: 30G로 상향 
### 출력: 생성된 EC2 클릭하여 확인 
- Public IP: '퍼블릭 IPv4 주소'
- SSH Key: 생성시 다운로드
- OS User: ubuntu
### 테스트
ssh ubuntu@{Public IP} -i {SSH Key파일 경로}
ex) ssh ubuntu@3.34.99.128 -i ~/workspace/ssh-key/my-ec2.pem
### 방화벽 오픈 
- 생성된 EC2 클릭 
- 보안탭에서 '보안그룹' 클릭 
- '인바운드 규칙 편집' 클릭 
- 규칙추가: 필요한 포트만 오픈하는게 맞으나 교육용이므로 모든 포트 오픈   
  - 유형: 모든 TCP
	- 소스: 0.0.0.0/0
  - 저장 
### 고정 IP 지정
- 'EC2' 메뉴 진입
- 좌측 메뉴에서 네트워크 및 보안 > 탄력적 IP 클릭 
- 상단의 탄력적 IP 주소 할당 클릭한 후 하단의 '할당'
- 할당한 IP 체크하고 산단의 작업 > 탄력적 IP 주소 연결 선택
- 인스턴스를 EC2 인스턴스 지정하고 하단의 '연결' 선택 

### EC2 삭제 
- EC2 메뉴 진입
- 삭제할 EC2 서버 선택하고 '인스턴스 상태 > 인스턴스 종료(삭제)' 클릭. 삭제 후에도 1시간 정도 보이고 자동 사라짐  
- 탄력적 IP삭제: 삭제해야 요금 청구 안됨 
  - 좌측 메뉴에서 네트워크 및 보안 > 탄력적 IP 클릭
  - 선택하고 상단의 '작업 > 탄력적IP 주소 릴리즈' 수행 

---

## Azure: 가상머신 생성 
### 시작 
- https://portal.azure.com 로그인 
- '만들기' 클릭 
- 가상머신 선택 
### 입력
- 구독: 본인 구독 
- 리소스그룹: 본인 리소스 그룹 
- 지역: Korea Central
- 이미지: Ubuntu 
- 크기: DS3_v2(4 vcpu, 14G, 월 240$) 또는 DS4_v2(8 vcpu, 28G, 월 482$)
  컨테이너 수가 4개 이상이면 DS4_v2 선택
- 사용자 이름: azureuser
- SSH 공개 키 원본: 새 키 쌍 생성
- 키 쌍 이름: 기본값 이용 또는 수정.  이 파일이 VM 접근 SSH Key임 
### 출력: 생성된 VM 클릭하여 확인 
- Public IP: '기본 NIC 공용 IP'
- SSH Key: 생성시 다운로드
- OS User: azureuser
### 테스트
ssh azureuser@{Public IP} -i {SSH Key파일 경로}
ex) ssh azureuser@20.249.211.13 -i ~/workspace/ssh-key/my-vm.pem
### 방화벽 오픈 
- 생성된 VM 클릭
- 좌측 메뉴에서 '네트워킹 > 네트워킹 설정' 클릭 
- 하단 '네트워크 보안 그룹' 우측의 '포트규칙 만들기' 버튼 클릭하고 '인바운드 포트 규칙' 선택
- 대상 포트 범위: 0-65535, 이름: Any라고 입력하고 저장. 필요한 포트만 오픈하는게 맞으나 교육용이므로 모든 포트 오픈 
### 가상머신 삭제
- 홈 햄버거 메뉴 > 모든 리소스 클릭 
- 우측 목록 상단의 '모든 필드에 대해 필터링'이라고 써있는 필터링 박스에 VM 이름 입력 
- SSH키, 가상머신, 공용 IP주소, 네트워크 보안그룹, 네트워크 인터페이스, 디스크 유형의 인스턴스 선택하고 삭제 
- 리프레시 해보면 하나씩 삭제되는것 확인할 수 있음  
  
---

## GCP: 가상머신 생성  
### 시작 
- https://console.cloud.google.com/ 로그인 
- 시작하기 아래에 'VM 만들기' 클릭 
### 입력
- 리전: asia-northeast3(서울)
- 머신유형: e2-standard-4 또는 e2-standard-8
  컨테이너 수가 4개 이상이면 e2-standard-8 선택
- OS및 스토리지 설정
	- 좌측 메뉴 'OS 및 스토리지' 선택 
	- '운영체제 및 스토리지' 하단의 '변경' 클릭 
	- 운영체제를 Ubuntu로 변경, 스토리지 크기를 30G로 상향 
- (옵션) 외부 IP 고정: VM 재시작해도 Public IP 변하지 않게 하는 옵션. 단 과금됨(시간당 1센트)
  - 좌측에서 '네트워킹' 클릭 
	- 스크롤 내려서 IP 스택 유형의 '외부 IPv4 주소' 찾음 
	- 클릭해서 '고정 외부 IP 주소 예약' 선택 
	- 이름을 적절히 입력하고 '예약' 클릭 
- 만들기 클릭 
   
### 출력: 생성된 VM 확인
- 초기화면에서 'Compute Engine' 버튼 클릭 > 가상머신 하위의 VM 인스턴스 클릭.   
  Compute Engine API 화면 나오면 몇분정도 기다림. 
	(만약 API 사용 설정 안되어 있으면 활성화함)       
	다시 가상머신 하위의 VM 인스턴스눌러서 생성된 VM클릭 
- 위치: 생성된 Zone(한국은 asia-northeast3-a)
- Public IP: 네트워크 인터페이스의 외부IP주소 컬럼(예:34.64.192.123) 
- OS User: GCP접속 ID(email이면 @앞)  
  확실하게 확인   
  - 'VM 인스턴스'목록의 '연결'컬럼의 SSH 우측 클릭하고 '브라우저 창에서 열기' 선택 
	- @앞에 있는것이 OS User명 
- SSH Key: 
	SSH Key 생성: ~/.ssh에 gcp_key, gcp_key.pub 파일 생성  	
	```
	ssh {USER}@{외부IP} -i ~/.ssh/gcp_key
	``` 
- SSH Key 업데이트   
	```
	gcloud compute instances add-metadata VM_NAME \
  --zone=asia-northeast3-a \
  --metadata ssh-keys="USERNAME:$(cat ~/.ssh/gcp_key.pub)"
  ```
	예)
	```
	gcloud compute instances add-metadata my-machine \
  --zone=asia-northeast3-a \
  --metadata ssh-keys="hiondal:$(cat ~/.ssh/gcp_key.pub)"	
	```
### 가상서버 삭제 


### 테스트
ssh {OS user}@{Public IP} -i {SSH Key파일 경로}
ex) ssh hiondal@34.64.192.123 -i ~/.ssh/gcp_key
### 방화벽 오픈 
- 'VM 인스턴스'목록의 '내부IP'컬럼의 'nic0' 클릭
- VPC 방화벽 규칙의 'VPC 방화벽 규칙 만들기' 클릭 
- 소스 IPv4범위: 0.0.0.0/0
- 프로토콜 및 포트: 모두 허용  
  필요한 포트만 오픈하는게 맞으나 교육용이므로 모든 포트 오픈 

---

## (필수) VM 접속 Config 파일 생성
아래 예제와 같이 ~/.ssh/config 파일에 접속 정보를 등록하면 'ssh aws'와 같이 편하게 접속할 수 있음   

아래 명령 수행하여 예제를 참고하여 본인 VM의 접속 정보 등록  
(주의) **이 작업은 반드시 해주세요**. AI가 이 정보를 읽어 필요한 툴을 자동으로 설치합니다.   
```
code ~/.ssh/config 
```

예시)  
Host 뒤의 값은 본인이 기억하기 쉬운 이름으로 아무거나 지정하시면 됩니다.  
```
Host aws
    HostName 3.36.58.0
    Port 22
    User ubuntu
    IdentityFile ~/.ssh/my-ec2.pem

Host azure
    HostName 20.249.211.13
    Port 22
    User azureuser
    IdentityFile ~/.ssh/my-vm.pem

Host gcp
    HostName 34.64.192.123
    Port 22
    User hiondal
    IdentityFile ~/.ssh/gcp_key
```