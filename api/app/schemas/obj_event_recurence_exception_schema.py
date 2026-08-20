from pydantic import BaseModel

class ObjEventRecurenceExceptionSchema(BaseModel):
    id: str
    date: int