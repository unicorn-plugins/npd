## CI/CD

### CI/CD 툴 설치: Jenkins, SonarQube, ArgoCD

https://github.com/cna-bootcamp/clauding-guide/blob/main/guides/setup/05.setup-cicd-tools.md

| [Top](#목차) |

---

### Jenkins를 이용한 CI/CD
#### 백엔드 서비스
작업 단계는 아래와 같습니다.    
https://github.com/cna-bootcamp/clauding-guide/blob/main/references/cicd-jenkins-backend-tasks.svg


**1.루트 build.gradle 수정**    
1)플러그인 'sonarqube'를 추가    
```
plugins {
  ...
  id "org.sonarqube" version "5.0.0.4638" apply false
}
```

2)플러그인 'jacoco' 추가    
jacoco는 소스 품질 검사 툴입니다.   
```
subprojects {
  ...

  apply plugin: 'org.sonarqube'
  apply plugin: 'jacoco' // 서브 프로젝트에 JaCoCo 플러그인 적용

  jacoco {
      toolVersion = "0.8.11" // JaCoCo 최신 버전 사용
  }

  ...
```

3)Test 설정    
기존에 'test'항목이 있으면 지우고 아래와 같이 변경합니다.     

```
subprojects {
  ...

  test {
      useJUnitPlatform()
      include '**/*Test.class'
      testLogging {
          events "passed", "skipped", "failed"
      }
      finalizedBy jacocoTestReport // 테스트 후 JaCoCo 리포트 생성
  }
  jacocoTestReport {
      dependsOn test
      reports {
          xml.required = true // SonarQube 분석을 위해 XML 형식 필요
          csv.required = false
          html.required = true
          html.outputLocation = layout.buildDirectory.dir("jacocoHtml").get().asFile
      }

      afterEvaluate {
          classDirectories.setFrom(files(classDirectories.files.collect {
              fileTree(dir: it, exclude: [
                      "**/config/**",        // 설정 클래스 제외
                      "**/entity/**",        // 엔티티 클래스 제외
                      "**/dto/**",           // DTO 클래스 제외
                      "**/*Application.class", // 메인 애플리케이션 클래스 제외
                      "**/exception/**"      // 예외 클래스 제외
              ])
          }))
      }
  }
}
```

**2.SonarQube 프로젝트 만들기**     
SonarQube에 로그인하여 수행합니다.  
1)각 서비스별 프로젝트 만들기    
{root project}-{서비스명}-{대상환경:dev/staging/prod}
아래 5개의 프로젝트를 만듭니다.
- phonebill-user-service-dev
- phonebill-bill-service-dev
- phonebill-product-service-dev
- phonebill-kos-mock-dev
- phonebill-api-gateway-dev

![](images/2025-09-11-19-07-13.png)  

branch명은 'main'으로 함.
![](images/2025-09-12-13-34-25.png)

![](images/2025-09-11-19-08-46.png)

2)각 프로젝트에서 Quality Gate 수정    

![](images/2025-09-11-19-09-11.png)

![](images/2025-09-11-19-11-44.png)  


**3.Jenkins CI/CD 파일 작성**     
IntelliJ를 실행하고 Claude Code도 시작한 후 수행 하세요.   
아래와 같이 프롬프팅하여 Jenkins CI/CD파일들을 작성합니다.    
deployment/cicd 디렉토리 하위에 파일들이 생성됩니다.    

예시)  
DockerHub + minikube 사용 시
```
/deploy-jenkins-cicd-guide-back

[실행정보]
- IMG_REG: docker.io
- IMG_ORG: phonebill
- JENKINS_CLOUD_NAME: k8s  
- NAMESPACE: phonebill
```

ACR + AKS 사용 시
```
/deploy-jenkins-cicd-guide-back

[실행정보]
- IMG_REG: acrdigitalgarage01.azurecr.io
- IMG_ORG: phonebill
- JENKINS_CLOUD_NAME: aks  
- NAMESPACE: phonebill-0500
```

deployment/cicd 디렉토리 밑에 생성된 파일을 검토하고 수정합니다.   

**4.Git Push**     
Jenkins 파이프라인 구동 시 원격 Git Repo에서 소스와 CI/CD파일들을 내려 받아 수행합니다.   
따라서 로컬에서 수정하면 반드시 원격 Git Repo에 푸시해야 합니다.    
프롬프트창에 아래 명령을 내립니다.   
```
push
```

**5.GitHub Credential 작성**        
Jenkins에서 Git에 접근할 수 있는 정보를 등록합니다.    
![](images/2025-09-12-14-53-13.png).


**6.Jenkins 파이프라인 작성**        

1)'새로운 Item'을 클릭   
![](images/2025-09-12-13-56-01.png)

2)프로파일명 입력 후 Pipeline 카드 선택    
![](images/2025-09-12-13-57-33.png)

