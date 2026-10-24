def test_pet_history_returns_appointments_and_treatment(client, vet_headers, pet, appointment, treatment):
    response = client.get(f"/api/v1/pets/{pet.id}/history", headers=vet_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["pet_id"] == pet.id
    assert data["appointments"][0]["id"] == appointment.id
    assert data["appointments"][0]["treatment"]["id"] == treatment.id


def test_pet_history_is_clinic_scoped(client, vet_headers, pet):
    response = client.get("/api/v1/pets/99999/history", headers=vet_headers)
    assert response.status_code == 404
