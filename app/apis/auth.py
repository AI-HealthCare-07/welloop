"""01 구역: 회원가입·로그인·내 정보·동의 (데모에 필요한 부분)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import api_error, create_access_token, current_user, hash_password, verify_password
from app.dtos.schemas import ConsentRequest, LoginRequest, SignupRequest
from app.models.tables import Consent, User

router = APIRouter(prefix="/api/v1", tags=["01 시작·계정"])


def _user_out(u: User) -> dict:
    return {"user_id": u.user_id, "email": u.email, "name": u.name, "birth_date": u.birth_date.isoformat(),
            "gender": u.gender, "font_size": u.font_size, "created_at": u.created_at.isoformat()}


@router.post("/auth/signup", status_code=201)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    if not (body.terms_agreed and body.privacy_agreed):
        raise api_error(400, "VALIDATION_ERROR", "필수 약관에 동의해야 해요")
    if db.scalar(select(User).where(User.email == body.email)):
        raise api_error(409, "EMAIL_DUPLICATED", "이미 가입된 이메일이에요")
    user = User(email=body.email, password=hash_password(body.password), name=body.name,
                birth_date=body.birth_date, gender=body.gender)
    db.add(user)
    db.commit()
    return _user_out(user)


@router.post("/auth/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password):
        raise api_error(401, "LOGIN_FAILED", "이메일 또는 비밀번호가 맞지 않아요")
    return {"access_token": create_access_token(user.user_id), "token_type": "bearer", "user": _user_out(user)}


@router.get("/users/me")
def me(user: User = Depends(current_user)):
    return _user_out(user)


@router.post("/consents", status_code=201)
def save_consent(body: ConsentRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    consent = Consent(user_id=user.user_id, consent_type=body.consent_type, agreed=body.agreed)
    db.add(consent)
    db.commit()
    return {"consent_id": consent.id, "consent_type": consent.consent_type, "agreed": consent.agreed,
            "created_at": consent.created_at.isoformat()}
