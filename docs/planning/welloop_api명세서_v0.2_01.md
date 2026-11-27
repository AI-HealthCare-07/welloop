# WELLOOP API 명세서 v2.0 — 영역 01 (인증·회원·동의·알림)

## 공통 규칙

| 항목 | 규칙 |
|---|---|
| Base URL | `/api/v1` |
| 형식 | 요청·응답 모두 JSON (`Content-Type: application/json`) |
| 네이밍 | 모든 필드는 **`snake_case`**, ERD v2.0 컬럼명과 일치 |
| 인증 | `Authorization: Bearer {access_token}` (JWT). 관리자 API는 관리자 권한(`ADMIN`) 필요 |
| 날짜·시간 | 날짜·일시: ISO 8601 (`2026-11-26T09:00:00+09:00`), 시각(`time`): `HH:MM:SS` (`09:00:00`) |
| 의료 안전 원칙 | 비의료 건강관리 서비스 명시 및 진단·처방 오인 표현 금지 (`SR-011`, `SR-013`) |

### 공통 에러 응답 형식

```json
{
  "detail": "필수값 누락: gender",
  "code": "VALIDATION_ERROR"
}
```

| HTTP Status | 에러 코드 예시 | 의미 및 발생 상황 |
|---|---|---|
| `400 Bad Request` | `VALIDATION_ERROR` | 필수값 누락, 이메일·비밀번호 형식 오류, 허용되지 않은 Enum 값 |
| `401 Unauthorized` | `UNAUTHORIZED` | 토큰 없음·만료, 이메일·비밀번호 불일치 |
| `403 Forbidden` | `FORBIDDEN` / `CONSENT_REQUIRED` | 접근 권한 없음(타인 정보 접근 차단 `SR-003`), 필수 민감정보·AI 동의 미확보 |
| `404 Not Found` | `NOT_FOUND` | 존재하지 않는 리소스 ID |
| `409 Conflict` | `EMAIL_DUPLICATED` | 이미 가입된 이메일 |
| `423 Locked` | `ACCOUNT_LOCKED` | 로그인 연속 5회 실패로 계정 일시 잠금 (`SR-008`) |
| `500 Internal Server Error` | `INTERNAL_ERROR` | 서버 내부 처리 오류 (단, 외부 AI 장애 시 핵심 기능은 정상 유지 `NFR-102`) |

---

<!-- 01 START · 인증·회원·동의·알림 · 담당: 엄태은 -->
## 01. 인증 · 회원 · 동의 · 알림 설정

- **관련 테이블**: `users`, `consents`, `notification_settings`
- **관련 요구사항**: `REQ-AUTH-001~005`, `REQ-NOTI-001~002`, `SR-001~003`, `SR-008`, `SR-034`
- **공통 Enum 정의**:
  - `Gender`: `MALE` (남성 — C 분기 안내 대상) / `FEMALE` (여성)
  - `User_role`: `USER` / `ADMIN`
  - `Consent_type`: `HEALTH_DATA` (민감 건강정보 수집·활용) / `AI_PROCESSING` (AI·LLM 처리) / `OVERSEAS_TRANSFER` (국외 이전 — 외부 LLM 사용 시)
  - `Notification_type`: `CHALLENGE` (챌린지 실천 독려) / `HEALTH_LOG` (건강 기록 안내) / `WEEKLY_REPORT` (주간 요약 리포트) / `CHECKUP` (정기검진 시기 안내)

### 01 구역 API 목록 요약

