# WELLOOP API 명세서 v2.0 — 영역 06 (관리자 기능)

## 06. 관리자 (통계 집계 · 모니터링 · 마스터 및 안전 기준 관리)

* **관련 테이블**: `users`, `risk_predictions`, `challenges`, `safety_keywords`, `risk_thresholds`, `admin_logs`
* **관련 요구사항**: `REQ-ADMIN-001~005`, `NFR-105`, `NFR-107~108`, `SR-004`, `SR-008~009`, `SR-030`, `SR-033`, `SR-035`
* **공통 Enum 정의**:
  * `User_role`: `ADMIN`
  * `Safety_keyword_kind`: `EMERGENCY` / `MENTAL_CRISIS` / `MEDICAL_BAN` / `HORMONE_BAN`
  * `Keyword_severity`: `HIGH` / `MEDIUM`
  * `System_component`: `API_SERVER` / `ML_PREDICTION` / `LLM_COACH` / `FOOD_VISION` / `DATABASE`

### 06 구역 API 목록 요약

| No | Method | Endpoint | 설명 | 우선순위 | 관련 요구사항 |
|---|---|---|---|---|---|
| 54 | `POST` | `/api/v1/admin/login` | 관리자 로그인 (`ADMIN` 역할 검증 및 전용 JWT 발급) | P1 | REQ-ADMIN-001, SR-008 |
| 55 | `GET` | `/api/v1/admin/stats/users` | 사용자 증감 및 A/B/C 분기·적용 사유 코드(`reason_code`)별 집계 조회 | P1 | REQ-ADMIN-002, SR-009 |
| 56 | `GET` | `/api/v1/admin/stats/challenges` | 카테고리·챌린지별 참여율 및 달성률 집계 조회 | P1 | REQ-ADMIN-003, REQ-CHAL-004 |
| 57 | `GET` | `/api/v1/admin/stats/llm-usage` | LLM 호출 횟수·토큰 사용량·비용·지연시간 집계 조회 | P1 | REQ-ADMIN-004, NFR-108, SR-009 |
| 58 | `GET` | `/api/v1/admin/monitoring/system` | 시스템 오류율·응답시간 및 외부 AI 연동 상태 모니터링 | P1 | REQ-ADMIN-005, NFR-101~102, NFR-105 |
| 59 | `GET` | `/api/v1/admin/monitoring/error-logs` | 마스킹된 운영 오류 로그 목록 조회 (민감정보 제외) | P1 | REQ-ADMIN-005, NFR-105, SR-004 |
| 60 | `GET` | `/api/v1/admin/challenges` | 챌린지 마스터 카탈로그 목록 조회 | P1 | REQ-CHAL-002 |
| 61 | `POST` | `/api/v1/admin/challenges` | 신규 챌린지 마스터 등록 (변경 이력 기록) | P1 | REQ-CHAL-002, NFR-107 |
| 62 | `PATCH` | `/api/v1/admin/challenges/{challenge_id}` | 챌린지 마스터 수정 및 활성/비활성 처리 | P1 | REQ-CHAL-002, NFR-107 |
| 63 | `GET` | `/api/v1/admin/safety-keywords` | 의료·응급 안전 키워드 목록 조회 | P1 | SR-030, SR-033, NFR-107 |
| 64 | `POST` | `/api/v1/admin/safety-keywords` | 의료·응급 안전 키워드 등록 (감사 로그 기록) | P1 | SR-030, SR-033, NFR-107 |
| 65 | `PATCH` | `/api/v1/admin/safety-keywords/{keyword_id}` | 의료·응급 안전 키워드 수정·비활성화 | P1 | SR-030, SR-033, NFR-107 |
| 66 | `DELETE` | `/api/v1/admin/safety-keywords/{keyword_id}` | 의료·응급 안전 키워드 삭제 | P1 | SR-030, SR-033, NFR-107 |
| 67 | `GET` | `/api/v1/admin/operational-policies` | 주요 운영·안전 기준 조회 | TBD | NFR-107, REQ-PRED-001 |
| 68 | `PATCH` | `/api/v1/admin/operational-policies/{policy_id}` | 운영·안전 기준 변경 및 변경 사유 이력 저장 | TBD | NFR-107, SR-035 |

