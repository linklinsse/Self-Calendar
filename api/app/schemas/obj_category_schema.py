from pydantic import BaseModel, Field

from app.schemas.common_fields import CommonFieldColor, CommonFieldTitle


class ObjCategorySchema(BaseModel):
    id: str | None = Field(default=None)
    user_id: str
    title: CommonFieldTitle
    color: CommonFieldColor
    description: str | None = Field(default=None)
