
from sqlmodel import Session, select

from app.models.obj_event_recurence_model import ObjEventRecurenceModel
from app.schemas.obj_event_recurence_schema import ObjEventRecurenceSchemaCreate, ObjEventRecurenceSchemaEdit

def create_event_recurence(
    new_recurence: ObjEventRecurenceSchemaCreate,
    session: Session,
) -> ObjEventRecurenceModel:
    db_recurence = ObjEventRecurenceModel.model_validate(new_recurence)
    session.add(db_recurence)
    session.commit()
    session.refresh(db_recurence)
    return db_recurence

def update_event_recurence(
    updated_recurence: ObjEventRecurenceSchemaEdit,
    session: Session,
) -> ObjEventRecurenceModel:
    recurence = session.get(ObjEventRecurenceModel, recurence_id)
    if recurence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurence not found",
        )

    patch_data = updated_recurence.model_dump(exclude_unset=True)
    for key, value in patch_data.items():
        setattr(recurence, key, value)

    session.add(recurence)
    session.commit()
    session.refresh(recurence)
    return recurence

def delete_event_recurence(
    recurence_id: str,
    session: Session,
) -> None:
    recurence = session.get(ObjEventRecurenceModel, recurence_id)
    if recurence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurence not found",
        )

    session.delete(recurence)
    session.commit()