def test_list_invoices_empty(client, vet_headers):
    response = client.get("/api/v1/invoices/", headers=vet_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_invoice(client, vet_headers, owner):
    response = client.post("/api/v1/invoices/", headers=vet_headers, json={
        "owner_id": owner.id,
        "amount": 2500.0,
        "description": "Consulta + Vacinação",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["owner_id"] == owner.id
    assert data["amount"] == 2500.0
    assert data["status"] == "draft"


def test_get_invoice(client, vet_headers, invoice):
    response = client.get(f"/api/v1/invoices/{invoice.id}", headers=vet_headers)
    assert response.status_code == 200
    assert response.json()["amount"] == 100.0


def test_get_invoice_not_found(client, vet_headers):
    response = client.get("/api/v1/invoices/99999", headers=vet_headers)
    assert response.status_code == 404


def test_update_invoice(client, vet_headers, invoice):
    response = client.patch(f"/api/v1/invoices/{invoice.id}", headers=vet_headers, json={
        "status": "paid",
        "amount": 150.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "paid"
    assert data["amount"] == 150.0


def test_sync_invoice_uses_mock_adapter(client, vet_headers, invoice):
    response = client.post(f"/api/v1/invoices/{invoice.id}/sync", headers=vet_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"
    assert data["sync_status"] == "synced"
    assert data["external_reference"].startswith("mock-patas-")

    status_response = client.get(f"/api/v1/invoices/{invoice.id}/sync-status", headers=vet_headers)
    assert status_response.status_code == 200
    assert status_response.json()["external_status"] == "sent"


def test_invoice_rejects_mismatched_appointment_owner(client, vet_headers, appointment, clinic, db_session):
    from src.models.owner import Owner
    other_owner = Owner(clinic_id=clinic.id, name="Other Owner")
    db_session.add(other_owner)
    db_session.commit()
    response = client.post("/api/v1/invoices/", headers=vet_headers, json={
        "owner_id": other_owner.id,
        "appointment_id": appointment.id,
        "amount": 100,
    })
    assert response.status_code == 422


def test_delete_invoice(client, vet_headers, invoice):
    response = client.delete(f"/api/v1/invoices/{invoice.id}", headers=vet_headers)
    assert response.status_code == 405
    response = client.get(f"/api/v1/invoices/{invoice.id}", headers=vet_headers)
    assert response.status_code == 200


def test_receptionist_can_create_invoice(client, receptionist_headers, owner):
    response = client.post("/api/v1/invoices/", headers=receptionist_headers, json={
        "owner_id": owner.id,
        "amount": 100.0,
    })
    assert response.status_code == 200


def test_cancel_invoice_requires_reason_and_is_terminal(client, vet_headers, invoice):
    missing_reason = client.patch(
        f"/api/v1/invoices/{invoice.id}",
        headers=vet_headers,
        json={"status": "cancelled"},
    )
    assert missing_reason.status_code == 422
    cancelled = client.patch(
        f"/api/v1/invoices/{invoice.id}",
        headers=vet_headers,
        json={"status": "cancelled", "reason": "Emitida por engano"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert client.patch(
        f"/api/v1/invoices/{invoice.id}",
        headers=vet_headers,
        json={"status": "paid"},
    ).status_code == 409
    assert client.post(
        f"/api/v1/invoices/{invoice.id}/sync",
        headers=vet_headers,
    ).status_code == 409


def test_receptionist_can_read_invoices(client, receptionist_headers, invoice):
    response = client.get("/api/v1/invoices/", headers=receptionist_headers)
    assert response.status_code == 200
    ids = [i["id"] for i in response.json()]
    assert invoice.id in ids


def test_invoices_scoped_by_clinic(client, vet_headers, invoice, db_session):
    from src.models.clinic import Clinic
    from src.models.invoice import Invoice
    other_clinic = Clinic(name="Other Clinic")
    db_session.add(other_clinic)
    db_session.commit()
    other_invoice = Invoice(
        clinic_id=other_clinic.id,
        owner_id=invoice.owner_id,
        amount=500.0,
    )
    db_session.add(other_invoice)
    db_session.commit()

    response = client.get("/api/v1/invoices/", headers=vet_headers)
    ids = [i["id"] for i in response.json()]
    assert invoice.id in ids
    assert other_invoice.id not in ids
