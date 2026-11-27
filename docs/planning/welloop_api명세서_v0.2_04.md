# WELLOOP API 명세서 v2.0 — 영역 04 (맞춤형 챌린지·실천 기록·증상·복약·게이미피케이션)

## 04. 맞춤형 생활습관 챌린지 · 실천 · 증상 · 복약 · 게이미피케이션

* **관련 테이블**: `user_categories`, `challenges`, `daily_challenges`, `activity_logs`, `symptom_scores`, `medication_logs`, `user_streaks`, `badges`, `user_badges`
* **관련 요구사항**: `REQ-CHAL-001~004`, `REQ-LOG-001`, `REQ-LOG-007~008`, `REQ-PRED-005`, `REQ-GAME-001~003`, `SR-017~026`, `SR-034~035`
* **공통 Enum 정의**:
  * `Challenge_category`: `DIET` / `ACTIVITY` / `WEIGHT_WAIST` / `SMOKE_DRINK` / `VITAMIN_D_OUTDOOR` / `MENOPAUSE_SYMPTOM` / `HEALTH_MONITORING`
  * `Challenge_cycle`: `DAILY` / `WEEKLY` (`assigned_date`는 해당 주 월요일 고정)
  * `Goal_type`: `WEEKLY_DAYS` / `WEEKLY_COUNT` / `WEEKLY_TOTAL` / `EVENT_RATIO` / `ONCE` / `TOOL`
  * `Event_outcome`: `NO_EVENT` / `KEPT` / `NOT_KEPT`
  * `Perceived_intensity`: `LIGHT` / `MODERATE` / `VIGOROUS`
  * `Symptom_frequency`: `NONE` / `ONCE_OR_TWICE` / `THREE_TO_FIVE` / `SIX_OR_MORE` / `SOMETIMES`
  * `Medication_type`: `LIPID_MED` / `HORMONE` / `PRESCRIPTION` / `SUPPLEMENT`
  * `Medication_status`: `ACTIVE` / `STOPPED` / `PAUSED` / `UNKNOWN`

### 04 구역 API 목록 요약

| No | Method | Endpoint | 설명 | 우선순위 | 관련 요구사항 |
|---|---|---|---|---|---|
| 30 | `GET` | `/api/v1/users/me/categories` | 내 건강관리 관심 영역 목록 조회 | P0 | REQ-CHAL-001 |
| 31 | `PUT` | `/api/v1/users/me/categories` | 내 건강관리 관심 영역 선택 저장 | P0 | REQ-CHAL-001 |
| 32 | `GET` | `/api/v1/challenges/recommendations` | 임상 지침 기반 맞춤형 챌린지 추천 목록 조회 | P0 | REQ-CHAL-001~003, SR-017~023 |
| 33 | `POST` | `/api/v1/challenges/active` | 활성 챌린지 선택 및 배정 | P0 | REQ-CHAL-002, SR-020~021 |
| 34 | `GET` | `/api/v1/challenges/active` | 배정된 일간·주간 챌린지 진행 현황 및 달성률 조회 | P0 | REQ-CHAL-002, REQ-CHAL-004 |
| 35 | `POST` | `/api/v1/challenges/weekly-transition` | 주간 결과 기반 다음 주 단계 변경·유지·휴식 제안 수락 | P0 | REQ-CHAL-002, REQ-GAME-002 |
| 36 | `POST` | `/api/v1/activity-logs` | 생활습관 및 운동 실천 기록 (`is_daytime` 낮 시간 여부 포함) | P0 | REQ-LOG-001, REQ-CHAL-004 |
| 37 | `PATCH` | `/api/v1/activity-logs/{log_id}` | 생활습관 실천 기록 수정 | P0 | REQ-LOG-001, TBD-013 |
| 38 | `POST` | `/api/v1/symptom-logs` | 폐경 관련 증상 일일 기록 | P1 | REQ-LOG-007, SR-024 |
| 39 | `GET` | `/api/v1/symptom-logs` | 폐경 관련 증상 기록 내역 조회 | P1 | REQ-LOG-007 |
| 40 | `POST` | `/api/v1/medication-logs` | 복용 이력 등록 (지질강하제 시작·중단 시 재판정 연동) | P0(최소) / TBD | REQ-LOG-008, REQ-PRED-005, SR-026 |
| 41 | `PATCH` | `/api/v1/medication-logs/{medication_id}` | 복용 상태·종료일 수정 | P0(최소) / TBD | REQ-LOG-008, REQ-PRED-005, SR-026 |
| 42 | `GET` | `/api/v1/medication-logs` | 내 복용 이력 목록 조회 | P0(최소) / TBD | REQ-LOG-008 |
| 43 | `GET` | `/api/v1/gamification/summary` | 연속 실천 기록(Streak), 주간 목표 및 성취 배지 조회 | P1 (배지 P2) | REQ-GAME-001~003, SR-034 |

