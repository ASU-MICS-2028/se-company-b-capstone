"""Mechanic matching engine v1 (docs/rules/02-mechanic-matching-spec.md).

Pure and deterministic: no database, no clock. The caller passes a snapshot of
listings and the evaluation time, so the same inputs always give the same lists.
The router maps ``MatchingError`` codes to HTTP 422 / 400.
"""

from __future__ import annotations

import math
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

EARTH_RADIUS_KM = 6371.0
RADIUS_STEPS_KM = (10, 20, 40)
DEFAULT_RADIUS_KM = 10
FRESHNESS = timedelta(hours=24)
AVAILABILITY_STATUSES = frozenset({"available", "busy", "unavailable"})
UNKNOWN = "unknown"


class MatchingError(ValueError):
    """Rejected request. ``code`` is stable so the router can map it to an HTTP status."""

    def __init__(self, code: str, message: str, suggestions: tuple[str, ...] = ()):
        super().__init__(message)
        self.code = code
        self.suggestions = suggestions


# --- Input data -------------------------------------------------------------------------


@dataclass(frozen=True)
class ServiceCategory:
    id: str
    label: str
    searchable: bool


@dataclass(frozen=True)
class Neighbourhood:
    name: str
    lat: float
    lng: float


@dataclass(frozen=True)
class Listing:
    id: str
    name: str
    neighbourhood: str
    lat: float | None
    lng: float | None
    service_radius_km: float | None
    assessment_status: str  # assessed | pending | self_reported | suspended
    assessed_on: str | None
    services: Mapping[str, str]  # category id -> verification (assessed | self_reported)
    availability_status: str | None
    availability_updated_at: datetime | None
    is_demo: bool
    published: bool


@dataclass(frozen=True)
class Origin:
    lat: float
    lng: float
    precision: str  # "neighbourhood" | "device" (API contract #68)


# --- Output -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Match:
    mechanic_id: str
    name: str
    neighbourhood: str
    distance_km: Decimal  # half-up to 0.1 km, used for display and ranking
    distance_km_exact: float  # used for both radius filters
    availability: str  # available | busy | unavailable | unknown
    reported_at: datetime | None  # last valid, non-future report (kept when stale)
    assessment_status: str
    service_verification: str
    assessed_on: str | None
    is_demo: bool


@dataclass(frozen=True)
class SearchResult:
    service: str
    radius_km: int
    origin_precision: str
    evaluated_at: datetime
    assessed: tuple[Match, ...]
    not_assessed: tuple[Match, ...]
    suggest_radius_km: int | None
    hidden_unavailable: int  # currently unavailable candidates left out by the filter
    message: str | None


# --- Helpers ----------------------------------------------------------------------------


