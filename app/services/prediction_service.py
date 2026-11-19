"""위험 신호 예측 서비스 계층 (API 명세서 03 구역 공통 규칙).

- 예측 입력 = 최근 문진 + health_logs 최신 체중·허리둘레 (+ 수면 체크인 평균: 체크인 구현 후 연결)
- 진단·복약 중인 질환은 예측하지 않고 is_managed 처리
- 위험 단계·종합 점수는 여기서 계산 (모델은 질환별 점수만 제공)
"""
import datetime as dt

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_worker.tasks.risk import RiskInputError, predict_risk
from app.core.config import DEFAULT_THRESHOLDS, DISCLAIMER, GRADE_LABELS
from app.core.security import api_error
from app.models.tables import Checkin, Consent, HealthLog, Questionnaire, RiskPrediction, RiskThreshold, User, now
from app.models.tables import iso

DISEASE_COLUMNS = {"HYPERTENSION": "htn", "DIABETES": "dm", "DYSLIPIDEMIA": "dl"}
LEVEL_ORDER = {"LOW": 0, "WARNING": 1, "HIGH": 2}
MODEL_FIELDS = ["height", "weight", "waist_size", "smoking_status", "drinking_days_per_week", "drinks_per_occasion",
                "activity_days_per_week", "activity_minutes_per_day", "strength_days_per_week", "veg_freq",
                "fruit_freq", "breakfast_freq", "sleep_hours", "family_htn", "family_dm", "family_dl",
                "menopause_status"]
FACTOR_LABELS = {
    "age": "나이", "gender": "성별", "weight": "체중(체질량지수)", "waist_size": "허리둘레",
    "smoking_status": "흡연", "drinking_days_per_week": "음주 빈도", "drinks_per_occasion": "1회 음주량",
    "activity_days_per_week": "신체활동 부족", "activity_minutes_per_day": "신체활동 시간",
    "strength_days_per_week": "근력운동", "veg_freq": "채소 섭취", "fruit_freq": "과일 섭취",
    "breakfast_freq": "아침식사", "sleep_hours": "수면 시간", "family_htn": "가족력(고혈압)",
    "family_dm": "가족력(당뇨)", "family_dl": "가족력(이상지질혈증)", "menopause_status": "폐경 상태",
}
FAMILY_FIELD = {"HYPERTENSION": "family_htn", "DIABETES": "family_dm", "DYSLIPIDEMIA": "family_dl"}
REASON_LABELS = {"INITIAL": "첫 문진 결과", "RECHECK": "재문진", "HEALTH_LOG": "체중 기록 반영", "SLEEP_CHECKIN": "수면 기록 반영"}


def get_thresholds(db: Session) -> dict[str, tuple[float, float]]:
    """질환별 (주의 시작, 높음 시작). 관리자가 risk_thresholds에서 바꿀 수 있고, 없으면 임시 기본값."""
    default = (DEFAULT_THRESHOLDS["warning_from"], DEFAULT_THRESHOLDS["high_from"])
    saved = {t.disease_type: (t.warning_from, t.high_from) for t in db.scalars(select(RiskThreshold))}
    return {d: saved.get(d, default) for d in DISEASE_COLUMNS}


def risk_level(score: float, th: tuple[float, float]) -> str:
    if score >= th[1]:
        return "HIGH"
    return "WARNING" if score >= th[0] else "LOW"


def _age(birth: dt.date, today: dt.date) -> int:
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def build_input(db: Session, user: User, q: Questionnaire, today: dt.date) -> tuple[dict, dict]:
    snapshot = {"age": _age(user.birth_date, today), "gender": user.gender}
    snapshot.update({f: getattr(q, f) for f in MODEL_FIELDS})
    sources = {"questionnaire_id": q.id, "weight": "QUESTIONNAIRE", "waist_size": "QUESTIONNAIRE", "sleep_hours": "QUESTIONNAIRE"}
    for field in ("weight", "waist_size"):
        log = db.scalar(select(HealthLog).where(HealthLog.user_id == user.user_id, getattr(HealthLog, field).is_not(None),
                                                HealthLog.created_at >= q.created_at)
                        .order_by(HealthLog.log_date.desc()))
        if log:
            snapshot[field], sources[field] = getattr(log, field), "HEALTH_LOG"
    # 수면: 최근 14일 중 7일 이상 기록이 있으면 평균, 아니면 문진 값 (03·04 합의)
    sleeps = list(db.scalars(select(Checkin.sleep_hours).where(
        Checkin.user_id == user.user_id, Checkin.sleep_hours.is_not(None),
        Checkin.checkin_date > today - dt.timedelta(days=14), Checkin.checkin_date <= today)))
    if len(sleeps) >= 7:
        snapshot["sleep_hours"], sources["sleep_hours"] = round(sum(sleeps) / len(sleeps), 1), "CHECKIN_14D"
    return snapshot, sources


