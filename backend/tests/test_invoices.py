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
    assert data["items"][0]["description"] == "Consulta + Vacinação"


def test_create_itemized_invoice_calculates_provisional_subtotal(
    client, vet_headers, owner, appointment
):
    response = client.post("/api/v1/invoices/", headers=vet_headers, json={
        "owner_id": owner.id,
        "appointment_id": appointment.id,
        "payment_method": "tpa",
        "items": [
            {"description": "Consulta", "quantity": 1, "unit_price": 10000, "tax_rate": 0},
            {"description": "Vacina", "quantity": 2, "unit_price": 2500, "tax_rate": 0},
        ],
    })
    assert response.status_code == 200
    data = response.json()
    assert data["subtotal"] == "15000.00"
    assert data["tax_total"] == "0.00"
    assert data["amount"] == 15000.0
    assert data["customer_nif"] == owner.nif
    assert len(data["items"]) == 2
    assert data["items"][0]["kind"] == "SERVICE"
    assert data["billing_external_id"].startswith("patas-")
    assert data["idempotency_key"] is None


def test_create_invoice_requires_owner_nif(client, vet_headers, owner, db_session):
    owner.nif = None
    db_session.commit()
    response = client.post("/api/v1/invoices/", headers=vet_headers, json={
        "owner_id": owner.id,
        "items": [{"description": "Consulta", "quantity": 1, "unit_price": 100, "tax_rate": 0}],
    })
    assert response.status_code == 422
    assert "NIF" in response.json()["detail"]


def test_create_invoice_rejects_local_tax_calculation(client, vet_headers, owner):
    response = client.post("/api/v1/invoices/", headers=vet_headers, json={
        "owner_id": owner.id,
        "items": [
            {"description": "Consulta", "quantity": 1, "unit_price": 100, "tax_rate": 14}
        ],
    })
    assert response.status_code == 422


def test_get_invoice(client, vet_headers, invoice):
    response = client.get(f"/api/v1/invoices/{invoice.id}", headers=vet_headers)
    assert response.status_code == 200
    assert response.json()["amount"] == 100.0


def test_get_invoice_not_found(client, vet_headers):
    response = client.get("/api/v1/invoices/99999", headers=vet_headers)
    assert response.status_code == 404


