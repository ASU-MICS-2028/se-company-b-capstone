"""Mechanic matching engine v1: MT-01 to MT-04 and MT-11 to MT-13 (test plan outline).

Fixture tests use data/seed/mechanics.json at its fixed seed_reference_time.
"""

import json
import math
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from app.modules.mechanics.matching import (
    EARTH_RADIUS_KM,
    Listing,
    MatchingError,
    Origin,
    coordinates_origin,
    from_seed,
    haversine_km,
    neighbourhood_origin,
    round_km,
    search,
)

SEED = Path(__file__).resolve().parents[3] / "data" / "seed" / "mechanics.json"


@pytest.fixture(scope="module")
def seed():
    return from_seed(json.loads(SEED.read_text(encoding="utf-8")))


def run(seed, service, area, radius=10, include_unavailable=False, demo_mode=True, listings=None):
    return search(
        seed.listings if listings is None else listings,
        seed.categories,
        service=service,
        origin=neighbourhood_origin(area, seed.neighbourhoods),
        radius_km=radius,
        include_unavailable=include_unavailable,
        now=seed.reference_time,
        demo_mode=demo_mode,
    )


def ids(matches):
    return [m.mechanic_id for m in matches]


# --- MT-01 to MT-04: fixture order ------------------------------------------------------


def test_mt01_brake_osu_10km(seed):
    r = run(seed, "brake_service", "Osu")
    assert ids(r.assessed) == ["M01", "M02"]
    assert ids(r.not_assessed) == []
    assert [m.availability for m in r.assessed] == ["available", "busy"]
    assert r.hidden_unavailable == 1  # M07 currently unavailable; M08 suspended, never counted
    assert r.suggest_radius_km is None
    assert r.origin_precision == "neighbourhood"


def test_mt02_include_unavailable_adds_m07(seed):
    r = run(seed, "brake_service", "Osu", include_unavailable=True)
    assert ids(r.assessed) == ["M01", "M02", "M07"]
    assert r.assessed[2].availability == "unavailable"
    assert r.hidden_unavailable == 0


def test_mt03_brake_osu_20km_m04_out_of_own_radius(seed):
    r = run(seed, "brake_service", "Osu", radius=20)
    assert ids(r.assessed) == ["M01", "M02"]
    assert ids(r.not_assessed) == ["M06"]
    m04 = next(li for li in seed.listings if li.id == "M04")
    osu = next(n for n in seed.neighbourhoods if n.name == "Osu")
    d = haversine_km(osu.lat, osu.lng, m04.lat, m04.lng)
    assert m04.service_radius_km < d <= 20  # inside the driver radius, outside its own


def test_mt04_oil_east_legon_stale_m03_unknown(seed):
    r = run(seed, "oil_service", "East Legon")
    assert ids(r.assessed) == ["M03", "M04", "M01"]
    assert ids(r.not_assessed) == ["M06"]
    m03 = r.assessed[0]
    assert m03.availability == "unknown"
    assert m03.reported_at is not None  # stale report keeps its last valid timestamp


# --- MT-11: distance and radius boundaries ----------------------------------------------


def test_mt11_osu_to_east_legon_about_9_2km(seed):
    r = run(seed, "oil_service", "East Legon")
    m01 = next(m for m in r.assessed if m.mechanic_id == "M01")
    assert m01.distance_km == round_km(m01.distance_km_exact)
    assert str(m01.distance_km) == "9.2"


def _listing(id="X01", lat=0.0, lng=0.0, radius=40.0, **kw):
    base = dict(
        id=id, name=f"DEMO - {id}", neighbourhood="Test", lat=lat, lng=lng,
        service_radius_km=radius, assessment_status="assessed", assessed_on="2026-11-01",
        services={"brake_service": "assessed"}, availability_status="available",
        availability_updated_at=None, is_demo=True, published=True,
    )
    base.update(kw)
    return Listing(**base)


def _north(km):
    """Latitude (from 0, 0) that is ``km`` due north along a meridian."""
    return math.degrees(km / EARTH_RADIUS_KM)


def _search_at_origin(seed, listings, radius=10, now=None, **kw):
    return search(
        listings, seed.categories, service="brake_service", origin=Origin(0.0, 0.0, "device"),
        radius_km=radius, now=now or seed.reference_time, demo_mode=True, **kw,
    )


def test_mt11_service_radius_equality_passes_and_just_outside_fails(seed):
    d = haversine_km(0, 0, _north(6.0), 0)
    exact = _listing("X01", lat=_north(6.0), radius=d)
    outside = _listing("X02", lat=_north(6.0), radius=d - 1e-9)
    r = _search_at_origin(seed, [exact, outside])
    assert ids(r.assessed) == ["X01"]


def test_mt11_driver_radius_uses_unrounded_distance(seed):
    # 9.96 km and 10.04 km both display as 10.0 km; only the first is inside 10 km.
    inside = _listing("X01", lat=_north(9.96))
    outside = _listing("X02", lat=_north(10.04))
    r = _search_at_origin(seed, [inside, outside])
    assert ids(r.assessed) == ["X01"]
    assert str(r.assessed[0].distance_km) == "10.0"
    assert str(round_km(haversine_km(0, 0, _north(10.04), 0))) == "10.0"


