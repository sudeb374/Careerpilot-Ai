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
    test_database_url: str | None = None

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

    # JSearch (RapidAPI)
    jsearch_api_key: str = ""
    jsearch_api_host: str = "jsearch.p.rapidapi.com"
    jsearch_api_base_url: str = "https://jsearch.p.rapidapi.com"
    jsearch_timeout_seconds: float = 30.0
    jsearch_connect_timeout_seconds: float = 10.0

    @property
    def clean_jsearch_api_host(self) -> str:
        """Sanitized JSearch host header value (e.g. jsearch.p.rapidapi.com)."""
        raw = self.jsearch_api_host or "jsearch.p.rapidapi.com"
        cleaned = raw.replace("https://", "").replace("http://", "").strip().strip("/")
        # Filter out control characters if any exist
        return "".join(c for c in cleaned if ord(c) >= 32 and ord(c) != 127)

    @property
    def clean_jsearch_base_url(self) -> str:
        """Sanitized root origin URL for JSearch API (e.g. https://jsearch.p.rapidapi.com)."""
        from urllib.parse import urlparse

        if self.jsearch_api_base_url and self.jsearch_api_base_url.strip():
            raw_base = self.jsearch_api_base_url.strip()
            # Filter control characters
            raw_base = "".join(c for c in raw_base if ord(c) >= 32 and ord(c) != 127)
            if not raw_base.startswith(("http://", "https://")):
                raw_base = f"https://{raw_base}"
            parsed = urlparse(raw_base)
            scheme = parsed.scheme if parsed.scheme in ("http", "https") else "https"
            netloc = (parsed.netloc or self.clean_jsearch_api_host).strip("/")
            return f"{scheme}://{netloc}"
        return f"https://{self.clean_jsearch_api_host}"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


# Singleton instance
settings = Settings()
