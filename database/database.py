from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)

from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///db.sqlite3"

engine = create_async_engine(
    DATABASE_URL,
    echo=True
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass