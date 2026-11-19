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
## 건강 문진 및 검진 수치 API 명세서

**대화형 4단계 건강 문진(`B01`\~`B04`)**, **선택 검진 수치 입력/검증(`B05`)**, 그리고 **위험 예측/관리 평가 실행(`C01`/`C02` 분기)**을 위한 백엔드 REST API 명세서입니다.

## 🗺️ API 매핑 요약

| 그룹 | 메서드 · 경로 | 설명 | 연관 테이블 / REQ | 연관 화면 | 
| ----- | ----- | ----- | ----- | ----- | 
| **문진** | `POST /api/v1/questionnaires` | 문진 응답 저장 (최종 제출 및 임시 저장) | `questionnaires` · `REQ-004` | `B01` \~ `B04` | 
| **문진** | `GET /api/v1/questionnaires/draft` *(보조)* | 작성 중인 문진(임시 저장) 조회 | `questionnaires` · `REQ-004` | `B01` \~ `B04` | 
| **문진** | `POST /api/v1/checkups` | 검진 수치 입력(선택) 및 유효성 검증 | `checkup_records` · `REQ-005` | `B05` | 
| **평가** | `POST /api/v1/predictions` | 위험 예측 / 관리 평가 실행 (`C01`/`C02` 분기) | `risk_predictions` · `REQ-006·035` | `B05` → `C01`/`C02` | 

## 1. 문진 응답 저장 및 임시 저장 (`REQ-004`)

와이어프레임 `B01`\~`B04`에서 입력한 기본 정보, 건강 이력, 생활 습관 데이터를 저장합니다.

* 프론트엔드에서 `B01`\~`B03` 입력 상태를 유지하다가 `B04`(확인)에서 한 번에 호출하거나, `B01`의 **"저장하고 나중에 계속"** 클릭 시 `isDraft: true`로 호출하여 중간 저장할 수 있습니다.

* **Method & Endpoint:** `POST /api/v1/questionnaires`

* **연관 테이블 / REQ:** `questionnaires` · `REQ-004`

* **연관 화면:** `B01 · 기본 정보` \~ `B04 · 확인`

### Request Body

| 필드명 | 타입 | 필수 | 설명 및 허용 값 | 
| ----- | ----- | ----- | ----- | 
| `questionnaireId` | Long | N | 기존 임시 저장된 문진을 업데이트할 경우 전달 (신규 생성 시 `null`) | 
| `isDraft` | Boolean | Y | `true`: 저장하고 나중에 계속(임시 저장) / `false`: 문진 4단계 확인 완료 | 
| `age` | Integer | N | `[B01]` 만 나이 (예: `52`) | 
| `gender` | String | N | `[B01]` 성별 (`FEMALE`: 여성, `MALE`: 남성, `NO_RESPONSE`: 응답하지 않음) | 
| `heightCm` | Double | N | `[B01]` 키 (단위: cm, 예: `162.0`) | 
| `weightKg` | Double | N | `[B01]` 몸무게 (단위: kg, 예: `61.0`) | 
| `hasDiagnosedDisease` | Boolean | N | `[B02]` 진단받은 질환 유무 (`false`: 아니요, `true`: 예, 건너뛴 경우 `null`) | 
| `diagnosedDiseases` | Array<String> | N | `[B02]` 진단 질환 목록 (`HYPERTENSION`: 고혈압, `DIABETES`: 당뇨병, `DYSLIPIDEMIA`: 이상지질혈증, `OTHER`: 기타, `UNKNOWN`: 잘 모르겠어요) | 
| `isTakingMedication` | String | N | `[B02]` 현재 복약 여부 (`NO`: 없음, `YES`: 있음, `UNKNOWN`: 모름) | 
| `hasFamilyHistory` | String | N | `[B02]` 가족력 여부 (`NO`: 없음, `YES`: 있음, `UNKNOWN`: 모름) | 
| `smokingStatus` | String | N | `[B03]` 흡연 여부 (`NON_SMOKER`: 비흡연, `FORMER_SMOKER`: 과거 흡연, `CURRENT_SMOKER`: 현재 흡연) | 
| `drinkingFrequency` | String | N | `[B03]` 음주 빈도 (`ONCE_A_WEEK_OR_LESS`: 주 1회 이하 등 코드값) | 
| `exerciseDaysPerWeek` | Integer | N | `[B03]` 주당 운동 일수 (예: `2`) | 
| `exerciseMinutesPerDay` | Integer | N | `[B03]` 하루 운동 시간 - 분 단위 (예: `20`) | 
| `averageSleepMinutes` | Integer | N | `[B03]` 평균 수면 시간 - 분 단위 환산 (예: 6시간 30분 -> `390`) | 

```
{
  "questionnaireId": null,
  "isDraft": false,
  "age": 52,
  "gender": "FEMALE",
  "heightCm": 162,
  "weightKg": 61,
  "hasDiagnosedDisease": false,
  "diagnosedDiseases": [],
  "isTakingMedication": "NO",
  "hasFamilyHistory": "UNKNOWN",
  "smokingStatus": "NON_SMOKER",
  "drinkingFrequency": "ONCE_A_WEEK_OR_LESS",
  "exerciseDaysPerWeek": 2,
  "exerciseMinutesPerDay": 20,
  "averageSleepMinutes": 390
}

```

### Response (`201 Created`)

```
{
  "success": true,
  "code": "QUESTIONNAIRE_201",
  "message": "문진 응답이 저장되었습니다.",
  "data": {
    "questionnaireId": 1024,
    "status": "COMPLETED",
    "createdAt": "2026-11-18T18:35:00+09:00"
  }
}

```

### 1-1. 임시 저장된 문진 조회 (`B01` 재진입 시)

`B01` 하단의 **"저장하고 나중에 계속"**으로 이탈 후 재진입했을 때 이전 입력 내용을 복원하기 위한 보조 API입니다.

* **Method & Endpoint:** `GET /api/v1/questionnaires/draft`

* **Response (`200 OK`):** 저장된 문진이 없으면 `data: null` 반환, 존재하면 위 Request Body와 동일한 구조의 필드 반환.

## 2. 검진 수치 입력 (선택) (`REQ-005`)

`B05 · 검진 수치 입력` 화면에서 사용자가 입력한 혈압 및 혈당 수치를 검증하고 `checkup_records` 테이블에 저장합니다.

* **"수치 없이 평가하기"**를 선택한 경우 이 API를 호출하지 않고 바로 `3. 위험 예측 / 관리 평가 실행` API를 호출합니다.

* **Method & Endpoint:** `POST /api/v1/checkups`

* **연관 테이블 / REQ:** `checkup_records` · `REQ-005`

* **연관 화면:** `B05 · 검진 수치 입력`

### Request Body

| 필드명 | 타입 | 필수 | 설명 및 검증 규칙 | 
| ----- | ----- | ----- | ----- | 
| `questionnaireId` | Long | N | 연관된 문진 ID (`questionnaires.id`) | 
| `systolicBp` | Integer | N | 수축기 혈압 (단위: mmHg, 양의 정수, 이완기 혈압보다 커야 함) | 
| `diastolicBp` | Integer | N | 이완기 혈압 (단위: mmHg, 양의 정수, 수축기 혈압보다 작아야 함) | 
| `fastingBloodSugar` | Integer | N | 공복 혈당 (단위: mg/dL, 양의 정수) | 
| `measuredDate` | String | N | 측정일 (`YYYY-MM-DD` 형식, 미래 날짜 불가) | 

```
{
  "questionnaireId": 1024,
  "systolicBp": 120,
  "diastolicBp": 80,
  "fastingBloodSugar": null,
  "measuredDate": "2026-11-10"
}

```