3)GitHub hook trigger for GITScm polling 체크    
GitHub Repository에 WebHook을 설정을 하여 소스 업로드 시 Jenkins에 파이프라인 구동을 요청할 수 있습니다.   
이를 위해 이 옵션을 체크해야 합니다.   

![](images/2025-09-12-13-58-37.png)

4)Pipeline 설정   
매개변수 지정:    
배포 대상 환경 'ENVIRONMENT'를 추가. 값은 dev, staging, prod 중 하나인데 실습시에는 'dev'로 지정합니다.    
소스품질검사 Skip여부 'SKIP_SONARQUBE'를 추가. 값은 true 또는 false로 지정.
![](images/2025-09-13-16-50-46.png)
![](images/2025-09-13-16-53-22.png)
![](images/2025-09-13-16-54-01.png)

원격 Git 레포지토리 주소와 인증 Credential 지정   
![](images/2025-09-12-15-18-54.png)

브랜치를 'main'으로 하고 Jenkinsfile의 경로를 정확하게 입력합니다.   
![](images/2025-09-12-15-39-23.png)

**7.CI/CD 노드 증가**    
현재 CI/CD 관련 노드는 한개입니다.   
```
k get node | grep cicd
aks-cicd-33603374-vmss000002        Ready    <none>   130d   v1.30.10
```
Azure Portal에 로그인하여 노드를 한개 더 늘립니다.   

AKS 검색  
![](images/2025-09-12-16-58-32.png)

노드풀 클릭   
![](images/2025-09-12-16-59-20.png)

'cicd' 노드풀을 선택     
![](images/2025-09-12-16-59-47.png)

2개로 노드 증가   
![](images/2025-09-12-17-01-14.png)


**8.파이프라인 실행**    
1)기존 배포된 k8s객체 삭제     
intelliJ에서 터미널을 열고 아래 명령으로 모든 객체를 삭제합니다.
'-R'옵션은 하위 모든 서브 디렉토리에서 매니페스트 파일을 찾는 옵션입니다.      
```
kubectl delete -f deployment/k8s -R
```

2)파이프라인 실행  
1)실행방법   
'지금빌드'를 클릭하여 실행합니다.  
![](images/2025-09-12-15-40-58.png)  

2)BlueOcean 사용법    
블루오션은 진행상황을 더 편하게 볼 수 있는 플러그인입니다.   
![](images/2025-09-12-15-43-28.png)  

![](images/2025-09-12-15-44-04.png)

- 좌측 상단 'Jenkins'로고 클릭: 파이프라인 목록 보기
- 파이파라인 이름 옆에 톱니바퀴: 파이프라인 설정으로 이동
- 우측 상단 'Administration' 클릭: Jenkins 관리로 이동

아래 예와 같이 각 단계 진행상황을 볼 수 있으며, 작업을 클릭하면 로그를 확인할 수 있습니다.   
![](images/2025-09-12-15-50-03.png)


3)트러블슈팅   
아래와 같이 파이프라인 실행 중 나오는 에러 메시지를 복사하여 Claude Code에 해결 요청을 합니다.   
```
파이프라인 실행 에러.

FAILURE: Build failed with an exception.
* What went wrong:

Execution failed for task ':bill-service:sonar'.

> Could not resolve all files for configuration ':bill-service:testCompileClasspath'.

   > Could not find redis.embedded:embedded-redis:0.7.3.

     Required by:

         project :bill-service

```

로컬에서 수정 후 반드시 'push'명령으로 원격 Git 레포지토리에 푸시합니다.   
그리고 다시 파이프라인을 실행합니다.   

4)새로운 파이프라인 빠르게 시작하기     
파이프라인에서 에러가 나서 중단되었고 에러를 고쳐 새로 파이프라인을 시작했는데 한참동안 시작이 안될 경우가 있습니다.    
원인은 그전 에이젼트 파드가 없어지지 않아 리소스를 점유하고 있기 때문입니다.   
아래와 같이 에이젼트 파드를 찾아서 삭제 하세요.    
```
% k get po -n jenkins
NAME                       READY   STATUS    RESTARTS   AGE
12-kp6r4-wqw0z             0/4     Pending   0          3m28s
jenkins-69dc948556-tnpx7   1/1     Running   0          130d
```

```
k delete po 12-kp6r4-wqw0z -n jenkins --force --grace-period=0
```


| [Top](#목차) |

---

#### 프론트엔드 서비스  
작업 단계는 아래와 같습니다.    
https://github.com/cna-bootcamp/clauding-guide/blob/main/references/cicd-jenkins-frontend-tasks.svg

**1.사전작업**         

1)'.dockerignore' 파일 작성         
Frontend의 Pipeline 구동 시 성능을 높이기 위해 image 빌드 시   
image 내로 파일 복사할 때 제외할 파일이나 디렉토리를 정의합니다.   

