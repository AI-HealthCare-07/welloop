"""요청 형식. 필드는 snake_case · ERD 컬럼명 · ERD Enum (API 명세서 공통 규칙)."""
import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field

YesNoUnknown = Literal["YES", "NO", "UNKNOWN"]


class SignupRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=72)
    name: str = Field(min_length=1, max_length=50)
    birth_date: dt.date
    gender: Literal["MALE", "FEMALE"]
    terms_agreed: bool
    privacy_agreed: bool


class LoginRequest(BaseModel):
    email: str
    password: str


class ConsentRequest(BaseModel):
    consent_type: Literal["HEALTH_DATA", "FAMILY_SHARE", "NOTIFICATION"]
    agreed: bool


class QuestionnaireRequest(BaseModel):
    height: float | None = Field(None, ge=100, le=220)
    weight: float | None = Field(None, ge=20, le=250)
    waist_size: float | None = Field(None, ge=40, le=200)
    htn_diagnosed: bool | None = None
    htn_medication: bool | None = None
    dm_diagnosed: bool | None = None
    dm_medication: bool | None = None
    dl_diagnosed: bool | None = None
    dl_medication: bool | None = None
    smoking_status: Literal["NEVER", "FORMER", "CURRENT"] | None = None
    quit_intention: bool | None = None
    drinking_days_per_week: int | None = Field(None, ge=0, le=7)
    drinks_per_occasion: int | None = Field(None, ge=0, le=30)
    activity_days_per_week: int | None = Field(None, ge=0, le=7)
    activity_minutes_per_day: int | None = Field(None, ge=0, le=600)
    strength_days_per_week: int | None = Field(None, ge=0, le=7)
    salty_food_freq: int | None = Field(None, ge=0, le=21)
    sweet_food_freq: int | None = Field(None, ge=0, le=21)
    refined_carb_freq: int | None = Field(None, ge=0, le=21)
    veg_freq: int | None = Field(None, ge=0, le=21)
    fruit_freq: int | None = Field(None, ge=0, le=21)
    breakfast_freq: int | None = Field(None, ge=0, le=7)
    sleep_hours: float | None = Field(None, ge=0, le=24)
    sleep_trouble: bool | None = None
    family_htn: YesNoUnknown | None = None
    family_dm: YesNoUnknown | None = None
    family_dl: YesNoUnknown | None = None
    exercise_restricted: bool | None = None
    discomfort_symptoms: str | None = Field(None, max_length=200)
    improvement_goal: str | None = Field(None, max_length=200)
    menopause_status: Literal["PRE", "PERI", "POST"] | None = None
    is_completed: bool = True
    is_recheck: bool = False


class PredictionRequest(BaseModel):
    questionnaire_id: int


class CheckinRequest(BaseModel):
    checkin_date: dt.date | None = None
    completed_daily_challenge_ids: list[int] = []
    sleep_hours: float | None = Field(None, ge=0, le=24)
    mood: int | None = Field(None, ge=1, le=5)
    refreshed: int | None = Field(None, ge=1, le=5)
    stress: int | None = Field(None, ge=1, le=5)
    memo: str | None = Field(None, max_length=500)
    medication_taken: bool | None = None


class HealthLogRequest(BaseModel):
    log_date: dt.date | None = None
    weight: float | None = Field(None, ge=20, le=250)
    waist_size: float | None = Field(None, ge=40, le=200)
    pressure_systolic: int | None = Field(None, ge=60, le=260)
    pressure_diastolic: int | None = Field(None, ge=30, le=160)


class SimulateRequest(BaseModel):
    changes: dict


class CheckupRequest(BaseModel):
    checkup_date: dt.date | None = None
    pressure_systolic: int | None = Field(None, ge=60, le=260)
    pressure_diastolic: int | None = Field(None, ge=30, le=160)
    fasting_glucose: int | None = Field(None, ge=30, le=600)
    hba1c: float | None = Field(None, ge=3, le=20)
    total_cholesterol: int | None = Field(None, ge=50, le=600)
    ldl_cholesterol: int | None = Field(None, ge=10, le=400)
    hdl_cholesterol: int | None = Field(None, ge=5, le=200)
    triglycerides: int | None = Field(None, ge=10, le=2000)


class ChallengeAdminRequest(BaseModel):
    category: Literal["DIET", "ACTIVITY", "SLEEP_REST", "SMOKE_DRINK"]
    title: str = Field(min_length=1, max_length=60)
    description: str = Field("", max_length=200)
    intensity: Literal["LIGHT", "MODERATE", "HARD"] = "LIGHT"
    is_active: bool = True


class KeywordRequest(BaseModel):
    keyword: str = Field(min_length=1, max_length=40)
    kind: Literal["RISK_SIGNAL", "MEDICAL_BAN", "FAMILY_BAN"]
    is_active: bool = True


class ThresholdRequest(BaseModel):
    warning_from: float = Field(gt=0, lt=1)
    high_from: float = Field(gt=0, lt=1)
