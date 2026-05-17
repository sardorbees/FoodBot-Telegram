# database/models/product.py
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False
    )

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    image = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True)

    # Связи
    category = relationship("Category", back_populates="products")
    sizes = relationship(
        "ProductSize",
        back_populates="product",
        cascade="all, delete-orphan"
    )


class ProductSize(Base):
    __tablename__ = "product_sizes"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    price_modifier = Column(Float, default=0)

    product = relationship("Product", back_populates="sizes")