def test_update_draft_invoice(client, vet_headers, invoice):
    response = client.patch(f"/api/v1/invoices/{invoice.id}", headers=vet_headers, json={
        "amount": 150.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "draft"
    assert data["amount"] == 150.0


def test_invoice_cannot_be_marked_paid_locally(client, vet_headers, invoice):
    response = client.patch(
        f"/api/v1/invoices/{invoice.id}",
        headers=vet_headers,
        json={"status": "paid"},
    )
    assert response.status_code == 409
    assert "software de faturação" in response.json()["detail"]


def test_sync_invoice_uses_mock_adapter(client, vet_headers, invoice, db_session):
    import json

    from src.models.audit_log import AuditLog

    preview = client.post(f"/api/v1/invoices/{invoice.id}/preview", headers=vet_headers)
    assert preview.status_code == 200
    assert preview.json()["quote_payable"] == "100.00"
    assert preview.json()["quote_id"] != preview.json()["idempotency_key"]
    preview_audit = db_session.query(AuditLog).filter(
        AuditLog.resource == "invoice",
        AuditLog.resource_id == invoice.id,
        AuditLog.action == "PREVIEW",
    ).one()
    audit_details = json.loads(preview_audit.details)
    assert set(audit_details) == {"quote_id", "sync_status"}
    response = client.post(f"/api/v1/invoices/{invoice.id}/sync", headers=vet_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"
    assert data["sync_status"] == "synced"
    assert data["external_reference"].startswith("mock-patas-")
    assert data["document_number"].startswith("MOCK-")
    assert data["series"] == "MOCK"
    assert data["provider_mode"] == "TRAINING"
    assert data["provider_status"] == "sent"
    assert data["sync_attempts"] == 1

    status_response = client.get(f"/api/v1/invoices/{invoice.id}/sync-status", headers=vet_headers)
    assert status_response.status_code == 200
    assert status_response.json()["external_status"] == "sent"


def test_sync_invoice_persists_vendas_series_uuid(client, vet_headers, invoice, db_session, monkeypatch):
    from src.models.invoice import Invoice
    from src.services.billing import BillingSyncResult

    series_id = "6246c22b-0501-4687-bdaa-8551e88ae493"
    assert Invoice.__table__.columns["series"].type.length >= len(series_id)
    preview = client.post(f"/api/v1/invoices/{invoice.id}/preview", headers=vet_headers)
    assert preview.status_code == 200

    class VendasAdapter:
        name = "vendas"

        def emit_invoice(self, payload):
            return BillingSyncResult(
                external_reference="3417736c-216c-4468-b605-35992f214100",
                status="ISSUED",
                document_number="FT ENSAIO/2",
                series=series_id,
                mode="TRAINING",
            )

    monkeypatch.setattr("src.api.invoices.get_billing_adapter", lambda: VendasAdapter())
    response = client.post(f"/api/v1/invoices/{invoice.id}/sync", headers=vet_headers)
    assert response.status_code == 200
    assert response.json()["series"] == series_id
    assert response.json()["document_number"] == "FT ENSAIO/2"
    db_session.expire_all()
    assert db_session.get(Invoice, invoice.id).series == series_id


def test_vendas_payload_maps_ft_without_payment(invoice):
    from src.services.billing import build_billing_payload

    invoice.quote_id = "00000000-0000-4000-8000-000000000001"
    invoice.quote_payable = 100
    invoice.idempotency_key = "00000000-0000-4000-8000-000000000002"
    payload = build_billing_payload(invoice)
    data = payload.to_vendas_dict()
    assert data["externalId"] == f"patas-{invoice.clinic_id}-invoice-{invoice.id}"
    assert data["storeExternalId"] == "patas-test-store"
    assert data["type"] == "FT"
    assert data["quoteId"] == invoice.quote_id
    assert data["customer"]["taxId"] == invoice.customer_nif
    assert data["lines"][0]["kind"] == "SERVICE"
    assert "payment" not in data
    assert len(payload.idempotency_key) == 36


def test_vendas_adapter_uses_bearer_and_persisted_idempotency(invoice, monkeypatch):
    from src.core.config import settings
    from src.services.billing import VendasBillingAdapter, build_billing_payload

    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "invoice": {
                    "id": "vendas-1",
                    "state": "ISSUED",
                    "reference": "FT 2026/1",
                    "number": "2026/1",
                    "seriesId": "series-a",
                    "mode": "TRAINING",
                },
                "meta": {},
            }

    def fake_post(url, *, json, headers, timeout):
        captured.update(url=url, json=json, headers=headers, timeout=timeout)
        return Response()

    monkeypatch.setattr(settings, "VENDAS_BASE_URL", "http://vendas.test")
    monkeypatch.setattr(settings, "VENDAS_API_KEY", type(settings.VENDAS_API_KEY)("secret"))
    monkeypatch.setattr(settings, "VENDAS_OPERATION_TYPE", "NORMAL")
    monkeypatch.setattr("src.services.billing.httpx.post", fake_post)
    invoice.quote_id = "00000000-0000-4000-8000-000000000001"
    invoice.quote_payable = 100
    invoice.idempotency_key = "00000000-0000-4000-8000-000000000002"
    payload = build_billing_payload(invoice)
    result = VendasBillingAdapter().emit_invoice(payload)
    assert captured["url"].endswith("/api/integrations/v1/invoices")
    assert captured["headers"]["Authorization"] == "Bearer secret"
    assert captured["headers"]["Idempotency-Key"] == payload.idempotency_key
    assert captured["json"]["externalId"] == payload.external_id
    assert captured["json"]["lines"][0]["operationType"] == "NORMAL"
    assert captured["json"]["lines"][0]["quantity"] == "1.000"
    assert captured["json"]["lines"][0]["unitPrice"] == "100.00"
    assert captured["json"]["lines"][0]["code"].startswith("PATAS-SERVICE-")
    assert captured["json"]["lines"][0]["vatProfileCode"] == "VAT-STD"
    assert captured["json"]["externalReference"] == f"appointment-{invoice.appointment_id}"
    assert captured["json"]["notes"] == invoice.description
    assert result.external_reference == "vendas-1"
    assert result.mode == "TRAINING"
    assert result.status == "ISSUED"
    assert result.series == "series-a"
    assert result.document_number == "FT 2026/1"


def test_vendas_preview_uses_strict_contract(invoice, monkeypatch):
    from src.core.config import settings
    from src.services.billing import VendasBillingAdapter, build_billing_preview_payload

    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "quote": {
                    "id": "00000000-0000-4000-8000-000000000010",
                    "expiresAt": "2026-09-29T12:10:00+00:00",
                    "vatConfigurationVersion": "vat-v3",
                    "calculationDigest": "digest-1",
                },
                "totals": {"payable": 114},
                "meta": {"mode": "TRAINING"},
            }

    def fake_post(url, *, json, headers, timeout):
        captured.update(url=url, json=json, headers=headers, timeout=timeout)
        return Response()

    monkeypatch.setattr(settings, "VENDAS_BASE_URL", "http://vendas.test")
    monkeypatch.setattr(settings, "VENDAS_API_KEY", type(settings.VENDAS_API_KEY)("secret"))
    monkeypatch.setattr(settings, "VENDAS_OPERATION_TYPE", "NORMAL")
    monkeypatch.setattr("src.services.billing.httpx.post", fake_post)
    key = "00000000-0000-4000-8000-000000000010"
    result = VendasBillingAdapter().preview_invoice(
        build_billing_preview_payload(invoice), key
    )

    assert captured["url"].endswith("/api/integrations/v1/invoices/preview")
    assert captured["headers"]["Authorization"] == "Bearer secret"
    assert captured["headers"]["Idempotency-Key"] == key
    assert set(captured["json"]) == {
        "externalId", "storeExternalId", "documentDate", "lines"
    }
    assert "customer" not in captured["json"]
    assert captured["json"]["lines"][0]["quantity"] == "1.000"
    assert captured["json"]["lines"][0]["unitPrice"] == "100.00"
    assert captured["json"]["lines"][0]["vatProfileCode"] == "VAT-STD"
    assert result.quote_id == key
    assert result.payable == 114


def test_vendas_status_reads_nested_invoice(monkeypatch):
    from src.core.config import settings
    from src.services.billing import VendasBillingAdapter

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"invoice": {"id": "vendas-1", "state": "ISSUED"}, "meta": {}}

    monkeypatch.setattr(settings, "VENDAS_BASE_URL", "http://vendas.test")
    monkeypatch.setattr(settings, "VENDAS_API_KEY", type(settings.VENDAS_API_KEY)("secret"))
    monkeypatch.setattr("src.services.billing.httpx.get", lambda *args, **kwargs: Response())

    assert VendasBillingAdapter().get_status("vendas-1") == "ISSUED"


