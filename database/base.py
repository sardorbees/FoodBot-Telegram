# database/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

Base = declarative_base()

# ←←← ЭТО САМОЕ ВАЖНОЕ ←←←
# Импортируем ВСЕ модели здесь, чтобы SQLAlchemy их увидел
from .models import *   # или явно:
# from .models.category import Category
# from .models.product import Product, ProductSize


async def init_db(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)