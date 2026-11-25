"""Stub routes (contract v1). Real logic: mechanics/matching.py (#45) + service layer."""

from datetime import UTC, date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Query, status

from app.core.auth import BearerToken
from app.core.errors import ERRORS
from app.core.pagination import Page, Paging
from app.modules.mechanics.schemas import (
    AdminMechanicOut,
    AssessmentIn,
    AvailabilityIn,
    AvailabilityOut,
    ComplaintIn,
    ComplaintOut,
    ComplaintPatch,
    ContactOut,
    MechanicProfile,
    MechanicServiceOut,
    NeighbourhoodOut,
    SearchResponse,
    SearchResult,
    ServiceCategoryOut,
)

router = APIRouter(tags=["mechanics"], responses=ERRORS)
admin = APIRouter(prefix="/admin", tags=["admin"], responses=ERRORS)

_AT = datetime(2026, 11, 23, 6, tzinfo=UTC)
_AVAIL = AvailabilityOut(status="available", reported_status="available", reported_at=_AT)
_M01_RESULT = SearchResult(
    id="M01",
    name="DEMO - Kojo Auto Works",
    neighbourhood="Osu",
    distance_km=0.0,
    availability=_AVAIL,
    assessment_status="assessed",
    service_verification="assessed",
    assessed_on=date(2026, 11, 15),
    is_demo=True,
)
_M01 = MechanicProfile(
    id="M01",
    name="DEMO - Kojo Auto Works",
    neighbourhood="Osu",
    service_radius_km=10,
    assessment_status="assessed",
    assessed_on=date(2026, 11, 15),
    assessor="Nkenten demo assessor (fictional)",
    assessment_basis="Fictional sprint fixture. Service-specific practical assessment.",
    assessed_services=[
        MechanicServiceOut(
            category="brake_service",
            label="Brake service",
            verification="assessed",
            assessed_on=date(2026, 11, 15),
        ),
    ],
    other_services=[
        MechanicServiceOut(
            category="diagnostics",
            label="Diagnostics",
            verification="self_reported",
            assessed_on=None,
        ),
    ],
    availability=_AVAIL,
    contact=ContactOut(mode="demo_dialog", display_name="DEMO - Kojo Auto Works", phone=None),
    is_demo=True,
)
_ADMIN_M01 = AdminMechanicOut(
    **_M01.model_dump(), published=True, suspension_reason=None, history=[]
)
_COMPLAINT = ComplaintOut(
    id=1,
    mechanic_id="M08",
    description="Demo complaint",
    mechanic_response=None,
    status="open",
    created_at=_AT,
    resolved_at=None,
)


@router.get("/service-categories")
def list_service_categories() -> list[ServiceCategoryOut]:
    return [ServiceCategoryOut(id="brake_service", label="Brake service", searchable=True)]


@router.get("/neighbourhoods")
def list_neighbourhoods() -> list[NeighbourhoodOut]:
    """Names only; centroids stay server-side."""
    return [NeighbourhoodOut(name="Osu")]


@router.get("/mechanics/search")
def search_mechanics(
    service: Annotated[str, Query(examples=["brake_service"])],
    neighbourhood: str | None = None,
    lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    lng: Annotated[float | None, Query(ge=-180, le=180)] = None,
    radius_km: Literal[10, 20, 40] = 10,
    include_unavailable: bool = False,
) -> SearchResponse:
    """US-08, US-09, US-10. Exactly one origin: `neighbourhood` or both `lat`+`lng` (else 422).
    400 `unsupported_service` (incl. ev_high_voltage) or `unknown_neighbourhood` (+ suggestions).
    Coordinates are never stored or logged.
    """
    return SearchResponse(
        service=service,
        radius_km=radius_km,
        origin_precision="neighbourhood" if neighbourhood else "device",
        assessed=[_M01_RESULT],
        not_assessed=[],
        suggest_radius_km=None,
        hidden_unavailable=1,
        message=None,
    )


@router.get("/mechanics/{mechanic_id}")
def get_mechanic(mechanic_id: str) -> MechanicProfile:
    """US-11. 404 for suspended/unpublished, and for demo records outside demo mode."""
    return _M01


@router.put("/mechanics/{mechanic_id}/availability")
def report_availability(mechanic_id: str, body: AvailabilityIn, _: BearerToken) -> AvailabilityOut:
    """US-13. The mechanic (own listing) or an admin. Server sets reported_at; change is logged."""
    return AvailabilityOut(status=body.status, reported_status=body.status, reported_at=_AT)


@admin.get("/mechanics")
def admin_list_mechanics(
    _: BearerToken, page: Paging, status_filter: str | None = Query(None, alias="status")
) -> Page[AdminMechanicOut]:
    """Admin only. Includes suspended, unpublished and demo records."""
    return Page(items=[_ADMIN_M01], page=page.page, page_size=page.page_size, total=1)


@admin.get("/mechanics/{mechanic_id}")
def admin_get_mechanic(mechanic_id: str, _: BearerToken) -> AdminMechanicOut:
    """MT-14: admins can open suspended listings and see change history."""
    return _ADMIN_M01


@admin.put("/mechanics/{mechanic_id}/assessment")
def admin_update_assessment(
    mechanic_id: str, body: AssessmentIn, _: BearerToken
) -> AdminMechanicOut:
    """US-12, US-14. Suspension removes the listing from search immediately. Every change logged."""
    return _ADMIN_M01


@admin.get("/mechanics/{mechanic_id}/complaints")
def admin_list_complaints(mechanic_id: str, _: BearerToken) -> list[ComplaintOut]:
    return [_COMPLAINT]


@admin.post("/mechanics/{mechanic_id}/complaints", status_code=status.HTTP_201_CREATED)
def admin_create_complaint(mechanic_id: str, body: ComplaintIn, _: BearerToken) -> ComplaintOut:
    """US-14."""
    return _COMPLAINT


@admin.patch("/complaints/{complaint_id}")
def admin_update_complaint(complaint_id: int, body: ComplaintPatch, _: BearerToken) -> ComplaintOut:
    """Attach the mechanic's response and/or resolve. Upholding does not auto-suspend."""
    return _COMPLAINT
