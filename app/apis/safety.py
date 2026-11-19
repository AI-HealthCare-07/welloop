"""02 구역 검진 수치(No 8) · 05 구역 위험 신호 안내."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import api_error, current_user
from app.dtos.schemas import CheckupRequest
from app.models.tables import CheckupRecord, User
from app.services import safety_service as svc

router = APIRouter(prefix="/api/v1", tags=["02 검진 수치 · 05 위험 신호 안내"])


@router.post("/checkups", status_code=201)
def save_checkup(body: CheckupRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    values = body.model_dump()
    if all(values[f] is None for f in svc.CHECKUP_FIELDS):
        raise api_error(400, "VALIDATION_ERROR", "입력한 수치가 없어요 (건너뛰려면 호출하지 않아도 돼요)")
    rec = CheckupRecord(user_id=user.user_id, **values)
    db.add(rec)
    db.commit()
    return svc.checkup_out(rec)


@router.get("/checkups/latest")
def latest_checkup(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rec = svc.latest_checkup(db, user.user_id)
    if rec is None:
        raise api_error(404, "NOT_FOUND", "입력한 검진 수치가 없어요")
    return svc.checkup_out(rec)


@router.get("/safety/alerts")
def safety_alerts(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return {"items": svc.alerts(db, user.user_id)}
