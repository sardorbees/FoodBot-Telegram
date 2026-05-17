from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import joinedload
from database.models import (
    User, Category, Product, CartItem, Order, OrderItem,
    Promocode, Address, Favorite, Review, Promotion,
    OrderStatus, UserRole, ProductSize
)
from datetime import datetime
import json
import random
import string


# ─── ПОЛЬЗОВАТЕЛИ ───────────────────────────────────────────────

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Импортируем из вашего конфига базы данных
from database.database import async_session  # ← Главное исправление!


async def get_or_create_user(
    session: AsyncSession,
    tg_id: int,
    username: str = None,
    full_name: str = None,
    **kwargs
):
    result = await session.execute(
        select(User).where(User.telegram_id == tg_id)
    )

    user = result.scalar_one_or_none()

    # Создание пользователя
    if user is None:

        user = User(
            telegram_id=tg_id,
            username=username,
            full_name=full_name,
            **kwargs
        )

        session.add(user)

        await session.commit()
        await session.refresh(user)

        return user

    # Обновление данных
    updated = False

    if username and user.username != username:
        user.username = username
        updated = True

    if full_name and user.full_name != full_name:
        user.full_name = full_name
        updated = True

    # Обновление остальных полей
    for key, value in kwargs.items():

        if hasattr(user, key):

            if getattr(user, key) != value:
                setattr(user, key, value)
                updated = True

    if updated:
        await session.commit()
        await session.refresh(user)

    return user

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def update_user_phone(session: AsyncSession, telegram_id: int, phone: str):
    await session.execute(
        update(User).where(User.telegram_id == telegram_id).values(phone=phone)
    )
    await session.commit()


async def get_all_couriers(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).where(User.role == UserRole.courier))
    return result.scalars().all()


# ─── КАТАЛОГ ────────────────────────────────────────────────────

async def get_categories(session):
    result = await session.execute(
        select(Category)
    )

    return result.scalars().all()


async def get_products_by_category(
    session,
    category_id
):
    result = await session.execute(
        select(Product).where(
            Product.category_id == category_id
        )
    )

    return result.scalars().all()


async def get_product(session: AsyncSession, product_id: int) -> Product | None:
    result = await session.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def get_product_with_details(session, product_id):

    result = await session.execute(
        select(Product).where(Product.id == product_id)
    )

    return result.scalar_one_or_none()


# ─── КОРЗИНА ────────────────────────────────────────────────────

async def get_cart(session, user_id: int):
    result = await session.execute(
        select(CartItem).where(CartItem.user_id == user_id)
    )
    return result.scalars().all()


async def remove_from_cart(session, user_id: int, product_id: int):
    result = await session.execute(
        select(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.product_id == product_id
        )
    )

    item = result.scalar_one_or_none()

    if item:
        await session.delete(item)
        await session.commit()


async def add_to_cart(session, user_id: int, product_id: int, price: int):
    result = await session.execute(
        select(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.product_id == product_id
        )
    )

    item = result.scalar_one_or_none()

    if item:
        item.quantity += 1
    else:
        item = CartItem(
            user_id=user_id,
            product_id=product_id,
            quantity=1,
            unit_price=price
        )
        session.add(item)

    await session.commit()


async def update_cart_item(session: AsyncSession, item_id: int, quantity: int):
    if quantity <= 0:
        await session.execute(delete(CartItem).where(CartItem.id == item_id))
    else:
        await session.execute(
            update(CartItem).where(CartItem.id == item_id).values(quantity=quantity)
        )
    await session.commit()


async def clear_cart(session: AsyncSession, user_id: int):
    await session.execute(delete(CartItem).where(CartItem.user_id == user_id))
    await session.commit()


async def get_cart_total(session: AsyncSession, user_id: int) -> int:
    items = await get_cart(session, user_id)
    return sum(item.unit_price * item.quantity for item in items)


# ─── ПРОМОКОДЫ ──────────────────────────────────────────────────

async def check_promocode(session: AsyncSession, code: str) -> Promocode | None:
    result = await session.execute(
        select(Promocode).where(
            Promocode.code == code.upper(),
            Promocode.is_active == True
        )
    )
    promo = result.scalar_one_or_none()
    if not promo:
        return None
    if promo.expires_at and promo.expires_at < datetime.now():
        return None
    if promo.usage_limit and promo.used_count >= promo.usage_limit:
        return None
    return promo


