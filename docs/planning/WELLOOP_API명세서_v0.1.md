# WELLOOP API 명세서 v0.1

> 기준 문서: 요구사항 정의서 v1.3 · ERD v1.3 · 와이어프레임(명석님 Figma, 37화면)
> 원본: 명석님 초안 시트(`WELLOOP_API명세서_v0.1.xlsx`, API 38개) → md 변환. 각자 맡은 구역을 검토·보완합니다. 개발 중 바뀌면 즉시 반영합니다(OT 가이드).

---

## ⚠️ 작성 규칙 (충돌 방지)

1. **자기 구역(`<!-- 0X START -->` ~ `<!-- 0X END -->`) 안만 수정합니다.** 다른 구역·공통 규칙은 건드리지 않습니다.
2. 구역 사이 빈 줄과 구분선(`---`)은 지우지 않습니다. (붙어 있는 줄을 서로 고치면 Git 충돌이 납니다)
3. 작업 전 `git pull origin dev`로 최신을 받고, 브랜치는 `docs/api-0X-이름`으로 만듭니다.
4. 다른 구역에 필요한 API가 보이면 직접 쓰지 말고, 그 담당에게 말하거나 자기 구역에 "→ 0X 참고"라고만 적습니다.
5. PR 제목: `docs: API 명세서 0X 구역 작성`

---

## 공통 규칙

| 항목 | 규칙 |
|---|---|
| Base URL | `/api/v1` |
| 형식 | 요청·응답 모두 JSON (`Content-Type: application/json`) |
| 네이밍 | 필드는 **snake_case**, ERD 컬럼명과 동일 |
| 인증 | `Authorization: Bearer {access_token}` (JWT). 관리자 API는 관리자 권한 필요 |
| 날짜 | ISO 8601 (`2026-11-18T09:00:00+09:00`) |
| 수치·문구 | 예시값. 의료 진단·처방처럼 보이는 문구 금지 (NFR-014) |

### 공통 에러 응답

```json
{ "detail": "필수값 누락: email", "code": "VALIDATION_ERROR" }
```

| 코드 | 의미 | 예시 |
|---|---|---|
| 400 | 요청 값 오류 | 필수값 누락, 형식 오류 |
| 401 | 인증 실패 | 토큰 없음·만료 |
| 403 | 권한 없음 | 일반 사용자가 관리자 API 호출, 그룹 미동의 |
| 404 | 대상 없음 | 존재하지 않는 id |
| 409 | 중복·충돌 | 이메일 중복 |
| 423 | 잠김 | 비밀번호 5회 오류 후 10분 잠금 (REQ-002) |
| 500 | 서버 오류 | 예측 모델·LLM 호출 실패 |

### API 작성 양식 (각 API마다 복사해서 사용)

```
### [기능명]
- Method / Endpoint:
- Description:
- 인증: 필요 / 불필요 / 관리자
- Request Header:
- Request Parameter (Path / Query):
- Request Body:
  (JSON 예시)
- Response Body (성공):
  (JSON 예시)
- Status Code: 200(또는 201) 성공 / 에러 코드와 이유
- 관련 요구사항: REQ-0XX
- 관련 화면: X0X
```

---


## 전체 목록

| 구역 | No | Method | Endpoint | 설명 | 우선순위 |
|---|---|---|---|---|---|
| 01 | 1 | POST | `/api/v1/auth/signup` | 회원가입 | MVP |
| 01 | 2 | POST | `/api/v1/auth/login` | 로그인 (JWT 발급) | MVP |
| 01 | 3 | GET | `/api/v1/users/me` | 내 정보 조회 | MVP |
| 01 | 4 | PATCH | `/api/v1/users/me` | 내 정보·설정 수정 (이름, 알림, 큰 글씨 모드) | MVP |
| 01 | 5 | DELETE | `/api/v1/users/me` | 회원 탈퇴 | MVP |
| 01 | 6 | POST | `/api/v1/consents` | 민감정보·AI 처리·해외 전송 동의 저장 | MVP |
| 01 | 22 | POST | `/api/v1/groups` | 가족·지인 그룹 생성 | 추가 |
| 01 | 23 | POST | `/api/v1/groups/{group_id}/invite` | 그룹 초대 (상호 동의 시작) | 추가 |
| 01 | 24 | POST | `/api/v1/groups/{group_id}/invite/accept` | 초대 수락 (제안: 스켈레톤에 없음) | 추가 |
| 01 | 25 | PUT | `/api/v1/groups/{group_id}/share-settings` | 공유 범위 설정 | 추가 |
| 01 | 26 | POST | `/api/v1/groups/{group_id}/messages/suggest` | 보낼 문구 추천 (LLM 제안 → 사용자 선택) | 추가 |
| 02 | 7 | POST | `/api/v1/questionnaires` | 문진 응답 저장 | MVP |
| 02 | 8 | POST | `/api/v1/checkups` | 검진 수치 입력 (선택) | MVP |
| 03 | 9 | POST | `/api/v1/predictions` | 위험 예측(미진단) / 관리 평가(기진단) 실행 | MVP |
| 03 | 10 | GET | `/api/v1/predictions` | 예측 이력 조회 | MVP |
| 03 | 11 | POST | `/api/v1/predictions/simulate` | “만약에” 시뮬레이션 (저장하지 않음) | 추가 |
| 03 | 17 | POST | `/api/v1/health-logs` | 건강 수치 기록 | MVP |
| 03 | 18 | GET | `/api/v1/health-logs` | 건강 수치 기록·추이 조회 | MVP |
| 03 | 19 | GET | `/api/v1/dashboard` | 기록 추이·위험도 변화 요약 | MVP |
| 04 | 12 | GET | `/api/v1/users/me/categories` | 켜진 생활습관 카테고리 조회 | MVP |
| 04 | 13 | PUT | `/api/v1/users/me/categories` | 카테고리 켜기/끄기 저장 | MVP |
| 04 | 14 | GET | `/api/v1/challenges/today` | 오늘의 미션 조회 | MVP |
| 04 | 15 | POST | `/api/v1/checkins` | 미션·수면·기분·복약 체크인 | MVP |
| 05 | 16 | POST | `/api/v1/sos` | 흡연 욕구 SOS 기록 | 추가 |
| 05 | 20 | GET | `/api/v1/coach/today` | 오늘의 코치 메시지 (하루 1회 생성, 저장본 재사용) | MVP |
| 05 | 21 | POST | `/api/v1/coach/chat` | AI 코치 실시간 대화 (SSE 스트리밍) | 추가 |
| 06 | 27 | POST | `/api/v1/admin/login` | 관리자 로그인 | MVP |
| 06 | 28 | GET | `/api/v1/admin/challenges` | 챌린지·콘텐츠 목록 조회 | MVP |
| 06 | 29 | POST | `/api/v1/admin/challenges` | 챌린지 등록 | MVP |
| 06 | 30 | PUT | `/api/v1/admin/challenges/{challenge_id}` | 챌린지 수정 | MVP |
| 06 | 31 | DELETE | `/api/v1/admin/challenges/{challenge_id}` | 챌린지 삭제 | MVP |
| 06 | 32 | GET | `/api/v1/admin/safety-keywords` | 위험 키워드 목록 조회 | MVP |
| 06 | 33 | POST | `/api/v1/admin/safety-keywords` | 위험 키워드 등록 | MVP |
| 06 | 34 | PUT | `/api/v1/admin/safety-keywords/{keyword_id}` | 위험 키워드 수정 | MVP |
| 06 | 35 | DELETE | `/api/v1/admin/safety-keywords/{keyword_id}` | 위험 키워드 삭제 | MVP |
| 06 | 36 | GET | `/api/v1/admin/thresholds` | 위험도 경계값 조회 | MVP |
| 06 | 37 | PUT | `/api/v1/admin/thresholds/{threshold_id}` | 위험도 경계값 수정 | MVP |
| 06 | 38 | GET | `/api/v1/admin/stats` | 운영 현황 조회 (개인 원문 제외) | MVP |

---

<!-- 01 START · 시작·계정 · 담당: 엄태은 -->
## 01. 시작·계정 (인증·회원·동의·함께 관리)

담당: 엄태은 · 관련 화면: A01~A08 · 기준: ERD v1.3 (`users`, `consents`, `family_groups`, `group_members`, `share_settings`, `family_messages`)

