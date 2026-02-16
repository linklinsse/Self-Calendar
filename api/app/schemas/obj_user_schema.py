from pydantic import BaseModel


class ObjUserSchemaComplete(BaseModel):
    id: str
    login: str
    hashed_password: str
