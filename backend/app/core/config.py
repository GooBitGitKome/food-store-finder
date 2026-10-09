from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Food Store Finder"
    API_V1_PREFIX: str = "/api/v1"
    OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"
    NOMINATIM_API_URL: str = "https://nominatim.openstreetmap.org/search"
    USER_AGENT: str = "FoodStoreFinderApp/1.0 (contact: developer@foodstorefinder.org)"
    REQUEST_TIMEOUT: float = 120.0
    CORS_ORIGINS: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

settings = Settings()
