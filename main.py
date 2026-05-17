import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database.seed import seed_categories, seed_products_from_json

from config.settings import BOT_TOKEN

from database.connection import init_db, async_session, engine
from database.models import Base

from database.json_loader import load_products_from_json

from sqlalchemy import select
from database.models import Category

# ================= MIDDLEWARE =================

from middlewares.session_middleware import SessionMiddleware
from middlewares.user_middleware import UserMiddleware
from middlewares.auth import AuthMiddleware

# ================= ROUTERS =================

from handlers import (
    user,
    catalog,
    product,
    cart,
    order,
    courier,
    admin
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():

    logger.info("🚀 Запуск FoodBot...")

    # ================= DB INIT =================

    await init_db()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("✅ Seed завершён")

    # ================= SEED DATA =================

    async with async_session() as session:

        # 🔥 1. categories
        await seed_categories(session)

        # 🔥 2. products
        await seed_products_from_json(session)


    # ================= BOT =================

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()

    # ================= MIDDLEWARE =================

    dp.message.middleware(SessionMiddleware(async_session))
    dp.callback_query.middleware(SessionMiddleware(async_session))

    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())

    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # ================= ROUTERS =================

    dp.include_router(user.router)
    dp.include_router(catalog.router)
    dp.include_router(product.router)
    dp.include_router(cart.router)
    dp.include_router(order.router)
    dp.include_router(courier.router)
    dp.include_router(admin.router)

    logger.info("🤖 Bot started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())