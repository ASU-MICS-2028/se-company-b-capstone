from sqlalchemy.exc import OperationalError

from app import __version__
from app.core.db import get_db
from app.main import app


def test_health_ok(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "version": __version__, "db": "ok"}


def test_health_reports_db_failure(client):
    class BrokenSession:
        def execute(self, *_):
            raise OperationalError("SELECT 1", {}, Exception("db down"))

    app.dependency_overrides[get_db] = lambda: BrokenSession()
    res = client.get("/api/health")
    assert res.status_code == 503
    assert res.json()["db"] == "error"
    assert res.json()["status"] == "degraded"