| No | Method | Endpoint | 설명 | 우선순위 | 관련 요구사항 |
|---|---|---|---|---|---|
| 1 | `POST` | `/api/v1/auth/signup` | 회원가입 (성별 필수 수집) | P0 | REQ-AUTH-001, REQ-ASMT-001 |
| 2 | `POST` | `/api/v1/auth/login` | 로그인 (JWT 발급) | P0 | REQ-AUTH-002, SR-008 |
| 3 | `POST` | `/api/v1/auth/refresh` | 액세스 토큰 재발급 | P0 | REQ-AUTH-002 |
| 4 | `POST` | `/api/v1/auth/logout` | 로그아웃 (리프레시 토큰 폐기) | P0 | REQ-AUTH-002 |
| 5 | `GET` | `/api/v1/users/me` | 내 회원정보 조회 | P0 | REQ-AUTH-004, SR-003 |
| 6 | `PATCH` | `/api/v1/users/me` | 내 회원정보 수정 | TBD | REQ-AUTH-004, TBD-028 |
| 7 | `DELETE` | `/api/v1/users/me` | 회원 탈퇴 및 건강정보 처리 | TBD | REQ-AUTH-005, TBD-028·030 |
| 8 | `POST` | `/api/v1/consents` | 건강정보 수집·활용 등 동의/철회 저장 | P0 | REQ-AUTH-003, SR-001 |
| 9 | `GET` | `/api/v1/consents` | 내 동의 내역 최신 상태 조회 | P0 | REQ-AUTH-003, SR-001 |
| 10 | `GET` | `/api/v1/users/me/notification-settings` | 내 알림 설정 목록 조회 | P1 | REQ-NOTI-002 |
| 11 | `PUT` | `/api/v1/users/me/notification-settings` | 알림 여부·시간·요일 설정 저장 | P1 | REQ-NOTI-002, SR-034 |
| 12 | `GET` | `/api/v1/notifications` | 웹 내부 알림 목록 조회 | P1 | REQ-NOTI-001, REQ-NOTI-003~004 |
| 13 | `PATCH` | `/api/v1/notifications/{notification_id}/read` | 웹 내부 알림 읽음 처리 | P1 | REQ-NOTI-001 |

---

### 1. 회원가입 · P0
- **Method / Endpoint**: `POST /api/v1/auth/signup`
- **Description**: 이메일 기반으로 서비스 계정을 생성한다. 성별·연령에 따른 일반 가입 제한은 없으나, AI 모델 적용 대상 여부 및 A/B/C 분기 판정을 위해 `gender`와 `birth_date`를 필수로 수집한다(`REQ-AUTH-001`, `REQ-ASMT-001`, `SR-002`).
- **인증**: 불필요
- **Request Header**: `Content-Type: application/json`
- **Request Parameter**: -
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "Welloop!2345",
    "name": "김미영",
    "birth_date": "1976-05-14",
    "gender": "FEMALE",
    "terms_agreed": true,
    "privacy_agreed": true
  }
  ```
- **Response Body (`201 Created`)**:
  ```json
  {
    "user_id": 1,
    "email": "user@example.com",
    "name": "김미영",
    "birth_date": "1976-05-14",
    "gender": "FEMALE",
    "role": "USER",
    "created_at": "2026-11-26T10:00:00+09:00"
  }
  ```
- **Status Code**:
  - `201 Created`: 회원가입 성공
  - `400 Bad Request`: 필수값 누락, 이메일 형식 오류, 비밀번호 규칙 미충족(영문·숫자·특수문자 포함 8자 이상), 필수 약관(`terms_agreed`, `privacy_agreed`) 미동의 (`VALIDATION_ERROR`)
  - `409 Conflict`: 이미 가입된 이메일 (`EMAIL_DUPLICATED`)
- **관련 테이블 · 요구사항**: `users` · `REQ-AUTH-001`, `REQ-ASMT-001`, `SR-002`, `SR-008`, `TBD-027`
- **비고**:
  - 비밀번호는 복원 불가능한 단방향 해시(`bcrypt` 등)로 암호화하여 저장한다(`SR-008`).
  - 미성년자 가입 시 법정대리인 동의 절차 추가 여부는 법적 검토(`TBD-027`, `TBD-030`) 후 확정한다.
  - 가입 직후 `notification_settings` 기본값(기본 비활성 또는 기본 시간) 행을 함께 초기화할지 백엔드 구현 시 결정한다.

---

### 2. 로그인 (JWT 발급) · P0
- **Method / Endpoint**: `POST /api/v1/auth/login`
- **Description**: 이메일과 비밀번호를 검증하고 `access_token`과 `refresh_token`을 발급한다. 연속 5회 실패 시 10분간 로그인을 잠근다.
- **인증**: 불필요
- **Request Header**: `Content-Type: application/json`
- **Request Parameter**: -
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "Welloop!2345",
    "keep_login": true
  }
  ```
