import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import ASGITransport, AsyncClient
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_doctor(client):
    response = client.post("/api/auth/register/doctor", json={
        "email": "doctor@example.com",
        "password": "password123",
        "name": "Dr. Smith",
        "address": "123 Medical St",
        "working_hours": [
            {"day_of_week": 0, "start_time": "09:00", "end_time": "12:00"},
            {"day_of_week": 0, "start_time": "13:00", "end_time": "17:00"},
            {"day_of_week": 1, "start_time": "09:00", "end_time": "12:00"},
            {"day_of_week": 1, "start_time": "13:00", "end_time": "17:00"},
            {"day_of_week": 2, "start_time": "09:00", "end_time": "12:00"},
            {"day_of_week": 2, "start_time": "13:00", "end_time": "17:00"},
            {"day_of_week": 3, "start_time": "09:00", "end_time": "12:00"},
            {"day_of_week": 3, "start_time": "13:00", "end_time": "17:00"},
            {"day_of_week": 4, "start_time": "09:00", "end_time": "12:00"},
            {"day_of_week": 4, "start_time": "13:00", "end_time": "17:00"},
        ],
    })
    return response.json()


@pytest.fixture
def doctor_token(client, sample_doctor):
    response = client.post("/api/auth/login", json={
        "email": "doctor@example.com",
        "password": "password123",
    })
    return response.json()["access_token"]


@pytest.fixture
def sample_patient(client, sample_doctor):
    response = client.post("/api/auth/register/patient", json={
        "email": "patient@example.com",
        "password": "password123",
        "name": "Jane Doe",
        "phone": "+359888123456",
        "doctor_id": sample_doctor["id"],
    })
    return response.json()


@pytest.fixture
def patient_token(client, sample_patient):
    response = client.post("/api/auth/login", json={
        "email": "patient@example.com",
        "password": "password123",
    })
    return response.json()["access_token"]
