import hashlib
import hmac
from dataclasses import dataclass
from typing import Any

import httpx

from src.core.config import Settings, settings


class WhatsAppConfigurationError(RuntimeError):
    pass


class WhatsAppAPIError(RuntimeError):
    pass


class WhatsAppVerificationError(RuntimeError):
    pass


@dataclass(frozen=True)
class WhatsAppConfig:
    enabled: bool
    graph_api_version: str
    phone_number_id: str
    access_token: str
    app_secret: str
    verify_token: str
    request_timeout_seconds: float = 10.0
    graph_api_base_url: str = "https://graph.facebook.com"

    @classmethod
    def from_settings(cls, app_settings: Settings) -> "WhatsAppConfig":
        return cls(
            enabled=app_settings.WHATSAPP_ENABLED,
            graph_api_version=app_settings.WHATSAPP_GRAPH_API_VERSION,
            phone_number_id=app_settings.WHATSAPP_PHONE_NUMBER_ID,
            access_token=app_settings.WHATSAPP_ACCESS_TOKEN.get_secret_value(),
            app_secret=app_settings.WHATSAPP_APP_SECRET.get_secret_value(),
            verify_token=app_settings.WHATSAPP_VERIFY_TOKEN.get_secret_value(),
            request_timeout_seconds=app_settings.WHATSAPP_REQUEST_TIMEOUT_SECONDS,
        )


@dataclass(frozen=True)
class WhatsAppWebhookSummary:
    messages: int
    statuses: int


class WhatsAppService:
    def __init__(
        self,
        config: WhatsAppConfig,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._config = config
        self._transport = transport

    @property
    def enabled(self) -> bool:
        return self._config.enabled

    def verify_challenge(self, mode: str, token: str, challenge: str) -> str:
        if not self._config.enabled or not self._config.verify_token:
            raise WhatsAppConfigurationError("WhatsApp integration is not configured")
        if mode != "subscribe" or not hmac.compare_digest(token, self._config.verify_token):
            raise WhatsAppVerificationError("Invalid WhatsApp webhook verification")
        return challenge

    def verify_signature(self, body: bytes, signature: str | None) -> bool:
        if not self._config.enabled or not self._config.app_secret or not signature:
            return False
        prefix = "sha256="
        if not signature.startswith(prefix):
            return False
        expected = hmac.new(
            self._config.app_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature[len(prefix):], expected)

    def summarize_webhook(self, payload: dict[str, Any]) -> WhatsAppWebhookSummary:
        message_count = 0
        status_count = 0
        for entry in payload.get("entry", []):
            if not isinstance(entry, dict):
                continue
            for change in entry.get("changes", []):
                if not isinstance(change, dict):
                    continue
                value = change.get("value", {})
                if not isinstance(value, dict):
                    continue
                messages = value.get("messages", [])
                statuses = value.get("statuses", [])
                message_count += len(messages) if isinstance(messages, list) else 0
                status_count += len(statuses) if isinstance(statuses, list) else 0
        return WhatsAppWebhookSummary(messages=message_count, statuses=status_count)

    async def send_text(self, to: str, body: str, preview_url: bool = False) -> str:
        if not body.strip():
            raise ValueError("WhatsApp message body cannot be empty")
        return await self._send(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": self._normalize_recipient(to),
                "type": "text",
                "text": {"preview_url": preview_url, "body": body},
            }
        )

    async def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str,
        components: list[dict[str, Any]] | None = None,
    ) -> str:
        if not template_name.strip() or not language_code.strip():
            raise ValueError("WhatsApp template name and language are required")
        template: dict[str, Any] = {
            "name": template_name,
            "language": {"code": language_code},
        }
        if components:
            template["components"] = components
        return await self._send(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": self._normalize_recipient(to),
                "type": "template",
                "template": template,
            }
        )

    async def _send(self, payload: dict[str, Any]) -> str:
        self._require_outbound_configuration()
        url = (
            f"{self._config.graph_api_base_url.rstrip('/')}/"
            f"{self._config.graph_api_version}/{self._config.phone_number_id}/messages"
        )
        headers = {
            "Authorization": f"Bearer {self._config.access_token}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(
                timeout=self._config.request_timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            raise WhatsAppAPIError(
                f"WhatsApp API returned HTTP {exc.response.status_code}"
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise WhatsAppAPIError("WhatsApp API request failed") from exc

        messages = data.get("messages") if isinstance(data, dict) else None
        first_message = messages[0] if isinstance(messages, list) and messages else None
        if not isinstance(first_message, dict) or not first_message.get("id"):
            raise WhatsAppAPIError("WhatsApp API response did not include a message id")
        return str(first_message["id"])

    def _require_outbound_configuration(self) -> None:
        required = (
            self._config.enabled,
            self._config.graph_api_version,
            self._config.phone_number_id,
            self._config.access_token,
        )
        if not all(required):
            raise WhatsAppConfigurationError("WhatsApp outbound messaging is not configured")

    @staticmethod
    def _normalize_recipient(recipient: str) -> str:
        normalized = "".join(character for character in recipient if character.isdigit())
        if not 8 <= len(normalized) <= 15:
            raise ValueError("WhatsApp recipient must be a valid international phone number")
        return normalized


whatsapp_service = WhatsAppService(WhatsAppConfig.from_settings(settings))
