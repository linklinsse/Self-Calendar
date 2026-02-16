from pydantic import Field
from typing import Annotated

CommonFieldColor = Annotated[
    str | None, Field(default=None, pattern="^#(?:[0-9a-fA-F]{3}){1,2}$")
]
CommonFieldTitle = Annotated[str, Field(max_length=255)]
