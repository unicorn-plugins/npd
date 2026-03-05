# CI/CD 도구 사전 설정 가이드

## 목적

AI 에이전트가 kubectl/helm CLI로 실행 가능한 CI/CD 도구 설치 자동화.  
대상 도구: Jenkins, SonarQube, ArgoCD (+ 클라우드별 사전작업).  
원본: `resources/references/setup-cicd-tools.md`에서 AI 실행 가능 부분 추출.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| K8s 클러스터 정보 | `(런타임 결정)` | CI/CD 도구 설치 대상 클러스터 |
| [실행정보] 블록 | `(프롬프트 제공)` | CLOUD, CI_TOOL 파싱 |

[실행정보] 예시:
```
[실행정보]
- CLOUD: AWS              # AWS / Azure / GCP
- CI_TOOL: Jenkins        # Jenkins / GitHubActions
- EKS_NAME: my-eks        # AWS인 경우 EKS 클러스터 이름
- VM_HOST: web-server     # ~/.ssh/config의 Host alias (Nginx 프록시 설정용)
```

## 출력 (이 단계 산출물)

| 산출물 | 설명 |
|--------|------|
| Jenkins (CI_TOOL=Jenkins인 경우) | jenkins 네임스페이스에 Helm 설치 완료 |
| SonarQube | sonarqube 네임스페이스에 Helm 설치 완료 |
| ArgoCD | argocd 네임스페이스에 Helm 설치 완료 |
| Nginx 프록시 설정 | Web Server VM에 SSH로 자동 설정 완료 |
| docs/cicd/cicd-pre-setup-report.md | 설치 결과 보고서 |

## 방법론

### 사전 준비사항 확인

[실행정보]에서 아래 변수를 파싱하여 환경변수로 설정:

```bash
export CLOUD="{CLOUD}"          # AWS / Azure / GCP
export CI_TOOL="{CI_TOOL}"      # Jenkins / GitHubActions
export VM_HOST="{VM_HOST}"      # ~/.ssh/config의 Host alias
```

AWS인 경우 추가:
```bash
export EKS_NAME="{EKS 클러스터 이름}"
```

SSH 접속 테스트:
```bash
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new ${VM_HOST} exit
```

이미 설치된 도구 감지 — 존재하면 해당 도구 설치 단계를 건너뜀:
```bash
kubectl get ns jenkins 2>/dev/null && helm list -n jenkins 2>/dev/null | grep jenkins && echo "Jenkins already installed, skipping"
kubectl get ns sonarqube 2>/dev/null && helm list -n sonarqube 2>/dev/null | grep sonar && echo "SonarQube already installed, skipping"
kubectl get ns argocd 2>/dev/null && helm list -n argocd 2>/dev/null | grep argocd && echo "ArgoCD already installed, skipping"
```

---

### Phase 1: 클라우드별 사전작업

#### [AWS EKS] 사전작업

> CLOUD == AWS인 경우에만 수행.

AWS CLI 사전 검증:
```bash
aws sts get-caller-identity
```

**StorageClass 생성 (gp2-eks-auto)**

EKS Auto Mode 전용 StorageClass를 생성함.  
기본 `gp2` StorageClass는 in-tree provisioner를 사용하여 EKS Auto Mode에서 지원되지 않음.
```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp2-eks-auto
provisioner: ebs.csi.eks.amazonaws.com
parameters:
  type: gp3
  fsType: ext4
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
allowVolumeExpansion: true
EOF
```

**ALB Subnet 태그 등록**

`create-k8s.md`의 'ALB 설정' 섹션을 이미 수행했다면 이 단계는 건너뜀.

Subnet 목록 확인:
```bash
aws ec2 describe-subnets \
  --subnet-ids $(aws eks describe-cluster --name ${EKS_NAME} \
  --query "cluster.resourcesVpcConfig.subnetIds" --output text) \
  --query "Subnets[*].{ID:SubnetId,AZ:AvailabilityZone,Public:MapPublicIpOnLaunch}" \
  --output table
```

위 결과의 모든 Subnet ID를 아래 명령에 넣어 태그 등록:
```bash
aws ec2 create-tags \
  --resources {subnet-1} {subnet-2} {subnet-3} {subnet-4} \
  --tags Key=kubernetes.io/role/elb,Value=1
```

**IngressClass 생성 (alb)**

```bash
cat <<EOF | kubectl apply -f -
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

확인:
```bash
kubectl get ingressclass
```

**NodePool 생성 (cicd)**

Karpenter NodePool CRD로 cicd 노드풀을 생성함:
```bash
NODEPOOL_NAME="cicd"
CAPACITY_TYPE="spot"

cat <<EOF | kubectl apply -f -
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: ${NODEPOOL_NAME}
  labels:
    agentpool: ${NODEPOOL_NAME}
