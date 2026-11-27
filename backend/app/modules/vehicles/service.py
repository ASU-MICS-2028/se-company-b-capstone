"""Register and manage a driver's vehicles (US-02, #50)."""

from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.pagination import Page, PageParams
from app.modules.service_logs import service as odometer
from app.modules.vehicles import repository
from app.modules.vehicles.models import Vehicle, VehicleModel
from app.modules.vehicles.schemas import VehicleIn, VehicleModelOut, VehicleOut, VehiclePatch

# Columns that can't be null: an explicit null in a PATCH means "leave unchanged".
REQUIRED_ON_PATCH = {"body_style", "source_market", "driving_condition", "handbook_confirmed"}


def list_models(db: Session, make: str | None, model: str | None) -> list[VehicleModelOut]:
    return [
        VehicleModelOut.model_validate(m, from_attributes=True)
        for m in repository.list_models(db, make, model)
    ]


def _resolve_catalogue(db: Session, body: VehicleIn) -> VehicleModel | None:
    """Explicit catalogue_id must exist and fit the car; otherwise auto-match or go manual."""
    if body.catalogue_id:
        row = repository.get_model(db, body.catalogue_id)
        if row is None:
            raise ApiError(400, "unknown_catalogue_id", f"No catalogue entry {body.catalogue_id}")
        fits = (
            row.make.lower() == body.make.lower()
            and row.model.lower() == body.model.lower()
            and row.year_from <= body.model_year <= row.year_to
            and body.powertrain in row.powertrains
        )
        if not fits:
            raise ApiError(
                400,
                "catalogue_mismatch",
                f"{body.catalogue_id} doesn't cover a {body.model_year} {body.make} "
                f"{body.model} ({body.powertrain})",
            )
        return row
    matches = repository.find_catalogue_match(db, body.make, body.model, body.model_year)
    return next((m for m in matches if body.powertrain in m.powertrains), None)


def to_out(db: Session, v: Vehicle) -> VehicleOut:
    latest = odometer.latest_reading(db, v.id)
    return VehicleOut(
        **{f: getattr(v, f) for f in VehicleOut.model_fields if hasattr(v, f)},
        reminder_support="supported" if repository.has_exact_rule(db, v) else "limited",
        latest_odometer_km=latest.odometer_km if latest else None,
        latest_odometer_at=latest.read_at if latest else None,
    )


def create(db: Session, owner_id: int, body: VehicleIn) -> VehicleOut:
    row = _resolve_catalogue(db, body)
    v = Vehicle(
        owner_id=owner_id,
        catalogue_id=row.catalogue_id if row else None,
        # Use the catalogue's spelling for matched cars so later rule lookups are exact.
        make=row.make if row else body.make,
        model=row.model if row else body.model,
        **body.model_dump(exclude={"catalogue_id", "make", "model", "odometer_km"}),
    )
    db.add(v)
    db.flush()
    odometer.record_reading(db, v.id, body.odometer_km)
    db.commit()
    return to_out(db, v)


def list_for_owner(db: Session, owner_id: int, page: PageParams) -> Page[VehicleOut]:
    rows, total = repository.list_for_owner(
        db, owner_id, (page.page - 1) * page.page_size, page.page_size
    )
    items = [to_out(db, v) for v in rows]
    return Page(items=items, page=page.page, page_size=page.page_size, total=total)


def get(db: Session, owner_id: int, vehicle_id: int) -> Vehicle:
    """Someone else's vehicle is a 404, not a 403, so IDs don't leak (AC-02)."""
    v = repository.get_owned(db, owner_id, vehicle_id)
    if v is None:
        raise ApiError(404, "not_found", "Vehicle not found")
    return v


def update(db: Session, owner_id: int, vehicle_id: int, body: VehiclePatch) -> VehicleOut:
    v = get(db, owner_id, vehicle_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        if value is None and field in REQUIRED_ON_PATCH:
            continue
        setattr(v, field, value)
    db.commit()
    return to_out(db, v)


def delete(db: Session, owner_id: int, vehicle_id: int) -> None:
    db.delete(get(db, owner_id, vehicle_id))  # readings, logs, snoozes cascade (FK)
    db.commit()
