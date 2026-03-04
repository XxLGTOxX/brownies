from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ExpenseCreate(BaseModel):
    description: str
    amount: float
    date: str  # "YYYY-MM-DD"


class ExpenseInDB(BaseModel):
    id: str
    description: str
    amount: float
    date: datetime
    created_at: datetime