아래 내용으로 .dockerignore 파일을 생성합니다.   
```
images
node_modules
npm-debug.log
build
.git
.github
coverage
.env*
.cache
dist
logs
**/*.log
**/.DS_Store
```

**2.SonarQube 프로젝트 만들기**     
SonarQube에 로그인하여 프론트엔드를 위한 프로젝트를 작성합니다.  
{서비스명}-{대상환경:dev/staging/prod}

아래 이름으로 작성합니다.  
- phonebill-front-dev


**3.Jenkins CI/CD 파일 작성**     
vscode를 실행하고 프론트엔드 서비스를 오픈하세요.   
Claude Code도 시작한 후 수행 하세요.   
아래와 같이 프롬프팅하여 Jenkins CI/CD파일들을 작성합니다.    
deployment/cicd 디렉토리 하위에 파일들이 생성됩니다.    
'Jenkins Kubernetes Cloud Name'은 Jenkins Cloud 설정에 추가한 이름을 지정합니다.   

예시)  
DockerHub + minikube 사용 시
```
@cicd
'프론트엔드Jenkins파이프라인작성가이드'에 따라 Jenkins를 이용한 CI/CD 가이드를 작성해 주세요.

[실행정보]
- IMG_REG: docker.io
- IMG_ORG: phonebill
- JENKINS_CLOUD_NAME: k8s  
- NAMESPACE: phonebill
```

ACR + AKS 사용 시
```
@cicd
'프론트엔드Jenkins파이프라인작성가이드'에 따라 Jenkins를 이용한 CI/CD 가이드를 작성해 주세요.
[실행정보]
- IMG_REG: acrdigitalgarage01.azurecr.io
- IMG_ORG: phonebill
- JENKINS_CLOUD_NAME: aks  
- NAMESPACE: phonebill-0500
```

deployment/cicd 디렉토리 밑에 생성된 파일을 검토하고 수정합니다.   

**4.Git Push**     
Jenkins 파이프라인 구동 시 원격 Git Repo에서 소스와 CI/CD파일들을 내려 받아 수행합니다.   
따라서 로컬에서 수정하면 반드시 원격 Git Repo에 푸시해야 합니다.    
프롬프트창에 아래 명령을 내립니다.   
```
push
```

**5.Jenkins 파이프라인 작성**        
1)'새로운 Item'을 클릭   
2)프로파일명 '서비스명' 입력 후 Pipeline 카드 선택: 예) phonebill-front    
3)GitHub hook trigger for GITScm polling 체크    
4)Pipeline 설정    
- 매개변수 지정:    
  - 배포 대상 환경 'ENVIRONMENT'를 추가. 값은 dev, staging, prod 중 하나인데 실습시에는 'dev'로 지정합니다.    
  - 소스품질검사 Skip여부 'SKIP_SONARQUBE'를 추가. 값은 true 또는 false로 지정.

- Repository URL: 원격 Git Repo 주소
- Credentials: 원격 Git Repo 접속 위한 인증 Credential
- branch를 '*/main'으로 수정  
- Jenkinsfile 경로: deployment/cicd/Jenkinsfile     

**6.파이프라인 실행**    
1)기존 배포된 k8s객체 삭제     
vscode에서 터미널을 열고 아래 명령으로 모든 객체를 삭제합니다.      
```
kubectl delete -f deployment/k8s
```
2)파이프라인 실행  

3)트러블슈팅   
아래와 같이 파이프라인 실행 중 나오는 에러 메시지를 복사하여 Claude Code에 해결 요청을 합니다.   
```
파이프라인 실행 에러.

{에러 메시지 붙여넣기}
```

로컬에서 수정 후 반드시 'push'명령으로 원격 Git 레포지토리에 푸시합니다.   
그리고 다시 파이프라인을 실행합니다.   

| [Top](#목차) |

---

#### WebhHook 설정
Git push 시 자동으로 pipeline이 구동되게 하려면 아래와 같이 github repository에 webhook 설정을 합니다.   

1.Git 레포지토리의 Settings를 클릭    
2.좌측메뉴에서 WebHooks 클릭   
3.Webhook 정보 입력       
  - Payload URL: http://{Jenkins service의 External IP}/github-webhook/
    아래와 같이 구합니다. 아래 예에서는 '20.249.203.199'가 Jenkins의 External IP입니다.   
    ```
    k get svc -n jenkins
    NAME                     TYPE           CLUSTER-IP    EXTERNAL-IP
    jenkins                  LoadBalancer   10.0.106.33   20.249.203.199
    ```
    Payload URL 예: http://20.249.203.199/github-webhook/

    주의) Payload URL 마지막에 반드시 ‘/’를 붙여야 합니다.
  - Content-Type: application/json
  - SSL Verification: Disable

  ![](images/2025-09-13-19-52-29.png)