### 30. 내 건강관리 관심 영역 목록 조회 · P0

* **Method / Endpoint**: `GET /api/v1/users/me/categories`
* **Description**: 초기 건강 평가 결과로 도출된 관리 필요 영역 및 사용자가 활성화한 생활습관 카테고리 목록을 조회한다(`REQ-CHAL-001`).
* **인증**: 필요
* **Request Header**: `Authorization: Bearer {access_token}`
* **Response Body (`200 OK`)**:

  ```json
  {
    "categories": [
      { "category": "DIET", "label": "영양 및 식습관", "is_recommended": true, "enabled": true },
      { "category": "WEIGHT_WAIST", "label": "체중 및 복부비만", "is_recommended": true, "enabled": true },
      { "category": "ACTIVITY", "label": "신체활동 및 운동", "is_recommended": false, "enabled": true },
      { "category": "VITAMIN_D_OUTDOOR", "label": "비타민 D 및 야외활동", "is_recommended": false, "enabled": false }
    ]
  }
  ```

* **Status Code**: `200 OK` / `401 Unauthorized`
* **관련 테이블 · 요구사항**: `user_categories` · `REQ-CHAL-001`

### 31. 내 건강관리 관심 영역 선택 저장 · P0

* **Method / Endpoint**: `PUT /api/v1/users/me/categories`
* **Description**: 사용자가 관리하고 싶은 생활습관 카테고리의 활성화 상태를 복합 PK `(user_id, category)` 기준으로 저장한다.
* **인증**: 필요
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Body**:

  ```json
  {
    "categories": [
      { "category": "DIET", "enabled": true },
      { "category": "ACTIVITY", "enabled": true },
      { "category": "VITAMIN_D_OUTDOOR", "enabled": true }
    ]
  }
  ```

* **Response Body (`200 OK`)**: `{ "updated_count": 3 }`
* **Status Code**: `200 OK` / `400 Bad Request` / `401 Unauthorized`
* **관련 테이블 · 요구사항**: `user_categories` · `REQ-CHAL-001`

### 32. 임상 지침 기반 맞춤형 챌린지 추천 목록 조회 · P0

