"""04 구역: 오늘의 미션·체크인 / 05 구역: 오늘의 코치 메시지."""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import current_user
from app.dtos.schemas import CheckinRequest
from app.models.tables import User
from app.services import challenge_service as svc

router = APIRouter(prefix="/api/v1", tags=["04 홈·챌린지 · 05 AI 코치"])


@router.get("/challenges/today")
def challenges_today(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return svc.today_missions(db, user)


@router.post("/checkins", status_code=201)
def checkin(body: CheckinRequest, response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)):
    result, created = svc.save_checkin(db, user, body)
    if not created:
        response.status_code = 200
    return result


@router.get("/coach/today")
def coach_today(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return svc.coach_today(db, user)
