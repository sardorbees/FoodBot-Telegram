# database/models/__init__.py
from .product import Base, Product, Category, Size, ProductSize
from .user import User  # и другие модели

__all__ = ["Base", "Product", "Category", "Size", "ProductSize", "User"]