* **Method / Endpoint**: `GET /api/v1/challenges/recommendations`
* **Description**: 안전 제외 → 추천 조건 → 임상 우선순위 순서로 도출된 맞춤형 챌린지 후보와 안전 제외된 챌린지(제외 사유 포함)를 반환한다(`REQ-CHAL-001~003`, `SR-017~023`).
* **인증**: 필요
* **Request Header**: `Authorization: Bearer {access_token}`
* **Response Body (`200 OK`)**:

  ```json
  {
    "is_onboarding_period": true,
    "max_selectable_count": 3,
    "recommended_items": [
      {
        "challenge_id": 101,
        "code": "DIET-01",
        "category": "DIET",
        "title": "기름진 육류·가공육 주 2회 이하로 줄이기",
        "challenge_cycle": "WEEKLY",
        "goal_type": "WEEKLY_COUNT",
        "recommended_level": 1,
        "target_value": 2,
        "target_unit": "회 이하/주",
        "role_type": "CORE",
        "priority_reason": "포화지방 섭취 감소를 통한 LDL 콜레스테롤 관리 핵심 수칙입니다."
      },
      {
        "challenge_id": 501,
        "code": "OUT-01",
        "category": "VITAMIN_D_OUTDOOR",
        "title": "낮 시간 가벼운 야외 산책하기",
        "challenge_cycle": "WEEKLY",
        "goal_type": "WEEKLY_DAYS",
        "recommended_level": 1,
        "target_value": 3,
        "target_unit": "일/주",
        "role_type": "SUB",
        "caution_note": "자외선이 강한 시간대를 피하고 자외선차단제를 적절히 사용하세요."
      }
    ],
    "excluded_items": [
      {
        "challenge_id": 301,
        "code": "WST-01",
        "category": "WEIGHT_WAIST",
        "title": "체중 감량 목표 실천하기",
        "excluded_reason_code": "NORMAL_OR_LOW_BMI",
        "excluded_message": "현재 정상 체중 범위에 해당하여 불필요한 체중 감량 대신 식습관·신체활동 챌린지를 우선 권장합니다."
      }
    ]
  }
  ```

* **Status Code**: `200 OK` / `401 Unauthorized` / `404 Not Found`
* **관련 테이블 · 요구사항**: `challenges`, `questionnaires` · `REQ-CHAL-001~003`, `SR-017~023`

### 33. 활성 챌린지 선택 및 배정 · P0

* **Method / Endpoint**: `POST /api/v1/challenges/active`
* **Description**: 수행할 챌린지와 단계(1~3단계)를 선택해 배정한다(`REQ-CHAL-002`). 직접 선택 시에도 안전 제외 조건(`SR-020~021`)을 동일하게 검증한다.
* **인증**: 필요
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Body**:

  ```json
  {
    "selections": [
      { "challenge_id": 101, "level": 1 },
      { "challenge_id": 202, "level": 1 },
      { "challenge_id": 501, "level": 1 }
    ]
  }
  ```

* **Response Body (`201 Created`)**:

  ```json
  {
    "assigned_items": [
      {
        "daily_challenge_id": 501,
        "challenge_id": 101,
        "challenge_cycle": "WEEKLY",
        "assigned_date": "2026-11-23",
        "level": 1,
        "adjusted_target_value": 1
      }
    ]
  }
  ```

* **Status Code**: `201 Created` / `400 Bad Request` / `401 Unauthorized` / `409 Conflict`
* **관련 테이블 · 요구사항**: `daily_challenges`, `challenges` · `REQ-CHAL-002`, `REQ-CHAL-004`, `SR-020~021`

### 34. 배정된 일간·주간 챌린지 진행 현황 및 달성률 조회 · P0

* **Method / Endpoint**: `GET /api/v1/challenges/active`
* **Description**: 기준 날짜(및 주간)에 배정된 일간(`DAILY`)·주간(`WEEKLY`) 챌린지 현황과 달성률을 조회한다(`REQ-CHAL-004`).
* **인증**: 필요
* **Request Header**: `Authorization: Bearer {access_token}`
* **Request Parameter (Query)**: `date` (`YYYY-MM-DD`, 기본 오늘), `cycle` (`DAILY` | `WEEKLY` | `ALL`, 기본 `ALL`)
* **Response Body (`200 OK`)**:

  ```json
  {
    "reference_date": "2026-11-26",
    "week_monday": "2026-11-23",
    "overall_weekly_achievement_rate": 0.78,
    "items": [
      {
        "daily_challenge_id": 502,
        "challenge_id": 202,
        "code": "ACT-02",
        "category": "ACTIVITY",
        "title": "10분 이상 빠르게 걷기",
        "challenge_cycle": "WEEKLY",
        "goal_type": "WEEKLY_TOTAL",
        "level": 1,
        "target_value": 90,
        "current_value": 70,
        "unit": "분",
        "achievement_rate": 0.78,
        "is_completed": false,
        "included_in_overall_avg": true
      }
    ]
  }
  ```

