"""
CareerPilot AI — Application Configuration

Loads settings from environment variables using Pydantic Settings.
Create a .env file in the backend root (see .env.example for reference).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_debug: bool = True
    app_port: int = 8000

    # Database
    database_url: str = "postgresql+psycopg://user:password@localhost:5432/careerpilot"

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_secret_key: str = ""

    # Gemini API
    gemini_api_key: str = ""

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Security
    secret_key: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


# Singleton instance
settings = Settings()
