import logging
from pydantic import Field, EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import List

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application configuration settings.
    
    Manages all application configuration including database connections,
    authentication, email services, and other runtime settings.
    
    Attributes:
        POSTGRES_USER: PostgreSQL database username.
        POSTGRES_PASSWORD: PostgreSQL database password (secret).
        POSTGRES_DB: PostgreSQL database name.
        POSTGRES_HOST: PostgreSQL database host.
        POSTGRES_PORT: PostgreSQL database port.
        ENABLE_REDIS: Whether Redis caching is enabled.
        REDIS_HOST: Redis server host.
        REDIS_PORT: Redis server port.
        JWT_SECRET: JWT signing secret (secret).
        JWT_ALGORITHM: JWT signing algorithm.
        JWT_EXPIRATION_SECONDS: JWT token expiration time in seconds.
        MAIL_USERNAME: Email service username.
        MAIL_PASSWORD: Email service password (secret).
        MAIL_FROM: Default email sender address.
        MAIL_FROM_NAME: Default email sender name.
        MAIL_SERVER: SMTP server address.
        MAIL_PORT: SMTP server port.
        MAIL_STARTTLS: Whether to use STARTTLS.
        MAIL_SSL_TLS: Whether to use SSL/TLS.
        USE_CREDENTIALS: Whether to use SMTP authentication.
        VALIDATE_CERTS: Whether to validate SSL certificates.
        CLD_NAME: Cloudinary cloud name.
        CLD_API_KEY: Cloudinary API key.
        CLD_API_SECRET: Cloudinary API secret (secret).
        ADMIN_USERNAME: Default admin username.
        ADMIN_EMAIL: Default admin email.
        ADMIN_PASSWORD: Default admin password (secret).
        CORS_ALLOWED_ORIGINS: Comma-separated list of allowed CORS origins.
        LOG_LEVEL: Application logging level.
    """
    # ============================
    # PostgreSQL Database
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
    # JWT Authentication
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
    # Logging
    # ============================
    LOG_LEVEL: str = Field(default="INFO")

    # ============================
    # Property methods
    # ============================

    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        """Parse CORS_ALLOWED_ORIGINS into a list of strings.
        
        Returns:
            List[str]: List of allowed origin URLs for CORS.
        """
        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def DATABASE_URL(self) -> str:
        """Generate asynchronous PostgreSQL connection URL.
        
        Returns:
            str: PostgreSQL connection URL for asyncpg driver.
        """
        password = self.POSTGRES_PASSWORD.get_secret_value()
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Generate synchronous PostgreSQL connection URL.
        
        Returns:
            str: PostgreSQL connection URL for psycopg2 driver (Alembic).
        """
        password = self.POSTGRES_PASSWORD.get_secret_value()
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def DB_ECHO(self) -> bool:
        """Determine if SQL query echoing should be enabled.
        
        Returns:
            bool: True if LOG_LEVEL is DEBUG, False otherwise.
        """
        return self.LOG_LEVEL.upper() == "DEBUG"

    # ============================
    # Validation
    # ============================

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: SecretStr) -> SecretStr:
        """Validate JWT secret minimum length.
        
        Args:
            v: JWT secret value to validate.
        
        Returns:
            SecretStr: Validated JWT secret.
        
        Raises:
            ValueError: If JWT secret is shorter than 32 characters.
        """
        if len(v.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level against allowed values.
        
        Args:
            v: Log level string to validate.
        
        Returns:
            str: Uppercase validated log level.
        
        Raises:
            ValueError: If log level is not in allowed values.
        """
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")
        return v.upper()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


# ============================
# Settings instance creation
# ============================
settings = Settings()


def display_all_settings() -> None:
    """Display all settings values with SecretStr masking.
    
    Shows all configuration settings in name: value format.
    For SecretStr types, displays asterisks with length indication.
    """
    print("\n" + "=" * 70)
    print("🔍 SETTINGS DIAGNOSTICS FROM .env")
    print("=" * 70)
    
    # Automatically get all field names from Settings class
    field_names = [field_name for field_name in settings.model_fields.keys()]
    
    for field_name in field_names:
        value = getattr(settings, field_name)
        
        if isinstance(value, SecretStr):
            secret_value = value.get_secret_value()
            masked_value = f"{'*' * 8} (length: {len(secret_value)} characters)"
            print(f"{field_name:<20}: {masked_value}")
        else:
            print(f"{field_name:<20}: {value}")
    
    print("=" * 70 + "\n")


# ====================== SETTINGS DIAGNOSTICS ======================
if settings.LOG_LEVEL.upper() == "DEBUG":
    display_all_settings()
