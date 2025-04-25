from typing import Dict
from pydantic import BaseModel, Field, StrictStr


class CatalogConfig(BaseModel):
    """
    Server-provided configuration for the catalog.
    """  # noqa: E501

    overrides: Dict[str, StrictStr] = Field(
        description="Properties that should be used to override client configuration; applied after defaults and client configuration."
    )
    defaults: Dict[str, StrictStr] = Field(
        description="Properties that should be used as default configuration; applied before client configuration."
    )
