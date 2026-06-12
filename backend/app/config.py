from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root


class Settings(BaseSettings):
    db_url: str = f"sqlite:///{BASE_DIR / 'data' / 'intel.db'}"
    llm_provider: str = "claude-cli"  # claude-cli | anthropic-api | mock
    llm_fast_model: str = "claude-haiku-4-5-20251001"
    llm_deep_model: str = "claude-sonnet-4-6"
    anthropic_api_key: str = ""
    admin_token: str = "changeme"
    site_base_url: str = "http://localhost:3000"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = ""
    wecom_webhook_url: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    timezone: str = "Asia/Shanghai"
    scheduler_enabled: bool = True

    model_config = {"env_file": ".env", "env_prefix": "INTEL_"}


settings = Settings()
