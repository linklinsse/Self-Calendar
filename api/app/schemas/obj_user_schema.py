from pydantic import BaseModel


class ObjUserSchemaComplete(BaseModel):
    id: str
    username: str

class ObjUserSchemaCreate(BaseModel):
    username: str
    password: str

class ObjUserSchemaChangePassword(BaseModel):
    user_id: str
    old_password: str
    new_password: str
