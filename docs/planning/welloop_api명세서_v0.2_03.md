# WELLOOP API 명세서 v2.0 — 영역 03 (모델 적용 조건 판정·예측·건강지표 기록·대시보드)

## 03. 모델 적용 조건 판정 · 예측 · 건강지표 기록 · 대시보드

* **관련 테이블**: `risk_predictions`, `health_logs`, `checkup_records`, `questionnaires`
* **관련 요구사항**: `REQ-PRED-001~012`, `REQ-LOG-002`, `REQ-LOG-006`, `REQ-DASH-001~004`, `DR-004`, `DR-013~014`, `SR-011~013`, `SR-025`, `SR-027~029`, `SR-035`
* **공통 Enum 정의**:
  * `Care_branch`:
    * `BRANCH_A`: 모델 적용 조건 충족 + 활용 가능한 LDL-C 검사 결과 미보유
    * `BRANCH_B`: 모델 적용·검증 조건 충족 + 활용 가능한 LDL-C 검사 결과 보유
    * `BRANCH_C`: AI 모델 적용 제외 대상 또는 모델 검증 미달 (일반 건강관리 안내)
  * `Model_type`:
    * `MODEL_1`: 폐경 전·폐경 이행기 초기 예측 모델 (`prediction_horizon_years = 5`)
    * `MODEL_2`: 폐경 이행기 후기·폐경 후 예측 모델 (`prediction_horizon_years`는 검증 확정 시 부여, 미검증 시 `BRANCH_C`)
  * `Branch_reason_code` *(11/27 ERD 반영 — 통합 판정·적용 사유 코드)*:
    * `ELIGIBLE_APPROVED`: **[B 분기]** 조건 충족 및 모델 결과 활용 승인 완료
    * `MODEL_APPROVAL_PENDING`: **[B 분기]** 조건 충족하나 MVP 결과 수치 노출 미승인 (임상 지침 안내 제공)
    * `LDL_MISSING`: **[A 분기]** 기타 적용 조건 충족하나 LDL-C 검사 결과 미보유
    * `LDL_TG_OVER_400`: **[A/C 분기]** 중성지방 400 mg/dL 이상으로 계산식 LDL-C 모델 활용 제한
    * `MALE`: **[C 분기]** 남성 (SWAN 여성 코호트 기반 모델 제외)
    * `OUT_OF_AGE_RANGE`: **[C 분기]** 모델 학습·검증 연령 범위 밖
    * `SURGERY`: **[C 분기]** 자궁절제술 또는 난소절제술 이력
    * `HORMONE_THERAPY`: **[C 분기]** 호르몬 요법 이력·복용 중
    * `EXISTING_HIGH_LDL`: **[C 분기]** 기존 고LDL 진단 또는 지질강하제 복용 중 (관리 흐름 안내)
    * `LDL_OVER_160`: **[C 분기]** 최신 LDL-C ≥ 160 mg/dL (상담 안내 및 신규 발생 예측 보류)
    * `MENOPAUSE_UNKNOWN`: **[C 분기]** 폐경 단계 판단 불가 (`UNKNOWN`)
    * `MODEL_UNVERIFIED`: **[C 분기]** 해당 폐경 단계 모델 검증 기준 미달·불확실
    * `PREDICTION_FAILED`: **[대체 경로]** 예측 추론 처리 실패 (일반 건강관리 대체 안내, 정상 예측 이력 미생성)
  * `Waist_measure_type` *(11/27 ERD 반영)*: `MEASURED` (줄자 직접 측정) / `ESTIMATED` (어림·추정 입력)
  * `Evaluation_trigger`: `INITIAL` / `ELIGIBILITY_RECHECK` / `RISK_REEVALUATION`

### 03 구역 API 목록 요약

