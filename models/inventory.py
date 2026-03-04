from pydantic import BaseModel
from datetime import datetime


class InventoryAdjust(BaseModel):
    bags: float  # Positive to add, negative to subtract
    reason: str = ""


class InventoryInDB(BaseModel):
    item: str
    bags: float
    updated_at: datetime