### 54. 관리자 로그인 · P1

* **Method / Endpoint**: `POST /api/v1/admin/login`
* **Description**: 관리자 계정(`users.role == "ADMIN"`)을 인증하고 전용 JWT를 발급한다(`REQ-ADMIN-001`).
* **인증**: 불필요
* **Request Header**: `Content-Type: application/json`
* **Request Body**:

  ```json
  {
    "email": "admin@welloop.example.com",
    "password": "AdminSecure!2026"
  }
  ```

* **Response Body (`200 OK`)**:

  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600,
    "admin": { "user_id": 999, "name": "운영관리자", "role": "ADMIN" }
  }
  ```

* **Status Code**: `200 OK` / `400 Bad Request` / `401 Unauthorized` / `403 Forbidden` / `423 Locked`
* **관련 테이블 · 요구사항**: `users`, `admin_logs` · `REQ-ADMIN-001`, `SR-008`

### 55. 사용자 증감 및 A/B/C 분기·적용 사유 코드별 집계 조회 · P1

* **Method / Endpoint**: `GET /api/v1/admin/stats/users`
* **Description**: 지정한 기간 동안의 사용자 증감 현황과 A/B/C 서비스 분기 분포, **모델별(`MODEL_1`/`MODEL_2`) 분포 및 적용 사유 코드(`Branch_reason_code`)별 집계 수**를 조회한다(`REQ-ADMIN-002`). 개인 식별 정보나 개별 건강 수치는 일절 포함하지 않는다(`SR-009`).
* **인증**: 관리자 (`ADMIN`)
* **Request Header**: `Authorization: Bearer {admin_access_token}`
* **Request Parameter (Query)**: `from_date` (`YYYY-MM-DD`, 필수), `to_date` (`YYYY-MM-DD`, 필수), `interval` (`DAY` | `WEEK` | `MONTH`, 기본 `DAY`)
* **Response Body (`200 OK`)**:

  ```json
  {
    "period": {
      "from_date": "2026-11-01",
      "to_date": "2026-11-26"
    },
    "interval": "DAY",
    "user_summary": {
      "total_users": 540,
      "new_users": 62,
      "withdrawn_users": 4,
      "active_users": 318,
      "assessment_completed_users": 490
    },
    "branch_distribution": {
      "BRANCH_A": 185,
      "BRANCH_B": 195,
      "BRANCH_C": 110
    },
    "model_distribution": {
      "MODEL_1": 195,
      "MODEL_2": 0
    },
    "reason_code_counts": {
      "MODEL_APPROVAL_PENDING": 195,
      "ELIGIBLE_APPROVED": 0,
      "LDL_MISSING": 179,
      "LDL_TG_OVER_400": 6,
      "EXISTING_HIGH_LDL": 36,
      "LDL_OVER_160": 6,
      "MALE": 21,
      "HORMONE_THERAPY": 18,
      "SURGERY": 12,
      "MODEL_UNVERIFIED": 10,
      "OUT_OF_AGE_RANGE": 5,
      "MENOPAUSE_UNKNOWN": 2
    },
    "series": [
      { "date": "2026-11-25", "new_users": 3, "withdrawn_users": 0, "active_users": 142 },
      { "date": "2026-11-26", "new_users": 5, "withdrawn_users": 1, "active_users": 156 }
    ]
  }
  ```

* **Status Code**: `200 OK` / `400 Bad Request` / `401 Unauthorized` / `403 Forbidden`
* **관련 테이블 · 요구사항**: `users`, `risk_predictions` · `REQ-ADMIN-002`, `REQ-PRED-011`, `SR-009`

### 56. 카테고리·챌린지별 참여율 및 달성률 집계 조회 · P1

* **Method / Endpoint**: `GET /api/v1/admin/stats/challenges`
* **Description**: 7대 건강관리 영역 및 개별 챌린지별 참여율·주간 평균 달성률을 집계 조회한다(`REQ-ADMIN-003`).
* **인증**: 관리자 (`ADMIN`)
* **Request Header**: `Authorization: Bearer {admin_access_token}`
* **Request Parameter (Query)**: `from_date` (필수), `to_date` (필수), `category` (선택)
* **Response Body (`200 OK`)**: `overall`, `by_category[]`, `top_challenges[]` 반환
* **Status Code**: `200 OK` / `400 Bad Request` / `401 Unauthorized` / `403 Forbidden`
* **관련 테이블 · 요구사항**: `challenges`, `daily_challenges`, `user_streaks` · `REQ-ADMIN-003`, `REQ-CHAL-004`

### 57. LLM 사용량 및 비용 조회 · P1

* **Method / Endpoint**: `GET /api/v1/admin/stats/llm-usage`
* **Description**: LLM 기능의 기간별 호출 횟수, 입·출력 토큰 수, 추정 비용(USD), 지연시간, 안전 가드레일 차단 건수를 조회한다(`REQ-ADMIN-004`, `NFR-108`).
* **인증**: 관리자 (`ADMIN`)
* **Request Header**: `Authorization: Bearer {admin_access_token}`
* **Request Parameter (Query)**: `from_date` (필수), `to_date` (필수), `group_by` (`DAY` | `FEATURE` | `MODEL`, 기본 `FEATURE`)
* **Response Body (`200 OK`)**: `budget_status`, `totals`, `items[]` 반환
* **Status Code**: `200 OK` / `400 Bad Request` / `401 Unauthorized` / `403 Forbidden`
* **관련 테이블 · 요구사항**: `admin_logs` · `REQ-ADMIN-004`, `NFR-108`, `SR-009`

### 58. 시스템 운영 현황 모니터링 · P1

* **Method / Endpoint**: `GET /api/v1/admin/monitoring/system`
* **Description**: API 응답시간(P95), 외부 연동 상태, 예측 실패 대체 경로(`PREDICTION_FAILED`) 및 응급 안전 알림 발동 건수를 조회한다(`REQ-ADMIN-005`, `NFR-105`).
* **인증**: 관리자 (`ADMIN`)
* **Request Header**: `Authorization: Bearer {admin_access_token}`
* **Request Parameter (Query)**: `window` (`1h` | `24h` | `7d`, 기본 `24h`)
* **Response Body (`200 OK`)**: `components[]`, `safety_and_fallback_counters` 반환
* **Status Code**: `200 OK` / `401 Unauthorized` / `403 Forbidden`
* **관련 테이블 · 요구사항**: `admin_logs` · `REQ-ADMIN-005`, `NFR-101~102`, `NFR-105`

### 59. 마스킹된 운영 오류 로그 목록 조회 · P1

* **Method / Endpoint**: `GET /api/v1/admin/monitoring/error-logs`
* **Description**: 개인·민감정보가 비식별화/마스킹 처리된 운영 오류 로그를 최신순으로 조회한다(`NFR-105`, `SR-004`).
* **인증**: 관리자 (`ADMIN`)
* **Request Header**: `Authorization: Bearer {admin_access_token}`
* **Request Parameter (Query)**: `component` (선택), `level` (`WARN` | `ERROR`, 기본 `ERROR`), `page` (기본 `1`), `size` (기본 `20`)
* **Response Body (`200 OK`)**: 마스킹된 `items[]` 반환
* **Status Code**: `200 OK` / `401 Unauthorized` / `403 Forbidden`
* **관련 테이블 · 요구사항**: `admin_logs` · `REQ-ADMIN-005`, `NFR-105`, `SR-004`

### 60. 챌린지 마스터 카탈로그 목록 조회 · P1

* **Method / Endpoint**: `GET /api/v1/admin/challenges`

* **Description**: 관리자가 시스템에 등록된 7대 영역 챌린지 마스터 카탈로그(활성·비활성 포함, 단계별 목표 및 안전 제외 조건 포함)를 조회한다(`REQ-CHAL-002`).

* **인증**: 관리자 (`ADMIN`)

* **Request Header**: `Authorization: Bearer {admin_access_token}`

* **Request Parameter (Query)**:

  * `category` (`Challenge_category`, 선택): 특정 건강관리 영역 필터링 (`DIET` | `ACTIVITY` | `WEIGHT_WAIST` | `SMOKE_DRINK` | `VITAMIN_D_OUTDOOR` | `MENOPAUSE_SYMPTOM` | `HEALTH_MONITORING`)

  * `is_active` (boolean, 선택): 활성 상태 필터링 (`true` | `false`, 미지정 시 전체)

  * `page` (integer, 선택, 기본 `1`)

  * `size` (integer, 선택, 기본 `20`)

* **Request Body**: -

* **Response Body (`200 OK`)**:

  ```json
  {
    "items": [
      {
        "challenge_id": 202,
        "code": "ACT-02",
        "category": "ACTIVITY",
        "title": "10분 이상 빠르게 걷기",
        "description": "중강도 유산소 활동을 주간 목표 시간만큼 나누어 실천합니다.",
        "challenge_cycle": "WEEKLY",
        "goal_type": "WEEKLY_TOTAL",
        "level_targets": {
          "level_1": 90,
          "level_2": 120,
          "level_3": 150,
          "unit": "분"
        },
        "safety_exclusion_rules": ["PROHIBITED", "SEATED_ONLY", "UNKNOWN"],
        "is_active": true,
        "updated_at": "2026-11-26T10:00:00+09:00"
      }
    ],
    "total": 28,
    "page": 1,
    "size": 20
  }
  ```

* **Status Code**:

  * `200 OK`: 조회 성공

  * `400 Bad Request`: 허용되지 않은 `category` 또는 페이지 파라미터 오류 (`VALIDATION_ERROR`)

  * `401 Unauthorized`: 토큰 없음·만료

  * `403 Forbidden`: 관리자 권한(`ADMIN`) 없음

* **관련 테이블 · 요구사항**: `challenges` · `REQ-CHAL-002`, `REQ-ADMIN-001`

### 61. 신규 챌린지 마스터 등록 · P1

* **Method / Endpoint**: `POST /api/v1/admin/challenges`

* **Description**: 검증된 임상 지침에 기반한 신규 생활습관 챌린지 마스터 항목을 등록하고 관리자 감사 로그(`admin_logs`)에 변경 이력을 남긴다(`REQ-CHAL-002`, `SR-017`, `NFR-107`).

* **인증**: 관리자 (`ADMIN`)

* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {admin_access_token}`

