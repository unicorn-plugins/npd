# CLOUD별 k8s 생성 

- [CLOUD별 k8s 생성](#cloud별-k8s-생성)
- [AWS](#aws)
  - [시작](#시작)
  - [클러스터 생성](#클러스터-생성)
  - [클러스터 생성 확인](#클러스터-생성-확인)
  - [Credential 획득](#credential-획득)
  - [ALB 설정](#alb-설정)
    - [Subnet에 Tag 등록](#subnet에-tag-등록)
    - [IngressClass 객체 생성](#ingressclass-객체-생성)
  - [커스텀 노드풀(NodePool) 생성](#커스텀-노드풀nodepool-생성)
  - [테스트](#테스트)
  - [비용절감을 위한 팁](#비용절감을-위한-팁)
- [Azure](#azure)


---

# AWS
## 시작
- 상단 검색바에 'EKS'입력하여 'Elastic Kubernetes Service' 선택
- 우측의 '클러스터 생성' 클릭
  
## 클러스터 생성
Auto Mode로 EKS를 생성합니다.   
Auto Mode는 k8s Control Plane(실제 서비스가 배포되는 Worker 노드들을 관리하는 노드)을 AWS가 알아서 관리해주는 모드입니다.   
```
EKS Auto Mode = "인프라는 AWS가, 앱은 내가" 
  
기존 EKS                        EKS Auto Mode
──────────────────────────────────────────────
노드 직접 생성/관리      →      AWS가 자동 생성/관리
CNI 직접 설치           →      AWS가 자동 설치
ALB Controller 설치     →      Control Plane에 내장
노드 스케일링 설정       →      Pod 배포하면 자동 스케일
OS 패치/업데이트        →      AWS가 자동 처리

사용자가 할 일: IngressClass 생성 + Pod 배포만!
```

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

## 클러스터 생성 확인
- 생성된 클러스터 클릭
- '컴퓨팅' 탭 클릭
- 워커노드가 한개 생성되었는지 확인: Auto Mode이기 때문에 Control Plane 노드들이 안보이고 기본 Worker 노드 1개만 생성됨    
  
## Credential 획득
로그인   
```
aws sso login --profile {SSO-profile-name}
```
> SSO Profile 확인: aws configure list-profiles

PC에서 아래 명령 수행하면 ~/.kube/config 파일이 생성 또는 업데이트 됨  
```
aws eks update-kubeconfig \
  --region ap-northeast-2 \
  --name {EKS-name} \
  --profile {SSO-profile-name}
```
> EKS-name 확인: aws eks list-clusters --profile {SSO-profile-name}

아래 명령으로 정상 접근 확인    
```
kubectl get nodes
```
주의) 인증은 8시간만 유효합니다.  만료 시 로그인을 다시하고 kube config파일도 업데이트 해야 합니다.   

이후 작업은 본인이 직접 EKS를 생성한 경우만 수행하시고 **이미 존재하는 EKS를 사용할때는 하지 마십시오**.   

## ALB 설정
AWS Load Balancer는 외부에서 들어오는 트래픽을 내부로 전달하는 역할을 합니다.   
기본(vanilla) k8s에서 nginx ingress controller의 역할이라고 생각하면 됩니다.   
EKS Auto Mode에서는 Control Plane에 내장되어 있으나 생성을 위해서는 추가 작업이 필요합니다.   
실제 ALB가 생성되는 시점은 ingresslcass라는 객체가 생성될때입니다.   
  
![](images/2026-03-02-00-32-09.png)

### Subnet에 Tag 등록
Subnet은 VPC(Virtual Private Cloud)의 네트워크를 목적별로 나눈것을 의미합니다. 
- Subnet 리스트 확인
  ```
  export EKS_NAME={EKS-name}
  aws ec2 describe-subnets \
    --subnet-ids $(aws eks describe-cluster --name ${EKS_NAME} \
    --query "cluster.resourcesVpcConfig.subnetIds" --output text) \
    --query "Subnets[*].{ID:SubnetId,AZ:AvailabilityZone,Public:MapPublicIpOnLaunch,Name:Tags[?Key=='Name']|[0].Value}" \
    --output table
  ```
  결과예시: 각 Zone별로 Subnet 객체가 생성됩니다.   
  ```
  -------------------------------------------------------------------
  |                         DescribeSubnets                         |
  +------------------+----------------------------+-------+---------+
  |        AZ        |            ID              | Name  | Public  |
  +------------------+----------------------------+-------+---------+
  |  ap-northeast-2b |  subnet-0fa6c9fd50363d5b7  |  None |  True   |
  |  ap-northeast-2a |  subnet-0cf5cbb8b68cd06e1  |  None |  True   |
  |  ap-northeast-2d |  subnet-04f9d5b52c9d596ce  |  None |  True   |
  |  ap-northeast-2c |  subnet-047fd36a035b3bd3a  |  None |  True   |
  +------------------+----------------------------+-------+---------+
  ```

- Subnet에 'kubernetes.io/role/elb' 태그 추가 
  위 결과에서 'subnet-*'이 각 Zone에 생성된 Subnet들의 ID입니다.   
  아래와 같이 모든 subnet에 태그를 추가합니다.  이는 ALB에게 어떤 subnet에 생성되어야 하는지를 알려줍니다.     
  ```
  aws ec2 create-tags \
    --resources {subnet 1} {subnet 2} {...} \
    --tags Key=kubernetes.io/role/elb,Value=1
  ```

  ```
  aws ec2 create-tags \
    --resources subnet-0fa6c9fd50363d5b7 subnet-0cf5cbb8b68cd06e1 subnet-04f9d5b52c9d596ce subnet-047fd36a035b3bd3a \
    --tags Key=kubernetes.io/role/elb,Value=1
  ```

### IngressClass 객체 생성

```
cat <<EOF | kubectl apply -f -
# ingressclass.yaml
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: alb
  annotations:
    ingressclass.kubernetes.io/is-default-class: "true"
spec:
  controller: eks.amazonaws.com/alb
EOF
```

```
kubectl get ingressclass
```

---

## 커스텀 노드풀(NodePool) 생성
노드풀은 Node들을 관리하는 리소스입니다.  
노드를 생성하려면 먼저 노드풀을 만들어야 합니다.   
'CAPACITY_TYPE'을 spot으로 지정하면 AWS가 자원이 부족하면 노드가 없어질 위험이 있습니다.    
하지만 비용이 평균 60~70% 최대 90% 싸기 때문에 교육시에 잠깐 쓰는 목적으로는 권장됩니다.   
```
# ============================================================
# 변수 설정
# ============================================================
NODEPOOL_NAME="service"          # 노드풀 이름
CAPACITY_TYPE="spot"             # spot 또는 on-demand

# ============================================================
# NodePool 생성
# ============================================================
cat <<EOF | kubectl apply -f -
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: ${NODEPOOL_NAME}
  labels:
    agentpool: ${NODEPOOL_NAME}
spec:
  limits:
    cpu: 32
    memory: 128Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
  template:
    metadata:
      labels:
        agentpool: ${NODEPOOL_NAME}
    spec:
      nodeClassRef:
        group: eks.amazonaws.com
        kind: NodeClass
        name: default
      requirements:
        - key: eks.amazonaws.com/instance-family
          operator: In
          values: ["t3a", "m5a"]
        - key: eks.amazonaws.com/instance-size
          operator: In
          values: ["xlarge", "2xlarge"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["${CAPACITY_TYPE}"]
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
EOF
```

## 테스트
Ingress, Service, Deployment 배포   
```
kubectl apply -f https://raw.githubusercontent.com/unicorn-plugins/npd/refs/heads/main/resources/samples/sample-alb-test.yaml
```
아래 명령으로 URL 확인 
```
kubectl get ing 
```
약 2~3분 후에 URL로 접근하여 nginx 페이지 열리는지 확인    

확인 후 리소스 삭제 
```
k delete -f https://raw.githubusercontent.com/unicorn-plugins/npd/refs/heads/main/resources/samples/sample-alb-test.yaml
```

## 비용절감을 위한 팁
사용하지 않을 때 EKS를 정지하면 좋겠으나 EKS 클러스터를 정지시킬 수는 없습니다.    
하지만 Node를 전부 삭제하면 Control plane만 남으므로 비용을 최소화 할 수 있습니다.    

- 배포한 Pod 모두 삭제
  배포한 Pod가 모두 사라지면 그 Pod가 생성된 커스텀 노드풀(service)의 노드도 자동으로 삭제됩니다. 
   
- metrics-server 파드를 0으로 스케일링  
  기본으로 생성되는 metrics-server Pod가 있어 기본 노드가 삭제 안되니 아래와 같이 Pod를 0으로 만듭니다.   
  ```
  kubectl scale --replicas=0 deploy/metrics-server -n kube-system
  ```
- node 삭제
  ```
  kubectl get nodes 
  kubectl delete node {node id} --force --grace-period=0
  ```

> 주의: 기본 내장 노드풀(system, general-purpose)과 커스텀 노드풀을 삭제하지 마세요.   
  
---

# Azure
