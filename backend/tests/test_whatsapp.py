import hashlib
import hmac
import json

import httpx
import pytest
from pydantic import ValidationError

from src.api.whatsapp import get_whatsapp_service
from src.core.config import Settings
from src.main import app
from src.services.whatsapp import (
    WhatsAppAPIError,
    WhatsAppConfig,
    WhatsAppService,
    WhatsAppVerificationError,
)


def whatsapp_config(**overrides) -> WhatsAppConfig:
    values = {
        "enabled": True,
        "graph_api_version": "v-test",
        "phone_number_id": "phone-123",
        "access_token": "access-secret",
        "app_secret": "app-secret",
        "verify_token": "verify-secret",
        "graph_api_base_url": "https://graph.example.test",
    }
    values.update(overrides)
    return WhatsAppConfig(**values)


def signed_payload(payload: dict, secret: str = "app-secret") -> tuple[bytes, str]:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return body, f"sha256={digest}"


def test_enabled_integration_requires_all_credentials():
    with pytest.raises(ValidationError, match="WHATSAPP_ACCESS_TOKEN"):
        Settings(
            _env_file=None,
            WHATSAPP_ENABLED=True,
            WHATSAPP_GRAPH_API_VERSION="v-test",
            WHATSAPP_PHONE_NUMBER_ID="phone-123",
            WHATSAPP_ACCESS_TOKEN="",
            WHATSAPP_APP_SECRET="",
            WHATSAPP_VERIFY_TOKEN="",
        )


def test_verify_challenge_accepts_matching_token():
    service = WhatsAppService(whatsapp_config())

    assert service.verify_challenge("subscribe", "verify-secret", "challenge-123") == "challenge-123"


def test_verify_challenge_rejects_invalid_token():
    service = WhatsAppService(whatsapp_config())

    with pytest.raises(WhatsAppVerificationError):
        service.verify_challenge("subscribe", "wrong-token", "challenge-123")


def test_webhook_signature_and_summary():
    service = WhatsAppService(whatsapp_config())
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [{"id": "wamid.1"}],
                            "statuses": [{"id": "wamid.2"}, {"id": "wamid.3"}],
                        }
                    }
                ]
            }
        ]
    }
    body, signature = signed_payload(payload)

    assert service.verify_signature(body, signature) is True
    assert service.verify_signature(body, "sha256=invalid") is False
    summary = service.summarize_webhook(payload)
    assert summary.messages == 1
    assert summary.statuses == 2


@pytest.mark.asyncio
async def test_send_text_uses_cloud_api_contract():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://graph.example.test/v-test/phone-123/messages"
        assert request.headers["Authorization"] == "Bearer access-secret"
        assert json.loads(request.content) == {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": "244923456789",
            "type": "text",
            "text": {"preview_url": False, "body": "Consulta confirmada"},
        }
        return httpx.Response(200, json={"messages": [{"id": "wamid.sent"}]})

    service = WhatsAppService(whatsapp_config(), transport=httpx.MockTransport(handler))

    message_id = await service.send_text("+244 923 456 789", "Consulta confirmada")

    assert message_id == "wamid.sent"


@pytest.mark.asyncio
async def test_send_text_hides_provider_response_details():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": {"message": "sensitive provider detail"}})

    service = WhatsAppService(whatsapp_config(), transport=httpx.MockTransport(handler))

    with pytest.raises(WhatsAppAPIError, match="HTTP 400") as exc_info:
        await service.send_text("244923456789", "Consulta confirmada")
    assert "sensitive provider detail" not in str(exc_info.value)


def test_webhook_endpoints_accept_verified_payload(client):
    service = WhatsAppService(whatsapp_config())
    app.dependency_overrides[get_whatsapp_service] = lambda: service

    verification = client.get(
        "/api/v1/integrations/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-secret",
            "hub.challenge": "challenge-123",
        },
    )
    assert verification.status_code == 200
    assert verification.text == "challenge-123"

    payload = {
        "entry": [
            {"changes": [{"value": {"messages": [{"id": "wamid.1"}], "statuses": []}}]}
        ]
    }
    body, signature = signed_payload(payload)
    delivery = client.post(
        "/api/v1/integrations/whatsapp/webhook",
        content=body,
        headers={"X-Hub-Signature-256": signature, "Content-Type": "application/json"},
    )

    assert delivery.status_code == 200
    assert delivery.json() == {"status": "accepted", "messages": 1, "statuses": 0}


def test_webhook_endpoint_rejects_invalid_signature(client):
    service = WhatsAppService(whatsapp_config())
    app.dependency_overrides[get_whatsapp_service] = lambda: service

    response = client.post(
        "/api/v1/integrations/whatsapp/webhook",
        json={"entry": []},
        headers={"X-Hub-Signature-256": "sha256=invalid"},
    )

    assert response.status_code == 401