* **Request Parameter**: -

* **Request Body**:

  ```json
  {
    "code": "DIET-05",
    "category": "DIET",
    "title": "통곡물·잡곡밥으로 하루 1끼 이상 바꾸기",
    "description": "정제 탄수화물 대신 식이섬유가 풍부한 통곡물을 섭취해 LDL 관리에 도움을 줍니다.",
    "challenge_cycle": "WEEKLY",
    "goal_type": "WEEKLY_DAYS",
    "level_targets": {
      "level_1": 3,
      "level_2": 5,
      "level_3": 7,
      "unit": "일/주"
    },
    "safety_exclusion_rules": [],
    "clinical_guideline_ref": "한국지질·동맥경화학회 이상지질혈증 진료지침 제5판",
    "is_active": true,
    "change_reason": "식이섬유 섭취 증진 신규 주간 챌린지 추가"
  }
  ```

* **Response Body (`201 Created`)**:

  ```json
  {
    "challenge_id": 105,
    "code": "DIET-05",
    "title": "통곡물·잡곡밥으로 하루 1끼 이상 바꾸기",
    "is_active": true,
    "created_at": "2026-11-27T15:30:00+09:00"
  }
  ```

* **Status Code**:

  * `201 Created`: 등록 성공

  * `400 Bad Request`: 필수값(`code`, `category`, `challenge_cycle`, `goal_type`, `change_reason` 등) 누락, 단계별 목표치 역전(`level_1 > level_2`), 임상 안전 기준 위반 항목(예: 오메가-3·비타민 D 보충제 복용 강제 `SR-019`, `SR-022`) (`VALIDATION_ERROR`)

  * `401 Unauthorized`: 토큰 없음·만료

  * `403 Forbidden`: 관리자 권한 없음

  * `409 Conflict`: 이미 존재하는 챌린지 `code` 또는 `title` (`CHALLENGE_DUPLICATED`)