4.테스트   
  - 백엔드 프로젝트에서 아무 파일이나 수정한 후 푸시    
    ```
    git add . && git commit -m "test cicd" && git push
    ```
  - 몇초 후 Jenkins 파이프라인이 구동되는것 확인    


| [Top](#목차) |

---

### GitHub Actions를 이용한 CI/CD

#### 백엔드 서비스
작업 단계는 아래와 같습니다.    

**0.사전작업**    
1)Jenkins로 배포한 객체 모두 삭제    
IntelliJ 터미널에서 아래 명령 수행   
```
k delete -f deployment/k8s -R
```

2)WebHook 트리거 해제   
소스 업로드 시 Jenkins 파이프라인 구동되지 않도록 파이프라인 설정에서 해제   
파이프라인 메뉴에서 '구성'을 클릭하거나,   
![](images/2025-09-15-15-58-32.png)  

블루오션에서 '설정' 아이콘을 클릭하여 파이프라인 설정화면으로 이동합니다.   
![](images/2025-09-15-15-58-59.png)

'GitHub hook trigger for GITScm polling'을 uncheck합니다.    
![](images/2025-09-15-16-00-47.png)

**1.Repository Secrets 설정(Azure)**      
GitHub Repository > Settings > Secrets and variables > Actions > Repository secrets에 다음 항목들을 등록하세요:   

Frontend에서도 사용하므로 **Organization Secret으로 등록**합니다.    
![](images/2025-12-02-16-58-23.png)

1)Azure 인증 정보    
Azure Cloude에 배포할때만 등록합니다.   
```json
AZURE_CREDENTIALS:
{
  "clientId": "5e4b5b41-7208-48b7-b821-d6d5acf50ecf",
  "clientSecret": "ldu8Q~GQEzFYU.dJX7_QsahR7n7C2xqkIM6hqbV8",
  "subscriptionId": "2513dd36-7978-48e3-9a7c-b221d4874f66",
  "tenantId": "4f0a3bfd-1156-4cce-8dc2-a049a13dba23"
}
```

팁) Azure Service Principal 등록   
위 Azure Credential 정보를 등록하는 방법은 아래 링크의 '10.Service Principal 작성'을 참고하세요.   
실습시에는 이미 되어 있으므로 절대 수행하지는 마세요.   
https://github.com/cna-bootcamp/clauding-guide/blob/main/guides/setup/05.setup-cicd-tools.md#jenkins%EC%84%A4%EC%B9%98

2)ACR Credentials    
Azure Cloude에 배포할때만 등록합니다.   
```bash
# ACR 자격 증명 확인 명령어   
az acr credential show --name acrdigitalgarage01
```
```
ACR_USERNAME: acrdigitalgarage01
ACR_PASSWORD: {ACR패스워드}
```

3)SonarQube 설정    
GitHub Actions 파이프라인에서 SonarQube를 접근하기 위한 정보를 등록합니다.   
```bash
# SonarQube URL 확인
kubectl get svc -n sonarqube

# SonarQube 토큰 생성 방법:
1. SonarQube 로그인 후 우측 상단 'Administrator' > My Account 클릭  
2. Security 탭 선택 후 토큰 생성  
```
```
SONAR_HOST_URL: http://{External IP}
SONAR_TOKEN: {SonarQube토큰}
```

4)Docker Hub 설정 (Rate Limit 해결)    
```
Docker Hub 패스워드 작성 방법
- DockerHub(https://hub.docker.com)에 로그인
- 우측 상단 프로필 아이콘 클릭 후 Account Settings를 선택
- 좌측메뉴에서 'Personal Access Tokens' 클릭하여 생성  
```

```
DOCKERHUB_USERNAME: {Docker Hub 사용자명}
DOCKERHUB_PASSWORD: {Docker Hub 패스워드}
```

5)VM_IP, VM_USER, VM_SSH_KEY, KUBECONFIG 등록     
minikube에 배포할때만 등록합니다.    
- VM_IP: minikube가 설치된 VM의 public IP
- VM_USER: minikube가 설치된 VM의 OS User
- VM_SSH_KEY: minikube가 설치된 VM 접속을 위한 private key file   
  Local에서 key file 내용을 읽어 등록   
  ```
  cat {SSH Key file 경로}
  ```
  예) cat ~/home/minikube_key.pem
- KUBECONFIG: minikube kubeconfig 파일 내용  
  Local에서 아래 명령을 수행한 결과를 등록    
  ```
  kubectl config view --minify --flatten
  ```


**2.Repository Variables 설정**    

GitHub Repository > Settings > Secrets and variables > Actions > Variables > Repository variables에 등록:
![](images/2025-09-15-15-50-36.png)  

```
ENVIRONMENT: dev
SKIP_SONARQUBE: true
```

