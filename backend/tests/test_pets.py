def test_list_pets_empty(client, vet_headers):
    response = client.get("/api/v1/pets/", headers=vet_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_pet(client, vet_headers, owner):
    response = client.post("/api/v1/pets/", headers=vet_headers, json={
        "owner_id": owner.id,
        "name": "Rex",
        "species": "Cão",
        "breed": "Labrador",
        "age": "2 years",
        "weight": 25.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Rex"
    assert data["owner_id"] == owner.id
    assert data["clinic_id"] is not None


def test_get_pet(client, vet_headers, pet):
    response = client.get(f"/api/v1/pets/{pet.id}", headers=vet_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Pet"


def test_get_pet_not_found(client, vet_headers):
    response = client.get("/api/v1/pets/99999", headers=vet_headers)
    assert response.status_code == 404


def test_update_pet(client, vet_headers, pet):
    response = client.patch(f"/api/v1/pets/{pet.id}", headers=vet_headers, json={
        "name": "Updated Pet",
        "weight": 30.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Pet"
    assert data["weight"] == 30.0


def test_delete_pet(client, vet_headers, pet):
    response = client.delete(f"/api/v1/pets/{pet.id}", headers=vet_headers)
    assert response.status_code == 200
    assert response.json()["ok"] is True
    response = client.get(f"/api/v1/pets/{pet.id}", headers=vet_headers)
    assert response.status_code == 404


def test_receptionist_can_manage_pets(client, receptionist_headers, owner):
    response = client.post("/api/v1/pets/", headers=receptionist_headers, json={
        "owner_id": owner.id,
        "name": "Recep Pet",
        "species": "Gato",
    })
    assert response.status_code == 200


def test_pets_scoped_by_clinic(client, vet_headers, pet, db_session):
    from app.models.clinic import Clinic
    from app.models.pet import Pet
    other_clinic = Clinic(name="Other Clinic")
    db_session.add(other_clinic)
    db_session.commit()
    other_pet = Pet(clinic_id=other_clinic.id, owner_id=pet.owner_id, name="Other Pet", species="Cão")
    db_session.add(other_pet)
    db_session.commit()

    response = client.get("/api/v1/pets/", headers=vet_headers)
    ids = [p["id"] for p in response.json()]
    assert pet.id in ids
    assert other_pet.id not in ids