* **관련 테이블 · 요구사항**: `challenges`, `admin_logs` · `REQ-CHAL-002`, `SR-017~023`, `NFR-107`

### 62. 챌린지 마스터 수정 및 활성/비활성 처리 · P1

* **Method / Endpoint**: `PATCH /api/v1/admin/challenges/{challenge_id}`

* **Description**: 기존 챌린지의 문구·목표 수치·안전 제외 규칙 또는 노출 여부(`is_active`)를 수정한다. 기존 사용자의 과거 달성 이력(`daily_challenges`, `activity_logs`) 무결성 보존을 위해 물리 삭제(`DELETE`) 대신 `is_active: false` 비활성화를 원칙으로 하며, 변경 전·후 값과 사유를 `admin_logs`에 기록한다(`NFR-107`).

* **인증**: 관리자 (`ADMIN`)

* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {admin_access_token}`

* **Request Parameter (Path)**: `challenge_id` (bigint)

* **Request Body**:

  ```json
  {
    "title": "통곡물·잡곡밥 하루 1끼 실천하기",
    "is_active": false,
    "change_reason": "유사 식습관 챌린지(DIET-02)와 통합 운영을 위한 신규 배정 중지"
  }
  ```

* **Response Body (`200 OK`)**:

  ```json
  {
    "challenge_id": 105,
    "code": "DIET-05",
    "title": "통곡물·잡곡밥 하루 1끼 실천하기",
    "is_active": false,
    "updated_at": "2026-11-27T15:35:00+09:00"
  }
  ```

* **Status Code**:

  * `200 OK`: 수정 성공

  * `400 Bad Request`: 수정할 필드 없음 또는 `change_reason` 누락 (`VALIDATION_ERROR`)

  * `401 Unauthorized`: 토큰 없음·만료

  * `403 Forbidden`: 관리자 권한 없음

  * `404 Not Found`: 존재하지 않는 `challenge_id`

* **관련 테이블 · 요구사항**: `challenges`, `admin_logs` · `REQ-CHAL-002`, `NFR-107`

* **비고**: `is_active: false` 처리 시 신규 추천·직접 선택 목록에서는 즉시 제외되나, 이번 주에 이미 배정받아 진행 중인 사용자의 챌린지는 이번 주 종료 시점까지 유지할지 정책(`TBD-015`)에 따라 처리한다.

### 63. 의료·응급 안전 키워드 목록 조회 · P1

* **Method / Endpoint**: `GET /api/v1/admin/safety-keywords`

* **Description**: LLM 코칭 및 사용자 입력 텍스트 검사에 즉시 적용되는 규칙 기반 안전장치 키워드(`EMERGENCY` 119 안내, `MENTAL_CRISIS` 109 안내, `MEDICAL_BAN` 진단·처방 차단, `HORMONE_BAN` 호르몬제 권고 차단) 목록을 조회한다(`SR-030`, `SR-033`).

* **인증**: 관리자 (`ADMIN`)

* **Request Header**: `Authorization: Bearer {admin_access_token}`

* **Request Parameter (Query)**:

  * `kind` (`Safety_keyword_kind`, 선택): `EMERGENCY` | `MENTAL_CRISIS` | `MEDICAL_BAN` | `HORMONE_BAN`

  * `is_active` (boolean, 선택)

  * `page` (integer, 선택, 기본 `1`)

  * `size` (integer, 선택, 기본 `20`)

* **Request Body**: -

* **Response Body (`200 OK`)**:

  ```json
  {
    "items": [
      {
        "keyword_id": 1,
        "keyword": "가슴 통증",
        "kind": "EMERGENCY",
        "severity": "HIGH",
        "mapped_alert_type": "EMERGENCY_119",
        "guide_message": "즉시 119 신고 또는 가까운 응급실 방문을 우선 안내합니다.",
        "is_active": true,
        "updated_at": "2026-11-26T09:00:00+09:00"
      },
      {
        "keyword_id": 14,
        "keyword": "호르몬제 추천",
        "kind": "HORMONE_BAN",
        "severity": "HIGH",
        "mapped_alert_type": null,
        "guide_message": "질환 예방 목적의 호르몬 요법 시작·중단·변경은 권고하지 않으며 담당 의료진 상담으로 안내합니다.",
        "is_active": true,
        "updated_at": "2026-11-26T09:00:00+09:00"
      }
    ],
    "total": 2,
    "page": 1,
    "size": 20
  }
  ```

* **Status Code**: `200 OK` / `400 Bad Request` / `401 Unauthorized` / `403 Forbidden`

* **관련 테이블 · 요구사항**: `safety_keywords` · `SR-030`, `SR-033`, `NFR-107`

### 64. 의료·응급 안전 키워드 등록 · P1

* **Method / Endpoint**: `POST /api/v1/admin/safety-keywords`

* **Description**: 새로운 응급 증상 표현이나 약물·호르몬제 처방/변경 차단 키워드를 등록하고 `admin_logs`에 감사 이력을 남긴다(`SR-030`, `SR-033`, `NFR-107`).

* **인증**: 관리자 (`ADMIN`)

* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {admin_access_token}`