spec:
  limits:
    cpu: 16
    memory: 64Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
  template:
    metadata:
      labels:
        agentpool: ${NODEPOOL_NAME}
    spec:
      taints:
        - key: dedicated
          value: ${NODEPOOL_NAME}
          effect: NoSchedule
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
          values: ["large", "xlarge"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["${CAPACITY_TYPE}"]
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
EOF
```

**NodePool 생성 (sonarqube)**

instance-size를 "xlarge", "2xlarge"로 설정하여 4core/16GB 이상 확보:
```bash
NODEPOOL_NAME="sonarqube"
CAPACITY_TYPE="spot"

cat <<EOF | kubectl apply -f -
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: ${NODEPOOL_NAME}
  labels:
    agentpool: ${NODEPOOL_NAME}
spec:
  limits:
    cpu: 16
    memory: 64Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
  template:
    metadata:
      labels:
        agentpool: ${NODEPOOL_NAME}
    spec:
      taints:
        - key: dedicated
          value: ${NODEPOOL_NAME}
          effect: NoSchedule
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

NodePool 생성 확인 (Node는 Pod 배포 시 자동 생성됨):
```bash
kubectl get nodepool
```

> NodePool 생성 후 실제 Node 프로비저닝은 Pod 배포 시 자동으로 이루어짐.  
> 리소스 부족 시 최대 5분 대기 필요.

---

#### [Azure AKS] 사전작업

> CLOUD == Azure인 경우에만 수행.

**NodePool 생성 (cicd)**

```bash
NODEPOOL_NAME="cicd"
CAPACITY_TYPE="on-demand"

cat <<EOF | kubectl apply -f -
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: ${NODEPOOL_NAME}
  labels:
    agentpool: ${NODEPOOL_NAME}
spec:
  limits:
    cpu: 16
    memory: 64Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
  template:
    metadata:
      labels:
        agentpool: ${NODEPOOL_NAME}
    spec:
      taints:
        - key: dedicated
          value: ${NODEPOOL_NAME}
          effect: NoSchedule
      nodeClassRef:
        group: karpenter.azure.com
        kind: AKSNodeClass
        name: default
      requirements:
        - key: karpenter.azure.com/sku-family
          operator: In
          values: ["D"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["${CAPACITY_TYPE}"]
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
EOF
```

**NodePool 생성 (sonarqube)**

```bash
NODEPOOL_NAME="sonarqube"
CAPACITY_TYPE="on-demand"

cat <<EOF | kubectl apply -f -
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: ${NODEPOOL_NAME}
  labels:
    agentpool: ${NODEPOOL_NAME}
spec:
  limits:
    cpu: 16
    memory: 64Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
  template:
    metadata:
      labels:
        agentpool: ${NODEPOOL_NAME}
    spec:
      taints:
        - key: dedicated
          value: ${NODEPOOL_NAME}
          effect: NoSchedule
      nodeClassRef:
        group: karpenter.azure.com
        kind: AKSNodeClass
        name: default
      requirements:
        - key: karpenter.azure.com/sku-family
          operator: In
          values: ["D"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["${CAPACITY_TYPE}"]
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
EOF
```

NodePool 생성 확인 (Node는 Pod 배포 시 자동 생성됨):
```bash
kubectl get nodepool
```

---

#### [GCP GKE] 사전작업

> CLOUD == GCP인 경우 별도 NodePool 생성 불필요.

GKE Autopilot은 커스텀 노드풀을 직접 생성할 수 없음.  
Pod를 배포하면 Google이 resources.requests 기반으로 노드를 자동 프로비저닝함.  
nodeSelector/tolerations를 사용한 노드 격리 불가이므로 네임스페이스 분리로 논리적 격리 유지.

---

### Phase 2: Jenkins 설치 (CI_TOOL == Jenkins인 경우)

> CI_TOOL != Jenkins이면 이 Phase를 건너뜀.

#### Helm repo 추가 및 chart 다운로드

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

mkdir -p ~/install && cd ~/install

helm pull bitnami/jenkins --version 13.6.17

tar xvf jenkins-13.6.17.tgz

cd jenkins
```

#### 클라우드별 jenkins.yaml 생성

> **MUST**: 아래 yaml의 `jenkinsPassword` 값을 반드시 그대로 사용할 것. 임의 변경 금지.

**[AWS EKS]** jenkins.yaml:
```bash
cat > jenkins.yaml << EOF
global:
  storageClass: "gp2-eks-auto"

jenkinsUser: admin
jenkinsPassword: "P@ssw0rd$"
jenkinsHost: "http://myjenkins.io"
jenkinsHome: /bitnami/jenkins/home

service:
  type: ClusterIP

javaOpts:
  - -Dfile.encoding=UTF-8

containerPorts:
  http: 8080
  https: 8443
  agentListener: 50000

agentListenerService:
  enabled: true
  type: ClusterIP
  ports:
    agentListener: 50000

persistence:
  enabled: true
  storageClass: "gp2-eks-auto"
  accessModes:
    - ReadWriteOnce
  size: 8Gi

nodeSelector:
  agentpool: cicd
tolerations:
- key: "dedicated"
  operator: "Equal"
  value: "cicd"
  effect: "NoSchedule"

image:
  registry: docker.io
  repository: bitnamilegacy/jenkins
  tag: 2.516.2-debian-12-r0

resources:
  limits:
    cpu: "1"
    memory: "2Gi"
  requests:
    cpu: "500m"
    memory: "1Gi"

agent:
  enabled: true
  resources:
    limits:
      cpu: "1"
      memory: "1Gi"
    requests:
      cpu: "500m"
      memory: "512Mi"
  image:
    registry: docker.io
    repository: bitnamilegacy/jenkins-agent
    tag: 0.3327.0-debian-12-r1

tls:
  resources:
    limits:
      cpu: "250m"
      memory: "256Mi"
    requests:
      cpu: "100m"
      memory: "128Mi"

ingress:
  enabled: true
  hostname: myjenkins.io
  pathType: Prefix
  ingressClassName: alb
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80}]'
    alb.ingress.kubernetes.io/group.name: cicd-tools
EOF
```

**[Azure AKS]** jenkins.yaml:
```bash
cat > jenkins.yaml << EOF
global:
  storageClass: "managed"

jenkinsUser: admin
jenkinsPassword: "P@ssw0rd$"
jenkinsHost: "http://myjenkins.io"
jenkinsHome: /bitnami/jenkins/home

service:
  type: ClusterIP

javaOpts:
  - -Dfile.encoding=UTF-8

containerPorts:
  http: 8080
  https: 8443
  agentListener: 50000

agentListenerService:
  enabled: true
  type: ClusterIP
  ports:
    agentListener: 50000

persistence:
  enabled: true
  storageClass: "managed"
  accessModes:
    - ReadWriteOnce
  size: 8Gi

