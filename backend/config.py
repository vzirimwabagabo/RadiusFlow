from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # radiusflow_app is the application DB role. Never use the radius runtime role or postgres here.
    DATABASE_URL: str = "postgresql+psycopg2://radiusflow_app:change-me@localhost:5432/radius"

    JWT_SECRET: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    CORS_ORIGINS: List[str] = ["*"]

    # --- SMS & Notifications ---
    SMS_API_KEY: str = ""
    SMS_USERNAME: str = ""
    SMS_SENDER_ID: str = "RADIUSFLOW"

    # --- Payment Gateway (M-Pesa / Stripe / Gateway API) ---
    PAYMENT_API_KEY: str = ""
    PAYMENT_API_SECRET: str = ""
    PAYMENT_PROVIDER_URL: str = ""
    PAYMENT_WEBHOOK_SECRET: str = ""

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"

    ENVIRONMENT: str = "development"
    AUTH_SESSION_HOURS: int = 12
    SESSION_COOKIE_SECURE: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.ENVIRONMENT.lower() != "production":
            return self
        if self.JWT_SECRET == "change-this-secret-in-production":
            raise ValueError("JWT_SECRET must be configured in production.")
        if "*" in self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS cannot contain '*' in production.")
        if not self.SESSION_COOKIE_SECURE:
            raise ValueError("SESSION_COOKIE_SECURE must be enabled in production.")
        return self

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()