* **Status Code**: `200 OK` / `400 Bad Request` / `401 Unauthorized`
* **관련 테이블 · 요구사항**: `daily_challenges`, `challenges` · `REQ-CHAL-004`

### 35. 주간 결과 기반 다음 주 단계 변경·유지·휴식 제안 수락 · P0

* **Method / Endpoint**: `POST /api/v1/challenges/weekly-transition`
* **Description**: 주간 달성 결과에 따른 차주 목표 단계 변경·유지·휴식 제안을 사용자가 수락하여 반영한다(`REQ-CHAL-002`).
* **인증**: 필요
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Body**:

  ```json
  {
    "next_week_monday": "2026-11-30",
    "decisions": [
      { "challenge_id": 202, "action": "LEVEL_UP", "next_level": 2 },
      { "challenge_id": 101, "action": "KEEP", "next_level": 1 }
    ]
  }
  ```

* **Response Body (`200 OK`)**: `{ "next_week_monday": "2026-11-30", "applied_count": 2 }`
* **Status Code**: `200 OK` / `400 Bad Request` / `401 Unauthorized`
* **관련 테이블 · 요구사항**: `daily_challenges` · `REQ-CHAL-002`, `REQ-GAME-002`

### 36. 생활습관 및 운동 실천 기록 (낮 시간 활동 여부 포함) · P0

* **Method / Endpoint**: `POST /api/v1/activity-logs`
* **Description**: 챌린지 실천 여부 또는 구체적인 운동 세션(종목, 시간, 체감 강도, **실외 여부 `is_outdoor`**, **낮 시간 활동 여부 `is_daytime`**, 식후 여부)을 기록하고 활성 챌린지 실적을 자동 갱신한다(`REQ-LOG-001`, `REQ-CHAL-004`).
* **인증**: 필요 (`HEALTH_DATA` 동의 필수)
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Body (실외 운동 + 낮 시간 활동 기록 예시)**:

  ```json
  {
    "log_date": "2026-11-26",
    "daily_challenge_id": 502,
    "activity_type": "BRISK_WALKING",
    "duration_minutes": 25,
    "perceived_intensity": "MODERATE",
    "is_outdoor": true,
    "is_daytime": true,
    "is_after_meal": true,
    "event_outcome": null,
    "has_emergency_symptom": false,
    "memo": "점심 식사 후 햇볕 쬐며 공원 걷기"
  }
  ```

  *(실내 운동일 경우: `"is_outdoor": false, "is_daytime": null` 전달)*

* **Response Body (`201 Created`)**:

  ```json
  {
    "log_id": 901,
    "log_date": "2026-11-26",
    "is_outdoor": true,
    "is_daytime": true,
    "effective_aerobic_minutes": 25,
    "updated_challenges": [
      {
        "daily_challenge_id": 502,
        "code": "ACT-02",
        "current_value": 95,
        "target_value": 90,
        "achievement_rate": 1.0,
        "is_completed": true
      },
      {
        "daily_challenge_id": 503,
        "code": "OUT-01",
        "current_value": 3,
        "target_value": 3,
        "achievement_rate": 1.0,
        "is_completed": true
      }
    ],
    "safety_alert": null,
    "created_at": "2026-11-26T13:30:00+09:00"
  }
  ```

* **Status Code**:
  * `201 Created`: 실천 기록 및 챌린지 실적 자동 반영 성공
  * `400 Bad Request`: **`is_outdoor == false`인데 `is_daytime`에 `null`이 아닌 값(`true` 또는 `false`)을 보낸 경우**, 당일·전날 입력 허용 범위를 벗어난 날짜 입력 (`VALIDATION_ERROR`)
  * `401 Unauthorized` / `403 Forbidden`
