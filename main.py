from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
import random
from db import get_db, Base, engine
from models.models import Patient, Medecine, PatientMedecineModel
from schemes.PatientScheme import PatientInput, PatientMedecine, PatientLogin
from schemes.MedecineScheme import Medecine as MedicineSchema
from auth.auth_handler import hash_password, verify_password, create_access_token
from auth.auth_bearer import JWTBearer
from datetime import datetime, timezone
Base.metadata.create_all(bind=engine)  # Create tables

app = FastAPI()


@app.get("/")
async def home():
    return {"message": "Welcome to the Medical API"}


@app.post("/register", tags=["Auth"])
def register_user(data: PatientInput, db: Session = Depends(get_db)):
    if db.query(Patient).filter(Patient.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    new_patient = Patient(
        id = random.randint(100000, 9999999),
        names=data.names,
        email=data.email,
        phone = data.phone,
        age = data.age,
        password=hash_password(data.password)
    )
    db.add(new_patient)
    db.commit()
    return {"message": "Patient registered successfully"}


@app.post("/login", tags=["Auth"])
def login_user(data: PatientLogin, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.email == data.email).first()
    if not patient or not verify_password(data.password, patient.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(patient.id)})
    return {"access_token": token}


@app.post("/add_medicine", tags=["Medicine"], dependencies=[Depends(JWTBearer())])
def add_medicine(med: MedicineSchema, db: Session = Depends(get_db)):
    new_med = Medecine(id=uuid4(), 
                       medicine_name=med.medecine_name,
                       description = med.description,
                       unit_price = med.unit_price
                       )
    db.add(new_med)
    db.commit()
    return {"message": "Medicine added", "id": str(new_med.id)}


@app.post("/assign_medicine", tags=["Patient"], dependencies=[Depends(JWTBearer())])
def assign_medicine(data: PatientMedecine, db: Session = Depends(get_db)):
    # Check patient and medicine
    patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    medicine = db.query(Medecine).filter(Medecine.id == data.medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")

    # Create DB record
    link = PatientMedecineModel(
        id=uuid4(),
        patient_id=data.patient_id,
        medicine_id=data.medicine_id,
        quantity=data.quantity,
        total_amount=data.total_amount,
        is_paid=data.is_paid,
        created_at=datetime.now(timezone.utc)
    )

    db.add(link)
    db.commit()

    return {"message": "Medicine assigned to patient"}

@app.get("/medicines", tags=["Medicine"], dependencies=[Depends(JWTBearer())])
def list_medicines(db: Session = Depends(get_db)):
    meds = db.query(Medecine).all()
    return [{"id": str(m.id), "name": m.medicine_name, "price": m.unit_price} for m in meds]


@app.get("/patients", tags=["Patient"], dependencies=[Depends(JWTBearer())])
def list_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return [{"id": str(p.id), "name": p.names, "email": p.email, "age": p.age} for p in patients]
