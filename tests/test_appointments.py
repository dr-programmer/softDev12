from datetime import datetime, timedelta


def _next_weekday(weekday: int):
    """Return the next date that falls on the given weekday (0=Monday)."""
    today = datetime.utcnow().date()
    days_ahead = weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    # Ensure it's at least 2 days ahead to satisfy 24h rule
    target = today + timedelta(days=days_ahead)
    if (target - today).days < 2:
        target += timedelta(weeks=1)
    return target


def _make_appointment_times(weekday: int, start_hour: int, end_hour: int):
    """Create start/end ISO strings for an appointment on the next given weekday."""
    d = _next_weekday(weekday)
    start = datetime(d.year, d.month, d.day, start_hour, 0).isoformat()
    end = datetime(d.year, d.month, d.day, end_hour, 0).isoformat()
    return start, end


# --- Creation ---

def test_create_appointment_success(client, patient_token):
    start, end = _make_appointment_times(0, 9, 10)  # Monday 09:00-10:00
    response = client.post(
        "/api/appointments/",
        json={"start_time": start, "end_time": end},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "active"


def test_create_appointment_outside_working_hours(client, patient_token):
    start, end = _make_appointment_times(0, 18, 19)  # Monday 18:00-19:00 (outside hours)
    response = client.post(
        "/api/appointments/",
        json={"start_time": start, "end_time": end},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response.status_code == 400
    assert "working hours" in response.json()["detail"].lower()


def test_create_appointment_on_day_off(client, patient_token):
    start, end = _make_appointment_times(5, 10, 11)  # Saturday (no working hours)
    response = client.post(
        "/api/appointments/",
        json={"start_time": start, "end_time": end},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response.status_code == 400


def test_create_appointment_less_than_24h(client, patient_token):
    # Create an appointment starting in 1 hour
    soon = datetime.utcnow() + timedelta(hours=1)
    end = soon + timedelta(hours=1)
    response = client.post(
        "/api/appointments/",
        json={"start_time": soon.isoformat(), "end_time": end.isoformat()},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response.status_code == 400
    assert "24 hours" in response.json()["detail"]


def test_create_appointment_overlap(client, patient_token):
    start, end = _make_appointment_times(0, 9, 10)
    # First appointment
    response1 = client.post(
        "/api/appointments/",
        json={"start_time": start, "end_time": end},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response1.status_code == 201

    # Overlapping appointment
    response2 = client.post(
        "/api/appointments/",
        json={"start_time": start, "end_time": end},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response2.status_code == 409


def test_create_appointment_start_after_end(client, patient_token):
    end, start = _make_appointment_times(0, 9, 10)  # swapped
    response = client.post(
        "/api/appointments/",
        json={"start_time": start, "end_time": end},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response.status_code == 400


def test_create_appointment_requires_patient(client, doctor_token):
    start, end = _make_appointment_times(0, 9, 10)
    response = client.post(
        "/api/appointments/",
        json={"start_time": start, "end_time": end},
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 403


# --- Cancellation ---

def test_cancel_appointment_by_patient(client, patient_token):
    start, end = _make_appointment_times(0, 9, 10)
    create_resp = client.post(
        "/api/appointments/",
        json={"start_time": start, "end_time": end},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    appt_id = create_resp.json()["id"]

    response = client.delete(
        f"/api/appointments/{appt_id}",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cancel_appointment_by_doctor(client, patient_token, doctor_token):
    start, end = _make_appointment_times(0, 9, 10)
    create_resp = client.post(
        "/api/appointments/",
        json={"start_time": start, "end_time": end},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    appt_id = create_resp.json()["id"]

    response = client.delete(
        f"/api/appointments/{appt_id}",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cancel_nonexistent_appointment(client, patient_token):
    response = client.delete(
        "/api/appointments/9999",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response.status_code == 404


def test_cancel_already_cancelled(client, patient_token):
    start, end = _make_appointment_times(0, 9, 10)
    create_resp = client.post(
        "/api/appointments/",
        json={"start_time": start, "end_time": end},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    appt_id = create_resp.json()["id"]

    client.delete(
        f"/api/appointments/{appt_id}",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    response = client.delete(
        f"/api/appointments/{appt_id}",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response.status_code == 400


# --- Listing ---

def test_list_appointments_patient(client, patient_token):
    start, end = _make_appointment_times(0, 9, 10)
    client.post(
        "/api/appointments/",
        json={"start_time": start, "end_time": end},
        headers={"Authorization": f"Bearer {patient_token}"},
    )

    response = client.get(
        "/api/appointments/",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_appointments_doctor(client, patient_token, doctor_token):
    start, end = _make_appointment_times(0, 9, 10)
    client.post(
        "/api/appointments/",
        json={"start_time": start, "end_time": end},
        headers={"Authorization": f"Bearer {patient_token}"},
    )

    response = client.get(
        "/api/appointments/",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_appointments_requires_auth(client):
    response = client.get("/api/appointments/")
    assert response.status_code == 401
