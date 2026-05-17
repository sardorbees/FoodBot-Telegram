# database/category.py
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from database.base import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)

    # Связь с продуктами
    products = relationship(
        "Product",
        back_populates="category",
        cascade="all, delete-orphan"
    )