- **Response Body (`200 OK`)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "user_id": 1,
      "name": "김미영",
      "gender": "FEMALE",
      "role": "USER"
    }
  }
  ```
- **Status Code**:
  - `200 OK`: 로그인 성공 (`failed_login_count` 0으로 초기화)
  - `400 Bad Request`: 이메일 또는 비밀번호 누락 (`VALIDATION_ERROR`)
  - `401 Unauthorized`: 이메일·비밀번호 불일치 또는 탈퇴한 계정 (`UNAUTHORIZED`)
  - `423 Locked`: 비밀번호 5회 연속 오류로 계정 잠금 (`ACCOUNT_LOCKED`, 해제 시각 `locked_until` 반환)
- **관련 테이블 · 요구사항**: `users` · `REQ-AUTH-002`, `SR-008`
- **비고**: 운영 로그에 평문 비밀번호나 민감 토큰 전체가 기록되지 않도록 마스킹한다(`SR-004`).

---

### 3. 액세스 토큰 재발급 · P0
- **Method / Endpoint**: `POST /api/v1/auth/refresh`
- **Description**: 만료된 `access_token`을 유효한 `refresh_token`을 이용해 재발급한다.
- **인증**: 불필요 (`refresh_token` 검증)
- **Request Header**: `Content-Type: application/json`
- **Request Parameter**: -
- **Request Body**:
  ```json
  {
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }
  ```
- **Response Body (`200 OK`)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600
  }
  ```
- **Status Code**:
  - `200 OK`: 재발급 성공
  - `401 Unauthorized`: 유효하지 않거나 만료·폐기된 `refresh_token` (`UNAUTHORIZED`)
- **관련 테이블 · 요구사항**: `users` · `REQ-AUTH-002`, `SR-008`

---

### 4. 로그아웃 · P0
- **Method / Endpoint**: `POST /api/v1/auth/logout`
- **Description**: 현재 로그인 세션을 종료하고 서버 측 `refresh_token`을 무효화(폐기)한다.
- **인증**: 필요
- **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- **Request Parameter**: -
- **Request Body**:
  ```json
  {
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }
  ```
- **Response Body (`204 No Content`)**: (본문 없음)
- **Status Code**:
  - `204 No Content`: 로그아웃 성공
  - `401 Unauthorized`: 인증 토큰 없음 또는 만료 (`UNAUTHORIZED`)
- **관련 테이블 · 요구사항**: `users` · `REQ-AUTH-002`

---

### 5. 내 회원정보 조회 · P0
- **Method / Endpoint**: `GET /api/v1/users/me`
- **Description**: 로그인한 사용자 본인의 기본 프로필 정보를 조회한다. 타인의 정보는 조회할 수 없다(`SR-003`).
- **인증**: 필요
- **Request Header**: `Authorization: Bearer {access_token}`
- **Request Parameter**: -
- **Request Body**: -
- **Response Body (`200 OK`)**:
  ```json
  {
    "user_id": 1,
    "email": "user@example.com",
    "name": "김미영",
    "birth_date": "1976-05-14",
    "gender": "FEMALE",
    "role": "USER",
    "created_at": "2026-11-26T10:00:00+09:00"
  }
  ```
- **Status Code**:
  - `200 OK`: 조회 성공
  - `401 Unauthorized`: 토큰 없음·만료
- **관련 테이블 · 요구사항**: `users` · `REQ-AUTH-004`, `SR-003`

---

### 6. 내 회원정보 수정 · TBD
- **Method / Endpoint**: `PATCH /api/v1/users/me`
- **Description**: 본인의 이름 또는 비밀번호 등 허용된 계정 정보를 수정한다. 변경할 필드만 전달한다.
- **인증**: 필요
- **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- **Request Parameter**: -
- **Request Body**:
  ```json
  {
    "name": "김민정",
    "current_password": "Welloop!2345",
    "new_password": "NewPassword!987"
  }
  ```
- **Response Body (`200 OK`)**:
  ```json
  {
    "user_id": 1,
    "name": "김민정",
    "updated_at": "2026-11-26T11:20:00+09:00"
  }
  ```
- **Status Code**:
  - `200 OK`: 수정 성공
  - `400 Bad Request`: 수정할 값 없음, 새 비밀번호 형식 오류 (`VALIDATION_ERROR`)
  - `401 Unauthorized`: 토큰 만료 또는 비밀번호 변경 시 `current_password` 불일치 (`UNAUTHORIZED`)
- **관련 테이블 · 요구사항**: `users` · `REQ-AUTH-004`, `TBD-028`
- **비고**: `email`, `birth_date`, `gender`는 AI 모델 적용 조건 및 예측 이력 기준값이므로 임의 수정을 제한한다(오입력 정정 정책은 `TBD-028`에서 결정).

---

