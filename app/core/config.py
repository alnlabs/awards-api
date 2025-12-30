from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours (1 day)

    class Config:
        env_file = ".env"


settings = Settings()