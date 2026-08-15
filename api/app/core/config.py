from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the application.

    Values can come from environment variables or a .env file.
    """

    app_name: str = "GitHub Team Brain API"
    app_version: str = "1.0.0"
    debug: bool = True

    database_url: str
    github_token: str | None = None
    github_request_timeout_seconds: float = 15.0
    gemini_api_key: str
    gemini_model: str = "models/gemini-3.6-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection_name: str = "teambrain"

    # JWT authentication
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Bootstrap admin account used to backfill repositories that were
    # created before user ownership existed. The email is not a secret;
    # the password must be supplied via the BOOTSTRAP_ADMIN_PASSWORD
    # environment variable and is never stored in source code.
    bootstrap_admin_email: str = "admin@teambrain.local"
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
