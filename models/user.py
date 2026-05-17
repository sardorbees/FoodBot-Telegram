# database/models/user.py
from sqlalchemy import Column, Integer, BigInteger, String, Enum as SQLEnum
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"
    courier = "courier"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)

    tg_id = Column(BigInteger, unique=True, nullable=False, index=True)  # ← Это обязательно!

    username = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True)

    role = Column(SQLEnum(UserRole), default=UserRole.user, nullable=False)

    # Дополнительные поля (можно расширять)
    phone = Column(String(20), nullable=True)
    bonus_points = Column(Integer, default=0)
    created_at = Column(String, server_default="CURRENT_TIMESTAMP")  # или используй DateTime

    def __repr__(self):
        return f"<User(id={self.id}, tg_id={self.tg_id}, role={self.role})>"