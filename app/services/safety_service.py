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
# 검진 수치 안내 기준 (필드, 이름, 단위, 방향, 주의 시작, 기준값)
# - 기준값(limit)은 NFR-009의 질환 판정 수치예요.
# - 주의(caution)는 "정상보다 높지만 기준은 넘지 않은" 구간이에요. 널리 쓰이는 참고 수치로 넣었고,
#   기관마다 다를 수 있어서 팀·멘토 확인이 필요해요. (진단이 아니라 "확인해 보세요" 안내에만 사용)
CHECKUP_RULES = [("pressure_systolic", "수축기 혈압", "mmHg", "high", 120, 140),
                 ("pressure_diastolic", "이완기 혈압", "mmHg", "high", 80, 90),
                 ("fasting_glucose", "공복혈당", "mg/dL", "high", 100, 126),
                 ("hba1c", "당화혈색소", "%", "high", 5.7, 6.5),
                 ("total_cholesterol", "총콜레스테롤", "mg/dL", "high", 200, 240),
                 ("ldl_cholesterol", "LDL 콜레스테롤", "mg/dL", "high", 130, 160),
                 ("triglycerides", "중성지방", "mg/dL", "high", 150, 200),
                 ("hdl_cholesterol", "HDL 콜레스테롤", "mg/dL", "low", 50, 40)]
CHECKUP_FIELDS = [r[0] for r in CHECKUP_RULES]


def _status(value, direction: str, caution, limit) -> str:
    if direction == "high":
        return "EXCEEDED" if value >= limit else "CAUTION" if value >= caution else "NORMAL"
    return "EXCEEDED" if value < limit else "CAUTION" if value < caution else "NORMAL"


def _just_below(limit):
    """기준 바로 아래 값. 주의 구간 끝을 표시할 때 써요 (140 → 139, 6.5 → 6.4)."""
    return limit - 1 if isinstance(limit, int) else round(limit - 0.1, 1)


def _reference(direction: str, caution, limit) -> str:
    if direction == "high":
        return f"정상 {caution} 미만 · 주의 {caution}~{_just_below(limit)} · 기준 초과 {limit} 이상"
    return f"정상 {caution} 이상 · 주의 {limit}~{_just_below(caution)} · 기준 초과 {limit} 미만"
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
    """입력한 값마다 상태(정상·주의·기준 초과)와 기준을 함께 돌려줘요.

    화면에서 "왜 기준 초과가 아닌지"를 알 수 있게, 넘지 않은 값도 기준과 같이 보여 줍니다.
    """
    items, exceeded, caution = [], [], []
    for field, label, unit, direction, caution_from, limit in CHECKUP_RULES:
        v = getattr(rec, field)
        if v is None:
            continue
        status = _status(v, direction, caution_from, limit)
        item = {"field": field, "label": label, "value": v, "unit": unit, "status": status,
                "reference": _reference(direction, caution_from, limit)}
        items.append(item)
        (exceeded if status == "EXCEEDED" else caution if status == "CAUTION" else []).append(item)
    stale = bool(rec.checkup_date and (now().date() - rec.checkup_date).days > 365)
    return {"checkup_id": rec.id, "checkup_date": rec.checkup_date.isoformat() if rec.checkup_date else None,
            **{f: getattr(rec, f) for f in CHECKUP_FIELDS}, "items": items, "exceeded": exceeded, "caution": caution,
            "is_stale": stale,
            "guide": ("기준을 넘는 수치가 있어요. 가까운 시일에 의료진과 상의해 보세요." if exceeded else None),
            "caution_guide": ("기준을 넘지는 않았지만 주의 범위인 수치가 있어요. 생활습관 관리를 이어가 주세요."
                              if caution and not exceeded else None),
            "stale_guide": "검진을 받은 지 1년이 넘었어요. 다시 검진을 받아 보세요." if stale else None,
            "notice": "기준은 기관에 따라 다를 수 있어요. 검진 수치는 안내에만 쓰고 위험 신호 예측에는 넣지 않아요.",
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