> 01 구역 공통: Enum 값은 ERD와 같은 **대문자**로 주고받습니다.
> `gender`: MALE / FEMALE · `font_size`: NORMAL / BIG · `consent_type`: HEALTH_DATA / FAMILY_SHARE / NOTIFICATION · `relation`: SPOUSE / PARENT_CHILD / FAMILY · `status`: INVITED / ACCEPTED / LEFT · `tone`: WARM / PLAIN / LIGHT

### 1. 회원가입 · MVP
- Method / Endpoint: `POST /api/v1/auth/signup`
- Description: 이메일로 가입한다. 성별·생년월일은 예측 모델과 갱년기 개인화에 필요해 가입 때 받는다.
- 인증: 불필요
- Request Header: `Content-Type: application/json`
- Request Parameter: -
- Request Body:

  ```json
  {
    "email": "user@example.com",
    "password": "Welloop!2345",
    "name": "홍길동",
    "birth_date": "1975-03-02",
    "gender": "MALE",
    "terms_agreed": true,
    "privacy_agreed": true
  }
  ```
- Response Body (201):

  ```json
  {
    "user_id": 1,
    "email": "user@example.com",
    "name": "홍길동",
    "font_size": "NORMAL",
    "created_at": "2026-11-18T10:00:00+09:00"
  }
  ```
- Status Code: 201 Created / 400 필수값 누락·형식 오류(VALIDATION_ERROR: 비밀번호 영문·숫자·특수문자 8자 이상, 필수 약관 미동의) / 409 이메일 중복(EMAIL_DUPLICATED)
- 관련 테이블 · REQ: users · REQ-001
- 비고: `password`는 bcrypt 해시로 저장. `font_size`는 만 65세 이상이면 BIG 자동 적용(ERD 주석). 가입 연령 제한(성인만 / 45세 이상만) 확정 필요. `terms_agreed`·`privacy_agreed`는 필수 약관(A02) — 저장 위치(consents 확장 vs 별도) 백엔드와 확정

### 2. 로그인 (JWT 발급) · MVP
- Method / Endpoint: `POST /api/v1/auth/login`
- Description: 이메일·비밀번호를 확인하고 토큰을 발급한다. 연속 5회 실패하면 10분 잠금.
- 인증: 불필요
- Request Header: `Content-Type: application/json`
- Request Parameter: -
- Request Body:

  ```json
  {
    "email": "user@example.com",
    "password": "Welloop!2345",
    "keep_login": true
  }
  ```
