import json
from json import JSONDecodeError

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from src.services.whatsapp import (
    WhatsAppConfigurationError,
    WhatsAppService,
    WhatsAppVerificationError,
    whatsapp_service,
)

router = APIRouter()


def get_whatsapp_service() -> WhatsAppService:
    return whatsapp_service


@router.get("/webhook", response_class=PlainTextResponse)
def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
    service: WhatsAppService = Depends(get_whatsapp_service),
) -> PlainTextResponse:
    try:
        challenge = service.verify_challenge(hub_mode, hub_verify_token, hub_challenge)
    except WhatsAppConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Integração WhatsApp não configurada",
        ) from exc
    except WhatsAppVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verificação do webhook WhatsApp inválida",
        ) from exc
    return PlainTextResponse(challenge)


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    service: WhatsAppService = Depends(get_whatsapp_service),
) -> dict[str, int | str]:
    body = await request.body()
    if not service.verify_signature(body, x_hub_signature_256):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Assinatura do webhook WhatsApp inválida",
        )
    try:
        payload = json.loads(body)
    except (JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload do webhook WhatsApp inválido",
        ) from exc
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload do webhook WhatsApp inválido",
        )
    summary = service.summarize_webhook(payload)
    return {
        "status": "accepted",
        "messages": summary.messages,
        "statuses": summary.statuses,
    }
