from pydantic import Field
from typing import Annotated

CommonFieldColor = Annotated[
    str | None, Field(default=None, pattern="^#(?:[0-9a-fA-F]{3}){1,2}$")
]
CommonFieldTitle = Annotated[str, Field(max_length=255)]
# Unbounded description fields + no request body size limit is an easy
# storage-exhaustion vector on a self-hosted SQLite instance.
CommonFieldDescription = Annotated[str | None, Field(default=None, max_length=2000)]