### Response (`201 Created`)

```
{
  "success": true,
  "code": "CHECKUP_201",
  "message": "검진 수치가 저장되었습니다.",
  "data": {
    "checkupRecordId": 502,
    "questionnaireId": 1024,
    "systolicBp": 120,
    "diastolicBp": 80,
    "fastingBloodSugar": null,
    "measuredDate": "2026-11-10"
  }
}

```

### Error Response (`400 Bad Request` - `B05` 검증 오류)

숫자가 아닌 값(`"abc"`) 입력, 수축기 $\le$ 이완기 혈압 역전, 의학적 경계값 초과 시 반환됩니다.

```
{
  "success": false,
  "code": "CHECKUP_VALIDATION_400",
  "message": "입력 오류를 수정해 주세요.",
  "errors": [
    {
      "field": "systolicBp",
      "rejectedValue": "abc",
      "reason": "숫자로 입력해 주세요. 예: 120"
    },
    {
      "field": "bloodPressureRange",
      "reason": "수축기 혈압은 이완기 혈압보다 높아야 합니다."
    }
  ]
}

```

## 3. 위험 예측 / 관리 평가 실행 (`REQ-006·035`)

저장된 문진 응답(`questionnaireId`)과 선택적으로 입력된 검진 수치(`checkupRecordId`)를 바탕으로 위험 예측 및 건강 상태 평가를 실행하고 `risk_predictions`에 결과를 저장합니다.

* **Method & Endpoint:** `POST /api/v1/predictions`

* **연관 테이블 / REQ:** `risk_predictions` · `REQ-006·035`

* **연관 화면:** `B05` 완료 또는 `수치 없이 평가하기` 클릭 → 결과 화면(`C01` / `C02`) 이동

### Request Body

| 필드명 | 타입 | 필수 | 설명 | 
| ----- | ----- | ----- | ----- | 
| `questionnaireId` | Long | Y | 평가 대상 문진 ID (`POST /api/v1/questionnaires` 응답값) | 
| `checkupRecordId` | Long | N | 검진 수치 ID (`POST /api/v1/checkups` 응답값, **"수치 없이 평가하기"** 선택 시 `null`) | 

```
{
  "questionnaireId": 1024,
  "checkupRecordId": 502
}

```

### Response (`201 Created`)

> `진단 여부 및 수치 유무에 따라 결과 화면 C01 / C02 분기`에 맞춰 프론트엔드 라우팅용 `resultScreenType`을 함께 반환합니다.

```
{
  "success": true,
  "code": "PREDICTION_201",
  "message": "위험 예측 및 관리 평가가 완료되었습니다.",
  "data": {
    "predictionId": 8801,
    "questionnaireId": 1024,
    "checkupRecordId": 502,
    "resultScreenType": "C01",
    "hasCheckupMetrics": true,
    "riskSummary": {
      "overallLevel": "LOW",
      "headline": "현재 생활 습관이 전반적으로 양호합니다."
    },
    "createdAt": "2026-11-18T18:36:10+09:00"
  }
}

```

## 📋 상태 및 코드 정의 (Enum Reference)

| 구분 | 코드값 | 화면 표시 라벨 | 
| ----- | ----- | ----- | 
| **성별 (`gender`)** | `FEMALE` / `MALE` / `NO_RESPONSE` | 여성 / 남성 / 응답하지 않음 | 
| **진단 질환 (`diagnosedDiseases`)** | `HYPERTENSION` / `DIABETES` / `DYSLIPIDEMIA` / `OTHER` / `UNKNOWN` | 고혈압 / 당뇨병 / 이상지질혈증 / 기타 / 잘 모르겠어요 | 
| **복약·가족력 (`NO/YES/UNKNOWN`)** | `NO` / `YES` / `UNKNOWN` | 없음 / 있음 / 모름 | 
| **흡연 (`smokingStatus`)** | `NON_SMOKER` / `FORMER_SMOKER` / `CURRENT_SMOKER` | 비흡연 / 과거 흡연 / 현재 흡연 | 
| **결과 분기 (`resultScreenType`)** | `C01` / `C02` | `C01` (수치 미입력/일반 관리군) / `C02` (유질환·수치 기반 정밀 평가군) | 

<!-- 02 END -->

---

<!-- 03 START · 평가·대시보드 · 담당: 김도엽 -->
## 03. 평가·대시보드 (예측·기록)

담당: 김도엽 · 관련 화면: C01~C07 · 기준: ERD v1.3 (`risk_predictions`, `health_logs`, `risk_thresholds`) + Figma 프로토타입 C01~C07

> 03 구역 공통
> - Enum 값은 ERD와 같은 **대문자**로 주고받습니다. `disease_type`: HYPERTENSION / DIABETES / DYSLIPIDEMIA · `risk_level`: LOW / WARNING / HIGH
> - 필드명은 ERD 컬럼명 그대로 씁니다 (`weight`, `waist_size`, `pressure_systolic`, `pressure_diastolic`, `activity_days_per_week`, `sleep_hours`).
> - **예측 입력** = 최근 완료 문진 + 재계산 규칙(REQ-007)에 따른 최신값입니다.
>   - 체중·허리둘레: `health_logs` 최신값 (없으면 문진 값)
>   - 수면 시간: `checkins` **최근 14일 중 7일 이상** 기록이 있으면 그 평균, 7일 미만이면 문진 값을 그대로 씁니다. 수면은 하루하루 변동이 커서 기록이 충분히 쌓였을 때만 반영합니다.
>   - 흡연·음주·신체활동·식습관·가족력: 최근 문진 (2주마다 1분 재문진으로 갱신)
>   - **쓰지 않는 값**: 검진 수치(`checkup_records`)와 혈압·혈당 기록. 질환 라벨을 정하는 값이라 입력에 넣으면 라벨 누수가 됩니다. 검진 수치는 규칙 기반 "기준 초과 안내"에만 씁니다.
>   - 실제 계산에 쓴 값과 출처는 `risk_predictions.input_snapshot`에 남깁니다.
> - **재계산 시점** (REQ-007, 하루 최대 1회)
>   - 바로 재계산: 첫 문진·재문진 완료(No 9), 체중·허리둘레 기록(No 17)
>   - 주기 재계산: 수면은 체크인할 때마다 재계산하지 않습니다. 주 1회(월요일 새벽) 서버가 아래 순서로 처리합니다. (04 구역은 체크인 저장만 담당, 대조 결과 11 합의)
>     1. 이번 주에 적용할 수면 값을 정합니다: 최근 14일 중 7일 이상 기록이 있으면 평균, 7일 미만이면 문진 값. 기록이 줄어 평균에서 문진 값으로 바뀌는 경우도 같은 방식으로 정합니다.
>     2. 이 값을 직전 예측의 입력 수면 값(`input_snapshot`)과 비교해 0.5시간 이상 차이 날 때만 새로 계산하고 이력을 남깁니다(`reason`: SLEEP_CHECKIN).
>   - 같은 날 이미 계산했다면 그날은 다시 계산하지 않고, 바뀐 값은 다음 재계산 때 반영합니다.
>   - 혈압·혈당 기록, 기분·복약 체크인은 예측 입력이 아니라 재계산하지 않습니다.
> - **점수 방향**: 질환별 `risk_score`(0~1)와 종합 `overall.score`(0~100) 모두 **높을수록 위험 신호가 큽니다.**
> - **화면 분기**: 미진단 질환이 하나라도 있으면 C01, 세 질환 모두 관리 중이면 C02. 일부만 관리 중인 사용자는 C01을 보되, 관리 중인 질환은 C01 안의 "관리 중인 질환" 카드에서 C02(No 19-1)로 연결합니다.
> - 화면 문구는 "위험 신호"이고 진단·치료 효과처럼 읽히는 표현은 쓰지 않습니다 (NFR-014). 모든 결과 응답에 `disclaimer`를 넣습니다.
> - ⚠️ 표시는 **ERD v1.3에 없는데 Figma 화면에는 있는 값**입니다. 구역 맨 아래 "ERD 대조 결과" 표에 모아 두었습니다.

