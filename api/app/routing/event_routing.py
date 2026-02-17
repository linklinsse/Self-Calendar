from typing import List
from fastapi import APIRouter

from app.schemas.obj_event_schema import ObjEventSchemaComplete, ObjEventSchemaCreate, ObjEventSchemaEdit
from app.services import obj_event_service


router = APIRouter(prefix="/event")


@router.post("/", response_model=ObjEventSchemaComplete)
async def create(
    new_event: ObjEventSchemaCreate,
) -> ObjEventSchemaComplete:
    return obj_event_service.create_event(
        new_event,
    )


@router.get("/", response_model=List[ObjEventSchemaComplete])
async def get_all() -> List[ObjEventSchemaComplete]:
    return obj_event_service.get_all_event()


@router.get("/{event_id}", response_model=ObjEventSchemaComplete)
async def get(event_id: str) -> ObjEventSchemaComplete:
    return obj_event_service.get_event(
        event_id,
    )


@router.patch("/{event_id}", response_model=ObjEventSchemaComplete)
async def patch(
    event_id: str, edited_event: ObjEventSchemaEdit
) -> ObjEventSchemaComplete:
    return obj_event_service.edit_event(
        event_id,
        edited_event,
    )


@router.delete("/{event_id}")
async def delete(event_id: str):
    return obj_event_service.delete_event(
        event_id,
    )