* **Request Parameter**: -

* **Request Body**:

  ```json
  {
    "keyword": "한쪽 팔 마비",
    "kind": "EMERGENCY",
    "severity": "HIGH",
    "mapped_alert_type": "EMERGENCY_119",
    "guide_message": "뇌혈관 응급 증상이 의심되므로 재측정이나 대기를 하지 않고 즉시 119 신고를 안내합니다.",
    "is_active": true,
    "change_reason": "뇌졸중 전조 응급 키워드 보강 (SR-033, SR-035)"
  }
  ```

* **Response Body (`201 Created`)**:

  ```json
  {
    "keyword_id": 25,
    "keyword": "한쪽 팔 마비",
    "kind": "EMERGENCY",
    "severity": "HIGH",
    "is_active": true,
    "created_at": "2026-11-27T15:40:00+09:00"
  }
  ```

* **Status Code**:

  * `201 Created`: 등록 성공

  * `400 Bad Request`: 필수값 누락, 허용되지 않은 `kind`·`severity` (`VALIDATION_ERROR`)

  * `401 Unauthorized`: 토큰 없음·만료

  * `403 Forbidden`: 관리자 권한 없음

  * `409 Conflict`: 동일 `keyword` 중복 등록 (`KEYWORD_DUPLICATED`)

