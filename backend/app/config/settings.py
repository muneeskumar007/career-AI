from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration, loaded from environment variables / .env.

    No field here has a production-unsafe default: SECRET_KEY has no
    default at all, so the app refuses to start without one being set
    explicitly (see .env.example).
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "CareerAI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api"

    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "careerai"

    # Frontend / CORS — comma separated in .env, exposed as a list below
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:5173"

    # Rate limiting (slowapi syntax, e.g. "5/minute")
    RATE_LIMIT_DEFAULT: str = "200/minute"
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"

    # LLM provider — see app/ai/providers/factory.py. Nothing in Module 1 or
    # the core parsing path in Module 2/3 requires this to be set; it's read
    # only when an LLM-enhanced code path is actually invoked.
    LLM_PROVIDER: str = "gemini"  # "gemini" | "ollama"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"

    # File uploads (Module 2)
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_UPLOAD_EXTENSIONS: str = "pdf,docx"

    # Voice/video interview answers (Modules 9-10) — see SETUP.md for how to
    # obtain the MediaPipe model files; unset paths mean video mode is
    # unavailable until you download them (see VideoModelUnavailableError).
    MAX_MEDIA_UPLOAD_SIZE_MB: int = 100
    FACE_LANDMARKER_MODEL_PATH: str = "models/face_landmarker.task"
    POSE_LANDMARKER_MODEL_PATH: str = "models/pose_landmarker_lite.task"

    @property
    def allowed_upload_extensions_list(self) -> list[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_UPLOAD_EXTENSIONS.split(",") if ext.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
