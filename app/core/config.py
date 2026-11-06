from pydantic import SecretStr
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    app_name: str = "Notification Service"
    app_env: str = "development"
    debug: bool = True  # Development-only configuration

    database_url: str

    log_level: str = "info"

    mail_server: str = "localhost"
    mail_port: int = 587
    mail_username: str
    mail_password: SecretStr
    mail_from: str = "noreply@example.com"
    mail_use_tls: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