* **관련 테이블 · 요구사항**: `safety_keywords`, `admin_logs` · `SR-030`, `SR-033`, `SR-035`, `NFR-107`

### 65. 의료·응급 안전 키워드 수정·비활성화 · P1

* **Method / Endpoint**: `PATCH /api/v1/admin/safety-keywords/{keyword_id}`

* **Description**: 등록된 안전 키워드의 심각도, 안내 문구 또는 활성화 상태를 수정하고 변경 사유를 감사 로그에 저장한다(`NFR-107`).

* **인증**: 관리자 (`ADMIN`)

* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {admin_access_token}`

* **Request Parameter (Path)**: `keyword_id` (bigint)

* **Request Body**:

  ```json
  {
    "severity": "HIGH",
    "guide_message": "즉시 119 신고 및 응급실 방문을 최우선 안내합니다.",
    "is_active": true,
    "change_reason": "응급 행동 수칙 안내 문구 명확화"
  }
  ```

* **Response Body (`200 OK`)**:

  ```json
  {
    "keyword_id": 25,
    "keyword": "한쪽 팔 마비",
    "severity": "HIGH",
    "is_active": true,
    "updated_at": "2026-11-27T15:42:00+09:00"
  }
  ```

* **Status Code**: `200 OK` / `400 Bad Request` / `401 Unauthorized` / `403 Forbidden` / `404 Not Found`

* **관련 테이블 · 요구사항**: `safety_keywords`, `admin_logs` · `SR-030`, `SR-033`, `NFR-107`

### 66. 의료·응급 안전 키워드 삭제 · P1

* **Method / Endpoint**: `DELETE /api/v1/admin/safety-keywords/{keyword_id}`

* **Description**: 오등록된 안전 키워드를 삭제하고 삭제된 키워드 정보와 사유를 `admin_logs`에 기록한다(`NFR-107`). (실제 운영 중 오탐 방지를 위한 일시 중지는 65번 `is_active: false` 사용 권장)

* **인증**: 관리자 (`ADMIN`)

* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {admin_access_token}`