nodeSelector:
  agentpool: cicd
tolerations:
- key: "dedicated"
  operator: "Equal"
  value: "cicd"
  effect: "NoSchedule"

image:
  registry: docker.io
  repository: bitnamilegacy/jenkins
  tag: 2.516.2-debian-12-r0

resources:
  limits:
    cpu: "1"
    memory: "2Gi"
  requests:
    cpu: "500m"
    memory: "1Gi"

agent:
  enabled: true
  resources:
    limits:
      cpu: "1"
      memory: "1Gi"
    requests:
      cpu: "500m"
      memory: "512Mi"
  image:
    registry: docker.io
    repository: bitnamilegacy/jenkins-agent
    tag: 0.3327.0-debian-12-r1

tls:
  resources:
    limits:
      cpu: "250m"
      memory: "256Mi"
    requests:
      cpu: "100m"
      memory: "128Mi"

ingress:
  enabled: true
  hostname: myjenkins.io
  pathType: Prefix
  ingressClassName: webapprouting.kubernetes.azure.com
EOF
```

**[GCP GKE]** jenkins.yaml:
```bash
cat > jenkins.yaml << EOF
global:
  storageClass: "standard-rwo"

jenkinsUser: admin
jenkinsPassword: "P@ssw0rd$"
jenkinsHost: "http://myjenkins.io"
jenkinsHome: /bitnami/jenkins/home

service:
  type: ClusterIP

javaOpts:
  - -Dfile.encoding=UTF-8

containerPorts:
  http: 8080
  https: 8443
  agentListener: 50000

agentListenerService:
  enabled: true
  type: ClusterIP
  ports:
    agentListener: 50000

persistence:
  enabled: true
  storageClass: "standard-rwo"
  accessModes:
    - ReadWriteOnce
  size: 8Gi

image:
  registry: docker.io
  repository: bitnamilegacy/jenkins
  tag: 2.516.2-debian-12-r0

resources:
  limits:
    cpu: "1"
    memory: "2Gi"
  requests:
    cpu: "500m"
    memory: "1Gi"

agent:
  enabled: true
  resources:
    limits:
      cpu: "1"
      memory: "1Gi"
    requests:
      cpu: "500m"
      memory: "512Mi"
  image:
    registry: docker.io
    repository: bitnamilegacy/jenkins-agent
    tag: 0.3327.0-debian-12-r1

tls:
  resources:
    limits:
      cpu: "250m"
      memory: "256Mi"
    requests:
      cpu: "100m"
      memory: "128Mi"

ingress:
  enabled: true
  hostname: myjenkins.io
  pathType: Prefix
  annotations:
    kubernetes.io/ingress.class: "gce"
EOF
```

> GKE Autopilot: nodeSelector와 tolerations 없음. Autopilot이 resources.requests 기반으로 노드를 자동 프로비저닝함.

#### namespace 생성 및 helm install

```bash
kubectl create ns jenkins

# dry-run 먼저 실행
helm upgrade -i jenkins -f jenkins.yaml . -n jenkins --dry-run

# 실제 설치
helm upgrade -i jenkins -f jenkins.yaml . -n jenkins
```

#### Pod 실행 대기 및 확인

```bash
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=jenkins -n jenkins --timeout=300s

kubectl get po -n jenkins
```

#### RBAC 설정 (ClusterRoleBinding)

Jenkins ServiceAccount에 cluster-admin 역할을 부여하여 클러스터의 모든 객체를 관리할 수 있는 권한 부여:
```bash
cat > ~/install/jenkins/rbac.yaml << 'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: jenkins-admin
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: jenkins
  namespace: jenkins
EOF

kubectl apply -f ~/install/jenkins/rbac.yaml
```

#### [수동 안내] Jenkins 후속 설정

아래 항목은 웹 UI에서 사람이 수동으로 수행:

**플러그인 설치** (웹 UI: `http://myjenkins.io`):  
- 공통: Kubernetes, Pipeline Utility Steps, Docker Pipeline, GitHub, Blue Ocean, SonarQube Scanner
- AWS 추가(선택): Amazon ECR

**Kubernetes Cloud 연결** (웹 UI: Dashboard > Manage Jenkins > Clouds):
```
- Kubernetes URL: https://kubernetes.default
- Kubernetes Namespace: jenkins
- Jenkins URL: http://jenkins
- Jenkins tunnel: jenkins-agent-listener:50000
```

**Jenkins tunnel 포트 설정** (웹 UI: Dashboard > Manage Jenkins > Security)

**계정 및 권한관리**: 실무 사용 시 필요. https://happycloud-lee.tistory.com/48 참조.

---

### Phase 3: SonarQube 설치

#### Helm chart 다운로드

```bash
mkdir -p ~/install && cd ~/install

helm pull bitnami/sonarqube --version 8.1.17

tar xvf sonarqube-8.1.17.tgz

cd sonarqube
```

#### 클라우드별 sonarqube.yaml 생성

> **MUST**: 아래 yaml의 `sonarqubePassword` 값을 반드시 그대로 사용할 것. 임의 변경 금지.

**[AWS EKS]** sonarqube.yaml:
```bash
cat > sonarqube.yaml << EOF
sonarqubeUsername: admin
sonarqubePassword: "sonarP@ssw0rd$"

service:
  type: ClusterIP
  ports:
    http: 80
    elastic: 9001

persistence:
  enabled: true
  storageClass: "gp2-eks-auto"
  accessModes:
    - ReadWriteOnce
  size: 2Gi

nodeSelector:
  agentpool: sonarqube
tolerations:
- key: "dedicated"
  operator: "Equal"
  value: "sonarqube"
  effect: "NoSchedule"

postgresql:
  auth:
    password: "P@ssw0rd$"
    username: bn_sonarqube
  primary:
    persistence:
      storageClass: "gp2-eks-auto"

resources:
  limits:
    cpu: "4"
    memory: "5Gi"
  requests:
    cpu: "3"
    memory: "4Gi"

image:
  registry: docker.io
  repository: bitnamilegacy/sonarqube
  tag: 25.5.0-debian-12-r0

sysctl:
  image:
    registry: docker.io
    repository: bitnamilegacy/os-shell
    tag: 12-debian-12-r51

ingress:
  enabled: true
  hostname: mysonar.io
  pathType: Prefix
  ingressClassName: alb
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80}]'
    alb.ingress.kubernetes.io/group.name: cicd-tools
EOF
```

