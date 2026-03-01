# CLOUD별 k8s 생성 

## AWS 
### 시작 
- 상단 검색바에 'EKS'입력하여 'Elastic Kubernetes Service' 선택
- 우측의 '클러스터 생성' 클릭
### 클러스터 생성  
- 이름: 팀 프로젝트 수행 시는 'eks-{Team ID}'로 개인 프로젝트 수행 시는 'eks-{개인ID}'
- 클러스터 IAM 역할: k8s Control Plane(실제 서비스가 배포되는 Worker 노드들을 관리하는 노드)이 AWS리소스를 관리하도록 역할 부여 
  - 우측 '권장 역할 생성' 클릭
  - 하단의 '역할 생성' 클릭
  - AmazonEKSAuthClusterRole 지정 
- 노드 IAM 역할: 워커 노드에서 ECR접근, 클러스터 등록 등 기본 역할 부여
  - 우측 '권장 역할 생성' 클릭
  - 하단의 '역할 생성' 클릭
  - AmazonEKSAutoNodeRole 지정 
- 하단의 '생성' 클릭 
### 워커 노드 생성 
- Amazon Elastic Kubernetes Service 접근 
- 좌측에서 '클러스터' 선택하고 생성된 EKS 클릭 
- '컴퓨팅' 탭 선택
- 스크롤 내려 '노드 그룹' 카드의 '추가' 클릭 
- 노드 그룹 구성
  - 이름: 'service'
  - 노드 IAM 역할: 기존 역할 선택. 없으면 우측의 '권장 역할 생성' 클릭 
    - 사용 사례: EC2 선택하고 '다음'버튼 클릭
    - 권한 정책: 
      - AmazonEKSWorkerNodePolicy, AmazonEC2ContainerRegistryReadOnly, AmazonEKS_CNI_Policy만 선택
      - '권한 정책(3/1116)'으로 되어 있으면 이미 선택되어 있는 것임 
      - '다음' 클릭
    - 역할 이름: node-iam-default-role 
    - '역할 생성' 클릭하여 생성 
    - 노드 그룹 구성 화면으로 돌아와서 '권장 역할 생성' 좌측의 '리프레시' 아이콘 클릭하고 만든 역할을 선택 
    - 하단의 '다음' 클릭 
- 컴퓨팅 및 조정 구성 설정 
  - 용량 유형: Spot 으로 지정. AWS가 노드를 없앨 위험이 있지만 90% 저렴하여 학습환경에 구너장 
  - 인스턴스 유형: t3.xlarge (4 vcpu, 4.5GB)
  - 디스크 크기: 50 GiB
  - 노드 그룹 조정 구성: 원하는 크기 2노드, 최소 크기 2 노드, 최대 크기 5 노드
  - '다음' 클릭 
- 네트워킹 지정: 수정하지 않고 '다음' 클릭
- 하단의 '생성' 클릭 

 