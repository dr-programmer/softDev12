from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Doctor, DoctorWorkingHours
from app.auth import hash_password
from app.schemas import DoctorRegisterRequest, DoctorResponse, WorkingHoursEntry

router = APIRouter(prefix="/api/auth", tags=["doctors"])


@router.post("/register/doctor", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
def register_doctor(request: DoctorRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        role="doctor",
    )
    db.add(user)
    db.flush()

    doctor = Doctor(id=user.id, name=request.name, address=request.address)
    db.add(doctor)
    db.flush()

    for wh in request.working_hours:
        db.add(DoctorWorkingHours(
            doctor_id=doctor.id,
            day_of_week=wh.day_of_week,
            start_time=wh.start_time,
            end_time=wh.end_time,
        ))

    db.commit()
    db.refresh(doctor)

    return DoctorResponse(
        id=doctor.id,
        email=user.email,
        name=doctor.name,
        address=doctor.address,
        role=user.role,
        working_hours=[
            WorkingHoursEntry(
                day_of_week=wh.day_of_week,
                start_time=wh.start_time,
                end_time=wh.end_time,
            )
            for wh in doctor.working_hours
        ],
    )
