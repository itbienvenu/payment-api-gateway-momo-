from pydantic import BaseModel
from typing import Optional
from datetime import datetime, UTC
import random
from uuid import UUID, uuid4

class Medecine(BaseModel):
    id: UUID
    medecine_name: str                     
    description: Optional[str] = None
    unit_price: float           
    created_at: datetime = datetime.now(UTC)
