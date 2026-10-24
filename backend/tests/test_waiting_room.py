from datetime import UTC, datetime


def test_waiting_room_check_in_and_transitions(client, appointment, receptionist_headers, vet_headers):
    services = client.get("/api/v1/service-types/", headers=receptionist_headers)
    assert services.status_code == 200
    service_id = next(item["id"] for item in services.json() if item["slug"] == "consulta")

    created = client.post(
        "/api/v1/waiting-room/entries",
        json={"appointment_id": appointment.id, "service_type_id": service_id, "room": "Consultório 1"},
        headers=receptionist_headers,
    )
    assert created.status_code == 200
    entry = created.json()
    assert entry["service_type_name"] == "Consulta"
    assert entry["status"] == "waiting"

    duplicate = client.post(
        "/api/v1/waiting-room/entries",
        json={"appointment_id": appointment.id},
        headers=receptionist_headers,
    )
    assert duplicate.status_code == 409

    called = client.post(
        f"/api/v1/waiting-room/entries/{entry['id']}/transition",
        json={"status": "called"},
        headers=receptionist_headers,
    )
    assert called.status_code == 200
    assert called.json()["status"] == "called"

    started = client.post(
        f"/api/v1/waiting-room/entries/{entry['id']}/transition",
        json={"status": "in-progress"},
        headers=vet_headers,
    )
    assert started.status_code == 200
    assert started.json()["status"] == "in-progress"

    completed = client.post(
        f"/api/v1/waiting-room/entries/{entry['id']}/transition",
        json={"status": "completed"},
        headers=vet_headers,
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    appointment_response = client.get(f"/api/v1/appointments/{appointment.id}", headers=vet_headers)
    assert appointment_response.json()["status"] == "completed"


def test_waiting_room_supports_walk_in(client, pet, vet_user, receptionist_headers):
    response = client.post(
        "/api/v1/waiting-room/entries",
        json={
            "pet_id": pet.id,
            "vet_id": vet_user.id,
            "reason": "Dor abdominal",
            "scheduled_at": datetime.now(UTC).isoformat(),
        },
        headers=receptionist_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["pet_id"] == pet.id
    assert payload["reason"] == "Dor abdominal"
    assert payload["status"] == "waiting"


def test_waiting_room_requires_cancel_reason(client, appointment, receptionist_headers):
    created = client.post(
        "/api/v1/waiting-room/entries",
        json={"appointment_id": appointment.id},
        headers=receptionist_headers,
    )
    entry_id = created.json()["id"]
    response = client.post(
        f"/api/v1/waiting-room/entries/{entry_id}/transition",
        json={"status": "cancelled", "reason": "  "},
        headers=receptionist_headers,
    )
    assert response.status_code == 422


def test_waiting_room_enforces_transition_matrix_and_clinical_roles(
    client, appointment, receptionist_headers, vet_headers
):
    created = client.post(
        "/api/v1/waiting-room/entries",
        json={"appointment_id": appointment.id},
        headers=receptionist_headers,
    )
    entry_id = created.json()["id"]
    skipped = client.post(
        f"/api/v1/waiting-room/entries/{entry_id}/transition",
        json={"status": "in-progress"},
        headers=vet_headers,
    )
    assert skipped.status_code == 409
    called = client.post(
        f"/api/v1/waiting-room/entries/{entry_id}/transition",
        json={"status": "called"},
        headers=receptionist_headers,
    )
    assert called.status_code == 200
    receptionist_start = client.post(
        f"/api/v1/waiting-room/entries/{entry_id}/transition",
        json={"status": "in-progress"},
        headers=receptionist_headers,
    )
    assert receptionist_start.status_code == 403
    backwards = client.post(
        f"/api/v1/waiting-room/entries/{entry_id}/transition",
        json={"status": "waiting"},
        headers=vet_headers,
    )
    assert backwards.status_code == 409


def test_waiting_room_no_show_requires_reason_and_syncs_appointment(
    client, appointment, receptionist_headers, vet_headers
):
    created = client.post(
        "/api/v1/waiting-room/entries",
        json={"appointment_id": appointment.id},
        headers=receptionist_headers,
    )
    entry_id = created.json()["id"]
    missing = client.post(
        f"/api/v1/waiting-room/entries/{entry_id}/transition",
        json={"status": "no-show"},
        headers=receptionist_headers,
    )
    assert missing.status_code == 422
    no_show = client.post(
        f"/api/v1/waiting-room/entries/{entry_id}/transition",
        json={"status": "no-show", "reason": "Não compareceu"},
        headers=receptionist_headers,
    )
    assert no_show.status_code == 200
    assert no_show.json()["status_reason"] == "Não compareceu"
    appointment_response = client.get(
        f"/api/v1/appointments/{appointment.id}", headers=vet_headers
    )
    assert appointment_response.json()["status"] == "no-show"
