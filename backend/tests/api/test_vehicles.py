"""US-02 register vehicle (#50): AT-US02-1/2/3a/3b and AC-02 ownership isolation."""

from datetime import date

import pytest

from app.core.db import get_db
from app.main import app
from app.modules.reminders.models import ReminderRule, RuleApplicability, Source
from app.modules.vehicles.models import VehicleModel

V = "/api/v1"
COROLLA_2014 = {
    "make": "Toyota",
    "model": "Corolla",
    "model_year": 2014,
    "powertrain": "petrol",
    "body_style": "sedan",
    "odometer_km": 142000,
}
ALMERA = {
    "make": "Nissan",
    "model": "Almera",
    "model_year": 2016,
    "powertrain": "petrol",
    "odometer_km": 98000,
}
COROLLA_2025_US = {
    "make": "toyota",
    "model": "corolla",
    "model_year": 2025,
    "powertrain": "petrol",
    "body_style": "sedan",
    "source_market": "US",
    "odometer_km": 48000,
}


@pytest.fixture
def catalogue(client):
    """V01 (no rules) and V03 with R01 for a US 2025 petrol sedan, as in the seed."""
    db = next(app.dependency_overrides[get_db]())
    db.add_all(
        [
            VehicleModel(
                catalogue_id="V01",
                make="Toyota",
                model="Corolla",
                year_from=2014,
                year_to=2018,
                powertrains=["petrol"],
                rules_supported=False,
                note=None,
            ),
            VehicleModel(
                catalogue_id="V03",
                make="Toyota",
                model="Corolla",
                year_from=2023,
                year_to=2025,
                powertrains=["petrol", "hybrid"],
                rules_supported=True,
                note=None,
            ),
            Source(
                source_id="S1",
                title="Toyota 2025 Corolla",
                url="https://example.com",
                accessed=date(2026, 11, 21),
            ),
        ]
    )
    db.flush()
    rule = ReminderRule(
        rule_id="R01",
        make="Toyota",
        model="Corolla",
        service_type="engine_oil_and_filter",
        label="Oil",
        condition="normal_recommended_oil",
        source_miles=10000,
        interval_km=16093.44,
        interval_months=12,
        anchor="last_completed_service",
        verified=True,
    )
    rule.applicability = [
        RuleApplicability(
            catalogue_id="V03",
            market="US",
            year_from=2025,
            year_to=2025,
            powertrain="petrol",
            body_style="sedan",
        )
    ]
    db.add(rule)
    db.commit()
    db.close()


