# WELLOOP API 명세서 v2.0 — 영역 05 (LLM 건강 코칭·상담 리포트·식단 분석·안전 안내)

<!-- 05 START · LLM 코칭·리포트·식단 분석 · 담당: ______ -->

## 05. LLM 건강 코칭 · 상담용 리포트 · 식단 이미지 분석 · 안전 안내

* **관련 테이블**: `coach_messages`(및 대화 스레드), `health_reports`, `diet_analyses`, `safety_keywords`

* **관련 요구사항**: `REQ-LLM-001~002`, `REQ-RPT-001~003`, `REQ-FOOD-001`, `NFR-102`, `NFR-108`, `SR-011`, `SR-014~015`, `SR-018~019`, `SR-026`, `SR-030~033`, `SR-035`

* **공통 Enum 정의**:

  * `Safety_alert_type` (공통 안전 안내 유형):

    * `EMERGENCY_119`: 흉통, 호흡곤란, 의식 저하, 마비 등 즉시 119 신고 및 응급실 방문 우선 안내 (`SR-033`, `SR-035`)

    * `BP_RECHECK_180_110`: 증상 없는 `SBP ≥ 180` 또는 `DBP ≥ 110` 5분 휴식 후 재측정 안내 (`SR-035`)

    * `BP_IMMEDIATE_MEDICAL_CONTACT`: 재측정 후에도 `180/110` 이상 지속 시 즉시 의료진 연락 안내 (`SR-035`)

    * `LDL_HIGH_160`: `LDL-C ≥ 160` mg/dL 의료기관 방문 및 전문가 상담 안내 (`REQ-PRED-001`, `SR-014`)

    * `LDL_VERY_HIGH_190`: `LDL-C ≥ 190` mg/dL 가까운 시일 내 진료 권유 강화 (`REQ-PRED-001`, `SR-014`)

    * `MENTAL_CRISIS_109`: 자해·극단적 선택 위기 표현 감지 시 상담전화(109) 즉시 안내

  * `Report_status`: `PENDING` (생성 중) / `COMPLETED` (생성 완료) / `FAILED` (생성 실패)

  * `Meal_type`: `BREAKFAST` (아침) / `LUNCH` (점심) / `DINNER` (저녁) / `SNACK` (간식)

  * `Ldl_diet_grade`: `GOOD` (LDL 관리에 권장되는 구성) / `MODERATE` (보통 — 일부 보완 권장) / `CAUTION` (포화지방·정제탄수화물 주의 필요)

### 05 구역 API 목록 요약

| No | Method | Endpoint | 설명 | 우선순위 | 관련 요구사항 | 
| ----- | ----- | ----- | ----- | ----- | ----- | 
| 44 | `GET` | `/api/v1/coach/today` | 오늘의 맞춤형 건강 코칭 메시지 조회 (임상 지침 기반, 장애 시 규칙 문구 폴백) | P1 | REQ-LLM-001, NFR-102, SR-030\~031 | 
| 45 | `POST` | `/api/v1/coach/chat` | LLM 건강 코칭 대화 (SSE 스트리밍 + 규칙 기반 응급·금칙어 선행 검사 + RAG) | P1 (RAG P2) | REQ-LLM-001\~002, NFR-108, SR-030\~033 | 
| 46 | `GET` | `/api/v1/coach/threads/{thread_id}/messages` | 코칭 대화 내역 조회 | P1 | REQ-LLM-001 | 
| 47 | `GET` | `/api/v1/safety/guides/{alert_type}` | 응급상황 및 이상 소견별 고정 안전 안내문 조회 | 필수\* | SR-014, SR-033, SR-035 | 
| 48 | `POST` | `/api/v1/reports` | 의료진 상담용 기간별 건강관리 리포트 생성 (보유 기록 기반 부분 리포트 허용) | P1 | REQ-RPT-001\~002, SR-015 | 
| 49 | `GET` | `/api/v1/reports` | 생성된 건강관리 리포트 목록 조회 | P1 | REQ-RPT-001 | 
| 50 | `GET` | `/api/v1/reports/{report_id}` | 건강관리 리포트 상세 스냅샷 조회 | P1 | REQ-RPT-001\~002, SR-015 | 
| 51 | `GET` | `/api/v1/reports/{report_id}/pdf` | 건강관리 리포트 PDF 생성 요청 및 다운로드 URL 조회 | P2 | REQ-RPT-003 | 
| 52 | `POST` | `/api/v1/diet-analyses` | 식단 이미지 업로드 및 LDL 관리 적합도 피드백 분석 | P2 | REQ-FOOD-001, SR-018\~019 | 
| 53 | `GET` | `/api/v1/diet-analyses` | 식단 이미지 분석 이력 목록 조회 | P2 | REQ-FOOD-001 | 

