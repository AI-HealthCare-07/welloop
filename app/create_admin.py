"""관리자 계정 만들기. 실행: python -m app.create_admin 이메일
비밀번호는 환경변수 ADMIN_PASSWORD, 없으면 새로 만들어 화면에 한 번 출력해요."""
import datetime as dt
import os
import secrets
import sys

from sqlalchemy import select

from app.core.db import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.tables import User


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("사용법: python -m app.create_admin admin@example.com")
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == sys.argv[1])):
            raise SystemExit("이미 있는 이메일이에요.")
        password = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(12)
        db.add(User(email=sys.argv[1], password=hash_password(password), name="관리자", birth_date=dt.date(1990, 1, 1),
                    gender="FEMALE", role="ADMIN"))
        db.commit()
        print(f"관리자 계정을 만들었어요 → {sys.argv[1]} / 비밀번호 {password}")


if __name__ == "__main__":
    main()