- Response Body (200):

  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": { "user_id": 1, "name": "홍길동", "role": "USER", "font_size": "NORMAL" }
  }
  ```
- Status Code: 200 OK / 400 필수값 누락 / 401 이메일·비밀번호 불일치(UNAUTHORIZED, 남은 시도 횟수 포함) / 423 5회 실패로 10분 잠금(ACCOUNT_LOCKED, `locked_until` 포함)
- 관련 테이블 · REQ: users(`failed_login_count`, `locked_until`) · REQ-002
- 비고: 성공 시 `failed_login_count` 0으로 초기화. 탈퇴 회원(`is_deleted=true`)은 401

### 2-1. 토큰 재발급 · MVP (추가 제안)
- Method / Endpoint: `POST /api/v1/auth/refresh`
- Description: access 토큰이 만료되면 refresh 토큰으로 새로 받는다 (A03 "로그인 상태 유지").
- 인증: 불필요 (refresh 토큰으로 확인)
- Request Header: `Content-Type: application/json`
- Request Body:

  ```json
  { "refresh_token": "eyJhbGciOi..." }
  ```
- Response Body (200):

  ```json
  { "access_token": "eyJhbGciOi...", "token_type": "bearer", "expires_in": 3600 }
  ```
- Status Code: 200 OK / 401 refresh 토큰 없음·만료(UNAUTHORIZED)
- 관련 테이블 · REQ: - · REQ-002
- 비고: refresh 토큰을 DB에 저장할지(로그아웃 시 폐기) 백엔드와 확정. 로그아웃은 프론트 토큰 삭제로 처리하거나 `POST /auth/logout` 추가

### 3. 내 정보 조회 · MVP
- Method / Endpoint: `GET /api/v1/users/me`
- Description: 내 프로필·화면 설정을 조회한다 (A05 내 정보).
- 인증: 필요
- Request Header: `Authorization: Bearer {access_token}`
- Request Parameter: -
- Request Body: -
- Response Body (200):

  ```json
  {
    "user_id": 1,
    "email": "user@example.com",
    "name": "홍길동",
    "birth_date": "1975-03-02",
    "gender": "MALE",
    "role": "USER",
    "font_size": "NORMAL",
    "created_at": "2026-11-18T10:00:00+09:00"
  }
  ```
- Status Code: 200 OK / 401 토큰 없음·만료
- 관련 테이블 · REQ: users · REQ-003

### 4. 내 정보·화면 설정 수정 · MVP
- Method / Endpoint: `PATCH /api/v1/users/me`
- Description: 이름·글자 크기를 바꾼다. 바꿀 필드만 보낸다.
- 인증: 필요
- Request Header: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- Request Body:

  ```json
  { "name": "홍길순", "font_size": "BIG" }
  ```
- Response Body (200):

  ```json
  { "user_id": 1, "name": "홍길순", "font_size": "BIG", "updated_at": "2026-11-18T10:30:00+09:00" }
  ```
- Status Code: 200 OK / 400 수정할 값 없음·허용되지 않은 값(VALIDATION_ERROR) / 401 토큰 없음·만료
- 관련 테이블 · REQ: users · REQ-003·025
- 비고: 이메일·생년월일·성별은 수정 불가(예측 기준값). **알림 켜기/끄기는 users에 컬럼이 없어 `consents`의 NOTIFICATION으로 처리** (6번)

### 5. 회원 탈퇴 · MVP
- Method / Endpoint: `DELETE /api/v1/users/me`
- Description: 탈퇴한다. 계정은 `is_deleted=true`로 막고, 건강 데이터는 실제 삭제한다.
- 인증: 필요
- Request Header: `Authorization: Bearer {access_token}`
- Request Body:

  ```json
  { "password": "Welloop!2345" }
  ```
- Response Body: (본문 없음)
- Status Code: 204 No Content / 400 비밀번호 누락 / 401 토큰 없음·만료·비밀번호 불일치
- 관련 테이블 · REQ: users + 건강 데이터 테이블 전체 · REQ-003, NFR-005
- 비고: 실수 방지를 위해 비밀번호 재확인. 함께 관리 그룹은 자동 LEFT 처리

### 6. 동의 저장 (민감정보·함께 관리·알림) · MVP
- Method / Endpoint: `POST /api/v1/consents`
- Description: 동의 또는 철회를 기록한다. 철회도 `agreed=false`로 새 기록을 남긴다(이력 보존).
- 인증: 필요
- Request Header: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- Request Body:

  ```json
  { "consent_type": "HEALTH_DATA", "version": "v1.0", "agreed": true }
  ```
- Response Body (201):

  ```json
  { "id": 10, "consent_type": "HEALTH_DATA", "version": "v1.0", "agreed": true, "agreed_at": "2026-11-18T10:05:00+09:00" }
  ```
- Status Code: 201 Created / 400 consent_type·version 값 오류 / 401 토큰 없음·만료
- 관련 테이블 · REQ: consents · NFR-005, REQ-023(알림)
- 비고: A04 "동의하지 않고 계속" → HEALTH_DATA `agreed=false` 저장, 문진·예측·코치 API는 409(CONSENT_REQUIRED). **v1.4 후보: Consent_type에 `AI_PROCESSING`(AI 처리)·`OVERSEAS_TRANSFER`(해외 API 전송) 추가 필요 → ERD 수정 요청**

### 6-1. 내 동의 내역 조회 · MVP (추가 제안)
- Method / Endpoint: `GET /api/v1/consents`
- Description: 동의 종류별 **최신** 상태를 조회한다 (설정 화면의 동의 관리·철회, 기능 잠금 판단).
- 인증: 필요
- Request Header: `Authorization: Bearer {access_token}`
- Response Body (200):

  ```json
  {
    "items": [
      { "consent_type": "HEALTH_DATA", "version": "v1.0", "agreed": true, "agreed_at": "2026-11-18T10:05:00+09:00" },
      { "consent_type": "NOTIFICATION", "version": "v1.0", "agreed": false, "agreed_at": "2026-11-18T10:06:00+09:00" }
    ]
  }
  ```
- Status Code: 200 OK / 401 토큰 없음·만료
- 관련 테이블 · REQ: consents · NFR-005

### 22. 함께 관리 그룹 만들기 · 추가
- Method / Endpoint: `POST /api/v1/groups`
- Description: 그룹을 만들고 만든 사람을 ACCEPTED 구성원으로 넣는다. FAMILY_SHARE 동의가 필요하다.
- 인증: 필요
- Request Header: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- Request Body:

  ```json
  { "name": "우리 부부", "relation": "SPOUSE" }
  ```
- Response Body (201):

  ```json
  { "group_id": 2, "name": "우리 부부", "relation": "SPOUSE", "created_by": 1, "created_at": "2026-11-18T11:00:00+09:00" }
  ```
- Status Code: 201 Created / 400 name·relation 누락 / 401 토큰 없음·만료 / 409 FAMILY_SHARE 동의 없음(CONSENT_REQUIRED)
- 관련 테이블 · REQ: family_groups, group_members · REQ-017
- 비고: 초안의 `role: owner`는 ERD에 없어 `created_by`로 대체

### 23. 그룹 초대 · 추가
- Method / Endpoint: `POST /api/v1/groups/{group_id}/invite`
- Description: 가입한 회원을 이메일로 초대한다. 상대가 수락해야 연결된다(상호 동의).
- 인증: 필요
- Request Header: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- Request Parameter: Path `group_id`
- Request Body:

  ```json
  { "invitee_email": "family@example.com" }
  ```
- Response Body (201):

  ```json
  { "group_id": 2, "user_id": 3, "status": "INVITED" }
  ```
- Status Code: 201 Created / 400 이메일 형식 오류 / 401 토큰 없음·만료 / 403 그룹을 만든 사람이 아님(FORBIDDEN) / 404 그룹 없음·가입하지 않은 이메일 / 409 이미 초대됨·연결됨
- 관련 테이블 · REQ: group_members(`status`) · REQ-017
- 비고: 초안의 `invite_id`·`expires_at`은 ERD에 없음 → group_members(group_id, user_id) 행으로 관리. 초대 만료가 필요하면 ERD에 컬럼 추가 요청. 성인만 초대(생년월일로 확인)

### 24. 초대 수락·거절 · 추가
- Method / Endpoint: `POST /api/v1/groups/{group_id}/invite/accept`
- Description: 초대받은 본인이 수락하면 ACCEPTED, 거절하면 LEFT로 바꾼다.
- 인증: 필요
- Request Header: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- Request Parameter: Path `group_id`
- Request Body:

  ```json
  { "accept": true }
  ```
- Response Body (200):

  ```json
  { "group_id": 2, "user_id": 3, "status": "ACCEPTED", "joined_at": "2026-11-18T12:00:00+09:00" }
  ```
- Status Code: 200 OK / 401 토큰 없음·만료 / 404 받은 초대 없음 / 409 이미 처리된 초대 · FAMILY_SHARE 동의 없음
- 관련 테이블 · REQ: group_members · REQ-017
- 비고: 내가 받은 초대 목록이 필요하면 `GET /api/v1/groups/invites` 추가 (A07 화면 확인 후)

### 25. 공유 범위 설정 · 추가
- Method / Endpoint: `PUT /api/v1/groups/{group_id}/share-settings`
- Description: 내 정보 중 그룹에 보여 줄 항목을 정한다. 기본은 오늘의 상태 칩만 공유.
- 인증: 필요
- Request Header: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- Request Parameter: Path `group_id`
- Request Body:

  ```json
  { "share_condition": true, "share_challenge": true, "share_trend": false }
  ```
- Response Body (200):

  ```json
  { "group_id": 2, "user_id": 1, "share_condition": true, "share_challenge": true, "share_trend": false, "updated_at": "2026-11-18T12:10:00+09:00" }
  ```
- Status Code: 200 OK / 400 값 형식 오류 / 401 토큰 없음·만료 / 403 그룹 구성원(ACCEPTED)이 아님 / 404 그룹 없음
- 관련 테이블 · REQ: share_settings · NFR-017
- 비고: ⚠️ 초안의 `share_risk_level`·`share_health_logs`·`share_mood`는 **NFR-017 위반(위험 신호·수치·메모는 공유 항목 자체가 없음)** 이라 ERD 3개 항목으로 교체

### 25-1. 그룹 요약 보기 · 추가 (추가 제안)
- Method / Endpoint: `GET /api/v1/groups/{group_id}/summary`
- Description: 구성원들이 **허용한 항목만** 요약 칩으로 보여 준다 (A08).
- 인증: 필요
- Request Header: `Authorization: Bearer {access_token}`
- Request Parameter: Path `group_id`
- Response Body (200):

  ```json
  {
    "group_id": 2,
    "members": [
      {
        "user_id": 3,
        "name": "김영희",
        "condition_chip": "컨디션 좋음",
        "challenge_chip": "오늘 미션 2/3",
        "trend_chip": null,
        "help_line": "오늘 같이 걸어 주면 좋아요"
      }
    ]
  }
  ```
- Status Code: 200 OK / 401 토큰 없음·만료 / 403 그룹 구성원이 아님 / 404 그룹 없음
- 관련 테이블 · REQ: share_settings, group_members · REQ-017, NFR-017
- 비고: 허용 안 한 항목은 `null`. 수치·메모·대화·위험 신호는 응답에 절대 포함하지 않음

### 26. 보낼 문구 추천 · 추가
- Method / Endpoint: `POST /api/v1/groups/{group_id}/messages/suggest`
- Description: LLM이 말투에 맞춘 문구 후보를 만든다. 자동 발송하지 않고 사용자가 고른다.
- 인증: 필요
- Request Header: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- Request Parameter: Path `group_id`
- Request Body:

  ```json
  { "target_user_id": 3, "tone": "WARM" }
  ```
- Response Body (200):

  ```json
  { "suggestions": ["오늘 산책 같이 나갈까요?", "요즘 잠은 잘 자요? 같이 일찍 자 봐요"] }
  ```
- Status Code: 200 OK / 400 tone 값 오류 / 401 토큰 없음·만료 / 403 그룹 구성원이 아님 / 409 동의 없음(CONSENT_REQUIRED) / 503 LLM 호출 실패(AI_UNAVAILABLE)
- 관련 테이블 · REQ: (저장 안 함) · REQ-036
- 비고: LLM에는 상대가 **허용한 요약 칩만** 전달. 후보는 금지어 검사 후 반환. 초안의 `situation`은 요약 칩으로 대체

### 26-1. 고른 문구 보내기 · 추가 (추가 제안)
- Method / Endpoint: `POST /api/v1/groups/{group_id}/messages`
- Description: 사용자가 고른(또는 고쳐 쓴) 문구를 그룹에 남긴다.
- 인증: 필요
- Request Header: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- Request Parameter: Path `group_id`
- Request Body:

  ```json
  { "tone": "WARM", "content": "오늘 산책 같이 나갈까요?" }
  ```
- Response Body (201):

  ```json
  { "id": 21, "group_id": 2, "sender_id": 1, "tone": "WARM", "content": "오늘 산책 같이 나갈까요?", "created_at": "2026-11-18T12:30:00+09:00" }
  ```
- Status Code: 201 Created / 400 content 비어 있음·금지어 포함 / 401 토큰 없음·만료 / 403 그룹 구성원이 아님
- 관련 테이블 · REQ: family_messages · REQ-036

#### 01 구역 ERD 대조 결과 · 팀 확인 요청
| # | 내용 | 확인할 사람 |
|---|---|---|
| 1 | `notification_enabled`·`large_font_mode`는 users에 없음 → 알림은 consents(NOTIFICATION), 글자 크기는 `font_size`(NORMAL/BIG)로 맞춤 | 백엔드 |
| 2 | Consent_type에 AI_PROCESSING·OVERSEAS_TRANSFER 추가 (v1.4 후보, NFR-005) | 팀장 · 백엔드 |
| 3 | 필수 약관(서비스 이용약관·개인정보 수집) 동의 저장 위치 | 백엔드 |
| 4 | 가입 연령 제한(성인 / 45세 이상) | 기획 |
| 5 | refresh 토큰 저장·로그아웃 방식 | 백엔드 |
| 6 | 초대 만료가 필요하면 group_members에 `invited_at`·`expires_at` 추가 | 백엔드 |
| 7 | share_settings는 ERD 3항목만 사용 (초안의 위험도·수치·기분 공유는 NFR-017 위반이라 제외) | 함께 관리 기획 |

<!-- 01 END -->

---

<!-- 02 START · 문진 · 담당: ______ -->
## 02. 문진 (문진·검진 수치)

담당: ______ · 관련 화면: B01~B05

### 7. 문진 응답 저장
- Method / Endpoint: `POST /api/v1/questionnaires`
- 인증: 필요
- Request Header: Content-Type: application/json / Authorization: Bearer {access_token}
- Request Parameter (Path / Query): -
- Request Body:

  ```json
  {
    "height_cm": 170.5,
    "weight_kg": 72.0,
    "diagnosed_diseases": [
      "hypertension"
    ],
    "smoking_status": "former",
    "drinking_per_week": 2,
    "exercise_days_per_week": 3,
    "sleep_hours": 6.5,
    "family_history": [
      "diabetes"
    ]
  }
  ```
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "questionnaire_id": 5,
    "bmi": 24.8,
    "created_at": "2026-11-18T10:10:00+09:00"
  }
  ```
