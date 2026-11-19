"""03 구역: 위험 신호 예측 (No 9, 9-1, 10)."""
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import api_error, current_user
from app.dtos.schemas import PredictionRequest, SimulateRequest
from app.models.tables import User
from app.services import prediction_service as svc

router = APIRouter(prefix="/api/v1/predictions", tags=["03 평가·대시보드"])


@router.post("", status_code=201)
def create_prediction(body: PredictionRequest, response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)):
    result, created = svc.run_prediction(db, user, body.questionnaire_id)
    if not created:
        response.status_code = 200
    return result


@router.post("/simulate")
def simulate(body: SimulateRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return svc.simulate(db, user.user_id, body.changes)


@router.get("/latest")
def latest_prediction(user: User = Depends(current_user), db: Session = Depends(get_db)):
    date = svc.latest_date(db, user.user_id)
    if date is None:
        raise api_error(404, "NOT_FOUND", "예측 이력이 없어요")
    return svc.build_response(db, user.user_id, date)


@router.get("")
def list_predictions(period: Literal["1m", "3m", "all"] = "3m", page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=50),
                     user: User = Depends(current_user), db: Session = Depends(get_db)):
    return svc.history(db, user.user_id, period, page, size)
