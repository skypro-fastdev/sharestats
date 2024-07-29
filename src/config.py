import os
from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from google.oauth2.service_account import Credentials
from pydantic_settings import BaseSettings, SettingsConfigDict

IS_HEROKU = "DYNO" in os.environ

env_file = Path(__file__).parent.parent / ".env" if not IS_HEROKU else None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_file, extra="ignore")

    CREDENTIALS_PATH: str = ""
    DEBUG: str = "False"
    SHEET_ID_TEST: str
    ORIGINS: str
    TG_TOKEN: str
    TG_CHANNEL: str = "https://t.me/skypro_sharingstats"
    CHANNEL_ID: str
    LOAD_STATS_HOST: str
    LOAD_STATS_TOKEN: str
    YANDEX_S3_KEY_ID: str
    YANDEX_S3_SECRET_KEY: str
    YANDEX_S3_BUCKET: str

    @property
    def debug(self) -> bool:
        return self.DEBUG == "True"

    @property
    def origins(self) -> list[str]:
        return self.ORIGINS.split(",")


settings = Settings()


def setup_middlewares(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.origins)


def get_creds():
    creds = Credentials.from_service_account_file(settings.CREDENTIALS_PATH)
    return creds.with_scopes(
        [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
        ]
    )
