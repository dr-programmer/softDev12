def test_register_patient(client, sample_doctor):
    response = client.post("/api/auth/register/patient", json={
        "email": "newpatient@example.com",
        "password": "password123",
        "name": "John Smith",
        "phone": "+359888000000",
        "doctor_id": sample_doctor["id"],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newpatient@example.com"
    assert data["name"] == "John Smith"
    assert data["doctor_id"] == sample_doctor["id"]
    assert data["role"] == "patient"


def test_register_patient_duplicate_email(client, sample_patient):
    response = client.post("/api/auth/register/patient", json={
        "email": "patient@example.com",
        "password": "password123",
        "name": "Duplicate",
        "phone": "+359888111111",
        "doctor_id": sample_patient["doctor_id"],
    })
    assert response.status_code == 409


def test_register_patient_invalid_doctor(client):
    response = client.post("/api/auth/register/patient", json={
        "email": "orphan@example.com",
        "password": "password123",
        "name": "Orphan Patient",
        "phone": "+359888222222",
        "doctor_id": 9999,
    })
    assert response.status_code == 404
