"""Vehicle catalogue and a driver's vehicles (US-02, #50)."""

from fastapi import APIRouter, Response, status

from app.core.db import DbSession
from app.core.errors import ERRORS
from app.core.pagination import Page, Paging
from app.modules.auth.deps import CurrentUser
from app.modules.vehicles import service
from app.modules.vehicles.schemas import VehicleIn, VehicleModelOut, VehicleOut, VehiclePatch

router = APIRouter(tags=["vehicles"], responses=ERRORS)


@router.get("/vehicle-models")
def list_vehicle_models(
    db: DbSession, make: str | None = None, model: str | None = None
) -> list[VehicleModelOut]:
    """Catalogue for the register-vehicle picker. Small, so not paginated."""
    return service.list_models(db, make, model)


@router.get("/vehicles")
def list_vehicles(user: CurrentUser, db: DbSession, page: Paging) -> Page[VehicleOut]:
    """The caller's own vehicles only (AC-02). Empty garage = `items: []`."""
    return service.list_for_owner(db, user.id, page)


@router.post("/vehicles", status_code=status.HTTP_201_CREATED)
def create_vehicle(body: VehicleIn, user: CurrentUser, db: DbSession) -> VehicleOut:
    """US-02. Matches the catalogue (or stores a manual car) and records the first odometer
    reading. `reminder_support: limited` => tell the driver reminders may be limited.
    400 `unknown_catalogue_id` / `catalogue_mismatch`; 422 negative or missing odometer."""
    return service.create(db, user.id, body)


@router.get("/vehicles/{vehicle_id}")
def get_vehicle(vehicle_id: int, user: CurrentUser, db: DbSession) -> VehicleOut:
    """404 if missing *or* owned by someone else (no existence leak)."""
    return service.to_out(db, service.get(db, user.id, vehicle_id))


@router.patch("/vehicles/{vehicle_id}")
def update_vehicle(
    vehicle_id: int, body: VehiclePatch, user: CurrentUser, db: DbSession
) -> VehicleOut:
    return service.update(db, user.id, vehicle_id, body)


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(vehicle_id: int, user: CurrentUser, db: DbSession) -> Response:
    service.delete(db, user.id, vehicle_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
