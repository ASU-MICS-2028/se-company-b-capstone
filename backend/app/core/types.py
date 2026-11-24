from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer

# Exact decimal internally (thresholds like 16093.44 km), JSON number on the wire.
Km = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]
