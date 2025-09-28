from pydantic import BaseModel
from datetime import date
from typing import Optional

class Invoice(BaseModel):
    id: int
    invoice_number: Optional[str] = None
    vendor: str
    date: date
    amount: float
    status: str  # e.g., 'Paid' or 'Unpaid'
    category: Optional[str] = None 