### 9. 위험 신호 예측 실행 · MVP
- Method / Endpoint: `POST /api/v1/predictions`
- Description: 문진을 마친 뒤 3개 질환의 위험 신호를 계산해 저장한다. 입력은 공통 규칙의 "예측 입력"대로 문진에 최신 기록값을 합친 것이다. 진단받았거나 약을 먹는 질환은 예측하지 않고 `is_managed: true`로 돌려준다. 미진단 질환이 하나라도 있으면 C01, 모두 관리 중이면 C02로 보낸다.
- 인증: 필요
- Request Header: `Content-Type: application/json` / `Authorization: Bearer {access_token}`
- Request Parameter: -
- Request Body:

  ```json
  { "questionnaire_id": 5 }
  ```
- Response Body (201):

  ```json
  {
    "prediction_date": "2026-11-18",
    "view": "RISK",
    "overall": { "score": 62, "score_max": 100, "grade": "WARNING", "grade_label": "관리 권장", "basis_disease_type": "DIABETES" },
    "managed_diseases": ["HYPERTENSION"],
    "input_count": 8,
    "input_sources": { "questionnaire_id": 5, "weight": "HEALTH_LOG", "waist_size": "QUESTIONNAIRE", "sleep_hours": "CHECKIN_14D" },
    "factors": [
      { "code": "activity_days_per_week", "label": "운동 시간 부족", "is_missing": false },
      { "code": "sleep_hours", "label": "수면 시간 부족", "is_missing": false },
      { "code": "waist_size", "label": "허리둘레", "is_missing": false },
      { "code": "family_htn", "label": "가족력은 미확인", "is_missing": true }
    ],
    "results": [
      { "prediction_id": 21, "disease_type": "HYPERTENSION", "is_managed": true, "risk_score": null, "risk_level": null, "major_factors": [] },
      { "prediction_id": 22, "disease_type": "DIABETES", "is_managed": false, "risk_score": 0.62, "risk_level": "WARNING", "major_factors": ["waist_size", "family_dm", "activity_days_per_week"] },
      { "prediction_id": 23, "disease_type": "DYSLIPIDEMIA", "is_managed": false, "risk_score": 0.18, "risk_level": "LOW", "major_factors": ["waist_size"] }
    ],
    "model_version": "risk-v0.1",
    "disclaimer": "진단·치료 판단에 사용할 수 없으며, 정확한 판단은 의료진과 상담하세요.",
    "created_at": "2026-11-18T10:15:00+09:00"
  }
  ```
- Status Code: 201 Created / 400 `questionnaire_id` 누락·문진 미완료(`is_completed=false`) / 401 토큰 없음·만료 / 404 문진 기록 없음 / 409 건강정보 동의 없음(→ 확인 필요 11) · 오늘 이미 계산함(하루 최대 1회, 기존 결과를 그대로 반환할지 팀 결정) / 500 예측 모델 오류
- 관련 테이블 · REQ: risk_predictions, questionnaires, risk_thresholds · REQ-006·007·035
- 관련 화면: C01 (전부 관리 중이면 C02)
- 종합 점수(`overall`) 산출 규칙 · 제안 (예측 모델 담당 확정 예정)
  1. 대상은 `is_managed: false`인 질환만입니다. 관리 중인 질환은 계산에서 뺍니다. 셋 다 관리 중이면 `overall`은 `null`이고 `view`는 MANAGEMENT입니다.
  2. 대상 질환 중 **위험 단계(`risk_level`)가 가장 높은 질환**을 기준으로 삼고, 단계가 같으면 `risk_score`가 큰 쪽을 고릅니다. 이 질환이 `basis_disease_type`입니다.
  3. `score` = 기준 질환의 `risk_score` × 100 (정수 반올림), `grade` = 기준 질환의 `risk_level`. 점수와 등급이 같은 질환에서 나오므로 서로 어긋나지 않습니다.
  4. 평균을 쓰지 않는 이유: 한 질환의 위험 신호가 높아도 나머지 두 질환이 낮으면 평균에 묻혀 버립니다.
  5. 전제: 질환별 모델 확률은 보정(calibration)해서 0~1의 의미를 맞춥니다. 단계 경계값은 질환별 `risk_thresholds`를 씁니다.
  6. `grade_label`(안): LOW "양호" · WARNING "관리 권장" · HIGH "상담 권장". 진단처럼 읽히지 않는지 문구 확정 필요(NFR-014).
- 재계산: 이 API는 사용자가 문진(첫 문진·재문진)을 마쳤을 때 호출합니다. 체중·허리둘레 기록과 수면 평균 변화에 따른 재계산은 서버가 공통 규칙의 "재계산 시점"대로 실행하고 새 이력을 남깁니다(사유는 No 10의 `reason`).
- 비고:
  - 초안의 `mode`(요청)와 `checkup_id`를 뺐습니다. 미진단/기진단은 사용자가 고르는 값이 아니라 문진의 진단·복약 응답으로 서버가 질환별로 정합니다(`is_managed`). `view`는 화면 분기용: RISK(C01) / MANAGEMENT(C02).
  - `managed_diseases`가 비어 있지 않으면 C01에 "관리 중인 질환" 카드를 띄우고 C02(No 19-1)로 연결합니다. 현재 Figma C01에는 이 카드가 없습니다. → 대조 결과 10
  - `input_sources`는 각 입력이 어디서 왔는지(`QUESTIONNAIRE` / `HEALTH_LOG` / `CHECKIN_14D`) 보여 줍니다. 수면 기록이 14일 중 7일 미만이면 `sleep_hours`는 `QUESTIONNAIRE`입니다. `input_snapshot`에 같이 저장합니다.
  - Figma C01 예시의 영향 요인 "최근 혈압 기록"은 쓸 수 없습니다. 혈압은 고혈압 라벨을 정하는 값이라 예측 입력이 아니기 때문입니다. 예시를 `waist_size`(허리둘레)로 바꿨고, 화면 문구도 수정이 필요합니다.
  - `results[]`는 ERD `risk_predictions` 행(질환당 1행)과 1:1입니다. `major_factors`는 `major_factor1~3`을 배열로 묶은 것이고 값은 문진 컬럼명입니다.
  - ⚠️ `overall`(대사 건강 위험 점수 62/100 · 관리 권장), `input_count`(입력 정보 8개 반영), `factors[].is_missing`(가족력은 미확인)은 C01에 있지만 ERD에 없습니다. → 대조 결과 1·2
  - 수치는 코드로 계산하고 LLM은 쓰지 않습니다.

### 9-1. 최근 예측 결과 조회 · MVP (추가 제안)
- Method / Endpoint: `GET /api/v1/predictions/latest`
- Description: 가장 최근 예측 결과를 다시 보여 준다 (C01 재진입, 홈 카드, C06 기준 결과).
- 인증: 필요
- Request Header: `Authorization: Bearer {access_token}`
- Request Parameter: -
- Response Body (200): No 9 응답과 동일
- Status Code: 200 OK / 401 토큰 없음·만료 / 404 예측 이력 없음
- 관련 테이블 · REQ: risk_predictions · REQ-006·007
- 관련 화면: C01, C06
- 비고: POST(No 9)는 계산을 새로 돌리므로, 화면을 다시 열 때는 이 API를 씁니다.

