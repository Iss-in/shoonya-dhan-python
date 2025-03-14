from pydantic import BaseModel
from datetime import date

class PlanSchema(BaseModel):
    date: date
    plan: str

    class Config:
        orm_mode = True  # Optional: allows compatibility with ORM models