def test_fr_tender_uses_exact_quoted_payable(invoice):
    from decimal import Decimal

    from src.models.invoice import InvoiceDocumentType, PaymentMethod
    from src.services.billing import build_billing_payload

    invoice.document_type = InvoiceDocumentType.INVOICE_RECEIPT
    invoice.payment_method = PaymentMethod.BANK_TRANSFER
    invoice.quote_id = "00000000-0000-4000-8000-000000000001"
    invoice.quote_payable = Decimal("114.37")
    invoice.idempotency_key = "00000000-0000-4000-8000-000000000002"

    data = build_billing_payload(invoice).to_vendas_dict()

    assert data["payment"]["tenders"] == [
        {"method": "TRANSFER", "amount": "114.37"}
    ]


def test_generated_catalog_code_is_stable_across_invoice_lines():
    from src.models.invoice import InvoiceLine, InvoiceLineKind
    from src.services.billing import _stable_line_code, _stable_product_external_id

    first = InvoiceLine(
        id=1, clinic_id=7, kind=InvoiceLineKind.SERVICE, description="Consulta geral"
    )
    second = InvoiceLine(
        id=999, clinic_id=7, kind=InvoiceLineKind.SERVICE, description="Consulta geral"
    )

    assert _stable_line_code(first) == _stable_line_code(second)
    assert len(_stable_line_code(first)) <= 64
    code = _stable_line_code(first)
    assert _stable_product_external_id(first, code) == _stable_product_external_id(
        second, code
    )


