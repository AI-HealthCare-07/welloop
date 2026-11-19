"""DB 테이블 (ERD v1.3 컬럼명 기준, 데모에 필요한 테이블만).

ERD와 다른 점 (ERD v1.4 반영 요청 대상):
- risk_predictions.reason, overall_score, overall_grade 추가 (03 대조 결과 2·3)
"""
import datetime as dt

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


KST = dt.timezone(dt.timedelta(hours=9))


def now() -> dt.datetime:
    return dt.datetime.now(KST)


def iso(value: dt.datetime | None) -> str | None:
    """API 응답용 시각 문자열. DB에서 시간대 없이 읽힌 값도 +09:00을 붙여요 (공통 규칙: ISO 8601 +09:00)."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=KST)
    return value.astimezone(KST).isoformat(timespec="seconds")


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    birth_date: Mapped[dt.date] = mapped_column(Date)
    gender: Mapped[str] = mapped_column(String)  # MALE / FEMALE
    role: Mapped[str] = mapped_column(String, default="USER")
    font_size: Mapped[str] = mapped_column(String, default="NORMAL")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now)


class Consent(Base):
    __tablename__ = "consents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    consent_type: Mapped[str] = mapped_column(String)  # HEALTH_DATA / FAMILY_SHARE / NOTIFICATION
    agreed: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now)


class Questionnaire(Base):
    __tablename__ = "questionnaires"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    height: Mapped[float | None] = mapped_column(Float)
    weight: Mapped[float | None] = mapped_column(Float)
    waist_size: Mapped[float | None] = mapped_column(Float)
    htn_diagnosed: Mapped[bool | None] = mapped_column(Boolean)
    htn_medication: Mapped[bool | None] = mapped_column(Boolean)
    dm_diagnosed: Mapped[bool | None] = mapped_column(Boolean)
    dm_medication: Mapped[bool | None] = mapped_column(Boolean)
    dl_diagnosed: Mapped[bool | None] = mapped_column(Boolean)
    dl_medication: Mapped[bool | None] = mapped_column(Boolean)
    smoking_status: Mapped[str | None] = mapped_column(String)
    quit_intention: Mapped[bool | None] = mapped_column(Boolean)
    drinking_days_per_week: Mapped[int | None] = mapped_column(Integer)
    drinks_per_occasion: Mapped[int | None] = mapped_column(Integer)
    activity_days_per_week: Mapped[int | None] = mapped_column(Integer)
    activity_minutes_per_day: Mapped[int | None] = mapped_column(Integer)
    strength_days_per_week: Mapped[int | None] = mapped_column(Integer)
    salty_food_freq: Mapped[int | None] = mapped_column(Integer)
    sweet_food_freq: Mapped[int | None] = mapped_column(Integer)
    refined_carb_freq: Mapped[int | None] = mapped_column(Integer)
    veg_freq: Mapped[int | None] = mapped_column(Integer)
    fruit_freq: Mapped[int | None] = mapped_column(Integer)
    breakfast_freq: Mapped[int | None] = mapped_column(Integer)
    sleep_hours: Mapped[float | None] = mapped_column(Float)
    sleep_trouble: Mapped[bool | None] = mapped_column(Boolean)
    family_htn: Mapped[str | None] = mapped_column(String)
    family_dm: Mapped[str | None] = mapped_column(String)
    family_dl: Mapped[str | None] = mapped_column(String)
    exercise_restricted: Mapped[bool | None] = mapped_column(Boolean)
    discomfort_symptoms: Mapped[str | None] = mapped_column(String)
    improvement_goal: Mapped[str | None] = mapped_column(String)
    menopause_status: Mapped[str | None] = mapped_column(String)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_recheck: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now)


class HealthLog(Base):
    __tablename__ = "health_logs"
    __table_args__ = (UniqueConstraint("user_id", "log_date"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    log_date: Mapped[dt.date] = mapped_column(Date)
    weight: Mapped[float | None] = mapped_column(Float)
    waist_size: Mapped[float | None] = mapped_column(Float)
    pressure_systolic: Mapped[int | None] = mapped_column(Integer)
    pressure_diastolic: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now)


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"
    __table_args__ = (UniqueConstraint("user_id", "prediction_date", "disease_type"),)  # 하루 1회차, 질환당 1행
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    questionnaire_id: Mapped[int] = mapped_column(ForeignKey("questionnaires.id"))
    prediction_date: Mapped[dt.date] = mapped_column(Date, index=True)
    disease_type: Mapped[str] = mapped_column(String)
    model_version: Mapped[str] = mapped_column(String)
    risk_score: Mapped[float | None] = mapped_column(Float)
    risk_level: Mapped[str | None] = mapped_column(String)
    is_managed: Mapped[bool] = mapped_column(Boolean, default=False)
    major_factor1: Mapped[str | None] = mapped_column(String)
    major_factor2: Mapped[str | None] = mapped_column(String)
    major_factor3: Mapped[str | None] = mapped_column(String)
    input_snapshot: Mapped[dict | None] = mapped_column(JSON)
    reason: Mapped[str] = mapped_column(String, default="INITIAL")  # ERD에 없음
    overall_score: Mapped[int | None] = mapped_column(Integer)  # ERD에 없음
    overall_grade: Mapped[str | None] = mapped_column(String)  # ERD에 없음
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now)


class Challenge(Base):
    __tablename__ = "challenges"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String)  # DIET / ACTIVITY / SLEEP_REST / SMOKE_DRINK
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    intensity: Mapped[str] = mapped_column(String, default="LIGHT")  # LIGHT / MODERATE / HARD
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class DailyChallenge(Base):
    __tablename__ = "daily_challenges"
    __table_args__ = (UniqueConstraint("user_id", "assigned_date", "challenge_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"))
    assigned_date: Mapped[dt.date] = mapped_column(Date)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class Checkin(Base):
    __tablename__ = "checkins"
    __table_args__ = (UniqueConstraint("user_id", "checkin_date"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    checkin_date: Mapped[dt.date] = mapped_column(Date)
    sleep_hours: Mapped[float | None] = mapped_column(Float)
    mood: Mapped[int | None] = mapped_column(Integer)
    refreshed: Mapped[int | None] = mapped_column(Integer)
    stress: Mapped[int | None] = mapped_column(Integer)
    memo: Mapped[str | None] = mapped_column(String)
    medication_taken: Mapped[bool | None] = mapped_column(Boolean)  # ERD에 없음 (03 대조 7 · 04 대조 9)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now)


class CoachMessage(Base):
    __tablename__ = "coach_messages"
    __table_args__ = (UniqueConstraint("user_id", "message_date"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    message_date: Mapped[dt.date] = mapped_column(Date)
    content: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)  # TEMPLATE / LLM
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now)


class CheckupRecord(Base):
    __tablename__ = "checkup_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    checkup_date: Mapped[dt.date | None] = mapped_column(Date)
    pressure_systolic: Mapped[int | None] = mapped_column(Integer)
    pressure_diastolic: Mapped[int | None] = mapped_column(Integer)
    fasting_glucose: Mapped[int | None] = mapped_column(Integer)
    hba1c: Mapped[float | None] = mapped_column(Float)
    total_cholesterol: Mapped[int | None] = mapped_column(Integer)
    ldl_cholesterol: Mapped[int | None] = mapped_column(Integer)
    hdl_cholesterol: Mapped[int | None] = mapped_column(Integer)
    triglycerides: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now)


class SafetyKeyword(Base):
    __tablename__ = "safety_keywords"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword: Mapped[str] = mapped_column(String, unique=True)
    kind: Mapped[str] = mapped_column(String)  # RISK_SIGNAL(위험 신호) / MEDICAL_BAN(의료 표현 금지) / FAMILY_BAN(가족 문구 금지)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_by: Mapped[int | None] = mapped_column(Integer)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), default=now)


class RiskThreshold(Base):
    __tablename__ = "risk_thresholds"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    disease_type: Mapped[str] = mapped_column(String, unique=True)
    warning_from: Mapped[float] = mapped_column(Float)
    high_from: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String, default="")
    updated_by: Mapped[int | None] = mapped_column(Integer)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), default=now)


class AdminLog(Base):
    __tablename__ = "admin_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String)
    target: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=now)