* **Request Parameter (Path)**: `keyword_id` (bigint)

* **Request Body**:

  ```json
  {
    "change_reason": "중복 유의어 오등록 정리"
  }
  ```

* **Response Body (`204 No Content`)**: (본문 없음)

* **Status Code**: `204 No Content` / `400 Bad Request` (`change_reason` 누락) / `401 Unauthorized` / `403 Forbidden` / `404 Not Found`

* **관련 테이블 · 요구사항**: `safety_keywords`, `admin_logs` · `SR-030`, `SR-033`, `NFR-107`

### 67. 주요 운영·안전 기준 및 경계값 조회 · TBD

* **Method / Endpoint**: `GET /api/v1/admin/operational-policies`

* **Description**: 시스템에 적용 중인 모델 적용 조건 판정 정책 버전(`policy_version`), 임상 이상 소견 및 응급 안전 경계값(`LDL-C 160/190`, `TG 400`, `혈압 180/110`, 가정혈압 참고선 `135/85`), 모델별 결과 노출 승인 플래그 등 주요 운영 기준과 최종 변경 이력을 조회한다(`NFR-107`, `REQ-PRED-001`, `REQ-PRED-008`, `SR-014`, `SR-035`).

* **인증**: 관리자 (`ADMIN`)

* **Request Header**: `Authorization: Bearer {admin_access_token}`

* **Request Parameter**: -

* **Request Body**: -

* **Response Body (`200 OK`)**:

  ```json
  {
    "active_policy_version": "elig-v2.0",
    "items": [
      {
        "policy_id": 1,
        "policy_key": "LDL_SAFETY_THRESHOLDS",
        "metric": "ldl_cholesterol",
        "unit": "mg/dL",
        "caution_value": 160.0,
        "danger_value": 190.0,
        "description": "160 이상 신규 예측 보류·상담 안내, 190 이상 빠른 시일 내 진료 권유 강화",
        "updated_by": 999,
        "updated_at": "2026-11-26T09:00:00+09:00"
      },
      {
        "policy_id": 2,
        "policy_key": "BP_EMERGENCY_THRESHOLDS",
        "metric": "blood_pressure",
        "unit": "mmHg",
        "caution_value": 135.0,
        "danger_value": 180.0,
        "extra_config": {
          "home_bp_diastolic_ref": 85,
          "emergency_diastolic": 110
        },
        "description": "SBP 180 또는 DBP 110 이상 시 5분 휴식 후 재측정 및 지속 시 의료진 연락 안내 (SR-035)",
        "updated_by": 999,
        "updated_at": "2026-11-26T09:00:00+09:00"
      },
      {
        "policy_id": 3,
        "policy_key": "MODEL_1_RESULT_APPROVAL",
        "metric": "model_1_signal_exposure",
        "unit": null,
        "caution_value": null,
        "danger_value": null,
        "extra_config": {
          "active_model_version": "m1-c3-v1.0",
          "prediction_horizon_years": 5,
          "expose_probability": false,
          "expose_shap": false,
          "expose_signal_stage": false
        },
        "description": "MVP 개별 확률·SHAP 외부 표시 제외, 단계형 신호는 별도 검증·승인 전 비활성 (REQ-PRED-006~009)",
        "updated_by": 999,
        "updated_at": "2026-11-26T09:00:00+09:00"
      }
    ]
  }
  ```

