def test_clinical_record_saves_exam_and_structured_medication(client, appointment, vet_headers, receptionist_headers):
    catalog = client.get("/api/v1/exam-catalog/", headers=receptionist_headers)
    assert catalog.status_code == 200
    finding = catalog.json()["systems"][0]["findings"][0]

    payload = {
        "anamnesis": "Animal com apetite reduzido.",
        "diagnosis": "Avaliação clínica em curso",
        "notes": "Reavaliar em sete dias.",
        "prescription": "Manter hidratação e repouso.",
        "consultation_type": "normal",
        "exam_findings": [{"finding_id": finding["id"], "status": "abnormal", "note": "Dor ligeira"}],
        "medications": [{
            "name": "Amoxicilina",
            "dosage": "250 mg",
            "frequency": "12/12h",
            "route": "oral",
            "start_date": "2026-09-09",
            "end_date": "2026-09-16",
            "instructions": "Administrar após a refeição",
        }],
    }
    response = client.put(f"/api/v1/appointments/{appointment.id}/clinical-record", json=payload, headers=vet_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["treatment"]["anamnesis"] == payload["anamnesis"]
    assert data["exam_findings"][0]["status"] == "abnormal"
    assert data["medications"][0]["name"] == "Amoxicilina"

    history = client.get(f"/api/v1/pets/{appointment.pet_id}/history", headers=receptionist_headers)
    assert history.status_code == 200
    assert history.json()["appointments"][0]["exam_findings"][0]["finding_name"] == finding["name"]


def test_receptionist_can_read_but_not_write_clinical_record(client, appointment, receptionist_headers):
    read = client.get(f"/api/v1/appointments/{appointment.id}/clinical-record", headers=receptionist_headers)
    assert read.status_code == 200
    write = client.put(
        f"/api/v1/appointments/{appointment.id}/clinical-record",
        json={"exam_findings": [], "medications": []},
        headers=receptionist_headers,
    )
    assert write.status_code == 403


def test_admin_can_configure_service_and_exam_catalog(client, admin_headers):
    service = client.post("/api/v1/service-types/", json={"name": "Internamento"}, headers=admin_headers)
    assert service.status_code == 200
    assert service.json()["slug"] == "internamento"

    system = client.post("/api/v1/exam-catalog/systems", json={"name": "Avaliação neurológica"}, headers=admin_headers)
    assert system.status_code == 200
    finding = client.post(
        f"/api/v1/exam-catalog/systems/{system.json()['id']}/findings",
        json={"name": "Marcha alterada"},
        headers=admin_headers,
    )
    assert finding.status_code == 200


def _first_finding(client, headers):
    return client.get("/api/v1/exam-catalog/", headers=headers).json()["systems"][0]["findings"][0]


def test_completed_record_correction_requires_reason_and_keeps_observation(
    client, appointment, vet_headers, receptionist_headers, db_session
):
    from src.models.appointment import AppointmentStatus
    from src.models.clinical_exam import ClinicalExamObservation

    finding = _first_finding(client, vet_headers)
    url = f"/api/v1/appointments/{appointment.id}/clinical-record"
    first = client.put(url, headers=vet_headers, json={
        "diagnosis": "Inicial",
        "exam_findings": [{"finding_id": finding["id"], "status": "abnormal", "note": "Dor"}],
    })
    assert first.status_code == 200
    appointment.status = AppointmentStatus.COMPLETED
    db_session.commit()

    correction = {
        "diagnosis": "Corrigido",
        "exam_findings": [{"finding_id": finding["id"], "status": "not-evaluated"}],
    }
    assert client.put(url, headers=vet_headers, json=correction).status_code == 422
    corrected = client.put(url, headers=vet_headers, json={**correction, "correction_reason": "Erro de digitação"})
    assert corrected.status_code == 200
    assert corrected.json()["treatment"]["diagnosis"] == "Corrigido"
    kept = db_session.query(ClinicalExamObservation).filter_by(appointment_id=appointment.id).one()
    assert kept.status == "not-evaluated"
    history = client.get(f"/api/v1/pets/{appointment.pet_id}/history", headers=vet_headers).json()
    assert history["appointments"][0]["exam_findings"] == []


def test_cancelled_appointment_rejects_clinical_record(client, appointment, vet_headers, db_session):
    from src.models.appointment import AppointmentStatus

    appointment.status = AppointmentStatus.CANCELLED
    appointment.status_reason = "Dono desmarcou"
    db_session.commit()
    response = client.put(
        f"/api/v1/appointments/{appointment.id}/clinical-record",
        headers=vet_headers,
        json={"diagnosis": "x", "correction_reason": "y"},
    )
    assert response.status_code == 409


def test_treatment_patch_on_completed_appointment_requires_reason(client, treatment, appointment, vet_headers, db_session):
    from src.models.appointment import AppointmentStatus

    appointment.status = AppointmentStatus.COMPLETED
    db_session.commit()
    url = f"/api/v1/treatments/{treatment.id}"
    assert client.patch(url, headers=vet_headers, json={"diagnosis": "Novo"}).status_code == 422
    assert client.patch(
        url, headers=vet_headers, json={"diagnosis": "Novo", "correction_reason": "Resultado laboratorial"}
    ).status_code == 200


def test_archived_pet_blocks_check_in_record_and_invoice(client, appointment, owner, vet_headers):
    archived = client.delete(f"/api/v1/pets/{appointment.pet_id}", headers=vet_headers)
    assert archived.status_code in {200, 204}

    check_in = client.post("/api/v1/waiting-room/entries", headers=vet_headers, json={"appointment_id": appointment.id})
    assert check_in.status_code == 409
    record = client.put(
        f"/api/v1/appointments/{appointment.id}/clinical-record", headers=vet_headers, json={"diagnosis": "x"}
    )
    assert record.status_code == 409
    invoice = client.post("/api/v1/invoices/", headers=vet_headers, json={
        "owner_id": owner.id,
        "appointment_id": appointment.id,
        "items": [{"description": "Consulta", "kind": "SERVICE", "unit": "UN", "quantity": 1, "unit_price": 100, "tax_rate": 0}],
    })
    assert invoice.status_code == 409
    cancelled = client.patch(
        f"/api/v1/appointments/{appointment.id}", headers=vet_headers,
        json={"status": "cancelled", "status_reason": "Animal arquivado"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["subject_archived"] is True
