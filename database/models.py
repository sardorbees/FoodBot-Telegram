from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text,
    DateTime, ForeignKey, Enum, BigInteger
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    user = "user"
    courier = "courier"
    admin = "admin"


class OrderStatus(str, enum.Enum):
    new = "new"
    preparing = "preparing"
    courier_assigned = "courier_assigned"
    in_delivery = "in_delivery"
    delivered = "delivered"
    cancelled = "cancelled"


class PaymentMethod(str, enum.Enum):
    click = "click"
    payme = "payme"
    uzum = "uzum"
    cash = "cash"
    card = "card"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100))
    full_name = Column(String(200))
    phone = Column(String(20))
    role = Column(Enum(UserRole), default=UserRole.user)
    bonus_points = Column(Integer, default=0)
    cashback_balance = Column(Float, default=0.0)
    vip_level = Column(Integer, default=0)
    referral_code = Column(String(20), unique=True)
    referred_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    language = Column(String(5), default="ru")
    created_at = Column(DateTime, server_default=func.now())

    orders = relationship("Order", back_populates="user", foreign_keys="Order.user_id")
    cart_items = relationship("CartItem", back_populates="user")
    addresses = relationship("Address", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")
    reviews = relationship("Review", back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    emoji = Column(String(10))
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"))

    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Integer, nullable=False)
    photo_id = Column(String(500))

    # relationships
    category = relationship("Category", back_populates="products")

    sizes = relationship("ProductSize", back_populates="product")
    addons = relationship("ProductAddon", back_populates="product")

    # 🔥 ВОТ ЭТО ТЫ ЗАБЫЛ
    cart_items = relationship("CartItem", back_populates="product")
    favorites = relationship("Favorite", back_populates="product")
    reviews = relationship("Review", back_populates="product")


class ProductAddon(Base):
    __tablename__ = "product_addons"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))

    name = Column(String(100))
    price = Column(Integer, default=0)

    # ✅ FIX HERE
    product = relationship("Product", back_populates="addons")


class ProductSize(Base):
    __tablename__ = "product_sizes"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    name = Column(String(50))       # S, M, L
    price_modifier = Column(Integer, default=0)   # доплата в сумах

    product = relationship("Product", back_populates="sizes")

class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(100))     # Дом, Работа
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    is_default = Column(Boolean, default=False)

    user = relationship("User", back_populates="addresses")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    quantity = Column(Integer, default=1)
    unit_price = Column(Integer)

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product")


class Promocode(Base):
    __tablename__ = "promocodes"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    discount_percent = Column(Integer, default=0)
    discount_fixed = Column(Integer, default=0)
    min_order = Column(Integer, default=0)
    usage_limit = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    courier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.new)
    payment_method = Column(Enum(PaymentMethod))
    address = Column(Text)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    phone = Column(String(20))
    comment = Column(Text)
    promocode_id = Column(Integer, ForeignKey("promocodes.id"), nullable=True)
    subtotal = Column(Integer)
    delivery_cost = Column(Integer, default=0)
    discount = Column(Integer, default=0)
    total = Column(Integer)
    bonus_used = Column(Integer, default=0)
    delivery_time = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="orders", foreign_keys=[user_id])
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    product_name = Column(String(200))
    quantity = Column(Integer)
    unit_price = Column(Integer)
    size_name = Column(String(50))
    addons = Column(Text)

    order = relationship("Order", back_populates="items")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    user = relationship("User", back_populates="favorites")

    # 🔥 ADD THIS
    product = relationship("Product", back_populates="favorites")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    rating = Column(Integer)
    text = Column(Text)

    user = relationship("User", back_populates="reviews")

    # 🔥 ADD THIS
    product = relationship("Product", back_populates="reviews")


class Promotion(Base):
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    description = Column(Text)
    photo_id = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
