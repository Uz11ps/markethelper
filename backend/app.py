from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import (
    profile, users, files, referrals, requests,
    mailing, ai, session_updater, settings, tokens,
    admin, admin_users, admin_broadcast, admin_settings, admin_tokens
)
from backend.core.db import init_db, close_db
from backend.services.settings_service import SettingsService

def create_app() -> FastAPI:
    app = FastAPI(
        title="MarketHelper Admin API",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # CORS для фронтенда админки
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # В продакшене указать конкретные домены
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Публичные роуты
    app.include_router(users.router, prefix="/api")
    """app.include_router(subscriptions.router)"""
    app.include_router(files.router, prefix="/api")
    app.include_router(referrals.router, prefix="/api")
    app.include_router(requests.router, prefix="/api")
    """app.include_router(mailing.router)
    app.include_router(session_updater.router)"""
    app.include_router(ai.router, prefix="/api")
    app.include_router(profile.router, prefix="/api")
    app.include_router(settings.router, prefix="/api")
    app.include_router(tokens.router, prefix="/api")

    # Админ роуты
    app.include_router(admin.router, prefix="/api")
    app.include_router(admin_users.router, prefix="/api")
    app.include_router(admin_broadcast.router, prefix="/api")
    app.include_router(admin_settings.router, prefix="/api")
    app.include_router(admin_tokens.router, prefix="/api")


    @app.on_event("startup")
    async def startup_event():
        await init_db()
        await SettingsService.initialize_defaults()

    @app.on_event("shutdown")
    async def shutdown_event():
        await close_db()

    return app
