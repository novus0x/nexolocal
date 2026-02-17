########## Modules ##########
from pydantic_settings import BaseSettings

########## Settings ##########
class Settings(BaseSettings):
    TIMEZONE: str

    DATABASE_MODE: str

    DATABASE_URL_LOCAL: str
    DATABASE_URL_DOCKER: str

    TOKEN_NAME: str
    SECRET_KEY: str

    TAX_ENGINE_USER: str
    TAX_ENGINE_PASSWORD: str

    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_SECRET_ID: str

    EMAIL_ENABLED: bool = True
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    @property
    def DATABASE_URL(self):
        if self.DATABASE_MODE == "docker":
            return self.DATABASE_URL_DOCKER
        return self.DATABASE_URL_LOCAL

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