* **Status Code**: `200 OK` / `401 Unauthorized` / `403 Forbidden`

* **관련 테이블 · 요구사항**: `risk_thresholds`, `admin_logs` · `NFR-107`, `REQ-PRED-001`, `REQ-PRED-008`, `SR-014`, `SR-035`

### 68. 운영·안전 기준 변경 및 변경 이력 저장 · TBD

* **Method / Endpoint**: `PATCH /api/v1/admin/operational-policies/{policy_id}`

* **Description**: 모델 적용·승인 정책이나 임상 안전 경계값을 수정한다. **기존 검증 범위를 벗어나는 임의 변경을 방지하기 위해 검증 근거 문서 참조(`verification_ref`)와 변경 사유(`change_reason`) 입력을 강제**하며, 변경 시 새 `policy_version`을 부여하거나 `admin_logs`에 변경 전·후 스냅샷을 영구 보존한다(`NFR-107`).

* **인증**: 관리자 (`ADMIN`)

* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {admin_access_token}`

* **Request Parameter (Path)**: `policy_id` (bigint)

* **Request Body**:

  ```json
  {
    "caution_value": 160.0,
    "danger_value": 190.0,
    "new_policy_version": "elig-v2.1",
    "verification_ref": "PR #48 임상 지침 및 안전 기준 검토 합의본",
    "change_reason": "고LDL 진료 권유 경계값 검증 결과 반영"
  }
  ```

* **Response Body (`200 OK`)**:

  ```json
  {
    "policy_id": 1,
    "policy_key": "LDL_SAFETY_THRESHOLDS",
    "active_policy_version": "elig-v2.1",
    "caution_value": 160.0,
    "danger_value": 190.0,
    "audit_log_id": 512,
    "updated_at": "2026-11-27T15:45:00+09:00"
  }
  ```

* **Status Code**:

  * `200 OK`: 기준 변경 및 감사 이력 기록 성공

  * `400 Bad Request`: `caution_value >= danger_value` 논리 역전, `change_reason` 또는 `verification_ref` 누락, MVP에서 금지된 확률·SHAP 강제 활성화 시도 (`VALIDATION_ERROR`)

  * `401 Unauthorized`: 토큰 없음·만료

  * `403 Forbidden`: 관리자 권한 없음

  * `404 Not Found`: 존재하지 않는 `policy_id`

* **관련 테이블 · 요구사항**: `risk_thresholds`, `admin_logs` · `NFR-107`, `REQ-PRED-001`, `REQ-PRED-008`, `SR-035`

### 📋 06 구역 미확정 사항(TBD) 및 팀 확인 포인트

| \# | 항목 | 관련 TBD / REQ | 확인 대상 및 내용 |
| ----- | ----- | ----- | ----- |
| 1 | 관리자 개인정보 접근 차단 및 마스킹 범위 | `TBD-020`, `SR-004`, `SR-009` | 관리자 통계는 100% 집계치만 반환 확정. 장애 대응용 오류 로그(`59번`)에서 이메일·IP·건강수치 마스킹 정규식 규칙 백엔드 확정 필요 |
| 2 | 운영 기준(`67~68번`) DB 테이블 vs 서버 설정 파일 관리 | `NFR-107`, `TBD-026` | `LDL 160/190`, `혈압 180/110`, `policy_version`을 기존 `risk_thresholds` 테이블 확장으로 관리할지, Git 버전 관리되는 서버 Config 파일로 고정하고 조회만 열어둘지 백엔드 협의 필요 |
| 3 | LLM 사용량·비용 수집 소스 | `REQ-ADMIN-004`, `NFR-108`, `TBD-029` | Langfuse 등 외부 옵저버빌리티 연동 조회 vs 자체 `llm_usage_logs` 테이블 적재 방식 확정 필요 |