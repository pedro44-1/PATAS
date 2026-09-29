"""
End-to-end integration test for the PATAS API.

Runs the full API flow: register → login → CRUD owners/pets/appointments/treatments/invoices
→ refresh token → permissions → logout.

Set BASE_URL env var to test against a live Docker stack (e.g. http://localhost:8001).
If unset, falls back to FastAPI TestClient with SQLite.
"""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, time, timedelta
from threading import Barrier
from zoneinfo import ZoneInfo

import pytest

BASE_URL = os.environ.get("BASE_URL")

if BASE_URL:
    import httpx
    client_factory = lambda: httpx.Client(base_url=BASE_URL)
    API_PREFIX = "/api/v1"
else:
    from fastapi.testclient import TestClient

    from src.main import app
    client_factory = lambda: TestClient(app)
    API_PREFIX = "/api/v1"


def _url(path):
    return f"{API_PREFIX}{path}"


pytestmark = pytest.mark.integration


@pytest.fixture
def api():
    with client_factory() as c:
        yield c


_TEST_EMAIL = "integration@test.ao"
_TEST_PASSWORD = "Password1"


def _email(suffix: str) -> str:
    return f"integration.{suffix}@test.ao"


class TestFullFlow:
    """Runs the full API lifecycle: register → login → CRUD → logout."""

    def _register(self, api, suffix: str):
        """Register a new clinic + admin user. Returns the user dict."""
        resp = api.post(_url("/auth/register"), json={
            "clinic_name": f"Clínica Integration {suffix}",
            "name": f"Integration Test {suffix}",
            "email": _email(suffix),
            "password": _TEST_PASSWORD,
        })
        assert resp.status_code == 200, f"register failed: {resp.text}"
        return resp.json()

    def _login(self, api, suffix: str):
        resp = api.post(_url("/auth/login"), json={
            "email": _email(suffix),
            "password": _TEST_PASSWORD,
        })
        assert resp.status_code == 200, f"login failed: {resp.text}"
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        return data

    def test_01_register_and_login(self, api):
        self._register(api, "register")
        tokens = self._login(api, "register")
        assert len(tokens["access_token"]) > 20

    def test_02_me(self, api):
        self._register(api, "me")
        tokens = self._login(api, "me")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        resp = api.get(_url("/auth/me"), headers=headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == _email("me")

    def test_03_full_crud(self, api):
        """Complete CRUD flow: owner → pet → appointment → treatment → invoice."""
        suffix = "crud"
        self._register(api, suffix)
        tokens = self._login(api, suffix)
        h = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Create owner
        owner_resp = api.post(_url("/owners/"), json={
            "name": "João Teste",
            "phone": "+244 900 111 222",
            "email": "joao.crud@test.ao",
        }, headers=h)
        assert owner_resp.status_code == 200, f"create owner: {owner_resp.text}"
        owner = owner_resp.json()
        assert owner["name"] == "João Teste"
        owner_id = owner["id"]

        # List owners
        owners_resp = api.get(_url("/owners/"), headers=h)
        assert owners_resp.status_code == 200
        assert any(o["id"] == owner_id for o in owners_resp.json())

        # Create pet
        pet_resp = api.post(_url("/pets/"), json={
            "owner_id": owner_id,
            "name": "Rex",
            "species": "cão",
            "breed": "Labrador",
            "weight": 28.5,
        }, headers=h)
        assert pet_resp.status_code == 200, f"create pet: {pet_resp.text}"
        pet = pet_resp.json()
        assert pet["name"] == "Rex"
        pet_id = pet["id"]

        # List pets
        pets_resp = api.get(_url("/pets/"), headers=h)
        assert pets_resp.status_code == 200
        assert any(p["id"] == pet_id for p in pets_resp.json())

        # Get vet_id from users list
        users_resp = api.get(_url("/users/"), headers=h)
        assert users_resp.status_code == 200
        vet_id = users_resp.json()[0]["id"]

        # Create appointment
        from datetime import datetime, timedelta
        appt_time = (datetime.now(UTC) + timedelta(days=7)).isoformat()
        appt_resp = api.post(_url("/appointments/"), json={
            "pet_id": pet_id,
            "vet_id": vet_id,
            "scheduled_at": appt_time,
            "duration_min": 30,
            "reason": "Vacinação anual",
        }, headers=h)
        assert appt_resp.status_code == 200, f"create appointment: {appt_resp.text}"
        appt = appt_resp.json()
        assert appt["reason"] == "Vacinação anual"
        appt_id = appt["id"]

        # List appointments
        appts_resp = api.get(_url("/appointments/"), headers=h)
        assert appts_resp.status_code == 200
        assert any(a["id"] == appt_id for a in appts_resp.json())

        # Create treatment
        tx_resp = api.post(_url("/treatments/"), json={
            "appointment_id": appt_id,
            "diagnosis": "Animal saudável",
            "prescription": "Regressar em 12 meses",
            "notes": "Sem reações adversas",
        }, headers=h)
        assert tx_resp.status_code == 200, f"create treatment: {tx_resp.text}"
        tx = tx_resp.json()
        assert tx["diagnosis"] == "Animal saudável"
        tx_id = tx["id"]

        # List treatments
        txs_resp = api.get(_url("/treatments/"), headers=h)
        assert txs_resp.status_code == 200
        assert any(t["id"] == tx_id for t in txs_resp.json())

        # Create invoice
        inv_resp = api.post(_url("/invoices/"), json={
            "owner_id": owner_id,
            "appointment_id": appt_id,
            "amount": 8500.0,
            "description": "Vacinação + consulta",
        }, headers=h)
        assert inv_resp.status_code == 200, f"create invoice: {inv_resp.text}"
        inv = inv_resp.json()
        assert inv["amount"] == 8500.0
        inv_id = inv["id"]

        # List invoices
        invs_resp = api.get(_url("/invoices/"), headers=h)
        assert invs_resp.status_code == 200
        assert any(i["id"] == inv_id for i in invs_resp.json())

        # Update invoice status to paid
        update_resp = api.patch(_url(f"/invoices/{inv_id}"), json={
            "status": "paid",
        }, headers=h)
        assert update_resp.status_code == 200, f"update invoice: {update_resp.text}"
        assert update_resp.json()["status"] == "paid"

        # Start and complete the appointment through the lifecycle
        start_resp = api.patch(_url(f"/appointments/{appt_id}"), json={
            "status": "in-progress",
        }, headers=h)
        assert start_resp.status_code == 200, f"start appointment: {start_resp.text}"
        complete_resp = api.patch(_url(f"/appointments/{appt_id}"), json={
            "status": "completed",
        }, headers=h)
        assert complete_resp.status_code == 200, f"complete appointment: {complete_resp.text}"
        assert complete_resp.json()["status"] == "completed"

    def test_04_refresh_token(self, api):
        suffix = "refresh"
        self._register(api, suffix)
        tokens = self._login(api, suffix)
        refresh_resp = api.post(_url("/auth/refresh"), json={
            "refresh_token": tokens["refresh_token"]
        })
        assert refresh_resp.status_code == 200, f"refresh failed: {refresh_resp.text}"
        new_tokens = refresh_resp.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["access_token"] != tokens["access_token"]

    def test_05_logout(self, api):
        suffix = "logout"
        self._register(api, suffix)
        tokens = self._login(api, suffix)
        h = {"Authorization": f"Bearer {tokens['access_token']}"}

        logout_resp = api.post(
            _url("/auth/logout"),
            headers=h,
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert logout_resp.status_code == 200

    def test_06_health(self, api):
        resp = api.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["app"] == "PATAS"

    def test_07_dashboard(self, api):
        suffix = "dash"
        self._register(api, suffix)
        tokens = self._login(api, suffix)
        h = {"Authorization": f"Bearer {tokens['access_token']}"}
        owner = api.post(_url("/owners/"), headers=h, json={"name": "Dono Dashboard"}).json()
        pet = api.post(
            _url("/pets/"),
            headers=h,
            json={"owner_id": owner["id"], "name": "Mimo", "species": "Gato"},
        ).json()
        vet_id = api.get(_url("/users/"), headers=h).json()[0]["id"]
        luanda = ZoneInfo("Africa/Luanda")
        local_noon = datetime.combine(datetime.now(luanda).date(), time(12), tzinfo=luanda)
        appointment = api.post(
            _url("/appointments/"),
            headers=h,
            json={
                "pet_id": pet["id"],
                "vet_id": vet_id,
                "scheduled_at": local_noon.astimezone(UTC).isoformat(),
                "reason": "Contagem real do dashboard",
            },
        )
        assert appointment.status_code == 200, appointment.text
        dash_resp = api.get(_url("/dashboard/"), headers=h)
        assert dash_resp.status_code == 200, f"dashboard: {dash_resp.text}"
        data = dash_resp.json()
        assert data["today_appointments_total"] == 1
        assert data["today_appointments_by_status"]["scheduled"] == 1
        assert data["total_owners"] == 1
        assert data["total_pets"] == 1

    def test_08_cross_tenant_isolation(self, api):
        """Users from clinic B cannot access clinic A's data (404 on scoped query)."""
        suffix_a = "isol_a"
        suffix_b = "isol_b"
        self._register(api, suffix_a)
        self._register(api, suffix_b)

        tokens_a = self._login(api, suffix_a)
        tokens_b = self._login(api, suffix_b)
        h_a = {"Authorization": f"Bearer {tokens_a['access_token']}"}
        h_b = {"Authorization": f"Bearer {tokens_b['access_token']}"}

        # Clinic A creates owner + pet + appointment
        owner_resp = api.post(_url("/owners/"), json={"name": "A Owner"}, headers=h_a)
        owner_id = owner_resp.json()["id"]
        pet_resp = api.post(_url("/pets/"), json={"owner_id": owner_id, "name": "A Pet", "species": "cão"}, headers=h_a)
        pet_id = pet_resp.json()["id"]
        users_resp = api.get(_url("/users/"), headers=h_a)
        vet_id = users_resp.json()[0]["id"]
        appt_resp = api.post(_url("/appointments/"), json={
            "pet_id": pet_id, "vet_id": vet_id,
            "scheduled_at": "2026-12-31T10:00:00Z",
        }, headers=h_a)
        appt_id = appt_resp.json()["id"]

        # Clinic B lists owners — should be empty
        owners_b = api.get(_url("/owners/"), headers=h_b)
        assert owners_b.status_code == 200
        assert len(owners_b.json()) == 0, "Cross-tenant: clinic B should see no owners from clinic A"

        # Clinic B tries to read clinic A's appointment — 404 (clinic-scoped)
        appt_b = api.get(_url(f"/appointments/{appt_id}"), headers=h_b)
        assert appt_b.status_code == 404

    def test_09_pagination_and_filters(self, api):
        """Verify list endpoints support skip, limit, and search params."""
        suffix = "paged"
        self._register(api, suffix)
        tokens = self._login(api, suffix)
        h = {"Authorization": f"Bearer {tokens['access_token']}"}

        for i in range(3):
            resp = api.post(_url("/owners/"), json={"name": f"Owner {i}"}, headers=h)
            assert resp.status_code == 200

        resp = api.get(_url("/owners/?skip=0&limit=2"), headers=h)
        assert resp.status_code == 200
        assert len(resp.json()) <= 2
        assert "X-Total-Count" in resp.headers

        resp = api.get(_url("/owners/?q=Owner"), headers=h)
        assert resp.status_code == 200
        assert len(resp.json()) >= 3

    def test_10_vertical_mvp_flow(self, api):
        """Admin creates team; reception operates; vet records and closes clinical care."""
        suffix = "vertical"
        self._register(api, suffix)
        admin_tokens = self._login(api, suffix)
        admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}

        def create_and_activate_team_user(name, email, role):
            temporary_password = "Temporary1"
            created = api.post(_url("/users/"), headers=admin_headers, json={
                "name": name,
                "email": email,
                "password": temporary_password,
                "role": role,
            })
            assert created.status_code == 201, created.text
            login = api.post(_url("/auth/login"), json={
                "email": email,
                "password": temporary_password,
            })
            assert login.status_code == 200, login.text
            temporary_tokens = login.json()
            temporary_headers = {
                "Authorization": f"Bearer {temporary_tokens['access_token']}"
            }
            changed = api.post(_url("/auth/change-password"), headers=temporary_headers, json={
                "current_password": temporary_password,
                "new_password": "Permanent2",
                "refresh_token": temporary_tokens["refresh_token"],
            })
            assert changed.status_code == 200, changed.text
            return created.json(), changed.json()

        receptionist, receptionist_tokens = create_and_activate_team_user(
            "Receção Vertical", "vertical.reception@test.ao", "receptionist"
        )
        vet, vet_tokens = create_and_activate_team_user(
            "Veterinária Vertical", "vertical.vet@test.ao", "vet"
        )
        reception_headers = {
            "Authorization": f"Bearer {receptionist_tokens['access_token']}"
        }
        vet_headers = {"Authorization": f"Bearer {vet_tokens['access_token']}"}

        owner_response = api.post(_url("/owners/"), headers=reception_headers, json={
            "name": "Dona Vertical",
            "phone": "+244 923 000 001",
        })
        assert owner_response.status_code == 200, owner_response.text
        owner = owner_response.json()
        pet_response = api.post(_url("/pets/"), headers=reception_headers, json={
            "owner_id": owner["id"],
            "name": "Kalu",
            "species": "Cão",
        })
        assert pet_response.status_code == 200, pet_response.text
        pet = pet_response.json()

        from datetime import datetime, timedelta
        scheduled_at = (datetime.now(UTC) + timedelta(minutes=5)).isoformat()
        appointment_response = api.post(
            _url("/appointments/"),
            headers=reception_headers,
            json={
                "pet_id": pet["id"],
                "vet_id": vet["id"],
                "scheduled_at": scheduled_at,
                "reason": "Consulta vertical",
            },
        )
        assert appointment_response.status_code == 200, appointment_response.text
        appointment = appointment_response.json()
        arrival = api.post(
            _url("/waiting-room/entries"),
            headers=reception_headers,
            json={"appointment_id": appointment["id"]},
        )
        assert arrival.status_code == 200, arrival.text
        entry = arrival.json()
        called = api.post(
            _url(f"/waiting-room/entries/{entry['id']}/transition"),
            headers=reception_headers,
            json={"status": "called"},
        )
        assert called.status_code == 200, called.text
        started = api.post(
            _url(f"/waiting-room/entries/{entry['id']}/transition"),
            headers=vet_headers,
            json={"status": "in-progress"},
        )
        assert started.status_code == 200, started.text

        catalog = api.get(_url("/exam-catalog/"), headers=vet_headers).json()
        finding_id = catalog["systems"][0]["findings"][0]["id"]
        clinical = api.put(
            _url(f"/appointments/{appointment['id']}/clinical-record"),
            headers=vet_headers,
            json={
                "anamnesis": "Sem alterações relevantes",
                "diagnosis": "Animal saudável",
                "prescription": "Regressar em 12 meses",
                "exam_findings": [{"finding_id": finding_id, "status": "normal"}],
                "medications": [{
                    "name": "Suplemento",
                    "dosage": "1 comprimido",
                    "frequency": "24/24h",
                    "route": "oral",
                    "start_date": datetime.now(UTC).date().isoformat(),
                }],
            },
        )
        assert clinical.status_code == 200, clinical.text
        vaccine = api.post(_url("/vaccinations/"), headers=vet_headers, json={
            "pet_id": pet["id"],
            "vet_id": vet["id"],
            "appointment_id": appointment["id"],
            "name": "V10",
            "dose": "1 ml",
            "administered_at": datetime.now(UTC).isoformat(),
        })
        assert vaccine.status_code == 200, vaccine.text
        completed = api.post(
            _url(f"/waiting-room/entries/{entry['id']}/transition"),
            headers=vet_headers,
            json={"status": "completed"},
        )
        assert completed.status_code == 200, completed.text

        history = api.get(_url(f"/pets/{pet['id']}/history"), headers=reception_headers)
        assert history.status_code == 200, history.text
        assert history.json()["vaccinations"][0]["name"] == "V10"
        invoice = api.post(_url("/invoices/"), headers=reception_headers, json={
            "owner_id": owner["id"],
            "appointment_id": appointment["id"],
            "amount": 8500,
            "description": "Consulta vertical",
        })
        assert invoice.status_code == 200, invoice.text
        assert invoice.json()["status"] == "draft"

    def test_11_concurrent_appointments_return_conflict(self, api):
        """Only one simultaneous booking for the same vet and interval can commit."""
        if not BASE_URL:
            pytest.skip("The concurrency gate requires the live PostgreSQL API")

        suffix = "concurrency"
        self._register(api, suffix)
        tokens = self._login(api, suffix)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        owner = api.post(
            _url("/owners/"),
            headers=headers,
            json={"name": "Dono Concorrente"},
        ).json()
        pet = api.post(
            _url("/pets/"),
            headers=headers,
            json={"owner_id": owner["id"], "name": "Kamba", "species": "Cão"},
        ).json()
        vet_id = api.get(_url("/users/"), headers=headers).json()[0]["id"]
        scheduled_at = (datetime.now(UTC) + timedelta(days=20)).isoformat()
        barrier = Barrier(4)

        def book_once(index: int) -> int:
            with client_factory() as concurrent_client:
                barrier.wait()
                response = concurrent_client.post(
                    _url("/appointments/"),
                    headers=headers,
                    json={
                        "pet_id": pet["id"],
                        "vet_id": vet_id,
                        "scheduled_at": scheduled_at,
                        "duration_min": 30,
                        "reason": f"Pedido concorrente {index}",
                    },
                )
                return response.status_code

        with ThreadPoolExecutor(max_workers=4) as executor:
            statuses = list(executor.map(book_once, range(4)))

        assert statuses.count(200) == 1, statuses
        assert statuses.count(409) == 3, statuses