**[Azure AKS]** sonarqube.yaml:
```bash
cat > sonarqube.yaml << EOF
sonarqubeUsername: admin
sonarqubePassword: "sonarP@ssw0rd$"

service:
  type: ClusterIP
  ports:
    http: 80
    elastic: 9001

persistence:
  enabled: true
  storageClass: "managed"
  accessModes:
    - ReadWriteOnce
  size: 2Gi

nodeSelector:
  agentpool: sonarqube
tolerations:
- key: "dedicated"
  operator: "Equal"
  value: "sonarqube"
  effect: "NoSchedule"

postgresql:
  auth:
    password: "P@ssw0rd$"
    username: bn_sonarqube
  primary:
    persistence:
      storageClass: "managed"

resources:
  limits:
    cpu: "4"
    memory: "5Gi"
  requests:
    cpu: "3"
    memory: "4Gi"

image:
  registry: docker.io
  repository: bitnamilegacy/sonarqube
  tag: 25.5.0-debian-12-r0

sysctl:
  image:
    registry: docker.io
    repository: bitnamilegacy/os-shell
    tag: 12-debian-12-r51

ingress:
  enabled: true
  hostname: mysonar.io
  pathType: Prefix
  ingressClassName: webapprouting.kubernetes.azure.com
EOF
```

**[GCP GKE]** sonarqube.yaml:
```bash
cat > sonarqube.yaml << EOF
sonarqubeUsername: admin
sonarqubePassword: "sonarP@ssw0rd$"

service:
  type: ClusterIP
  ports:
    http: 80
    elastic: 9001

persistence:
  enabled: true
  storageClass: "standard-rwo"
  accessModes:
    - ReadWriteOnce
  size: 2Gi

postgresql:
  auth:
    password: "P@ssw0rd$"
    username: bn_sonarqube
  primary:
    persistence:
      storageClass: "standard-rwo"

resources:
  limits:
    cpu: "4"
    memory: "5Gi"
  requests:
    cpu: "3"
    memory: "4Gi"

image:
  registry: docker.io
  repository: bitnamilegacy/sonarqube
  tag: 25.5.0-debian-12-r0

sysctl:
  enabled: false
  image:
    registry: docker.io
    repository: bitnamilegacy/os-shell
    tag: 12-debian-12-r51

ingress:
  enabled: true
  hostname: mysonar.io
  pathType: Prefix
  annotations:
    kubernetes.io/ingress.class: "gce"
EOF
```

> GKE Autopilot: nodeSelector와 tolerations 없음. `sysctl.enabled: false`로 설정됨.  
> Autopilot은 privileged init container를 허용하지 않으므로 sysctl 초기화 컨테이너가 차단됨.

#### postgresql 이미지 변경 (sed)

```bash
# 파일 존재 확인 후 실행
ls charts/postgresql/values.yaml && \
  sed -i 's|repository: bitnami/postgresql|repository: bitnamilegacy/postgresql|' charts/postgresql/values.yaml
```

#### namespace 생성 및 helm install

```bash
kubectl create ns sonarqube

# dry-run 먼저 실행
helm upgrade -i sonar -f sonarqube.yaml . -n sonarqube --dry-run

# 실제 설치
helm upgrade -i sonar -f sonarqube.yaml . -n sonarqube
```

#### affinity 패치

sonarqube Pod에서 affinity 설정을 삭제함.  
postgresql DB와 동일 노드에 설치하는 affinity인데 DB Pod가 다른 노드에 설치되어 Pod가 배포되지 않음.

Deployment 존재 확인 후 패치 실행:
```bash
kubectl get deploy sonar-sonarqube -n sonarqube 2>/dev/null || (echo "Deployment not found, waiting 10s..." && sleep 10)

kubectl patch deploy sonar-sonarqube -n sonarqube --type=json \
  -p='[{"op": "remove", "path": "/spec/template/spec/affinity"}]'
```

affinity 패치로 새 ReplicaSet이 생성되면서 기존 ReplicaSet과 충돌할 수 있음.
깨끗한 재시작을 위해 scale 0 → 1 수행:
```bash
kubectl scale deploy sonar-sonarqube -n sonarqube --replicas=0
sleep 5
kubectl scale deploy sonar-sonarqube -n sonarqube --replicas=1
```

#### Pod 실행 대기 및 확인

```bash
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=sonarqube \
  -n sonarqube --timeout=300s

kubectl get po -n sonarqube
```

#### [GKE 전용] sysctl.enabled: false 및 vm.max_map_count 대응

GKE Autopilot에서 SonarQube Pod가 시작되지 않는 경우 아래 순서로 대응:

1. Pod 상태 확인:
```bash
kubectl get po -n sonarqube -w
```

2. 실패 시 sonarqubeProperties 추가 (Helm upgrade):
```bash
helm upgrade sonar -f sonarqube.yaml . -n sonarqube \
  --set 'sonarqubeProperties.sonar\.search\.javaAdditionalOpts=-Dnode.store.allow_mmap=false'
```

3. 위 방법으로 해결되지 않으면 GKE Standard 모드 사용 권장.

#### [수동 안내] SonarQube 후속 설정

아래 항목은 웹 UI에서 사람이 수동으로 수행:

