from tortoise import Tortoise
from backend.models import Tariff, Status, Duration, Audience

TORTOISE_ORM = {
    "connections": {
        "default": "sqlite://db.sqlite3"
    },
    "apps": {
        "models": {
            "models": ["backend.models"],
            "default_connection": "default",
        }
    },
}

# Данные для заполнения
TARIFFS = [
    {"code": "INDIVIDUAL", "name": "Индивидуальный"},
    {"code": "GROUP", "name": "Групповой"}
]

STATUSES = [
    {"type": "subscription", "code": "ACTIVE", "name": "Активна"},
    {"type": "subscription", "code": "EXPIRED", "name": "Истекла"},

    {"type": "request", "code": "PENDING", "name": "В ожидании"},
    {"type": "request", "code": "APPROVED", "name": "Одобрена"},
    {"type": "request", "code": "REJECTED", "name": "Отклонена"},
]
DURATIONS = [1, 3, 6]

AUDIENCES = [
    {"code": "ALL", "name": "Все"},
    {"code": "ACTIVE", "name": "Активные"},
    {"code": "INACTIVE", "name": "Неактивные"},
]

FILE_TYPES = [
    {"code": "TXT", "name": "Текстовый файл"},
    {"code": "PDF", "name": "PDF файл"},
    {"code": "DOCX", "name": "Документ Word"},
]

LEVELS = [
    {"code": "NOVICE", "name": "Новичок", "xp_required": 0},
    {"code": "PRACTICER", "name": "Практик", "xp_required": 100},
]

EXPERIENCES = [
    {"code": "BEGINNER", "name": "Начинающий"},
    {"code": "SELLER", "name": "Продавец"},
    {"code": "PRO", "name": "Профессионал"},
]

PLATFORMS = [
    {"code": "WB", "name": "Wildberries"},
    {"code": "OZON", "name": "Ozon"},
    {"code": "BOTH", "name": "Обе"},
]

TRAFFIC_SOURCES = [
    {"code": "REF", "name": "Реферальные"},
    {"code": "REELS", "name": "Рилсы"},
    {"code": "AD", "name": "Реклама"},
]

# Функция для инициализации базы данных и данных
async def init_db():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()

    # Проверка и заполнение таблиц данными, если они пустые
    if not await Tariff.exists():
        for tariff in TARIFFS:
            await Tariff.create(**tariff)

    if not await Status.exists():
        for status in STATUSES:
            await Status.create(**status)

    if not await Duration.exists():
        for duration in DURATIONS:
            await Duration.create(months=duration)

    if not await Audience.exists():
        for audience in AUDIENCES:
            await Audience.create(**audience)

# Функция для закрытия соединений с БД
async def close_db():
    await Tortoise.close_connections()
