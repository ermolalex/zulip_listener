import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_TG_ID: int
    ZULIP_API_KEY: str
    ZULIP_EMAIL: str
    ZULIP_SITE: str
    ZULIP_ALLOW_INSECURE: bool

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".", ".env")
    )

settings = Settings()
