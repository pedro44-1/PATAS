def test_list_invoices_empty(client, vet_headers):
    response = client.get("/api/v1/invoices/", headers=vet_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_invoice(client, vet_headers, owner):
    response = client.post("/api/v1/invoices/", headers=vet_headers, json={
        "owner_id": owner.id,
        "amount": 2500.0,
        "description": "Consulta + VacinaГ§ГЈo",
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


def test_delete_invoice(client, vet_headers, invoice):
    response = client.delete(f"/api/v1/invoices/{invoice.id}", headers=vet_headers)
    assert response.status_code == 200
    assert response.json()["ok"] is True
    response = client.get(f"/api/v1/invoices/{invoice.id}", headers=vet_headers)
    assert response.status_code == 404


def test_receptionist_cannot_create_invoice(client, receptionist_headers, owner):
    response = client.post("/api/v1/invoices/", headers=receptionist_headers, json={
        "owner_id": owner.id,
        "amount": 100.0,
    })
    assert response.status_code == 403


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