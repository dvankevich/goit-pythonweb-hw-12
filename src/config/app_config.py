import logging
from pydantic import Field, EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import List

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # ============================
    # База даних PostgreSQL
    # ============================
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: SecretStr = Field(default=SecretStr("567234"))
    POSTGRES_DB: str = Field(default="contacts_db")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)

    # ============================
    # Redis
    # ============================
    ENABLE_REDIS: bool = Field(default=False)
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)

    # ============================
    # JWT Автентифікація
    # ============================
    JWT_SECRET: SecretStr = Field(
        default=SecretStr("your_super_secret_jwt_key_change_in_production")
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_SECONDS: int = Field(default=3600)

    # ============================
    # Email (Brevo)
    # ============================
    MAIL_USERNAME: EmailStr = Field(default="example@smtp-brevo.com")
    MAIL_PASSWORD: SecretStr = Field(default=SecretStr("xsmtpsib-your-brevo-smtp-key"))
    MAIL_FROM: EmailStr = Field(default="admin@dvankevich.pp.ua")
    MAIL_FROM_NAME: str = Field(default="Contacts API")
    MAIL_SERVER: str = Field(default="smtp-relay.brevo.com")
    MAIL_PORT: int = Field(default=587)
    MAIL_STARTTLS: bool = Field(default=True)
    MAIL_SSL_TLS: bool = Field(default=False)
    USE_CREDENTIALS: bool = Field(default=True)
    VALIDATE_CERTS: bool = Field(default=True)

    # ============================
    # Cloudinary
    # ============================
    CLD_NAME: str = Field(default="cloud")
    CLD_API_KEY: str = Field(default="")
    CLD_API_SECRET: SecretStr = Field(default=SecretStr("secret"))

    # ============================
    # Admin user
    # ============================
    ADMIN_USERNAME: str = Field(default="admin")
    ADMIN_EMAIL: EmailStr = Field(default="admin@dvankevich.pp.ua")
    ADMIN_PASSWORD: SecretStr = Field(default=SecretStr("SuperSecretPassword123"))

    # ============================
    # CORS
    # ============================
    CORS_ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"
    )

    # ============================
    # Логування
    # ============================
    LOG_LEVEL: str = Field(default="INFO")

    # ============================
    # Property методи
    # ============================

    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        """Повертає список дозволених origins для CORS"""
        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def DATABASE_URL(self) -> str:
        """Асинхронне підключення для FastAPI"""
        password = self.POSTGRES_PASSWORD.get_secret_value()
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Синхронне підключення для Alembic"""
        password = self.POSTGRES_PASSWORD.get_secret_value()
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def DB_ECHO(self) -> bool:
        """Вмикати відображення SQL запитів тільки в DEBUG режимі"""
        return self.LOG_LEVEL.upper() == "DEBUG"

    # ============================
    # Валідація
    # ============================

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET повинен бути не коротшим за 32 символи")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL повинен бути одним з: {valid_levels}")
        return v.upper()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


# ============================
# Створення екземпляра налаштувань
# ============================
settings = Settings()


def display_all_settings() -> None:
    """Display all settings values with SecretStr masking.
    
    Shows all configuration settings in name: value format.
    For SecretStr types, displays asterisks with length indication.
    """
    print("\n" + "=" * 70)
    print("🔍 ДІАГНОСТИКА НАЛАШТУВАНЬ З .env")
    print("=" * 70)
    
    # Automatically get all field names from Settings class
    field_names = [field_name for field_name in settings.model_fields.keys()]
    
    for field_name in field_names:
        value = getattr(settings, field_name)
        
        if isinstance(value, SecretStr):
            secret_value = value.get_secret_value()
            masked_value = f"{'*' * 8} (довжина: {len(secret_value)} символів)"
            print(f"{field_name:<20}: {masked_value}")
        else:
            print(f"{field_name:<20}: {value}")
    
    print("=" * 70 + "\n")


# ====================== ДІАГНОСТИКА НАЛАШТУВАНЬ ======================
if settings.LOG_LEVEL.upper() == "DEBUG":
    display_all_settings()
