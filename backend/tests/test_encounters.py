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


def test_admin_can_configure_service_and_exam_catalog(client, vet_headers):
    service = client.post("/api/v1/service-types/", json={"name": "Internamento"}, headers=vet_headers)
    assert service.status_code == 200
    assert service.json()["slug"] == "internamento"

    system = client.post("/api/v1/exam-catalog/systems", json={"name": "Avaliação neurológica"}, headers=vet_headers)
    assert system.status_code == 200
    finding = client.post(
        f"/api/v1/exam-catalog/systems/{system.json()['id']}/findings",
        json={"name": "Marcha alterada"},
        headers=vet_headers,
    )
    assert finding.status_code == 200
