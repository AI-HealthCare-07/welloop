"""01 구역: 회원가입·로그인·내 정보·동의 (데모에 필요한 부분)."""
import re

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import api_error, create_access_token, current_user, hash_password, verify_password
from app.dtos.schemas import ConsentRequest, LoginRequest, SignupRequest
from app.models.tables import Consent, User, now
from app.models.tables import iso

router = APIRouter(prefix="/api/v1", tags=["01 시작·계정"])


def _user_out(u: User) -> dict:
    return {"user_id": u.user_id, "email": u.email, "name": u.name, "birth_date": u.birth_date.isoformat(),
            "gender": u.gender, "font_size": u.font_size, "created_at": iso(u.created_at)}


@router.post("/auth/signup", status_code=201)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    if not (body.terms_agreed and body.privacy_agreed):
        raise api_error(400, "VALIDATION_ERROR", "필수 약관에 동의해야 해요")
    pw = body.password
    if len(pw.encode()) > 72 or not (re.search(r"[A-Za-z]", pw) and re.search(r"\d", pw) and re.search(r"[^A-Za-z0-9\s]", pw)):
        raise api_error(400, "VALIDATION_ERROR", "비밀번호는 영문·숫자·특수문자를 포함해 8자 이상이어야 해요")
    today = now().date()
    age = today.year - body.birth_date.year - ((today.month, today.day) < (body.birth_date.month, body.birth_date.day))
    if not 19 <= age <= 110:  # 가입 연령 기준은 팀 미결정(성인 / 45세 이상). 예측 모델 입력 범위에 맞춰 성인만 받음
        raise api_error(400, "VALIDATION_ERROR", "만 19세 이상만 가입할 수 있어요")
    email = body.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise api_error(409, "EMAIL_DUPLICATED", "이미 가입된 이메일이에요")
    user = User(email=email, password=hash_password(body.password), name=body.name,
                birth_date=body.birth_date, gender=body.gender)
    db.add(user)
    db.commit()
    return _user_out(user)


@router.post("/auth/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
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
            "created_at": iso(consent.created_at)}