**SonarQube 환경설정** (웹 UI: `http://mysonar.io`, admin / sonarP@ssw0rd$):
- User Token 발급: MyAccount > Security
- Jenkins 통보 Webhook 작성: `http://jenkins.jenkins.svc.cluster.local/sonarqube-webhook/`
- Quality Gate 작성: 'Sonar way' 복사 후 Code Coverage 조정
- Jenkins Credential 등록: 위에서 발급한 Token으로 등록
- SonarQube Server 설정: Jenkins System 설정에서 서버 URL 및 Token Credential 등록

**Backend 루트 build.gradle 수정** (SonarQube + JaCoCo 연동):

Backend 프로젝트의 루트 `build.gradle`에 아래 설정을 추가해야 SonarQube 코드 품질 분석이 동작함.

1) 플러그인 `sonarqube` 추가:
```gradle
plugins {
  ...
  id "org.sonarqube" version "5.0.0.4638" apply false
}
```

2) subprojects 블록에 `sonarqube`, `jacoco` 플러그인 적용:
```gradle
subprojects {
  ...

  apply plugin: 'org.sonarqube'
  apply plugin: 'jacoco'

  jacoco {
      toolVersion = "0.8.11"
  }

  ...
```

3) subprojects 블록의 test 설정 변경 (JaCoCo 리포트 자동 생성):
```gradle
subprojects {
  ...

  test {
      useJUnitPlatform()
      include '**/*Test.class'
      testLogging {
          events "passed", "skipped", "failed"
      }
      finalizedBy jacocoTestReport
  }
  jacocoTestReport {
      dependsOn test
      reports {
          xml.required = true
          csv.required = false
          html.required = true
          html.outputLocation = layout.buildDirectory.dir("jacocoHtml").get().asFile
      }

      afterEvaluate {
          classDirectories.setFrom(files(classDirectories.files.collect {
              fileTree(dir: it, exclude: [
                      "**/config/**",
                      "**/entity/**",
                      "**/dto/**",
                      "**/*Application.class",
                      "**/exception/**"
              ])
          }))
      }
  }
}
```

#### 백엔드 단위테스트 실행 및 에러 해결

build.gradle에 SonarQube/JaCoCo 설정을 추가한 후, CI 파이프라인 실행 전에 로컬에서 단위테스트를 실행하여 빌드 정상 여부를 확인.
테스트 실패 시 CI 파이프라인도 실패하므로, 이 단계에서 모든 에러를 해결해야 함.

**1) 전체 빌드 및 테스트 실행**

```bash
chmod +x gradlew
./gradlew clean build
```

> `build` 태스크에 `test`가 포함되어 있으므로 별도 `./gradlew test` 실행 불필요.
> 빌드 성공 시 각 서비스의 `build/reports/jacoco/test/jacocoTestReport.xml`에 커버리지 리포트가 생성됨.

**2) 테스트 실패 시 개별 서비스 테스트**

전체 빌드 실패 시 서비스별로 테스트를 실행하여 실패 지점을 특정:
```bash
./gradlew :{서비스명}:test --info
```

> `--info` 옵션으로 상세 로그 확인 가능. 실패한 테스트 클래스와 메서드가 출력됨.

**3) 주요 에러 유형 및 해결 방법**

| 에러 유형 | 증상 | 해결 방법 |
|----------|------|----------|
| ApplicationContext 로딩 실패 | `Failed to load ApplicationContext` | 테스트용 설정 파일(`application-test.yml`) 누락 확인. `@SpringBootTest` 사용 시 필요한 Bean이 모두 등록되었는지 확인 |
| DB 연결 실패 | `Connection refused`, `DataSource` 에러 | `src/test/resources/application.yml`에 H2 인메모리 DB 설정 추가. 또는 `@DataJpaTest` 사용 시 `@AutoConfigureTestDatabase(replace = NONE)` 확인 |
| 포트 충돌 | `Port already in use` | 테스트 설정에 `server.port=0` (랜덤 포트) 지정 |
| Lombok 관련 | `cannot find symbol` (getter/setter) | `build.gradle`에 `annotationProcessor 'org.projectlombok:lombok'` 확인 |
| JaCoCo 에러 | `Could not resolve all files for configuration ':jacocoAgent'` | `build.gradle`의 `jacoco { toolVersion }` 버전이 현재 JDK와 호환되는지 확인 |
| 외부 API 의존 | `ConnectException`, 타임아웃 | 테스트에서 외부 API를 모킹(Mocking) 처리. `@MockBean` 또는 WireMock 사용 |

**4) 테스트 환경 설정 파일 확인**

각 서비스의 `src/test/resources/application.yml` (또는 `application-test.yml`)에 테스트용 DB 설정이 있는지 확인:
```yaml
spring:
  datasource:
    url: jdbc:h2:mem:testdb
    driver-class-name: org.h2.Driver
  jpa:
    hibernate:
      ddl-auto: create-drop
```

> H2 의존성이 없으면 서비스의 `build.gradle`에 추가:
> ```gradle
> testImplementation 'com.h2database:h2'
> ```

**5) 테스트 성공 확인**

모든 테스트 통과 후 JaCoCo 리포트 생성 확인:
```bash
./gradlew clean build

# JaCoCo 리포트 확인 (각 서비스별)
ls {서비스명}/build/reports/jacoco/test/jacocoTestReport.xml
```

> BUILD SUCCESSFUL 메시지와 함께 각 서비스의 `jacocoTestReport.xml`이 존재하면 정상.
> 이 상태에서 CI 파이프라인(Jenkins/GitHub Actions)을 실행하면 SonarQube 분석까지 정상 동작함.

---

### Phase 4: ArgoCD 설치

#### Helm repo 추가 및 chart 다운로드

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

mkdir -p ~/install && cd ~/install

helm pull argo/argo-cd --version 3.35.4

