from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Продукция компании"
    database_url: str = "postgresql+psycopg2://postgres:0909@localhost:5432/postgres"
    debug: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
