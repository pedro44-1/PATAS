def test_list_treatments_empty(client, vet_headers):
    response = client.get("/api/v1/treatments/", headers=vet_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_treatment(client, vet_headers, appointment):
    response = client.post("/api/v1/treatments/", headers=vet_headers, json={
        "appointment_id": appointment.id,
        "diagnosis": "Test diagnosis",
        "notes": "Test notes",
        "prescription": "Test prescription",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["appointment_id"] == appointment.id
    assert data["diagnosis"] == "Test diagnosis"


def test_get_treatment(client, vet_headers, treatment):
    response = client.get(f"/api/v1/treatments/{treatment.id}", headers=vet_headers)
    assert response.status_code == 200
    assert response.json()["diagnosis"] == "Test diagnosis"


def test_get_treatment_not_found(client, vet_headers):
    response = client.get("/api/v1/treatments/99999", headers=vet_headers)
    assert response.status_code == 404


def test_update_treatment(client, vet_headers, treatment):
    response = client.patch(f"/api/v1/treatments/{treatment.id}", headers=vet_headers, json={
        "diagnosis": "Updated diagnosis",
        "prescription": "Updated prescription",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["diagnosis"] == "Updated diagnosis"
    assert data["prescription"] == "Updated prescription"


def test_vet_can_create_treatment(client, vet_headers, appointment):
    response = client.post("/api/v1/treatments/", headers=vet_headers, json={
        "appointment_id": appointment.id,
        "diagnosis": "Vet diagnosis",
    })
    assert response.status_code == 200


def test_receptionist_cannot_create_treatment(client, receptionist_headers, appointment):
    response = client.post("/api/v1/treatments/", headers=receptionist_headers, json={
        "appointment_id": appointment.id,
        "diagnosis": "Recep diagnosis",
    })
    assert response.status_code == 403


def test_delete_treatment(client, vet_headers, treatment):
    response = client.delete(f"/api/v1/treatments/{treatment.id}", headers=vet_headers)
    assert response.status_code == 200
    assert response.json()["ok"] is True
    response = client.get(f"/api/v1/treatments/{treatment.id}", headers=vet_headers)
    assert response.status_code == 404


def test_receptionist_cannot_delete_treatment(client, receptionist_headers, treatment):
    response = client.delete(f"/api/v1/treatments/{treatment.id}", headers=receptionist_headers)
    assert response.status_code == 403


def test_treatments_scoped_by_clinic(client, vet_headers, treatment, db_session):
    from src.models.clinic import Clinic
    from src.models.treatment import Treatment
    from src.models.appointment import Appointment
    from datetime import datetime, timezone, timedelta
    other_clinic = Clinic(name="Other Clinic")
    db_session.add(other_clinic)
    db_session.commit()
    other_appt = Appointment(
        clinic_id=other_clinic.id,
        pet_id=treatment.appointment.pet_id,
        vet_id=treatment.appointment.vet_id,
        owner_id=treatment.appointment.owner_id,
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(other_appt)
    db_session.commit()
    other_treatment = Treatment(
        clinic_id=other_clinic.id,
        appointment_id=other_appt.id,
        diagnosis="Other diagnosis",
    )
    db_session.add(other_treatment)
    db_session.commit()

    response = client.get("/api/v1/treatments/", headers=vet_headers)
    ids = [t["id"] for t in response.json()]
    assert treatment.id in ids
    assert other_treatment.id not in ids