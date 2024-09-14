import secrets
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    computed_field,
    MySQLDsn,
    RedisDsn
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    DOMAIN: str = "localhost"
    ENVIRONMENT: Literal["local", "test", "prod"] = "local"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def server_host(self) -> str:
        # Use HTTPS for anything other than local development
        if self.ENVIRONMENT == "local":
            return f'http://{self.DOMAIN}'
        return f"https://{self.DOMAIN}"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    PROJECT_NAME: str

    LOG_PATH: str
    LOG_LEVEL: str

    DB_HOST: str
    DB_PORT: int = 3306
    DB_DATABASE: str = ""
    DB_USER: str
    DB_PASSWORD: str = ""
    DB_DEBUG: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> MySQLDsn:
        return MultiHostUrl.build(
            scheme="mysql+pymysql",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=self.DB_DATABASE,
        )

    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_USER: str | None = None
    REDIS_PASSWORD: str | None = None
    REDIS_DB: str | None = None

    @property
    def REDIS_URI(self) -> RedisDsn:
        auth = f"{self.REDIS_USER}:{self.REDIS_PASSWORD}@" if self.REDIS_USER or self.REDIS_PASSWORD else ''
        path = f"/{self.REDIS_DB}" if self.REDIS_DB else ''
        dsn = f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}{path}"
        return RedisDsn(dsn)

    OPENAI_API_KEY: str = ""
    YDC_API_KEY: str = ""
    SERPER_API_KEY: str = ""
    OUTPUT_DIR: str = ""
    DELETE_ARTICLE_OUTPUT_DIR: bool = True

    HTTP_PROXY: str = ""


settings = Settings()