def test_mt11_haversine_zero_and_half_up_rounding():
    assert haversine_km(5.556, -0.182, 5.556, -0.182) == 0.0
    assert str(round_km(0.25)) == "0.3"  # half-up, not banker's rounding
    assert str(round_km(0.35)) == "0.4"


# --- MT-12: ties on rounded distance ----------------------------------------------------


def test_mt12_newer_report_wins_then_id_then_null_last(seed):
    now = seed.reference_time
    lat = _north(2.0)
    listings = [
        _listing("X04", lat=lat, availability_updated_at=None),
        _listing("X03", lat=lat, availability_updated_at=now - timedelta(hours=1)),
        _listing("X02", lat=lat, availability_updated_at=now - timedelta(hours=1)),
        _listing("X01", lat=lat, availability_updated_at=now - timedelta(hours=5)),
        _listing("X05", lat=_north(2.04), availability_updated_at=now),  # also rounds to 2.0
    ]
    r = _search_at_origin(seed, listings)
    assert ids(r.assessed) == ["X05", "X02", "X03", "X01", "X04"]
    assert len({m.distance_km for m in r.assessed}) == 1


# --- MT-13: availability freshness ------------------------------------------------------


@pytest.mark.parametrize(
    ("age", "status", "expected", "keeps_timestamp"),
    [
        (timedelta(hours=24), "busy", "busy", True),  # exactly 24 h is current
        (timedelta(hours=24, seconds=1), "busy", "unknown", True),  # stale keeps time
        (-timedelta(seconds=1), "available", "unknown", False),  # future-dated
        (None, "available", "unknown", False),  # missing report
        (timedelta(hours=1), "on_holiday", "unknown", False),  # invalid status
    ],
)
def test_mt13_freshness(seed, age, status, expected, keeps_timestamp):
    now = seed.reference_time
    ts = None if age is None else now - age
    li = _listing(lat=_north(1.0), availability_status=status, availability_updated_at=ts)
    (m,) = _search_at_origin(seed, [li]).assessed
    assert m.availability == expected
    assert (m.reported_at is not None) is keeps_timestamp


def test_mt13_stale_unavailable_becomes_unknown_and_is_listed(seed):
    now = seed.reference_time
    stale = _listing(lat=_north(1.0), availability_status="unavailable",
                     availability_updated_at=now - timedelta(hours=30))
    fresh = replace(stale, id="X02", availability_updated_at=now - timedelta(hours=2))
    r = _search_at_origin(seed, [stale, fresh])
    assert ids(r.assessed) == ["X01"]
    assert r.assessed[0].availability == "unknown"
    assert r.hidden_unavailable == 1


# --- Supporting rules from the spec -----------------------------------------------------


def test_suspended_unpublished_and_demo_gating(seed):
    r = run(seed, "brake_service", "Dansoman", include_unavailable=True)
    assert "M08" not in ids(r.assessed) + ids(r.not_assessed)
    r = run(seed, "brake_service", "Osu", demo_mode=False)
    assert r.assessed == () and r.not_assessed == ()


def test_mt09_self_reported_service_of_assessed_mechanic_is_not_assessed(seed):
    r = run(seed, "diagnostics", "Osu")
    assert ids(r.assessed) == ["M03"]
    assert ids(r.not_assessed) == ["M01"]


def test_empty_assessed_suggests_next_radius_then_terminal_message(seed):
    r10 = run(seed, "suspension_steering", "Osu")  # MT-06
    assert r10.assessed == () and r10.suggest_radius_km == 20
    r40 = run(seed, "air_conditioning", "Adenta", radius=40)  # MT-05
    assert r40.assessed == () and r40.suggest_radius_km is None
    assert ids(r40.not_assessed) == ["M05"]
    assert "Air conditioning" in r40.message


@pytest.mark.parametrize("name", ["Osu", "  osu ", "OSU", "Ｏｓｕ"])  # incl. full-width
def test_neighbourhood_resolution_normalises(seed, name):
    assert neighbourhood_origin(name, seed.neighbourhoods).lat == 5.556


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"service": "ev_high_voltage"}, "unsupported_service"),  # MT-08, searchable false
        ({"service": "brake_service", "radius": 15}, "invalid_radius"),
        ({"service": "brake_service", "area": "Nkawkaw"}, "unknown_neighbourhood"),  # MT-10
    ],
)
def test_rejections(seed, kwargs, code):
    kwargs.setdefault("area", "Osu")
    with pytest.raises(MatchingError) as e:
        run(seed, kwargs.pop("service"), kwargs.pop("area"), **kwargs)
    assert e.value.code == code


@pytest.mark.parametrize(("lat", "lng"), [(91, 0), (0, -181), (math.nan, 0), (0, math.inf)])
def test_invalid_coordinates(lat, lng):
    with pytest.raises(MatchingError) as e:
        coordinates_origin(lat, lng)
    assert e.value.code == "invalid_coordinates"


def test_device_origin_precision_matches_contract():
    assert coordinates_origin(5.556, -0.182).precision == "device"
