# CI/CD 툴 설치 가이드

## 목차

- [CI/CD 툴 설치 가이드](#cicd-툴-설치-가이드)
  - [목차](#목차)
  - [클라우드별 차이 요약](#클라우드별-차이-요약)
  - [사전작업](#사전작업)
    - [\[AWS EKS\] 사전작업](#aws-eks-사전작업)
    - [\[Azure AKS\] 사전작업](#azure-aks-사전작업)
    - [\[GCP GKE\] 사전작업](#gcp-gke-사전작업)
  - [hosts 파일 등록](#hosts-파일-등록)
  - [Jenkins설치](#jenkins설치)
  - [SonarQube 설치](#sonarqube-설치)
  - [ArgoCD 설치](#argocd-설치)
    - [Ingress 설정 확인](#ingress-설정-확인)
  - [Image Registry Credential 설정](#image-registry-credential-설정)
    - [\[AWS EKS\] ECR Credential 생성](#aws-eks-ecr-credential-생성)
    - [\[Azure AKS\] ACR Credential 생성](#azure-aks-acr-credential-생성)
    - [\[GCP GKE\] Artifact Registry Credential 생성](#gcp-gke-artifact-registry-credential-생성)
  - [DockerHub Credentials 생성](#dockerhub-credentials-생성)
  - [GitHub Actions Repository Secrets/Variables 설정](#github-actions-repository-secretsvariables-설정)
    - [Repository Secrets (인증정보)](#repository-secrets-인증정보)
    - [Repository Variables (워크플로우 제어)](#repository-variables-워크플로우-제어)


| [Top](#목차) |

---

> **전제 조건**: 이 가이드는 **EKS Auto Mode / AKS Automatic / GKE Autopilot** 클러스터가
> `create-k8s.md`에 따라 이미 생성되어 있는 상태를 전제로 합니다.
> 사용하는 CLOUD에 해당하는 부분만 수행합니다.

## 클라우드별 차이 요약

| 항목 | AWS EKS | Azure AKS | GCP GKE |
|------|---------|-----------|---------|
| NodePool 생성 | Karpenter CRD | Karpenter CRD | 불필요 (Autopilot) |
| StorageClass (일반) | gp2 | managed | standard-rwo |
| Container Registry | ECR | ACR | Artifact Registry |
| Ingress Controller | ALB (`alb`) | app-routing (`webapprouting`) | GCE (`gce` annotation) |
| Registry Credential | ECR 관리자 계정 | ACR 관리자 계정 | Artifact Registry SA |
| 노드 격리 | taint (dedicated=cicd) | taint (dedicated=cicd) | 불가 (네임스페이스 분리) |

Window사용자는 Window Terminal의 GitBash 터미널에서 작업하고,
Mac사용자는 맥 기본 터미널에서 작업합니다.

## 사전작업

### [AWS EKS] 사전작업

EKS Auto Mode 전용 StorageClass를 생성합니다.
기본 제공되는 `gp2` StorageClass는 in-tree provisioner(`kubernetes.io/aws-ebs`)를 사용하여 EKS Auto Mode에서 지원되지 않습니다.

```
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

ALB(Application Load Balancer) 설정을 합니다.
`create-k8s.md`의 'ALB 설정' 섹션을 이미 수행했다면 이 단계는 건너뜁니다.

Subnet에 `kubernetes.io/role/elb` 태그를 등록합니다. ALB가 어떤 Subnet에 생성될지 지정하는 태그입니다.
```
export EKS_NAME={EKS 클러스터 이름}

aws ec2 describe-subnets \
  --subnet-ids $(aws eks describe-cluster --name ${EKS_NAME} \
  --query "cluster.resourcesVpcConfig.subnetIds" --output text) \
  --query "Subnets[*].{ID:SubnetId,AZ:AvailabilityZone,Public:MapPublicIpOnLaunch}" \
  --output table
```

위 결과의 모든 Subnet ID를 아래 명령에 넣어 태그를 추가합니다.
```
aws ec2 create-tags \
  --resources {subnet-1} {subnet-2} {subnet-3} {subnet-4} \
  --tags Key=kubernetes.io/role/elb,Value=1
```

IngressClass 객체를 생성합니다.
```
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
```
kubectl get ingressclass
```

Karpenter NodePool CRD로 **cicd** 노드풀을 생성합니다.

```
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

동일 패턴으로 **sonarqube** 노드풀을 생성합니다. (instance-size를 "xlarge", "2xlarge"로 변경하여 4core/16GB 이상 확보)

```
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

NodePool 생성을 확인합니다. (Node는 Pod 배포 시 자동 생성됩니다.)
```
kubectl get nodepool
```

| [Top](#목차) |


### [Azure AKS] 사전작업

Karpenter NodePool CRD로 **cicd** 노드풀을 생성합니다.

```
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

동일 패턴으로 **sonarqube** 노드풀을 생성합니다.

```
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

NodePool 생성을 확인합니다. (Node는 Pod 배포 시 자동 생성됩니다.)
```
kubectl get nodepool
```

| [Top](#목차) |


### [GCP GKE] 사전작업

GKE Autopilot은 커스텀 노드풀을 직접 생성할 수 없습니다.
Pod를 배포하면 Google이 리소스 요청에 맞는 노드를 자동으로 프로비저닝합니다.
따라서 별도의 NodePool 생성이나 Taint 설정이 필요없습니다.

> **제약사항**: CI/CD Pod(Jenkins, ArgoCD)와 사용자 서비스 Pod가 동일 노드에 공존할 수 있습니다.
> nodeSelector/toleration을 사용한 노드 격리가 불가능합니다.
>
> **완화 조치**:
> - `resources.requests`를 충분히 설정하여 CI/CD Pod가 독립적인 노드에 프로비저닝되도록 유도
> - 네임스페이스 분리로 논리적 격리 유지 (jenkins, sonarqube, argocd 각각 별도 네임스페이스)
> - 아래 Jenkins/SonarQube/ArgoCD 설치 시 **nodeSelector와 tolerations를 생략**합니다.

| [Top](#목차) |

---

## hosts 파일 등록

AWS ALB는 IP가 수시로 변경되므로 hosts 파일에 직접 IP를 등록하면 접속이 끊길 수 있습니다.
Nginx Web Server VM을 Reverse Proxy로 사용하면 DNS를 자동으로 resolve하므로 이 문제가 해결됩니다.

```
브라우저 → myjenkins.io (VM Public IP) → Nginx VM → Ingress Controller (ALB FQDN / IP)
```

> **전제 조건**: `~/.ssh/config`에 Web Server VM의 SSH 접속 정보가 등록되어 있어야 합니다.
> `create-k8s.md`의 Nginx Web Server 생성 섹션을 참조하세요.

Web Server VM의 Public IP를 확인하고 로컬 PC의 hosts 파일에 등록합니다.
이후 변경할 필요 없습니다.
```
{WEB_SERVER_PUBLIC_IP}	myjenkins.io mysonar.io myargocd.io
```

> **hosts파일 편집** (Windows)
> 'Window키 + d'를 눌러 바탕화면으로 이동합니다.
> 아래와 같이 바로가기를 만듭니다. 이름은 'hosts'로 합니다.
> ```
> notepad "c:\windows\system32\drivers\etc\hosts"
> ```
> 우측마우스 버튼 메뉴에서 '관리자 권한으로 실행하기'를 선택하여 엽니다.

> **주의**: Nginx는 시작/reload 시 `proxy_pass`에 지정된 모든 hostname을 DNS resolve합니다.
> 삭제된 ALB 등 더 이상 존재하지 않는 주소가 설정에 남아있으면 resolve 실패로 **전체 Nginx 설정이 거부**됩니다.
> 사용하지 않는 서비스의 server 블록은 반드시 삭제하세요.
> 수정 대상 파일은 `/etc/nginx/sites-available/` 디렉토리 하위의 설정 파일입니다.
>
> **설정 확인 방법**:
> ```
> ssh {WEB_SERVER_SSH_HOST}
> sudo nginx -t                # 기존 Nginx 설정이 유효한지 검증
> ```
> `nginx -t` 결과가 실패하면 기존 설정에 문제가 있는 것이므로, 서비스를 추가하기 전에 먼저 해결해야 합니다.

| [Top](#목차) |

---

## Jenkins설치

**1.Helm registry추가**
```
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

**2.Jenkins Helm chart 다운로드**
```
mkdir -p ~/install && cd ~/install

helm search repo jenkins

helm pull bitnami/jenkins --version 13.6.17

tar xvf jenkins-13.6.17.tgz

cd jenkins
```

**3.설치 매니페스트 작성**
설치를 위한 manifest 파일을 만듭니다. 사용하는 CLOUD에 해당하는 jenkins.yaml을 작성합니다.

**[AWS EKS]** jenkins.yaml:
```
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

> **AWS ALB 비용 참고**: Jenkins, SonarQube, ArgoCD 각각 Ingress를 생성하면 ALB가 3개 만들어집니다.
> `group.name`을 동일하게 지정하면 하나의 ALB를 공유하여 비용을 절감할 수 있습니다.

**[Azure AKS]** jenkins.yaml:
```
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
  ingressClassName: webapprouting.kubernetes.azure.com
EOF
```

**[GCP GKE]** jenkins.yaml:
```
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
  annotations:
    kubernetes.io/ingress.class: "gce"
EOF
```

> **GKE Autopilot**: nodeSelector와 tolerations가 없습니다. Autopilot이 resources.requests 기반으로 노드를 자동 프로비저닝합니다.


**4.설치**
```
kubectl create ns jenkins

kubens jenkins

helm upgrade -i jenkins -f jenkins.yaml . --dry-run

helm upgrade -i jenkins -f jenkins.yaml .
```

Pod가 정상 실행될때까지 기다립니다.
```
k get po -w
```

**5.Nginx 프록시 설정**

Ingress Address를 확인하여 Web Server VM의 Nginx 설정에 반영합니다.

**[AWS EKS]**: Ingress의 ALB FQDN 확인
```
kubectl get ing -n jenkins
```
ADDRESS 컬럼의 ALB FQDN(예: `k8s-jenkins-xxx.ap-northeast-2.elb.amazonaws.com`)을 복사합니다.

**[Azure AKS]**: app-routing Ingress Controller의 IP 확인
```
kubectl get svc -n app-routing-system nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

**[GCP GKE]**: Ingress ADDRESS 확인 (약 3~5분 소요)
```
kubectl get ing -n jenkins
```

Web Server VM에 SSH 접속하여 Nginx 프록시 설정을 추가합니다.
위에서 확인한 Ingress Address를 환경변수로 설정합니다.
```
export WEB_SERVER_SSH_HOST={Web Server SSH Host}
```

접근:
```
ssh ${WEB_SERVER_SSH_HOST}
```

위에서 확인한 Ingress Address를 환경변수로 설정합니다.
```
export JENKINS_ADDRESS={Ingress Address}
```

dummy 인증서 생성 (HTTPS catch-all용, 최초 1회):
```
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/dummy.key -out /etc/nginx/ssl/dummy.crt \
  -subj '/CN=localhost'
```

프록시 설정 (`/etc/nginx/sites-available/cicd` 파일 생성):
```
cat << EOF | sudo tee /etc/nginx/sites-available/cicd
server {
    listen 80 default_server;
    server_name myjenkins.io;
    location / {
        proxy_pass http://${JENKINS_ADDRESS};
        proxy_set_header Host myjenkins.io;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}

# HTTPS 요청을 HTTP로 리다이렉트 (기존 사이트의 443 설정이 있을 경우 필요)
server {
    listen 443 ssl default_server;
    server_name _;
    ssl_certificate /etc/nginx/ssl/dummy.crt;
    ssl_certificate_key /etc/nginx/ssl/dummy.key;
    return 301 http://\$host\$request_uri;
}
EOF

sudo ln -sf /etc/nginx/sites-available/cicd /etc/nginx/sites-enabled/cicd
```

nginx 재시작:
```
sudo nginx -t && sudo systemctl reload nginx
```
  
브라우저에서 `http://myjenkins.io`로 접근합니다.

**6.플러그인 설치**
http://myjenkins.io를 브라우저에서 엽니다.
'admin'에 'P@ssw0rd$'로 로그인합니다.

'설정'아이콘 클릭 후 Plugins 메뉴를 클릭합니다.
![](images/2026-03-04-00-11-27.png)

**공통 플러그인** (모든 클라우드):
```
- Kubernetes
- Pipeline Utility Steps
- Docker Pipeline
- GitHub
- Blue Ocean
- SonarQube Scanner
```

**클라우드별 추가 플러그인** (선택):

| 클라우드 | 추가 플러그인 | 비고 |
|---------|-------------|------|
| AWS EKS | Amazon ECR | ECR 토큰 자동 갱신에 유용 (선택, 설치 후 동작 검증 필요) |

> **참고**: CI에서 CD를 ArgoCD가 처리하므로 k8s 접근용 플러그인(Azure Credentials, Pipeline: AWS Steps, Google OAuth Credentials)은 불필요합니다.
> ECR 토큰 자동 갱신이 필요 없다면 클라우드별 추가 플러그인 없이 공통 플러그인만으로 충분합니다.

검색바에 위 플러그인을 검색하여 추가한 후 한꺼번에 설치 합니다.
![](images/2026-03-04-00-01-33.png)


설치가 끝나면 자동으로 재시작합니다.
설치가 모두 끝났는대도 자동으로 재시작을 안하면 3~4분 정도 기다렸다가 전체화면을 리프레시 합니다.
![](images/2026-03-04-00-01-47.png)

**7.Kubernetes 연결 설정**
Jenkins설치 시 생성된 Service Account 'jenkins'에 cluster-admin 역할을 부여하여
클러스터의 모든 객체를 관리할 수 있는 권한을 부여합니다.
```
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

'Dashboard > Manage Jenkins'메뉴에서 'Clouds'를 선택하고, 새로운 Cloud 프로파일을 작성합니다.
아래 항목의 값만 입력합니다.
```
- Kubernetes URL: https://kubernetes.default
- Kubernetes Namespace: jenkins
- Jenkins URL: http://jenkins
- Jenkins tunnel: jenkins-agent-listener:50000
```

System Configurations > Clouds 선택
![](images/2026-03-04-00-02-38.png)

Cloud name은 아무거나 입력. k8s cloud 이름과 동일하게 하는것이 관리상 좋음  
![](images/2026-03-04-16-36-49.png)

Kubernetes URL과 Kubernetes Namespace를 그림과 같이 입력
![](images/2026-03-04-00-03-27.png)

Jenkins URL과 Jenkins tunnel을 그림과 같이 입력
![](images/2026-03-04-00-03-43.png)

하단 우측에 있는 '[Test Connection]'버튼을 클릭하여 연결되는 지 확인합니다.

Jenkins URL과 Jenkins tunnel을 정확히 지정합니다.
참고로 Jenkins URL과 Jenkins tunnel은 Service 오브젝트의 주소입니다.
```
k get svc
NAME                     TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)          AGE
jenkins                  ClusterIP   10.0.120.3    <none>        80/TCP,443/TCP   15m
jenkins-agent-listener   ClusterIP   10.0.61.235   <none>        50000/TCP        15m
```
프로파일을 저장합니다.

**8.Jenkins tunnel 포트 설정**
'Dashboard > Manage Jenkins'메뉴에서 'Security'를 선택합니다.
![](images/2026-03-04-00-03-55.png)


**9.계정 및 권한관리**
학습 목적으로 Jenkins를 사용한다면 admin user만 있으면 되므로 이 작업은 필요 없습니다.
하지만 실무에 사용하려면 계정과 권한관리는 반드시 하셔야 합니다.
아래 링크를 참조하세요.
https://happycloud-lee.tistory.com/48


| [Top](#목차) |

---

## SonarQube 설치

**1.Helm chart 다운로드**
```
mkdir -p ~/install && cd ~/install
```

```
helm search repo sonarqube
NAME                    CHART VERSION   APP VERSION     DESCRIPTION
bitnami/sonarqube       8.1.17           25.2.0
```

```
helm pull bitnami/sonarqube --version 8.1.17
```

```
tar xvf sonarqube-8.1.17.tgz

cd sonarqube
```

**2.설치 manifest 파일 작성**

사용하는 CLOUD에 맞는 sonarqube.yaml을 작성합니다.

**[AWS EKS]** sonarqube.yaml:
```
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
```
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
  ingressClassName: webapprouting.kubernetes.azure.com
EOF
```

**[GCP GKE]** sonarqube.yaml:
```
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
  annotations:
    kubernetes.io/ingress.class: "gce"
EOF
```

> **GKE Autopilot 주의사항**: nodeSelector와 tolerations가 없습니다. Autopilot이 resources.requests 기반으로 노드를 자동 프로비저닝합니다.
> `sysctl.enabled: false`로 설정되어 있습니다. GKE Autopilot은 privileged init container를 허용하지 않으므로 sysctl 초기화 컨테이너가 차단됩니다.
> `vm.max_map_count` 기본값(65530)이 SonarQube/Elasticsearch 요구사항(262144)보다 낮아
> 부팅 실패가 발생할 수 있습니다.
>
> **해결 방법** (우선순위 순):
> 1. SonarQube Pod가 정상 시작되는지 확인 (`kubectl get po -n sonarqube -w`). GKE 노드 이미지에 따라 기본값이 충분할 수 있음
> 2. 실패 시: SonarQube Helm values에 `sonarqubeProperties."sonar.search.javaAdditionalOpts": "-Dnode.store.allow_mmap=false"` 추가
> 3. 위 방법으로 해결되지 않으면 **GKE Standard 모드 사용**을 권장합니다


charts/postgresql/values.yaml의 이미지 repository와 tag를 변경합니다.
```
sed -i 's|repository: bitnami/postgresql|repository: bitnamilegacy/postgresql|' charts/postgresql/values.yaml
```

**3.설치하기**
namespace 생성 후 이동
```
k create ns sonarqube
kubens sonarqube
```

설치하기
```
helm upgrade -i sonar -f sonarqube.yaml .
```

sonarqube Pod에서 affinity설정을 삭제합니다.
postgresql DB와 동일 노드에 설치하는 affinity인데 DB Pod가 다른 노드에 설치되기 때문에 Pod가 배포 안되기 때문입니다.
```
kubectl patch deploy sonar-sonarqube --type=json -p='[{"op": "remove", "path": "/spec/template/spec/affinity"}]'
```

Pod 실행까지 기다립니다. 약 3~4분 걸립니다.
```
kubectl get po -w
```

**4.접속하기**

Ingress Address를 확인합니다.

**[AWS EKS]**:
```
kubectl get ing -n sonarqube
```

**[Azure AKS]**: Jenkins와 동일한 Ingress Controller IP를 사용합니다.

**[GCP GKE]**:
```
kubectl get ing -n sonarqube
```

Web Server VM에 SSH 접속하여 Nginx 프록시 설정을 추가합니다.

Web Server 접속:
```
ssh ${WEB_SERVER_SSH_HOST}
```

위에서 확인한 Ingress Address를 환경변수로 설정합니다.
```
export JENKINS_ADDRESS={Jenkins Ingress Address}
export SONAR_ADDRESS={SonarQube Ingress Address}
```

Config 수정:
```
cat << EOF | sudo tee /etc/nginx/sites-available/cicd
server {
    listen 80 default_server;
    server_name myjenkins.io;
    location / {
        proxy_pass http://${JENKINS_ADDRESS};
        proxy_set_header Host myjenkins.io;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}

server {
    listen 80;
    server_name mysonar.io;
    location / {
        proxy_pass http://${SONAR_ADDRESS};
        proxy_set_header Host mysonar.io;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}

# HTTPS 요청을 HTTP로 리다이렉트
server {
    listen 443 ssl default_server;
    server_name _;
    ssl_certificate /etc/nginx/ssl/dummy.crt;
    ssl_certificate_key /etc/nginx/ssl/dummy.key;
    return 301 http://\$host\$request_uri;
}
EOF
```

Nginx 재시작:
```
sudo nginx -t && sudo systemctl reload nginx
```

브라우저에서 `http://mysonar.io`로 접근합니다.   
지정한 ID(admin)와 초기 암호(sonarP@ssword$)로 로그인 하세요.   

**5.환경설정**
1)User Token 발급
MyAccount > Security에서 User Token발급
![](images/2026-03-04-17-12-51.png)
![](images/2026-03-04-17-13-03.png)


생성된 토큰값을 클립보드에 복사합니다.

2)Jenkins 통보 Webhook 작성
SonarQube 품질 검사 결과를 Jenkins로 보내기 위해 Webhook을 만듭니다.
![](images/2026-03-04-17-14-16.png)

- name: 적절히 지정. 예) jenkins-webhook.
- url: Jenkins 서버의 주소
  Jenkins를 k8s에 설치한 경우 http://jenkins.jenkins.svc.cluster.local/sonarqube-webhook/ 으로 하고,
  그냥 설치한 경우는 http://{IP 또는 host}/sonarqube-webhook/ 으로 함   
  (주의) 맨 마지막에 '/'를 반드시 입력해야 함

  ![](images/2026-03-04-17-14-54.png)


3)Quality Gate 작성
SonarQube의 Quality Gate 복사하여 Custom 만들고 New code의 code coverage를 조정함.
![](images/2026-03-04-17-15-44.png)

'Sonar way'선택 후 우측 상단에서 '[Copy]'버튼 클릭
![](images/2026-03-04-17-16-09.png)

적절한 이름을 부여합니다. 
![](images/2026-03-04-17-16-24.png)

작성한 Quality Gate를 선택하고 Code Coverage를 조정함.
실습에서는 테스트 코드가 없는 서비스도 많으므로 일단 '0'으로 함.
![](images/2026-03-04-17-16-38.png)  


4)Jenkins Credential 등록
Jenkins에 Credential을 위에서 만든 Token으로 만듭니다.
![](images/2026-03-04-17-13-14.png)

5)SonarQube Server설정
System설정에서 SonarQube 서버 설정을 합니다.
Jenkins에 플러그인 'SonarQube Scanner'를 먼저 설치 해야 합니다.

- Name: CI/CD파이프라인에서 참조할 이름입니다. 보통 SonarQube라고 합니다.
- Server URL: Jenkins Pod에서 접근할 SonarQube 서비스의 주소. kubectl get svc -n sonarqube로 확인하고 다른 네임스페이스에 있으므로 전체 주소를 입력합니다.
- Authentication Token: 위에서 만든 credential 'sonarqube-access-token'을 선택

![](images/2026-03-04-17-13-41.png)  

  
| [Top](#목차) |

---

## ArgoCD 설치

### Ingress 설정 확인

`create-k8s.md`에서 Ingress가 이미 구성되어 있어야 합니다.

| 클라우드 | Ingress Controller | IngressClass |
|---------|-------------------|-------------|
| AWS EKS | ALB (내장) | `alb` |
| Azure AKS | app-routing addon (내장) | `webapprouting.kubernetes.azure.com` |
| GCP GKE | GCE Ingress (내장) | annotation `kubernetes.io/ingress.class: "gce"` |

> ArgoCD는 `--insecure` 모드(HTTP backend)로 실행하므로
> 각 Ingress Controller가 일반 HTTP 트래픽으로 처리합니다.
> HTTPS 접근이 필요하면 외부 Nginx Web Server에서 HTTPS 프록시로 처리합니다 (`create-k8s.md` SSL 설정 섹션 참조).


**1.Helm registry 추가**
```
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
```

**2.Helm chart 다운로드**
```
mkdir -p ~/install && cd ~/install
```

```
helm search repo argocd

NAME                            CHART VERSION   APP VERSION
argo/argocd-applicationset      1.12.1          v0.4.1
argo/argocd-apps                2.0.2
argo/argocd-image-updater       0.12.0          v0.15.2
argo/argocd-notifications       1.8.1           v1.2.1
argo/argo-cd                    3.35.4          v2.2.5
```

```
helm pull argo/argo-cd --version 7.8.13
```

> **참고**: 재현성을 위해 버전을 고정합니다. 최신 버전은 `helm search repo argo/argo-cd`로 확인하세요.

```
tar xvf {helm chart 압축파일명}

cd argo-cd
```

**3.Ingress External IP 확인 및 도메인 설정**

**[AWS EKS]** ALB 주소 확인:
ALB는 Ingress 생성 시 자동으로 프로비저닝되므로, 설치 후 Ingress ADDRESS에서 확인합니다.
도메인은 nip.io를 사용합니다.
```
export ARGO_DOMAIN=argo.{nip.io 도메인}
```

**[Azure AKS]** app-routing Ingress IP 확인:
```
kubectl get svc -n app-routing-system nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```
```
export ING_IP={위에서 구한 IP}
export ARGO_DOMAIN=argo.$ING_IP.nip.io
```

**[GCP GKE]** GCE Ingress IP 확인:
GCE Ingress는 생성 시 자동으로 외부 IP를 할당합니다. 설치 후 Ingress ADDRESS에서 확인합니다.
```
export ARGO_DOMAIN=argo.{nip.io 도메인}
```


**4.설치 manifest 파일 작성**
사용하는 CLOUD에 해당하는 argocd.yaml을 작성합니다.

**[AWS EKS]** argocd.yaml:
```
cat > argocd.yaml << EOF
global:
  domain: ${ARGO_DOMAIN}
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
    pathType: Prefix
    ingressClassName: alb
    annotations:
      alb.ingress.kubernetes.io/scheme: internet-facing
      alb.ingress.kubernetes.io/target-type: ip
      alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80}]'
      alb.ingress.kubernetes.io/group.name: cicd-tools  # 선택: ALB 공유 시 (비용 절감)
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
```
cat > argocd.yaml << EOF
global:
  domain: argo.$ING_IP.nip.io
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
```
cat > argocd.yaml << EOF
global:
  domain: ${ARGO_DOMAIN}
  # nodeSelector, tolerations 없음 (Autopilot)

server:
  ingress:
    enabled: true
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

> **GCE Ingress Health Check 주의**: GCE Ingress는 기본적으로 `/` 경로로 HTTP health check를 수행합니다.
> ArgoCD가 정상 응답하지 않아 backend가 UNHEALTHY로 표시되면
> BackendConfig를 통해 health check 경로를 `/healthz`로 조정하세요.

> **공통**: 모든 클라우드에서 `--insecure` + `server.insecure: true`로 HTTP backend 사용.
> TLS 종료가 필요하면 외부 Nginx Web Server에서 HTTPS 프록시로 처리합니다.


**5.namespace 작성 및 설치**

```
k create ns argocd
kubens argocd
```

```
helm upgrade -i argocd -f argocd.yaml .
```


**6.접속하기**

Ingress Address를 확인합니다.

**[AWS EKS]**:
```
kubectl get ing -n argocd
```

**[Azure AKS]**:
```
kubectl get ing -n argocd
```

**[GCP GKE]** (약 3~5분 소요):
```
kubectl get ing -n argocd
```

Web Server VM에 SSH 접속하여 Nginx 프록시 설정을 추가합니다.
위에서 확인한 Ingress Address를 환경변수로 설정합니다.
`JENKINS_ADDRESS`, `SONAR_ADDRESS`는 이전 단계에서 확인한 Ingress Address입니다.
```
export WEB_SERVER_SSH_HOST={Web Server SSH Host}
export JENKINS_ADDRESS={Jenkins Ingress Address}
export SONAR_ADDRESS={SonarQube Ingress Address}
export ARGOCD_ADDRESS={ArgoCD Ingress Address}
```

```
ssh ${WEB_SERVER_SSH_HOST}

cat << EOF | sudo tee /etc/nginx/sites-available/cicd
server {
    listen 80 default_server;
    server_name myjenkins.io;
    location / {
        proxy_pass http://${JENKINS_ADDRESS};
        proxy_set_header Host myjenkins.io;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}

server {
    listen 80;
    server_name mysonar.io;
    location / {
        proxy_pass http://${SONAR_ADDRESS};
        proxy_set_header Host mysonar.io;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}

server {
    listen 80;
    server_name myargocd.io;
    location / {
        proxy_pass http://${ARGOCD_ADDRESS};
        proxy_set_header Host myargocd.io;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}

# HTTPS 요청을 HTTP로 리다이렉트
server {
    listen 443 ssl default_server;
    server_name _;
    ssl_certificate /etc/nginx/ssl/dummy.crt;
    ssl_certificate_key /etc/nginx/ssl/dummy.key;
    return 301 http://\$host\$request_uri;
}
EOF

sudo nginx -t && sudo systemctl reload nginx
```

브라우저에서 `http://myargocd.io`로 접근합니다.

ID는 admin이고 초기 암호는 아래와 같이 구합니다.
```
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
```

비밀번호는 로그인 후 'User Info'에서 변경할 수 있습니다.


| [Top](#목차) |

---

## Image Registry Credential 설정

> **CI/CD 아키텍처**: CI(Jenkins/GitHub Actions)는 이미지 빌드 및 Push만 수행하고, CD는 ArgoCD가 담당합니다.
> 따라서 k8s 클러스터 접근 Credential(Service Principal, IAM Role, GCP SA)은 불필요하며
> Image Registry Credential만 등록합니다.
> Jenkins의 Kubernetes 연결(섹션 7)은 빌드 Agent Pod 프로비저닝용이며
> 인-클러스터 ServiceAccount로 처리됩니다.


### [AWS EKS] ECR Credential 생성

ECR 로그인 토큰을 구합니다.
```
aws ecr get-login-password --region ap-northeast-2
```

Jenkins credential에 등록: 이름은 'imagereg-credentials'으로 등록
```
- Kind: Username with password
- Username: AWS
- Password: {위에서 구한 ECR 로그인 토큰}
```

> **참고**: ECR 로그인 토큰은 12시간마다 만료됩니다.
> 프로덕션 환경에서는 Jenkins Pipeline에서 `ecr:getLogin` 스텝을 사용하거나,
> `amazon-ecr-credential-helper`를 설치하여 자동 갱신하는 것을 권장합니다.


### [Azure AKS] ACR Credential 생성

아래 명령으로 암호를 획득합니다.
```
az acr credential show -n {acr 이름}
```

```
az acr credential show -n unicorncr

{
  "passwords": [
    {
      "name": "password",
      "value": "{ACR_PASSWORD_1}"
    },
    {
      "name": "password2",
      "value": "{ACR_PASSWORD_2}"
    }
  ],
  "username": "{ACR_USERNAME}"
}
```

Jenkins credential에 등록: 이름은 'imagereg-credentials'으로 등록

![](images/2025-12-01-12-29-46.png)


### [GCP GKE] Artifact Registry Credential 생성

GCP Console에서 Artifact Registry 접근용 Service Account를 생성합니다.
1. Service Account 생성
2. Role 부여: **Artifact Registry 관리자** (Kubernetes Engine 역할은 불필요)
3. JSON Key 다운로드

Jenkins credential에 등록: 이름은 'imagereg-credentials'으로 등록
```
- Kind: Username with password
- Username: _json_key
- Password: {Service Account JSON Key 내용 전체}
```


| [Top](#목차) |

---

## DockerHub Credentials 생성

Pipeline 실행 시 DockerHub에서도 이미지를 내려 받기 때문에 인증정보를 등록해줘야 합니다.
public image는 인증 없이도 내려받을수 있으나 횟수에 제한이 있어 등록해 줘야 합니다.

1)Access Token생성
DockerHub(https://hub.docker.com)에 로그인 합니다.

Account Settings를 클릭
![](images/2025-09-12-23-58-09.png)

Personal Access Token을 생성합니다.
![](images/2025-09-12-23-58-57.png)

![](images/2025-09-12-23-59-43.png)

2)Jenkins Credentials 등록
'dockerhub-credentials'라는 이름으로 등록합니다.
username은 Docker Hub 로그인 id 이고 암호는 위에서 만든 토큰을 입력합니다.
![](images/2025-09-13-00-01-56.png)

| [Top](#목차) |

---

## GitHub Actions Repository Secrets/Variables 설정

> **대상**: CI 도구로 **GitHub Actions**를 선택한 경우에만 해당합니다. Jenkins 사용자는 이 섹션을 건너뛰세요.

GitHub Actions는 별도 서버 설치가 불필요하지만, 워크플로우에서 사용할 인증정보와 변수를 GitHub Repository에 등록해야 합니다.

**등록 위치**: Repository Settings > Secrets and variables > Actions

### Repository Secrets (인증정보)

**클라우드별 레지스트리 인증:**

| CLOUD | Secret 이름 | 값 |
|-------|-----------|-----|
| AWS | `AWS_ACCESS_KEY_ID` | AWS 액세스 키 ID |
| AWS | `AWS_SECRET_ACCESS_KEY` | AWS 시크릿 액세스 키 |
| Azure | `AZURE_CREDENTIALS` | Service Principal JSON (`az ad sp create-for-rbac` 출력) |
| Azure | `ACR_USERNAME` | ACR 관리자 사용자명 (`az acr credential show -n {ACR명}`) |
| Azure | `ACR_PASSWORD` | ACR 관리자 패스워드 |
| GCP | `GCP_SA_KEY` | GCP 서비스 계정 키 JSON |

**공통 Secrets:**

| Secret 이름 | 값 | 용도 |
|-----------|-----|------|
| `SONAR_TOKEN` | SonarQube 사용자 토큰 | 코드 품질 분석 |
| `SONAR_HOST_URL` | SonarQube 서버 URL (예: `http://20.249.187.69`) | 코드 품질 분석 |
| `DOCKERHUB_USERNAME` | Docker Hub 사용자명 | Rate Limit 해결 |
| `DOCKERHUB_PASSWORD` | Docker Hub Personal Access Token | Rate Limit 해결 |
| `GIT_USERNAME` | 매니페스트 레포지토리 접근용 GitHub 사용자명 | ArgoCD GitOps |
| `GIT_PASSWORD` | 매니페스트 레포지토리 접근용 GitHub Token | ArgoCD GitOps |

> **참고**: `GIT_USERNAME`/`GIT_PASSWORD`는 기본 이름입니다. 다른 이름을 사용하려면 워크플로우 YAML의 `secrets.GIT_USERNAME`/`secrets.GIT_PASSWORD` 참조를 해당 이름으로 변경하세요.

### Repository Variables (워크플로우 제어)

| Variable 이름 | 값 예시 | 설명 |
|-------------|--------|------|
| `CLOUD` | `Azure` | 클라우드 서비스 (AWS/Azure/GCP) |
| `REGISTRY` | `acrdigitalgarage01.azurecr.io` | 컨테이너 이미지 레지스트리 주소 |
| `IMAGE_ORG` | `phonebill` | 이미지 조직명 |
| `ENVIRONMENT` | `dev` | 기본 배포 환경 (dev/staging/prod) |
| `SKIP_SONARQUBE` | `true` | SonarQube 분석 스킵 여부 |

| [Top](#목차) |

---