**3.GitHub Actions CI/CD 파일 작성**     
IntelliJ를 실행하고 Claude Code도 시작한 후 수행 하세요.   
아래와 같이 프롬프팅하여 GitHub Actions CI/CD파일들을 작성합니다.    
deployment/.github 디렉토리 하위에 파일들이 생성됩니다.    

예시)  
Azure Cloud 배포용:   
```
/deploy-actions-cicd-guide-back

[실행정보]
- ACR_NAME: acrdigitalgarage01
- RESOURCE_GROUP: rg-digitalgarage-01
- AKS_CLUSTER: aks-digitalgarage-01
- NAMESPACE: phonebill-dg0500
```

minikube 배포용:    
MINIKUBE_IP는 minikube가 설치된 VM에서 'minikube ip' 명령으로 확인하세요.   

```
@cicd
아래 가이드에 따라 GitHub Actions를 이용한 CI/CD 가이드를 작성해 주세요.
[가이드]
- URL: https://raw.githubusercontent.com/cna-bootcamp/clauding-guide/refs/heads/main/guides/deploy/deploy-actions-cicd-back-minikube.md
- 파일명: deploy-actions-cicd-back-minikube.md
[실행정보]
- SYSTEM_NAME: phonebill
- IMG_REG: docker.io
- IMG_ORG: hiondal
- NAMESPACE: phonebill
- VM_IP: 52.231.227.173
- VM_USER: azureuser
- MINIKUBE_IP: 192.168.49.2
```

deployment/.github 디렉토리 밑에 생성된 파일을 검토하고 수정합니다.   


**4.Git Push**     
GitHub Actions 파이프라인 구동 시 원격 Git Repo에서 소스와 CI/CD파일들을 내려 받아 수행합니다.   
따라서 로컬에서 수정하면 반드시 원격 Git Repo에 푸시해야 합니다.    
프롬프트창에 아래 명령을 내립니다.   
```
push
```

**5.파이프라인 구동 확인**    
Actions 탭을 클릭하면 자동으로 파이프라인이 구동되는 것을 확인할 수 있습니다.   
![](images/2025-09-15-15-51-49.png)  

수행되고 있는 파이프라인을 클릭하면 Build -> Release -> Deploy별로 진행상태를 볼 수 있습니다.   
각 단계를 클릭하면 상세한 타스크 진행상태를 볼 수 있습니다.    

파이프라인 구동 시 에러가 발생하면 아래와 같이 에러메시지를 첨부하여 에러 해결을 요청합니다.   
예)
```
파이프라인 수행중 에러.

Run # 환경별 디렉토리로 이동
error: accumulating resources: accumulation err='accumulating resources from '../../base': '/home/runner/work/phonebill/phonebill/.github/kustomize/base' must resolve to a file':
...
Error: Process completed with exit code 1.
```

| [Top](#목차) |

---

#### 프론트엔드 서비스  

**0.사전작업**    
1)Jenkins로 배포한 객체 모두 삭제    
vscode 터미널에서 아래 명령 수행   
```
k delete -f deployment/k8s
```

2)WebHook 트리거 해제   
소스 업로드 시 Jenkins 파이프라인 구동되지 않도록 파이프라인 설정에서 해제   
파이프라인 메뉴에서 '구성'을 클릭하거나, 블루오션에서 '설정' 아이콘을 클릭하여 파이프라인 설정화면으로 이동합니다.  

'GitHub hook trigger for GITScm polling'을 uncheck합니다.

**1.Repository Secrets 설정**      

백엔드 배포 시 Organization Secret으로 등록한 값을 사용하므로 추가 등록 안합니다.  

**2.Repository Variables 설정**    

GitHub Repository > Settings > Secrets and variables > Actions > Variables > Repository variables에 등록:
![](images/2025-09-15-15-50-36.png)  

```
ENVIRONMENT: dev
SKIP_SONARQUBE: true
```

**3.GitHub Actions CI/CD 파일 작성**     
vscode를 실행하고 Claude Code도 시작한 후 수행 하세요.   
아래와 같이 프롬프팅하여 GitHub Actions CI/CD파일들을 작성합니다.  
[실행정보]는 본인 프로젝트에 맞게 수정하여야 합니다.     
.github 디렉토리 하위에 파일들이 생성됩니다.    

예시)  
Azure Cloud 배포용  
```
@cicd
'프론트엔드GitHubActions파이프라인작성가이드'에 따라 GitHub Actions를 이용한 CI/CD 가이드를 작성해 주세요.   
[실행정보]
- SYSTEM_NAME: phonebill
- ACR_NAME: acrdigitalgarage01
- RESOURCE_GROUP: rg-digitalgarage-01
- AKS_CLUSTER: aks-digitalgarage-01
- NAMESPACE: phonebill-dg0500
```

minikube 배포용:    
MINIKUBE_IP는 minikube가 설치된 VM에서 'minikube ip' 명령으로 확인하세요.   

