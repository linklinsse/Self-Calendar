from pydantic import BaseModel


class ObjCategoryBase(BaseModel):
    title: str
    color: str | None = None


class ObjCategoryCreate(ObjCategoryBase):
    calendar_id: str


class ObjCategoryUpdate(BaseModel):
    title: str | None = None
    color: str | None = None


class ObjCategoryRead(ObjCategoryBase):
    id: str
    calendar_id: str
