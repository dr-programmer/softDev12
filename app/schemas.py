from datetime import date, datetime
from pydantic import BaseModel, EmailStr


# --- Working Hours ---

class WorkingHoursEntry(BaseModel):
    day_of_week: int  # 0=Monday ... 6=Sunday
    start_time: str   # "HH:MM"
    end_time: str     # "HH:MM"


# --- Auth ---

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Doctor ---

class DoctorRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    address: str
    working_hours: list[WorkingHoursEntry]


class DoctorResponse(BaseModel):
    id: int
    email: str
    name: str
    address: str
    role: str
    working_hours: list[WorkingHoursEntry]

    class Config:
        from_attributes = True


class UpdateWorkingHoursRequest(BaseModel):
    working_hours: list[WorkingHoursEntry]


# --- Schedule Changes ---

class TemporaryScheduleChangeRequest(BaseModel):
    effective_date: date
    end_date: date
    working_hours: list[WorkingHoursEntry]


class PermanentScheduleChangeRequest(BaseModel):
    effective_date: date
    working_hours: list[WorkingHoursEntry]


class ScheduleChangeResponse(BaseModel):
    id: int
    doctor_id: int
    change_type: str
    effective_date: date
    end_date: date | None
    working_hours: list[WorkingHoursEntry]

    class Config:
        from_attributes = True


# --- Patient ---

class PatientRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: str
    doctor_id: int


class PatientResponse(BaseModel):
    id: int
    email: str
    name: str
    phone: str
    doctor_id: int
    role: str

    class Config:
        from_attributes = True


# --- Appointment ---

class AppointmentCreateRequest(BaseModel):
    start_time: datetime
    end_time: datetime


class AppointmentResponse(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    start_time: datetime
    end_time: datetime
    status: str

    class Config:
        from_attributes = True
