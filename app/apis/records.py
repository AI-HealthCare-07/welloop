"""03 구역: 건강 수치 기록(No 17·17-1·17-2·18) · 대시보드(No 19) · 관리 평가 요약(No 19-1)."""
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import current_user
from app.dtos.schemas import HealthLogRequest
from app.models.tables import User
from app.services import record_service as svc

router = APIRouter(prefix="/api/v1", tags=["03 평가·대시보드"])
Period = Literal["1m", "3m", "all"]


@router.post("/health-logs", status_code=201)
def create_log(body: HealthLogRequest, response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)):
    result, created = svc.save_log(db, user, body)
    if not created:
        response.status_code = 200
    return result


@router.get("/health-logs")
def list_logs(period: Period = "1m", page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=100),
              user: User = Depends(current_user), db: Session = Depends(get_db)):
    return svc.list_logs(db, user.user_id, period, page, size)


@router.patch("/health-logs/{health_log_id}")
def update_log(health_log_id: int, body: HealthLogRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    log = svc.get_own_log(db, user, health_log_id)
    for f in svc.LOG_FIELDS:
        if getattr(body, f) is not None:
            setattr(log, f, getattr(body, f))
    db.commit()
    return svc.log_out(log)


@router.delete("/health-logs/{health_log_id}", status_code=204)
def delete_log(health_log_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(svc.get_own_log(db, user, health_log_id))
    db.commit()


@router.get("/dashboard")
def dashboard(period: Period = "1m", user: User = Depends(current_user), db: Session = Depends(get_db)):
    return svc.dashboard(db, user.user_id, period)


@router.get("/management/summary")
def management_summary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return svc.management_summary(db, user.user_id)
