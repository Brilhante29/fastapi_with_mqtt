from pydantic import BaseModel

class Message(BaseModel):
    topic: str
    payload: str