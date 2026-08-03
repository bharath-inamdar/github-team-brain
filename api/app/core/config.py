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
    api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
