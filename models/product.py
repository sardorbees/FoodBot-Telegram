# database/models/product.py
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    emoji = Column(String(20), nullable=True)

    products = relationship("Product", back_populates="category")


class Size(Base):
    __tablename__ = "sizes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)          # Например: "Маленький", "Большой"
    price_modifier = Column(Integer, default=0)        # +0, +5000 и т.д.


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False)            # базовая цена в сумах
    image_url = Column(String(500), nullable=True)
    is_available = Column(Boolean, default=True)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category = relationship("Category", back_populates="products")

    # Многие ко многим с размерами
    sizes = relationship("ProductSize", back_populates="product")


class ProductSize(Base):
    """Связующая таблица для размеров у продукта"""
    __tablename__ = "product_sizes"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    size_id = Column(Integer, ForeignKey("sizes.id"), nullable=False)

    product = relationship("Product", back_populates="sizes")
    size = relationship("Size")