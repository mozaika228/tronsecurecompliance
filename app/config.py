import os

try:
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

except ModuleNotFoundError:

    class Settings:
        def __init__(self) -> None:
            self.app_env = os.getenv("APP_ENV", "dev")
            self.api_host = os.getenv("API_HOST", "0.0.0.0")
            self.api_port = int(os.getenv("API_PORT", "8000"))
            self.database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/tronsecure")
            self.aml_provider = os.getenv("AML_PROVIDER", "mock")
            self.aml_http_base_url = os.getenv("AML_HTTP_BASE_URL", "https://api.example-aml-provider.com/v1")
            self.aml_http_api_key = os.getenv("AML_HTTP_API_KEY", "")
            self.aml_http_timeout_s = float(os.getenv("AML_HTTP_TIMEOUT_S", "20"))
            self.aml_http_check_path = os.getenv("AML_HTTP_CHECK_PATH", "/check")
            self.bot_token = os.getenv("BOT_TOKEN", "")
            self.backend_base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8000/api/v1")


settings = Settings()