def _normalise(name: str) -> str:
    return unicodedata.normalize("NFKC", name).strip().casefold()


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance, Earth radius 6,371 km, intermediate value clamped to [0, 1]."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    a = min(1.0, max(0.0, a))
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def round_km(distance_km: float) -> Decimal:
    """Half-up decimal rounding to 0.1 km (not float banker's rounding)."""
    return Decimal(repr(distance_km)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def effective_availability(listing: Listing, now: datetime) -> tuple[str, datetime | None]:
    """Resolve availability at ``now``. Returns (status, last valid report time).

    A valid status reported at most 24 h ago (inclusive) is current. Missing, invalid,
    future-dated or older reports are ``unknown``. A stale report keeps its timestamp.
    """
    ts = listing.availability_updated_at
    if ts is None or ts > now:
        return UNKNOWN, None
    if listing.availability_status not in AVAILABILITY_STATUSES:
        return UNKNOWN, None
    if now - ts <= FRESHNESS:
        return listing.availability_status, ts
    return UNKNOWN, ts


def resolve_neighbourhood(name: str, neighbourhoods: Iterable[Neighbourhood]) -> Neighbourhood:
    """Trim, NFKC-normalise and case-fold, then match against the supported list."""
    known = list(neighbourhoods)
    wanted = _normalise(name)
    for n in known:
        if _normalise(n.name) == wanted:
            return n
    suggestions = tuple(n.name for n in known if wanted and wanted[:3] in _normalise(n.name))
    raise MatchingError("unknown_neighbourhood", f"Unknown neighbourhood: {name!r}",
                        suggestions or tuple(n.name for n in known))


def coordinates_origin(lat: float, lng: float) -> Origin:
    if not (math.isfinite(lat) and math.isfinite(lng)) or not (
        -90 <= lat <= 90 and -180 <= lng <= 180
    ):
        raise MatchingError("invalid_coordinates", "Latitude or longitude out of range")
    return Origin(lat, lng, "device")


def neighbourhood_origin(name: str, neighbourhoods: Iterable[Neighbourhood]) -> Origin:
    n = resolve_neighbourhood(name, neighbourhoods)
    return Origin(n.lat, n.lng, "neighbourhood")


# --- Search -----------------------------------------------------------------------------


def _sort_key(m: Match) -> tuple:
    # Distance (rounded), then newest report first with missing last, then stable ID.
    newest_first = -m.reported_at.timestamp() if m.reported_at else math.inf
    return (m.distance_km, newest_first, m.mechanic_id)


def search(
    listings: Iterable[Listing],
    categories: Mapping[str, ServiceCategory],
    *,
    service: str,
    origin: Origin,
    radius_km: int = DEFAULT_RADIUS_KM,
    include_unavailable: bool = False,
    now: datetime,
    demo_mode: bool,
) -> SearchResult:
    """Filter and rank one snapshot of listings at a single evaluation time ``now`` (UTC)."""
    if radius_km not in RADIUS_STEPS_KM:
        raise MatchingError("invalid_radius", f"Radius must be one of {RADIUS_STEPS_KM} km")
    category = categories.get(service)
    if category is None or not category.searchable:
        raise MatchingError("unsupported_service", f"Unsupported service: {service!r}")

    assessed: list[Match] = []
    not_assessed: list[Match] = []
    hidden_unavailable = 0

    for li in listings:
        if not li.published or li.assessment_status == "suspended":
            continue
        if li.is_demo and not demo_mode:
            continue
        verification = li.services.get(service)
        if verification is None:
            continue
        if li.lat is None or li.lng is None or not li.service_radius_km:
            continue

        distance = haversine_km(origin.lat, origin.lng, li.lat, li.lng)
        if distance > radius_km or distance > li.service_radius_km:  # equality passes
            continue

        availability, reported_at = effective_availability(li, now)
        if availability == "unavailable" and not include_unavailable:
            hidden_unavailable += 1
            continue

        match = Match(
            mechanic_id=li.id,
            name=li.name,
            neighbourhood=li.neighbourhood,
            distance_km=round_km(distance),
            distance_km_exact=distance,
            availability=availability,
            reported_at=reported_at,
            assessment_status=li.assessment_status,
            service_verification=verification,
            assessed_on=li.assessed_on,
            is_demo=li.is_demo,
        )
        if li.assessment_status == "assessed" and verification == "assessed":
            assessed.append(match)
        else:
            not_assessed.append(match)

    assessed.sort(key=_sort_key)
    not_assessed.sort(key=_sort_key)

    suggest = None
    message = None
    if not assessed:
        message = f"No assessed mechanics for {category.label} within {radius_km} km."
        step = RADIUS_STEPS_KM.index(radius_km)
        if step + 1 < len(RADIUS_STEPS_KM):
            suggest = RADIUS_STEPS_KM[step + 1]
        elif not_assessed:
            message += " Self-reported and pending listings are shown separately."

    return SearchResult(
        service=service,
        radius_km=radius_km,
        origin_precision=origin.precision,
        evaluated_at=now,
        assessed=tuple(assessed),
        not_assessed=tuple(not_assessed),
        suggest_radius_km=suggest,
        hidden_unavailable=hidden_unavailable,
        message=message,
    )


# --- Seed adapter -----------------------------------------------------------------------


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else None  # naive timestamps are invalid


@dataclass(frozen=True)
class SeedSnapshot:
    reference_time: datetime | None
    categories: dict[str, ServiceCategory]
    neighbourhoods: tuple[Neighbourhood, ...]
    listings: tuple[Listing, ...]


def from_seed(data: Mapping[str, Any]) -> SeedSnapshot:
    """Build engine inputs from ``data/seed/mechanics.json``."""
    return SeedSnapshot(
        reference_time=parse_utc(data.get("seed_reference_time")),
        categories={
            c["id"]: ServiceCategory(c["id"], c["label"], bool(c.get("searchable", True)))
            for c in data["service_categories"]
        },
        neighbourhoods=tuple(
            Neighbourhood(n["name"], n["lat"], n["lng"]) for n in data["neighbourhoods"]
        ),
        listings=tuple(
            Listing(
                id=m["id"],
                name=m["name"],
                neighbourhood=m["neighbourhood"],
                lat=m.get("lat"),
                lng=m.get("lng"),
                service_radius_km=m.get("service_radius_km"),
                assessment_status=m["assessment_status"],
                assessed_on=m.get("assessed_on"),
                services={s["category"]: s["verification"] for s in m.get("services", [])},
                availability_status=m.get("availability_status"),
                availability_updated_at=parse_utc(m.get("availability_updated_at")),
                is_demo=bool(m.get("is_demo", False)),
                published=bool(m.get("published", False)),
            )
            for m in data["mechanics"]
        ),
    )
