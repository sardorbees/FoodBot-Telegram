from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from database.models import Base
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.settings import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
