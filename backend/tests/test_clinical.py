from datetime import UTC, date, datetime, timedelta

from src.models.clinic import Clinic
from src.models.owner import Owner
from src.models.pet import Pet


def vaccination_payload(pet_id, vet_id, appointment_id=None, administered_at=None):
    return {
        "pet_id": pet_id,
        "vet_id": vet_id,
        "appointment_id": appointment_id,
        "name": "V10",
        "administered_at": (administered_at or datetime.now(UTC)).isoformat(),
        "dose": "1 ml",
        "lot_number": "LOT-001",
        "next_due_at": (date.today() + timedelta(days=365)).isoformat(),
        "notes": "Aplicada sem reação",
    }


def medication_payload(pet_id, vet_id, appointment_id=None):
    return {
        "pet_id": pet_id,
        "vet_id": vet_id,
        "appointment_id": appointment_id,
        "name": "Amoxicilina",
        "dosage": "250 mg",
        "frequency": "12/12h",
        "route": "oral",
        "start_date": date.today().isoformat(),
        "instructions": "Administrar após a refeição",
    }


def test_vaccination_crud_void_and_history(client, vet_headers, pet, appointment, vet_user):
    response = client.post(
        "/api/v1/vaccinations/",
        json=vaccination_payload(pet.id, vet_user.id, appointment.id),
        headers=vet_headers,
    )
    assert response.status_code == 200
    vaccination = response.json()
    assert vaccination["vet_name"] == vet_user.name

    updated = client.patch(
        f"/api/v1/vaccinations/{vaccination['id']}",
        json={"dose": "1.5 ml"},
        headers=vet_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["dose"] == "1.5 ml"

    missing_reason = client.post(
        f"/api/v1/vaccinations/{vaccination['id']}/void",
        json={"reason": "   "},
        headers=vet_headers,
    )
    assert missing_reason.status_code == 422

    voided = client.post(
        f"/api/v1/vaccinations/{vaccination['id']}/void",
        json={"reason": "Registo duplicado"},
        headers=vet_headers,
    )
    assert voided.status_code == 200
    assert voided.json()["status"] == "voided"

    history = client.get(f"/api/v1/pets/{pet.id}/history", headers=vet_headers)
    assert history.status_code == 200
    assert history.json()["vaccinations"][0]["status"] == "voided"


def test_medication_crud_status_and_date_validation(client, vet_headers, pet, appointment, vet_user):
    invalid = medication_payload(pet.id, vet_user.id, appointment.id)
    invalid["end_date"] = (date.today() - timedelta(days=1)).isoformat()
    assert client.post("/api/v1/medications/", json=invalid, headers=vet_headers).status_code == 422

    response = client.post(
        "/api/v1/medications/",
        json=medication_payload(pet.id, vet_user.id, appointment.id),
        headers=vet_headers,
    )
    assert response.status_code == 200
    medication = response.json()

    updated = client.patch(
        f"/api/v1/medications/{medication['id']}",
        json={"status": "completed", "frequency": "24/24h"},
        headers=vet_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "completed"
    assert updated.json()["frequency"] == "24/24h"


def test_clinical_permissions_and_clinic_scope(
    client, db_session, pet, vet_user, vet_headers, receptionist_headers, receptionist_user
):
    assert client.get(f"/api/v1/vaccinations/?pet_id={pet.id}", headers=receptionist_headers).status_code == 200
    assert client.get(f"/api/v1/medications/?pet_id={pet.id}", headers=receptionist_headers).status_code == 200
    assert client.post(
        "/api/v1/vaccinations/",
        json=vaccination_payload(pet.id, vet_user.id),
        headers=receptionist_headers,
    ).status_code == 403

    other_clinic = Clinic(name="Other Clinic")
    db_session.add(other_clinic)
    db_session.flush()
    other_owner = Owner(clinic_id=other_clinic.id, name="Other Owner")
    db_session.add(other_owner)
    db_session.flush()
    other_pet = Pet(clinic_id=other_clinic.id, owner_id=other_owner.id, name="Other Pet", species="Dog")
    db_session.add(other_pet)
    db_session.commit()

    assert client.get(f"/api/v1/vaccinations/?pet_id={other_pet.id}", headers=receptionist_headers).json() == []
    assert client.post(
        "/api/v1/medications/",
        json=medication_payload(other_pet.id, vet_user.id),
        headers={"Authorization": receptionist_headers["Authorization"]},
    ).status_code == 403
    assert client.post(
        "/api/v1/medications/",
        json=medication_payload(other_pet.id, vet_user.id),
        headers=vet_headers,
    ).status_code == 404


def test_clinical_rejects_non_vet_responsible(client, vet_headers, pet, receptionist_user):
    response = client.post(
        "/api/v1/medications/",
        json=medication_payload(pet.id, receptionist_user.id),
        headers=vet_headers,
    )
    assert response.status_code == 422
