"""Application configuration via environment variables."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Factur-X Prêt API"
    DEBUG: bool = False

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3004",
        "http://localhost:3005",
        "https://facturx-pret.fr",
        "https://www.facturx-pret.fr",
    ]

    # File upload
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS: list[str] = [
        "pdf", "csv", "xlsx", "xls",
        "sta", "mt940", "940", "mt9",
        "xml",
        "jpg", "jpeg", "png", "heic",
    ]
    UPLOAD_DIR: str = "/tmp/facturx-pret/uploads"
    OUTPUT_DIR: str = "/tmp/facturx-pret/output"

    # Azure OpenAI (AI fallback parsing)
    AZURE_OPENAI_API_KEY: SecretStr | None = None
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"

    # PDF generation
    PDF_TIMEOUT: int = 30  # seconds


settings = Settings()