- Status Code: 성공: 201 Created / 400 필수값 누락·범위 오류 / 401 토큰 없음·만료
- 관련 테이블 · REQ: questionnaires · REQ-004
- 우선순위: MVP
- 비고: 문진 4단계는 1회 제출 또는 단계별 저장 중 선택 필요. 필드는 문진표 확정 후 수정

### 8. 검진 수치 입력 (선택)
- Method / Endpoint: `POST /api/v1/checkups`
- 인증: 필요
- Request Header: Content-Type: application/json / Authorization: Bearer {access_token}
- Request Parameter (Path / Query): -
- Request Body:

  ```json
  {
    "checkup_date": "2026-10-05",
    "systolic_bp": 132,
    "diastolic_bp": 84,
    "fasting_glucose": 104,
    "hba1c": 5.8,
    "total_cholesterol": 210,
    "ldl": 130,
    "hdl": 48,
    "triglycerides": 160
  }
  ```
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "checkup_id": 3,
    "created_at": "2026-11-18T10:12:00+09:00"
  }
  ```
- Status Code: 성공: 201 Created / 400 수치 범위 오류 / 401 토큰 없음·만료
- 관련 테이블 · REQ: checkup_records · REQ-005
- 우선순위: MVP
- 비고: 모든 수치 선택 입력(건너뛰기 가능)

#### ➕ 추가 검토 (뼈대·화면에는 있는데 초안에 없는 API)
- [ ] GET /api/v1/questionnaires/latest — 최근 문진 조회 (재문진·수정 화면용)

<!-- 02 END -->

---

<!-- 03 START · 평가·대시보드 · 담당: ______ -->
## 03. 평가·대시보드 (예측·기록)

담당: ______ · 관련 화면: C01~C07

### 9. 위험 예측(미진단) / 관리 평가(기진단) 실행
- Method / Endpoint: `POST /api/v1/predictions`
- 인증: 필요
- Request Header: Content-Type: application/json / Authorization: Bearer {access_token}
- Request Parameter (Path / Query): -
- Request Body:

  ```json
  {
    "questionnaire_id": 5,
    "checkup_id": 3,
    "mode": "risk_prediction"
  }
  ```
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "prediction_id": 7,
    "mode": "risk_prediction",
    "results": [
      {
        "disease": "hypertension",
        "risk_level": "medium",
        "risk_score": 0.42,
        "top_factors": [
          "체중",
          "수면 부족"
        ]
      }
    ],
    "disclaimer": "진단이 아닌 참고용 정보입니다.",
    "created_at": "2026-11-18T10:15:00+09:00"
  }
  ```
- Status Code: 성공: 201 Created / 400 questionnaire_id 누락 / 401 토큰 없음·만료 / 404 문진 기록 없음 / 409 AI 처리 동의 없음 / 503 예측 모델 오류
- 관련 테이블 · REQ: risk_predictions · REQ-006·035
- 우선순위: MVP
- 비고: mode: risk_prediction(미진단) / management_evaluation(기진단). 수치는 코드로 계산, LLM은 설명 문구만

### 10. 예측 이력 조회
- Method / Endpoint: `GET /api/v1/predictions`
- 인증: 필요
- Request Header: Content-Type: application/json / Authorization: Bearer {access_token}
- Request Parameter (Path / Query): page(기본 1), size(기본 10), from_date, to_date
- Request Body: -
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "items": [
      {
        "prediction_id": 7,
        "mode": "risk_prediction",
        "highest_risk_level": "medium",
        "created_at": "2026-11-18T10:15:00+09:00"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 10
  }
  ```
- Status Code: 성공: 200 OK / 400 날짜 형식 오류 / 401 토큰 없음·만료
- 관련 테이블 · REQ: risk_predictions · REQ-007
- 우선순위: MVP

### 11. “만약에” 시뮬레이션 (저장하지 않음)
- Method / Endpoint: `POST /api/v1/predictions/simulate`
- 인증: 필요
- Request Header: Content-Type: application/json / Authorization: Bearer {access_token}
- Request Parameter (Path / Query): -
- Request Body:

  ```json
  {
    "base_prediction_id": 7,
    "changes": {
      "smoking_status": "never",
      "exercise_days_per_week": 5
    }
  }
  ```
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "original": {
      "disease": "hypertension",
      "risk_level": "medium",
      "risk_score": 0.42
    },
    "simulated": {
      "disease": "hypertension",
      "risk_level": "low",
      "risk_score": 0.31
    },
    "diff": -0.11
  }
  ```
- Status Code: 성공: 200 OK / 400 changes 값 오류 / 401 토큰 없음·만료 / 404 기준 예측 없음
- 관련 테이블 · REQ: REQ-008
- 우선순위: 추가
- 비고: DB에 저장하지 않음

### 17. 건강 수치 기록
- Method / Endpoint: `POST /api/v1/health-logs`
- 인증: 필요
- Request Header: Content-Type: application/json / Authorization: Bearer {access_token}
- Request Parameter (Path / Query): -
- Request Body:

  ```json
  {
    "log_type": "blood_pressure",
    "systolic_bp": 128,
    "diastolic_bp": 82,
    "measured_at": "2026-11-18T08:00:00+09:00"
  }
  ```
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "health_log_id": 31,
    "log_type": "blood_pressure",
    "created_at": "2026-11-18T08:01:00+09:00"
  }
  ```
- Status Code: 성공: 201 Created / 400 log_type·수치 오류 / 401 토큰 없음·만료
- 관련 테이블 · REQ: health_logs · REQ-018·029
- 우선순위: MVP
- 비고: log_type: blood_pressure / blood_glucose / weight 등 (확정 필요)

### 18. 건강 수치 기록·추이 조회
- Method / Endpoint: `GET /api/v1/health-logs`
- 인증: 필요
- Request Header: Content-Type: application/json / Authorization: Bearer {access_token}
- Request Parameter (Path / Query): log_type, from_date, to_date, page, size
- Request Body: -
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "items": [
      {
        "health_log_id": 31,
        "log_type": "blood_pressure",
        "systolic_bp": 128,
        "diastolic_bp": 82,
        "measured_at": "2026-11-18T08:00:00+09:00"
      }
    ],
    "total": 1
  }
  ```
- Status Code: 성공: 200 OK / 400 날짜 형식 오류 / 401 토큰 없음·만료
- 관련 테이블 · REQ: health_logs · REQ-018·029
- 우선순위: MVP

### 19. 기록 추이·위험도 변화 요약
- Method / Endpoint: `GET /api/v1/dashboard`
- 인증: 필요
- Request Header: Content-Type: application/json / Authorization: Bearer {access_token}
- Request Parameter (Path / Query): period(7d | 30d | 90d, 기본 30d)
- Request Body: -
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "period": "30d",
    "challenge_completion_rate": 0.72,
    "health_trends": [
      {
        "log_type": "blood_pressure",
        "points": [
          {
            "date": "2026-11-10",
            "systolic_bp": 130
          }
        ]
      }
    ],
    "risk_change": {
      "disease": "hypertension",
      "from": "medium",
      "to": "low"
    }
  }
  ```
- Status Code: 성공: 200 OK / 400 period 값 오류 / 401 토큰 없음·만료
- 관련 테이블 · REQ: REQ-018·019
- 우선순위: MVP
- 비고: 프론트 차트에 필요한 값만 집계해서 반환

<!-- 03 END -->

---

<!-- 04 START · 홈·챌린지 · 담당: ______ -->
## 04. 홈·챌린지 (카테고리·미션·체크인·복약)

담당: ______ · 관련 화면: D01~D07

### 12. 켜진 생활습관 카테고리 조회
- Method / Endpoint: `GET /api/v1/users/me/categories`
- 인증: 필요
- Request Header: Content-Type: application/json / Authorization: Bearer {access_token}
- Request Parameter (Path / Query): -
- Request Body: -
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "categories": [
      {
        "category_code": "exercise",
        "enabled": true
      },
      {
        "category_code": "diet",
        "enabled": true
      },
      {
        "category_code": "sleep",
        "enabled": false
      },
      {
        "category_code": "smoking",
        "enabled": false
      }
    ]
  }
  ```
