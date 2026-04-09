from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Appointment
from app.auth import get_current_user, require_patient
from app.schemas import AppointmentCreateRequest, AppointmentResponse
from app.services.appointment import validate_appointment

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    request: AppointmentCreateRequest,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    doctor_id = validate_appointment(db, current_user.id, request.start_time, request.end_time)

    appointment = Appointment(
        doctor_id=doctor_id,
        patient_id=current_user.id,
        start_time=request.start_time,
        end_time=request.end_time,
        status="active",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return AppointmentResponse(
        id=appointment.id,
        doctor_id=appointment.doctor_id,
        patient_id=appointment.patient_id,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        status=appointment.status,
    )


@router.delete("/{appointment_id}", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )

    if appointment.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment is already cancelled.",
        )

    # Check user is either the patient or the doctor
    if current_user.id != appointment.patient_id and current_user.id != appointment.doctor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own appointments.",
        )

    # Check 12-hour rule
    now = datetime.now(timezone.utc)
    start_aware = appointment.start_time.replace(tzinfo=timezone.utc) if appointment.start_time.tzinfo is None else appointment.start_time
    if start_aware < now + timedelta(hours=12):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel an appointment less than 12 hours before its start time.",
        )

    appointment.status = "cancelled"
    db.commit()
    db.refresh(appointment)

    return AppointmentResponse(
        id=appointment.id,
        doctor_id=appointment.doctor_id,
        patient_id=appointment.patient_id,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        status=appointment.status,
    )


@router.get("/", response_model=list[AppointmentResponse])
def list_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "doctor":
        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == current_user.id
        ).all()
    else:
        appointments = db.query(Appointment).filter(
            Appointment.patient_id == current_user.id
        ).all()

    return [
        AppointmentResponse(
            id=a.id,
            doctor_id=a.doctor_id,
            patient_id=a.patient_id,
            start_time=a.start_time,
            end_time=a.end_time,
            status=a.status,
        )
        for a in appointments
    ]
