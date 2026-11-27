from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.reminders.models import RuleApplicability
from app.modules.vehicles.models import Vehicle, VehicleModel


def list_models(db: Session, make: str | None, model: str | None) -> list[VehicleModel]:
    q = select(VehicleModel).order_by(VehicleModel.make, VehicleModel.model, VehicleModel.year_from)
    if make:
        q = q.where(func.lower(VehicleModel.make) == make.lower())
    if model:
        q = q.where(func.lower(VehicleModel.model) == model.lower())
    return list(db.scalars(q))


def get_model(db: Session, catalogue_id: str) -> VehicleModel | None:
    return db.get(VehicleModel, catalogue_id)


def find_catalogue_match(db: Session, make: str, model: str, year: int) -> list[VehicleModel]:
    """Catalogue rows for this make/model whose year band contains `year` (powertrain checked
    by the caller, since `powertrains` is a JSON list)."""
    return list(
        db.scalars(
            select(VehicleModel).where(
                func.lower(VehicleModel.make) == make.lower(),
                func.lower(VehicleModel.model) == model.lower(),
                VehicleModel.year_from <= year,
                VehicleModel.year_to >= year,
            )
        )
    )


def has_exact_rule(db: Session, v: Vehicle) -> bool:
    """True if any rule's applicability matches this exact configuration (rule spec)."""
    if v.catalogue_id is None:
        return False
    return (
        db.scalar(
            select(RuleApplicability.id)
            .where(
                RuleApplicability.catalogue_id == v.catalogue_id,
                RuleApplicability.market == v.source_market,
                RuleApplicability.powertrain == v.powertrain,
                RuleApplicability.body_style == v.body_style,
                RuleApplicability.year_from <= v.model_year,
                RuleApplicability.year_to >= v.model_year,
            )
            .limit(1)
        )
        is not None
    )


def list_for_owner(
    db: Session, owner_id: int, offset: int, limit: int
) -> tuple[list[Vehicle], int]:
    where = Vehicle.owner_id == owner_id
    total = db.scalar(select(func.count()).select_from(Vehicle).where(where))
    rows = db.scalars(select(Vehicle).where(where).order_by(Vehicle.id).offset(offset).limit(limit))
    return list(rows), total


def get_owned(db: Session, owner_id: int, vehicle_id: int) -> Vehicle | None:
    v = db.get(Vehicle, vehicle_id)
    return v if v and v.owner_id == owner_id else None
