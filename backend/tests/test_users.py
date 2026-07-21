def test_admin_can_list_users(client, vet_headers, receptionist_user):
    response = client.get("/api/v1/users/", headers=vet_headers)
    assert response.status_code == 200
    users = response.json()
    assert any(u["email"] == receptionist_user.email for u in users)


def test_receptionist_cannot_list_users(client, receptionist_headers):
    response = client.get("/api/v1/users/", headers=receptionist_headers)
    assert response.status_code == 403


def test_admin_can_update_user_role(client, vet_headers, receptionist_user):
    response = client.patch(
        f"/api/v1/users/{receptionist_user.id}/role",
        headers=vet_headers,
        json={"role": "vet"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "vet"


def test_receptionist_cannot_update_user_role(client, receptionist_headers, vet_user):
    response = client.patch(
        f"/api/v1/users/{vet_user.id}/role",
        headers=receptionist_headers,
        json={"role": "receptionist"},
    )
    assert response.status_code == 403