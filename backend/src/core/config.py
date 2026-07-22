import os
from typing import Any
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "dev-encryption-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://patas:patas_dev_password@db:5432/patas"
    )

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        raw = self.CORS_ORIGINS.strip()
        if not raw:
            return ["*"]
        return [o.strip() for o in raw.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"

    def model_post_init(self, __context: Any) -> None:
        if self.APP_ENV == "production":
            if self.SECRET_KEY in ("dev-secret-change-in-production", "change-me-in-production"):
                raise ValueError(
                    "SECRET_KEY must be changed in production! "
                    "Generate a secure key and set it via environment variable."
                )


settings = Settings()
