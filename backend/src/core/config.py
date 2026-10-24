import os
from typing import Any

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "dev-encryption-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    APP_TIMEZONE: str = "Africa/Luanda"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://patas:patas_dev_password@db:5432/patas"
    )

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")

    WHATSAPP_ENABLED: bool = False
    WHATSAPP_GRAPH_API_VERSION: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: SecretStr = SecretStr("")
    WHATSAPP_APP_SECRET: SecretStr = SecretStr("")
    WHATSAPP_VERIFY_TOKEN: SecretStr = SecretStr("")
    WHATSAPP_REQUEST_TIMEOUT_SECONDS: float = 10.0
    BILLING_PROVIDER: str = "mock"
    VENDAS_BASE_URL: str = ""
    VENDAS_API_KEY: SecretStr = SecretStr("")
    VENDAS_REQUEST_TIMEOUT_SECONDS: float = 10.0
    VENDAS_OPERATION_TYPE: str = ""
    VENDAS_DEFAULT_VAT_PROFILE_CODE: str = ""
    VENDAS_CASH_SESSION_ID: str = ""
    VENDAS_PAID_STATES: str = "PAID,SETTLED"
    BILLING_RECONCILE_ENABLED: bool = False
    BILLING_RECONCILE_INTERVAL_SECONDS: int = 600

    @property
    def VENDAS_PAID_STATES_SET(self) -> set[str]:
        return {state.strip().upper() for state in self.VENDAS_PAID_STATES.split(",") if state.strip()}

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        raw = self.CORS_ORIGINS.strip()
        if not raw:
            return ["*"]
        return [o.strip() for o in raw.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"

    def model_post_init(self, __context: Any, /) -> None:
        if self.APP_ENV == "production" and self.SECRET_KEY in (
            "dev-secret-change-in-production",
            "change-me-in-production",
        ):
            raise ValueError(
                "SECRET_KEY must be changed in production! "
                "Generate a secure key and set it via environment variable."
            )

        if self.WHATSAPP_ENABLED:
            required = {
                "WHATSAPP_GRAPH_API_VERSION": self.WHATSAPP_GRAPH_API_VERSION,
                "WHATSAPP_PHONE_NUMBER_ID": self.WHATSAPP_PHONE_NUMBER_ID,
                "WHATSAPP_ACCESS_TOKEN": self.WHATSAPP_ACCESS_TOKEN.get_secret_value(),
                "WHATSAPP_APP_SECRET": self.WHATSAPP_APP_SECRET.get_secret_value(),
                "WHATSAPP_VERIFY_TOKEN": self.WHATSAPP_VERIFY_TOKEN.get_secret_value(),
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError(
                    "WhatsApp integration is enabled but required settings are missing: "
                    + ", ".join(missing)
                )

        if self.BILLING_PROVIDER == "vendas":
            required = {
                "VENDAS_BASE_URL": self.VENDAS_BASE_URL,
                "VENDAS_API_KEY": self.VENDAS_API_KEY.get_secret_value(),
                "VENDAS_OPERATION_TYPE": self.VENDAS_OPERATION_TYPE,
                "VENDAS_DEFAULT_VAT_PROFILE_CODE": self.VENDAS_DEFAULT_VAT_PROFILE_CODE,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError(
                    "Vendas billing integration is enabled but required settings are missing: "
                    + ", ".join(missing)
                )


settings = Settings()
