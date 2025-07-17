from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, UTC
import uuid
import sqlalchemy

Base = declarative_base()
sqlalchemy.url = "sqlite:///./payments.db"
# 1. Patients Table
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    names = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    medicines = relationship("PatientMedicine", back_populates="patient")


# 2. Medicines Table
class Medecine(Base):
    __tablename__ = "medicines"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medicine_name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    unit_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient_links = relationship("PatientMedecine", back_populates="medicine")


# 3. Patient-Medicine Link Table (Billing)
class PatientMedecine(Base):
    __tablename__ = "patient_medicines"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    medicine_id = Column(PG_UUID(as_uuid=True), ForeignKey("medicines.id"), nullable=False)

    quantity = Column(Integer, default=1)
    total_amount = Column(Float, nullable=False)
    is_paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(UTC))

    # Relationships
    patient = relationship("Patient", back_populates="medicines")
    medicine = relationship("Medecine", back_populates="patient_links")
