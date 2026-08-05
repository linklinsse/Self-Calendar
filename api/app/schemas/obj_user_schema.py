from pydantic import BaseModel, Field
from typing import Annotated

# bcrypt hashes at most 72 bytes and the underlying library *raises* on
# anything longer rather than truncating, so an unbounded password field
# turns a long passphrase into an unhandled ValueError (HTTP 500) on both
# register and change-password. Reject it at the schema instead, as a 422.
# Truncating silently is not an option: it would make two different
# passwords equivalent.
CommonFieldPassword = Annotated[str, Field(min_length=12, max_length=72)]


class ObjUserSchemaComplete(BaseModel):
    id: str
    username: str

class ObjUserSchemaCreate(BaseModel):
    username: Annotated[str, Field(min_length=1, max_length=64)]
    password: CommonFieldPassword

class ObjUserSchemaChangePassword(BaseModel):
    old_password: str
    new_password: CommonFieldPassword
