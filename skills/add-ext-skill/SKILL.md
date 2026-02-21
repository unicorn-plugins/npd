---
name: add-ext-skill
description: 외부호출 스킬(ext-{대상플러그인}) 추가 유틸리티
type: utility
user-invocable: true
allowed-tools: Read, Write, Edit, Bash
---

# Add Ext Skill

## 목표

사용자가 `/npd:add-ext-skill`로 호출하여 외부 플러그인 연동 스킬(ext-{대상플러그인})을 추가할 수 있게 함.

## 활성화 조건

사용자가 `/npd:add-ext-skill` 호출 시 또는 "외부 스킬 추가", "ext-skill 추가" 키워드 감지 시.

## 워크플로우

### Step 1: 대상 플러그인 탐색

dmap 리소스 마켓플레이스에서 플러그인 카탈로그 다운로드:
```bash
curl https://raw.githubusercontent.com/unicorn-plugins/dmap/refs/heads/main/resources/plugin-resources.md > .dmap/plugin-resources.md
```
다운로드 실패 시: `.dmap/plugin-resources.md` 캐시 파일 재사용. 캐시도 없으면 사용자에게 대상 플러그인명 직접 입력 요청.

### Step 2: 대상 플러그인 선택

`.dmap/plugin-resources.md`의 플러그인 목록을 사용자에게 표시하고 선택받음.
이미 `skills/ext-{대상플러그인}/` 디렉토리가 존재하면 중복 안내 후 중단.

### Step 3: 플러그인 명세서 다운로드

```bash
curl https://raw.githubusercontent.com/unicorn-plugins/dmap/refs/heads/main/resources/plugins/{분류}/{name}.md > .dmap/plugins/{name}.md
```
다운로드 실패 시 캐시 재사용. 캐시도 없으면 사용자에게 안내하고 중단.

### Step 4: 도메인 컨텍스트 수집

아래 파일에서 도메인 컨텍스트 수집:
- `.dmap/npd/requirements.md` (요구사항 정의서, 존재 시)
- `.claude-plugin/plugin.json` (플러그인 메타데이터)
- `CLAUDE.md` (프로젝트 컨텍스트)

### Step 5: ext-{대상플러그인} External 스킬 생성

명세서의 제공 스킬(FQN), ARGS 스키마, 실행 경로, 도메인 컨텍스트를 기반으로
`skills/ext-{대상플러그인}/SKILL.md` 작성.

External 유형 표준 골격:
```yaml
---
name: ext-{대상플러그인}
description: {대상플러그인} 외부 플러그인 워크플로우 실행
type: external
user-invocable: true
allowed-tools: Skill
---
```

### Step 6: commands/ 진입점 생성

`commands/ext-{대상플러그인}.md` 작성:
```yaml
---
description: {대상플러그인} 외부 플러그인 실행
allowed-tools: Skill
---

Use the Skill tool to invoke the `npd:ext-{대상플러그인}` skill with all arguments passed through.
```

### Step 7: help 스킬 업데이트

`skills/help/SKILL.md`의 명령 테이블에 `/npd:ext-{대상플러그인}` 행 추가.

## MUST 규칙

| # | 규칙 |
|---|------|
| 1 | 중복 스킬 확인 후 생성할 것 |
| 2 | 플러그인 명세서를 반드시 읽고 ARGS 스키마를 반영할 것 |
| 3 | help 스킬 명령 테이블을 반드시 업데이트할 것 |

## MUST NOT 규칙

| # | 금지 사항 |
|---|----------|
| 1 | 명세서 없이 ext 스킬을 생성하지 않을 것 |
| 2 | 기존 스킬을 덮어쓰지 않을 것 |

## 검증 체크리스트

- [ ] 중복 스킬 확인 완료
- [ ] 플러그인 명세서 다운로드 완료
- [ ] `skills/ext-{대상플러그인}/SKILL.md` 생성 완료
- [ ] `commands/ext-{대상플러그인}.md` 생성 완료
- [ ] `skills/help/SKILL.md` 명령 테이블 업데이트 완료

## 참고사항 — External 유형 표준 골격

External 스킬 SKILL.md 필수 섹션:
- 목표: 어떤 외부 플러그인 워크플로우를 실행하는지
- 선행 요구사항: 외부 플러그인 설치 여부
- 활성화 조건: 호출 트리거
- 크로스-플러그인 스킬 위임 규칙: FQN, ARGS, 반환값
- 도메인 컨텍스트 수집: npd 프로젝트 컨텍스트를 외부 스킬에 전달하는 방법
- 워크플로우: Phase 0(사전 확인) ~ 완료
- MUST 규칙, MUST NOT 규칙, 검증 체크리스트