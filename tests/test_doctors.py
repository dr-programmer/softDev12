def test_register_doctor(client):
    response = client.post("/api/auth/register/doctor", json={
        "email": "newdoc@example.com",
        "password": "password123",
        "name": "Dr. New",
        "address": "456 Health Ave",
        "working_hours": [
            {"day_of_week": 0, "start_time": "08:00", "end_time": "16:00"},
        ],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newdoc@example.com"
    assert data["name"] == "Dr. New"
    assert data["role"] == "doctor"
    assert len(data["working_hours"]) == 1


def test_register_doctor_duplicate_email(client, sample_doctor):
    response = client.post("/api/auth/register/doctor", json={
        "email": "doctor@example.com",
        "password": "password123",
        "name": "Dr. Duplicate",
        "address": "789 Copy St",
        "working_hours": [],
    })
    assert response.status_code == 409


def test_login_success(client, sample_doctor):
    response = client.post("/api/auth/login", json={
        "email": "doctor@example.com",
        "password": "password123",
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(client, sample_doctor):
    response = client.post("/api/auth/login", json={
        "email": "doctor@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


def test_login_nonexistent_email(client):
    response = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123",
    })
    assert response.status_code == 401
