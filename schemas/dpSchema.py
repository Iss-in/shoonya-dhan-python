from pydantic import BaseModel
from datetime import date

class DpSchema(BaseModel):
    date: date
    name: str
    value: float
    call: bool
    put: bool

    class Config:
        orm_mode = True  # Optional: allows compatibility with ORM models
