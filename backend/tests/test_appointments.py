from datetime import UTC


def test_list_appointments_empty(client, vet_headers):
    response = client.get("/api/v1/appointments/", headers=vet_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_appointment(client, vet_headers, pet, vet_user):
    from datetime import datetime, timedelta
    scheduled = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    response = client.post("/api/v1/appointments/", headers=vet_headers, json={
        "pet_id": pet.id,
        "vet_id": vet_user.id,
        "scheduled_at": scheduled,
        "duration_min": 30,
        "reason": "Checkup",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["pet_id"] == pet.id
    assert data["vet_id"] == vet_user.id
    assert data["owner_id"] == pet.owner_id
    assert data["status"] == "scheduled"


def test_create_appointment_invalid_pet(client, vet_headers, vet_user):
    from datetime import datetime, timedelta
    scheduled = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    response = client.post("/api/v1/appointments/", headers=vet_headers, json={
        "pet_id": 99999,
        "vet_id": vet_user.id,
        "scheduled_at": scheduled,
    })
    assert response.status_code == 404


def test_create_appointment_rejects_non_vet(client, vet_headers, pet, receptionist_user):
    from datetime import datetime, timedelta
    response = client.post("/api/v1/appointments/", headers=vet_headers, json={
        "pet_id": pet.id,
        "vet_id": receptionist_user.id,
        "scheduled_at": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
    })
    assert response.status_code == 422


def test_create_appointment_rejects_overlap(client, vet_headers, appointment, pet, vet_user):
    response = client.post("/api/v1/appointments/", headers=vet_headers, json={
        "pet_id": pet.id,
        "vet_id": vet_user.id,
        "scheduled_at": appointment.scheduled_at.isoformat(),
        "duration_min": 15,
    })
    assert response.status_code == 409


def test_get_appointment(client, vet_headers, appointment):
    response = client.get(f"/api/v1/appointments/{appointment.id}", headers=vet_headers)
    assert response.status_code == 200
    assert response.json()["reason"] == "Test appointment"


def test_get_appointment_not_found(client, vet_headers):
    response = client.get("/api/v1/appointments/99999", headers=vet_headers)
    assert response.status_code == 404


def test_update_appointment(client, vet_headers, appointment):
    response = client.patch(f"/api/v1/appointments/{appointment.id}", headers=vet_headers, json={
        "notes": "Updated notes",
        "duration_min": 45,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "Updated notes"
    assert data["duration_min"] == 45


def test_delete_appointment(client, vet_headers, appointment):
    response = client.delete(f"/api/v1/appointments/{appointment.id}", headers=vet_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    response = client.get(f"/api/v1/appointments/{appointment.id}", headers=vet_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_appointment_status_flow_and_cancel_reason(client, vet_headers, appointment):
    response = client.patch(f"/api/v1/appointments/{appointment.id}", headers=vet_headers, json={
        "status": "cancelled",
    })
    assert response.status_code == 422

    response = client.patch(f"/api/v1/appointments/{appointment.id}", headers=vet_headers, json={
        "status": "in-progress",
    })
    assert response.status_code == 200
    response = client.patch(f"/api/v1/appointments/{appointment.id}", headers=vet_headers, json={
        "status": "completed",
    })
    assert response.status_code == 200
    response = client.patch(f"/api/v1/appointments/{appointment.id}", headers=vet_headers, json={
        "notes": "late update",
    })
    assert response.status_code == 409


def test_list_appointments_filter_by_date(client, vet_headers, appointment):
    date_str = appointment.scheduled_at.strftime("%Y-%m-%d")
    response = client.get(f"/api/v1/appointments/?date={date_str}", headers=vet_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_list_appointments_filter_wrong_date(client, vet_headers, appointment):
    response = client.get("/api/v1/appointments/?date=2099-01-01", headers=vet_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_receptionist_can_manage_appointments(client, receptionist_headers, pet, vet_user):
    from datetime import datetime, timedelta
    scheduled = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    response = client.post("/api/v1/appointments/", headers=receptionist_headers, json={
        "pet_id": pet.id,
        "vet_id": vet_user.id,
        "scheduled_at": scheduled,
    })
    assert response.status_code == 200


def test_receptionist_cannot_start_or_write_clinical_weight(
    client, receptionist_headers, appointment
):
    start = client.patch(
        f"/api/v1/appointments/{appointment.id}",
        headers=receptionist_headers,
        json={"status": "in-progress"},
    )
    assert start.status_code == 403
    weight = client.patch(
        f"/api/v1/appointments/{appointment.id}",
        headers=receptionist_headers,
        json={"weight": 12.5},
    )
    assert weight.status_code == 403


def test_appointment_rejects_invalid_and_terminal_transitions(client, vet_headers, appointment):
    skipped = client.patch(
        f"/api/v1/appointments/{appointment.id}",
        headers=vet_headers,
        json={"status": "completed"},
    )
    assert skipped.status_code == 409
    no_reason = client.patch(
        f"/api/v1/appointments/{appointment.id}",
        headers=vet_headers,
        json={"status": "no-show"},
    )
    assert no_reason.status_code == 422
    no_show = client.patch(
        f"/api/v1/appointments/{appointment.id}",
        headers=vet_headers,
        json={"status": "no-show", "status_reason": "Não compareceu"},
    )
    assert no_show.status_code == 200
    assert no_show.json()["status_reason"] == "Não compareceu"
    assert client.patch(
        f"/api/v1/appointments/{appointment.id}",
        headers=vet_headers,
        json={"status": "in-progress"},
    ).status_code == 409


def test_started_appointment_cannot_change_schedule(client, vet_headers, appointment):
    assert client.patch(
        f"/api/v1/appointments/{appointment.id}",
        headers=vet_headers,
        json={"status": "in-progress"},
    ).status_code == 200
    response = client.patch(
        f"/api/v1/appointments/{appointment.id}",
        headers=vet_headers,
        json={"duration_min": 60},
    )
    assert response.status_code == 409


def test_archived_pet_cannot_be_scheduled(client, vet_headers, pet, vet_user):
    from datetime import datetime, timedelta

    assert client.delete(f"/api/v1/pets/{pet.id}", headers=vet_headers).status_code == 200
    response = client.post("/api/v1/appointments/", headers=vet_headers, json={
        "pet_id": pet.id,
        "vet_id": vet_user.id,
        "scheduled_at": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
    })
    assert response.status_code == 404


def test_appointments_scoped_by_clinic(client, vet_headers, appointment, db_session):
    from datetime import datetime, timedelta

    from src.models.appointment import Appointment
    from src.models.clinic import Clinic
    other_clinic = Clinic(name="Other Clinic")
    db_session.add(other_clinic)
    db_session.commit()
    other_appt = Appointment(
        clinic_id=other_clinic.id,
        pet_id=appointment.pet_id,
        vet_id=appointment.vet_id,
        owner_id=appointment.owner_id,
        scheduled_at=datetime.now(UTC) + timedelta(days=1),
    )
    db_session.add(other_appt)
    db_session.commit()

    response = client.get("/api/v1/appointments/", headers=vet_headers)
    ids = [a["id"] for a in response.json()]
    assert appointment.id in ids
    assert other_appt.id not in ids
