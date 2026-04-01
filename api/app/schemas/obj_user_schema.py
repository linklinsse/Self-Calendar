from pydantic import BaseModel


class ObjUserSchemaComplete(BaseModel):
    id: str
    username: str
