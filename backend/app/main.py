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
cors_origins = settings.cors_origins_list
allow_credentials = False if cors_origins == ["*"] else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# メインのプレフィックスでルーターを登録 (デフォルト: /api/v1)
main_prefix = settings.API_V1_PREFIX.rstrip("/")
if main_prefix:
    app.include_router(router, prefix=main_prefix)

# 互換性のため、どのプレフィックス（/api, /v1, プレフィックスなし）でアクセスされても動作するようにフォールバック登録
compatible_prefixes = ["", "/api", "/v1", "/api/v1"]
for p in compatible_prefixes:
    if p != main_prefix:
        app.include_router(router, prefix=p)

@app.get("/")
async def root():
    return {
        "message": "Food Store Finder API is running.",
        "docs": "/docs",
        "health": f"{main_prefix}/health" if main_prefix else "/health"
    }
