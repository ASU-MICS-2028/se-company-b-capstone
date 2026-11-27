"""Contract v1 smoke tests: every stub route answers with its documented status and shape.

When a route gets real logic, replace its row here with proper API tests.
"""

import re

import pytest

V = "/api/v1"
# Routes with real logic and their own API tests (test_auth.py, ...).
REAL = {
    ("post", "/auth/register"),
    ("post", "/auth/login"),
    ("get", "/auth/me"),
    ("get", "/vehicle-models"),
    ("get", "/vehicles"),
    ("post", "/vehicles"),
    ("get", "/vehicles/1"),
    ("patch", "/vehicles/1"),
    ("delete", "/vehicles/1"),
}

ROUTES = [
    ("get", "/vehicles/1/service-logs", None, 200),
    (
        "post",
        "/vehicles/1/service-logs",
        {"service_keys": ["engine_oil_and_filter"], "service_date": "2026-06-01"},
        201,
    ),
    ("get", "/vehicles/1/odometer-readings", None, 200),
    ("post", "/vehicles/1/odometer-readings", {"odometer_km": 53000}, 201),
    ("get", "/vehicles/1/reminders", None, 200),
    (
        "post",
        "/vehicles/1/reminders/R01/snooze",
        {"service_key": "engine_oil_and_filter", "until": "2026-12-01"},
        200,
    ),
    (
        "post",
        "/vehicles/1/reminders/R01/complete",
        {"service_key": "engine_oil_and_filter", "service_date": "2026-11-20"},
        201,
    ),
    ("get", "/vehicles/1/minder-prompts", None, 200),
    ("post", "/vehicles/1/minder-prompts", {"code": "7"}, 201),
    ("post", "/vehicles/1/minder-prompts/1/clear", None, 200),
    ("get", "/service-categories", None, 200),
    ("get", "/neighbourhoods", None, 200),
    ("get", "/mechanics/search?service=brake_service&neighbourhood=Osu", None, 200),
    ("get", "/mechanics/M01", None, 200),
    ("put", "/mechanics/M01/availability", {"status": "busy"}, 200),
    ("get", "/admin/mechanics", None, 200),
    ("get", "/admin/mechanics/M01", None, 200),
    (
        "put",
        "/admin/mechanics/M01/assessment",
        {"assessment_status": "suspended", "suspension_reason": "Complaint upheld"},
        200,
    ),
    ("get", "/admin/mechanics/M08/complaints", None, 200),
    ("post", "/admin/mechanics/M08/complaints", {"description": "No-show"}, 201),
    ("patch", "/admin/complaints/1", {"status": "upheld"}, 200),
]


@pytest.mark.parametrize(("method", "path", "body", "status"), ROUTES, ids=[r[1] for r in ROUTES])
def test_stub_route(client, method, path, body, status):
    res = client.request(method, V + path, json=body)
    assert res.status_code == status, res.text


def test_every_documented_route_is_covered(client):
    """Fails when a route is added to the API without a row in ROUTES."""
    tested = {(m, p.split("?")[0]) for m, p, _, _ in ROUTES} | REAL
    for path, ops in client.get("/openapi.json").json()["paths"].items():
        if not path.startswith(V):
            continue
        pattern = re.compile(re.sub(r"\{[^}]+\}", "[^/]+", path.removeprefix(V)) + "$")
        for method in ops:
            assert any(m == method and pattern.match(t) for m, t in tested), (method, path)


@pytest.mark.parametrize(
    ("path", "status", "code"),
    [
        ("/mechanics/search?service=brake_service&radius_km=15", 422, "validation_error"),
        ("/does-not-exist", 404, "not_found"),
    ],
)
def test_error_shape(client, path, status, code):
    res = client.get(V + path)
    assert res.status_code == status
    assert res.json()["error"]["code"] == code
    assert set(res.json()["error"]) == {"code", "message", "details"}
