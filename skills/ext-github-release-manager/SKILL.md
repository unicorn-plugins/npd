---
name: ext-github-release-manager
description: github-release-manager 외부 플러그인 워크플로우 실행
type: external
user-invocable: true
allowed-tools: Skill
---

# ext-github-release-manager

## 목표

`github-release-manager` 플러그인에 GitHub Release 문서 자동 생성·수정·삭제 및 구성 추천 워크플로우를 위임함.

## 선행 요구사항

- `github-release-manager` 플러그인 설치 필수
  - `claude plugin marketplace add unicorn-plugins/github-release-manager`
  - `claude plugin install github-release-manager@github-release-manager`
- GitHub CLI (gh) 설치 및 인증 완료
- Context7 MCP 서버 설치 (공식 문서 조회용)

## 활성화 조건

사용자가 `/npd:ext-github-release-manager` 호출 시.

## 크로스-플러그인 스킬 위임 규칙

| 스킬 | FQN | 설명 |
|------|-----|------|
| 구성 추천 | `github-release-manager:recommend-template` | 프로젝트 특성 분석 기반 Release 문서 구성 추천 |
| Release 생성 | `github-release-manager:create-release` | 커밋·PR·이슈 분석 후 Release 문서 자동 생성 |
| Release 수정 | `github-release-manager:edit-release` | 기존 Release 문서 분석 및 수정 |
| Release 삭제 | `github-release-manager:delete-release` | Release 문서 삭제 및 태그 관리 |

### ARGS 스키마

**recommend-template**
```json
{
  "source_plugin": "npd",
  "project_dir": "{프로젝트 디렉토리}"
}
```

**create-release**
```json
{
  "source_plugin": "npd",
  "project_dir": "{프로젝트 디렉토리}",
  "version": "{릴리스 버전 (선택)}",
  "base_ref": "{비교 기준 태그/커밋 (선택)}"
}
```

**edit-release**
```json
{
  "source_plugin": "npd",
  "project_dir": "{프로젝트 디렉토리}",
  "version": "{수정 대상 릴리스 버전}",
  "changes": "{수정할 내용 설명 (선택)}"
}
```

**delete-release**
```json
{
  "source_plugin": "npd",
  "project_dir": "{프로젝트 디렉토리}",
  "version": "{삭제 대상 릴리스 버전}",
  "delete_tag": false
}
```

## 도메인 컨텍스트 수집

Phase 0에서 아래 컨텍스트를 수집하여 실행 경로를 결정함:

| 수집 대상 | 명령 | 용도 |
|----------|------|------|
| 기존 릴리스 목록 | `gh release list --limit 10` | 경로 분기 판단 |
| Git 태그 목록 | `git tag --sort=-v:refname` | 버전 결정, base_ref 추론 |
| 최근 커밋 이력 | `git log {last_tag}..HEAD --oneline` | Release 본문 생성 소스 |
| 릴리스 구성 파일 | `.github/release.yml` 존재 여부 | 경로 분기 판단 |
| 패키지 버전 | `package.json`, `pyproject.toml` 버전 필드 | 버전 자동 추론 |

### 경로 분기 판단 기준

| 조건 | 실행 경로 |
|------|----------|
| 기존 릴리스 0건 또는 `.github/release.yml` 미존재 | Recommend → Create |
| 기존 릴리스 1건 이상 + `.github/release.yml` 존재 | Direct Create |
| 사용자가 특정 릴리스 수정 요청 | Direct Edit |
| 사용자가 특정 릴리스 삭제 요청 | Direct Delete |

## 워크플로우

### Phase 0: 사전 확인

1. `github-release-manager` 플러그인 설치 여부 확인
2. `gh` CLI 설치 및 인증 상태 확인
3. 현재 프로젝트 디렉토리 확인 (`cwd`)
4. 도메인 컨텍스트 수집 (릴리스 목록, 태그, 커밋, 구성 파일, 패키지 버전)
5. 사용자 의도 파악 (생성/수정/삭제) 및 실행 경로 결정

### Phase 1: 실행 경로별 스킬 위임

**Recommend → Create 경로:**
1. `github-release-manager:recommend-template` 호출
2. 추천 결과 사용자 확인
3. `github-release-manager:create-release` 호출

**Direct Create 경로:**
1. `github-release-manager:create-release` 호출

**Direct Edit 경로:**
1. `github-release-manager:edit-release` 호출

**Direct Delete 경로:**
1. `github-release-manager:delete-release` 호출

### Phase 2: 완료

위임 결과를 사용자에게 보고.

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | Phase 0에서 반드시 도메인 컨텍스트를 수집한 뒤 경로를 결정할 것 |
| 2 | `source_plugin: "npd"` 를 항상 ARGS에 포함할 것 |
| 3 | 플러그인 미설치 시 설치 안내 후 중단할 것 |

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | 플러그인 설치 확인 없이 스킬을 위임하지 않을 것 |
| 2 | 사용자 의도 파악 없이 임의로 삭제 경로를 실행하지 않을 것 |

## 검증 체크리스트

- [ ] Phase 0 도메인 컨텍스트 수집 완료
- [ ] 실행 경로 결정 완료
- [ ] 해당 스킬 위임 완료
- [ ] 위임 결과 사용자 보고 완료
