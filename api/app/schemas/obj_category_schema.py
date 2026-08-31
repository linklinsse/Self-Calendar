from pydantic import BaseModel

from app.schemas.common_fields import CommonFieldColor, CommonFieldTitle


class ObjCategorySchemaBase(BaseModel):
    title: CommonFieldTitle
    color: CommonFieldColor


class ObjCategorySchemaCreate(ObjCategorySchemaBase):
    calendar_id: str


class ObjCategorySchemaEdit(BaseModel):
    title: CommonFieldTitle | None = None
    color: CommonFieldColor
    calendar_id: str | None = None


class ObjCategorySchemaComplete(ObjCategorySchemaBase):
    id: str
    calendar_id: str