### 10. 예측 이력 조회 · MVP
- Method / Endpoint: `GET /api/v1/predictions`
- Description: 날짜별 예측 이력을 최신순으로 보여 준다. 하루 최대 1회라 날짜가 한 회차다.
- 인증: 필요
- Request Header: `Authorization: Bearer {access_token}`
- Request Parameter: Query `period`(1m | 3m | all, 기본 3m), `page`(기본 1), `size`(기본 10)
- Response Body (200):

  ```json
  {
    "items": [
      { "prediction_date": "2026-11-18", "overall_score": 62, "reason": "SLEEP_CHECKIN", "reason_label": "수면 기록 반영", "model_version": "risk-v0.1" },
      { "prediction_date": "2026-11-11", "overall_score": 65, "reason": "RECHECK", "reason_label": "운동·수면 문진", "model_version": "risk-v0.1" },
      { "prediction_date": "2026-11-04", "overall_score": 68, "reason": "HEALTH_LOG", "reason_label": "체중 기록 반영", "model_version": "risk-v0.1" },
      { "prediction_date": "2026-10-28", "overall_score": 72, "reason": "INITIAL", "reason_label": "첫 문진 결과", "model_version": "risk-v0.1" }
    ],
    "total": 4,
    "page": 1,
    "size": 10,
    "model_version_changed": false
  }
  ```
- Status Code: 200 OK / 400 `period` 값 오류 / 401 토큰 없음·만료
- 관련 테이블 · REQ: risk_predictions · REQ-007
- 관련 화면: C03
- 비고:
  - C03 카드 = 날짜 · 점수 · 다시 계산된 이유. 초안의 `from_date`·`to_date`는 화면의 기간 선택(최근 3개월 ▼)에 맞춰 `period`로 바꿨습니다.
  - `model_version_changed`는 하단 안내("입력 항목이나 모델 변경 시 직접 비교에 유의")를 띄울지 판단하는 값입니다.
  - `reason` 값: INITIAL(첫 문진) / RECHECK(재문진) / HEALTH_LOG(체중·허리둘레 기록 반영) / SLEEP_CHECKIN(수면 평균 반영). `reason_label`은 화면 문구입니다(예: "체중 기록 반영", "수면 기록 반영"). C03의 "최근 결과" 표시는 사유가 아니라 목록 첫 항목에 화면이 붙이는 표시입니다.
  - ⚠️ `reason`은 ERD에 없습니다. → 대조 결과 3
  - 카드의 `›`를 눌러 그 회차 상세로 들어간다면 상세 API가 더 필요합니다. → 추가 검토

### 11. “만약에” 시뮬레이션 (저장하지 않음) · 추가
- Method / Endpoint: `POST /api/v1/predictions/simulate`
- Description: 최근 예측의 입력에서 바꿀 수 있는 생활습관 값만 바꿔 다시 계산해 비교한다. 저장하지 않는다.
- 인증: 필요
- Request Header: `Content-Type: application/json` / `Authorization: Bearer {access_token}`
- Request Parameter: -
- Request Body:

  ```json
  {
    "base_prediction_date": "2026-11-18",
    "changes": { "activity_days_per_week": 4, "sleep_hours": 7.0 }
  }
  ```
- Response Body (200):

  ```json
  {
    "base_prediction_date": "2026-11-18",
    "changes": [
      { "code": "activity_days_per_week", "label": "주간 운동 횟수", "unit": "일", "current": 2, "assumed": 4 },
      { "code": "sleep_hours", "label": "하루 평균 수면", "unit": "시간", "current": 6.5, "assumed": 7.0 }
    ],
    "overall": { "current": 62, "simulated": 56, "diff": -6 },
    "results": [
      { "disease_type": "DIABETES", "current_level": "WARNING", "simulated_level": "WARNING" },
      { "disease_type": "DYSLIPIDEMIA", "current_level": "LOW", "simulated_level": "LOW" }
    ],
    "is_saved": false,
    "notice": "결과는 효과를 보장하지 않으며, 인과관계나 치료 효과로 해석할 수 없습니다."
  }
  ```
- Status Code: 200 OK / 400 `changes` 값 범위 오류·바꿀 수 없는 항목(나이·성별·가족력) 포함 / 401 토큰 없음·만료 / 404 기준 예측 없음 / 500 예측 모델 오류
- 관련 테이블 · REQ: risk_predictions(`input_snapshot` 읽기만) · REQ-008
- 관련 화면: C06
- 비고:
  - C06은 "현재 2일 → 가정 4일"처럼 쌍으로 보여 주므로 응답 `changes[]`에 현재값·가정값을 함께 줍니다. 현재값은 `input_snapshot`에서 꺼냅니다.
  - 화면에 그려진 조절 항목은 운동 횟수·수면 2개입니다. REQ-008은 허리둘레·흡연·음주도 포함하므로 `changes`는 같은 방식으로 `waist_size`, `smoking_status`, `drinking_days_per_week`를 받을 수 있게 둡니다(화면 추가 여부는 프론트와 결정).
  - 관리 중(`is_managed`)인 질환은 `results`에서 빠집니다.

### 17. 건강 수치 기록 · MVP
- Method / Endpoint: `POST /api/v1/health-logs`
- Description: 그날의 건강 수치를 기록한다. 화면의 탭(혈압·혈당·체중)에서 입력한 항목만 보내고, 같은 날짜에 다시 보내면 보낸 항목만 덮어쓴다.
- 인증: 필요
- Request Header: `Content-Type: application/json` / `Authorization: Bearer {access_token}`
- Request Parameter: -
- Request Body (혈압 탭 예시):

  ```json
  {
    "log_date": "2026-11-18",
    "measured_time": "08:30",
    "pressure_systolic": 128,
    "pressure_diastolic": 82,
    "measure_context": "MORNING_REST",
    "memo": "아침 식사 전 측정"
  }
  ```
  체중 탭은 `{ "log_date": "2026-11-18", "weight": 61.0 }`, 허리둘레는 `"waist_size": 82.5`를 같은 방식으로 보낸다.
- Response Body (201 새 기록 / 200 같은 날 덮어쓰기):

  ```json
  {
    "health_log_id": 31,
    "log_date": "2026-11-18",
    "weight": null,
    "waist_size": null,
    "pressure_systolic": 128,
    "pressure_diastolic": 82,
    "measured_time": "08:30",
    "measure_context": "MORNING_REST",
    "memo": "아침 식사 전 측정",
    "recalculated": false,
    "created_at": "2026-11-18T08:31:00+09:00"
  }
  ```
- Status Code: 201 Created / 200 OK(같은 날 덮어쓰기) / 400 수치 범위·형식 오류, 수치가 하나도 없음, 혈압은 수축기·이완기 둘 다 필요 / 401 토큰 없음·만료
- 관련 테이블 · REQ: health_logs · REQ-029·007·018
- 관련 화면: C05
- 비고:
  - 초안의 `log_type` 방식 대신 ERD `health_logs` 구조(하루 1행, 항목별 컬럼, "하루 여러 번이면 마지막 값 사용")를 그대로 따랐습니다. 화면의 탭은 어떤 항목을 보낼지만 결정합니다.
  - `recalculated`: 체중·허리둘레 최신값이 예측 입력에 반영돼 위험 신호가 다시 계산됐으면 true입니다(공통 규칙 "예측 입력", REQ-007, 하루 최대 1회). 혈압만 기록한 경우는 예측 입력이 아니라 false입니다.
  - ⚠️ C05에 있는 **혈당 탭**, 측정 시각(`measured_time`), 측정 상황(`measure_context`), 메모(`memo`)는 ERD에 없습니다. 반대로 ERD·REQ-029에 있는 **허리둘레는 C05에 없습니다.** → 대조 결과 4·5
  - 혈당·체중 탭 안쪽 항목은 Figma에 혈압 탭만 그려져 있어 확인하지 못했습니다.

