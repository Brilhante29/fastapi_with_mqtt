from pydantic import BaseModel, Field


class Temperature(BaseModel):
    """Timestamp features of a reading; out_in is 0 for an indoor sensor and 1 for outdoor."""

    hour: int = Field(ge=0, le=23)
    day: int = Field(ge=1, le=31)
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)
    out_in: int = Field(ge=0, le=1)
