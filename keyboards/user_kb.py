from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from database.models import Category, Product, CartItem, Address


def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🍔 Меню"),
        KeyboardButton(text="🛒 Корзина"),
    )
    builder.row(
        KeyboardButton(text="📦 Мои заказы"),
        KeyboardButton(text="❤️ Избранное"),
    )
    builder.row(
        KeyboardButton(text="🎁 Акции"),
        KeyboardButton(text="📍 Адрес доставки"),
    )
    builder.row(KeyboardButton(text="☎️ Поддержка"))
    return builder.as_markup(resize_keyboard=True)


def categories_kb(categories: list[Category]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"{cat.emoji or ''} {cat.name}",
            callback_data=f"cat:{cat.id}"
        )
    builder.adjust(2)
    return builder.as_markup()


def products_kb(products: list[Product], category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        builder.button(
            text=f"{p.name} — {p.price:,} сум",
            callback_data=f"product:{p.id}"
        )
    builder.button(text="◀️ Назад", callback_data="back_to_categories")
    builder.adjust(1)
    return builder.as_markup()


def product_detail_kb(product_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Добавить в корзину",
                    callback_data=f"add_cart:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛒 Открыть корзину",
                    callback_data="open_cart"
                )
            ]
        ]
    )


def sizes_kb(product_id: int, sizes) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for size in sizes:
        builder.button(
            text=f"{size.name} (+{size.price_modifier:,} сум)",
            callback_data=f"add_cart:{product_id}:{size.id}"
        )
    builder.button(text="◀️ Назад", callback_data=f"product:{product_id}")
    builder.adjust(1)
    return builder.as_markup()


def cart_kb(items: list[CartItem]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.button(
            text=f"❌ {item.product.name}",
            callback_data=f"cart_del:{item.id}"
        )
        builder.button(
            text=f"➖",
            callback_data=f"cart_dec:{item.id}"
        )
        builder.button(
            text=f"{item.quantity}",
            callback_data="noop"
        )
        builder.button(
            text=f"➕",
            callback_data=f"cart_inc:{item.id}"
        )
    builder.adjust(4)
    builder.row(
        InlineKeyboardButton(text="🏷 Промокод", callback_data="promo"),
        InlineKeyboardButton(text="✅ Оформить", callback_data="checkout")
    )
    builder.row(InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="cart_clear"))
    return builder.as_markup()


def payment_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    methods = [
        ("💳 Click", "pay:click"),
        ("💳 Payme", "pay:payme"),
        ("🏦 Uzum Bank", "pay:uzum"),
        ("💵 Наличные", "pay:cash"),
        ("🃏 Карта", "pay:card"),
    ]
    for text, cb in methods:
        builder.button(text=text, callback_data=cb)
    builder.adjust(2)
    return builder.as_markup()


def delivery_time_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    times = [
        "Как можно скорее",
        "Через 30 минут",
        "Через 1 час",
        "Через 2 часа",
    ]
    for t in times:
        builder.button(text=t, callback_data=f"time:{t}")
    builder.adjust(2)
    return builder.as_markup()


def phone_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 Отправить номер", request_contact=True)
    builder.button(text="◀️ Главное меню")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def location_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📍 Отправить геолокацию", request_location=True)
    builder.button(text="✏️ Ввести адрес вручную")
    builder.button(text="◀️ Главное меню")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def addresses_kb(addresses: list[Address]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for addr in addresses:
        builder.button(text=f"📍 {addr.title}: {addr.address[:30]}...", callback_data=f"addr:{addr.id}")
    builder.button(text="➕ Новый адрес", callback_data="addr_new")
    builder.adjust(1)
    return builder.as_markup()


def order_status_kb(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить статус", callback_data=f"order_status:{order_id}")
    builder.button(text="◀️ Мои заказы", callback_data="my_orders")
    builder.adjust(1)
    return builder.as_markup()


def skip_kb(callback: str = "skip") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Пропустить ➡️", callback_data=callback)
    return builder.as_markup()

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def cart_action_kb(product_id: int):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🛒 Открыть корзину", callback_data="open_cart"),
            ],
            [
                InlineKeyboardButton(text="➕ Ещё", callback_data=f"add_cart:{product_id}"),
                InlineKeyboardButton(text="➖ Убрать", callback_data=f"cart_dec:{product_id}")
            ],
            [
                InlineKeyboardButton(text="🗑 Очистить", callback_data="cart_clear")
            ]
        ]
    )