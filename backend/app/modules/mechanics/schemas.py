from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

Verification = Literal["assessed", "self_reported", "pending"]
Availability = Literal["available", "busy", "unavailable", "unknown"]
AssessmentStatus = Literal["assessed", "pending", "self_reported", "suspended"]


class ServiceCategoryOut(BaseModel):
    id: str = Field(examples=["brake_service"])
    label: str
    searchable: bool


class NeighbourhoodOut(BaseModel):
    name: str = Field(examples=["Osu"])


class MechanicServiceOut(BaseModel):
    category: str
    label: str
    verification: Verification
    assessed_on: date | None


class AvailabilityOut(BaseModel):
    status: Availability = Field(description="Effective: reports older than 24 h become unknown")
    reported_status: Literal["available", "busy", "unavailable"] | None
    reported_at: datetime | None = Field(description="Show as 'updated X hours ago' (US-11)")


class SearchResult(BaseModel):
    id: str = Field(examples=["M01"])
    name: str
    neighbourhood: str
    distance_km: float = Field(description="Straight-line, rounded half-up to 0.1")
    availability: AvailabilityOut
    assessment_status: AssessmentStatus
    service_verification: Verification = Field(description="For the requested service")
    assessed_on: date | None
    is_demo: bool


class SearchResponse(BaseModel):
    """Matching spec, 'Request and result'."""

    service: str
    radius_km: Literal[10, 20, 40]
    origin_precision: Literal["neighbourhood", "device"]
    assessed: list[SearchResult]
    not_assessed: list[SearchResult] = Field(description="Collapsed section in the UI")
    suggest_radius_km: Literal[20, 40] | None = Field(description="Set when assessed is empty")
    hidden_unavailable: int = Field(
        0,
        description="Unavailable matches left out; drives the include-unavailable control",
    )
    message: str | None = Field(examples=["No assessed mechanics here yet"])


class ContactOut(BaseModel):
    mode: Literal["demo_dialog", "phone"]
    display_name: str
    phone: str | None = Field(description="Never set for demo records")


class MechanicProfile(BaseModel):
    """US-11. Assessed and self-reported services are listed separately."""

    id: str
    name: str
    neighbourhood: str
    service_radius_km: float
    assessment_status: AssessmentStatus
    assessed_on: date | None
    assessor: str | None
    assessment_basis: str | None
    assessed_services: list[MechanicServiceOut]
    other_services: list[MechanicServiceOut] = Field(description="Self-reported or pending")
    availability: AvailabilityOut
    contact: ContactOut
    is_demo: bool


# ---- admin ----


class ServiceAssessmentIn(BaseModel):
    """US-12: assessor and assessed_on required when verification is `assessed` (else 422)."""

    category: str
    verification: Verification
    assessor: str | None = None
    assessed_on: date | None = None


class AssessmentIn(BaseModel):
    assessment_status: AssessmentStatus
    assessed_on: date | None = None
    assessor: str | None = None
    assessment_basis: str | None = None
    suspension_reason: str | None = Field(None, description="Required when suspended")
    services: list[ServiceAssessmentIn] | None = None


class AvailabilityIn(BaseModel):
    """US-13. Admin or the mechanic themself. Timestamp is set by the server."""

    status: Literal["available", "busy", "unavailable"]


class ComplaintIn(BaseModel):
    description: str = Field(min_length=1, max_length=2000)


class ComplaintPatch(BaseModel):
    mechanic_response: str | None = Field(None, max_length=2000)
    status: Literal["open", "dismissed", "upheld"] | None = None


class ComplaintOut(BaseModel):
    id: int
    mechanic_id: str
    description: str
    mechanic_response: str | None
    status: Literal["open", "dismissed", "upheld"]
    created_at: datetime
    resolved_at: datetime | None


class MechanicChangeOut(BaseModel):
    field: str
    old_value: str | None
    new_value: str | None
    actor_id: int | None
    changed_at: datetime


class AdminMechanicOut(MechanicProfile):
    published: bool
    suspension_reason: str | None
    history: list[MechanicChangeOut]