| No | Method | Endpoint | 설명 | 우선순위 | 관련 요구사항 |
|---|---|---|---|---|---|
| 20 | `POST` | `/api/v1/predictions` | 모델 적용 조건 판정(A/B/C 분기) 및 위험 예측 실행 | P0 | REQ-PRED-001~008, 011~012 |
| 21 | `GET` | `/api/v1/predictions/latest` | 최신 분기 판정 및 건강관리 안내 결과 조회 | P0 | REQ-DASH-003, SR-012 |
| 22 | `GET` | `/api/v1/predictions` | 판정 및 예측 이력 목록 조회 | P0 | REQ-PRED-011, REQ-DASH-003 |
| 23 | `POST` | `/api/v1/predictions/recheck-eligibility` | 건강정보·검사값 변경 시 모델 적용 조건 재판정 | P0 | REQ-PRED-005 |
| 24 | `POST` | `/api/v1/predictions/reevaluate` | 최신 정보 기반 위험도 재평가 요청 | P0 | REQ-DASH-004, SR-028 |
| 25 | `POST` | `/api/v1/health-logs` | 일상 건강지표 기록 (체중·허리둘레 실측/추정·가정혈압) | P0 | REQ-LOG-002, DR-014, SR-035 |
| 26 | `GET` | `/api/v1/health-logs` | 일상 건강지표 기록 목록 조회 | P0 | REQ-LOG-002 |
| 27 | `PATCH` | `/api/v1/health-logs/{health_log_id}` | 일상 건강지표 기록 수정 | P0 | REQ-LOG-002 |
| 28 | `DELETE` | `/api/v1/health-logs/{health_log_id}` | 일상 건강지표 기록 삭제 | P0 | REQ-LOG-002 |
| 29 | `GET` | `/api/v1/dashboard` | 건강 추적 대시보드 조회 | P0 | REQ-DASH-001~003, SR-028~029 |

### 20. 모델 적용 조건 판정(A/B/C 분기) 및 위험 예측 실행 · P0

* **Method / Endpoint**: `POST /api/v1/predictions`
* **Description**: 완료된 초기 건강 평가(`questionnaire_id`)와 선택 입력된 혈중 지질검사 기록(`record_id`)을 바탕으로 **분기(`branch`) + 적용 모델(`model_type`) + 예측 기간(`prediction_horizon_years`) + 적용 사유 코드(`reason_code`)**를 판정·저장한다(`REQ-PRED-001~011`).
* **인증**: 필요 (`HEALTH_DATA` 동의 필수)
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Body**:

  ```json
  {
    "questionnaire_id": 105,
    "record_id": 52
  }
  ```

* **Response Body (`201 Created` — B 분기 예시, `prediction_horizon_years` 및 `reason_code` 반영)**:

  ```json
  {
    "prediction_id": 301,
    "questionnaire_id": 105,
    "record_id": 52,
    "branch": "BRANCH_B",
    "care_flow": "PREVENTIVE",
    "model_type": "MODEL_1",
    "model_version": "m1-c3-v1.0",
    "prediction_horizon_years": 5,
    "policy_version": "elig-v2.0",
    "reason_code": "MODEL_APPROVAL_PENDING",
    "reason_message": "초기 건강 평가와 LDL-C 검사 결과가 확인되어 임상 지침 기반 맞춤형 관리 영역을 안내해 드립니다.",
    "execution_status": "COMPLETED",
    "is_result_approved": false,
    "signal_level": null,
    "signal_label": null,
    "management_areas": [
      {
        "category": "DIET",
        "title": "영양 및 식습관",
        "priority": 1,
        "guideline_summary": "포화지방 섭취를 줄이고 식이섬유가 풍부한 식단을 유지하는 것이 LDL 콜레스테롤 관리에 권장됩니다."
      },
      {
        "category": "WEIGHT_WAIST",
        "title": "체중 및 복부비만",
        "priority": 2,
        "guideline_summary": "폐경 이행기 복부비만 예방을 위해 규칙적인 유산소 활동과 허리둘레 관리가 도움이 됩니다."
      }
    ],
    "checkup_guide": {
      "guide_type": "REGULAR_CHECKUP",
      "message": "정기적인 혈중 지질검사와 의료진 상담을 통해 수치 변화를 꾸준히 확인하세요."
    },
    "safety_alert": null,
    "disclaimer": "본 안내는 의료적 진단이나 확정적인 질환 발생 판단이 아니며, 치료 및 처방을 대체하지 않습니다.",
    "created_at": "2026-11-26T14:20:00+09:00"
  }
  ```

