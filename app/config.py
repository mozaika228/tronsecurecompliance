from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = "dev"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tronsecure"
    aml_provider: str = "mock"
    aml_http_base_url: str = "https://api.example-aml-provider.com/v1"
    aml_http_api_key: str = ""
    aml_http_timeout_s: float = 20.0
    aml_http_check_path: str = "/check"
    bot_token: str = ""
    backend_base_url: str = "http://localhost:8000/api/v1"


settings = Settings()
