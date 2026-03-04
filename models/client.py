from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ClientCreate(BaseModel):
    name: str
    sells_individual: bool = Field(True, description="¿Vende brownies individuales?")
    sells_charola: bool = Field(True, description="¿Vende charolas?")
    price_individual: Optional[float] = None
    price_charola: Optional[float] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    sells_individual: Optional[bool] = None
    sells_charola: Optional[bool] = None
    price_individual: Optional[float] = None
    price_charola: Optional[float] = None


class ClientInDB(BaseModel):
    id: str
    name: str
    sells_individual: bool
    sells_charola: bool
    price_individual: Optional[float] = None
    price_charola: Optional[float] = None
    created_at: datetime