* **Response Body (`201 Created` — C 분기 예시: 기진단·복약 관리 흐름)**:

  ```json
  {
    "prediction_id": 302,
    "questionnaire_id": 106,
    "record_id": null,
    "branch": "BRANCH_C",
    "care_flow": "MANAGEMENT",
    "model_type": null,
    "model_version": null,
    "prediction_horizon_years": null,
    "policy_version": "elig-v2.0",
    "reason_code": "EXISTING_HIGH_LDL",
    "reason_message": "현재 지질강하제를 복용 중이시거나 기존 진단을 받으신 경우, 신규 발생 예측 대신 진료지침 기반의 생활습관 관리 흐름으로 안내해 드립니다.",
    "execution_status": "SKIPPED_INELIGIBLE",
    "is_result_approved": false,
    "signal_level": null,
    "signal_label": null,
    "management_areas": [
      {
        "category": "DIET",
        "title": "영양 및 식습관",
        "priority": 1,
        "guideline_summary": "처방약 복용과 함께 포화지방·트랜스지방 섭취를 줄이는 식사요법을 병행해 보세요."
      }
    ],
    "checkup_guide": {
      "guide_type": "GENERAL_MEDICAL_FOLLOWUP",
      "message": "담당 의료진이 안내한 검사 주기와 목표 LDL-C 수치를 기준으로 정기 진료를 이어가세요."
    },
    "safety_alert": null,
    "disclaimer": "복용 중인 약물의 중단이나 용량 변경은 반드시 담당 의료진과 상의하시기 바랍니다.",
    "created_at": "2026-11-26T14:22:00+09:00"
  }
  ```

* **Response Body (`200 OK` — 모델 추론 오류 시 대체 경로 `REQ-PRED-012`)**:

  ```json
  {
    "prediction_id": null,
    "branch": "BRANCH_B",
    "model_type": "MODEL_1",
    "prediction_horizon_years": 5,
    "reason_code": "PREDICTION_FAILED",
    "execution_status": "PREDICTION_FAILED",
    "error_notice": "일시적인 시스템 오류로 예측 처리를 완료하지 못했습니다. 일반 건강관리, 맞춤형 챌린지 및 기록 기능은 정상적으로 이용하실 수 있습니다.",
    "management_areas": [
      {
        "category": "DIET",
        "title": "영양 및 식습관",
        "priority": 1,
        "guideline_summary": "임상 지침에 따른 건강한 식습관 챌린지부터 시작해 보세요."
      }
    ],
    "checkup_guide": {
      "guide_type": "REGULAR_CHECKUP",
      "message": "정기적인 건강검진을 통해 지질 수치를 확인하세요."
    },
    "disclaimer": "본 서비스는 의료적 진단을 대체하지 않습니다."
  }
  ```

* **Status Code**: `201 Created` / `200 OK` (예측 실패 대체 경로) / `400 Bad Request` / `401 Unauthorized` / `403 Forbidden` / `404 Not Found`
* **관련 테이블 · 요구사항**: `risk_predictions` · `REQ-PRED-001~012`, `DR-004`, `DR-013`, `SR-011~013`

### 21. 최신 분기 판정 및 건강관리 안내 결과 조회 · P0

* **Method / Endpoint**: `GET /api/v1/predictions/latest`
* **Description**: 사용자의 현재 유효한 분기(`branch`), 적용 모델(`model_type`), 예측 기간(`prediction_horizon_years`), 사유 코드(`reason_code`) 및 건강관리 안내를 조회한다(`REQ-DASH-003`).
* **인증**: 필요
* **Request Header**: `Authorization: Bearer {access_token}`
* **Response Body (`200 OK`)**: 20번(`POST /api/v1/predictions`) 정상 응답 본문과 동일
* **Status Code**: `200 OK` / `401 Unauthorized` / `404 Not Found`
* **관련 테이블 · 요구사항**: `risk_predictions` · `REQ-DASH-003`, `SR-012`

### 22. 판정 및 예측 이력 목록 조회 · P0

