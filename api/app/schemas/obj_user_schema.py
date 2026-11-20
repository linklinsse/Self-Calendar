from pydantic import AfterValidator, BaseModel, Field
from typing import Annotated

# Defined here rather than in app.common.security (which uses it too) because
# security already imports this module — importing back would be circular.
BCRYPT_MAX_PASSWORD_BYTES = 72


def _fits_bcrypt(password: str) -> str:
    """bcrypt hashes at most 72 *bytes* — max_length counts characters.

    A 40-character password of accented letters is 80 bytes in UTF-8: it got
    past max_length=72 and the bcrypt library then raised (HTTP 500).
    """
    if len(password.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(
            f"password must be at most {BCRYPT_MAX_PASSWORD_BYTES} bytes "
            f"once UTF-8 encoded"
        )
    return password


# bcrypt hashes at most 72 bytes and the underlying library *raises* on
# anything longer rather than truncating, so an unbounded password field
# turns a long passphrase into an unhandled ValueError (HTTP 500) on both
# register and change-password. Reject it at the schema instead, as a 422.
# Truncating silently is not an option: it would make two different
# passwords equivalent.
CommonFieldPassword = Annotated[
    str, Field(min_length=12, max_length=72), AfterValidator(_fits_bcrypt)
]


class ObjUserSchemaComplete(BaseModel):
    id: str
    username: str

class ObjUserSchemaCreate(BaseModel):
    username: Annotated[str, Field(min_length=1, max_length=64)]
    password: CommonFieldPassword

class ObjUserSchemaChangePassword(BaseModel):
    old_password: str
    new_password: CommonFieldPassword
