from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="自社Webサイトを持たない飲食店・食品店探索 & 連絡先収集API",
    version="1.0.0"
)

# CORS設定（Next.js等のフロントエンド連携用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    return {
        "message": "Food Store Finder API is running.",
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }
