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
    assert response.status_code == 404


def test_receptionist_can_list_owners(client, receptionist_headers):
    response = client.get("/api/v1/owners/", headers=receptionist_headers)
    assert response.status_code == 200


def test_receptionist_can_create_owner(client, receptionist_headers):
    response = client.post("/api/v1/owners/", headers=receptionist_headers, json={
        "name": "Recep Owner",
    })
    assert response.status_code == 200


def test_owners_scoped_by_clinic(client, vet_headers, owner, db_session):
    from app.models.clinic import Clinic
    from app.models.owner import Owner
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