### 7. 회원 탈퇴 및 건강정보 처리 · TBD
- **Method / Endpoint**: `DELETE /api/v1/users/me`
- **Description**: 서비스에서 탈퇴하고 관련 법령 및 확정된 개인정보 처리 방침에 따라 계정을 비활성화(`is_deleted=true`)하며 민감 건강정보를 즉시 파기(또는 분리 처리)한다(`REQ-AUTH-005`).
- **인증**: 필요
- **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- **Request Parameter**: -
- **Request Body**:
  ```json
  {
    "password": "Welloop!2345"
  }
  ```
- **Response Body (`204 No Content`)**: (본문 없음)
- **Status Code**:
  - `204 No Content`: 탈퇴 및 데이터 파기 완료
  - `400 Bad Request`: 비밀번호 누락
  - `401 Unauthorized`: 토큰 만료 또는 비밀번호 불일치
- **관련 테이블 · 요구사항**: `users` 및 전 건강정보 관련 테이블 · `REQ-AUTH-005`, `TBD-028`, `TBD-030`
- **비고**: 관리자 통계(`REQ-ADMIN-002`)에 개인 식별 정보 없이 누적 탈퇴 수만 남길지 여부는 `TBD-030` 정책 확정 시 반영한다.

---

### 8. 건강정보 수집·활용 등 동의 저장 · P0
- **Method / Endpoint**: `POST /api/v1/consents`
- **Description**: 초기 건강 평가 및 AI 코칭 이용 전 필수적인 민감정보(건강정보) 수집·활용 동의 여부와 시점을 기록한다(`REQ-AUTH-003`, `SR-001`). 동의 철회 시에도 `agreed: false`로 새 이력을 남겨 감사 추적을 보존한다.
- **인증**: 필요
- **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- **Request Parameter**: -
- **Request Body**:
  ```json
  {
    "consents": [
      {
        "consent_type": "HEALTH_DATA",
        "version": "v2.0",
        "agreed": true
      },
      {
        "consent_type": "AI_PROCESSING",
        "version": "v2.0",
        "agreed": true
      }
    ]
  }
  ```
- **Response Body (`201 Created`)**:
  ```json
  {
    "items": [
      {
        "consent_id": 10,
        "consent_type": "HEALTH_DATA",
        "version": "v2.0",
        "agreed": true,
        "agreed_at": "2026-11-26T10:02:00+09:00"
      },
      {
        "consent_id": 11,
        "consent_type": "AI_PROCESSING",
        "version": "v2.0",
        "agreed": true,
        "agreed_at": "2026-11-26T10:02:00+09:00"
      }
    ]
  }
  ```
- **Status Code**:
  - `201 Created`: 동의 이력 저장 성공
  - `400 Bad Request`: 허용되지 않은 `consent_type` 또는 `version` 누락 (`VALIDATION_ERROR`)
  - `401 Unauthorized`: 토큰 없음·만료
- **관련 테이블 · 요구사항**: `consents` · `REQ-AUTH-003`, `SR-001`, `TBD-030`
- **비고**:
  - `HEALTH_DATA` 동의가 확보되지 않은(`agreed: false` 또는 미기록) 사용자가 초기 건강 평가(02 구역)나 건강 기록(04 구역) API를 호출하면 서버는 데이터를 수집하지 않고 `403 Forbidden`(`CONSENT_REQUIRED`)을 반환한다(`REQ-AUTH-003`).
  - 여러 항목을 한 화면에서 일괄 동의할 수 있도록 배열(`consents[]`) 입력을 지원한다.

---

### 9. 내 동의 내역 최신 상태 조회 · P0
- **Method / Endpoint**: `GET /api/v1/consents`
- **Description**: 동의 유형(`consent_type`)별 가장 최근 동의 상태와 일시를 조회한다. 프론트엔드에서 초기 건강 평가 진입 가능 여부 및 설정 화면의 동의 철회 상태를 표시할 때 사용한다.
- **인증**: 필요
- **Request Header**: `Authorization: Bearer {access_token}`
- **Request Parameter**: -
- **Request Body**: -
- **Response Body (`200 OK`)**:
  ```json
  {
    "items": [
      {
        "consent_type": "HEALTH_DATA",
        "version": "v2.0",
        "agreed": true,
        "agreed_at": "2026-11-26T10:02:00+09:00"
      },
      {
        "consent_type": "AI_PROCESSING",
        "version": "v2.0",
        "agreed": false,
        "agreed_at": "2026-11-26T10:02:00+09:00"
      }
    ]
  }
  ```
