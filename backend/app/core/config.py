from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Local dev default: the Docker database on host port 5433.
    database_url: str = "postgresql+psycopg://nfw:nfw_dev_password@127.0.0.1:5433/nfw"


settings = Settings()
