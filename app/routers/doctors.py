from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Doctor, DoctorWorkingHours, DoctorScheduleChange, ScheduleChangeHours
from app.auth import hash_password, require_doctor
from app.schemas import (
    DoctorRegisterRequest, DoctorResponse, WorkingHoursEntry,
    UpdateWorkingHoursRequest, TemporaryScheduleChangeRequest,
    PermanentScheduleChangeRequest, ScheduleChangeResponse,
)

register_router = APIRouter(prefix="/api/auth", tags=["doctors"])
router = APIRouter(prefix="/api/doctors", tags=["doctors"])


@register_router.post("/register/doctor", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
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


@router.put("/me/working-hours")
def update_working_hours(
    request: UpdateWorkingHoursRequest,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    db.query(DoctorWorkingHours).filter(
        DoctorWorkingHours.doctor_id == current_user.id
    ).delete()

    for wh in request.working_hours:
        db.add(DoctorWorkingHours(
            doctor_id=current_user.id,
            day_of_week=wh.day_of_week,
            start_time=wh.start_time,
            end_time=wh.end_time,
        ))

    db.commit()
    return {"message": "Working hours updated", "working_hours": request.working_hours}


@router.post(
    "/me/schedule-changes/temporary",
    response_model=ScheduleChangeResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_temporary_schedule_change(
    request: TemporaryScheduleChangeRequest,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(DoctorScheduleChange)
        .filter(
            DoctorScheduleChange.doctor_id == current_user.id,
            DoctorScheduleChange.change_type == "temporary",
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A temporary schedule change already exists. Remove it before adding a new one.",
        )

    if request.end_date < request.effective_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="End date must be after or equal to effective date.",
        )

    change = DoctorScheduleChange(
        doctor_id=current_user.id,
        change_type="temporary",
        effective_date=request.effective_date,
        end_date=request.end_date,
    )
    db.add(change)
    db.flush()

    for wh in request.working_hours:
        db.add(ScheduleChangeHours(
            change_id=change.id,
            day_of_week=wh.day_of_week,
            start_time=wh.start_time,
            end_time=wh.end_time,
        ))

    db.commit()
    db.refresh(change)

    return ScheduleChangeResponse(
        id=change.id,
        doctor_id=change.doctor_id,
        change_type=change.change_type,
        effective_date=change.effective_date,
        end_date=change.end_date,
        working_hours=[
            WorkingHoursEntry(
                day_of_week=h.day_of_week,
                start_time=h.start_time,
                end_time=h.end_time,
            )
            for h in change.hours
        ],
    )


@router.post(
    "/me/schedule-changes/permanent",
    response_model=ScheduleChangeResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_permanent_schedule_change(
    request: PermanentScheduleChangeRequest,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    min_date = date.today() + timedelta(weeks=1)
    if request.effective_date < min_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Effective date must be at least one week in the future (earliest: {min_date}).",
        )

    change = DoctorScheduleChange(
        doctor_id=current_user.id,
        change_type="permanent",
        effective_date=request.effective_date,
        end_date=None,
    )
    db.add(change)
    db.flush()

    for wh in request.working_hours:
        db.add(ScheduleChangeHours(
            change_id=change.id,
            day_of_week=wh.day_of_week,
            start_time=wh.start_time,
            end_time=wh.end_time,
        ))

    db.commit()
    db.refresh(change)

    return ScheduleChangeResponse(
        id=change.id,
        doctor_id=change.doctor_id,
        change_type=change.change_type,
        effective_date=change.effective_date,
        end_date=change.end_date,
        working_hours=[
            WorkingHoursEntry(
                day_of_week=h.day_of_week,
                start_time=h.start_time,
                end_time=h.end_time,
            )
            for h in change.hours
        ],
    )
