from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.types import Km

Powertrain = Literal["petrol", "diesel", "hybrid", "plug_in_hybrid", "electric"]
BodyStyle = Literal["sedan", "hatchback", "suv", "other", "unknown"]
SourceMarket = Literal["US", "CA", "GH", "OTHER", "UNKNOWN"]
DrivingCondition = Literal["normal", "primarily_dirt_or_dusty", "other_special_use", "unknown"]


class VehicleModelOut(BaseModel):
    catalogue_id: str = Field(examples=["V03"])
    make: str
    model: str
    year_from: int
    year_to: int
    powertrains: list[Powertrain]
    rules_supported: bool
    note: str | None


class VehicleIn(BaseModel):
    """US-02. Omit catalogue_id and the server matches make, model, year and powertrain against
    the catalogue; no match = manual vehicle (`catalogue_id` null, reminders limited)."""

    catalogue_id: str | None = Field(None, examples=["V03"])
    make: str = Field(min_length=1, max_length=40, examples=["Toyota"])
    model: str = Field(min_length=1, max_length=40, examples=["Corolla"])

    @field_validator("make", "model")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @field_validator("nickname")
    @classmethod
    def _blank_nickname_is_none(cls, v: str | None) -> str | None:
        return v.strip() or None if v else None

    model_year: int = Field(ge=1980, le=2100, examples=[2025])
    powertrain: Powertrain
    body_style: BodyStyle = "unknown"
    source_market: SourceMarket = "UNKNOWN"
    driving_condition: DrivingCondition = "unknown"
    regular_dusty_gravel_or_visible_soot: bool | None = None
    last_oil_meets_spec: bool | None = None
    handbook_confirmed: bool = False
    nickname: str | None = Field(None, max_length=40)
    odometer_km: Km = Field(ge=0, max_digits=9, decimal_places=1, examples=[48000])


class VehiclePatch(BaseModel):
    """Partial update; same fields as VehicleIn except odometer (use odometer-readings)."""

    body_style: BodyStyle | None = None
    source_market: SourceMarket | None = None
    driving_condition: DrivingCondition | None = None
    regular_dusty_gravel_or_visible_soot: bool | None = None
    last_oil_meets_spec: bool | None = None
    handbook_confirmed: bool | None = None
    nickname: str | None = Field(None, max_length=40)


class VehicleOut(BaseModel):
    id: int
    catalogue_id: str | None
    make: str
    model: str
    model_year: int
    powertrain: Powertrain
    body_style: BodyStyle
    source_market: SourceMarket
    driving_condition: DrivingCondition
    regular_dusty_gravel_or_visible_soot: bool | None
    last_oil_meets_spec: bool | None
    handbook_confirmed: bool
    nickname: str | None
    reminder_support: Literal["supported", "limited"] = Field(
        description="`limited` for manual or catalogue-only vehicles (US-02 message)"
    )
    latest_odometer_km: Km | None
    latest_odometer_at: datetime | None