def overall_of(results: list[dict], ths: dict) -> dict | None:
    """종합 점수 규칙 (03 No 9 제안): 가장 높은 단계 질환 기준, 같으면 점수가 큰 쪽."""
    level = lambda r: risk_level(r["risk_score"], ths[r["disease_type"]])  # noqa: E731
    basis = max(results, key=lambda r: (LEVEL_ORDER[level(r)], r["risk_score"]), default=None)
    if basis is None:
        return None
    return {"score": round(basis["risk_score"] * 100), "grade": level(basis),
            "basis_disease_type": basis["disease_type"]}


def latest_questionnaire(db: Session, user_id: int) -> Questionnaire | None:
    return db.scalar(select(Questionnaire).where(Questionnaire.user_id == user_id, Questionnaire.is_completed.is_(True))
                     .order_by(Questionnaire.id.desc()))


def recalculate(db: Session, user: User, reason: str) -> bool:
    """기록이 바뀌었을 때 다시 계산해요. 오늘 이미 계산했거나 문진이 없으면 하지 않습니다 (하루 최대 1회)."""
    q = latest_questionnaire(db, user.user_id)
    if q is None or _rows(db, user.user_id, now().date()):
        return False
    try:
        return run_prediction(db, user, q.id, reason)[1]
    except Exception:  # 동의 철회 등: 기록 저장은 막지 않음
        db.rollback()
        return False


def weekly_sleep_recalculation(db: Session, user: User) -> bool:
    """주 1회(월요일 새벽) 실행용. 이번 주 수면 값이 직전 예측 입력과 0.5시간 이상 다르면 재계산."""
    q, last = latest_questionnaire(db, user.user_id), latest_date(db, user.user_id)
    if q is None or last is None:
        return False
    new_sleep = build_input(db, user, q, now().date())[0].get("sleep_hours")
    old_sleep = _rows(db, user.user_id, last)[0].input_snapshot["input"].get("sleep_hours")
    if new_sleep is None or old_sleep is None or abs(new_sleep - old_sleep) < 0.5:
        return False
    return recalculate(db, user, "SLEEP_CHECKIN")


SIMULATABLE = {"activity_days_per_week", "activity_minutes_per_day", "sleep_hours", "waist_size", "weight",
               "smoking_status", "drinking_days_per_week", "drinks_per_occasion"}
UNITS = {"activity_days_per_week": "일", "activity_minutes_per_day": "분", "sleep_hours": "시간", "waist_size": "cm",
         "weight": "kg", "drinking_days_per_week": "일", "drinks_per_occasion": "잔"}
SIM_LABELS = {"activity_days_per_week": "주간 운동 횟수", "activity_minutes_per_day": "하루 운동 시간",
              "sleep_hours": "하루 평균 수면", "waist_size": "허리둘레", "weight": "체중", "smoking_status": "흡연",
              "drinking_days_per_week": "주간 음주 횟수", "drinks_per_occasion": "1회 음주량"}


