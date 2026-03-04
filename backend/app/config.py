from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OCR provider: "paddleocr" or "mock"
    OCR_PROVIDER: str = "paddleocr"
    OCR_DPI: int = 150

    # Database
    DATABASE_URL: str = "sqlite:///./verifydoc.db"

    # File storage
    UPLOAD_DIR: str = "./uploads"

    # Verification thresholds
    NAME_MATCH_THRESHOLD: int = 80
    SALARY_RECURRENCE_MIN_MONTHS: int = 3
    SALARY_RECURRENCE_LOOKBACK: int = 6
    SALARY_STABILITY_TOLERANCE: float = 0.15
    DEBT_TO_SALARY_MAX_RATIO: float = 0.40

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
