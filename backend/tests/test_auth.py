def test_register(client, db_session):
    response = client.post("/api/v1/auth/register", json={
        "clinic_name": "Nova Clínica",
        "name": "New User",
        "email": "new@test.com",
        "password": "Password1",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new@test.com"
    assert data["role"] == "admin"
    assert data["clinic_name"] == "Nova Clínica"
    assert data["must_change_password"] is False
    assert "id" in data


def test_register_duplicate_email(client, vet_user):
    response = client.post("/api/v1/auth/register", json={
        "clinic_name": "Duplicate Clinic",
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


def test_blacklisted_refresh_token_cannot_change_password(client, vet_user):
    tokens = client.post("/api/v1/auth/login", json={
        "email": vet_user.email,
        "password": "Password1",
    }).json()
    rotated = client.post("/api/v1/auth/refresh", json={
        "refresh_token": tokens["refresh_token"],
    })
    assert rotated.status_code == 200

    response = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={
            "current_password": "Password1",
            "new_password": "Permanent2",
            "refresh_token": tokens["refresh_token"],
        },
    )
    assert response.status_code == 401


def test_login_wrong_password(client, vet_user):
    response = client.post("/api/v1/auth/login", json={
        "email": "vet@test.com",
        "password": "WrongPass1",
    })
    assert response.status_code == 401


def test_login_unknown_email_does_not_fail_with_server_error(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "missing@test.com",
        "password": "Password1",
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


def test_register_rejects_role_selection(client):
    response = client.post("/api/v1/auth/register", json={
        "clinic_name": "Nova Clínica",
        "name": "Public User",
        "email": "public@test.com",
        "password": "Password1",
        "role": "receptionist",
    })
    assert response.status_code == 422


def test_refresh_token_cannot_authenticate_protected_endpoint(client, vet_user):
    tokens = client.post("/api/v1/auth/login", json={
        "email": vet_user.email,
        "password": "Password1",
    }).json()
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )
    assert response.status_code == 401


def test_temporary_password_change_and_logout_revoke_both_tokens(client, vet_headers):
    created = client.post("/api/v1/users/", headers=vet_headers, json={
        "name": "Dra. Temporária",
        "email": "temporary@test.com",
        "password": "Temporary1",
        "role": "vet",
    })
    assert created.status_code == 201
    assert created.json()["must_change_password"] is True

    login = client.post("/api/v1/auth/login", json={
        "email": "temporary@test.com",
        "password": "Temporary1",
    })
    old_tokens = login.json()
    old_headers = {"Authorization": f"Bearer {old_tokens['access_token']}"}
    assert old_tokens["must_change_password"] is True
    assert client.get("/api/v1/auth/me", headers=old_headers).status_code == 200
    blocked = client.get("/api/v1/owners/", headers=old_headers)
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "PASSWORD_CHANGE_REQUIRED"

    changed = client.post("/api/v1/auth/change-password", headers=old_headers, json={
        "current_password": "Temporary1",
        "new_password": "Permanent2",
        "refresh_token": old_tokens["refresh_token"],
    })
    assert changed.status_code == 200
    new_tokens = changed.json()
    assert new_tokens["must_change_password"] is False
    assert client.get("/api/v1/auth/me", headers=old_headers).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={
        "refresh_token": old_tokens["refresh_token"],
    }).status_code == 401

    new_headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
    assert client.get("/api/v1/owners/", headers=new_headers).status_code == 200
    logout = client.post("/api/v1/auth/logout", headers=new_headers, json={
        "refresh_token": new_tokens["refresh_token"],
    })
    assert logout.status_code == 200
    assert client.get("/api/v1/auth/me", headers=new_headers).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={
        "refresh_token": new_tokens["refresh_token"],
    }).status_code == 401
