from pydantic import BaseModel, Field


class Message(BaseModel):
    """A message to publish on an MQTT topic."""

    topic: str = Field(min_length=1, max_length=256, examples=["sensors/room-admin/temperature"])
    payload: str = Field(max_length=65536, examples=["29.5"])