### 17-1. 건강 수치 기록 수정 · MVP (추가 제안)
- Method / Endpoint: `PATCH /api/v1/health-logs/{health_log_id}`
- Description: 저장한 기록의 일부 항목을 고친다.
- 인증: 필요
- Request Header: `Content-Type: application/json` / `Authorization: Bearer {access_token}`
- Request Parameter: Path `health_log_id`
- Request Body:

  ```json
  { "pressure_systolic": 126, "pressure_diastolic": 80 }
  ```
- Response Body (200): No 17 응답과 동일
- Status Code: 200 OK / 400 수치 범위·형식 오류 / 401 토큰 없음·만료 / 403 내 기록이 아님 / 404 기록 없음
- 관련 테이블 · REQ: health_logs · REQ-029
- 관련 화면: C04 → C05
- 비고: C05 안내문 "저장 후 기록 추이에서 수정·삭제할 수 있어요" 때문에 필요합니다.

### 17-2. 건강 수치 기록 삭제 · MVP (추가 제안)
- Method / Endpoint: `DELETE /api/v1/health-logs/{health_log_id}`
- Description: 기록 1건(하루치)을 지운다.
- 인증: 필요
- Request Header: `Authorization: Bearer {access_token}`
- Request Parameter: Path `health_log_id`
- Response Body (204): -
- Status Code: 204 No Content / 401 토큰 없음·만료 / 403 내 기록이 아님 / 404 기록 없음
- 관련 테이블 · REQ: health_logs · REQ-029
- 관련 화면: C04
- 비고: 이미 계산된 예측 이력은 지우지 않습니다(이력은 `input_snapshot`으로 남음).

### 18. 건강 수치 기록 목록 조회 · MVP
- Method / Endpoint: `GET /api/v1/health-logs`
- Description: 기록 원본을 날짜 최신순으로 준다 (수정·삭제할 기록 고르기용). 차트용 집계는 No 19가 맡는다.
- 인증: 필요
- Request Header: `Authorization: Bearer {access_token}`
- Request Parameter: Query `period`(1m | 3m | all, 기본 1m), `page`(기본 1), `size`(기본 10)
- Response Body (200):

  ```json
  {
    "items": [
      { "health_log_id": 31, "log_date": "2026-11-18", "weight": 61.0, "waist_size": null, "pressure_systolic": 128, "pressure_diastolic": 82, "measured_time": "08:30", "measure_context": "MORNING_REST", "memo": "아침 식사 전 측정" },
      { "health_log_id": 27, "log_date": "2026-11-11", "weight": 61.4, "waist_size": 82.5, "pressure_systolic": 130, "pressure_diastolic": 84, "measured_time": "08:20", "measure_context": "MORNING_REST", "memo": null }
    ],
    "total": 2,
    "page": 1,
    "size": 10
  }
  ```
- Status Code: 200 OK / 400 `period` 값 오류 / 401 토큰 없음·만료
- 관련 테이블 · REQ: health_logs · REQ-029·018
- 관련 화면: C04, C05
- 비고: 초안의 `log_type`·`from_date`·`to_date` 대신 C04와 같은 `period` 하나로 맞췄습니다. 공통 페이지 응답(`items`·`total`·`page`·`size`)을 따릅니다.

### 19. 기록 추이·위험도 변화 요약 · MVP
- Method / Endpoint: `GET /api/v1/dashboard`
- Description: 선택한 기간의 위험 점수 추이와 건강 수치 추이를 차트에 바로 쓸 수 있게 집계해 준다.
- 인증: 필요
- Request Header: `Authorization: Bearer {access_token}`
- Request Parameter: Query `period`(1m | 3m | all, 기본 1m)
- Response Body (200):

  ```json
  {
    "period": "1m",
    "risk_score_trend": {
      "score_max": 100,
      "points": [
        { "date": "2026-10-28", "score": 72 },
        { "date": "2026-11-04", "score": 68 },
        { "date": "2026-11-11", "score": 65 },
        { "date": "2026-11-18", "score": 62 }
      ]
    },
    "health_trends": [
      {
        "metric": "pressure_systolic",
        "label": "수축기 혈압",
        "unit": "mmHg",
        "points": [
          { "date": "2026-10-28", "value": 134 },
          { "date": "2026-11-04", "value": 132 },
          { "date": "2026-11-11", "value": 130 },
          { "date": "2026-11-18", "value": 128 }
        ]
      }
    ],
    "notice": "서로 다른 지표는 분리해 표시합니다. 변화가 치료 효과를 뜻하지 않습니다."
  }
  ```
- Status Code: 200 OK / 400 `period` 값 오류 / 401 토큰 없음·만료
- 관련 테이블 · REQ: risk_predictions, health_logs · REQ-018·019
- 관련 화면: C04
- 비고:
  - 초안의 `period`(7d | 30d | 90d)를 C04 선택지(최근 1개월 · 3개월 · 전체)에 맞췄습니다.
  - C04에 그려진 차트는 위험 점수 추이·수축기 혈압 추이 2개입니다. `health_trends`를 배열로 두어 체중(`weight`)·허리둘레(`waist_size`) 카드가 추가돼도 응답 구조가 안 바뀌게 했습니다.
  - 초안의 `challenge_completion_rate`는 C04에 없어 뺐습니다(실천율은 C02 → No 19-1). `risk_change`는 `risk_score_trend`로 대체했습니다.
  - REQ-018의 미션 달성률·수면 추이, REQ-019의 **질환별** 위험도 그래프는 C04에 없습니다. → 대조 결과 1·6
  - 마지막 점이 최신값입니다(화면에서 진하게 표시).

### 19-1. 관리 평가 요약 (기진단) · MVP (추가 제안)
- Method / Endpoint: `GET /api/v1/management/summary`
- Description: 진단받은 질환이 **하나라도 있는** 사용자에게 그 질환들의 이번 주 생활 관리 현황을 보여 준다. 예측 점수는 주지 않는다. 진입: 세 질환 모두 관리 중이면 예측 직후 C02로 바로, 일부만 관리 중이면 C01의 "관리 중인 질환" 카드에서 C02로.
- 인증: 필요
- Request Header: `Authorization: Bearer {access_token}`
- Request Parameter: -
- Response Body (200):

  ```json
  {
    "week_start": "2026-11-16",
    "week_end": "2026-11-22",
    "completion": { "rate": 0.71, "planned_count": 7, "completed_count": 5 },
    "managed_items": [
      {
        "disease_type": "HYPERTENSION",
        "label": "고혈압",
        "latest_log": { "log_date": "2026-11-18", "pressure_systolic": 128, "pressure_diastolic": 82 },
        "medication_check": { "checked_days": 6, "total_days": 7 }
      }
    ],
    "suggestions": [
      "같은 시간에 혈압을 기록해 보세요.",
      "처방약 변경·중단은 반드시 의료진과 상의하세요."
    ],
    "disclaimer": "이 평가는 생활 관리 요약이며 질환의 호전이나 치료 효과를 판정하지 않습니다."
  }
  ```
