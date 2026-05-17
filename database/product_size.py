from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.base import Base


class ProductSize(Base):
    __tablename__ = "product_sizes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String(100), nullable=False)        # Например: "Маленький", "Большой"
    price_modifier = Column(Integer, default=0)       # +0, +5000, +10000 и т.д.

    product = relationship("Product", back_populates="sizes")

    def __repr__(self):
        return f"<ProductSize(name={self.name}, modifier={self.price_modifier})>"