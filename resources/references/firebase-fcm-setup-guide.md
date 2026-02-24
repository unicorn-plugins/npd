# Firebase Cloud Messaging (FCM) 설정 가이드

## 목적

Firebase Cloud Messaging을 사용한 웹 푸시 알림 구현 시, 필요한 3가지 크리덴셜(Firebase Config, VAPID Key, Service Account Key)을 발급받는 절차를 안내한다.

## 필요한 크리덴셜 요약

| 크리덴셜 | 용도 | 사용 위치 |
|----------|------|----------|
| Firebase Config | Firebase SDK 초기화 | 프론트엔드 |
| VAPID Key (웹푸시인증서 키) | 브라우저 푸시 구독 등록 (`getToken()`) | 프론트엔드 |
| Service Account Key (JSON) | Firebase Admin SDK 인증 (푸시 발송) | 백엔드 |

## 사전 준비

1. [Firebase Console](https://console.firebase.google.com/) 접속 → Google 계정으로 로그인
2. **프로젝트 추가** 클릭 → 프로젝트 이름 입력 → 생성 완료

> 기존 Firebase 프로젝트가 있으면 해당 프로젝트를 선택한다.

---

## 1. Firebase Config 발급

Firebase Config는 프론트엔드에서 Firebase SDK를 초기화할 때 사용하는 설정 값이다.

### 발급 절차

1. [Firebase Console](https://console.firebase.google.com/) → 프로젝트 선택
2. 좌측 상단 **⚙ 톱니바퀴** → **프로젝트 설정**
3. **일반** 탭 → 하단 **내 앱** 섹션
4. 앱이 없으면 **웹 앱 추가** (</> 아이콘) 클릭:
   - 앱 닉네임 입력 (예: `travel-planner-web`)
   - **Firebase Hosting 설정** 체크 해제 (별도 호스팅 사용 시)
   - **앱 등록** 클릭
5. **SDK 설정 및 구성** 섹션에서 `firebaseConfig` 객체 확인

### 발급 결과

```javascript
const firebaseConfig = {
  apiKey: "AIzaSy...",
  authDomain: "{project-id}.firebaseapp.com",
  projectId: "{project-id}",
  storageBucket: "{project-id}.firebasestorage.app",
  messagingSenderId: "1234567890",
  appId: "1:1234567890:web:abcdef123456"
};
```

### 환경변수 설정

프론트엔드 `.env` 또는 `runtime-env.js`에 아래 값을 설정한다:

```dotenv
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN={project-id}.firebaseapp.com
FIREBASE_PROJECT_ID={project-id}
FIREBASE_STORAGE_BUCKET={project-id}.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=1234567890
FIREBASE_APP_ID=1:1234567890:web:abcdef123456
```

---

## 2. VAPID Key (웹푸시인증서 키) 발급

VAPID Key는 브라우저에서 푸시 알림 구독을 등록할 때 사용하는 공개 키이다. `getToken({ vapidKey: "..." })` 호출 시 필요하다.

### 발급 절차

1. [Firebase Console](https://console.firebase.google.com/) → 프로젝트 선택
2. 좌측 상단 **⚙ 톱니바퀴** → **프로젝트 설정**
3. **클라우드 메시징** 탭 선택
4. **웹 푸시 인증서** 섹션에서:
   - 기존 키가 있으면 해당 키 사용
   - 없으면 **키 쌍 생성** 클릭
5. 생성된 **키 쌍** (긴 문자열)을 복사

### 발급 결과

```
BLxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> 약 88자의 Base64 문자열이다.

### 환경변수 설정

프론트엔드 `.env` 또는 `runtime-env.js`에 추가:

```dotenv
FIREBASE_VAPID_KEY=BLxxxxxxxx...
```

---

## 3. Service Account Key (JSON) 발급

Service Account Key는 백엔드에서 Firebase Admin SDK를 초기화하여 푸시 메시지를 발송할 때 사용하는 인증 파일이다.

### 발급 절차

1. [Firebase Console](https://console.firebase.google.com/) → 프로젝트 선택
2. 좌측 상단 **⚙ 톱니바퀴** → **프로젝트 설정**
3. **서비스 계정** 탭 선택
4. **Firebase Admin SDK** 섹션에서:
   - 언어 선택: Java / Python / Node.js 등 (코드 예시 참조용)
   - **새 비공개 키 생성** 클릭
5. JSON 파일이 자동 다운로드됨

### 발급 결과

다운로드된 JSON 파일 내용 (예: `{project-id}-firebase-adminsdk-xxxxx.json`):

```json
{
  "type": "service_account",
  "project_id": "{project-id}",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxxxx@{project-id}.iam.gserviceaccount.com",
  "client_id": "1234567890",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

### 환경변수 설정

**방법 A: 파일 경로로 지정** (권장)

```dotenv
GOOGLE_APPLICATION_CREDENTIALS=./firebase-service-account.json
```

**방법 B: JSON 내용을 환경변수로 지정**

```dotenv
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}
```

### 보안 주의사항

- **JSON 파일을 Git에 커밋하지 않는다.** `.gitignore`에 반드시 추가:
  ```
  *-firebase-adminsdk-*.json
  firebase-service-account.json
  ```
- `.env.example`에는 키 이름만 포함하고 실제 값은 제외한다
- CI/CD 환경에서는 Secret Manager 또는 환경변수로 주입한다

---

## 확인 체크리스트

- [ ] Firebase 프로젝트 생성 완료
- [ ] 웹 앱 등록 및 Firebase Config 확보
- [ ] VAPID Key (웹푸시인증서 키) 생성 완료
- [ ] Service Account Key JSON 다운로드 완료
- [ ] JSON 파일이 `.gitignore`에 등록됨
- [ ] 프론트엔드 `.env`에 Firebase Config + VAPID Key 설정
- [ ] 백엔드 `.env`에 Service Account Key 경로 설정
