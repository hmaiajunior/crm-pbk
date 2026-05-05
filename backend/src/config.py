from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str
    PLAYBEKIDS_DB_URL: str
    NINO_WEBHOOK_KEY: str
    JWT_SECRET: str
    JWT_EXPIRE_HOURS: int = 24
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    INVITE_TOKEN_TTL_HOURS: int = 48


settings = Settings()