def driver(client, email="ama@example.com"):
    res = client.post(
        f"{V}/auth/register",
        json={"full_name": "Ama", "email": email, "password": "Demo-pass-2026"},
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def garage(client, auth):
    return client.get(f"{V}/vehicles", headers=auth).json()


def test_new_driver_has_an_empty_garage(client):
    assert garage(client, driver(client)) == {"items": [], "page": 1, "page_size": 20, "total": 0}


def test_catalogue_car_is_linked_but_schedule_limited(client, catalogue):
    """AT-US02-1: V01 matched from make/model/year/powertrain; it has no rules."""
    auth = driver(client)
    res = client.post(f"{V}/vehicles", json=COROLLA_2014, headers=auth)
    assert res.status_code == 201, res.text
    car = res.json()
    assert car["catalogue_id"] == "V01"
    assert car["reminder_support"] == "limited"
    assert car["latest_odometer_km"] == 142000
    assert garage(client, auth)["total"] == 1


def test_exact_rule_configuration_is_supported(client, catalogue):
    car = client.post(f"{V}/vehicles", json=COROLLA_2025_US, headers=driver(client)).json()
    assert car["catalogue_id"] == "V03"
    assert (car["make"], car["model"]) == ("Toyota", "Corolla")  # catalogue spelling
    assert car["reminder_support"] == "supported"


def test_unknown_market_is_not_supported(client, catalogue):
    """Catalogue hit + rule exists, but the market is unknown: never guess (RT-11/12)."""
    body = COROLLA_2025_US | {"source_market": "UNKNOWN"}
    car = client.post(f"{V}/vehicles", json=body, headers=driver(client)).json()
    assert (car["catalogue_id"], car["reminder_support"]) == ("V03", "limited")


def test_unlisted_car_is_saved_as_manual(client, catalogue):
    """AT-US02-2."""
    auth = driver(client)
    car = client.post(f"{V}/vehicles", json=ALMERA, headers=auth).json()
    assert car["catalogue_id"] is None
    assert car["reminder_support"] == "limited"
    assert [c["model"] for c in garage(client, auth)["items"]] == ["Almera"]


@pytest.mark.parametrize(
    "odometer", [-5, None, "missing"], ids=["negative (3a)", "null (3b)", "blank (3b)"]
)
def test_bad_odometer_blocks_save(client, catalogue, odometer):
    """AT-US02-3a/3b: 422 pointing at odometer_km, and no vehicle is created."""
    auth = driver(client)
    body = dict(ALMERA)
    if odometer == "missing":
        del body["odometer_km"]
    else:
        body["odometer_km"] = odometer
    res = client.post(f"{V}/vehicles", json=body, headers=auth)
    assert res.status_code == 422
    assert any("odometer_km" in d["loc"] for d in res.json()["error"]["details"])
    assert garage(client, auth)["total"] == 0


@pytest.mark.parametrize(
    ("catalogue_id", "code"),
    [("V99", "unknown_catalogue_id"), ("V03", "catalogue_mismatch")],
)
def test_explicit_catalogue_id_must_fit(client, catalogue, catalogue_id, code):
    body = COROLLA_2014 | {"catalogue_id": catalogue_id}  # V03 is 2023-2025, car is 2014
    res = client.post(f"{V}/vehicles", json=body, headers=driver(client))
    assert res.status_code == 400 and res.json()["error"]["code"] == code


def test_vehicles_need_a_signed_in_user(client):
    assert client.get(f"{V}/vehicles").status_code == 401
    assert client.post(f"{V}/vehicles", json=ALMERA).status_code == 401


def test_other_drivers_vehicles_are_invisible(client, catalogue):
    """AC-02: reads and writes on someone else's car are 404."""
    ama, kofi = driver(client), driver(client, "kofi@example.com")
    car_id = client.post(f"{V}/vehicles", json=ALMERA, headers=ama).json()["id"]
    assert garage(client, kofi)["total"] == 0
    assert client.get(f"{V}/vehicles/{car_id}", headers=kofi).status_code == 404
    assert (
        client.patch(f"{V}/vehicles/{car_id}", json={"nickname": "x"}, headers=kofi).status_code
        == 404
    )
    assert client.delete(f"{V}/vehicles/{car_id}", headers=kofi).status_code == 404
    assert client.get(f"{V}/vehicles/{car_id}", headers=ama).status_code == 200


def test_patch_updates_config_and_recomputes_support(client, catalogue):
    auth = driver(client)
    body = COROLLA_2025_US | {"source_market": "UNKNOWN"}
    car_id = client.post(f"{V}/vehicles", json=body, headers=auth).json()["id"]
    res = client.patch(
        f"{V}/vehicles/{car_id}",
        json={"source_market": "US", "body_style": None, "nickname": "Blue"},
        headers=auth,
    )
    assert res.status_code == 200
    car = res.json()
    assert (car["source_market"], car["body_style"], car["nickname"]) == ("US", "sedan", "Blue")
    assert car["reminder_support"] == "supported"


def test_delete_removes_the_car(client, catalogue):
    auth = driver(client)
    car_id = client.post(f"{V}/vehicles", json=ALMERA, headers=auth).json()["id"]
    assert client.delete(f"{V}/vehicles/{car_id}", headers=auth).status_code == 204
    assert client.get(f"{V}/vehicles/{car_id}", headers=auth).status_code == 404


def test_catalogue_listing_filters(client, catalogue):
    rows = client.get(f"{V}/vehicle-models", params={"make": "toyota"}).json()
    assert [r["catalogue_id"] for r in rows] == ["V01", "V03"]
    assert client.get(f"{V}/vehicle-models", params={"make": "Honda"}).json() == []
