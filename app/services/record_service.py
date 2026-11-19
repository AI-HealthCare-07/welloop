"""03 구역: 건강 수치 기록 · 대시보드 · 관리 평가 요약."""
import datetime as dt

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import api_error
from app.models.tables import Checkin, DailyChallenge, HealthLog, RiskPrediction, User, now
from app.services import prediction_service as pred
from app.models.tables import iso

LOG_FIELDS = ("weight", "waist_size", "pressure_systolic", "pressure_diastolic")
DISEASE_LABELS = {"HYPERTENSION": "고혈압", "DIABETES": "당뇨", "DYSLIPIDEMIA": "이상지질혈증"}
TRENDS = [("weight", "체중", "kg"), ("waist_size", "허리둘레", "cm"), ("pressure_systolic", "수축기 혈압", "mmHg")]


def log_out(log: HealthLog, recalculated: bool | None = None) -> dict:
    out = {"health_log_id": log.id, "log_date": log.log_date.isoformat(), **{f: getattr(log, f) for f in LOG_FIELDS},
           "created_at": iso(log.created_at)}
    if recalculated is not None:
        out["recalculated"] = recalculated
    return out


def _check(values: dict) -> None:
    if all(v is None for v in values.values()):
        raise api_error(400, "VALIDATION_ERROR", "기록할 수치가 하나는 있어야 해요")
    if (values.get("pressure_systolic") is None) != (values.get("pressure_diastolic") is None):
        raise api_error(400, "VALIDATION_ERROR", "혈압은 수축기·이완기를 함께 입력해 주세요")


def save_log(db: Session, user: User, body) -> tuple[dict, bool]:
    """하루 1행. 같은 날 다시 보내면 보낸 항목만 덮어써요. 체중·허리둘레가 바뀌면 재계산(하루 최대 1회)."""
    values = {f: getattr(body, f) for f in LOG_FIELDS}
    _check(values)
    date = body.log_date or now().date()
    if date > now().date():
        raise api_error(400, "VALIDATION_ERROR", "미래 날짜로는 기록할 수 없어요")
    find = select(HealthLog).where(HealthLog.user_id == user.user_id, HealthLog.log_date == date)
    log = db.scalar(find)
    created = log is None
    if created:
        log = HealthLog(user_id=user.user_id, log_date=date)
        db.add(log)
        try:
            db.flush()
        except IntegrityError:  # 같은 순간에 다른 요청이 먼저 만듦 → 그 기록을 고침
            db.rollback()
            log, created = db.scalar(find), False
    body_changed = any(values[f] is not None and values[f] != getattr(log, f) for f in ("weight", "waist_size"))
    for f, v in values.items():
        if v is not None:
            setattr(log, f, v)
    db.commit()
    recalculated = pred.recalculate(db, user, "HEALTH_LOG") if body_changed and date == now().date() else False
    return log_out(log, recalculated), created


def get_own_log(db: Session, user: User, log_id: int) -> HealthLog:
    log = db.get(HealthLog, log_id)
    if log is None:
        raise api_error(404, "NOT_FOUND", "기록이 없어요")
    if log.user_id != user.user_id:
        raise api_error(403, "FORBIDDEN", "내 기록이 아니에요")
    return log


def _since(period: str) -> dt.date | None:
    days = {"1m": 30, "3m": 90, "all": None}[period]
    return now().date() - dt.timedelta(days=days) if days else None


def list_logs(db: Session, user_id: int, period: str, page: int, size: int) -> dict:
    stmt = select(HealthLog).where(HealthLog.user_id == user_id)
    if _since(period):
        stmt = stmt.where(HealthLog.log_date >= _since(period))
    rows = list(db.scalars(stmt.order_by(HealthLog.log_date.desc())))
    return {"items": [log_out(r) for r in rows[(page - 1) * size: page * size]], "total": len(rows), "page": page, "size": size}


def dashboard(db: Session, user_id: int, period: str) -> dict:
    """No 19 (C04): 위험 점수 추이 + 건강 수치 추이. 데이터가 없으면 빈 배열(화면은 빈 상태 표시)."""
    since = _since(period)
    p = select(RiskPrediction).where(RiskPrediction.user_id == user_id, RiskPrediction.overall_score.is_not(None))
    h = select(HealthLog).where(HealthLog.user_id == user_id)
    if since:
        p, h = p.where(RiskPrediction.prediction_date >= since), h.where(HealthLog.log_date >= since)
    scores: dict[dt.date, int] = {}
    for r in db.scalars(p.order_by(RiskPrediction.prediction_date)):
        scores.setdefault(r.prediction_date, r.overall_score)
    logs = list(db.scalars(h.order_by(HealthLog.log_date)))
    trends = []
    for field, label, unit in TRENDS:
        points = [{"date": g.log_date.isoformat(), "value": getattr(g, field)} for g in logs if getattr(g, field) is not None]
        if points:
            trends.append({"metric": field, "label": label, "unit": unit, "points": points})
    return {"period": period,
            "risk_score_trend": {"score_max": 100, "points": [{"date": d.isoformat(), "score": s} for d, s in scores.items()]},
            "health_trends": trends,
            "notice": "서로 다른 지표는 분리해 표시합니다. 변화가 치료 효과를 뜻하지 않습니다."}


def management_summary(db: Session, user_id: int) -> dict:
    """No 19-1 (C02): 관리 중인 질환의 이번 주 생활 관리 현황. 예측 점수는 주지 않아요."""
    last = pred.latest_date(db, user_id)
    managed = [r.disease_type for r in pred._rows(db, user_id, last) if r.is_managed] if last else []
    if not managed:
        raise api_error(404, "NOT_FOUND", "관리 중인 질환이 없어요")
    today = now().date()
    start = today - dt.timedelta(days=today.weekday())
    end = start + dt.timedelta(days=6)
    assigned = list(db.scalars(select(DailyChallenge).where(DailyChallenge.user_id == user_id,
                                                           DailyChallenge.assigned_date.between(start, end))))
    done = sum(d.is_completed for d in assigned)
    bp = db.scalar(select(HealthLog).where(HealthLog.user_id == user_id, HealthLog.pressure_systolic.is_not(None))
                   .order_by(HealthLog.log_date.desc()))
    med_days = len(list(db.scalars(select(Checkin.id).where(Checkin.user_id == user_id, Checkin.medication_taken.is_(True),
                                                            Checkin.checkin_date.between(start, end)))))
    latest_log = {"log_date": bp.log_date.isoformat(), "pressure_systolic": bp.pressure_systolic,
                  "pressure_diastolic": bp.pressure_diastolic} if bp else None
    return {
        "week_start": start.isoformat(), "week_end": end.isoformat(),
        "completion": {"rate": round(done / len(assigned), 2) if assigned else 0.0,
                       "planned_count": len(assigned), "completed_count": done},
        "managed_items": [{"disease_type": d, "label": DISEASE_LABELS[d],
                           "latest_log": latest_log if d == "HYPERTENSION" else None,
                           "medication_check": {"checked_days": med_days, "total_days": 7}} for d in managed],
        "suggestions": ["같은 시간에 기록해 보세요.", "처방약 변경·중단은 반드시 의료진과 상의하세요."],
        "disclaimer": "이 평가는 생활 관리 요약이며 질환의 호전이나 치료 효과를 판정하지 않습니다.",
    }