- Status Code: 200 OK / 401 토큰 없음·만료 / 404 관리 중인 질환 없음
- 관련 테이블 · REQ: risk_predictions(`is_managed`), daily_challenges, health_logs, checkins · REQ-035
- 관련 화면: C02
- 비고:
  - C02 = 이번 주 실천율(71% · 계획 7회 중 5회) · 관리 중인 항목(질환, 최근 기록, 복약 체크 6/7일) · 이번 주 제안. 매일 바뀌는 집계라 예측 저장(No 9)과 분리했습니다.
  - `completion`은 `daily_challenges`(배정·완료)에서 계산합니다. 실천율은 초안과 같이 0~1 비율로 줍니다.
  - `suggestions`는 규칙 기반 고정 문구로 시작합니다(LLM 아님). 약 조절을 권하는 문구는 넣지 않습니다.
  - ⚠️ 복약 체크는 ERD `checkins`에 컬럼이 없습니다(No 15 요청에는 `medication_taken`이 있음). → 대조 결과 7 · 04 참고

#### ➕ 추가 검토 (화면에는 있는데 03 구역에 아직 없는 것)
- [ ] 예측 회차 상세 조회 (예: `GET /api/v1/predictions/{prediction_date}`) — C03 카드의 `›`가 상세로 들어가는 동작이면 필요. 응답은 No 9와 동일하게.
- [ ] C07 참여 유형 선택(혼자 꾸준히 / 가까운 사람과 함께 / 코치의 안내와 함께, "나중에 선택하기" 있음) 저장 → 사용자 설정이라 **01 참고** (No 4 `PATCH /users/me`에 필드 추가 요청). REQ-020의 자동 분류(운동형·식이형 등)와는 다른 값입니다.
- [ ] C01 "나에게 맞는 챌린지 보기" → **04 참고** (D02 추천).

#### 03 구역 ERD 대조 결과 · 팀 확인 요청
| # | 내용 | 확인할 사람 |
|---|---|---|
| 1 | Figma C01·C03·C04·C06은 **종합 점수 1개(대사 건강 위험 점수 0~100)** 만 보여 주는데, 요구사항(REQ-006·019)과 ERD는 **질환별 3개**(`risk_score` 0~1, `risk_level`)입니다. 지금 명세는 둘 다 응답에 넣었습니다. 종합 점수 규칙은 No 9에 **제안**으로 적었습니다(관리 중 질환 제외, 가장 높은 단계 질환 기준, 높을수록 위험). 결정 필요: ① 이 규칙 채택 여부 ② 질환별 결과를 화면에 보여 줄지 | 팀 전체 · 예측 모델(김도엽) · 프론트 |
| 2 | 종합 점수·등급을 저장하려면 ERD에 자리가 필요합니다(`risk_predictions`는 질환당 1행). 저장하지 않고 조회 때마다 계산하는 방법도 있지만, 경계값이 바뀌면 과거 점수가 달라집니다. 등급 이름("관리 권장")과 `risk_level` 3단계(낮음·주의·높음)의 관계도 정리 필요 | 백엔드 · 예측 모델 |
| 3 | C03의 "다시 계산된 이유"(첫 문진 / 재문진 / 기록 반영)를 보여 주려면 `risk_predictions`에 `reason` 컬럼이 필요 | 백엔드 |
| 4 | C05에 혈당 탭·측정 시각·측정 상황·메모가 있는데 ERD `health_logs`에는 없음 → 컬럼 추가(`blood_glucose`, `measured_time`, `measure_context`, `memo`) 또는 화면에서 제외. 혈당은 REQ-029(체중·허리둘레·혈압)에도 없고 예측 입력도 아님 | 프론트 · 백엔드 · 기획 |
| 5 | 허리둘레는 재계산 입력(REQ-007)인데 C05에 입력 칸이 없음 → C05에 추가하거나 재문진에서만 받기 | 프론트 · 기획 |
| 6 | REQ-018의 체중·허리둘레·미션 달성률·수면 추이, REQ-020 참여 유형 분류가 C04에 없음 → 화면에 추가할지, 요구사항에서 뺄지 | 프론트 · 기획 |
| 7 | 복약 체크(C02 "이번 주 6/7일")를 저장할 컬럼이 `checkins`에 없음 | 04 담당 · 백엔드 |
| 8 | C01 "입력 정보 8개 반영"의 세는 기준(문진 항목 수 vs 모델 입력 수), `factors`의 `code`·문구는 문진(02) 필드와 모델 확정 후 맞춤. 지금 값은 화면 예시 기준 | 02 담당 · 예측 모델 |
| 9 | 같은 날 예측을 다시 요청했을 때(하루 최대 1회) 409로 막을지, 기존 결과를 200으로 돌려줄지 | 백엔드 |
| 10 | 일부 질환만 관리 중인 사용자를 위해 C01에 "관리 중인 질환" 카드(→ C02)가 필요합니다. 영향 요인 예시 "최근 혈압 기록"은 예측 입력이 아니라서 문구 교체가 필요합니다 | 프론트 |
| 11 | ✅ 합의(11/19, 홍시윤): 수면은 "14일 중 7일 이상이면 평균·미만이면 문진 값, 주 1회 재계산, 직전 입력값과 0.5시간 이상 차이 날 때만 새 이력". 04 구역은 체크인 저장, 재계산은 03 공통 규칙에 따라 서버 처리 | 04 담당(홍시윤) · 예측 모델(김도엽) · 백엔드 |

<!-- 03 END -->

---

<!-- 04 START · 홈·챌린지 · 담당: ______ -->
## 04. 홈·챌린지 (카테고리·미션·체크인·복약)

- 담당: 홍시윤
- 관련 화면: D01~D07
- 관련 요구사항: REQ-009~013, REQ-024, REQ-028
- 우선순위: MVP (날씨 맞춤 기능은 추가)
- 관련 테이블: `user_categories`, `challenges`, `daily_challenges`, `checkins` 등
- 기준: 요구사항 정의서 v1.3 · ERD v1.3 · 와이어프레임

> **공통 확인 사항**
> - 카테고리 4개의 최종 명칭과 `category_code`는 확정 전입니다.
> - 개인화 추천 조건 및 미션 생성 방식은 팀 협의가 필요합니다.
> - 아래 JSON의 값은 개발 협의를 위한 예시(Mock Data)입니다.
> - ERD 컬럼과 일치 여부를 최종 확인해야 합니다.

### 12. 켜진 생활습관 카테고리 조회
- **Method / Endpoint:** `GET /api/v1/users/me/categories`
- **Description:** 로그인한 사용자가 활성화한 생활습관 카테고리 목록을 조회합니다.
- **인증:** 필요
- **Request Header:** `Authorization: Bearer {access_token}`
- **Request Parameter:** 없음
- **Request Body:** 없음

**Response Body (200 OK)**

