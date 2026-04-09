from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Appointment
from app.auth import require_patient
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
