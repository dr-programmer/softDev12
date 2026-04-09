from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "doctor" or "patient"

    doctor = relationship("Doctor", back_populates="user", uselist=False)
    patient = relationship("Patient", back_populates="user", uselist=False)


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    name = Column(String, nullable=False)
    address = Column(Text, nullable=False)

    user = relationship("User", back_populates="doctor")
    working_hours = relationship("DoctorWorkingHours", back_populates="doctor", cascade="all, delete-orphan")
    schedule_changes = relationship("DoctorScheduleChange", back_populates="doctor", cascade="all, delete-orphan")
    patients = relationship("Patient", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")


class DoctorWorkingHours(Base):
    __tablename__ = "doctor_working_hours"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday ... 6=Sunday
    start_time = Column(String, nullable=False)  # "HH:MM"
    end_time = Column(String, nullable=False)  # "HH:MM"

    doctor = relationship("Doctor", back_populates="working_hours")


class DoctorScheduleChange(Base):
    __tablename__ = "doctor_schedule_changes"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    change_type = Column(String, nullable=False)  # "temporary" or "permanent"
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # only for temporary changes

    doctor = relationship("Doctor", back_populates="schedule_changes")
    hours = relationship("ScheduleChangeHours", back_populates="schedule_change", cascade="all, delete-orphan")


class ScheduleChangeHours(Base):
    __tablename__ = "schedule_change_hours"

    id = Column(Integer, primary_key=True, index=True)
    change_id = Column(Integer, ForeignKey("doctor_schedule_changes.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)

    schedule_change = relationship("DoctorScheduleChange", back_populates="hours")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)

    user = relationship("User", back_populates="patient")
    doctor = relationship("Doctor", back_populates="patients")
    appointments = relationship("Appointment", back_populates="patient")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default="active")  # "active" or "cancelled"

    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")