```json
{
  "categories": [
    {
      "category_code": "diet",
      "enabled": true
    },
    {
      "category_code": "exercise",
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

**Status Code**

| 코드 | 설명 |
|---|---|
| 200 | 카테고리 조회 성공 |
| 401 | 인증 토큰 없음 또는 만료 |
| 500 | 서버 내부 오류 |

- **관련 테이블:** `user_categories`
- **관련 요구사항:** REQ-010
- **관련 화면:** D02

**비고**
- 카테고리 코드는 기존 API 초안의 예시를 유지했습니다.
- 현재 와이어프레임에는 식습관·움직임·수면·마음으로 표시되어 있어 최종 분류를 통일해야 합니다.
- 신규 사용자의 기본 활성화 상태를 정의해야 합니다.
- 활성화 상태와 AI 추천 우선순위를 별도로 관리할지 확인이 필요합니다.

### 13. 카테고리 켜기/끄기 저장
- **Method / Endpoint:** `PUT /api/v1/users/me/categories`
- **Description:** 사용자가 선택한 생활습관 카테고리의 활성화 상태를 저장합니다.
- **인증:** 필요
- **Request Header:**
  - `Content-Type: application/json`
  - `Authorization: Bearer {access_token}`
- **Request Parameter:** 없음

**Request Body**

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

**Response Body (200 OK)**

```json
{
  "updated": 2
}
```

**Status Code**

| 코드 | 설명 |
|---|---|
| 200 | 설정 저장 성공 |
| 400 | 유효하지 않은 카테고리 코드 또는 입력값 |
| 401 | 인증 토큰 없음 또는 만료 |
| 500 | 서버 내부 오류 |

- **관련 테이블:** `user_categories`
- **관련 요구사항:** REQ-010
- **관련 화면:** D02

**비고**
- 기존 API 초안의 요청·응답 구조를 유지했습니다.
- 요청에 포함된 카테고리만 변경할지, 전체 설정을 교체할지 결정해야 합니다.
- 카테고리 비활성화 시 이미 배정된 미션을 유지할지 확인이 필요합니다.
- 사용자 선택과 AI 추천 결과가 충돌할 경우 우선순위를 정해야 합니다.

### 14. 오늘의 미션 조회
- **Method / Endpoint:** `GET /api/v1/challenges/today`
- **Description:** 로그인한 사용자에게 해당 날짜에 배정된 생활습관 미션과 수행 상태를 조회합니다.
- **인증:** 필요
- **Request Header:** `Authorization: Bearer {access_token}`

**Request Parameter (Query)**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| date | string (YYYY-MM-DD) | N | 조회 날짜, 기본값은 오늘 |

**Response Body (200 OK)**

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
    },
    {
      "daily_challenge_id": 22,
      "challenge_id": 7,
      "category_code": "diet",
      "title": "저녁 식사 후 야식 피하기",
      "completed": true
    }
  ]
}
```

**Status Code**

| 코드 | 설명 |
|---|---|
| 200 | 오늘의 미션 조회 성공 |
| 400 | 날짜 형식 오류 |
| 401 | 인증 토큰 없음 또는 만료 |
| 500 | 서버 내부 오류 |

- **관련 테이블:** `daily_challenges`, `challenges`, `checkins`
- **관련 요구사항:** REQ-009, REQ-011
- **관련 화면:** D01, D03

**비고**
- 기존 API 초안의 응답 필드를 유지했습니다.
- 미션이 없는 경우 `missions: []`를 반환합니다.
- 하루 최대 미션 개수는 확정이 필요합니다.
- 같은 날짜에 여러 번 조회해도 미션이 중복 생성되지 않아야 합니다.
- 미션을 자동 배정할지, 추천 목록에서 사용자가 선택하도록 할지 결정해야 합니다.
- 미션 상세 설명·목표량·단위 등이 필요하다면 응답 필드 확장을 검토해야 합니다.

### 15. 미션·수면·기분·복약 체크인
- **Method / Endpoint:** `POST /api/v1/checkins`
- **Description:** 사용자의 일일 미션 수행 결과와 수면·기분·복약 기록을 저장합니다.
- **인증:** 필요
- **Request Header:**
  - `Content-Type: application/json`
  - `Authorization: Bearer {access_token}`
- **Request Parameter:** 없음

**Request Body**

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

**Response Body (201 Created)**

```json
{
  "checkin_id": 15,
  "completion_rate": 0.5,
  "created_at": "2026-11-18T21:00:00+09:00"
}
```

**Status Code**

| 코드 | 설명 |
|---|---|
| 201 | 체크인 저장 성공 |
| 400 | 입력값 또는 허용 범위 오류 |
| 401 | 인증 토큰 없음 또는 만료 |
| 404 | 존재하지 않는 미션 |
| 409 | 동일 날짜 체크인 중복 |
| 500 | 서버 내부 오류 |

- **관련 테이블:** `checkins`, `daily_challenges`
- **관련 요구사항:** REQ-012, REQ-013, REQ-024
- **관련 화면:** D01, D03, D04, D05

**비고**
- `mood_score` 허용 범위는 1~5로 가정했습니다.
- `completion_rate`는 해당 날짜에 배정된 미션 중 완료된 미션의 비율입니다.
- 수면·기분·복약 기록을 모두 필수 입력으로 받을 필요는 없습니다.
- 같은 날 체크인 수정이 가능하도록 별도 수정 API를 둘지 결정해야 합니다.
- 복약 기록은 여러 약물을 복용하는 사용자까지 고려하면 `medication_taken: true/false`만으로는 부족할 수 있습니다.
- 하나의 체크인 API로 모든 기록을 저장할지, 기능별로 분리할지 검토가 필요합니다.
- 체크인한 미션이 실제 해당 사용자에게 배정된 미션인지 검증해야 합니다.

#### ➕ 추가 검토 (뼈대·화면에는 있는데 초안에 없는 API)
- [ ] GET /api/v1/challenges/recommended — 맞춤 챌린지 추천 (D02, REQ-009 · MVP 반영 검토)
  - 사용자 문진 결과, 건강 상태, 활성화된 카테고리를 기반으로 챌린지 추천
  - 추천 기준(기진단 여부, 질환별 위험도, 생활습관 등) 확정 필요
  - 추천 결과를 DB에 저장할지, 요청 시 생성할지 결정 필요
  - 추천 목록 조회와 실제 미션 배정 방식 구분 필요
  
- [ ] GET /api/v1/weather/mission — 날씨 맞춤 미션 조정 (D06, REQ-024 · 추가)
  - 외부 날씨 API 연동 여부 및 지역정보 입력 방식 결정 필요
  - 날씨에 따른 대체 미션 추천 기준 확정 필요
  - 실제 미션 변경 또는 대체 미션 안내만 제공할지 결정 필요

#### 04 구역 ERD·와이어프레임 대조 결과 · 팀 확인 요청
| # | 내용 | 확인할 사람 |
|---|---|---|
| 1 | 카테고리 4개 명칭 및 `category_code` 불일치: API 예시(diet/exercise/sleep/smoking)와 와이어프레임(식습관/움직임/수면/마음) 통일 필요 | 기획 · 백엔드 |
| 2 | 사용자 카테고리 선택과 건강 상태 기반 추천의 우선순위 확정 필요 | 기획 · AI |
| 3 | 맞춤 챌린지 추천 API가 기존 38개 목록에 없음 → MVP 포함 여부 확인 | 팀장 · 백엔드 |
| 4 | 하루 미션 개수 및 자동 배정·사용자 선택 방식 확정 필요 | 기획 |
| 5 | 동일 날짜 체크인 재제출 시 409 반환 또는 PUT 수정 방식 결정 필요 | 백엔드 |
| 6 | 수면·기분·복약 기록을 단일 체크인 API로 처리할지 확인 필요 | 백엔드 · 프론트엔드 |
| 7 | 미션 상세 화면(D03)에 필요한 설명·목표량 등 응답 필드 및 상세 조회 API 검토 | 프론트엔드 · 백엔드 |
| 8 | 날씨 맞춤 미션의 실제 변경 여부 및 외부 API 연동 범위 확정 필요 | 기획 · 백엔드 |
| 9 | `user_categories`, `daily_challenges`, `checkins` 등 관련 테이블과 요청·응답 필드 일치 여부 확인 | 백엔드 |
<!-- 04 END -->

---

<!-- 05 START · AI 코치·케어 · 담당: ______ -->
## 05. AI 코치·케어 (코치·SOS·갱년기·감정 메모)

