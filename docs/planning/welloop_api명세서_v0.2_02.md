# WELLOOP API 명세서 v2.0 — 영역 02 (초기 건강 평가·혈중 지질검사 입력)

## 02. 초기 건강 평가 및 혈중 지질검사 입력

* **관련 테이블**: `questionnaires`, `checkup_records`
* **관련 요구사항**: `REQ-ASMT-001~007`, `REQ-LOG-003~006`, `DR-014`, `NFR-103`, `SR-014`, `SR-020`, `SR-035`
* **공통 Enum 정의**:
  * `Waist_measure_type` *(11/27 ERD 반영)*: `MEASURED` (줄자 직접 측정·실측) / `ESTIMATED` (바지 사이즈 등 어림·추정 입력)
  * `Menopause_status`: `PRE` (폐경 전) / `EARLY_PERI` (폐경 이행 초기) / `LATE_PERI` (폐경 이행 후기) / `EARLY_POST` (폐경 후 초기) / `LATE_POST` (폐경 후 후기) / `UNKNOWN` (판단 불가 — C 분기)
  * `Hormone_therapy_status`: `NONE` (복용 경험 없음) / `FORMER` (과거 복용·현재 중단) / `CURRENT` (현재 복용 중) / `UNKNOWN` (모름)
  * `Tri_state_answer`: `NO` (아니오) / `YES` (예) / `UNKNOWN` (모름)
  * `Swan_symptom_freq` (모델 입력용 지난 2주 발생 일수 5구간): `NONE` (없음) / `DAYS_1_TO_5` (1~5일) / `DAYS_6_TO_8` (6~8일) / `DAYS_9_TO_13` (9~13일) / `DAILY` (매일)
  * `Smoking_status`: `NON_SMOKER` (비흡연) / `FORMER_SMOKER` (과거 흡연) / `CURRENT_SMOKER` (현재 흡연)
  * `Activity_limit_level` (`SR-020` 의료진 허용 활동 범위): `NONE` (제한 없음) / `LIGHT_WALK_ONLY` (가벼운 걷기만 허용) / `SEATED_ONLY` (앉아서 하는 활동만 가능) / `PROHIBITED` (운동 금지) / `UNKNOWN` (확인 필요·모름)
  * `Bp_source` (`DR-014` 혈압 측정 출처 구분): `CLINIC` (병원·검진기관 측정) / `HOME` (가정혈압 측정)
  * `Ldl_measure_type`: `CALCULATED` (계산값) / `DIRECT` (직접측정값) / `UNKNOWN` (미확인)

### 02 구역 API 목록 요약

| No | Method | Endpoint | 설명 | 우선순위 | 관련 요구사항 |
|---|---|---|---|---|---|
| 14 | `POST` | `/api/v1/questionnaires` | 초기 건강 평가 저장 (최종 제출 및 중간 저장) | P0 (중간저장 TBD) | REQ-ASMT-001~007, DR-014 |
| 15 | `GET` | `/api/v1/questionnaires/draft` | 작성 중인 초기 건강 평가(임시 저장본) 조회 | TBD | REQ-ASMT-007, TBD-028 |
| 16 | `GET` | `/api/v1/questionnaires/latest` | 가장 최근 완료된 초기 건강 평가 조회 | P0 | REQ-ASMT-001~006 |
| 17 | `POST` | `/api/v1/checkups` | 혈중 지질검사 및 검진 수치 입력 (초기 평가 및 추가 입력) | P0 | REQ-ASMT-004, REQ-LOG-003~004, NFR-103 |
| 18 | `PATCH` | `/api/v1/checkups/{record_id}` | 입력한 검사 결과 수정 및 변경 관리 | TBD | REQ-LOG-005, TBD-018·028 |
| 19 | `GET` | `/api/v1/checkups` | 내 혈중 지질검사 결과 이력 목록 조회 | P0 | REQ-LOG-006, REQ-DASH-001 |

### 14. 초기 건강 평가 저장 (최종 제출 및 중간 저장) · P0

* **Method / Endpoint**: `POST /api/v1/questionnaires`
* **Description**: 초기 건강 평가에 필요한 신체계측(허리둘레 실측/추정 구분 포함), 폐경 단계, 수술·호르몬 요법 이력, 고LDL 진단·지질강하제 복용 여부, 모델 입력용 증상 빈도 및 챌린지 추천용 생활습관 정보를 수집한다(`REQ-ASMT-001~006`).
* **인증**: 필요 (`HEALTH_DATA` 동의 필수 — 미동의 시 `403 CONSENT_REQUIRED`)
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Parameter**: -
* **Request Body**:

  ```json
  {
    "questionnaire_id": null,
    "is_completed": true,
    "height": 160.5,
    "weight": 58.0,
    "waist_size": 81.0,
    "waist_measure_type": "MEASURED",
    "systolic_bp": 122,
    "diastolic_bp": 78,
    "bp_source": "CLINIC",
    "menopause_status": "EARLY_PERI",
    "hysterectomy": false,
    "oophorectomy": false,
    "surgery_date": null,
    "hormone_therapy_status": "NONE",
    "high_ldl_diagnosed": "NO",
    "lipid_lowering_med": "NO",
    "lipid_med_started_at": null,
    "lipid_med_stopped_at": null,
    "hot_flash_swan_freq": "DAYS_1_TO_5",
    "night_sweat_swan_freq": "NONE",
    "symptom_discomfort_level": 2,
    "smoking_status": "NON_SMOKER",
    "quit_smoking_intent": null,
    "secondhand_smoke": false,
    "drinking_days_per_week": 1,
    "fatty_meat_freq": 2,
    "fried_fastfood_freq": 1,
    "milk_butter_freq": 2,
    "fiber_freq": 5,
    "fish_freq": 2,
    "activity_days_per_week": 3,
    "activity_minutes_per_day": 30,
    "sedentary_hours_per_day": 7,
    "medical_activity_limit": "NONE",
    "outdoor_activity_freq": 3,
    "sleep_hours": 6.5,
    "has_emergency_symptom": false
  }
  ```