* **Method / Endpoint**: `GET /api/v1/predictions`
* **Description**: 사용자의 분기 판정 이력과 정상 예측 이력을 구분하여 최신순으로 조회한다(`REQ-PRED-011`, `TBD-018`).
* **인증**: 필요
* **Request Header**: `Authorization: Bearer {access_token}`
* **Request Parameter (Query)**: `history_type` (`ALL` | `PREDICTION_ONLY` | `BRANCH_CHANGE`, 기본 `ALL`), `page` (기본 `1`), `size` (기본 `10`)
* **Response Body (`200 OK`)**:

  ```json
  {
    "items": [
      {
        "prediction_id": 310,
        "trigger_type": "ELIGIBILITY_RECHECK",
        "branch": "BRANCH_B",
        "model_type": "MODEL_1",
        "model_version": "m1-c3-v1.0",
        "prediction_horizon_years": 5,
        "policy_version": "elig-v2.0",
        "reason_code": "MODEL_APPROVAL_PENDING",
        "signal_level": null,
        "summary_text": "혈중 지질검사 결과 반영 — B 분기 건강관리 안내",
        "created_at": "2026-11-26T15:00:00+09:00"
      },
      {
        "prediction_id": 301,
        "trigger_type": "INITIAL",
        "branch": "BRANCH_A",
        "model_type": null,
        "model_version": null,
        "prediction_horizon_years": null,
        "policy_version": "elig-v2.0",
        "reason_code": "LDL_MISSING",
        "signal_level": null,
        "summary_text": "초기 건강 평가 완료 — LDL-C 미입력 A 분기 안내",
        "created_at": "2026-11-10T10:20:00+09:00"
      }
    ],
    "total": 2,
    "page": 1,
    "size": 10,
    "disclaimer": "판정 및 안내 이력은 실제 혈액검사 결과와 구분되며, 질환의 호전이나 치료 효과를 의미하지 않습니다."
  }
  ```

* **Status Code**: `200 OK` / `401 Unauthorized`
* **관련 테이블 · 요구사항**: `risk_predictions` · `REQ-PRED-011`, `REQ-DASH-003`, `DR-004`, `DR-013`, `TBD-018`

### 23. 모델 적용 조건 재판정 · P0

* **Method / Endpoint**: `POST /api/v1/predictions/recheck-eligibility`
* **Description**: 지질검사 추가 입력, 폐경 단계 변경, 고LDL 진단 또는 지질강하제 복용 변경 시 전체 적용 조건을 재판정하고 새 `reason_code`와 분기를 저장한다(`REQ-PRED-005`).
* **인증**: 필요
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Body**:

  ```json
  {
    "change_source": "MEDICATION_UPDATED"
  }
  ```

* **Response Body (`200 OK`)**:

  ```json
  {
    "prediction_id": 315,
    "previous_branch": "BRANCH_B",
    "current_branch": "BRANCH_C",
    "branch_changed": true,
    "care_flow": "MANAGEMENT",
    "model_type": null,
    "prediction_horizon_years": null,
    "policy_version": "elig-v2.0",
    "reason_code": "EXISTING_HIGH_LDL",
    "reason_message": "지질강하제 복용 이력이 확인되어 신규 발생 예측 대상에서 일반 건강관리(관리 흐름)로 전환되었습니다.",
    "created_at": "2026-11-26T16:00:00+09:00"
  }
  ```

* **Status Code**: `200 OK` / `401 Unauthorized` / `404 Not Found`
* **관련 테이블 · 요구사항**: `risk_predictions`, `questionnaires`, `checkup_records`, `medication_logs` · `REQ-PRED-005`, `TBD-007`

### 24. 최신 정보 기반 위험도 재평가 요청 · P0

* **Method / Endpoint**: `POST /api/v1/predictions/reevaluate`
* **Description**: 모델 학습 변수 정의와 일치하는 최신 건강정보를 바탕으로 적용 조건 재판정 및 검증된 범위 내 위험도 재평가를 수행한다(`REQ-DASH-004`, `SR-028`).
* **인증**: 필요
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Body**:

  ```json
  {
    "questionnaire_id": 112,
    "record_id": 58
  }
  ```

* **Response Body (`201 Created`)**: 20번(`POST /api/v1/predictions`) 응답 구조와 동일 (`trigger_type: "RISK_REEVALUATION"`)
* **Status Code**: `201 Created` / `400 Bad Request` / `401 Unauthorized` / `409 Conflict`
* **관련 테이블 · 요구사항**: `risk_predictions` · `REQ-DASH-004`, `REQ-PRED-005`, `DR-014`, `SR-028~029`

### 25. 일상 건강지표 기록 (체중·허리둘레 실측/추정·가정혈압) · P0

