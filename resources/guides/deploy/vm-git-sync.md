# VM 소스 동기화 공통 가이드

> 본 가이드는 `skills/deploy/SKILL.md`의 다음 4개 Step에서 호출됨:
> - Phase 3 / Step 1 (PREV_ACTION) — Phase 진입 전 동기화
> - Phase 3 / Step 3 (POST_ACTION) — 산출물 커밋
> - Phase 4 / Step 1 (PREV_ACTION) — Phase 진입 전 동기화 + `.env` scp
> - Phase 4 / Step 4 (POST_ACTION) — 산출물 커밋
>
> 4곳의 git sync 절차를 시점·commit message·`.env` 처리로 분기하여 단일 가이드로 정의.

## 입력

- `{VM.HOST}` (Phase 1 / Step 5에서 수집)
- `{ROOT}` (AGENTS.md 시스템명, VM 작업 디렉토리 `~/workspace/{ROOT}`)
- `{org}/{repo}` (Git 원격 저장소)
- `{commit_message}` (호출 시점에 따라 결정, 아래 매핑 참조)
- `{is_private}` (저장소 Private 여부, true이면 PAT 사용)
- `{copy_env}` (true이면 로컬 `.env`를 VM으로 scp, Phase 4 / Step 1 한정)

## 호출 시점별 매핑

| 호출 시점 | 모드 | commit message | `.env` scp |
|----------|------|----------------|------------|
| Phase 3 / Step 1 (PREV) | A. 진입 전 동기화 | `"deploy: Phase 3 시작 전 소스 동기화"` | 불필요 |
| Phase 3 / Step 3 (POST) | C. 산출물 커밋 | `"deploy: Phase 3 산출물 (Dockerfile, build-image guide)"` | 불필요 |
| Phase 4 / Step 1 (PREV) | B. 진입 전 동기화 + .env | `"deploy: Phase 4 시작 전 소스 동기화"` (커밋 불필요) | **필요** |
| Phase 4 / Step 4 (POST) | C. 산출물 커밋 | `"deploy: Phase 4 산출물 (backing-service-result, run-container-result)"` | 불필요 |

---

## 모드 A: Phase 진입 전 동기화 (PREV_ACTION 일반)

### A-1. 로컬 소스 커밋 & 푸시

```bash
git add -A && git commit -m "{commit_message}" && git push
```

### A-2. VM 소스 준비 (clone 또는 pull)

**Public 저장소:**
```bash
ssh {VM.HOST} 'if [ -d ~/workspace/{ROOT} ]; then cd ~/workspace/{ROOT} && git pull; else mkdir -p ~/workspace && cd ~/workspace && git clone https://github.com/{org}/{repo}.git && cd {ROOT}; fi'
```

**Private 저장소 (PAT 사용):**
```bash
GIT_PAT=$(gh auth token)
ssh {VM.HOST} "if [ -d ~/workspace/{ROOT} ]; then cd ~/workspace/{ROOT} && git pull; else mkdir -p ~/workspace && cd ~/workspace && git clone https://\${GIT_PAT}@github.com/{org}/{repo}.git && cd {ROOT} && git remote set-url origin https://github.com/{org}/{repo}.git; fi"
```

---

## 모드 B: Phase 진입 전 동기화 + `.env` scp (Phase 4 / Step 1 전용)

### B-1. VM 소스 동기화

**Public 저장소:**
```bash
ssh {VM.HOST} 'cd ~/workspace/{ROOT} && git pull'
```

**Private 저장소:**
```bash
GIT_PAT=$(gh auth token)
ssh {VM.HOST} "cd ~/workspace/{ROOT} && git remote set-url origin https://\${GIT_PAT}@github.com/{org}/{repo}.git && git pull && git remote set-url origin https://github.com/{org}/{repo}.git"
```

### B-2. 로컬 `.env` 파일을 VM에 복사

```bash
scp .env {VM.HOST}:~/workspace/{ROOT}/.env
```

> `.env`는 `.gitignore`에 포함되어 git으로 전달되지 않으므로 `scp`로 직접 복사한다.
> AI 서비스 컨테이너 실행 시 `--env-file`로 참조한다.

---

## 모드 C: 산출물 커밋 (POST_ACTION 일반)

### C-1. VM에서 커밋 & 푸시

**Public 저장소:**
```bash
ssh {VM.HOST} 'cd ~/workspace/{ROOT} && git add -A && git commit -m "{commit_message}" && git push'
```

**Private 저장소 (PAT 기반):**
```bash
GIT_PAT=$(gh auth token)

ssh {VM.HOST} "cd ~/workspace/{ROOT} \
  && git add -A \
  && git commit -m '{commit_message}' \
  && git remote set-url origin https://${GIT_PAT}@github.com/{org}/{repo}.git \
  && git push \
  && git remote set-url origin https://github.com/{org}/{repo}.git"
```

### C-2. 로컬 동기화

```bash
git pull
```

---

## 산출물

- VM `~/workspace/{ROOT}` 디렉토리에 최신 소스 + (모드 B) `.env` 파일 적재
- 원격 저장소(`{org}/{repo}`)에 최신 산출물 커밋 (모드 A·C)
- 로컬 `git pull`로 VM 산출물과 동기화 (모드 C)
