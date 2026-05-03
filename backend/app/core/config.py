from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = "Eloq Backend"
    environment: str = "development"
    debug: str = "true"

    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    groq_api_key: str
    groq_model: str = "llama-3.1-70b-versatile"

    groq_tts_api_key: str | None = None
    groq_tts_model: str = "canopylabs/orpheus-v1-english"
    groq_tts_voice: str = "austin"

    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    cloudinary_audio_folder: str = "eloq/audio"

    cors_origins: str = Field(default="http://localhost:5173")

    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def debug_bool(self) -> bool:
        return self.debug.strip().lower() in {"1", "true", "yes", "on", "development"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