- Status Code: 성공: 200 OK / 401 토큰 없음·만료
- 관련 테이블 · REQ: user_categories · REQ-010
- 우선순위: MVP
- 비고: category_code 4개 값은 기획 확정값으로 교체 (예시임)

### 13. 카테고리 켜기/끄기 저장
- Method / Endpoint: `PUT /api/v1/users/me/categories`
- 인증: 필요
- Request Header: Content-Type: application/json / Authorization: Bearer {access_token}
- Request Parameter (Path / Query): -
- Request Body:

  ```json
  {
    "categories": [
      {
        "category_code": "exercise",
        "enabled": true
      },
      {
        "category_code": "sleep",
        "enabled": true
      }
    ]
  }
  ```
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "updated": 2
  }
  ```
- Status Code: 성공: 200 OK / 400 알 수 없는 category_code / 401 토큰 없음·만료
- 관련 테이블 · REQ: user_categories · REQ-010
- 우선순위: MVP

### 14. 오늘의 미션 조회
- Method / Endpoint: `GET /api/v1/challenges/today`
- 인증: 필요
- Request Header: Content-Type: application/json / Authorization: Bearer {access_token}
- Request Parameter (Path / Query): date(선택, 기본 오늘)
- Request Body: -
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "date": "2026-11-18",
    "missions": [
      {
        "daily_challenge_id": 21,
        "challenge_id": 4,
        "category_code": "exercise",
        "title": "30분 걷기",
        "completed": false
      }
    ]
  }
  ```
- Status Code: 성공: 200 OK / 401 토큰 없음·만료
- 관련 테이블 · REQ: daily_challenges · REQ-009·011
- 우선순위: MVP