```
@cicd
아래 가이드에 따라 GitHub Actions를 이용한 CI/CD 가이드를 작성해 주세요.
[가이드]
- URL: https://raw.githubusercontent.com/cna-bootcamp/clauding-guide/refs/heads/main/guides/deploy/deploy-actions-cicd-front-minikube.md
- 파일명: deploy-actions-cicd-front-minikube.md
[실행정보]
- SYSTEM_NAME: phonebill
- IMG_REG: docker.io
- IMG_ORG: hiondal
- NAMESPACE: phonebill
- VM_IP: 52.231.227.173
- VM_USER: azureuser
- MINIKUBE_IP: 192.168.49.2
```

.github 디렉토리 밑에 생성된 파일을 검토하고 수정합니다.   


**4.Git Push**     
GitHub Actions 파이프라인 구동 시 원격 Git Repo에서 소스와 CI/CD파일들을 내려 받아 수행합니다.   
따라서 로컬에서 수정하면 반드시 원격 Git Repo에 푸시해야 합니다.    
프롬프트창에 아래 명령을 내립니다.   
```
push
```

**5.파이프라인 구동 확인**    
Actions 탭을 클릭하면 자동으로 파이프라인이 구동되는 것을 확인할 수 있습니다.   

수행되고 있는 파이프라인을 클릭하면 Build -> Release -> Deploy별로 진행상태를 볼 수 있습니다.   
각 단계를 클릭하면 상세한 타스크 진행상태를 볼 수 있습니다.    
![](images/2025-09-15-16-51-05.png)  

파이프라인 구동 시 에러가 발생하면 아래와 같이 에러메시지를 첨부하여 에러 해결을 요청합니다.   
예)
```
파이프라인 수행중 에러.

Run # 환경별 디렉토리로 이동
error: accumulating resources: accumulation err='accumulating resources from '../../base': '/home/runner/work/phonebill/phonebill/.github/kustomize/base' must resolve to a file':
...
Error: Process completed with exit code 1.
```

| [Top](#목차) |

---

### ArgoCD를 이용한 CI와 CD 분리  

작업 단계는 아래와 같습니다.    

**0.사전작업**    
1)Jenkins로 배포한 객체 모두 삭제    
IntelliJ 터미널에서 아래 명령 수행   
```
k delete -f deployment/k8s -R
```
2)GitHub Actions workflow 수정   
기존 Workflow가 소스 푸시 시 동작하지 않도록 Disable함   
Actions탭 클릭 -> 기존 Workflow 클릭 -> 우측 메뉴에서 'Disable Workflow' 선택  

![](images/2025-09-15-20-19-28.png)

백엔드 레포지토리와 프론트엔드 레포지토리에서 모두 수행함.   

3)백엔드와 프론트엔드 레포지토리에 Secret 변수 등록    
GitHub Repository > Settings > Secrets and variables > Actions > Repository secrets에 다음 항목들을 등록하세요.        
매니페스트 레포지토리에 접근할 수 있는 인증정보를 등록.   
```
GIT_USERNAME
GIT_PASSWORD
```

**1.manifest 레포지토리 생성**    
1)원격 레포지토리 생성   
GitHub에 원격 레포티지토리를 생성합니다.   
{SYSTEM_NAME}-manifest 형식으로 작성합니다.    
예) phonebill-manifest

2)로컬 레포지토리 생성  
Window는 Window Terminal의 GitBash 터미널을 열고 Mac은 기본 터미널을 열어 작업합니다.    

```
cd ~/home/workspace
mkdir {SYSTEM_NAME}-manifest
cd {SYSTEM_NAME}-manifest
git init
git checkout -b main
git remote add origin {원격 Git Repository 주소}
```

예) SYSTEM_NAME이 phonebill인 경우   
```
cd ~/home/workspace
mkdir phonebill-manifest
cd phonebill-manifest
git init
git checkout -b main
git remote add origin https://github.com/cna-bootcamp/phonebill-manifest
```

**2.CLAUDE.md 작성**       
vscode에서 로컬 레포지토리를 오픈합니다.    
```
code .
```

아래 내용으로 CLAUDE.md 파일을 만듭니다.   
```
# ArgoCD 가이드

[Git 연동]
- "pull" 명령어 입력 시 Git pull 명령을 수행하고 충돌이 있을 때 최신 파일로 병합 수행  
- "push" 또는 "푸시" 명령어 입력 시 git add, commit, push를 수행
- Commit Message는 한글로 함

[URL링크 참조]
- URL링크는 WebFetch가 아닌 'curl {URL} > claude/{filename}'명령으로 저장
- 동일한 파일이 있으면 덮어 씀
- 'claude'디렉토리가 없으면 생성하고 다운로드   
- 저장된 파일을 읽어 사용함

## 가이드
- ArgoCD파이프라인준비가이드
  - 설명: 프론트엔드/백엔드 서비스를 ArgoCD를 이용하여 CI와 CD를 분리하는 가이드  
  - URL: https://raw.githubusercontent.com/cna-bootcamp/clauding-guide/refs/heads/main/guides/deploy/deploy-argocd-cicd.md
  - 파일명: deploy-argocd-cicd.md

### 작업 약어
- "@complex-flag": --seq --c7 --uc --wave-mode auto --wave-strategy systematic --delegate auto

- "@plan": --plan --think
- "@cicd": /sc:implement @devops --think @complex-flag
- "@document": /sc:document --think @scribe @complex-flag
- "@fix": /sc:troubleshoot --think @complex-flag
- "@estimate": /sc:estimate --think-hard @complex-flag
- "@improve": /sc:improve --think @complex-flag
- "@analyze": /sc:analyze --think --seq
- "@explain": /sc:explain --think --seq --answer-only
```