* **관련 테이블 · 요구사항**: `activity_logs`, `daily_challenges` · `REQ-LOG-001`, `REQ-CHAL-004`, `SR-035`
* **ERD `is_daytime` 컬럼 검증 및 판정 규칙 (`REQ-LOG-001` · 11/27 ERD 반영)**:
  1. `is_outdoor == false` (실내 활동): `is_daytime`은 반드시 `null`이어야 한다.
  2. `is_outdoor == true` (실외 활동): `is_daytime`은 선택 입력(`true` / `false` / `null`) 가능하며, **`is_outdoor: true`이면서 `is_daytime: true`인 경우에만 `OUT-01`(비타민 D·낮 시간 야외활동) 챌린지 달성 실적에 반영**한다.

### 37. 생활습관 실천 기록 수정 · P0

* **Method / Endpoint**: `PATCH /api/v1/activity-logs/{log_id}`
* **Description**: 당일·전날 입력한 실천 기록(`is_outdoor`, `is_daytime` 포함)을 수정하고 주간 챌린지 달성률을 재계산한다. (`is_outdoor`를 `false`로 변경 시 `is_daytime`은 자동으로 `null` 초기화)
* **인증**: 필요
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Parameter (Path)**: `log_id` (bigint)
* **Request Body**:

  ```json
  {
    "duration_minutes": 30,
    "is_outdoor": true,
    "is_daytime": true
  }
  ```

* **Response Body (`200 OK`)**: 갱신된 실천 기록 및 `updated_challenges` 배열 반환
* **Status Code**: `200 OK` / `400 Bad Request` / `401 Unauthorized` / `403 Forbidden` / `404 Not Found`
* **관련 테이블 · 요구사항**: `activity_logs`, `daily_challenges` · `REQ-LOG-001`, `TBD-013`

### 38. 폐경 관련 증상 일일 기록 · P1

* **Method / Endpoint**: `POST /api/v1/symptom-logs`
* **Description**: 안면홍조, 야간발한, 수면 장애의 발생 빈도(`Symptom_frequency`)와 불편 정도(0~4점)를 기록한다(`REQ-LOG-007`).
* **인증**: 필요 (`HEALTH_DATA` 동의 필수)
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Body**:

  ```json
  {
    "recorded_date": "2026-11-26",
    "hot_flash_freq": "ONCE_OR_TWICE",
    "hot_flash_discomfort": 2,
    "night_sweat_freq": "NONE",
    "night_sweat_discomfort": 0,
    "sleep_disturbance_freq": "ONCE_OR_TWICE",
    "sleep_disturbance_discomfort": 3,
    "other_symptoms": null,
    "memo": "새벽에 한 번 깨서 다시 잠들기까지 시간이 걸림"
  }
  ```

* **Response Body (`201 Created` / `200 OK`)**: 저장된 증상 객체 + 생활관리 `care_tip` + `safety_alert`
* **Status Code**: `201 Created` / `200 OK` / `400 Bad Request` / `401 Unauthorized` / `403 Forbidden`
* **관련 테이블 · 요구사항**: `symptom_scores` · `REQ-LOG-007`, `SR-024`

### 39. 폐경 관련 증상 기록 내역 조회 · P1

* **Method / Endpoint**: `GET /api/v1/symptom-logs`
* **Description**: 기간별 폐경 관련 증상 기록 목록을 조회한다.
* **인증**: 필요
* **Request Header**: `Authorization: Bearer {access_token}`
* **Request Parameter (Query)**: `from_date`, `to_date`, `page` (기본 `1`), `size` (기본 `14`)
* **Response Body (`200 OK`)**: `items[]`, `total`, `page`, `size` 반환
* **Status Code**: `200 OK` / `401 Unauthorized`
* **관련 테이블 · 요구사항**: `symptom_scores` · `REQ-LOG-007`, `SR-003`

### 40. 복용 이력 등록 · P0 (지질강하제 최소 범위) / 기타 TBD