### 15. 미션·수면·기분·복약 체크인
- Method / Endpoint: `POST /api/v1/checkins`
- 인증: 필요
- Request Header: Content-Type: application/json / Authorization: Bearer {access_token}
- Request Parameter (Path / Query): -
- Request Body:

  ```json
  {
    "checkin_date": "2026-11-18",
    "completed_daily_challenge_ids": [
      21
    ],
    "sleep_hours": 6.5,
    "mood_score": 4,
    "medication_taken": true
  }
  ```
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "checkin_id": 15,
    "completion_rate": 1.0,
    "created_at": "2026-11-18T21:00:00+09:00"
  }
  ```
- Status Code: 성공: 201 Created / 400 mood_score 범위(1~5) 오류 / 401 토큰 없음·만료 / 409 같은 날 체크인 중복
- 관련 테이블 · REQ: checkins · REQ-012·013·024
- 우선순위: MVP
- 비고: 같은 날 재제출은 409 대신 PUT 덮어쓰기로 할지 팀 결정 필요

#### ➕ 추가 검토 (뼈대·화면에는 있는데 초안에 없는 API)
- [ ] GET /api/v1/challenges/recommended — 맞춤 챌린지 추천 (D02, REQ-009)
- [ ] GET /api/v1/weather/mission — 날씨 맞춤 미션 조정 (D06, REQ-024 · 추가)

<!-- 04 END -->

---

<!-- 05 START · AI 코치·케어 · 담당: 전은지 -->
## 05. AI 코치·케어 (코치·SOS·갱년기·감정 메모)

담당: 전은지 · 관련 화면: E01~E06, D01(오늘의 코치 카드) · 관련 요구사항: REQ-014~016·021·022·034

> 05 구역 공통
> - **`safety_alert` 공통 객체**: `{ "alert_id": 55, "alert_type": "medical_consult", "reason_code": "bp_over_threshold", "created_at": "2026-11-18T09:15:00+09:00" }` · `alert_type`: emergency(119) / medical_consult(진료 권고) / mental_crisis(109). 응답에 이 값이 있으면 프론트는 E02(21-2)를 띄운다. 다른 구역 API(문진·검진·예측·체크인·건강 기록)에도 같은 형식으로 넣어야 해서 → 02·03·04 참고
> - **SSE 이벤트(21번)**: `meta`(대화 시작) → `token`(답변 조각) → `done`(종료·추천 행동) / `safety_alert`(위험 표현, LLM 미호출) / `error`(스트림 중 오류)
> - 위험 판단은 LLM이 아니라 **서버 키워드·수치 규칙**으로 한다 (REQ-022). 동작 설명·대처 행동·제안 문구는 **고정 콘텐츠**로, LLM은 코치 말투만 만든다

### 16. 흡연 욕구 SOS 시작 (5분 미루기) · 추가
- Method / Endpoint: `POST /api/v1/care/sos`
- Description: 충동 강도와 상황을 기록하고 5분 미루기 타이머·고정 대처 행동 3가지를 돌려준다.
- 인증: 필요
- Request Header: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- Request Parameter: -
- Request Body:

  ```json
  {
    "craving_level": 7,
    "situation": "stress"
  }
  ```
- Response Body (201):

  ```json
  {
    "sos_id": 4,
    "delay_minutes": 5,
    "ends_at": "2026-11-18T13:25:00+09:00",
    "tips": [
      "담배가 있는 장소에서 잠시 벗어나요.",
      "물을 천천히 마시거나 편안하게 호흡해요.",
      "짧은 산책이나 다른 행동으로 관심을 돌려요."
    ],
    "created_at": "2026-11-18T13:20:00+09:00"
  }
  ```
- Status Code: 201 Created / 400 craving_level 범위(1~10)·situation 값 오류 / 401 토큰 없음·만료
- 관련 테이블 · REQ: sos_logs · REQ-016
- 관련 화면: E05
- 비고: 초안의 `/api/v1/sos`를 옮김, memo 필드 제외(화면에 없음). situation(선택): stress / after_meal / boredom / drinking / other. tips는 고정 콘텐츠

### 20. 오늘의 코치 메시지·추천 행동 (하루 1회 생성, 저장본 재사용) · MVP
- Method / Endpoint: `GET /api/v1/coach/today`
- Description: 사실 데이터(예측·기록)를 바탕으로 만든 오늘의 코치 메시지와 추천 행동을 돌려준다.
- 인증: 필요
- Request Header: `Authorization: Bearer {access_token}`
- Request Parameter: Query `date` (선택, 기본 오늘)
- Request Body: -
- Response Body (200):

  ```json
  {
    "coach_message_id": 12,
    "date": "2026-11-18",
    "message": "피곤함이 이어져 힘드셨겠어요. 오늘은 무리한 목표보다 잠드는 시간을 기록하고, 편안한 호흡부터 해 보면 어떨까요?",
    "based_on": [
      "sleep_hours_low",
      "checkin_missed_2d"
    ],
    "recommended_actions": [
      {
        "action_code": "breathing",
        "title": "편안한 호흡 3분",
        "target": "routine",
        "target_id": 1
      },
      {
        "action_code": "sleep_checkin",
        "title": "수면 체크인",
        "target": "checkin",
        "target_id": null
      }
    ],
    "source": "llm",
    "safety_alert": null,
    "disclaimer": "AI 코치는 진단·처방·응급 상담을 제공하지 않아요.",
    "generated_at": "2026-11-18T07:00:00+09:00"
  }
  ```
- Status Code: 200 OK / 401 토큰 없음·만료 / 409 AI 처리 동의 없음(CONSENT_REQUIRED) · ※ LLM 실패·생성 전이어도 503 대신 규칙 기반 기본 문구로 200 (`source: "rule"`)
- 관련 테이블 · REQ: coach_messages · daily_challenges · checkins · REQ-021, NFR-001·007·010·014
- 관련 화면: D01, E01
- 비고: 새벽 배치로 AI 워커가 미리 생성 → 없으면 규칙 문구를 바로 반환하고 백그라운드 생성(P95 3초). `based_on` = LLM에 넘긴 사실 데이터 키(수치 원문 X). `target`: routine / checkin / menopause / sos / emotion_note / challenge. 위험 상태면 일반 코칭 대신 `safety_alert`와 고정 안내만 반환

### 21. AI 코치 대화 (SSE 스트리밍) · 추가
- Method / Endpoint: `POST /api/v1/coach/chat`
- Description: 사용자 메시지에 대한 코치 답변을 스트리밍으로 보낸다. 위험 표현이면 LLM을 부르지 않고 안내만 보낸다.
- 인증: 필요
- Request Header: `Content-Type: application/json`, `Authorization: Bearer {access_token}`, `Accept: text/event-stream`
- Request Parameter: -
- Request Body:

  ```json
  {
    "thread_id": null,
    "message": "요즘 피곤하고 잠이 부족해요."
  }
  ```
- Response Body (200 · text/event-stream):

  ```text
  Content-Type: text/event-stream

  event: meta
  data: {"thread_id":"th_7f3a","message_id":101}

  event: token
  data: {"text":"피곤함이 이어져 "}

  event: done
  data: {"message_id":102,"recommended_actions":[{"action_code":"breathing","target":"routine","target_id":1}]}

  (위험 표현 감지 시 · LLM 호출 없이)
  event: safety_alert
  data: {"alert_id":55,"alert_type":"mental_crisis"}

  (스트림 중 오류)
  event: error
  data: {"code":"AI_UNAVAILABLE","message":"잠시 후 다시 시도해 주세요."}
  ```
- Status Code: 200 OK (스트림 시작) / 400 message 비어 있음·500자 초과 / 401 토큰 없음·만료 / 404 thread 없음(본인 대화 아님 포함) / 409 AI 처리 동의 없음 / 429 호출 한도 초과 · ※ 스트림 시작 후 오류는 상태 코드 대신 `event: error`
- 관련 테이블 · REQ: coach_threads · coach_chat_messages(추가 제안) · safety_alerts · REQ-021·022, NFR-002·010
- 관련 화면: E01
- 비고: `thread_id`가 null이면 서버가 새 대화 생성(클라이언트 임의 id 금지). 입력을 먼저 서버 키워드 규칙으로 검사 → 위험이면 LLM 미호출. 최근 N턴만 LLM 전달, max_tokens 512. 와이어프레임 E01은 MVP라 범위 확인 필요

### 21-1. 코치 대화 내역 조회 · 추가 (추가 제안)
- Method / Endpoint: `GET /api/v1/coach/threads/{thread_id}/messages`
- Description: 이전 대화를 이어서 보여 주거나, 응답 생성 중·재시도 상태를 복원한다.
- 인증: 필요
- Request Header: `Authorization: Bearer {access_token}`
- Request Parameter: Path `thread_id` · Query `before_id`(선택), `size`(기본 20)
- Request Body: -
- Response Body (200):

  ```json
  {
    "thread_id": "th_7f3a",
    "items": [
      {
        "message_id": 101,
        "role": "user",
        "content": "요즘 피곤하고 잠이 부족해요.",
        "created_at": "2026-11-18T09:12:00+09:00"
      },
      {
        "message_id": 102,
        "role": "assistant",
        "content": "피곤함이 이어져 힘드셨겠어요. …",
        "created_at": "2026-11-18T09:12:04+09:00"
      }
    ],
    "has_more": false
  }
  ```
- Status Code: 200 OK / 400 size 범위 오류 / 401 토큰 없음·만료 / 404 thread 없음(본인 대화 아님 포함)
- 관련 테이블 · REQ: coach_chat_messages · REQ-021
- 관련 화면: E01
- 비고: 최신순 페이지네이션(`before_id`)

### 21-2. 위험 신호 안내 내용 조회 · MVP (추가 제안)
- Method / Endpoint: `GET /api/v1/safety/guides/{alert_type}`
- Description: 안내 종류별 제목·행동 버튼·안내 문구를 돌려준다 (E02 화면 내용).
- 인증: 불필요
- Request Header: `Content-Type: application/json`
- Request Parameter: Path `alert_type` (emergency | medical_consult | mental_crisis)
- Request Body: -
- Response Body (200):

  ```json
  {
    "alert_type": "emergency",
    "title": "지금은 안전 확인이 먼저예요",
    "question": "갑작스러운 심한 흉통·호흡곤란, 의식 저하, 한쪽 마비가 있나요?",
    "primary_action": {
      "label": "119에 전화하기",
      "type": "call",
      "value": "119"
    },
    "guides": [
      {
        "heading": "즉시 할 수 있는 행동",
        "items": [
          "혼자 있으면 주변 사람에게 도움을 요청하세요.",
          "직접 운전하지 말고 안내에 따라 도움을 받으세요."
        ]
      },
      {
        "heading": "응급 증상이 아니라면",
        "items": [
          "증상이 지속·악화되면 의료기관에 문의하세요."
        ]
      }
    ],
    "disclaimer": "이 안내는 증상만으로 상태를 확정하지 않습니다."
  }
  ```
- Status Code: 200 OK / 404 알 수 없는 alert_type
- 관련 테이블 · REQ: safety_guides(또는 서버 고정 설정) · REQ-022, NFR-014
- 관련 화면: E02
- 비고: 응급 안내는 로그인이 풀려도 열려야 해서 인증 불필요. mental_crisis = 자살예방 상담전화 109 안내, medical_consult = 의료기관 진료 권고. 문구 변경은 관리자 검토·승인 후 적용(F03)

### 21-3. 호흡·스트레칭 콘텐츠 목록 · 추가 (추가 제안)
- Method / Endpoint: `GET /api/v1/care/routines`
- Description: 미리 만든 호흡·스트레칭 루틴 목록을 돌려준다.
- 인증: 필요
- Request Header: `Authorization: Bearer {access_token}`
- Request Parameter: Query `type` (선택: breathing | stretching)
- Request Body: -
- Response Body (200):

  ```json
  {
    "items": [
      {
        "routine_id": 1,
        "type": "breathing",
        "title": "편안한 호흡 3분",
        "duration_sec": 180,
        "steps": [
          "코로 4초 들이마시고, 6초 천천히 내쉬어요.",
          "숨을 참거나 억지로 깊게 쉬지 않아도 돼요."
        ],
        "caution": "불편하거나 어지러우면 멈추고 평소처럼 호흡해요.",
        "seated": true
      },
      {
        "routine_id": 4,
        "type": "stretching",
        "title": "어깨·목 가볍게 풀기",
        "duration_sec": 300,
        "steps": [
          "어깨를 천천히 위아래로 5회 움직여요."
        ],
        "caution": "통증이 없는 범위에서 천천히 움직이세요.",
        "seated": true
      }
    ]
  }
  ```
- Status Code: 200 OK / 400 type 값 오류 / 401 토큰 없음·만료
- 관련 테이블 · REQ: care_routines(고정 콘텐츠) · REQ-014
- 관련 화면: E03
- 비고: 동작 설명은 미리 만든 고정 콘텐츠(LLM이 운동법을 만들지 않음). 문진에서 운동 제한 "예"인 사용자는 서버가 `seated: true`만 반환

### 21-4. 갱년기 오늘의 상태 저장 (같은 날 덮어쓰기) · 추가 (추가 제안)
- Method / Endpoint: `PUT /api/v1/care/menopause-logs/{log_date}`
- Description: 오늘 느낀 변화와 불편한 정도를 저장하고 생활 관리 제안을 돌려준다.
- 인증: 필요
- Request Header: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- Request Parameter: Path `log_date` (YYYY-MM-DD)
- Request Body:

  ```json
  {
    "symptoms": [
      "sleep_discomfort"
    ],
    "severity": "moderate"
  }
  ```
- Response Body (200):

  ```json
  {
    "log_date": "2026-11-18",
    "symptoms": [
      "sleep_discomfort"
    ],
    "severity": "moderate",
    "suggestions": [
      "편안한 수면 환경을 준비해 보세요.",
      "짧은 호흡·스트레칭으로 긴장을 풀어 보세요."
    ],
    "safety_alert": null,
    "updated_at": "2026-11-18T21:30:00+09:00"
  }
  ```
- Status Code: 200 OK (첫 저장·덮어쓰기 모두) / 400 값 오류 ("none"과 다른 증상 동시 선택 포함) / 401 토큰 없음·만료
- 관련 테이블 · REQ: menopause_logs(symptom_scores 대체 제안) · REQ-015
- 관련 화면: E04
- 비고: `symptoms`: hot_flash / sleep_discomfort / mood_change / other / none, `severity`: mild / moderate / severe. 제안 문구는 고정 규칙. 화면(일일 기록)과 REQ-015(MRS 4주)가 달라 확인 필요

### 21-5. 감정 메모 저장 · 추가 (추가 제안)
- Method / Endpoint: `POST /api/v1/care/emotion-notes`
- Description: 오늘의 감정과 짧은 메모를 나만 보기로 저장한다.
- 인증: 필요
- Request Header: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- Request Parameter: -
- Request Body:

  ```json
  {
    "note_date": "2026-11-18",
    "emotion": "tired",
    "memo": "오늘은 피곤했지만 잠깐 걸어서 좋았어요."
  }
  ```
- Response Body (201):

  ```json
  {
    "note_id": 17,
    "note_date": "2026-11-18",
    "emotion": "tired",
    "memo": "오늘은 피곤했지만 잠깐 걸어서 좋았어요.",
    "visibility": "private",
    "safety_alert": null,
    "created_at": "2026-11-18T22:10:00+09:00"
  }
  ```
- Status Code: 201 Created / 400 emotion 값 오류·memo 500자 초과 / 401 토큰 없음·만료
- 관련 테이블 · REQ: emotion_notes(추가 제안) · REQ-034·022, NFR-005·016
- 관련 화면: E06
- 비고: `emotion`: calm / tired / worried / happy, memo 선택(0~500자). 항상 나만 보기(가족 공유·관리자 조회 불가). memo는 서버 키워드 검사 → 위험 표현이면 `safety_alert`(mental_crisis). 임시 작성 내용은 프론트에서만 보관

### 21-6. 감정 메모 목록 조회 · 추가 (추가 제안)
- Method / Endpoint: `GET /api/v1/care/emotion-notes`
- Description: 내 감정 메모를 기간별로 조회한다.
- 인증: 필요
- Request Header: `Authorization: Bearer {access_token}`
- Request Parameter: Query `from_date`, `to_date`, `page`(기본 1), `size`(기본 10)
- Request Body: -
- Response Body (200):

  ```json
  {
    "items": [
      {
        "note_id": 17,
        "note_date": "2026-11-18",
        "emotion": "tired",
        "memo": "오늘은 피곤했지만 잠깐 걸어서 좋았어요.",
        "created_at": "2026-11-18T22:10:00+09:00"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 10
  }
  ```
- Status Code: 200 OK / 400 날짜 형식 오류 / 401 토큰 없음·만료
- 관련 테이블 · REQ: emotion_notes · REQ-034
- 관련 화면: E06
- 비고: 본인 메모만 조회

### 21-7. 감정 메모 수정 · 추가 (추가 제안)
- Method / Endpoint: `PATCH /api/v1/care/emotion-notes/{note_id}`
- Description: 감정이나 메모 내용을 고친다.
- 인증: 필요
- Request Header: `Content-Type: application/json`, `Authorization: Bearer {access_token}`
- Request Parameter: Path `note_id`
- Request Body:

  ```json
  {
    "emotion": "calm",
    "memo": "산책하고 나니 마음이 편해졌어요."
  }
  ```
- Response Body (200):

  ```json
  {
    "note_id": 17,
    "emotion": "calm",
    "memo": "산책하고 나니 마음이 편해졌어요.",
    "safety_alert": null,
    "updated_at": "2026-11-18T22:30:00+09:00"
  }
  ```
- Status Code: 200 OK / 400 값 오류·500자 초과 / 401 토큰 없음·만료 / 404 메모 없음(본인 것 아님 포함)
- 관련 테이블 · REQ: emotion_notes · REQ-034
- 관련 화면: E06
- 비고: 바뀐 필드만 전달. 수정할 때도 키워드 검사

### 21-8. 감정 메모 삭제 · 추가 (추가 제안)
- Method / Endpoint: `DELETE /api/v1/care/emotion-notes/{note_id}`
- Description: 감정 메모를 바로 삭제한다.
- 인증: 필요
- Request Header: `Authorization: Bearer {access_token}`
- Request Parameter: Path `note_id`
- Request Body: -
- Response Body (204):

  (본문 없음)
- Status Code: 204 No Content / 401 토큰 없음·만료 / 404 메모 없음(본인 것 아님 포함)
- 관련 테이블 · REQ: emotion_notes · REQ-034, NFR-005
- 관련 화면: E06
- 비고: 즉시 실제 삭제 (화면 안내: "언제든 수정·삭제할 수 있어요")

#### ➕ 추가 검토 (화면에 없어 본문에서 뺀 API · 화면이 추가되면 본문으로 옮김)
- [ ] PATCH /api/v1/care/sos/{sos_id} — 흡연 욕구 SOS 결과 기록 (버텼어요/피웠어요) (E05, REQ-016)
- [ ] GET /api/v1/care/sos/summary — 흡연 욕구 패턴 요약 (E05, REQ-016)
- [ ] PUT /api/v1/coach/messages/{coach_message_id}/feedback — 코치 메시지 피드백 👍/👎 (E01, NFR-008)
- [ ] PATCH /api/v1/safety/alerts/{alert_id} — 위험 신호 안내 확인·행동 기록 (E02, REQ-022·033)
- [ ] POST /api/v1/care/routines/{routine_id}/sessions — 호흡·스트레칭 완료·중단 기록 (E03, REQ-014)
- [ ] GET /api/v1/care/menopause-logs — 갱년기 기록 조회·변화 추이 (E04, REQ-015)

<!-- 05 END -->

---

<!-- 06 START · 관리자 · 담당: ______ -->
## 06. 관리자

담당: ______ · 관련 화면: F01~F04

### 27. 관리자 로그인
- Method / Endpoint: `POST /api/v1/admin/login`
- 인증: 불필요
- Request Header: Content-Type: application/json
- Request Parameter (Path / Query): -
- Request Body:

  ```json
  {
    "admin_id": "admin01",
    "password": "********"
  }
  ```
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 3600
  }
  ```
- Status Code: 성공: 200 OK / 400 필수값 누락 / 401 아이디/비밀번호 불일치
- 관련 테이블 · REQ: REQ-030
- 우선순위: MVP
- 비고: 일반 사용자 토큰과 구분(role=admin)

### 28. 챌린지·콘텐츠 목록 조회
- Method / Endpoint: `GET /api/v1/admin/challenges`
- 인증: 관리자
- Request Header: Content-Type: application/json / Authorization: Bearer {admin_access_token}
- Request Parameter (Path / Query): page, size, category_code(선택)
- Request Body: -
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "items": [
      {
        "challenge_id": 4,
        "category_code": "exercise",
        "title": "30분 걷기",
        "is_active": true
      }
    ],
    "total": 1
  }
  ```
- Status Code: 성공: 200 OK / 401 토큰 없음·만료 / 403 관리자 권한 없음
- 관련 테이블 · REQ: challenges · REQ-031
- 우선순위: MVP

### 29. 챌린지 등록
- Method / Endpoint: `POST /api/v1/admin/challenges`
- 인증: 관리자
- Request Header: Content-Type: application/json / Authorization: Bearer {admin_access_token}
- Request Parameter (Path / Query): -
- Request Body:

  ```json
  {
    "category_code": "exercise",
    "title": "30분 걷기",
    "description": "가까운 공원을 걸어요",
    "is_active": true
  }
  ```
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "challenge_id": 4,
    "created_at": "2026-11-18T12:00:00+09:00"
  }
  ```
- Status Code: 성공: 201 Created / 400 필수값 누락 / 401 토큰 없음·만료 / 403 관리자 권한 없음 / 409 제목 중복
- 관련 테이블 · REQ: challenges · REQ-031
- 우선순위: MVP

### 30. 챌린지 수정
- Method / Endpoint: `PUT /api/v1/admin/challenges/{challenge_id}`
- 인증: 관리자
- Request Header: Content-Type: application/json / Authorization: Bearer {admin_access_token}
- Request Parameter (Path / Query): Path: challenge_id
- Request Body:

  ```json
  {
    "title": "40분 걷기",
    "is_active": true
  }
  ```
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "challenge_id": 4,
    "title": "40분 걷기",
    "updated_at": "2026-11-18T12:30:00+09:00"
  }
  ```
- Status Code: 성공: 200 OK / 400 값 오류 / 401 토큰 없음·만료 / 403 관리자 권한 없음 / 404 챌린지 없음
- 관련 테이블 · REQ: challenges · REQ-031
- 우선순위: MVP

### 31. 챌린지 삭제
- Method / Endpoint: `DELETE /api/v1/admin/challenges/{challenge_id}`
- 인증: 관리자
- Request Header: Content-Type: application/json / Authorization: Bearer {admin_access_token}
- Request Parameter (Path / Query): Path: challenge_id
- Request Body: -
- Response Body (성공 예시 = Mock Data): (본문 없음)
- Status Code: 성공: 204 No Content / 401 토큰 없음·만료 / 403 관리자 권한 없음 / 404 챌린지 없음
- 관련 테이블 · REQ: challenges · REQ-031
- 우선순위: MVP
- 비고: 이력 보존을 위해 실제로는 비활성화(is_active=false) 처리 검토

### 32. 위험 키워드 목록 조회
- Method / Endpoint: `GET /api/v1/admin/safety-keywords`
- 인증: 관리자
- Request Header: Content-Type: application/json / Authorization: Bearer {admin_access_token}
- Request Parameter (Path / Query): page, size
- Request Body: -
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "items": [
      {
        "keyword_id": 1,
        "keyword": "가슴 통증",
        "severity": "high",
        "guide_message": "즉시 의료진 상담을 권해요"
      }
    ],
    "total": 1
  }
  ```
