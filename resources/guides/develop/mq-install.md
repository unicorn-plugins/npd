# MQ설치가이드

## 목적
MQ설치계획서에 따라 제공된 설치 대상 환경에 Message Queue를 설치한다. 설치 후 연결 방법을 안내하고 연결 문자열을 파일로 저장한다.

## 입력 (이전 단계 산출물)

| 산출물 | 파일 경로 | 활용 방법 |
|--------|----------|----------|
| MQ 설치 계획서 | `develop/mq/mq-plan-{설치대상환경}.md` | 설치 사양 확인 |

## 출력 (이 단계 산출물)

| 산출물 | 파일 경로 |
|--------|----------|
| MQ 설치 실행 결과서 | `develop/mq/mq-exec-{설치대상환경}.md` |
| MQ 연결 문자열 | `mq-connection-string.txt` |

## 방법론

- 제공된 {설치대상환경}에만 설치
- 'MQ설치계획서'에 따라 병렬로 설치
- 현재 OS에 맞게 설치
- 설치 후 연결 방법 안내
- 설치 대상 클라우드 플랫폼은 이미 로그인되어 있음
- Kubernetes에 배포 manifest나 helm 설치를 위한 values.yaml은 develop/mq 디렉토리에 생성
- MQ연결문자열을 얻는 명령어를 결과서에 명시하고 연결문자열을 mq-connection-string.txt에 저장
- 설치 결과 파일에는 설치 시 사용한 명령을 포함하여 작성

## 출력 형식

- 파일명: `develop/mq/mq-exec-{설치대상환경}.md`
- `{설치대상환경}`은 `dev` 또는 `prod`로 함
- 설치 시 사용한 명령(helm 명령, values.yaml 등) 포함
- MQ 연결 문자열 획득 명령어 명시
- 연결 문자열은 별도로 `mq-connection-string.txt`에 저장

## 품질 기준

- [ ] MQ 연결 문자열 환경변수 기반
- [ ] 민감 정보 하드코딩 금지

## 주의사항

- 지정된 설치 대상 환경({설치대상환경})에만 설치
- MQ 연결 문자열은 결과서 명시 및 별도 파일(`mq-connection-string.txt`) 저장 모두 수행
- Kubernetes 배포용 values.yaml은 `develop/mq` 디렉토리에 생성