def test_provider_failure_is_safe_and_retryable(client, vet_headers, owner, monkeypatch):
    import httpx

    class FailingAdapter:
        name = "vendas"

        def emit_invoice(self, payload):
            raise httpx.ConnectError("provider unavailable")

    created = client.post("/api/v1/invoices/", headers=vet_headers, json={
        "owner_id": owner.id,
        "items": [{"description": "Consulta", "kind": "SERVICE", "unit": "UN", "quantity": 1, "unit_price": 100, "tax_rate": 0}],
    })
    preview = client.post(
        f"/api/v1/invoices/{created.json()['id']}/preview", headers=vet_headers
    )
    assert preview.status_code == 200
    monkeypatch.setattr("src.api.invoices.get_billing_adapter", lambda: FailingAdapter())
    response = client.post(f"/api/v1/invoices/{created.json()['id']}/sync", headers=vet_headers)
    assert response.status_code == 502
    assert "faturação" in response.json()["detail"]
    stored = client.get(f"/api/v1/invoices/{created.json()['id']}", headers=vet_headers).json()
    assert stored["status"] == "draft"
    assert stored["sync_status"] == "failed"
    assert stored["sync_attempts"] == 1
    assert stored["idempotency_key"] == preview.json()["idempotency_key"]
    recalculation = client.post(
        f"/api/v1/invoices/{created.json()['id']}/preview", headers=vet_headers
    )
    assert recalculation.status_code == 409


def test_timeout_retry_keeps_emission_key_even_after_quote_expiry(
    client, vet_headers, invoice, db_session, monkeypatch
):
    import httpx

    from src.services.billing import MockBillingAdapter

    preview = client.post(f"/api/v1/invoices/{invoice.id}/preview", headers=vet_headers)
    emission_key = preview.json()["idempotency_key"]

    class FailingAdapter:
        name = "vendas"

        def emit_invoice(self, payload):
            raise httpx.ReadTimeout("uncertain provider result")

    monkeypatch.setattr("src.api.invoices.get_billing_adapter", lambda: FailingAdapter())
    failed = client.post(f"/api/v1/invoices/{invoice.id}/sync", headers=vet_headers)
    assert failed.status_code == 502
    db_session.refresh(invoice)
    invoice.quote_expires_at = invoice.created_at
    db_session.commit()

    monkeypatch.setattr("src.api.invoices.get_billing_adapter", lambda: MockBillingAdapter())
    retried = client.post(f"/api/v1/invoices/{invoice.id}/sync", headers=vet_headers)

    assert retried.status_code == 200
    assert retried.json()["idempotency_key"] == emission_key


def test_preview_reports_missing_vat_profile(client, vet_headers, invoice, monkeypatch):
    import httpx

    class Adapter:
        name = "vendas"

        def preview_invoice(self, payload, idempotency_key):
            response = httpx.Response(
                422,
                json={"code": "VAT_PROFILE_REQUIRED"},
                request=httpx.Request("POST", "http://vendas.test/preview"),
            )
            raise httpx.HTTPStatusError(
                "invalid VAT profile", request=response.request, response=response
            )

    monkeypatch.setattr("src.api.invoices.get_billing_adapter", lambda: Adapter())
    response = client.post(f"/api/v1/invoices/{invoice.id}/preview", headers=vet_headers)
    assert response.status_code == 422
    assert "perfil de IVA" in response.json()["detail"]


