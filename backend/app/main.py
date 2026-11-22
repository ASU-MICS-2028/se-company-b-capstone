from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import __version__
from app.core.config import get_settings
from app.core.db import DbSession

app = FastAPI(title="Nkenten AutoCare API", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["health"])
def health(db: DbSession) -> JSONResponse:
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except SQLAlchemyError:
        db_status = "error"
    ok = db_status == "ok"
    return JSONResponse(
        status_code=200 if ok else 503,
        content={"status": "ok" if ok else "degraded", "version": __version__, "db": db_status},
    )
