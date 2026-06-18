from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Base de datos
    DATABASE_URL: str

    # Seguridad
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Configuración para leer desde el archivo .env
    model_config = SettingsConfigDict(env_file=".env.local", env_file_encoding="utf-8", extra="ignore")


# Instanciamos la configuración para poder importarla en otros archivos
settings = Settings()
