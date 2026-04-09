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


# --- Schedule Management ---

def test_update_working_hours(client, doctor_token):
    response = client.put(
        "/api/doctors/me/working-hours",
        json={"working_hours": [
            {"day_of_week": 0, "start_time": "10:00", "end_time": "14:00"},
        ]},
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["working_hours"]) == 1


def test_update_working_hours_requires_doctor(client, patient_token):
    response = client.put(
        "/api/doctors/me/working-hours",
        json={"working_hours": []},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response.status_code == 403


def test_add_temporary_schedule_change(client, doctor_token):
    response = client.post(
        "/api/doctors/me/schedule-changes/temporary",
        json={
            "effective_date": "2026-05-01",
            "end_date": "2026-05-03",
            "working_hours": [
                {"day_of_week": 0, "start_time": "10:00", "end_time": "14:00"},
            ],
        },
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["change_type"] == "temporary"
    assert data["effective_date"] == "2026-05-01"
    assert data["end_date"] == "2026-05-03"


def test_add_second_temporary_change_fails(client, doctor_token):
    client.post(
        "/api/doctors/me/schedule-changes/temporary",
        json={
            "effective_date": "2026-05-01",
            "end_date": "2026-05-03",
            "working_hours": [],
        },
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    response = client.post(
        "/api/doctors/me/schedule-changes/temporary",
        json={
            "effective_date": "2026-06-01",
            "end_date": "2026-06-03",
            "working_hours": [],
        },
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 409


def test_add_permanent_schedule_change(client, doctor_token):
    from datetime import date, timedelta
    future_date = (date.today() + timedelta(weeks=2)).isoformat()
    response = client.post(
        "/api/doctors/me/schedule-changes/permanent",
        json={
            "effective_date": future_date,
            "working_hours": [
                {"day_of_week": 0, "start_time": "08:00", "end_time": "12:00"},
            ],
        },
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 201
    assert response.json()["change_type"] == "permanent"


def test_permanent_change_too_soon_fails(client, doctor_token):
    from datetime import date, timedelta
    soon_date = (date.today() + timedelta(days=3)).isoformat()
    response = client.post(
        "/api/doctors/me/schedule-changes/permanent",
        json={
            "effective_date": soon_date,
            "working_hours": [],
        },
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 422
