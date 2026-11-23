from uuid import uuid4

from sqlmodel import Field, SQLModel


class ObjCategoryModel(SQLModel, table=True):
    __tablename__ = "obj_category"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
    )
    calendar_id: str = Field(foreign_key="obj_calendar.id")
    title: str = Field(max_length=255)
    color: str | None = Field(default=None, max_length=7)
    # Emoji shown next to the category label. NULL = the client's default
    # icon (categories created before this column existed).
    icon: str | None = Field(default=None, max_length=16)
