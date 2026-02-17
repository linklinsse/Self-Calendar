from typing import List
from app.models.obj_calendar_model import ObjCalendarModel
from app.models.obj_user_model import ObjUserModel


right_order: List[str] = [
    'C',
    'P',
    'O'
]

def verif_user_right_calendar(
    db_user: ObjUserModel,
    db_calendar: ObjCalendarModel,
    needed_right: str = 'C'
) -> bool:
    needed_right_level = right_order.index(needed_right)

    for db_lnk_user in db_calendar.lnk_users:
        if db_lnk_user.user_id == db_user.id:
            print("right", right_order.index(db_lnk_user.right), needed_right_level)
            if right_order.index(db_lnk_user.right) >= needed_right_level:
                return True
            break

    return False