def test_stale_quote_is_cleared_before_retry(client, vet_headers, invoice, monkeypatch):
    import httpx

    preview = client.post(f"/api/v1/invoices/{invoice.id}/preview", headers=vet_headers)
    assert preview.status_code == 200

    class Adapter:
        name = "vendas"

        def emit_invoice(self, payload):
            response = httpx.Response(
                409,
                json={"code": "QUOTE_STALE"},
                request=httpx.Request("POST", "http://vendas.test/invoices"),
            )
            raise httpx.HTTPStatusError(
                "stale quote", request=response.request, response=response
            )

    monkeypatch.setattr("src.api.invoices.get_billing_adapter", lambda: Adapter())
    response = client.post(f"/api/v1/invoices/{invoice.id}/sync", headers=vet_headers)
    assert response.status_code == 409
    stored = client.get(f"/api/v1/invoices/{invoice.id}", headers=vet_headers).json()
    assert stored["status"] == "draft"
    assert stored["quote_id"] is None
    assert stored["idempotency_key"] is None


def test_fr_sync_uses_provider_quote_and_becomes_paid(client, vet_headers, owner):
    created = client.post("/api/v1/invoices/", headers=vet_headers, json={
        "owner_id": owner.id,
        "document_type": "FR",
        "payment_method": "bank-transfer",
        "items": [{"description": "Consulta", "kind": "SERVICE", "unit": "UN", "quantity": 1, "unit_price": 100, "tax_rate": 0}],
    })
    assert created.status_code == 200
    preview = client.post(
        f"/api/v1/invoices/{created.json()['id']}/preview", headers=vet_headers
    )
    assert preview.status_code == 200
    synced = client.post(f"/api/v1/invoices/{created.json()['id']}/sync", headers=vet_headers)
    assert synced.status_code == 200
    assert synced.json()["status"] == "paid"
    assert synced.json()["paid_at"] is not None
    replay = client.post(f"/api/v1/invoices/{created.json()['id']}/sync", headers=vet_headers)
    assert replay.status_code == 200
    assert replay.json()["external_reference"] == synced.json()["external_reference"]
    assert replay.json()["sync_attempts"] == synced.json()["sync_attempts"]


def test_fr_cash_requires_vendas_cash_session(client, vet_headers, owner):
    created = client.post("/api/v1/invoices/", headers=vet_headers, json={
        "owner_id": owner.id,
        "document_type": "FR",
        "payment_method": "cash",
        "items": [{"description": "Consulta", "kind": "SERVICE", "unit": "UN", "quantity": 1, "unit_price": 100, "tax_rate": 0}],
    })
    preview = client.post(
        f"/api/v1/invoices/{created.json()['id']}/preview", headers=vet_headers
    )
    assert preview.status_code == 200
    response = client.post(f"/api/v1/invoices/{created.json()['id']}/sync", headers=vet_headers)
    assert response.status_code == 422
    assert "sessão de caixa" in response.json()["detail"]


def test_fr_requires_payment_method(client, vet_headers, owner):
    response = client.post("/api/v1/invoices/", headers=vet_headers, json={
        "owner_id": owner.id,
        "document_type": "FR",
        "items": [{"description": "Consulta", "kind": "SERVICE", "unit": "UN", "quantity": 1, "unit_price": 100, "tax_rate": 0}],
    })
    assert response.status_code == 422


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


def test_cannot_cancel_document_already_issued_by_provider(client, vet_headers, invoice):
    preview = client.post(f"/api/v1/invoices/{invoice.id}/preview", headers=vet_headers)
    assert preview.status_code == 200
    synced = client.post(f"/api/v1/invoices/{invoice.id}/sync", headers=vet_headers)
    assert synced.status_code == 200
    response = client.patch(
        f"/api/v1/invoices/{invoice.id}",
        headers=vet_headers,
        json={"status": "cancelled", "reason": "Correção"},
    )
    assert response.status_code == 409
    assert "Vendas" in response.json()["detail"]


