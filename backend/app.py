from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from backend.api import (
    profile, users, files, referrals, requests,
    mailing, ai, session_updater, settings, tokens,
    admin, admin_users, admin_broadcast, admin_settings, admin_tokens
)
from backend.api import admin_subscriptions, admin_groups, admin_bonuses, admin_referral_payouts, user_generation_settings
from backend.core.db import init_db, close_db
from backend.services.settings_service import SettingsService
from backend.models.subscription import AccessGroup
from backend.models.admin import Admin
from backend.api.admin import get_current_admin

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
    from backend.api import channel
    app.include_router(channel.router, prefix="/api")
    app.include_router(user_generation_settings.router, prefix="/api")

    # Админ роуты
    # ВАЖНО: Порядок регистрации роутеров критичен!
    # Специфичные маршруты (например, /admin/groups) должны регистрироваться ПЕРЕД общими маршрутами (например, /admin/{admin_id})
    # FastAPI проверяет маршруты в порядке их регистрации, поэтому специфичные маршруты должны быть первыми
    
    # 1. Регистрируем роутер с группами ПЕРВЫМ (для GET, POST, PUT, DELETE)
    app.include_router(admin_groups.router, prefix="/api/admin")
    
    # 2. Регистрируем другие админские роутеры
    app.include_router(admin_users.router, prefix="/api")
    app.include_router(admin_broadcast.router, prefix="/api")
    app.include_router(admin_settings.router, prefix="/api")
    app.include_router(admin_tokens.router, prefix="/api")
    app.include_router(admin_subscriptions.router, prefix="/api")
    app.include_router(admin_bonuses.router, prefix="/api")
    app.include_router(admin_referral_payouts.router, prefix="/api")
    app.include_router(files.admin_router, prefix="/api")
    
    # 3. Регистрируем основной роутер admin (маршруты /api/admin/me, /api/admin/all и т.д.)
    # ВАЖНО: Этот роутер НЕ содержит маршрут /{admin_id}, он только в admin_param_router
    app.include_router(admin.router, prefix="/api")
    
    # 4. В ПОСЛЕДНЮЮ ОЧЕРЕДЬ регистрируем роутер с параметрами /{admin_id}
    # Это гарантирует, что FastAPI сначала проверит все специфичные маршруты
    # КРИТИЧНО: Этот роутер должен быть ПОСЛЕДНИМ
    app.include_router(admin.admin_param_router, prefix="/api")
    
    # Публичные роуты
    app.include_router(admin_groups.public_router, prefix="/api")


    @app.on_event("startup")
    async def startup_event():
        await init_db()
        await SettingsService.initialize_defaults()
        # Выполняем миграции
        from backend.core.migrations import migrate_user_generation_settings
        await migrate_user_generation_settings()

    @app.on_event("shutdown")
    async def shutdown_event():
        await close_db()

    return app