def simulate(db: Session, user_id: int, changes: dict) -> dict:
    """No 11 '만약에' (저장하지 않음)."""
    date = latest_date(db, user_id)
    if date is None:
        raise api_error(404, "NOT_FOUND", "기준 예측이 없어요")
    bad = sorted(set(changes) - SIMULATABLE)
    if bad or not changes:
        raise api_error(400, "VALIDATION_ERROR", f"바꿀 수 없는 항목이에요: {bad}" if bad else "바꿀 항목이 없어요")
    rows = _rows(db, user_id, date)
    base = rows[0].input_snapshot["input"]
    targets = [r.disease_type for r in rows if not r.is_managed]
    if not targets:
        raise api_error(404, "NOT_FOUND", "예측 대상 질환이 없어요")
    try:
        cur = predict_risk(base, targets)["results"]
        sim = predict_risk({**base, **changes}, targets)["results"]
    except RiskInputError as e:
        raise api_error(400, "VALIDATION_ERROR", f"값을 확인해 주세요: {e.errors}")
    ths = get_thresholds(db)
    o_cur, o_sim = overall_of(cur, ths), overall_of(sim, ths)
    return {
        "base_prediction_date": date.isoformat(),
        "changes": [{"code": k, "label": SIM_LABELS[k], "unit": UNITS.get(k), "current": base.get(k), "assumed": v}
                    for k, v in changes.items()],
        "overall": {"current": o_cur["score"], "simulated": o_sim["score"], "diff": o_sim["score"] - o_cur["score"]},
        "results": [{"disease_type": c["disease_type"], "current_level": risk_level(c["risk_score"], ths[c["disease_type"]]),
                     "simulated_level": risk_level(s["risk_score"], ths[s["disease_type"]])} for c, s in zip(cur, sim)],
        "is_saved": False,
        "notice": "결과는 효과를 보장하지 않으며, 인과관계나 치료 효과로 해석할 수 없습니다.",
    }


def run_prediction(db: Session, user: User, questionnaire_id: int, reason: str | None = None) -> tuple[dict, bool]:
    """예측을 실행해 저장하고 응답을 돌려줘요. (응답, 새로 만들었는지)"""
    consent = db.scalar(select(Consent).where(Consent.user_id == user.user_id, Consent.consent_type == "HEALTH_DATA")
                        .order_by(Consent.id.desc()))
    if consent is None or not consent.agreed:
        raise api_error(409, "CONSENT_REQUIRED", "건강정보 수집 동의가 필요해요")
    q = db.get(Questionnaire, questionnaire_id)
    if q is None or q.user_id != user.user_id:
        raise api_error(404, "NOT_FOUND", "문진 기록이 없어요")
    if not q.is_completed:
        raise api_error(400, "VALIDATION_ERROR", "문진이 완료되지 않았어요")

    today = now().date()
    existing = _rows(db, user.user_id, today)
    if existing:
        # 하루에 이력은 1회차만 남겨요 (03 대조 결과 9 임시 결정).
        # 같은 문진이면 기존 결과를 그대로, 그날 문진을 새로 냈으면 오늘 회차를 새 결과로 바꿉니다.
        if existing[0].questionnaire_id == q.id or q.id < existing[0].questionnaire_id:
            return build_response(db, user.user_id, today), False
        db.execute(delete(RiskPrediction).where(RiskPrediction.user_id == user.user_id, RiskPrediction.prediction_date == today))
        if reason is None and existing[0].reason == "INITIAL":
            reason = "INITIAL"  # 첫 문진을 같은 날 고쳐 낸 경우

    snapshot, sources = build_input(db, user, q, today)
    managed = {d: bool(getattr(q, f"{c}_diagnosed") or getattr(q, f"{c}_medication")) for d, c in DISEASE_COLUMNS.items()}
    targets = [d for d, m in managed.items() if not m]
    try:
        out = predict_risk(snapshot, targets) if targets else {"model_version": "-", "data_source": "-", "results": [], "imputed_fields": []}
    except RiskInputError as e:
        raise api_error(400, "VALIDATION_ERROR", f"예측에 필요한 문진 값이 부족해요: {e.errors}")
    scored = {r["disease_type"]: r for r in out["results"]}

    ths = get_thresholds(db)
    overall = overall_of(list(scored.values()), ths)
    basis = scored[overall["basis_disease_type"]] if overall else None
    overall_score = overall["score"] if overall else None
    overall_grade = overall["grade"] if overall else None
    if reason is None:
        reason = "RECHECK" if q.is_recheck else "INITIAL"
    meta = {"sources": sources, "imputed_fields": out["imputed_fields"], "data_source": out["data_source"],
            "basis_disease_type": basis["disease_type"] if basis else None}
    for disease in DISEASE_COLUMNS:
        r = scored.get(disease)
        factors = (r["major_factors"] + [None] * 3)[:3] if r else [None] * 3
        db.add(RiskPrediction(
            user_id=user.user_id, questionnaire_id=q.id, prediction_date=today, disease_type=disease,
            model_version=out["model_version"], is_managed=managed[disease],
            risk_score=r["risk_score"] if r else None, risk_level=risk_level(r["risk_score"], ths[disease]) if r else None,
            major_factor1=factors[0], major_factor2=factors[1], major_factor3=factors[2],
            input_snapshot={"input": snapshot, **meta}, reason=reason,
            overall_score=overall_score, overall_grade=overall_grade))
    try:
        db.commit()
    except IntegrityError:  # 같은 순간에 다른 요청이 먼저 저장함 → 그 결과를 사용
        db.rollback()
        return build_response(db, user.user_id, today), False
    return build_response(db, user.user_id, today), True


