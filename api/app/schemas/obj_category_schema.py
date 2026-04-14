from pydantic import BaseModel


class ObjCategorySchemaBase(BaseModel):
    title: str
    color: str | None = None


class ObjCategorySchemaCreate(ObjCategorySchemaBase):
    calendar_id: str


class ObjCategorySchemaEdit(BaseModel):
    title: str | None = None
    color: str | None = None


class ObjCategorySchemaComplete(ObjCategorySchemaBase):
    id: str
    calendar_id: str
