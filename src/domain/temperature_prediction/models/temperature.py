from pydantic import BaseModel


class Temperature(BaseModel):
    hour: int
    day: int
    month: int
    year: int
    out_in: int