* **Method / Endpoint**: `POST /api/v1/health-logs`
* **Description**: 사용자가 일상에서 측정한 체중, 허리둘레(실측/추정 구분 포함), 가정혈압을 기록한다(`REQ-LOG-002`, `DR-014`).
* **인증**: 필요 (`HEALTH_DATA` 동의 필수)
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Body**:

  ```json
  {
    "log_date": "2026-11-26",
    "measured_at": "2026-11-26T07:30:00+09:00",
    "weight": 57.8,
    "waist_size": 80.5,
    "waist_measure_type": "MEASURED",
    "pressure_systolic": 182,
    "pressure_diastolic": 108,
    "bp_arm": "RIGHT",
    "bp_session": "MORNING",
    "reading_order": 1,
    "is_recheck_after_high": false,
    "has_emergency_symptom": false,
    "memo": "기상 후 화장실 다녀와서 5분 휴식 후 측정"
  }
  ```

* **Response Body (`201 Created` — `SBP ≥ 180` 안전 안내 작동 예시 `SR-035`)**:

  ```json
  {
    "health_log_id": 88,
    "log_date": "2026-11-26",
    "measured_at": "2026-11-26T07:30:00+09:00",
    "weight": 57.8,
    "waist_size": 80.5,
    "waist_measure_type": "MEASURED",
    "pressure_systolic": 182,
    "pressure_diastolic": 108,
    "safety_alert": {
      "alert_type": "BP_RECHECK_180_110",
      "title": "안정을 취한 뒤 혈압을 다시 측정해 주세요",
      "message": "수축기 혈압 180 mmHg 이상 또는 이완기 혈압 110 mmHg 이상이 확인되었습니다. 바른 자세로 5분간 휴식한 뒤 1분 이상 간격으로 재측정해 주세요. 재측정 중 흉통·호흡곤란·마비 등 증상이 나타나면 즉시 119에 연락하세요.",
      "require_immediate_119": false
    },
    "created_at": "2026-11-26T07:31:00+09:00"
  }
  ```

* **Status Code**:
  * `201 Created`: 기록 저장 성공
  * `400 Bad Request`: 기록할 지표가 없음, **`waist_size` 입력 시 `waist_measure_type` 누락(또는 그 반대)**, 혈압 수축기·이완기 한쪽만 입력 (`VALIDATION_ERROR`)
  * `401 Unauthorized` / `403 Forbidden`
* **관련 테이블 · 요구사항**: `health_logs` · `REQ-LOG-002`, `DR-014`, `NFR-103`, `SR-035`

### 26. 일상 건강지표 기록 목록 조회 · P0

* **Method / Endpoint**: `GET /api/v1/health-logs`
* **Description**: 사용자가 기록한 체중, 허리둘레(`waist_measure_type` 포함), 가정혈압 원본 내역을 최신순으로 조회한다.
* **인증**: 필요
* **Request Header**: `Authorization: Bearer {access_token}`
* **Request Parameter (Query)**: `from_date` (`YYYY-MM-DD`, 선택), `to_date` (`YYYY-MM-DD`, 선택), `page` (기본 `1`), `size` (기본 `20`)
* **Response Body (`200 OK`)**:

  ```json
  {
    "items": [
      {
        "health_log_id": 88,
        "log_date": "2026-11-26",
        "measured_at": "2026-11-26T07:30:00+09:00",
        "weight": 57.8,
        "waist_size": 80.5,
        "waist_measure_type": "MEASURED",
        "pressure_systolic": 182,
        "pressure_diastolic": 108,
        "bp_session": "MORNING",
        "memo": "기상 후 화장실 다녀와서 5분 휴식 후 측정"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 20
  }
  ```

* **Status Code**: `200 OK` / `401 Unauthorized`
* **관련 테이블 · 요구사항**: `health_logs` · `REQ-LOG-002`, `SR-003`

### 27. 일상 건강지표 기록 수정 · P0

* **Method / Endpoint**: `PATCH /api/v1/health-logs/{health_log_id}`
* **Description**: 본인이 작성한 건강지표 기록을 수정한다. 허리둘레를 수정할 경우 `waist_measure_type`도 함께 수정 가능하다.
* **인증**: 필요
* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
* **Request Parameter (Path)**: `health_log_id` (bigint)
* **Request Body**:

  ```json
  {
    "waist_size": 80.0,
    "waist_measure_type": "MEASURED"
  }
  ```

