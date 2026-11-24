from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine, create_engine, event
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


@event.listens_for(Engine, "connect")
def _sqlite_foreign_keys(dbapi_conn, _record):
    """SQLite ignores foreign keys unless enabled per connection (ADR-003)."""
    if type(dbapi_conn).__module__.startswith("sqlite3"):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")


engine = create_engine(
    get_settings().database_url,
    connect_args={"check_same_thread": False},  # SQLite + FastAPI threadpool
)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    with SessionLocal() as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]


def create_all(bind: Engine = engine) -> None:
    """Create every module's tables. Imports the models so they register on Base."""
    import app.models  # noqa: F401

    Base.metadata.create_all(bind)


def choice(name: str, *values: str) -> SAEnum:
    """String column limited to `values` by a CHECK constraint (portable, no native enum)."""
    return SAEnum(*values, name=name, native_enum=False, create_constraint=True, length=40)