tar xvf argo-cd-3.35.4.tgz

cd argo-cd
```

#### 클라우드별 argocd.yaml 생성

**[AWS EKS]** argocd.yaml:
```bash
cat > argocd.yaml << EOF
global:
  domain: myargocd.io
  nodeSelector:
    agentpool: cicd
  tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "cicd"
    effect: "NoSchedule"

server:
  ingress:
    enabled: true
    hostname: myargocd.io
    pathType: Prefix
    ingressClassName: alb
    annotations:
      alb.ingress.kubernetes.io/scheme: internet-facing
      alb.ingress.kubernetes.io/target-type: ip
      alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80}]'
      alb.ingress.kubernetes.io/group.name: cicd-tools
  extraArgs:
    - --insecure

configs:
  params:
    server.insecure: true
certificate:
  enabled: false
EOF
```

**[Azure AKS]** argocd.yaml:
```bash
cat > argocd.yaml << EOF
global:
  domain: myargocd.io
  nodeSelector:
    agentpool: cicd
  tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "cicd"
    effect: "NoSchedule"

server:
  ingress:
    enabled: true
    hostname: myargocd.io
    pathType: Prefix
    ingressClassName: webapprouting.kubernetes.azure.com
  extraArgs:
    - --insecure

configs:
  params:
    server.insecure: true
certificate:
  enabled: false
EOF
```

**[GCP GKE]** argocd.yaml:
```bash
cat > argocd.yaml << EOF
global:
  domain: myargocd.io
  # nodeSelector, tolerations 없음 (Autopilot)

server:
  ingress:
    enabled: true
    hostname: myargocd.io
    pathType: Prefix
    annotations:
      kubernetes.io/ingress.class: "gce"
  extraArgs:
    - --insecure

configs:
  params:
    server.insecure: true
certificate:
  enabled: false
EOF
```

#### namespace 생성 및 helm install

```bash
kubectl create ns argocd

# dry-run 먼저 실행
helm upgrade -i argocd -f argocd.yaml . -n argocd --dry-run

# 실제 설치
helm upgrade -i argocd -f argocd.yaml . -n argocd
```

#### --insecure 플래그 적용 검증

Helm values의 `server.insecure: true`가 실제 적용되지 않는 경우가 있음.
Pod 기동 후 리다이렉트(307) 여부로 검증하고, 미적용 시 command에 직접 추가:
```bash
# argocd-server Pod IP 확인
ARGOCD_POD=$(kubectl get po -n argocd -l app.kubernetes.io/name=argocd-server -o jsonpath='{.items[0].metadata.name}')