- Status Code: 성공: 200 OK / 401 토큰 없음·만료 / 403 관리자 권한 없음
- 관련 테이블 · REQ: safety_keywords · REQ-032
- 우선순위: MVP

### 33. 위험 키워드 등록
- Method / Endpoint: `POST /api/v1/admin/safety-keywords`
- 인증: 관리자
- Request Header: Content-Type: application/json / Authorization: Bearer {admin_access_token}
- Request Parameter (Path / Query): -
- Request Body:

  ```json
  {
    "keyword": "가슴 통증",
    "severity": "high",
    "guide_message": "즉시 의료진 상담을 권해요"
  }
  ```
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "keyword_id": 1,
    "created_at": "2026-11-18T12:40:00+09:00"
  }
  ```
- Status Code: 성공: 201 Created / 400 필수값 누락 / 401 토큰 없음·만료 / 403 관리자 권한 없음 / 409 키워드 중복
- 관련 테이블 · REQ: safety_keywords · REQ-032
- 우선순위: MVP

### 34. 위험 키워드 수정
- Method / Endpoint: `PUT /api/v1/admin/safety-keywords/{keyword_id}`
- 인증: 관리자
- Request Header: Content-Type: application/json / Authorization: Bearer {admin_access_token}
- Request Parameter (Path / Query): Path: keyword_id
- Request Body:

  ```json
  {
    "severity": "medium",
    "guide_message": "상담을 권해요"
  }
  ```
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "keyword_id": 1,
    "updated_at": "2026-11-18T12:50:00+09:00"
  }
  ```
