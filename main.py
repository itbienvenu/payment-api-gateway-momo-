from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4

from db import get_db, Base, engine
from models.models import Patient, Medecine, PatientMedecine
from schemes.PatientScheme import PatientInput, PatientMedecine, PatientLogin
from schemes.MedecineScheme import Medecine as MedicineSchema
from auth.auth_handler import hash_password, verify_password, create_access_token
from auth.auth_bearer import JWTBearer

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
        id=uuid4(),
        name=data.names,
        email=data.email,
        age=data.age,
        hashed_password=hash_password(data.password)
    )
    db.add(new_patient)
    db.commit()
    return {"message": "Patient registered successfully"}


@app.post("/login", tags=["Auth"])
def login_user(data: PatientLogin, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.email == data.email).first()
    if not patient or not verify_password(data.password, patient.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(patient.id)})
    return {"access_token": token}


@app.post("/add_medicine", tags=["Medicine"], dependencies=[Depends(JWTBearer())])
def add_medicine(med: MedicineSchema, db: Session = Depends(get_db)):
    new_med = Medecine(id=uuid4(), medecine_name=med.medecine_name)
    db.add(new_med)
    db.commit()
    return {"message": "Medicine added", "id": str(new_med.id)}


@app.post("/assign_medicine", tags=["Patient"], dependencies=[Depends(JWTBearer())])
def assign_medicine(data: PatientMedecine, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    medicine = db.query(Medecine).filter(Medecine.id == data.medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")

    link = PatientMedecine(id=uuid4(), patient_id=patient.id, medecine_id=medicine.id)
    db.add(link)
    db.commit()
    return {"message": "Medicine assigned to patient"}


@app.get("/medicines", tags=["Medicine"], dependencies=[Depends(JWTBearer())])
def list_medicines(db: Session = Depends(get_db)):
    meds = db.query(Medecine).all()
    return [{"id": str(m.id), "name": m.medecine_name} for m in meds]


@app.get("/patients", tags=["Patient"], dependencies=[Depends(JWTBearer())])
def list_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return [{"id": str(p.id), "name": p.name, "email": p.email, "age": p.age} for p in patients]
