"""06 구역: 관리자 (REQ-030~033). 개인 건강 정보는 다루지 않고 집계·콘텐츠만 (NFR-016). 작업은 admin_logs에 남겨요."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import api_error, create_access_token, current_user, verify_password
from app.dtos.schemas import ChallengeAdminRequest, KeywordRequest, LoginRequest, ThresholdRequest
from app.models.tables import (AdminLog, Challenge, Checkin, CoachMessage, DailyChallenge, RiskPrediction, RiskThreshold,
                               SafetyKeyword, User, now)
from app.services import challenge_service, prediction_service, safety_service

router = APIRouter(prefix="/api/v1/admin", tags=["06 관리자"])


def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != "ADMIN":
        raise api_error(403, "FORBIDDEN", "관리자만 사용할 수 있어요")
    return user


def _log(db: Session, admin: User, action: str, target: str) -> None:
    db.add(AdminLog(admin_id=admin.user_id, action=action, target=target))
    db.commit()


@router.post("/login")
def admin_login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password):
        raise api_error(401, "LOGIN_FAILED", "이메일 또는 비밀번호가 맞지 않아요")
    if user.role != "ADMIN":
        raise api_error(403, "FORBIDDEN", "관리자 계정이 아니에요")
    return {"access_token": create_access_token(user.user_id), "token_type": "bearer"}


def _challenge_out(c: Challenge) -> dict:
    return {"challenge_id": c.id, "category": c.category, "title": c.title, "description": c.description,
            "intensity": c.intensity, "is_active": c.is_active}


@router.get("/challenges")
def list_challenges(admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    challenge_service.seed_challenges(db)
    items = [_challenge_out(c) for c in db.scalars(select(Challenge).order_by(Challenge.category, Challenge.id))]
    return {"items": items, "total": len(items)}


@router.post("/challenges", status_code=201)
def create_challenge(body: ChallengeAdminRequest, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    c = Challenge(**body.model_dump())
    db.add(c)
    db.commit()
    _log(db, admin, "챌린지 등록", f"challenges:{c.id}")
    return _challenge_out(c)


@router.put("/challenges/{challenge_id}")
def update_challenge(challenge_id: int, body: ChallengeAdminRequest, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    c = db.get(Challenge, challenge_id)
    if c is None:
        raise api_error(404, "NOT_FOUND", "챌린지가 없어요")
    for k, v in body.model_dump().items():
        setattr(c, k, v)
    db.commit()
    _log(db, admin, "챌린지 수정", f"challenges:{c.id}")
    return _challenge_out(c)


@router.delete("/challenges/{challenge_id}")
def deactivate_challenge(challenge_id: int, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    """실제로 지우지 않고 비활성화해요 (과거 미션 기록 보존, REQ-031)."""
    c = db.get(Challenge, challenge_id)
    if c is None:
        raise api_error(404, "NOT_FOUND", "챌린지가 없어요")
    c.is_active = False
    db.commit()
    _log(db, admin, "챌린지 비활성화", f"challenges:{c.id}")
    return _challenge_out(c)


def _keyword_out(k: SafetyKeyword) -> dict:
    return {"keyword_id": k.id, "keyword": k.keyword, "kind": k.kind, "is_active": k.is_active}


@router.get("/safety-keywords")
def list_keywords(admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    safety_service.seed_keywords(db)
    items = [_keyword_out(k) for k in db.scalars(select(SafetyKeyword).order_by(SafetyKeyword.kind, SafetyKeyword.id))]
    return {"items": items, "total": len(items)}


@router.post("/safety-keywords", status_code=201)
def create_keyword(body: KeywordRequest, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    safety_service.seed_keywords(db)
    if db.scalar(select(SafetyKeyword).where(SafetyKeyword.keyword == body.keyword)):
        raise api_error(409, "DUPLICATED", "이미 등록된 키워드예요")
    k = SafetyKeyword(**body.model_dump(), updated_by=admin.user_id)
    db.add(k)
    db.commit()
    _log(db, admin, "키워드 등록", f"safety_keywords:{k.id}")
    return _keyword_out(k)


@router.put("/safety-keywords/{keyword_id}")
def update_keyword(keyword_id: int, body: KeywordRequest, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    k = db.get(SafetyKeyword, keyword_id)
    if k is None:
        raise api_error(404, "NOT_FOUND", "키워드가 없어요")
    k.keyword, k.kind, k.is_active, k.updated_by, k.updated_at = body.keyword, body.kind, body.is_active, admin.user_id, now()
    db.commit()
    _log(db, admin, "키워드 수정", f"safety_keywords:{k.id}")
    return _keyword_out(k)


@router.delete("/safety-keywords/{keyword_id}", status_code=204)
def delete_keyword(keyword_id: int, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    k = db.get(SafetyKeyword, keyword_id)
    if k is None:
        raise api_error(404, "NOT_FOUND", "키워드가 없어요")
    db.delete(k)
    db.commit()
    _log(db, admin, "키워드 삭제", f"safety_keywords:{keyword_id}")


@router.get("/thresholds")
def list_thresholds(admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    ths = prediction_service.get_thresholds(db)
    return {"items": [{"disease_type": d, "warning_from": w, "high_from": h} for d, (w, h) in ths.items()],
            "note": "새 값은 다음 계산부터 적용돼요. 지난 예측 이력의 단계는 바뀌지 않습니다."}


@router.put("/thresholds/{disease_type}")
def update_threshold(disease_type: str, body: ThresholdRequest, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    if disease_type not in prediction_service.DISEASE_COLUMNS:
        raise api_error(404, "NOT_FOUND", "질환 종류가 올바르지 않아요")
    if body.warning_from >= body.high_from:
        raise api_error(400, "VALIDATION_ERROR", "주의 시작값은 높음 시작값보다 작아야 해요")
    t = db.scalar(select(RiskThreshold).where(RiskThreshold.disease_type == disease_type))
    if t is None:
        t = RiskThreshold(disease_type=disease_type, warning_from=body.warning_from, high_from=body.high_from)
        db.add(t)
    t.warning_from, t.high_from, t.updated_by, t.updated_at = body.warning_from, body.high_from, admin.user_id, now()
    db.commit()
    _log(db, admin, "경계값 수정", f"risk_thresholds:{disease_type}")
    return {"disease_type": disease_type, "warning_from": t.warning_from, "high_from": t.high_from, "updated_at": t.updated_at.isoformat()}


@router.get("/stats")
def stats(admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    """집계만 돌려줘요. 개인별 건강 정보·메모는 포함하지 않습니다 (NFR-016)."""
    count = lambda stmt: db.scalar(stmt) or 0  # noqa: E731
    week_ago = now().date().toordinal() - 7
    assigned = count(select(func.count(DailyChallenge.id)))
    done = count(select(func.count(DailyChallenge.id)).where(DailyChallenge.is_completed.is_(True)))
    actives = {u for u, d in db.execute(select(Checkin.user_id, Checkin.checkin_date)) if d.toordinal() > week_ago}
    versions = db.execute(select(RiskPrediction.model_version, func.count(func.distinct(RiskPrediction.user_id)))
                          .group_by(RiskPrediction.model_version)).all()
    logs = db.scalars(select(AdminLog).order_by(AdminLog.id.desc()).limit(10))
    return {"total_users": count(select(func.count(User.user_id)).where(User.role == "USER")),
            "active_users_7d": len(actives),
            "mission_completion_rate": round(done / assigned, 2) if assigned else 0.0,
            "coach_messages": count(select(func.count(CoachMessage.id))),
            "llm_calls": count(select(func.count(CoachMessage.id)).where(CoachMessage.source == "LLM")),
            "model_versions": [{"model_version": v, "users": n} for v, n in versions],
            "recent_admin_logs": [{"action": g.action, "target": g.target, "created_at": g.created_at.isoformat()} for g in logs]}
