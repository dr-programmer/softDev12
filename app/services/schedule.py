from datetime import date, time
from sqlalchemy.orm import Session
from app.models import DoctorWorkingHours, DoctorScheduleChange, ScheduleChangeHours


def parse_time(time_str: str) -> time:
    parts = time_str.split(":")
    return time(int(parts[0]), int(parts[1]))


def get_working_hours_for_date(
    db: Session, doctor_id: int, target_date: date
) -> list[tuple[time, time]]:
    """
    Returns list of (start_time, end_time) intervals for a doctor on a given date.
    Resolution priority: temporary change > permanent change > base hours.
    """
    day_of_week = target_date.weekday()  # 0=Monday ... 6=Sunday

    # 1. Check temporary schedule change
    temp_change = (
        db.query(DoctorScheduleChange)
        .filter(
            DoctorScheduleChange.doctor_id == doctor_id,
            DoctorScheduleChange.change_type == "temporary",
            DoctorScheduleChange.effective_date <= target_date,
            DoctorScheduleChange.end_date >= target_date,
        )
        .first()
    )
    if temp_change:
        return _get_hours_from_change(db, temp_change.id, day_of_week)

    # 2. Check permanent schedule change (latest effective_date <= target_date)
    perm_change = (
        db.query(DoctorScheduleChange)
        .filter(
            DoctorScheduleChange.doctor_id == doctor_id,
            DoctorScheduleChange.change_type == "permanent",
            DoctorScheduleChange.effective_date <= target_date,
        )
        .order_by(DoctorScheduleChange.effective_date.desc())
        .first()
    )
    if perm_change:
        return _get_hours_from_change(db, perm_change.id, day_of_week)

    # 3. Fall back to base working hours
    base_hours = (
        db.query(DoctorWorkingHours)
        .filter(
            DoctorWorkingHours.doctor_id == doctor_id,
            DoctorWorkingHours.day_of_week == day_of_week,
        )
        .all()
    )
    return [(parse_time(h.start_time), parse_time(h.end_time)) for h in base_hours]


def _get_hours_from_change(
    db: Session, change_id: int, day_of_week: int
) -> list[tuple[time, time]]:
    hours = (
        db.query(ScheduleChangeHours)
        .filter(
            ScheduleChangeHours.change_id == change_id,
            ScheduleChangeHours.day_of_week == day_of_week,
        )
        .all()
    )
    return [(parse_time(h.start_time), parse_time(h.end_time)) for h in hours]