**3.매니페스트 구성 및 파이프라인 작성**     
vscode에서 Claude Code를 수행합니다.   

Claude Code 수행: View > Command Palette 수행하고 'Run Claude Code'로 실행    

YOLO모드로 실행하려면 View > Terminal을 수행하고 아래 명령으로 시작합니다.   
```
cy-yolo
```

아래 예시와 같이 프롬프팅 합니다.      
'[실행정보]'는 본인 프로젝트에 맞게 수정해야 합니다.   

예시)
Jenkins기반의 CI/CD 분리:  
```
@cicd
'ArgoCD파이프라인준비가이드'에 따라 Jenkins기반의 CI와 CD분리 준비 작업을 해주세요.   
[실행정보]
- SYSTEM_NAME: phonebill
- FRONTEND_SERVICE: phonebill-front
- IMG_REG: acrdigitalgarage01.azurecr.io
- IMG_ORG: phonebill
- MANIFEST_REG: https://github.com/cna-bootcamp/phonebill-manifest.git
- JENKINS_GIT_CREDENTIALS: github-credentials-dg0500
```

GitHub Actions기반의 CI/CD 분리:
```
@cicd
'ArgoCD파이프라인준비가이드'에 따라 GitHub Actions기반의 CI와 CD분리 준비 작업을 해주세요.   
[실행정보]
- SYSTEM_NAME: phonebill
- FRONTEND_SERVICE: phonebill-front
- IMG_REG: acrdigitalgarage01.azurecr.io
- IMG_ORG: phonebill
- MANIFEST_REG: https://github.com/cna-bootcamp/phonebill-manifest.git
- MANIFEST_SECRET_GIT_USERNAME: GIT_USERNAME
- MANIFEST_SECRET_GIT_PASSWORD: GIT_PASSWORD
```

Jenkins와 GitHub Actions 모두 CI/CD 분리시:
```
@cicd
'ArgoCD파이프라인준비가이드'에 따라 CI와 CD분리 준비 작업을 해주세요.   
[실행정보]
- SYSTEM_NAME: phonebill
- FRONTEND_SERVICE: phonebill-front
- IMG_REG: acrdigitalgarage01.azurecr.io
- IMG_ORG: phonebill
- MANIFEST_REG: https://github.com/cna-bootcamp/phonebill-manifest.git
- JENKINS_GIT_CREDENTIALS: github-credentials-dg0500
- MANIFEST_SECRET_GIT_USERNAME: GIT_USERNAME
- MANIFEST_SECRET_GIT_PASSWORD: GIT_PASSWORD
```

수행결과 확인:  
- 매니페스트 레포지토리에 매니페스트 파일 생성     
- 백엔드/프론트엔드 Jenkins 파이프라인 스크립트 생성: deployment/cicd/Jenkinsfile_ArgoCD
- 백엔드/프론트엔드 GitHub Actions Workflow 파일 생성:
  - .github/workflows/backend-cicd_ArgoCD.yaml
  - .github/workflows/frontend-cicd_ArgoCD.yaml

**4.원격 레포지토리에 푸시**        
매니페스트 레포지토리 푸시: vscode의 Claude Code 창에서 'push'입력   

**5.기존 k8s객체 삭제**       
vscode GitBash 터미널을 추가하고 아래 명령을 수행합니다.    
1)백엔드 객체 삭제   
```
k delete ../phonebill/deployment/k8s -R
```

2)프론트엔드 객체 삭제
```
k delete ../phonebill-front/deployment/k8s
```

**6.ArgoCD 설정**    
ArgoCD에서는 아래와 같은 작업을 합니다.   
- Project 등록: ArgoCD의 애플리케이션들을 논리적으로 그룹핑한 개념. 매니페스트 레포지토리, 배포 대상 환경을 관리      
- 레포지토리 등록: 매니페스트 레포지토리 정보와 인증정보 등록   
- Application 등록: 백엔드와 프론트엔드별로 Project, 매니페스트 레포지토리와 배포 환경과의 동기화 옵션 등을 등록  

