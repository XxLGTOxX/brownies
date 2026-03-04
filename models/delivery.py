from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DeliveryCreate(BaseModel):
    client_id: str
    product_type: str  # "individual" | "charola"
    quantity: int


class DeliveryInDB(BaseModel):
    id: str
    client_id: str
    client_name: str
    product_type: str
    quantity: int
    unit_price: float
    total: float
    status: str  # "pendiente" | "pagada"
    paid_at: Optional[datetime] = None
    created_at: datetime