# ─── ЗАКАЗЫ ─────────────────────────────────────────────────────

async def create_order(session: AsyncSession, user_id: int, data: dict) -> Order:
    cart = await get_cart(session, user_id)
    subtotal = sum(i.unit_price * i.quantity for i in cart)

    from config.settings import DELIVERY_COST, FREE_DELIVERY_FROM
    delivery_cost = 0 if subtotal >= FREE_DELIVERY_FROM else DELIVERY_COST

    discount = data.get("discount", 0)
    total = subtotal + delivery_cost - discount

    order = Order(
        user_id=user_id,
        status=OrderStatus.new,
        payment_method=data["payment_method"],
        address=data["address"],
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        phone=data["phone"],
        comment=data.get("comment", ""),
        subtotal=subtotal,
        delivery_cost=delivery_cost,
        discount=discount,
        total=total,
        delivery_time=data.get("delivery_time", "Как можно скорее")
    )
    session.add(order)
    await session.flush()

    for item in cart:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_name=item.product.name,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        session.add(order_item)

    await session.commit()
    await session.refresh(order)
    await clear_cart(session, user_id)
    return order


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    return result.scalar_one_or_none()


async def get_user_orders(session: AsyncSession, user_id: int) -> list[Order]:
    result = await session.execute(
        select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
    )
    return result.scalars().all()


async def update_order_status(session: AsyncSession, order_id: int, status: OrderStatus):
    await session.execute(
        update(Order).where(Order.id == order_id).values(status=status)
    )
    await session.commit()


async def assign_courier(session: AsyncSession, order_id: int, courier_id: int):
    await session.execute(
        update(Order).where(Order.id == order_id).values(
            courier_id=courier_id,
            status=OrderStatus.courier_assigned
        )
    )
    await session.commit()


async def get_courier_orders(session: AsyncSession, courier_id: int) -> list[Order]:
    result = await session.execute(
        select(Order).where(
            Order.courier_id == courier_id
        ).order_by(Order.created_at.desc())
    )
    return result.scalars().all()


async def get_new_orders(session: AsyncSession) -> list[Order]:
    result = await session.execute(
        select(Order).where(Order.status == OrderStatus.new).order_by(Order.created_at)
    )
    return result.scalars().all()


# ─── АДРЕСА ─────────────────────────────────────────────────────

async def get_user_addresses(session: AsyncSession, user_id: int) -> list[Address]:
    result = await session.execute(select(Address).where(Address.user_id == user_id))
    return result.scalars().all()


async def save_address(session: AsyncSession, user_id: int, address: str,
                       lat: float = None, lon: float = None, title: str = "Новый адрес"):
    addr = Address(user_id=user_id, title=title, address=address,
                   latitude=lat, longitude=lon)
    session.add(addr)
    await session.commit()
    return addr


# ─── ИЗБРАННОЕ ──────────────────────────────────────────────────

async def toggle_favorite(session: AsyncSession, user_id: int, product_id: int) -> bool:
    result = await session.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.product_id == product_id)
    )
    fav = result.scalar_one_or_none()
    if fav:
        await session.delete(fav)
        await session.commit()
        return False
    else:
        session.add(Favorite(user_id=user_id, product_id=product_id))
        await session.commit()
        return True


async def get_favorites(session: AsyncSession, user_id: int) -> list[Favorite]:
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(Favorite)
        .options(selectinload(Favorite.product))
        .where(Favorite.user_id == user_id)
    )
    return result.scalars().all()


# ─── СТАТИСТИКА (АДМИН) ─────────────────────────────────────────

async def get_sales_stats(session: AsyncSession) -> dict:
    total_orders = await session.scalar(select(func.count(Order.id)))
    total_revenue = await session.scalar(
        select(func.sum(Order.total)).where(Order.status == OrderStatus.delivered)
    )
    today_orders = await session.scalar(
        select(func.count(Order.id)).where(
            func.date(Order.created_at) == func.current_date()
        )
    )
    return {
        "total_orders": total_orders or 0,
        "total_revenue": total_revenue or 0,
        "today_orders": today_orders or 0,
    }


# ─── АКЦИИ ──────────────────────────────────────────────────────

async def get_active_promotions(session: AsyncSession) -> list[Promotion]:
    result = await session.execute(
        select(Promotion).where(Promotion.is_active == True).order_by(Promotion.created_at.desc())
    )
    return result.scalars().all()