"""데모 계정과 4주치 예시 기록을 만들어요 (추이 화면 확인용, 전부 지어낸 값).

실행: python -m app.seed_demo
- 계정: demo@welloop.local / 비밀번호는 환경변수 DEMO_PASSWORD, 없으면 새로 만들어 화면에 출력
- 이미 있으면 아무것도 하지 않아요.
"""
import datetime as dt
import os
import secrets

from sqlalchemy import select

from app.core.db import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.tables import Checkin, Consent, DailyChallenge, HealthLog, Questionnaire, RiskPrediction, User, now
from app.services import challenge_service, prediction_service

EMAIL = "demo@welloop.local"


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == EMAIL)):
            print("데모 계정이 이미 있어요:", EMAIL)
            return
        password = os.environ.get("DEMO_PASSWORD") or secrets.token_urlsafe(9)
        user = User(email=EMAIL, password=hash_password(password), name="김온유", birth_date=dt.date(1974, 5, 20), gender="FEMALE")
        db.add(user)
        db.commit()
        db.add(Consent(user_id=user.user_id, consent_type="HEALTH_DATA", agreed=True))
        q = Questionnaire(user_id=user.user_id, height=162, weight=66, waist_size=88, smoking_status="NEVER",
                          drinking_days_per_week=1, drinks_per_occasion=2, activity_days_per_week=1, activity_minutes_per_day=20,
                          veg_freq=5, breakfast_freq=4, sleep_hours=6.0, sleep_trouble=True, family_dm="YES", family_htn="UNKNOWN",
                          family_dl="NO", menopause_status="PERI", htn_diagnosed=True, htn_medication=True, is_completed=True)
        db.add(q)
        db.commit()

        today = now().date()
        for back in range(13, 0, -1):  # 지난 13일 미션·체크인 (오늘은 직접 해 보도록 비워 둠)
            day = today - dt.timedelta(days=back)
            challenge_service.today_missions(db, user, day)
            for i, d in enumerate(db.scalars(select(DailyChallenge).where(DailyChallenge.user_id == user.user_id,
                                                                         DailyChallenge.assigned_date == day))):
                d.is_completed = (back + i) % 3 != 0
            db.add(Checkin(user_id=user.user_id, checkin_date=day, sleep_hours=6.5 + (back % 3) * 0.5, mood=3 + back % 2,
                           medication_taken=back % 5 != 0))
        db.commit()

        steps = [(21, 66.0, 88.0, 134, 86, "INITIAL"), (14, 65.2, 87.0, 132, 84, "HEALTH_LOG"),
                 (7, 64.5, 86.0, 130, 84, "HEALTH_LOG"), (0, 63.8, 85.0, 128, 82, "HEALTH_LOG")]
        for back, weight, waist, sys, dia, reason in steps:
            day = today - dt.timedelta(days=back)
            db.add(HealthLog(user_id=user.user_id, log_date=day, weight=weight, waist_size=waist,
                             pressure_systolic=sys, pressure_diastolic=dia))
            db.commit()
            prediction_service.run_prediction(db, user, q.id, reason)
            if back:  # '하루 최대 1회' 규칙 때문에, 방금 만든 결과를 그 주 날짜로 옮김
                for r in db.scalars(select(RiskPrediction).where(RiskPrediction.user_id == user.user_id,
                                                                 RiskPrediction.prediction_date == today)):
                    r.prediction_date = day
                db.commit()
        print(f"데모 계정을 만들었어요 → 이메일 {EMAIL} / 비밀번호 {password}")
        print("고혈압 관리 중 + 당뇨·이상지질혈증 예측 대상인 사용자예요. 수치는 전부 예시입니다.")


if __name__ == "__main__":
    main()