- **Status Code**:
  - `200 OK`: 조회 성공
  - `401 Unauthorized`: 토큰 없음·만료
- **관련 테이블 · 요구사항**: `consents` · `REQ-AUTH-003`, `SR-001`

---

### 10. 내 알림 설정 목록 조회 · P1
- **Method / Endpoint**: `GET /api/v1/users/me/notification-settings`
- **Description**: 알림 유형(`CHALLENGE`, `HEALTH_LOG`, `WEEKLY_REPORT`, `CHECKUP`)별 활성화 여부, 지정 시각, 수신 요일 플래그를 조회한다(`REQ-NOTI-002`).
- **인증**: 필요
- **Request Header**: `Authorization: Bearer {access_token}`
- **Request Parameter**: -
- **Request Body**: -
- **Response Body (`200 OK`)**:
  ```json
  {
    "items": [
      {
        "notification_type": "CHALLENGE",
        "is_enabled": true,
        "notification_time": "09:00:00",
        "ntf_flg_sun": false,
        "ntf_flg_mon": true,
        "ntf_flg_tue": true,
        "ntf_flg_wed": true,
        "ntf_flg_thu": true,
        "ntf_flg_fri": true,
        "ntf_flg_sat": false
      },
      {
        "notification_type": "HEALTH_LOG",
        "is_enabled": true,
        "notification_time": "20:00:00",
        "ntf_flg_sun": true,
        "ntf_flg_mon": true,
        "ntf_flg_tue": true,
        "ntf_flg_wed": true,
        "ntf_flg_thu": true,
        "ntf_flg_fri": true,
        "ntf_flg_sat": true
      }
    ]
  }
  ```
- **Status Code**:
  - `200 OK`: 조회 성공
  - `401 Unauthorized`: 토큰 없음·만료
- **관련 테이블 · 요구사항**: `notification_settings` · `REQ-NOTI-002`
- **비고**: ERD v2.0의 `notification_settings` 컬럼 구조(`notification_time`, `ntf_flg_sun` ~ `ntf_flg_sat`)와 1:1 매핑된다.

---

### 11. 알림 여부·시간·요일 설정 저장 · P1
- **Method / Endpoint**: `PUT /api/v1/users/me/notification-settings`
- **Description**: 사용자가 과도한 실천 압박 없이 원하는 시간과 빈도(요일 조합)로만 알림을 받을 수 있도록 알림 설정을 변경한다(`REQ-NOTI-002`, `SR-034`).
- **인증**: 필요
- **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- **Request Parameter**: -
- **Request Body**:
  ```json
  {
    "settings": [
      {
        "notification_type": "CHALLENGE",
        "is_enabled": true,
        "notification_time": "09:00:00",
        "ntf_flg_sun": false,
        "ntf_flg_mon": true,
        "ntf_flg_tue": false,
        "ntf_flg_wed": true,
        "ntf_flg_thu": false,
        "ntf_flg_fri": true,
        "ntf_flg_sat": false
      }
    ]
  }
  ```
- **Response Body (`200 OK`)**:
  ```json
  {
    "updated_count": 1,
    "updated_at": "2026-11-26T11:45:00+09:00"
  }
  ```
- **Status Code**:
  - `200 OK`: 설정 저장 성공
  - `400 Bad Request`: 시간 형식(`HH:MM:SS`) 오류, 허용되지 않은 `notification_type`, `is_enabled: true`인데 모든 요일이 `false`인 경우 (`VALIDATION_ERROR`)
  - `401 Unauthorized`: 토큰 없음·만료
- **관련 테이블 · 요구사항**: `notification_settings` · `REQ-NOTI-002`, `SR-034`
- **비고**: 복합 PK `(user_id, notification_type)` 기준으로 Upsert(있으면 갱신, 없으면 생성) 처리한다.

---

### 12. 웹 내부 알림 목록 조회 · P1
- **Method / Endpoint**: `GET /api/v1/notifications`
- **Description**: 웹 서비스 내부에서 사용자에게 발송된 챌린지 독려, 건강 기록 안내, 정기검진 시기 안내, 주간 리포트 알림 목록을 최신순으로 조회한다(`REQ-NOTI-001`, `REQ-NOTI-003~004`).
- **인증**: 필요
- **Request Header**: `Authorization: Bearer {access_token}`
- **Request Parameter (Query)**:
  - `unread_only` (boolean, 선택, 기본 `false`): 읽지 않은 알림만 필터링
  - `page` (integer, 선택, 기본 `1`)
  - `size` (integer, 선택, 기본 `20`)
