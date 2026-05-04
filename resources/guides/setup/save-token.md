# 토큰 절약 Tip

## RTK(Rust Token Killer) 설치

Git: https://github.com/rtk-ai/rtk.git

### 원리
AI Runtime이 명령(git, bash 등)을 수행하면 RTK가 hook으로 가로채서 자신이 명령을 수행하고 그 결과에서 불필요한 부분을 제거하고 AI Runtime에 넘기는 방식.  
AI Runtime은 명령 수행 결과를 그대로 Cloud로 보내는데 보내는 데이터가 작아지니 토큰이 절약되는 것임.    
```
  Without rtk:                                    With rtk:

  Claude  --git status-->  shell  -->  git         Claude  --git status-->  RTK  -->  git
    ^                                   |            ^                      |          |
    |        ~2,000 tokens (raw)        |            |   ~200 tokens        | filter   |
    +-----------------------------------+            +------- (filtered) ---+----------+
```

### 설치
- Linux/Mac: https://github.com/rtk-ai/rtk/tree/master#installation 참조
- Window: 
  - https://github.com/rtk-ai/rtk/releases 접근
  - 최신버전의 `rtk-x86_64-pc-windows-msvc.zip` 다운로드 후 압축 해제
  - ~/.local/bin 디렉토리에 rtk.exe 이동
    (위 디렉토리가 PATH에 있어야 함. 안되어 있으면 환경변수 PATH에 추가)
  - 아래 명령으로 AI Runtime에 따라 설치.   
    telemetry는 에러 발생 시 공급자에게 로그 전송하는 기능.  가급적 설치 X 
    ```
    # 1. Install for your AI tool
    rtk init -g                     # Claude Code / Copilot (default)
    rtk init -g --gemini            # Gemini CLI
    rtk init -g --codex             # Codex (OpenAI)
    rtk init -g --agent cursor      # Cursor
    rtk init --agent windsurf       # Windsurf
    rtk init --agent cline          # Cline / Roo Code
    rtk init --agent kilocode       # Kilo Code
    rtk init --agent antigravity    # Google Antigravity
    ``` 
    ※ Window에서 아래 경고는 무시해도 됨. Window Claude에서는 Hook 처리가 안되어 ~/.claude/CLAUDE.md의 지침으로 해결한다는 의미. 단, Cursor는 Hook처리됨.  
    Window에서 WSL(Window Subsystem for Linux)을 설치하고 WSL에서 하면 hook으로 동작함.  
    ```
    [warn] Hook-based mode requires Unix (macOS/Linux).
    Windows: use --claude-md mode for full injection.
    Falling back to --claude-md mode.
    ```
### 테스트
- Claude Code 재시작 후 대화창에 'git status' 입력. 아래와 같이 'rtk' 앞에 붙으면 성공   
  ```
  ❯ git status

  ● Bash(rtk git status)
  ⎿  * main...origin/main
     clean — nothing to commit
  ```
  ※ Mac/Linux, 그리고 Cursor에서는 Hook으로 처리하므로 'rtk'가 안보임 

### 절약 통계 보기
터미널에서 아래 명령 수행
```
rtk gain
```

결과 예시: 약 57.5% 절약
```
RTK Token Savings (Global Scope)
════════════════════════════════════════════════════════════

Total commands:    10
Input tokens:      475
Output tokens:     202
Tokens saved:      273 (57.5%)
Total exec time:   2.8s (avg 284ms)
Efficiency meter: ██████████████░░░░░░░░░░ 57.5%

[warn] No hook installed — run `rtk init -g` for automatic token savings

By Command
───────────────────────────────────────────────────────────────────────
  #  Command                   Count  Saved    Avg%    Time  Impact
───────────────────────────────────────────────────────────────────────
 1.  rtk git status                5    145   57.3%   158ms  ██████████
 2.  rtk git diff -- .clau...      1     67   40.1%   145ms  █████░░░░░
 3.  rtk git commit                1     23   95.8%   170ms  ██░░░░░░░░
 4.  rtk git push                  1     20   90.9%    1.5s  █░░░░░░░░░
 5.  rtk git add .claude/s...      1     18   58.1%   133ms  █░░░░░░░░░
 6.  rtk git log -5 --oneline      1      0    0.0%    74ms  ░░░░░░░░░░
───────────────────────────────────────────────────────────────────────
```

### 삭제
동작만 중지:   
```
rtk init -g --uninstall 
```

설치파일(rtk) 삭제: cargo는 RUSK 설치 매니저(yum, npm과 유사)
```
cargo uninstall rtk
```
  
Mac에서 Homebrew로 설치했으면,  
```
brew uninstall rtk
```