1)Project 등록   
- Settings > Projects를 클릭.  
  ![](images/2025-09-15-23-12-59.png)    
- 'NEW PROJECT' 버튼 클릭   
- 프로젝트명과 설명 입력
  ![](images/2025-09-15-23-14-35.png)  
- SOURCE REPOSITORIES 등록: 매니페스트 레포지토리 등록      
  'EDIT'버튼 클릭 > ADD SOURCE 클릭 > 매니페스트 레포지토리의 주소를 입력하고 'SAVE'버튼을 클릭하여 저장    
  ![](images/2025-09-15-23-15-36.png)     
- DESTINATIONS 등록: 배포 환경 정보 등록  
  'EDIT'버튼 클릭 > ADD DESTINATION 클릭 > 쿠버네티스 정보를 그림과 같이 입력하고 'SAVE'버튼을 클릭하여 저장  
  ![](images/2025-09-15-23-17-54.png)   

2)레포지토리 등록
- Settings > Repositories 클릭   
  ![](images/2025-09-15-23-21-17.png)
- 'CONNECT REPO' 클릭  
- 레포지토리 정보 등록   
  ![](images/2025-09-15-23-23-47.png)       
  - Choose your connection method: HTTPS
  - Type: git
  - Name: 적절히 입력. 보통 레포지토리명과 동일하게 함
  - Repository URL: 매니페스트 레포지토리의 주소
  - Username: 매니페스트 레포지토리 접근할 수 있는 유저ID
  - Password: Git Access Token (로그인 암호가 아님)
- 상단의 'CONNECT'를 눌러 저장한 후 연결상태가 'SUCCESSFUL'로 나와야 함  
  ![](images/2025-09-15-23-27-00.png)     

3)백엔드 Application 등록
- Applications > NEW APP 클릭
  ![](images/2025-09-15-23-29-01.png)  
- GENERAL 정보 등록
  ![](images/2025-09-15-23-31-19.png)
  - SYNC POLICY: 매니페스트 레포지토리와 현재 배포된 객체간 동기화 옵션
    - Prune Resources: 매니페스트 레포지토리에 정의 되지 않은 객체 삭제  
    - SELF HEALS: 매니페스트 레포지토리에 정의된대로 현재 배포된 객체를 동기화
  - 나머지 옵션은 체크하지 않음
- SOURCE 정보 등록
  ![](images/2025-09-15-23-35-29.png)  
  Path에 동기화할 Kustomize 디렉토리를 입력   
- DESTINATION 정보 등록  
  ![](images/2025-09-15-23-37-21.png)
- Kustomize 섹션: 디폴트값 그대로 정의  

4)프론트엔드 Application 등록   
백엔드 Application 등록 참조하여 등록합니다.   

5)확인   
아래와 같이 Status가 Healthy + Synched로 나와야 합니다.   
![](images/2025-09-16-00-33-57.png)  

터미널에서 확인해 보면 매니페스트에 정의된대로 k8s객체가 생성되는 것을 확인할 수 있습니다.   
```
kubectl get po
```

Application을 선택하고 우측 상단의 'Application Details Network'에서 3번째 아이콘을 눌러보세요.   
아래와 같이 k8s객체의 상태가 이쁘게 나옵니다.   
![](images/2025-09-16-00-38-26.png)

**7.Jenkins CI/CD 분리 테스트**           
1)백엔드 테스트    
백엔드 Jenkins 파이프라인 설정에서 Script Path를 수정합니다.    
![](images/2025-09-16-00-42-31.png)

파이프라인을 수동으로 실행하고 완료될때까지 기다립니다.       
약 3분 후 ArgoCD에서 Pod의 이미지 Tag가 변경되는것을 확인합니다.

Pod를 클릭합니다.  
![](images/2025-09-16-02-40-42.png)

image명이 변경된것을 확인합니다.  
![](images/2025-09-16-02-40-20.png)  

2)프론트엔드 테스트    
프론트엔드 Jenkins 파이프라인 설정에서 Script Path를 수정합니다.    
deployment/cicd/Jenkinsfile_ArgoCD로 수정하면 됩니다.   
파이프라인을 수동으로 실행하고 완료될때까지 기다립니다.    

약 3분 후 ArgoCD에서 Pod의 이미지 Tag가 변경되는것을 확인합니다.  

**8.GitHub Actions CI/CD 분리 테스트**          
각 로컬 레포지토리의 파일을 원격 레포지토리에 푸시 합니다.    
1)백엔드: IntelliJ의 Claude Code 창에서 'push'입력   
2)프론트엔드: vscode의 Claude Code 창에서 'push'입력   

원격 레포지토리의 Action탭에서 Workflow가 실행되는것을 확인합니다.   
Workflow 완료 후 약 3분 후 ArgoCD에서 Pod의 이미지 Tag가 변경되는것을 확인합니다.  

| [Top](#목차) |

---
