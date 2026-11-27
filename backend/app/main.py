from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import __version__
from app.core import errors
from app.core.config import get_settings
from app.core.db import DbSession
from app.modules.auth.router import router as auth_router
from app.modules.mechanics.router import admin as admin_router
from app.modules.mechanics.router import router as mechanics_router
from app.modules.reminders.router import prompts as minder_prompts_router
from app.modules.reminders.router import router as reminders_router
from app.modules.service_logs.router import router as service_logs_router
from app.modules.vehicles.router import router as vehicles_router

app = FastAPI(
    title="Nkenten AutoCare API",
    version=__version__,
    description="Contract v1. Routes under /api/v1 are stubs returning example data "
    "until their issues land (#49, #50, #82, #44, #45). See docs/api/contract.md.",
)
errors.install(app)
for r in (
    auth_router,
    vehicles_router,
    service_logs_router,
    reminders_router,
    minder_prompts_router,
    mechanics_router,
    admin_router,
):
    app.include_router(r, prefix="/api/v1")

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
