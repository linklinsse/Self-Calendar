from typing import List
from app.schemas.obj_event_schema import ObjEventSchemaComplete, ObjEventSchemaCreate, ObjEventSchemaEdit

#TODO
def create_event(new_event: ObjEventSchemaCreate) -> ObjEventSchemaComplete:
    return None

def get_all_event_between() -> List[ObjEventSchemaComplete]:
    return []

def get_event(event_id: str) -> ObjEventSchemaComplete:
    return None

def edit_event(event_id: str, edited_event: ObjEventSchemaEdit) -> ObjEventSchemaComplete:
    return None

def delete_event(event_id: str):
    return None
