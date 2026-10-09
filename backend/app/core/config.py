from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "Food Store Finder"
    API_V1_PREFIX: str = "/api/v1"
    OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"
    NOMINATIM_API_URL: str = "https://nominatim.openstreetmap.org/search"
    USER_AGENT: str = "FoodStoreFinderApp/1.0 (contact: developer@foodstorefinder.org)"
    REQUEST_TIMEOUT: float = 120.0

settings = Settings()