담당: ______ · 관련 화면: E01~E06

### 16. 흡연 욕구 SOS 기록
- Method / Endpoint: `POST /api/v1/sos`
- 인증: 필요
- Request Header: Content-Type: application/json / Authorization: Bearer {access_token}
- Request Parameter (Path / Query): -
- Request Body:

  ```json
  {
    "craving_level": 8,
    "memo": "식사 후 흡연 욕구"
  }
  ```
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "sos_id": 4,
    "guide_message": "잠시 심호흡을 해 볼까요?",
    "created_at": "2026-11-18T13:20:00+09:00"
  }
  ```
- Status Code: 성공: 201 Created / 400 craving_level 범위(1~10) 오류 / 401 토큰 없음·만료
- 관련 테이블 · REQ: sos_logs · REQ-016
- 우선순위: 추가

### 20. 오늘의 코치 메시지 (하루 1회 생성, 저장본 재사용)
- Method / Endpoint: `GET /api/v1/coach/today`
- 인증: 필요
- Request Header: Content-Type: application/json / Authorization: Bearer {access_token}
- Request Parameter (Path / Query): -
- Request Body: -
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "coach_message_id": 12,
    "date": "2026-11-18",
    "message": "어제보다 걸음 수가 늘었어요. 오늘도 가볍게 걸어 볼까요?",
    "sources": [
      {
        "title": "고혈압 생활습관 권고"
      }
    ],
    "safety_notice": null,
    "generated_at": "2026-11-18T07:00:00+09:00"
  }
  ```
- Status Code: 성공: 200 OK / 401 토큰 없음·만료 / 409 AI 처리 동의 없음 / 503 LLM 호출 실패(저장본 없을 때)
- 관련 테이블 · REQ: coach_messages · REQ-021, NFR-007
- 우선순위: MVP
- 비고: 근거 문서 부족 시 답 보류(“의료진과 상의” 안내) — v1.4 후보 REQ-021

### 21. AI 코치 실시간 대화 (SSE 스트리밍)
- Method / Endpoint: `POST /api/v1/coach/chat`
- 인증: 필요
- Request Header: Content-Type: application/json / Authorization: Bearer {access_token} / Accept: text/event-stream
- Request Parameter (Path / Query): -
- Request Body:

  ```json
  {
    "thread_id": "t-1",
    "message": "오늘 운동 뭐가 좋을까요?"
  }
  ```
- Response Body (성공 예시 = Mock Data):

  ```json
  Content-Type: text/event-stream
  
  event: token
  data: {"text":"가벼운 걷기부터"}
  
  event: done
  data: {"thread_id":"t-1","sources":[{"title":"운동 권고"}]}
  
  (위험 신호 감지 시) event: safety_alert
  data: {"message":"의료진 상담을 권해요"}
  ```
- Status Code: 성공: 200 OK (스트림) / 400 message 비어 있음 / 401 토큰 없음·만료 / 409 AI 처리 동의 없음 / 429 호출 한도 초과 / 503 LLM 호출 실패
- 관련 테이블 · REQ: NFR-002
- 우선순위: 추가
- 비고: thread_id는 사용자별 분리. LLM이 DB를 직접 조회하지 않고 백엔드 정해진 API로만 요약 전달

#### ➕ 추가 검토 (뼈대·화면에는 있는데 초안에 없는 API)
- [ ] POST·GET /api/v1/symptoms — 갱년기 증상 점수 (E04, REQ-015, symptom_scores)
- [ ] POST·GET /api/v1/mood-notes — 감정 메모 (E06, REQ-034, ERD 테이블 확인 필요)

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
    "coach_calls": 340
  }
  ```
- Status Code: 성공: 200 OK / 400 날짜 형식 오류 / 401 토큰 없음·만료 / 403 관리자 권한 없음
- 관련 테이블 · REQ: admin_logs · REQ-033, NFR-016
- 우선순위: MVP
- 비고: LLM 토큰·비용·지연은 39번 admin/llm-usage, 가입자 증감은 40번 admin/users/stats에서 조회

### 39. LLM 사용량 확인 (토큰·비용·지연·도구 호출, 기능별·모델별·기간별)
- Method / Endpoint: `GET /api/v1/admin/llm-usage`
- 인증: 관리자
- Request Header: Content-Type: application/json / Authorization: Bearer {admin_access_token}
- Request Parameter (Path / Query): from_date, to_date, group_by(day | week | model | feature, 기본 day), feature(선택: coach_today | coach_chat | prediction_explain | message_suggest)
- Request Body: -
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "period": {
      "from": "2026-11-01",
      "to": "2026-11-18"
    },
    "group_by": "feature",
    "totals": {
      "requests": 340,
      "input_tokens": 412000,
      "output_tokens": 98000,
      "total_tokens": 510000,
      "cost_usd": 12.4,
      "avg_ttft_ms": 820,
      "avg_latency_ms": 3100,
      "tool_calls": 510,
      "error_rate": 0.018
    },
    "items": [
      {
        "key": "coach_chat",
        "requests": 210,
        "total_tokens": 360000,
        "cost_usd": 8.9,
        "avg_ttft_ms": 900,
        "tool_calls": 420
      },
      {
        "key": "coach_today",
        "requests": 95,
        "total_tokens": 110000,
        "cost_usd": 2.6,
        "avg_ttft_ms": 700,
        "tool_calls": 60
      }
    ]
  }
  ```
- Status Code: 성공: 200 OK / 400 날짜 형식·group_by·feature 값 오류 / 401 토큰 없음·만료 / 403 관리자 권한 없음 / 500 사용량 수집(Langfuse) 조회 실패
- 관련 테이블 · REQ: admin_logs · REQ-033, NFR-006·010
- 우선순위: MVP
- 비고: 사용자 대화 원문·개인정보 없이 집계값만 반환. Langfuse 연동 방식(직접 조회 vs 자체 로그 테이블 저장)은 백엔드 확정 필요. 도구 호출·모델 호출 상한(NFR-010)은 v1.4 후보

### 40. 사용자 증감 현황 (신규 가입·탈퇴·순증감·활성 사용자)
- Method / Endpoint: `GET /api/v1/admin/users/stats`
- 인증: 관리자
- Request Header: Content-Type: application/json / Authorization: Bearer {admin_access_token}
- Request Parameter (Path / Query): from_date, to_date, interval(day | week | month, 기본 day)
- Request Body: -
- Response Body (성공 예시 = Mock Data):

  ```json
  {
    "period": {
      "from": "2026-11-01",
      "to": "2026-11-18"
    },
    "interval": "day",
    "summary": {
      "total_users": 520,
      "new_users": 48,
      "withdrawn_users": 6,
      "net_change": 42,
      "change_rate": 0.088,
      "active_users": 120
    },
    "series": [
      {
        "date": "2026-11-17",
        "new_users": 3,
        "withdrawn_users": 0,
        "net_change": 3,
        "total_users": 518
      },
      {
        "date": "2026-11-18",
        "new_users": 2,
        "withdrawn_users": 0,
        "net_change": 2,
        "total_users": 520
      }
    ]
  }
  ```
- Status Code: 성공: 200 OK / 400 날짜 형식·interval 값 오류 / 401 토큰 없음·만료 / 403 관리자 권한 없음
- 관련 테이블 · REQ: users · admin_logs · REQ-033, NFR-016
- 우선순위: MVP
- 비고: 개인 식별 정보 없이 집계 수치만 반환. 탈퇴 수치는 탈퇴 시 기록 삭제 정책(ERD 확인 질문)과 맞춰 집계 방식 결정 필요(예: 탈퇴 시점 카운터 별도 저장)

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