* **Response Body (`201 Created` / 기존 임시저장 갱신 시 `200 OK`)**:

  ```json
  {
    "questionnaire_id": 105,
    "is_completed": true,
    "bmi": 22.5,
    "waist_size": 81.0,
    "waist_measure_type": "MEASURED",
    "safety_alert": null,
    "created_at": "2026-11-26T14:10:00+09:00"
  }
  ```

* **Status Code**:
  * `201 Created` / `200 OK`: 초기 건강 평가(또는 임시 저장본) 저장 성공
  * `400 Bad Request`: `is_completed: true`인데 필수 항목 누락, **`waist_size` 값이 존재하는데 `waist_measure_type`이 누락(`null`)되었거나 반대로 `waist_size`가 `null`인데 `waist_measure_type`만 전달된 경우**, 물리적 허용 범위 밖 수치 (`VALIDATION_ERROR`)
  * `401 Unauthorized`: 토큰 없음·만료
  * `403 Forbidden`: 건강정보 수집·활용 동의(`HEALTH_DATA`) 미확보 (`CONSENT_REQUIRED`)
* **관련 테이블 · 요구사항**: `questionnaires` · `REQ-ASMT-001~007`, `DR-014`, `NFR-103`, `SR-001`, `SR-020`, `SR-035`
* **비고**:
  * **허리둘레 측정/추정 구분 (`DR-014`, 11/27 ERD 반영)**: 사용자가 줄자로 직접 잰 값(`MEASURED`)인지 바지 인치 등으로 어림잡은 값(`ESTIMATED`)인지 함께 저장하여 모델 입력 변수 적합성 판정 및 추후 실측 재확인 안내에 활용한다. 미응답 시 두 컬럼 모두 `null`로 저장한다.
  * **미응답과 실제값 구분 (`DR-014`)**: 응답하지 않은 선택 문항은 임의의 `0`이나 평균값으로 대치해 저장하지 않고 반드시 `null`로 저장한다.

### 15. 작성 중인 초기 건강 평가(임시 저장본) 조회 · TBD

* **Method / Endpoint**: `GET /api/v1/questionnaires/draft`
* **Description**: 사용자가 초기 평가 도중 '저장하고 나중에 계속'(`is_completed: false`)을 선택한 뒤 재진입했을 때 작성 중이던 내용을 복원한다(`REQ-ASMT-007`).
* **인증**: 필요
* **Request Header**: `Authorization: Bearer {access_token}`
* **Response Body (`200 OK`)**: 작성 중인 임시 저장본이 있을 경우 14번 Request Body와 동일한 필드(`waist_measure_type` 포함) + `updated_at` 반환, 없을 경우 `{ "draft": null }` 반환
* **Status Code**: `200 OK` / `401 Unauthorized`
* **관련 테이블 · 요구사항**: `questionnaires` · `REQ-ASMT-007`, `TBD-028`

### 16. 가장 최근 완료된 초기 건강 평가 조회 · P0

* **Method / Endpoint**: `GET /api/v1/questionnaires/latest`
* **Description**: 본인(`user_id`)의 완료된(`is_completed: true`) 가장 최신 초기 건강 평가 데이터를 조회한다.
* **인증**: 필요
* **Request Header**: `Authorization: Bearer {access_token}`
* **Response Body (`200 OK`)**:

  ```json
  {
    "questionnaire_id": 105,
    "is_completed": true,
    "height": 160.5,
    "weight": 58.0,
    "waist_size": 81.0,
    "waist_measure_type": "MEASURED",
    "menopause_status": "EARLY_PERI",
    "high_ldl_diagnosed": "NO",
    "lipid_lowering_med": "NO",
    "medical_activity_limit": "NONE",
    "created_at": "2026-11-26T14:10:00+09:00"
  }
  ```

* **Status Code**: `200 OK` / `401 Unauthorized` / `404 Not Found`
* **관련 테이블 · 요구사항**: `questionnaires` · `REQ-ASMT-001~006`, `SR-003`

### 17. 혈중 지질검사 및 검진 수치 입력 · P0

