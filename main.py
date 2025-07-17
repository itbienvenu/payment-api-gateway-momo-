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
from datetime import datetime, timezone, UTC
from typing import List
Base.metadata.create_all(bind=engine)

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
def add_medicines(meds: List[MedicineSchema], db: Session = Depends(get_db)):
    added_ids = []
    for med in meds:
        new_med = Medecine(
            id=uuid4(),
            medicine_name=med.medecine_name,
            description=med.description,
            unit_price=med.unit_price
        )
        db.add(new_med)
        added_ids.append(str(new_med.id))
    db.commit()
    return {"message": "Medicines added", "ids": added_ids}

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


@app.post("/get_medicine_assigned/{patient_id}", tags=['Patient'], dependencies=[Depends(JWTBearer())])
async def get_assigned_medicine(patient_id: int, db: Session = Depends(get_db)):
    # Get the patient by ID
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Invalid patient ID")

    # Get all assigned medicines
    assigned_meds = db.query(PatientMedecineModel).filter(PatientMedecineModel.patient_id == patient_id).all()
    if not assigned_meds:
        return {"message": "No medicines assigned"}

    result = []
    grand_total = 0
    paid_total = 0
    unpaid_total = 0

    for item in assigned_meds:
        medicine = db.query(Medecine).filter(Medecine.id == item.medicine_id).first()
        total_amount = medicine.unit_price * item.quantity
        grand_total += total_amount

        if item.is_paid:
            paid_total += total_amount
        else:
            unpaid_total += total_amount

        result.append({
            "medicine_name": medicine.medicine_name,
            "quantity": item.quantity,
            "unit_price": medicine.unit_price,
            "total_amount": total_amount,
            "is_paid": item.is_paid,
            "assigned_at": item.created_at,
        })

    return {
        "patient_name": patient.names,
        "assigned_medicines": result,
        "summary": {
            "grand_total": grand_total,
            "paid_total": paid_total,
            "unpaid_total": unpaid_total
        }
    }
@app.post("/initiate_payment/{patient_id}", tags=["Payment"], dependencies=[Depends(JWTBearer())])
async def initiate_payment(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    unpaid_meds = db.query(PatientMedecineModel).filter(
        PatientMedecineModel.patient_id == patient_id,
        PatientMedecineModel.is_paid == False
    ).all()

    if not unpaid_meds:
        raise HTTPException(status_code=400, detail="No unpaid medicines found")

    total_amount = 0
    for item in unpaid_meds:
        med = db.query(Medecine).filter(Medecine.id == item.medicine_id).first()
        total_amount += med.unit_price * item.quantity

    # Optional: create a Payment record in DB with `is_completed=False`
    # You can generate a payment reference here too

    return {
        "message": "Payment initialized",
        "patient_name": patient.names,
        "amount_to_pay": total_amount,
        "currency": "RWF",
        "payment_reference": f"{patient_id}-{datetime.now(UTC).timestamp()}"  # optional
    }
@app.post("/verify_payment/{patient_id}", tags=["Payment"], dependencies=[Depends(JWTBearer())])
async def verify_payment(patient_id: int, db: Session = Depends(get_db)):
    unpaid_items = db.query(PatientMedecineModel).filter(
        PatientMedecineModel.patient_id == patient_id,
        PatientMedecineModel.is_paid == False
    ).all()

    for item in unpaid_items:
        item.is_paid = True
    db.commit()

    return {"message": "Payment verified and medicines marked as paid."}
