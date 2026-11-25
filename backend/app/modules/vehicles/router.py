"""Stub routes (contract v1). Real logic: #50."""

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Response, status

from app.core.auth import BearerToken
from app.core.errors import ERRORS
from app.core.pagination import Page, Paging
from app.modules.vehicles.schemas import VehicleIn, VehicleModelOut, VehicleOut, VehiclePatch

router = APIRouter(tags=["vehicles"], responses=ERRORS)

_V03 = VehicleModelOut(
    catalogue_id="V03",
    make="Toyota",
    model="Corolla",
    year_from=2023,
    year_to=2025,
    powertrains=["petrol", "hybrid"],
    rules_supported=True,
    note=None,
)
_CAR = VehicleOut(
    id=1,
    catalogue_id="V03",
    make="Toyota",
    model="Corolla",
    model_year=2025,
    powertrain="petrol",
    body_style="sedan",
    source_market="US",
    driving_condition="normal",
    regular_dusty_gravel_or_visible_soot=None,
    last_oil_meets_spec=True,
    handbook_confirmed=True,
    nickname=None,
    reminder_support="supported",
    latest_odometer_km=Decimal("48000"),
    latest_odometer_at=datetime(2026, 11, 21, 9, tzinfo=UTC),
)


@router.get("/vehicle-models")
def list_vehicle_models(make: str | None = None, model: str | None = None) -> list[VehicleModelOut]:
    """Catalogue for the register-vehicle picker. Small, so not paginated."""
    return [_V03]


@router.get("/vehicles")
def list_vehicles(_: BearerToken, page: Paging) -> Page[VehicleOut]:
    """The caller's own vehicles only (AC-02)."""
    return Page(items=[_CAR], page=page.page, page_size=page.page_size, total=1)


@router.post("/vehicles", status_code=status.HTTP_201_CREATED)
def create_vehicle(body: VehicleIn, _: BearerToken) -> VehicleOut:
    """US-02. Also records the first odometer reading. 400 `unknown_catalogue_id`."""
    return _CAR


@router.get("/vehicles/{vehicle_id}")
def get_vehicle(vehicle_id: int, _: BearerToken) -> VehicleOut:
    """404 if missing *or* owned by someone else (no existence leak)."""
    return _CAR


@router.patch("/vehicles/{vehicle_id}")
def update_vehicle(vehicle_id: int, body: VehiclePatch, _: BearerToken) -> VehicleOut:
    return _CAR


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(vehicle_id: int, _: BearerToken) -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)