* **Method / Endpoint**: `POST /api/v1/checkups`
* **Description**: 초기 건강 평가 단계 또는 서비스 이용 중 추가로 받은 혈중 지질검사 결과(LDL-C, HDL-C, 총콜레스테롤, 중성지방)와 검사일·측정 단위를 저장한다(`REQ-ASMT-004`, `REQ-LOG-003~004`).
* **인증**: 필요 (`HEALTH_DATA` 동의 필수)
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Body**:

  ```json
  {
    "checkup_date": "2026-11-15",
    "ldl_cholesterol": 142.0,
    "ldl_measure_type": "CALCULATED",
    "hdl_cholesterol": 54.0,
    "total_cholesterol": 218.0,
    "triglycerides": 125.0,
    "lipid_unit": "mg/dL",
    "pressure_systolic": 124,
    "pressure_diastolic": 80,
    "fasting_glucose": null,
    "doctor_target_ldl": null,
    "confirm_extreme_value": false
  }
  ```

* **Response Body (`201 Created`)**:

  ```json
  {
    "record_id": 52,
    "checkup_date": "2026-11-15",
    "ldl_cholesterol": 142.0,
    "hdl_cholesterol": 54.0,
    "total_cholesterol": 218.0,
    "triglycerides": 125.0,
    "lipid_unit": "mg/dL",
    "is_ldl_usable_for_model": true,
    "ldl_unusable_reason": null,
    "branch_recheck_triggered": true,
    "current_branch": "BRANCH_B",
    "current_reason_code": "MODEL_APPROVAL_PENDING",
    "safety_alert": null,
    "disclaimer": "입력된 검사 수치는 건강관리 참고용이며 의학적 진단을 대체하지 않습니다.",
    "created_at": "2026-11-26T14:15:00+09:00"
  }
  ```

* **Status Code**: `201 Created` / `400 Bad Request` / `401 Unauthorized` / `403 Forbidden`
* **관련 테이블 · 요구사항**: `checkup_records` · `REQ-ASMT-004`, `REQ-LOG-003~004`, `REQ-PRED-001`, `REQ-PRED-005`, `NFR-103`, `SR-014`

### 18. 입력한 검사 결과 수정 및 변경 관리 · TBD

* **Method / Endpoint**: `PATCH /api/v1/checkups/{record_id}`
* **Description**: 사용자가 오입력한 검사 수치나 검사일을 수정하고 최신 검사값이 바뀌면 모델 적용 조건을 재판정한다(`REQ-LOG-005`, `REQ-PRED-005`).
* **인증**: 필요
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Parameter (Path)**: `record_id` (bigint)
* **Request Body**:

  ```json
  {
    "ldl_cholesterol": 136.0,
    "triglycerides": 118.0
  }
  ```

* **Response Body (`200 OK`)**:

  ```json
  {
    "record_id": 52,
    "checkup_date": "2026-11-15",
    "ldl_cholesterol": 136.0,
    "triglycerides": 118.0,
    "is_ldl_usable_for_model": true,
    "branch_recheck_triggered": true,
    "current_branch": "BRANCH_B",
    "current_reason_code": "MODEL_APPROVAL_PENDING",
    "safety_alert": null,
    "updated_at": "2026-11-26T15:00:00+09:00"
  }
  ```

* **Status Code**: `200 OK` / `400 Bad Request` / `401 Unauthorized` / `403 Forbidden` / `404 Not Found`
* **관련 테이블 · 요구사항**: `checkup_records` · `REQ-LOG-005`, `REQ-PRED-005`, `TBD-018`, `TBD-028`

### 19. 내 혈중 지질검사 결과 이력 목록 조회 · P0

* **Method / Endpoint**: `GET /api/v1/checkups`
* **Description**: 사용자가 입력한 실제 혈중 지질검사 기록 목록을 검사일(`checkup_date`) 최신순으로 조회한다(`REQ-LOG-006`).
* **인증**: 필요
* **Request Header**: `Authorization: Bearer {access_token}`
* **Request Parameter (Query)**: `from_date` (`YYYY-MM-DD`, 선택), `to_date` (`YYYY-MM-DD`, 선택), `page` (기본 `1`), `size` (기본 `10`)
* **Response Body (`200 OK`)**:

  ```json
  {
    "items": [
      {
        "record_id": 52,
        "checkup_date": "2026-11-15",
        "ldl_cholesterol": 136.0,
        "ldl_measure_type": "CALCULATED",
        "hdl_cholesterol": 54.0,
        "total_cholesterol": 218.0,
        "triglycerides": 118.0,
        "lipid_unit": "mg/dL",
        "doctor_target_ldl": 130.0,
        "is_ldl_usable_for_model": true,
        "created_at": "2026-11-26T14:15:00+09:00"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 10
  }
  ```

* **Status Code**: `200 OK` / `400 Bad Request` / `401 Unauthorized`
* **관련 테이블 · 요구사항**: `checkup_records` · `REQ-LOG-006`, `REQ-DASH-001`, `SR-003`