from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Doctor, Patient
from app.auth import hash_password
from app.schemas import PatientRegisterRequest, PatientResponse

router = APIRouter(prefix="/api/auth", tags=["patients"])


@router.post("/register/patient", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def register_patient(request: PatientRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    doctor = db.query(Doctor).filter(Doctor.id == request.doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )

    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        role="patient",
    )
    db.add(user)
    db.flush()

    patient = Patient(
        id=user.id,
        name=request.name,
        phone=request.phone,
        doctor_id=request.doctor_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    return PatientResponse(
        id=patient.id,
        email=user.email,
        name=patient.name,
        phone=patient.phone,
        doctor_id=patient.doctor_id,
        role=user.role,
    )
