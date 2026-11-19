"""02 구역: 문진 저장 (필드는 ERD questionnaires 컬럼)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import current_user
from app.dtos.schemas import QuestionnaireRequest
from app.models.tables import Questionnaire, User
from app.models.tables import iso

router = APIRouter(prefix="/api/v1", tags=["02 문진"])


@router.post("/questionnaires", status_code=201)
def save_questionnaire(body: QuestionnaireRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = Questionnaire(user_id=user.user_id, **body.model_dump())
    db.add(q)
    db.commit()
    bmi = round(q.weight / (q.height / 100) ** 2, 1) if q.height and q.weight else None
    return {"questionnaire_id": q.id, "bmi": bmi, "is_completed": q.is_completed, "created_at": iso(q.created_at)}
