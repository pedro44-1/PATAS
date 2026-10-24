def test_list_owners_empty(client, vet_headers):
    response = client.get("/api/v1/owners/", headers=vet_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_owner(client, vet_headers):
    response = client.post("/api/v1/owners/", headers=vet_headers, json={
        "name": "Maria Owner",
        "phone": "+244 900 000 001",
        "email": "maria@test.com",
        "address": "Rua Teste, Luanda",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Maria Owner"
    assert data["clinic_id"] is not None
    assert "id" in data


def test_get_owner(client, vet_headers, owner):
    response = client.get(f"/api/v1/owners/{owner.id}", headers=vet_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Owner"


def test_get_owner_not_found(client, vet_headers):
    response = client.get("/api/v1/owners/99999", headers=vet_headers)
    assert response.status_code == 404


def test_update_owner(client, vet_headers, owner):
    response = client.patch(f"/api/v1/owners/{owner.id}", headers=vet_headers, json={
        "name": "Updated Owner",
        "phone": "+244 900 000 002",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Owner"
    assert data["phone"] == "+244 900 000 002"


def test_delete_owner(client, vet_headers, owner):
    response = client.delete(f"/api/v1/owners/{owner.id}", headers=vet_headers)
    assert response.status_code == 200
    assert response.json()["ok"] is True
    response = client.get(f"/api/v1/owners/{owner.id}", headers=vet_headers)
    assert response.status_code == 200
    assert response.json()["archived_at"] is not None
    assert client.get("/api/v1/owners/", headers=vet_headers).json() == []
    archived = client.get("/api/v1/owners/?include_archived=true", headers=vet_headers)
    assert any(item["id"] == owner.id for item in archived.json())


def test_archiving_owner_archives_pets_and_blocks_new_invoice(
    client, vet_headers, owner, pet
):
    response = client.delete(f"/api/v1/owners/{owner.id}", headers=vet_headers)
    assert response.status_code == 200
    archived_pet = client.get(f"/api/v1/pets/{pet.id}", headers=vet_headers)
    assert archived_pet.status_code == 200
    assert archived_pet.json()["archived_at"] is not None
    assert client.get("/api/v1/pets/", headers=vet_headers).json() == []
    invoice = client.post("/api/v1/invoices/", headers=vet_headers, json={
        "owner_id": owner.id,
        "amount": 100,
    })
    assert invoice.status_code == 404


def test_receptionist_can_list_owners(client, receptionist_headers):
    response = client.get("/api/v1/owners/", headers=receptionist_headers)
    assert response.status_code == 200


def test_receptionist_can_create_owner(client, receptionist_headers):
    response = client.post("/api/v1/owners/", headers=receptionist_headers, json={
        "name": "Recep Owner",
    })
    assert response.status_code == 200


def test_owners_scoped_by_clinic(client, vet_headers, owner, db_session):
    from src.models.clinic import Clinic
    from src.models.owner import Owner
    other_clinic = Clinic(name="Other Clinic")
    db_session.add(other_clinic)
    db_session.commit()
    other_owner = Owner(clinic_id=other_clinic.id, name="Other Owner")
    db_session.add(other_owner)
    db_session.commit()

    response = client.get("/api/v1/owners/", headers=vet_headers)
    data = response.json()
    ids = [o["id"] for o in data]
    assert owner.id in ids
    assert other_owner.id not in ids


def test_owner_blank_optional_fields_are_stored_as_null(client, vet_headers):
    created = client.post("/api/v1/owners/", headers=vet_headers, json={
        "name": "Sem Email",
        "phone": "",
        "email": "",
        "address": "  ",
        "nif": "",
        "notes": "",
    })
    assert created.status_code == 200
    data = created.json()
    assert data["email"] is None
    assert data["address"] is None

    updated = client.patch(f"/api/v1/owners/{data['id']}", headers=vet_headers, json={"email": ""})
    assert updated.status_code == 200
    assert updated.json()["email"] is None


def test_owner_nif_and_phone_are_validated_and_normalized(client, vet_headers):
    personal = client.post("/api/v1/owners/", headers=vet_headers, json={
        "name": "Ana", "nif": "004 567 890 la 042", "phone": "+244  923 456 789",
    })
    assert personal.status_code == 200
    assert personal.json()["nif"] == "004567890LA042"
    assert personal.json()["phone"] == "+244 923 456 789"

    company = client.post("/api/v1/owners/", headers=vet_headers, json={"name": "Lda", "nif": "5417-123-456"})
    assert company.json()["nif"] == "5417123456"

    invalid_nif = client.post("/api/v1/owners/", headers=vet_headers, json={"name": "X", "nif": "12345"})
    assert invalid_nif.status_code == 422
    invalid_phone = client.post("/api/v1/owners/", headers=vet_headers, json={"name": "X", "phone": "abc"})
    assert invalid_phone.status_code == 422


def test_owner_update_audit_does_not_copy_personal_data(client, vet_headers, owner, db_session):
    from src.models.audit_log import AuditLog

    client.patch(f"/api/v1/owners/{owner.id}", headers=vet_headers, json={"phone": "923000111"})
    entry = db_session.query(AuditLog).filter_by(resource="owner", action="UPDATE").order_by(AuditLog.id.desc()).first()
    assert "923000111" not in (entry.details or "")
    assert "phone" in entry.details
