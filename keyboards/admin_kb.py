from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from database.models import Order, User


def admin_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📋 Заказы"),
        KeyboardButton(text="🍽 Меню"),
    )
    builder.row(
        KeyboardButton(text="📊 Статистика"),
        KeyboardButton(text="👥 Курьеры"),
    )
    builder.row(
        KeyboardButton(text="🎁 Акции"),
        KeyboardButton(text="📣 Рассылка"),
    )
    builder.row(KeyboardButton(text="◀️ Выйти из админки"))
    return builder.as_markup(resize_keyboard=True)


def admin_orders_kb(orders: list[Order]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    status_icons = {
        "new": "🆕", "preparing": "👨‍🍳", "courier_assigned": "📦",
        "in_delivery": "🚴", "delivered": "✅", "cancelled": "❌"
    }
    for order in orders:
        icon = status_icons.get(order.status.value, "❓")
        builder.button(
            text=f"{icon} #{order.id} — {order.total:,} сум",
            callback_data=f"admin_order:{order.id}"
        )
    builder.adjust(1)
    return builder.as_markup()


def admin_order_detail_kb(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👨‍🍳 Готовится", callback_data=f"admin_status:{order_id}:preparing")
    builder.button(text="📦 Назначить курьера", callback_data=f"admin_assign:{order_id}")
    builder.button(text="✅ Доставлен", callback_data=f"admin_status:{order_id}:delivered")
    builder.button(text="❌ Отменить", callback_data=f"admin_status:{order_id}:cancelled")
    builder.button(text="◀️ Назад", callback_data="admin_orders")
    builder.adjust(2)
    return builder.as_markup()


def admin_assign_courier_kb(order_id: int, couriers: list[User]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for courier in couriers:
        builder.button(
            text=f"🚴 {courier.full_name or courier.username}",
            callback_data=f"assign_courier:{order_id}:{courier.id}"
        )
    builder.button(text="◀️ Назад", callback_data=f"admin_order:{order_id}")
    builder.adjust(1)
    return builder.as_markup()


def admin_product_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Название", callback_data=f"edit_product:name:{product_id}")
    builder.button(text="💰 Цена", callback_data=f"edit_product:price:{product_id}")
    builder.button(text="📝 Описание", callback_data=f"edit_product:desc:{product_id}")
    builder.button(text="🖼 Фото", callback_data=f"edit_product:photo:{product_id}")
    builder.button(text="🔛 Вкл/Выкл", callback_data=f"toggle_product:{product_id}")
    builder.button(text="◀️ Назад", callback_data="admin_menu_products")
    builder.adjust(2)
    return builder.as_markup()


# ─── КУРЬЕР ─────────────────────────────────────────────────────

def courier_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📋 Мои заказы"),
        KeyboardButton(text="🆕 Новые заказы"),
    )
    builder.row(
        KeyboardButton(text="📊 История"),
        KeyboardButton(text="◀️ Главное меню"),
    )
    return builder.as_markup(resize_keyboard=True)


def courier_order_kb(order_id: int, phone: str, lat: float = None, lon: float = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять заказ", callback_data=f"courier_accept:{order_id}")
    builder.button(text=f"📞 Позвонить клиенту", url=f"tel:{phone}")
    if lat and lon:
        builder.button(
            text="🗺 Навигация",
            url=f"https://maps.google.com/?q={lat},{lon}"
        )
    builder.button(text="🚴 В пути", callback_data=f"courier_status:{order_id}:in_delivery")
    builder.button(text="✅ Доставлен", callback_data=f"courier_status:{order_id}:delivered")
    builder.adjust(2)
    return builder.as_markup()