def test_sync_backfills_stable_identifiers_for_legacy_draft(
    client, vet_headers, invoice, db_session
):
    invoice.billing_external_id = None
    invoice.idempotency_key = None
    invoice.issuer_store_external_id = None
    db_session.commit()

    response = client.post(f"/api/v1/invoices/{invoice.id}/preview", headers=vet_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["billing_external_id"] == f"patas-{invoice.clinic_id}-invoice-{invoice.id}"
    assert len(data["idempotency_key"]) == 36
    assert data["issuer_store_external_id"] == "patas-test-store"


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


def test_admin_can_update_clinic_nif(client, admin_headers):
    response = client.patch("/api/v1/clinics/me", headers=admin_headers, json={"nif": "5000998877"})
    assert response.status_code == 200
    assert response.json()["nif"] == "5000998877"


def test_draft_change_after_preview_clears_quote(client, vet_headers, invoice):
    preview = client.post(f"/api/v1/invoices/{invoice.id}/preview", headers=vet_headers)
    assert preview.status_code == 200
    assert preview.json()["quote_id"]

    updated = client.patch(f"/api/v1/invoices/{invoice.id}", headers=vet_headers, json={"amount": 250})
    assert updated.status_code == 200
    assert updated.json()["quote_id"] is None
    assert updated.json()["idempotency_key"] is None

    blocked = client.post(f"/api/v1/invoices/{invoice.id}/sync", headers=vet_headers)
    assert blocked.status_code == 409


def test_draft_with_pending_emission_cannot_change(client, vet_headers, invoice, monkeypatch):
    import httpx

    class FailingAdapter:
        name = "vendas"

        def emit_invoice(self, payload):
            raise httpx.ReadTimeout("uncertain provider result")

    assert client.post(f"/api/v1/invoices/{invoice.id}/preview", headers=vet_headers).status_code == 200
    monkeypatch.setattr("src.api.invoices.get_billing_adapter", lambda: FailingAdapter())
    assert client.post(f"/api/v1/invoices/{invoice.id}/sync", headers=vet_headers).status_code == 502

    response = client.patch(f"/api/v1/invoices/{invoice.id}", headers=vet_headers, json={"amount": 250})
    assert response.status_code == 409
    stored = client.get(f"/api/v1/invoices/{invoice.id}", headers=vet_headers).json()
    assert stored["idempotency_key"]
    assert float(stored["amount"]) == 100.0


def test_draft_cannot_be_marked_sent_without_provider(client, vet_headers, invoice):
    response = client.patch(f"/api/v1/invoices/{invoice.id}", headers=vet_headers, json={"status": "sent"})
    assert response.status_code == 409


def test_appointment_accepts_only_one_active_invoice(client, vet_headers, invoice, owner):
    payload = {
        "owner_id": owner.id,
        "appointment_id": invoice.appointment_id,
        "items": [{"description": "Consulta", "kind": "SERVICE", "unit": "UN", "quantity": 1, "unit_price": 100, "tax_rate": 0}],
    }
    duplicate = client.post("/api/v1/invoices/", headers=vet_headers, json=payload)
    assert duplicate.status_code == 409

    cancelled = client.patch(
        f"/api/v1/invoices/{invoice.id}", headers=vet_headers,
        json={"status": "cancelled", "reason": "Emitida por engano"},
    )
    assert cancelled.status_code == 200
    assert client.post("/api/v1/invoices/", headers=vet_headers, json=payload).status_code == 200


def test_cancelled_appointment_cannot_be_invoiced(client, vet_headers, appointment, owner, db_session):
    from src.models.appointment import AppointmentStatus

    appointment.status = AppointmentStatus.CANCELLED
    db_session.commit()
    response = client.post("/api/v1/invoices/", headers=vet_headers, json={
        "owner_id": owner.id,
        "appointment_id": appointment.id,
        "items": [{"description": "Consulta", "kind": "SERVICE", "unit": "UN", "quantity": 1, "unit_price": 100, "tax_rate": 0}],
    })
    assert response.status_code == 409


def test_definitive_provider_rejection_allows_new_preview(client, vet_headers, invoice, monkeypatch):
    import httpx

    class RejectingAdapter:
        name = "vendas"

        def emit_invoice(self, payload):
            response = httpx.Response(
                422,
                json={"code": "CUSTOMER_INVALID"},
                request=httpx.Request("POST", "http://vendas.test/invoices"),
            )
            raise httpx.HTTPStatusError("invalid", request=response.request, response=response)

    assert client.post(f"/api/v1/invoices/{invoice.id}/preview", headers=vet_headers).status_code == 200
    monkeypatch.setattr("src.api.invoices.get_billing_adapter", lambda: RejectingAdapter())
    failed = client.post(f"/api/v1/invoices/{invoice.id}/sync", headers=vet_headers)
    assert failed.status_code == 502
    stored = client.get(f"/api/v1/invoices/{invoice.id}", headers=vet_headers).json()
    assert stored["sync_status"] == "failed"
    assert stored["idempotency_key"] is None
    assert stored["last_sync_error"]

    monkeypatch.undo()
    assert client.post(f"/api/v1/invoices/{invoice.id}/preview", headers=vet_headers).status_code == 200


def test_list_invoices_filters_by_pet_and_query(client, vet_headers, invoice, pet, db_session):
    by_pet = client.get("/api/v1/invoices/", headers=vet_headers, params={"pet_id": pet.id})
    assert [item["id"] for item in by_pet.json()] == [invoice.id]
    assert by_pet.headers["X-Total-Count"] == "1"
    other_pet = client.get("/api/v1/invoices/", headers=vet_headers, params={"pet_id": pet.id + 999})
    assert other_pet.json() == []
    by_owner_name = client.get("/api/v1/invoices/", headers=vet_headers, params={"q": "Test Owner"})
    assert [item["id"] for item in by_owner_name.json()] == [invoice.id]


def test_preview_refreshes_customer_snapshot_from_owner(client, vet_headers, invoice, owner, db_session):
    owner.nif = "5499999999"
    db_session.commit()
    preview = client.post(f"/api/v1/invoices/{invoice.id}/preview", headers=vet_headers)
    assert preview.status_code == 200
    assert preview.json()["customer_nif"] == "5499999999"


def test_reconcile_marks_issued_ft_paid(client, vet_headers, invoice, monkeypatch):
    from src.services.billing import MockBillingAdapter

    assert client.post(f"/api/v1/invoices/{invoice.id}/preview", headers=vet_headers).status_code == 200
    issued = client.post(f"/api/v1/invoices/{invoice.id}/sync", headers=vet_headers)
    assert issued.json()["status"] == "sent"

    class PaidAdapter(MockBillingAdapter):
        def get_status(self, external_reference):
            return "paid"

    monkeypatch.setattr("src.api.invoices.get_billing_adapter", lambda: PaidAdapter())
    reconciled = client.post(f"/api/v1/invoices/{invoice.id}/reconcile", headers=vet_headers)
    assert reconciled.status_code == 200
    assert reconciled.json()["status"] == "paid"
    assert reconciled.json()["provider_status"] == "paid"


def test_reconcile_requires_issued_document(client, receptionist_headers, invoice):
    response = client.post(f"/api/v1/invoices/{invoice.id}/reconcile", headers=receptionist_headers)
    assert response.status_code == 409


def test_reconciliation_job_only_promotes_paid_ft(db_session, invoice):
    from src.models.invoice import InvoiceStatus
    from src.services.billing import MockBillingAdapter
    from src.services.billing_reconciliation import reconcile_pending_invoices

    invoice.status = InvoiceStatus.SENT
    invoice.external_reference = "mock-patas-job"
    db_session.commit()

    class Adapter(MockBillingAdapter):
        def get_status(self, external_reference):
            return "SETTLED"

    result = reconcile_pending_invoices(db_session, adapter=Adapter())
    db_session.refresh(invoice)
    assert result == {"checked": 1, "paid": 1, "failed": 0}
    assert invoice.status == InvoiceStatus.PAID
    assert invoice.paid_at is not None


def test_preview_requires_issuer_nif_before_offering_emission(client, vet_headers, invoice, clinic, db_session):
    clinic.nif = None
    db_session.commit()
    response = client.post(f"/api/v1/invoices/{invoice.id}/preview", headers=vet_headers)
    assert response.status_code == 422
    assert "NIF" in response.json()["detail"]