* **Response Body (`200 OK`)**: 수정된 기록 객체 및 `safety_alert` 반환
* **Status Code**: `200 OK` / `400 Bad Request` / `401 Unauthorized` / `403 Forbidden` / `404 Not Found`
* **관련 테이블 · 요구사항**: `health_logs` · `REQ-LOG-002`, `SR-003`, `SR-035`

### 28. 일상 건강지표 기록 삭제 · P0

* **Method / Endpoint**: `DELETE /api/v1/health-logs/{health_log_id}`
* **Description**: 본인이 작성한 건강지표 기록 1건을 삭제한다.
* **인증**: 필요
* **Request Header**: `Authorization: Bearer {access_token}`
* **Request Parameter (Path)**: `health_log_id` (bigint)
* **Response Body (`204 No Content`)**: (본문 없음)
* **Status Code**: `204 No Content` / `401 Unauthorized` / `403 Forbidden` / `404 Not Found`
* **관련 테이블 · 요구사항**: `health_logs` · `REQ-LOG-002`, `SR-003`

### 29. 건강 추적 대시보드 조회 · P0

* **Method / Endpoint**: `GET /api/v1/dashboard`
* **Description**: 지질검사 추이, 건강지표 추이(허리둘레 실측/추정 구분 표시), 챌린지 달성률 추이 및 현재 분기·사유 상태를 분리하여 반환한다(`REQ-DASH-001~003`).
* **인증**: 필요
* **Request Header**: `Authorization: Bearer {access_token}`
* **Request Parameter (Query)**: `period` (`1m` | `3m` | `6m` | `1y`, 기본 `3m`)
* **Response Body (`200 OK`)**:

  ```json
  {
    "period": "3m",
    "current_status": {
      "branch": "BRANCH_B",
      "reason_code": "MODEL_APPROVAL_PENDING",
      "model_type": "MODEL_1",
      "prediction_horizon_years": 5,
      "care_flow": "PREVENTIVE",
      "last_evaluated_at": "2026-11-26T14:20:00+09:00"
    },
    "lipid_checkup_trends": {
      "unit": "mg/dL",
      "doctor_target_ldl": {
        "value": 130.0,
        "label": "사용자 직접 입력 의료진 권장 목표치"
      },
      "points": [
        {
          "checkup_date": "2026-11-15",
          "ldl_cholesterol": 136.0,
          "hdl_cholesterol": 54.0,
          "total_cholesterol": 218.0,
          "triglycerides": 118.0
        }
      ]
    },
    "health_metric_trends": {
      "home_bp_weekly_avg": {
        "reference_line": {
          "systolic": 135,
          "diastolic": 85,
          "note": "가정혈압 관리 참고 기준선 (진단 기준 아님)"
        },
        "points": [
          {
            "week_start": "2026-11-16",
            "measured_days": 6,
            "avg_systolic": 124.2,
            "avg_diastolic": 79.5,
            "first_day_excluded": true
          }
        ]
      },
      "waist_size_trends": {
        "reference_line_cm": 85.0,
        "points": [
          { "date": "2026-11-01", "waist_size": 82.0, "waist_measure_type": "ESTIMATED", "weight": 58.4 },
          { "date": "2026-11-26", "waist_size": 80.5, "waist_measure_type": "MEASURED", "weight": 57.8 }
        ]
      },
      "weekly_aerobic_minutes": [
        { "week_start": "2026-11-09", "effective_minutes": 120 },
        { "week_start": "2026-11-16", "effective_minutes": 155 }
      ]
    },
    "challenge_achievement_trends": {
      "points": [
        { "week_start": "2026-11-09", "achievement_rate": 0.72 },
        { "week_start": "2026-11-16", "achievement_rate": 0.85 }
      ]
    },
    "disclaimer": "실제 검사 수치, 건강지표 기록 및 챌린지 달성률은 각각 별도의 참고 지표이며, 생활습관 달성률 향상이나 지표 변화가 질환 예방·치료 효과를 보장하지 않습니다."
  }
  ```

* **Status Code**: `200 OK` / `400 Bad Request` / `401 Unauthorized`
* **관련 테이블 · 요구사항**: `checkup_records`, `health_logs`, `daily_challenges`, `risk_predictions` · `REQ-DASH-001~003`, `DR-014`, `SR-028~029`