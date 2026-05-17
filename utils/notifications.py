from aiogram import Bot
from database.models import Order, OrderStatus, User
from database.queries import get_all_couriers
from sqlalchemy.ext.asyncio import AsyncSession

STATUS_TEXTS = {
    OrderStatus.new: "🆕 Ваш заказ принят! Ожидайте подтверждения.",
    OrderStatus.preparing: "👨‍🍳 Ваш заказ готовится! Скоро будет готов.",
    OrderStatus.courier_assigned: "📦 Курьер принял ваш заказ и скоро выедет!",
    OrderStatus.in_delivery: "🚴 Ваш заказ в пути! Ожидайте курьера.",
    OrderStatus.delivered: "✅ Заказ доставлен! Приятного аппетита! 😋",
    OrderStatus.cancelled: "❌ Ваш заказ отменён. Обратитесь в поддержку.",
}


async def notify_user_order_status(bot: Bot, order: Order, user_telegram_id: int):
    text = STATUS_TEXTS.get(order.status, "Статус заказа обновлён")
    msg = (
        f"{text}\n\n"
        f"📋 Заказ #{order.id}\n"
        f"💰 Итого: {order.total:,} сум"
    )
    try:
        await bot.send_message(user_telegram_id, msg)
    except Exception as e:
        print(f"Ошибка уведомления пользователя: {e}")


async def notify_couriers_new_order(bot: Bot, order: Order, session: AsyncSession):
    from keyboards.admin_kb import courier_order_kb
    couriers = await get_all_couriers(session)
    text = (
        f"🆕 Новый заказ #{order.id}!\n\n"
        f"📍 Адрес: {order.address}\n"
        f"💰 Сумма: {order.total:,} сум\n"
        f"📞 Телефон: {order.phone}\n"
        f"⏰ Время: {order.delivery_time}"
    )
    for courier in couriers:
        try:
            kb = courier_order_kb(order.id, order.phone, order.latitude, order.longitude)
            await bot.send_message(courier.telegram_id, text, reply_markup=kb)
        except Exception as e:
            print(f"Ошибка уведомления курьера {courier.id}: {e}")


async def notify_admins_new_order(bot: Bot, order: Order, admin_ids: list[int]):
    text = (
        f"🆕 Новый заказ #{order.id}!\n\n"
        f"👤 Пользователь ID: {order.user_id}\n"
        f"📍 Адрес: {order.address}\n"
        f"💳 Оплата: {order.payment_method.value}\n"
        f"💰 Итого: {order.total:,} сум\n"
        f"🕒 Доставка: {order.delivery_time}"
    )
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, text)
        except Exception as e:
            print(f"Ошибка уведомления админа {admin_id}: {e}")


async def broadcast_message(bot: Bot, user_ids: list[int], text: str, photo_id: str = None):
    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            if photo_id:
                await bot.send_photo(uid, photo_id, caption=text)
            else:
                await bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1
    return sent, failed
