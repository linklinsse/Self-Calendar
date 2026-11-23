from pydantic import BaseModel

from app.schemas.common_fields import CommonFieldColor, CommonFieldIcon, CommonFieldTitle


class ObjCategorySchemaBase(BaseModel):
    title: CommonFieldTitle
    color: CommonFieldColor
    icon: CommonFieldIcon


class ObjCategorySchemaCreate(ObjCategorySchemaBase):
    calendar_id: str


class ObjCategorySchemaEdit(BaseModel):
    title: CommonFieldTitle | None = None
    color: CommonFieldColor
    icon: CommonFieldIcon
    calendar_id: str | None = None


class ObjCategorySchemaComplete(ObjCategorySchemaBase):
    id: str
    calendar_id: str
