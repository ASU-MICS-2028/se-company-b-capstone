from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.core.types import Km

ServiceKey = Literal[
    "engine_oil_and_filter",
    "engine_oil",
    "tyre_rotation",
    "brake_inspection",
    "cabin_air_filter",
    "engine_air_filter",
    "brake_fluid",
    "other",
]


class OdometerIn(BaseModel):
    odometer_km: Km = Field(ge=0, max_digits=9, decimal_places=1, examples=[53000])
    read_at: datetime | None = Field(None, description="Defaults to now. Future rejected.")
    confirm_lower: bool = Field(
        False, description="Must be true to save a reading lower than the latest (US-04)"
    )


class OdometerOut(BaseModel):
    id: int
    odometer_km: Km
    read_at: datetime
    source: Literal["manual", "obd"]


class ServiceLogIn(BaseModel):
    """US-04. A combined engine+cabin filter job is sent as two service_keys."""

    service_keys: list[ServiceKey] = Field(min_length=1, examples=[["engine_oil_and_filter"]])
    service_date: date = Field(description="Future dates rejected (400 `future_date`)")
    odometer_km: Km | None = Field(None, ge=0, max_digits=9, decimal_places=1)
    confirm_lower: bool = Field(False, description="Required if odometer_km < latest reading")
    oil_meets_spec: bool | None = None
    minder_reset_on: date | None = Field(None, description="Honda Minder reset (R09)")
    notes: str | None = Field(None, max_length=500)


class ServiceLogOut(BaseModel):
    id: int
    service_key: ServiceKey
    service_date: date
    odometer_km: Km | None
    confirmed: bool
    oil_meets_spec: bool | None
    minder_reset_on: date | None
    notes: str | None
    created_at: datetime
