from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, UserRole, OrderStatus
from database.queries import (
    get_new_orders, get_courier_orders, get_order,
    update_order_status, assign_courier, get_user_by_telegram_id
)
from keyboards.admin_kb import courier_menu_kb, courier_order_kb
from utils.notifications import notify_user_order_status

router = Router()


def courier_only(func):
    async def wrapper(event, db_user: User, **kwargs):
        if db_user.role not in (UserRole.courier, UserRole.admin):
            if hasattr(event, 'answer'):
                await event.answer("⛔️ Нет доступа")
            return
        return await func(event, db_user=db_user, **kwargs)
    return wrapper


@router.message(F.text == "🆕 Новые заказы")
async def new_orders(message: Message, db_user: User, session: AsyncSession):
    if db_user.role not in (UserRole.courier, UserRole.admin):
        return

    orders = await get_new_orders(session)
    if not orders:
        await message.answer("📭 Новых заказов нет. Ожидайте...")
        return

    for order in orders:
        text = (
            f"🆕 <b>Заказ #{order.id}</b>\n\n"
            f"📍 {order.address}\n"
            f"📞 {order.phone}\n"
            f"💰 {order.total:,} сум\n"
            f"⏰ {order.delivery_time}\n"
            f"💬 {order.comment or '—'}"
        )
        kb = courier_order_kb(order.id, order.phone, order.latitude, order.longitude)
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(F.text == "📋 Мои заказы")
async def courier_my_orders(message: Message, db_user: User, session: AsyncSession):
    if db_user.role not in (UserRole.courier, UserRole.admin):
        return

    orders = await get_courier_orders(session, db_user.id)
    active = [o for o in orders if o.status.value not in ("delivered", "cancelled")]

    if not active:
        await message.answer("У вас нет активных заказов.")
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for order in active:
        builder.button(
            text=f"📦 #{order.id} — {order.total:,} сум — {order.status.value}",
            callback_data=f"courier_order_detail:{order.id}"
        )
    builder.adjust(1)
    await message.answer("📋 <b>Ваши активные заказы:</b>",
                         reply_markup=builder.as_markup(), parse_mode="HTML")


@router.message(F.text == "📊 История")
async def courier_history(message: Message, db_user: User, session: AsyncSession):
    if db_user.role not in (UserRole.courier, UserRole.admin):
        return

    orders = await get_courier_orders(session, db_user.id)
    delivered = [o for o in orders if o.status.value == "delivered"]

    if not delivered:
        await message.answer("История доставок пуста.")
        return

    text = f"📊 <b>История доставок ({len(delivered)}):</b>\n\n"
    for order in delivered[:20]:
        text += f"✅ #{order.id} — {order.total:,} сум — {order.created_at.strftime('%d.%m.%Y')}\n"

    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data.startswith("courier_accept:"))
async def accept_order(callback: CallbackQuery, db_user: User,
                       session: AsyncSession, bot: Bot):
    if db_user.role not in (UserRole.courier, UserRole.admin):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])
    await assign_courier(session, order_id, db_user.id)

    order = await get_order(session, order_id)
    await callback.answer("✅ Заказ принят!")
    await callback.message.edit_text(
        f"✅ Вы приняли заказ #{order_id}\n\n"
        f"📍 Адрес: {order.address}\n"
        f"📞 Клиент: {order.phone}",
        reply_markup=courier_order_kb(order_id, order.phone, order.latitude, order.longitude)
    )

    # Уведомляем пользователя
    user = await session.get(User, order.user_id)
    if user:
        await notify_user_order_status(bot, order, user.telegram_id)


@router.callback_query(F.data.startswith("courier_status:"))
async def update_courier_status(callback: CallbackQuery, db_user: User,
                                session: AsyncSession, bot: Bot):
    parts = callback.data.split(":")
    order_id = int(parts[1])
    new_status = OrderStatus(parts[2])

    await update_order_status(session, order_id, new_status)
    order = await get_order(session, order_id)
    await callback.answer(f"Статус обновлён: {new_status.value}")

    # Уведомляем пользователя
    user = await session.get(User, order.user_id)
    if user:
        await notify_user_order_status(bot, order, user.telegram_id)

    if new_status == OrderStatus.delivered:
        from utils.loyalty import add_cashback, update_vip_level
        from database.queries import get_user_orders
        user_orders = await get_user_orders(session, order.user_id)
        cashback, bonus = await add_cashback(session, user, order.total)
        total_delivered = len([o for o in user_orders if o.status == OrderStatus.delivered])
        await update_vip_level(session, user, total_delivered)
        await bot.send_message(
            user.telegram_id,
            f"🎉 Спасибо за заказ!\n"
            f"💰 Вам начислено: {cashback:,} сум кэшбека и {bonus} бонусных баллов!"
        )

    await callback.message.edit_text(
        f"📦 Заказ #{order_id}\nСтатус: {new_status.value}",
    )


@router.callback_query(F.data.startswith("courier_order_detail:"))
async def courier_order_detail(callback: CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split(":")[1])
    order = await get_order(session, order_id)
    if not order:
        await callback.answer("Заказ не найден")
        return
    await callback.answer()
    kb = courier_order_kb(order_id, order.phone, order.latitude, order.longitude)
    await callback.message.answer(
        f"📦 <b>Заказ #{order.id}</b>\n\n"
        f"📍 {order.address}\n"
        f"📞 {order.phone}\n"
        f"💰 {order.total:,} сум",
        reply_markup=kb,
        parse_mode="HTML"
    )
