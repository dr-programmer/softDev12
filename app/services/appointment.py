from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import Patient, Appointment
from app.services.schedule import get_working_hours_for_date, parse_time


def validate_appointment(
    db: Session, patient_id: int, start_time: datetime, end_time: datetime
) -> int:
    """
    Validates appointment business rules. Returns doctor_id on success.
    Raises HTTPException on validation failure.
    """
    if start_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be before end time.",
        )

    now = datetime.now(timezone.utc)
    start_aware = start_time.replace(tzinfo=timezone.utc) if start_time.tzinfo is None else start_time
    if start_aware < now + timedelta(hours=24):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment must be created at least 24 hours before the start time.",
        )

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    doctor_id = patient.doctor_id

    # Check appointment is within working hours
    target_date = start_time.date()
    working_intervals = get_working_hours_for_date(db, doctor_id, target_date)

    appointment_start = start_time.time()
    appointment_end = end_time.time()

    if start_time.date() != end_time.date():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment must start and end on the same day.",
        )

    within_hours = False
    for interval_start, interval_end in working_intervals:
        if appointment_start >= interval_start and appointment_end <= interval_end:
            within_hours = True
            break

    if not within_hours:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment is not within the doctor's working hours.",
        )

    # Check for overlapping appointments
    overlap = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "active",
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
        )
        .first()
    )
    if overlap:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This time slot overlaps with an existing appointment.",
        )

    return doctor_id