# insecure 모드 검증 (port-forward로 확인)
kubectl port-forward -n argocd ${ARGOCD_POD} 18080:8080 &
PF_PID=$!
sleep 3
HTTP_CODE=$(curl -sk -o /dev/null -w '%{http_code}' http://localhost:18080/)
kill ${PF_PID} 2>/dev/null

if [ "${HTTP_CODE}" = "307" ]; then
  echo "insecure 모드 미적용 — command에 --insecure 플래그 직접 추가"
  kubectl patch deploy argocd-server -n argocd --type=json \
    -p='[{"op":"add","path":"/spec/template/spec/containers/0/command/-","value":"--insecure"}]'
  kubectl rollout status deploy argocd-server -n argocd --timeout=120s
else
  echo "insecure 모드 정상 적용 (HTTP ${HTTP_CODE})"
fi
```

#### Pod 실행 대기 및 확인

```bash
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=argocd-server \
  -n argocd --timeout=300s

kubectl get po -n argocd
```

#### 초기 관리자 비밀번호 조회

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo
```

#### [GKE 전용] Health Check BackendConfig

GCE Ingress는 기본적으로 `/` 경로로 HTTP health check를 수행함.  
ArgoCD가 정상 응답하지 않아 backend가 UNHEALTHY로 표시되면  
BackendConfig를 통해 health check 경로를 `/healthz`로 조정:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: cloud.google.com/v1
kind: BackendConfig
metadata:
  name: argocd-backend-config
  namespace: argocd
spec:
  healthCheck:
    requestPath: /healthz
EOF
```

#### [수동 안내] ArgoCD 후속 설정

아래 항목은 웹 UI에서 사람이 수동으로 수행:

**ArgoCD 초기 접속** (웹 UI: `http://myargocd.io`):  
- ID: admin, 초기 암호: 위 비밀번호 조회 결과
- User Info에서 비밀번호 변경 권장

---

### Nginx 프록시 설정 (SSH 자동)

> 모든 도구 설치 완료 후, Web Server VM에 SSH 접속하여 Nginx 프록시를 일괄 설정.  
> `[실행정보]`의 `VM_HOST`를 사용하여 SSH 접속.

#### Ingress Address 수집

설치된 도구별 Ingress Address를 수집:

**[AWS EKS]**:
```bash
JENKINS_ADDRESS=$(kubectl get ing -n jenkins -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
SONAR_ADDRESS=$(kubectl get ing -n sonarqube -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
ARGOCD_ADDRESS=$(kubectl get ing -n argocd -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
```

**[Azure AKS]**:
```bash
INGRESS_IP=$(kubectl get svc -n app-routing-system nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
JENKINS_ADDRESS=${INGRESS_IP}
SONAR_ADDRESS=${INGRESS_IP}
ARGOCD_ADDRESS=${INGRESS_IP}
```

**[GCP GKE]**:
```bash
JENKINS_ADDRESS=$(kubectl get ing -n jenkins -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null)
SONAR_ADDRESS=$(kubectl get ing -n sonarqube -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null)
ARGOCD_ADDRESS=$(kubectl get ing -n argocd -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null)
```

> CI_TOOL == GitHubActions인 경우 `JENKINS_ADDRESS`는 빈 값.

#### dummy 인증서 생성 (최초 1회)

```bash
ssh ${VM_HOST} 'sudo mkdir -p /etc/nginx/ssl && \
  [ ! -f /etc/nginx/ssl/dummy.crt ] && \
  sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/dummy.key -out /etc/nginx/ssl/dummy.crt \
    -subj "/CN=localhost" || echo "dummy cert already exists"'
```

#### Nginx 프록시 설정 파일 생성

CI_TOOL에 따라 Jenkins 블록 포함 여부가 결정됨.

**CI_TOOL == Jenkins인 경우** (3개 도구 모두 포함):
```bash
ssh ${VM_HOST} "cat << 'NGINXEOF' | sudo tee /etc/nginx/sites-available/cicd
server {
    listen 80 default_server;
    server_name myjenkins.io;
    location / {
        proxy_pass http://${JENKINS_ADDRESS};
        proxy_set_header Host myjenkins.io;
        proxy_set_header X-Real-IP \\\$remote_addr;
    }
}

server {
    listen 80;
    server_name mysonar.io;
    location / {
        proxy_pass http://${SONAR_ADDRESS};
        proxy_set_header Host mysonar.io;
        proxy_set_header X-Real-IP \\\$remote_addr;
    }
}

server {
    listen 80;
    server_name myargocd.io;
    location / {
        proxy_pass http://${ARGOCD_ADDRESS};
        proxy_set_header Host myargocd.io;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}

# HTTPS 요청을 HTTP로 리다이렉트
server {
    listen 443 ssl default_server;
    server_name _;
    ssl_certificate /etc/nginx/ssl/dummy.crt;
    ssl_certificate_key /etc/nginx/ssl/dummy.key;
    return 301 http://\\\$host\\\$request_uri;
}
NGINXEOF"
```

**CI_TOOL == GitHubActions인 경우** (Jenkins 제외, 2개 도구만):
```bash
ssh ${VM_HOST} "cat << 'NGINXEOF' | sudo tee /etc/nginx/sites-available/cicd
server {
    listen 80 default_server;
    server_name mysonar.io;
    location / {
        proxy_pass http://${SONAR_ADDRESS};
        proxy_set_header Host mysonar.io;
        proxy_set_header X-Real-IP \\\$remote_addr;
    }
}

server {
    listen 80;
    server_name myargocd.io;
    location / {
        proxy_pass http://${ARGOCD_ADDRESS};
        proxy_set_header Host myargocd.io;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}

# HTTPS 요청을 HTTP로 리다이렉트
server {
    listen 443 ssl default_server;
    server_name _;
    ssl_certificate /etc/nginx/ssl/dummy.crt;
    ssl_certificate_key /etc/nginx/ssl/dummy.key;
    return 301 http://\\\$host\\\$request_uri;
}
NGINXEOF"
```

#### symlink 생성 및 Nginx 재시작

```bash
ssh ${VM_HOST} 'sudo ln -sf /etc/nginx/sites-available/cicd /etc/nginx/sites-enabled/cicd && \
  sudo nginx -t && sudo systemctl reload nginx'
```

> `nginx -t` 실패 시: 기존 설정에 resolve 불가능한 주소가 남아있을 수 있음.  
> `/etc/nginx/sites-available/` 하위 파일을 확인하여 삭제된 서비스의 server 블록 제거 필요.

#### Nginx 설정 검증

```bash
ssh ${VM_HOST} 'sudo nginx -t'
```

#### 프록시 연결 검증

각 도구의 프록시가 정상 동작하는지 curl로 확인.
HTTP 응답 코드가 200 또는 3xx이면 정상:

```bash
# Jenkins (CI_TOOL == Jenkins인 경우)
ssh ${VM_HOST} "curl -s -o /dev/null -w '%{http_code}' -H 'Host: myjenkins.io' http://localhost/"

# SonarQube
ssh ${VM_HOST} "curl -s -o /dev/null -w '%{http_code}' -H 'Host: mysonar.io' http://localhost/"

# ArgoCD
ssh ${VM_HOST} "curl -s -o /dev/null -w '%{http_code}' -H 'Host: myargocd.io' http://localhost/"
```

> 응답 코드 `000` 또는 `502`인 경우: Ingress Address가 아직 할당되지 않았거나 Pod가 Ready 상태가 아닐 수 있음.
> `kubectl get ing -n {네임스페이스}`로 Address 할당 확인 후 재시도.

---

### Phase 5: 수동 후속 작업 안내

> 아래 항목은 AI 에이전트가 자동화할 수 없으므로 사람이 직접 수행.

**hosts 파일 등록** (로컬 PC):

Web Server VM의 Public IP를 확인하고 로컬 PC의 hosts 파일에 등록:
```
{WEB_SERVER_PUBLIC_IP}  myjenkins.io mysonar.io myargocd.io
```

Windows hosts 파일 경로: `c:\windows\system32\drivers\etc\hosts` (관리자 권한으로 실행)

**Image Registry Credential 등록** (Jenkins 웹 UI):

| CLOUD | 등록 방법 |
|-------|---------|
| AWS EKS | `aws ecr get-login-password --region ap-northeast-2` 결과를 Username=AWS로 등록 |
| Azure AKS | `az acr credential show -n {acr명}` 결과를 Username/Password로 등록 |
| GCP GKE | Artifact Registry SA JSON Key를 Username=_json_key로 등록 |

Credential 이름: `imagereg-credentials` (Kind: Username with password)

**DockerHub Credentials 등록** (Jenkins 웹 UI):  
- DockerHub(https://hub.docker.com)에서 Personal Access Token 생성
- Credential 이름: `dockerhub-credentials` (Kind: Username with password)

**GitHub Actions Secrets/Variables 설정** (CI_TOOL == GitHubActions인 경우):

Repository Settings > Secrets and variables > Actions에서 등록.

Repository Secrets (인증정보):

| CLOUD | Secret 이름 | 값 |
|-------|-----------|-----|
| AWS | `AWS_ACCESS_KEY_ID` | AWS 액세스 키 ID |
| AWS | `AWS_SECRET_ACCESS_KEY` | AWS 시크릿 액세스 키 |
| Azure | `AZURE_CREDENTIALS` | Service Principal JSON |
| Azure | `ACR_USERNAME` | ACR 관리자 사용자명 |
| Azure | `ACR_PASSWORD` | ACR 관리자 패스워드 |
| GCP | `GCP_SA_KEY` | GCP 서비스 계정 키 JSON |

공통 Secrets:

| Secret 이름 | 값 | 용도 |
|-----------|-----|------|
| `SONAR_TOKEN` | SonarQube 사용자 토큰 | 코드 품질 분석 |
| `SONAR_HOST_URL` | SonarQube 서버 URL | 코드 품질 분석 |
| `DOCKERHUB_USERNAME` | Docker Hub 사용자명 | Rate Limit 해결 |
| `DOCKERHUB_PASSWORD` | Docker Hub Personal Access Token | Rate Limit 해결 |
| `GIT_USERNAME` | 매니페스트 레포지토리 접근용 GitHub 사용자명 | ArgoCD GitOps |
| `GIT_PASSWORD` | 매니페스트 레포지토리 접근용 GitHub Token | ArgoCD GitOps |

Repository Variables (워크플로우 제어):

| Variable 이름 | 값 예시 | 설명 |
|-------------|--------|------|
| `CLOUD` | `Azure` | 클라우드 서비스 (AWS/Azure/GCP) |
| `REGISTRY` | `acrdigitalgarage01.azurecr.io` | 컨테이너 이미지 레지스트리 주소 |
| `IMAGE_ORG` | `phonebill` | 이미지 조직명 |
| `ENVIRONMENT` | `dev` | 기본 배포 환경 (dev/staging/prod) |
| `SKIP_SONARQUBE` | `false` | SonarQube 분석 스킵 여부 |

---

### 결과 보고서 작성

설치 완료 후 `docs/cicd/cicd-pre-setup-report.md`에 아래 템플릿으로 작성:

```markdown
# CI/CD 도구 사전 설정 결과 보고서

## 1. 설치 환경

| 항목 | 값 |
|------|-----|
| CLOUD | {CLOUD} |
| CI_TOOL | {CI_TOOL} |
| K8S_CLUSTER | {클러스터명} |
| VM_HOST | {VM_HOST} ({Public IP}) |
| 레지스트리 | {레지스트리유형} ({IMG_REG}/{IMG_ORG}) |

## 2. 도구 설치 결과

| 도구 | 네임스페이스 | 상태 | Ingress Address |
|------|-----------|------|----------------|
| Jenkins | jenkins | 완료/건너뜀 | {address} |
| SonarQube | sonarqube | 완료/건너뜀 | {address} |
| ArgoCD | argocd | 완료/건너뜀 | {address} |

## 3. 접속 정보

| 도구 | URL | ID | 암호 |
|------|-----|----|----|
| Jenkins | http://myjenkins.io | admin | {secret 조회값} |
| SonarQube | http://mysonar.io | admin | {secret 조회값} |
| ArgoCD | http://myargocd.io | admin | {secret 조회값} |

> 암호 조회 명령:
> - Jenkins: `kubectl get secret jenkins -n jenkins -o jsonpath='{.data.jenkins-password}' | base64 -d`
> - SonarQube: `kubectl get secret sonar-sonarqube -n sonarqube -o jsonpath='{.data.sonarqube-password}' | base64 -d`
> - ArgoCD: `kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath='{.data.password}' | base64 -d`

## 4. Nginx 프록시

| 항목 | 결과 |
|------|------|
| 설정 파일 | `/etc/nginx/sites-available/cicd` |
| nginx -t | {syntax ok / 실패 메시지} |
| curl myjenkins.io | {HTTP 응답코드} |
| curl mysonar.io | {HTTP 응답코드} |
| curl myargocd.io | {HTTP 응답코드} |
```

---

## 에러 핸들링

| 실패 시나리오 | 처리 방안 |
|-------------|----------|
| Helm install 실패 | `helm uninstall {릴리즈명} -n {ns}` 후 재시도. 2회 실패 시 사용자에게 보고 |
| Pod 미기동 | `kubectl wait --timeout=300s` 타임아웃 시 `kubectl describe pod -n {ns}` |
| SonarQube affinity 패치 실패 | Deployment 존재 확인 후 10초 대기 재시도 |
| 리소스 부족 | NodePool 생성 후 최대 5분 대기 |
| 이미 설치된 도구 감지 | `kubectl get ns` + `helm list`로 확인. 존재 시 건너뜀 |
| AWS CLI 실패 | `aws sts get-caller-identity` 사전 검증 |
| sed 대상 파일 미존재 | `ls charts/postgresql/values.yaml` 확인 후 건너뜀 |

## 품질 기준

- [ ] 클라우드별 사전작업 완료 (AWS: StorageClass, ALB, NodePool / Azure: NodePool / GCP: 없음)
- [ ] Jenkins 설치 완료 및 Pod Ready 상태 확인 (CI_TOOL=Jenkins인 경우)
- [ ] SonarQube 설치 완료 및 Pod Ready 상태 확인
- [ ] ArgoCD 설치 완료 및 Pod Ready 상태 확인
- [ ] 각 도구 RBAC 설정 완료 (Jenkins ClusterRoleBinding)
- [ ] Nginx 프록시 설정 완료 (SSH 자동, `nginx -t` 성공)
- [ ] docs/cicd/cicd-pre-setup-report.md 작성 완료
- [ ] 수동 후속 작업 목록 사용자에게 안내
