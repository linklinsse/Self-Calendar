from pydantic import BaseModel, Field


class ObjUserSchemaComplete(BaseModel):
    id: str
    login: str
    hashed_password: str
