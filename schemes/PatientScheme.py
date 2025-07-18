from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime, UTC
import random

# Patient input schema
class PatientInput(BaseModel):
    id: int = random.randint(100000, 9999999)
    names: str
    email: Optional[EmailStr]
    phone: str
    age: int
    password: str
    created_at: datetime = datetime.now(UTC)

# Patient medicine or billing schema
class PatientMedecine(BaseModel):
    id: Optional[UUID] = None
    record_id: int = random.randint(100000, 9999999)
    patient_id: int                     
    medicine_id: UUID               
    quantity: int = 1                  
    total_amount: float                
    is_paid: bool = False
    created_at: datetime = datetime.now(UTC)

class PatientLogin(BaseModel):
    email: EmailStr
    password: str