def _rows(db: Session, user_id: int, date: dt.date) -> list[RiskPrediction]:
    return list(db.scalars(select(RiskPrediction).where(RiskPrediction.user_id == user_id,
                                                        RiskPrediction.prediction_date == date).order_by(RiskPrediction.id)))


def latest_date(db: Session, user_id: int) -> dt.date | None:
    return db.scalar(select(RiskPrediction.prediction_date).where(RiskPrediction.user_id == user_id)
                     .order_by(RiskPrediction.prediction_date.desc()))


def build_response(db: Session, user_id: int, date: dt.date) -> dict:
    """No 9 응답 형식 (C01 화면)."""
    rows = _rows(db, user_id, date)
    first, meta = rows[0], rows[0].input_snapshot
    snapshot, basis_disease = meta["input"], meta["basis_disease_type"]
    basis = next((r for r in rows if r.disease_type == basis_disease), None)

    factors = []
    if basis:
        for code in (basis.major_factor1, basis.major_factor2, basis.major_factor3):
            if code:
                factors.append({"code": code, "label": FACTOR_LABELS.get(code, code), "is_missing": False})
        fam = FAMILY_FIELD[basis_disease]
        if snapshot.get(fam) in (None, "UNKNOWN"):
            factors.append({"code": fam, "label": "가족력은 미확인", "is_missing": True})
    answered = [k for k, v in snapshot.items() if v is not None]
    is_demo = meta["data_source"] == "SYNTHETIC"
    return {
        "prediction_date": date.isoformat(),
        "view": "RISK" if basis else "MANAGEMENT",
        "overall": {"score": first.overall_score, "score_max": 100, "grade": first.overall_grade,
                    "grade_label": GRADE_LABELS[first.overall_grade], "basis_disease_type": basis_disease} if basis else None,
        "managed_diseases": [r.disease_type for r in rows if r.is_managed],
        "input_count": len(answered),
        "input_sources": meta["sources"],
        "factors": factors,
        "results": [{"prediction_id": r.id, "disease_type": r.disease_type, "is_managed": r.is_managed,
                     "risk_score": r.risk_score, "risk_level": r.risk_level,
                     "major_factors": [f for f in (r.major_factor1, r.major_factor2, r.major_factor3) if f]} for r in rows],
        "model_version": first.model_version,
        "is_demo_model": is_demo,  # 합성 데이터 모델이면 true → 화면에 데모 표시 (명세서에 없는 필드, 데모 기간용)
        "disclaimer": DISCLAIMER + (" (데모용 모델: 점수에 의미가 없어요)" if is_demo else ""),
        "created_at": iso(first.created_at),
    }


def history(db: Session, user_id: int, period: str, page: int, size: int) -> dict:
    """No 10 응답 형식 (C03 화면). 날짜가 한 회차."""
    days = {"1m": 30, "3m": 90, "all": None}[period]
    stmt = select(RiskPrediction).where(RiskPrediction.user_id == user_id)
    if days:
        stmt = stmt.where(RiskPrediction.prediction_date >= now().date() - dt.timedelta(days=days))
    by_date: dict[dt.date, RiskPrediction] = {}
    for r in db.scalars(stmt.order_by(RiskPrediction.prediction_date.desc(), RiskPrediction.id)):
        by_date.setdefault(r.prediction_date, r)
    rows = list(by_date.values())
    items = [{"prediction_date": r.prediction_date.isoformat(), "overall_score": r.overall_score, "reason": r.reason,
              "reason_label": REASON_LABELS.get(r.reason, r.reason), "model_version": r.model_version}
             for r in rows[(page - 1) * size: page * size]]
    return {"items": items, "total": len(rows), "page": page, "size": size,
            "model_version_changed": len({r.model_version for r in rows}) > 1}
