"""위험 신호 안내 (REQ-022) · 검진 수치 기준 초과 안내 (REQ-005) · 키워드 검사.

- 전부 서버 규칙이에요. LLM을 쓰지 않고, 감정 메모 원문은 LLM에 보내지 않습니다 (NFR-017).
- 문구는 진단·처방처럼 읽히지 않게 "확인·상담 권유"로만 씁니다 (NFR-014).
"""
import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import CheckupRecord, Checkin, RiskPrediction, SafetyKeyword, now
from app.models.tables import iso

SEED_KEYWORDS = [("죽고 싶", "RISK_SIGNAL"), ("자살", "RISK_SIGNAL"), ("자해", "RISK_SIGNAL"), ("사라지고 싶", "RISK_SIGNAL"),
                 ("진단", "MEDICAL_BAN"), ("처방", "MEDICAL_BAN"), ("완치", "MEDICAL_BAN"), ("당장 병원", "FAMILY_BAN")]
# NFR-009 기준 (필드, 비교, 기준값, 이름)
CHECKUP_RULES = [("pressure_systolic", ">=", 140, "수축기 혈압"), ("pressure_diastolic", ">=", 90, "이완기 혈압"),
                 ("fasting_glucose", ">=", 126, "공복혈당"), ("hba1c", ">=", 6.5, "당화혈색소"),
                 ("total_cholesterol", ">=", 240, "총콜레스테롤"), ("ldl_cholesterol", ">=", 160, "LDL 콜레스테롤"),
                 ("triglycerides", ">=", 200, "중성지방"), ("hdl_cholesterol", "<", 40, "HDL 콜레스테롤")]
CHECKUP_FIELDS = [r[0] for r in CHECKUP_RULES]
CRISIS = {"type": "CRISIS", "level": "URGENT", "title": "혼자 견디지 않으셔도 돼요",
          "message": "지금 많이 힘드시다면 자살예방 상담전화 109(24시간)로 바로 이야기해 보세요. 가까운 사람이나 의료진에게 알리는 것도 도움이 됩니다."}


def seed_keywords(db: Session) -> None:
    if db.scalar(select(SafetyKeyword.id).limit(1)) is None:
        db.add_all(SafetyKeyword(keyword=k, kind=kind) for k, kind in SEED_KEYWORDS)
        db.commit()


def matches(db: Session, text: str | None, kind: str) -> bool:
    """글에 해당 종류의 키워드가 있는지. 어떤 단어였는지는 돌려주지 않아요."""
    if not text:
        return False
    seed_keywords(db)
    compact = text.replace(" ", "")
    return any(k.replace(" ", "") in compact for k in db.scalars(
        select(SafetyKeyword.keyword).where(SafetyKeyword.kind == kind, SafetyKeyword.is_active.is_(True))))


def checkup_out(rec: CheckupRecord) -> dict:
    exceeded = []
    for field, op, limit, label in CHECKUP_RULES:
        v = getattr(rec, field)
        if v is not None and (v >= limit if op == ">=" else v < limit):
            exceeded.append({"field": field, "label": label, "value": v, "reference": f"{'이상' if op == '>=' else '미만'} {limit}"})
    stale = bool(rec.checkup_date and (now().date() - rec.checkup_date).days > 365)
    return {"checkup_id": rec.id, "checkup_date": rec.checkup_date.isoformat() if rec.checkup_date else None,
            **{f: getattr(rec, f) for f in CHECKUP_FIELDS}, "exceeded": exceeded, "is_stale": stale,
            "guide": ("기준을 넘는 수치가 있어요. 가까운 시일에 의료진과 상의해 보세요." if exceeded else None),
            "stale_guide": "검진을 받은 지 1년이 넘었어요. 다시 검진을 받아 보세요." if stale else None,
            "notice": "검진 수치는 기준 초과 안내에만 쓰고, 위험 신호 예측에는 넣지 않아요.",
            "created_at": iso(rec.created_at)}


def latest_checkup(db: Session, user_id: int) -> CheckupRecord | None:
    return db.scalar(select(CheckupRecord).where(CheckupRecord.user_id == user_id).order_by(CheckupRecord.id.desc()))


def alerts(db: Session, user_id: int) -> list[dict]:
    """지금 보여 줄 안내 목록 (REQ-022 ①~④)."""
    out, today = [], now().date()
    memo = db.scalar(select(Checkin.memo).where(Checkin.user_id == user_id, Checkin.checkin_date == today))
    if matches(db, memo, "RISK_SIGNAL"):
        out.append(CRISIS)
    last = db.scalar(select(RiskPrediction.prediction_date).where(RiskPrediction.user_id == user_id)
                     .order_by(RiskPrediction.prediction_date.desc()))
    if last and db.scalar(select(RiskPrediction.id).where(RiskPrediction.user_id == user_id, RiskPrediction.prediction_date == last,
                                                          RiskPrediction.risk_level == "HIGH")):
        out.append({"type": "HIGH_RISK", "level": "CARE", "title": "의료진과 상의해 보세요",
                    "message": "위험 신호가 높게 나온 항목이 있어요. 진단은 아니지만, 검진이나 진료로 확인해 보시길 권해요."})
    rec = latest_checkup(db, user_id)
    if rec and checkup_out(rec)["exceeded"]:
        out.append({"type": "CHECKUP_EXCEEDED", "level": "CARE", "title": "검진 수치를 확인해 보세요",
                    "message": "입력하신 검진 수치 중 기준을 넘는 항목이 있어요. 의료진과 상의해 보세요."})
    moods = list(db.scalars(select(Checkin.mood).where(Checkin.user_id == user_id, Checkin.mood.is_not(None),
                                                       Checkin.checkin_date > today - dt.timedelta(days=7))))
    if sum(m <= 2 for m in moods) >= 5:
        out.append({"type": "LOW_MOOD", "level": "CARE", "title": "요즘 마음이 많이 지치셨나요",
                    "message": "기분이 좋지 않은 날이 이어지고 있어요. 전문 상담을 받아 보시는 것도 좋아요. 정신건강 상담전화 1577-0199."})
    return out
