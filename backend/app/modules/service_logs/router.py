"""Stub routes (contract v1). Real logic: #50."""

from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import APIRouter, status

from app.core.auth import BearerToken
from app.core.errors import ERRORS
from app.core.pagination import Page, Paging
from app.modules.service_logs.schemas import OdometerIn, OdometerOut, ServiceLogIn, ServiceLogOut

router = APIRouter(prefix="/vehicles/{vehicle_id}", tags=["service logs"], responses=ERRORS)

_NOW = datetime(2026, 11, 21, 9, tzinfo=UTC)
_LOG = ServiceLogOut(
    id=1,
    service_key="engine_oil_and_filter",
    service_date=date(2026, 6, 1),
    odometer_km=Decimal("40000"),
    confirmed=True,
    oil_meets_spec=True,
    minder_reset_on=None,
    notes="0W-16 synthetic",
    created_at=_NOW,
)
_READING = OdometerOut(id=1, odometer_km=Decimal("48000"), read_at=_NOW, source="manual")


@router.get("/service-logs")
def list_service_logs(vehicle_id: int, _: BearerToken, page: Paging) -> Page[ServiceLogOut]:
    """History, newest first (service_date desc, then id desc)."""
    return Page(items=[_LOG], page=page.page, page_size=page.page_size, total=1)


@router.post("/service-logs", status_code=status.HTTP_201_CREATED)
def create_service_log(vehicle_id: int, body: ServiceLogIn, _: BearerToken) -> list[ServiceLogOut]:
    """US-04. One row per service_key. 409 `odometer_lower_than_latest` unless confirm_lower."""
    return [_LOG]


@router.get("/odometer-readings")
def list_odometer_readings(vehicle_id: int, _: BearerToken, page: Paging) -> Page[OdometerOut]:
    return Page(items=[_READING], page=page.page, page_size=page.page_size, total=1)


@router.post("/odometer-readings", status_code=status.HTTP_201_CREATED)
def create_odometer_reading(vehicle_id: int, body: OdometerIn, _: BearerToken) -> OdometerOut:
    """409 `odometer_lower_than_latest` unless confirm_lower. 400 `future_reading`."""
    return _READING
