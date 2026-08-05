from uuid import uuid4
from sqlmodel import Field, SQLModel


class ObjUserModel(SQLModel, table=True):
    """Database model for an application user."""

    __tablename__ = "obj_user"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    username: str = Field(nullable=False, unique=True, index=True)
    disabled: bool = Field(nullable=False, default=False, index=True)
    hashed_password: str = Field(nullable=False)
    token_version: int = Field(nullable=False, default=0)