* **Method / Endpoint**: `POST /api/v1/medication-logs`
* **Description**: 지질강하제(`LIPID_MED`) 등 복용 이력을 등록하고, 적용 조건 관련 약물인 경우 모델 적용 조건 재판정(`REQ-PRED-005`)을 자동 실행하여 갱신된 `current_branch`와 `current_reason_code`를 반환한다(`REQ-LOG-008`).
* **인증**: 필요 (`HEALTH_DATA` 동의 필수)
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Body**:

  ```json
  {
    "medication_type": "LIPID_MED",
    "status": "ACTIVE",
    "name": "스타틴 계열 처방약",
    "dosage": "10mg",
    "frequency": "하루 1회 저녁",
    "start_date": "2026-11-25",
    "end_date": null,
    "is_date_unknown": false,
    "memo": "내과 진료 후 복용 시작"
  }
  ```

* **Response Body (`201 Created`)**:

  ```json
  {
    "medication_id": 12,
    "medication_type": "LIPID_MED",
    "status": "ACTIVE",
    "start_date": "2026-11-25",
    "end_date": null,
    "branch_recheck_triggered": true,
    "current_branch": "BRANCH_C",
    "current_reason_code": "EXISTING_HIGH_LDL",
    "disclaimer": "처방약·호르몬제·영양제의 복용 시작, 중단 또는 용량 변경은 반드시 담당 의료진과 상의하세요.",
    "created_at": "2026-11-26T16:00:00+09:00"
  }
  ```

* **Status Code**: `201 Created` / `400 Bad Request` / `401 Unauthorized` / `403 Forbidden`
* **관련 테이블 · 요구사항**: `medication_logs` · `REQ-LOG-008`, `REQ-PRED-005`, `SR-026`

### 41. 복용 상태·종료일 수정 · P0 (지질강하제 최소 범위) / 기타 TBD

* **Method / Endpoint**: `PATCH /api/v1/medication-logs/{medication_id}`
* **Description**: 복용 중단(`STOPPED`) 등 상태를 수정하고 필요 시 모델 적용 조건을 재판정하여 `current_branch`와 `current_reason_code`를 반환한다.
* **인증**: 필요
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Parameter (Path)**: `medication_id` (bigint)
* **Request Body**: `{ "status": "STOPPED", "end_date": "2026-11-26" }`
* **Response Body (`200 OK`)**: 수정된 복용 이력 객체 + `branch_recheck_triggered`, `current_branch`, `current_reason_code`
* **Status Code**: `200 OK` / `400 Bad Request` / `401 Unauthorized` / `403 Forbidden` / `404 Not Found`
* **관련 테이블 · 요구사항**: `medication_logs` · `REQ-LOG-008`, `REQ-PRED-005`, `SR-026`

### 42. 내 복용 이력 목록 조회 · P0 (지질강하제 최소 범위) / 기타 TBD

* **Method / Endpoint**: `GET /api/v1/medication-logs`
* **Description**: 등록된 복용 이력을 조회한다.
* **인증**: 필요
* **Request Header**: `Authorization: Bearer {access_token}`
* **Request Parameter (Query)**: `status` (`ACTIVE` | `STOPPED` | `ALL`, 기본 `ALL`)
* **Response Body (`200 OK`)**: `items[]` 배열 반환
* **Status Code**: `200 OK` / `401 Unauthorized`
* **관련 테이블 · 요구사항**: `medication_logs` · `REQ-LOG-008`, `SR-003`

### 43. 연속 실천 기록(Streak), 주간 목표 및 성취 배지 조회 · P1 (배지 P2)

* **Method / Endpoint**: `GET /api/v1/gamification/summary`
* **Description**: 주간 챌린지 연속 달성 주수(`REQ-GAME-001`), 이번 주 목표 달성 현황(`REQ-GAME-002`), 성취 배지 목록(`REQ-GAME-003`)을 조회한다.
* **인증**: 필요
* **Request Header**: `Authorization: Bearer {access_token}`
* **Response Body (`200 OK`)**: `challenge_streak`, `current_week_goal`, `earned_badges[]` 반환
* **Status Code**: `200 OK` / `401 Unauthorized`
* **관련 테이블 · 요구사항**: `user_streaks`, `badges`, `user_badges` · `REQ-GAME-001~003`, `SR-034`