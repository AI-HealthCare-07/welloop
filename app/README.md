# WELLOOP 데모 실행

문진 → 위험 신호 → 미션·체크인 → 기록 → 대시보드 → 재계산까지 실제 DB로 동작하는 데모예요.

```bash
# 레포 루트에서
pip install -r app/requirements.txt -r ai_worker/risk_model/requirements.txt
python -m app.seed_demo            # (선택) 4주치 예시 기록이 있는 데모 계정 만들기. 비밀번호가 출력돼요
uvicorn app.main:app --reload      # 화면 http://localhost:8000 · API 문서 http://localhost:8000/docs
python -m pytest app/tests ai_worker/risk_model/tests -q
```

관리자 화면: `python -m app.create_admin admin@example.com` 으로 계정을 만든 뒤 http://localhost:8000/admin.html

- DB: 기본은 `data/welloop_demo.db`(SQLite, git 제외). `DATABASE_URL`로 바꿀 수 있어요.
- `JWT_SECRET`을 `.env`에 두지 않으면 서버를 켤 때마다 새로 만들어져 로그인이 풀려요.
- 초기화: `data/welloop_demo.db` 파일을 지우면 됩니다.

## 데모에서 알아 둘 것
- **위험 점수는 합성 데이터 모델(`risk-v0.0-synth`)이 낸 값이라 의미가 없어요.** 화면에 데모 표시가 나옵니다.
- 위험 단계 경계값 기본값(15% / 35%)과 등급 문구는 임시값이에요. 경계값은 관리자 화면에서 질환별로 바꿀 수 있어요.
- 위험 신호 안내(높음 단계 · 검진 수치 기준 초과 · 기분 저하 7일 중 5일 · 메모의 위험 표현)는 서버 규칙이에요. 메모는 LLM에 보내지 않아요.
- 코치 메시지는 고정 문구예요. LLM 연결 자리는 `challenge_service.coach_today`에 있어요.
- 주 1회 수면 재계산은 함수(`prediction_service.weekly_sleep_recalculation`)만 있고 스케줄러는 아직 없어요.
- 아직 없는 것: 함께 관리, SOS, 갱년기 기록, 토큰 재발급, 실제 LLM 연결, Docker·배포
