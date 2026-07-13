from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = Field(default="postgresql://nami:nami@localhost:5432/nami")

    # Auth
    jwt_secret_key: str = Field(default="dev-secret-change-me")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=1440)

    # Gemma / Fireworks API
    fireworks_api_key: str = Field(default="")
    fireworks_base_url: str = Field(default="https://api.fireworks.ai/inference/v1")
    # AI Model Selection
    gemma_model_id: str = Field(default="accounts/fireworks/models/minimax-m3")

    # Video processing constraints (lowered to allow 6-second example clips)
    min_video_seconds: int = Field(default=2)
    max_video_seconds: int = Field(default=300)
    frames_per_second: float = Field(default=1.0)
    frame_jpeg_quality: int = Field(default=70)

    # Batch runner
    input_tasks_path: str = Field(default="/input/tasks.json")
    output_results_path: str = Field(default="/output/results.json")


settings = Settings()