- **Request Body**: -
- **Response Body (`200 OK`)**:
  ```json
  {
    "unread_count": 1,
    "items": [
      {
        "notification_id": 105,
        "notification_type": "CHALLENGE",
        "title": "오늘의 걷기 습관을 가볍게 시작해 볼까요?",
        "body": "점심 식사 후 10분 산책만으로도 좋은 시작이 됩니다.",
        "target_path": "/challenges",
        "is_read": false,
        "created_at": "2026-11-26T09:00:00+09:00"
      },
      {
        "notification_id": 98,
        "notification_type": "CHECKUP",
        "title": "정기 혈중 지질검사 시기를 확인해 보세요",
        "body": "마지막 검사일로부터 6개월이 지났습니다. 의료진 권고 주기에 맞춰 검진을 챙겨보세요.",
        "target_path": "/lipid-records",
        "is_read": true,
        "created_at": "2026-11-20T09:00:00+09:00"
      }
    ],
    "total": 2,
    "page": 1,
    "size": 20
  }
  ```
- **Status Code**:
  - `200 OK`: 조회 성공
  - `401 Unauthorized`: 토큰 없음·만료
- **관련 테이블 · 요구사항**: `notifications`(신규/로그 테이블 확인 필요) · `REQ-NOTI-001`, `REQ-NOTI-003`, `REQ-NOTI-004`, `SR-025`, `SR-034`
- **비고**: 알림 문구는 죄책감이나 압박감을 유발하는 표현을 배제한다(`SR-034`).

---

### 13. 웹 내부 알림 읽음 처리 · P1
- **Method / Endpoint**: `PATCH /api/v1/notifications/{notification_id}/read`
- **Description**: 특정 웹 내부 알림을 읽음(`is_read: true`) 상태로 변경한다. (`notification_id` 대신 `all` 전달 또는 별도 일괄 읽음 엔드포인트 지원 가능)
- **인증**: 필요
- **Request Header**: `Authorization: Bearer {access_token}`
- **Request Parameter (Path)**: `notification_id` (bigint)
- **Request Body**: -
- **Response Body (`200 OK`)**:
  ```json
  {
    "notification_id": 105,
    "is_read": true,
    "read_at": "2026-11-26T12:10:00+09:00"
  }
  ```
- **Status Code**:
  - `200 OK`: 읽음 처리 성공
  - `401 Unauthorized`: 토큰 없음·만료
  - `403 Forbidden`: 본인의 알림이 아님 (`SR-003`)
  - `404 Not Found`: 존재하지 않는 알림 ID
- **관련 테이블 · 요구사항**: `notifications` · `REQ-NOTI-001`, `SR-003`

---

### 📋 01 구역 미확정 사항(TBD) 및 팀 확인 포인트

| # | 항목 | 관련 TBD / REQ | 확인 대상 및 내용 |
|---|---|---|---|
| 1 | 미성년자 가입·동의 절차 | `TBD-027`, `TBD-030` | 성별·연령 일반 제한 없음 확정. 만 14세 미만 등 미성년자 가입 시 법정대리인 동의 절차 추가 여부 및 생년월일 검증 정책 확인 필요 (기획·운영 정책) |
| 2 | 동의 항목(`Consent_type`) 세분화 | `TBD-030`, `REQ-AUTH-003` | ERD v2.0의 `Consent_type`에서 `FAMILY_SHARE` 제거 후 `HEALTH_DATA` 외에 `AI_PROCESSING`, `OVERSEAS_TRANSFER` 분리 여부 확정 필요 (백엔드·기획) |
| 3 | 회원 수정·탈퇴 우선순위 및 파기 범위 | `TBD-028`, `TBD-030` | `REQ-AUTH-004~005`의 MVP 포함 여부 및 탈퇴 시 데이터 즉시 물리 삭제(Hard Delete) vs 비식별 통계 보존 범위 확인 필요 |
| 4 | 웹 내부 알림 발송 내역 저장 테이블 | `REQ-NOTI-001` | ERD v2.0에 `notification_settings`(설정) 외에 실제 발송된 알림함을 담는 `notifications` 테이블 추가 여부 확인 필요 (ERD·백엔드) |

<!-- 01 END -->