### 44. 오늘의 맞춤형 건강 코칭 메시지 조회 · P1

* **Method / Endpoint**: `GET /api/v1/coach/today`

* **Description**: 사용자의 현재 분기(`BRANCH_A`/`B`/`C`), 관리 필요 영역, 최근 챌린지 실천 상태를 바탕으로 임상 지침에 근거한 일일 생활습관 피드백을 제공한다(`REQ-LLM-001`, `SR-031`). 하루 1회 생성 후 저장본을 재사용하여 LLM 호출 비용을 통제한다(`NFR-108`).

* **인증**: 필요 (`AI_PROCESSING` 동의 필요 — 단, 외부 LLM 장애 시 규칙 기반 기본 안내로 폴백 `NFR-102`)

* **Request Header**: `Authorization: Bearer {access_token}`

* **Request Parameter (Query)**: `date` (string `YYYY-MM-DD`, 선택, 기본 오늘)

* **Request Body**: -

* **Response Body (`200 OK`)**:

  ```json
  {
    "coach_message_id": 120,
    "date": "2026-11-26",
    "message": "이번 주 빠르게 걷기 챌린지를 꾸준히 실천하고 계시네요! 외식 일정이 있으시다면 기름진 부위보다 살코기와 채소 반찬을 먼저 드시는 것만으로도 좋은 LDL 관리 습관이 됩니다.",
    "based_on_context": [
      "BRANCH_B",
      "AREA_DIET",
      "CHALLENGE_ACT_02_IN_PROGRESS"
    ],
    "guideline_sources": [
      "한국지질·동맥경화학회 이상지질혈증 진료지침 — 식사요법"
    ],
    "source_type": "LLM",
    "safety_alert": null,
    "disclaimer": "AI 코칭은 검증된 임상 지침에 기반한 생활습관 안내이며, 의학적 진단·약물 처방·호르몬 요법 결정을 대체하지 않습니다.",
    "generated_at": "2026-11-26T07:00:00+09:00"
  }
  ```

* **Status Code**:

  * `200 OK`: 조회 성공 (외부 LLM API 장애 시에도 `500` 에러를 내지 않고 `source_type: "RULE_FALLBACK"` 고정 가이드 문구 반환 `NFR-102`)

  * `401 Unauthorized`: 토큰 없음·만료

  * `403 Forbidden`: 건강정보 또는 AI 처리 동의 미확보 (`CONSENT_REQUIRED`)

* **관련 테이블 · 요구사항**: `coach_messages` · `REQ-LLM-001`, `NFR-102`, `NFR-108`, `SR-030~031`, `SR-034`

### 45. LLM 건강 코칭 대화 (SSE 스트리밍 + RAG) · P1 (RAG P2)

* **Method / Endpoint**: `POST /api/v1/coach/chat`

* **Description**: 사용자의 생활습관·건강관리 질문에 대해 검증된 임상 지침 및 건강관리 자료(RAG 검색 근거 `REQ-LLM-002`)를 바탕으로 답변을 스트리밍 전송한다. **LLM 호출 전 서버 규칙 기반 안전장치를 선행 적용**하여 응급 의심 증상은 즉시 119 안내로 전환하고, 약물·호르몬제 처방/변경 요구는 의료진 상담 안내로 안전하게 제한한다(`SR-030~033`).

* **인증**: 필요 (`HEALTH_DATA` 및 `AI_PROCESSING` 동의 필수)

* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`, `Accept: text/event-stream`

* **Request Parameter**: -

* **Request Body**:

  ```json
  {
    "thread_id": null,
    "message": "폐경 이행기라 콜레스테롤이 걱정되는데 호르몬제를 먹으면 LDL 수치가 내려가나요?"
  }
  ```

* **Response Body (`200 OK` · `text/event-stream`)**:

  ```text
  event: meta
  data: {"thread_id":"th_9a2c","user_message_id":201}

  event: token
  data: {"text":"폐경 이행기에는 여성호르몬 변화로 LDL 콜레스테롤 수치가 상승하기 쉬워 걱정이 되실 수 있습니다. "}

  event: token
  data: {"text":"다만 고LDL콜레스테롤혈증 등 심혈관 질환 예방만을 목적으로 호르몬 요법을 시작하거나 변경하는 것은 권장되지 않으며, 호르몬제 복용 여부는 증상과 건강 상태를 종합해 반드시 담당 의료진과 상의하셔야 합니다."}

  event: done
  data: {"assistant_message_id":202,"citations":[{"title":"한국지질·동맥경화학회 진료지침","section":"여성 및 폐경 이행기 관리"}],"disclaimer":"본 답변은 생활습관 참고 정보이며 의료적 진단·처방을 대신하지 않습니다."}
  ```

  *(흉통·호흡곤란 등 응급 키워드 감지 시 — LLM 호출 없이 즉시 반환 `SR-033`)*:

  ```text
  event: safety_alert
  data: {"alert_type":"EMERGENCY_119","title":"즉시 119 신고 또는 응급실 방문이 필요합니다","message":"가슴 통증, 호흡곤란 등 응급 증상이 의심되는 경우 일반 건강 코칭보다 즉시 119에 연락하거나 가까운 응급실을 방문해 주세요."}
  ```

* **Status Code**:

  * `200 OK`: 스트림 시작 성공

  * `400 Bad Request`: 빈 메시지 또는 최대 글자 수(500자) 초과 (`VALIDATION_ERROR`)

  * `401 Unauthorized`: 토큰 없음·만료

  * `403 Forbidden`: `AI_PROCESSING` 동의 미확보 (`CONSENT_REQUIRED`)

  * `404 Not Found`: 존재하지 않거나 본인 소유가 아닌 `thread_id` (`SR-003`)

  * `429 Too Many Requests`: 일일 사용자별 LLM 호출 횟수/토큰 상한 초과 (`NFR-108` 비용 통제)

* **관련 테이블 · 요구사항**: `coach_messages`, `safety_keywords` · `REQ-LLM-001~002`, `NFR-102`, `NFR-108`, `SR-026`, `SR-030~033`

* **LLM · RAG 의료 안전 가드레일 (`SR-030~033` 필수 적용)**:

  1. **입력 선행 필터링 (규칙 기반 `SR-033`)**: `safety_keywords`의 `EMERGENCY` 키워드(흉통, 호흡곤란, 한쪽 마비 등) 감지 시 LLM을 호출하지 않고 즉시 `EMERGENCY_119` 이벤트를 반환한다.

  2. **금지 의료 행위 차단 (`SR-026`, `SR-030`)**: 진단 확정, 지질강하제·기존 복용약 시작/중단/용량 조절 권고, 질환 예방 목적의 호르몬 요법(MHT) 권고를 시스템 프롬프트 및 출력 필터로 차단한다.

  3. **환각 방지 (`SR-032`)**: 승인된 임상 지침(RAG 문서)에 근거가 없는 의학 정보는 단정적으로 생성하지 않고 의료진 상담을 권유하도록 처리하며, 입·출력 토큰과 비용을 관리자 통계용으로 기록한다(`NFR-108`).

### 46. 코칭 대화 내역 조회 · P1

* **Method / Endpoint**: `GET /api/v1/coach/threads/{thread_id}/messages`

* **Description**: 특정 대화 스레드의 이전 질문·답변 및 인용 근거(`citations`) 목록을 조회한다. 본인의 스레드만 조회 가능하다(`SR-003`).

* **인증**: 필요

* **Request Header**: `Authorization: Bearer {access_token}`

* **Request Parameter**: Path `thread_id` (string) · Query `before_id` (bigint, 선택), `size` (integer, 기본 `20`)

* **Request Body**: -

* **Response Body (`200 OK`)**:

  ```json
  {
    "thread_id": "th_9a2c",
    "items": [
      {
        "message_id": 201,
        "role": "USER",
        "content": "폐경 이행기라 콜레스테롤이 걱정되는데 호르몬제를 먹으면 LDL 수치가 내려가나요?",
        "created_at": "2026-11-26T16:10:00+09:00"
      },
      {
        "message_id": 202,
        "role": "ASSISTANT",
        "content": "폐경 이행기에는 여성호르몬 변화로...",
        "citations": [
          { "title": "한국지질·동맥경화학회 진료지침", "section": "여성 및 폐경 이행기 관리" }
        ],
        "created_at": "2026-11-26T16:10:03+09:00"
      }
    ],
    "has_more": false
  }
  ```

* **Status Code**: `200 OK` / `401 Unauthorized` / `403 Forbidden` / `404 Not Found`

* **관련 테이블 · 요구사항**: `coach_messages` · `REQ-LLM-001`, `SR-003`

### 47. 응급상황 및 이상 소견별 고정 안전 안내문 조회 · 필수

* **Method / Endpoint**: `GET /api/v1/safety/guides/{alert_type}`

* **Description**: 문진(02 구역), 지질검사·가정혈압 기록(02·03 구역), 실천 기록(04 구역), AI 코칭(05 구역) 응답에서 `safety_alert`가 반환되었을 때 화면 모달/전면 배너에 표시할 검증된 고정 행동 수칙과 전화 연결 정보를 조회한다(`SR-014`, `SR-033`, `SR-035`).

* **인증**: 불필요 (세션 만료 상태에서도 응급 안내는 즉시 열람 가능해야 함)

* **Request Header**: `Content-Type: application/json`

* **Request Parameter (Path)**: `alert_type` (`Safety_alert_type` Enum 값)

* **Request Body**: -

* **Response Body (`200 OK` — `EMERGENCY_119` 예시)**:

  ```json
  {
    "alert_type": "EMERGENCY_119",
    "title": "지금은 즉시 안전 확인과 응급 도움이 먼저입니다",
    "symptom_check_question": "갑작스러운 가슴 통증·압박감, 호흡곤란, 의식 저하, 한쪽 팔다리 마비나 발음 어눌함이 있으신가요?",
    "primary_action": {
      "label": "119에 즉시 전화하기",
      "action_type": "TEL",
      "value": "119"
    },
    "action_guides": [
      "재측정이나 증상 호전을 기다리지 말고 즉시 119에 신고하거나 응급실을 방문하세요.",
      "직접 운전하지 마시고 주변 사람이나 구급대의 도움을 받으세요."
    ],
    "disclaimer": "본 안내는 응급 안전을 위한 행동 수칙이며 의학적 진단을 확정하지 않습니다."
  }
  ```

* **Status Code**: `200 OK` / `404 Not Found` (정의되지 않은 `alert_type`)

* **관련 테이블 · 요구사항**: 서버 고정 설정(또는 안전 안내 마스터) · `SR-014`, `SR-033`, `SR-035`

### 48. 의료진 상담용 기간별 건강관리 리포트 생성 · P1

* **Method / Endpoint**: `POST /api/v1/reports`

* **Description**: 사용자가 선택한 기간(`period_start` \~ `period_end`) 동안의 실제 혈중 지질검사 결과, 일상 건강지표(가정혈압·체중·허리둘레), 폐경 관련 증상, 복용 이력, 생활습관 챌린지 기록을 요약하여 스냅샷(`summary_snapshot`)으로 생성한다(`REQ-RPT-001`). **모든 항목의 입력을 강제하지 않으며, 사용자가 보유한 기록만으로 부분 리포트를 생성하고 미입력 영역은 `'미기록'`으로 명확히 구분해 표시**한다(`REQ-RPT-002`).

* **인증**: 필요 (`HEALTH_DATA` 동의 필수)

* **Request Header**: `Content-Type: application/json`, `Authorization: Bearer {access_token}`

* **Request Parameter**: -

* **Request Body**:

  ```json
  {
    "period_start": "2026-09-01",
    "period_end": "2026-11-26",
    "include_sections": [
      "LIPID_CHECKUPS",
      "HEALTH_METRICS",
      "MENOPAUSE_SYMPTOMS",
      "MEDICATIONS",
      "LIFESTYLE_CHALLENGES"
    ]
  }
  ```

* **Response Body (`201 Created`)**:

  ```json
  {
    "report_id": 45,
    "period_start": "2026-09-01",
    "period_end": "2026-11-26",
    "status": "COMPLETED",
    "is_partial_report": true,
    "recorded_sections": [
      "LIPID_CHECKUPS",
      "HEALTH_METRICS",
      "MEDICATIONS",
      "LIFESTYLE_CHALLENGES"
    ],
    "unrecorded_sections": [
      "MENOPAUSE_SYMPTOMS"
    ],
    "summary_snapshot": {
      "lipid_summary": {
        "latest_checkup_date": "2026-11-15",
        "ldl_cholesterol": 136.0,
        "hdl_cholesterol": 54.0,
        "triglycerides": 118.0,
        "unit": "mg/dL",
        "doctor_target_ldl": 130.0
      },
      "home_bp_summary": {
        "measured_days": 18,
        "avg_systolic": 125.4,
        "avg_diastolic": 80.1,
        "high_bp_alert_count": 1
      },
      "body_composition_summary": {
        "latest_weight_kg": 57.8,
        "latest_waist_cm": 80.5
      },
      "menopause_symptom_summary": null,
      "medication_summary": [
        {
          "medication_type": "LIPID_MED",
          "name": "스타틴 계열 처방약",
          "status": "ACTIVE",
          "start_date": "2026-11-25"
        }
      ],
      "lifestyle_summary": {
        "avg_weekly_challenge_rate": 0.76,
        "avg_weekly_aerobic_minutes": 145
      }
    },
    "pdf_url": null,
    "disclaimer": "본 리포트는 사용자가 직접 입력·기록한 정보를 요약한 진료 상담용 참고 자료이며, 의학적 진단 결과서가 아닙니다.",
    "created_at": "2026-11-26T16:20:00+09:00"
  }
  ```

* **Status Code**:

  * `201 Created`: 리포트 스냅샷 생성 완료

  * `400 Bad Request`: `period_start > period_end`, 미래 종료일 지정, 선택 기간 내 기록이 전무하여 요약할 데이터가 0건인 경우 (`VALIDATION_ERROR`)

  * `401 Unauthorized`: 토큰 없음·만료

  * `403 Forbidden`: 건강정보 동의 미확보 (`CONSENT_REQUIRED`)

* **관련 테이블 · 요구사항**: `health_reports` · `REQ-RPT-001~002`, `REQ-LOG-006`, `SR-015`, `TBD-024`

* **비고**: 생성 이후 사용자가 과거 기록을 수정하더라도 당시 진료 상담에 활용한 리포트 원본을 보존할 수 있도록 ERD 제안안대로 `summary_snapshot` (`json`) 컬럼에 사본을 저장한다. AI 예측 확률이나 미승인 단계는 진단 결과로 오인되지 않도록 리포트에 포함하지 않는다(`SR-013`, `SR-015`).

### 49. 생성된 건강관리 리포트 목록 조회 · P1

* **Method / Endpoint**: `GET /api/v1/reports`

* **Description**: 본인이 생성한 의료진 상담용 건강관리 리포트 이력 목록을 최신순으로 조회한다.

* **인증**: 필요

* **Request Header**: `Authorization: Bearer {access_token}`

* **Request Parameter (Query)**: `page` (기본 `1`), `size` (기본 `10`)

* **Request Body**: -

* **Response Body (`200 OK`)**:

  ```json
  {
    "items": [
      {
        "report_id": 45,
        "period_start": "2026-09-01",
        "period_end": "2026-11-26",
        "status": "COMPLETED",
        "is_partial_report": true,
        "has_pdf": false,
        "created_at": "2026-11-26T16:20:00+09:00"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 10
  }
  ```

* **Status Code**: `200 OK` / `401 Unauthorized`

* **관련 테이블 · 요구사항**: `health_reports` · `REQ-RPT-001`, `SR-003`

### 50. 건강관리 리포트 상세 스냅샷 조회 · P1

* **Method / Endpoint**: `GET /api/v1/reports/{report_id}`

* **Description**: 특정 건강관리 리포트의 상세 요약 데이터(`summary_snapshot`)를 조회한다.

* **인증**: 필요

* **Request Header**: `Authorization: Bearer {access_token}`

* **Request Parameter (Path)**: `report_id` (bigint)

* **Request Body**: -

* **Response Body (`200 OK`)**: 48번(`POST /api/v1/reports`) 응답 본문과 동일

* **Status Code**: `200 OK` / `401 Unauthorized` / `403 Forbidden` (타인 리포트 접근 차단 `SR-003`) / `404 Not Found`

* **관련 테이블 · 요구사항**: `health_reports` · `REQ-RPT-001~002`, `SR-003`, `SR-015`

### 51. 건강관리 리포트 PDF 다운로드 · P2

* **Method / Endpoint**: `GET /api/v1/reports/{report_id}/pdf`

* **Description**: 진료실 지참·인쇄용으로 건강관리 리포트를 PDF 파일로 변환하여 서명된 다운로드 URL(또는 `application/pdf` 바이너리 스트림)을 반환한다(`REQ-RPT-003`). 비동기 생성 중일 때는 `Report_status` (`PENDING`)를 반환한다.

* **인증**: 필요

* **Request Header**: `Authorization: Bearer {access_token}`

* **Request Parameter (Path)**: `report_id` (bigint)

* **Request Body**: -

* **Response Body (`200 OK`)**:

  ```json
  {
    "report_id": 45,
    "status": "COMPLETED",
    "pdf_url": "https://storage.welloop.example.com/reports/45_signed.pdf?expires=...",
    "expires_in": 600
  }
  ```

* **Status Code**: `200 OK` / `202 Accepted` (`status: "PENDING"` 비동기 렌더링 중) / `401 Unauthorized` / `403 Forbidden` / `404 Not Found`

* **관련 테이블 · 요구사항**: `health_reports` · `REQ-RPT-003`, `SR-003`, `SR-015`, `TBD-024`

### 52. 식단 이미지 업로드 및 LDL 관리 적합도 피드백 분석 · P2

* **Method / Endpoint**: `POST /api/v1/diet-analyses`

* **Description**: 사용자가 업로드한 식단 사진에서 식품을 인식(`detected_foods`)하고 포화지방 감소·불포화지방 대체·식이섬유 증진 중심의 LDL 관리 적합도 등급(`Ldl_diet_grade`)과 식습관 개선 방향을 안내한다(`REQ-FOOD-001`, `SR-018`). **사진 한 장에만 근거한 정밀 칼로리(kcal)나 영양소 섭취량(g, mg) 수치는 제공하지 않는다(`REQ-FOOD-001`).**

* **인증**: 필요 (`HEALTH_DATA` 및 `AI_PROCESSING` 동의 필수)

* **Request Header**: `Content-Type: multipart/form-data`, `Authorization: Bearer {access_token}`

* **Request Parameter**: -

* **Request Body (`multipart/form-data`)**:

  * `image` (file, 필수: `jpg`, `jpeg`, `png`, `webp`, 최대 10MB)

  * `meal_type` (string `Meal_type`, 필수: `BREAKFAST` | `LUNCH` | `DINNER` | `SNACK`)

  * `eaten_at` (string ISO 8601, 선택, 기본 현재 시각)

* **Response Body (`201 Created`)**:

  ```json
  {
    "diet_analysis_id": 33,
    "meal_type": "LUNCH",
    "image_url": "https://storage.welloop.example.com/diets/33.jpg",
    "detected_foods": [
      { "name": "고등어구이", "food_group": "UNSATURATED_FISH" },
      { "name": "현미밥", "food_group": "WHOLE_GRAIN" },
      { "name": "된장찌개", "food_group": "SOUP" },
      { "name": "나물무침", "food_group": "VEGETABLE_FIBER" }
    ],
    "ldl_grade": "GOOD",
    "ldl_grade_label": "LDL 관리에 권장되는 식단 구성",
    "feedback_content": "등푸른생선(불포화지방)과 통곡물·채소(식이섬유)가 고루 포함되어 LDL 콜레스테롤 관리에 아주 좋은 식사입니다. 찌개 국물만 절반 정도로 남기시면 더욱 균형 잡힌 식습관이 됩니다.",
    "eaten_at": "2026-11-26T12:30:00+09:00",
    "disclaimer": "이미지 기반 식품 인식 결과로 실제 조리법·섭취량과 차이가 있을 수 있으며, 정밀 영양소 분석이나 의학적 식사 처방을 대체하지 않습니다.",
    "created_at": "2026-11-26T12:31:05+09:00"
  }
  ```

* **Status Code**:

  * `201 Created`: 식단 이미지 분석 및 저장 성공

  * `400 Bad Request`: 지원하지 않는 이미지 확장자·용량 초과, 음식이 전혀 인식되지 않은 이미지 (`UNRECOGNIZABLE_FOOD_IMAGE`)

  * `401 Unauthorized`: 토큰 없음·만료

  * `403 Forbidden`: 동의 미확보 (`CONSENT_REQUIRED`)

  * `503 Service Unavailable`: 외부 Vision/CV 모델 일시 장애 (`AI_UNAVAILABLE` — 핵심 기록·챌린지 기능에는 영향 없음 `NFR-102`)

* **관련 테이블 · 요구사항**: `diet_analyses` · `REQ-FOOD-001`, `NFR-102`, `SR-018~019`, `TBD-029`

### 53. 식단 이미지 분석 이력 목록 조회 · P2

* **Method / Endpoint**: `GET /api/v1/diet-analyses`

* **Description**: 사용자가 분석·저장한 식단 이미지 및 LDL 적합도 피드백 이력을 최신 식사 일시(`eaten_at`) 순으로 조회한다.

* **인증**: 필요

* **Request Header**: `Authorization: Bearer {access_token}`

* **Request Parameter (Query)**: `from_date` (`YYYY-MM-DD`, 선택), `to_date` (`YYYY-MM-DD`, 선택), `meal_type` (`Meal_type`, 선택), `page` (기본 `1`), `size` (기본 `10`)

* **Request Body**: -

* **Response Body (`200 OK`)**:

  ```json
  {
    "items": [
      {
        "diet_analysis_id": 33,
        "meal_type": "LUNCH",
        "image_url": "https://storage.welloop.example.com/diets/33.jpg",
        "detected_food_names": ["고등어구이", "현미밥", "된장찌개", "나물무침"],
        "ldl_grade": "GOOD",
        "eaten_at": "2026-11-26T12:30:00+09:00"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 10
  }
  ```

* **Status Code**: `200 OK` / `401 Unauthorized`

* **관련 테이블 · 요구사항**: `diet_analyses` · `REQ-FOOD-001`, `SR-003`

### 📋 05 구역 미확정 사항(TBD) 및 팀 확인 포인트

| \# | 항목 | 관련 TBD / REQ | 확인 대상 및 내용 | 
| ----- | ----- | ----- | ----- | 
| 1 | 외부 LLM 제공사·RAG 문서 범위·CV 모델 선정 | `TBD-029`, `REQ-LLM-001~002`, `REQ-FOOD-001` | OpenAI / Claude / 오픈소스 여부, RAG 인덱싱 대상 진료지침 범위, 식단 분석을 멀티모달 VLM으로 처리할지 별도 CV 모델로 분리할지 확정 필요 (전체 팀·AI) | 
| 2 | LLM 안전장치 및 응급 의심 규칙 주관 담당자 | `TBD-031`, `SR-032~033` | 입·출력 금칙어(`HORMONE_BAN`, `MEDICAL_BAN`, `EMERGENCY`) 상세 패턴 및 Hallucination 검증 로직 담당자 지정 필요 (전체 팀) | 
| 3 | 상담용 리포트 화면 구성 및 PDF 구현 범위 | `TBD-024`, `TBD-026`, `REQ-RPT-001~003` | P1 웹 화면 리포트 우선 구현 후 P2 PDF 다운로드(`51번`)를 이번 MVP에 포함할지 여부 확정 필요 (와이어프레임·전체 팀) | 

<!-- 05 END -->