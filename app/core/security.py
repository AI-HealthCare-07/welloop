import datetime as dt

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import ACCESS_TOKEN_MINUTES, JWT_ALGORITHM, JWT_SECRET
from .db import get_db

bearer = HTTPBearer(auto_error=False)


def api_error(status: int, code: str, detail: str) -> HTTPException:
    """공통 에러 형식 {detail, code} (API 명세서 공통 규칙)."""
    return HTTPException(status_code=status, detail={"detail": detail, "code": code})


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(user_id: int) -> str:
    exp = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": exp}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)):
    from app.models.tables import User

    if cred is None:
        raise api_error(401, "UNAUTHORIZED", "토큰이 없어요")
    try:
        user_id = int(jwt.decode(cred.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])["sub"])
    except jwt.PyJWTError:
        raise api_error(401, "UNAUTHORIZED", "토큰이 만료됐거나 올바르지 않아요")
    user = db.get(User, user_id)
    if user is None:
        raise api_error(401, "UNAUTHORIZED", "사용자를 찾을 수 없어요")
    return user
