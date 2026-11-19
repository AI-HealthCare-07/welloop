"""WELLOOP 백엔드 (데모). 실행: uvicorn app.main:app --reload  →  화면 http://localhost:8000 · API 문서 /docs"""
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.apis import auth, challenges, predictions, questionnaires, records
from app.core.db import Base, engine
from app.models import tables  # noqa: F401  (테이블 등록)

app = FastAPI(title="WELLOOP API (데모)", version="0.1.0")
Base.metadata.create_all(engine)  # 데모: 마이그레이션 도구 없이 테이블 생성 (템플릿 병합 후 교체)

for module in (auth, questionnaires, predictions, records, challenges):
    app.include_router(module.router)


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException):
    body = exc.detail if isinstance(exc.detail, dict) else {"detail": str(exc.detail), "code": "ERROR"}
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    first = exc.errors()[0]
    field = ".".join(str(x) for x in first["loc"] if x != "body")
    return JSONResponse(status_code=400, content={"detail": f"{field}: {first['msg']}", "code": "VALIDATION_ERROR"})


@app.get("/health")
def health():
    return {"status": "ok"}


# 데모 화면 (빌드 도구 없이 동작). 라우터 등록 뒤에 붙여야 /api 경로를 가리지 않아요.
_DEMO_UI = Path(__file__).resolve().parents[1] / "frontend" / "demo"
if _DEMO_UI.exists():
    app.mount("/", StaticFiles(directory=_DEMO_UI, html=True), name="demo-ui")