- Status Code: 성공: 200 OK / 400 값 오류 / 401 토큰 없음·만료 / 403 관리자 권한 없음 / 404 키워드 없음
- 관련 테이블 · REQ: safety_keywords · REQ-032
- 우선순위: MVP

### 35. 위험 키워드 삭제
- Method / Endpoint: `DELETE /api/v1/admin/safety-keywords/{keyword_id}`
- 인증: 관리자
- Request Header: Content-Type: application/json / Authorization: Bearer {admin_access_token}
- Request Parameter (Path / Query): Path: keyword_id
- Request Body: -
- Response Body (성공 예시 = Mock Data): (본문 없음)
- Status Code: 성공: 204 No Content / 401 토큰 없음·만료 / 403 관리자 권한 없음 / 404 키워드 없음
- 관련 테이블 · REQ: safety_keywords · REQ-032
- 우선순위: MVP

### 36. 위험도 경계값 조회
- Method / Endpoint: `GET /api/v1/admin/thresholds`
- 인증: 관리자
- Request Header: Content-Type: application/json / Authorization: Bearer {admin_access_token}
- Request Parameter (Path / Query): -
- Request Body: -
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "items": [
      {
        "threshold_id": 1,
        "metric": "systolic_bp",
        "caution_value": 130,
        "danger_value": 160
      }
    ]
  }
  ```
- Status Code: 성공: 200 OK / 401 토큰 없음·만료 / 403 관리자 권한 없음
- 관련 테이블 · REQ: risk_thresholds · REQ-032
- 우선순위: MVP
- 비고: metric·단위는 ERD risk_thresholds 컬럼과 맞춤

### 37. 위험도 경계값 수정
- Method / Endpoint: `PUT /api/v1/admin/thresholds/{threshold_id}`
- 인증: 관리자
- Request Header: Content-Type: application/json / Authorization: Bearer {admin_access_token}
- Request Parameter (Path / Query): Path: threshold_id
- Request Body:

  ```json
  {
    "caution_value": 135,
    "danger_value": 160
  }
  ```
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "threshold_id": 1,
    "caution_value": 135,
    "danger_value": 160,
    "updated_at": "2026-11-18T13:00:00+09:00"
  }
  ```
- Status Code: 성공: 200 OK / 400 값 오류(주의값 ≥ 위험값 등) / 401 토큰 없음·만료 / 403 관리자 권한 없음 / 404 경계값 없음
- 관련 테이블 · REQ: risk_thresholds · REQ-032
- 우선순위: MVP

### 38. 운영 현황 조회 (개인 원문 제외)
- Method / Endpoint: `GET /api/v1/admin/stats`
- 인증: 관리자
- Request Header: Content-Type: application/json / Authorization: Bearer {admin_access_token}
- Request Parameter (Path / Query): from_date, to_date
- Request Body: -
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "period": {
      "from": "2026-11-01",
      "to": "2026-11-18"
    },
    "active_users": 120,
    "checkin_rate": 0.64,
    "coach_calls": 340,
    "avg_ttft_ms": 820,
    "token_cost_usd": 12.4,
    "tool_calls": 510
  }
  ```
- Status Code: 성공: 200 OK / 400 날짜 형식 오류 / 401 토큰 없음·만료 / 403 관리자 권한 없음
- 관련 테이블 · REQ: admin_logs · REQ-033, NFR-016
- 우선순위: MVP
- 비고: avg_ttft_ms·token_cost_usd·tool_calls는 v1.4 후보 REQ-033 (Langfuse 연동) 결정 후 확정

<!-- 06 END -->

---

## 확인 필요 (초안에서 가정한 부분)

| No | 내용 | 확인할 사람 |
|---|---|---|
| 1 | 요청·응답 필드는 ERD v1.3 컬럼과 대조해 이름·타입을 맞춰야 해요. 지금 필드는 요구사항·화면 설명을 바탕으로 만든 예시예요. | 백엔드 담당 |
| 2 | 카테고리 4개의 category_code 값(예시: exercise, diet, sleep, smoking)을 기획 확정값으로 교체 | 서비스 구조 담당 |
| 3 | 로그인 응답의 토큰 구성(access만 vs refresh 포함), 만료 시간 | 백엔드 담당 |
| 4 | 문진을 4단계 한 번에 제출할지, 단계별로 저장할지 (지금은 1회 제출 가정) | 문진 담당 · 백엔드 |
| 5 | 같은 날 체크인 재제출 정책(409 vs 덮어쓰기) | 챌린지 담당 · 백엔드 |
| 6 | 초대 수락 API(POST …/invite/accept)와 선택 문구 실제 전송 API는 스켈레톤에 없어서 제안으로 넣었거나 빠져 있어요 | 함께 관리 담당 |
| 7 | 관리자 챌린지 삭제를 실제 삭제로 할지 비활성화로 할지 | 관리자 담당 |
| 8 | v1.4 후보(REQ-021 근거 부족 시 답 보류·출처, NFR-005 해외 전송 동의, REQ-033 TTFT·토큰 비용)가 확정되면 coach·consents·stats 응답 필드 수정 | 팀장 |
| 9 | 개발 중에는 FastAPI Swagger(/docs)와 이 시트를 대조하고, 완료 후 시트를 최신 상태로 정리 | 백엔드 담당 |
| 10 | 체크인(No.15) 관련 REQ 표기 REQ-024(날씨) → REQ-028(복약) 정정 | 챌린지 담당 |
| 11 | AI 동의 없음을 409로 둘지 403으로 둘지 (권한 성격이라 403도 자연스러움) | 백엔드 담당 |

## 변경 이력

| 버전 | 날짜 | 내용 | 작성 |
|---|---|---|---|
| v0.1 | 2026-11-18 | 초안 시트 작성 (API 38개, 공통 규칙, 확인 필요) | 이명석 |
| v0.1-md | 2026-11-18 | md 변환 · 6구역 분리 · 추가 검토 항목 표시 | 엄태은 |
