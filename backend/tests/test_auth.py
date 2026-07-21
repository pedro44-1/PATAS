def test_register(client, db_session):
    from app.models.clinic import Clinic
    response = client.post("/api/v1/auth/register", json={
        "name": "New User",
        "email": "new@test.com",
        "password": "Password1",
        "role": "receptionist",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new@test.com"
    assert data["role"] == "receptionist"
    assert "id" in data


def test_register_duplicate_email(client, vet_user):
    response = client.post("/api/v1/auth/register", json={
        "name": "Duplicate",
        "email": "vet@test.com",
        "password": "Password1",
    })
    assert response.status_code == 400
    assert "Email já registado" in response.text


def test_login_success(client, vet_user):
    response = client.post("/api/v1/auth/login", json={
        "email": "vet@test.com",
        "password": "Password1",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token(client, vet_user):
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "vet@test.com",
        "password": "Password1",
    })
    data = login_resp.json()
    refresh = data["refresh_token"]

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    new_data = resp.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data


def test_refresh_token_used_twice(client, vet_user):
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "vet@test.com",
        "password": "Password1",
    })
    refresh = login_resp.json()["refresh_token"]

    resp1 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp1.status_code == 200

    resp2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp2.status_code == 401


def test_login_wrong_password(client, vet_user):
    response = client.post("/api/v1/auth/login", json={
        "email": "vet@test.com",
        "password": "WrongPass1",
    })
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "nobody@test.com",
        "password": "Password1",
    })
    assert response.status_code == 401


def test_me_authenticated(client, vet_headers, vet_user):
    response = client.get("/api/v1/auth/me", headers=vet_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "vet@test.com"
    assert data["role"] == "admin"


def test_me_unauthenticated(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403