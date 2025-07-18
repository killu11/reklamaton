from pydantic import BaseModel, Field, HttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Annotated, Optional, Dict


class Settings(BaseSettings):
    token: str = Field(default='token')

    driver: str = Field(default="postgresql+psycopg2")
    username: str
    password: str
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    db: str
    query: Dict = Field(default_factory=dict)

    # Конфигурация
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def database_url(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme=self.driver,
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            path=self.db,
            query=self.query
        )


def get_settings():
    return Settings()


settings = get_settings()
