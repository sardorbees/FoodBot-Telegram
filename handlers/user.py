from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, UserRole
from database.queries import (
    get_user_orders,
    get_favorites,
    get_active_promotions,
    get_user_addresses
)
from keyboards.user_kb import main_menu_kb, order_status_kb, addresses_kb
from keyboards.admin_kb import admin_menu_kb, courier_menu_kb
from config.settings import SUPPORT_USERNAME

router = Router()

STATUS_LABELS = {
    "new": "🆕 Новый",
    "preparing": "👨‍🍳 Готовится",
    "courier_assigned": "📦 Передан курьеру",
    "in_delivery": "🚴 В пути",
    "delivered": "✅ Доставлен",
    "cancelled": "❌ Отменён",
}


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    db_user: User,
    session: AsyncSession,
    state: FSMContext
):
    await state.clear()
    name = message.from_user.first_name

    # Реферальная система
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            from utils.loyalty import process_referral
            referrer = await process_referral(session, db_user, args[1][4:])
            if referrer:
                await message.answer("🎁 Вы получили 100 бонусных баллов по реферальной ссылке!")
        except:
            pass  # если модуль не готов — пропускаем

    welcome = f"Привет, {name}! 👋\n\n🍔 Я бот доставки еды. Выберите раздел:"

    if db_user.role == UserRole.admin:
        await message.answer(
            welcome + "\n\n⚙️ Вы вошли как <b>администратор</b>.",
            reply_markup=admin_menu_kb(),
            parse_mode="HTML"
        )
    elif db_user.role == UserRole.courier:
        await message.answer(
            welcome + "\n\n🚴 Вы вошли как <b>курьер</b>.",
            reply_markup=courier_menu_kb(),
            parse_mode="HTML"
        )
    else:
        await message.answer(welcome, reply_markup=main_menu_kb(), parse_mode="HTML")


@router.message(F.text == "📦 Мои заказы")
async def my_orders(message: Message, db_user: User, session: AsyncSession):
    orders = await get_user_orders(session, db_user.id)
    if not orders:
        await message.answer("У вас пока нет заказов. 🍽\nСделайте первый заказ!")
        return

    text = "📦 <b>Ваши заказы:</b>\n\n"
    for order in orders[:10]:
        status = STATUS_LABELS.get(order.status.value, order.status.value)
        text += (
            f"🔹 Заказ <b>#{order.id}</b>\n"
            f"   Статус: {status}\n"
            f"   Сумма: {order.total:,} сум\n"
            f"   Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "❤️ Избранное")
async def my_favorites(message: Message, db_user: User, session: AsyncSession):
    favorites = await get_favorites(session, db_user.id)
    if not favorites:
        await message.answer("❤️ У вас пока нет избранных блюд.")
        return

    text = "❤️ <b>Избранные блюда:</b>\n\n"
    for fav in favorites:
        text += f"• {fav.product.name} — {fav.product.price:,} сум\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🎁 Акции")
async def promotions(message: Message, session: AsyncSession):
    promos = await get_active_promotions(session)
    if not promos:
        await message.answer("🎁 Сейчас нет активных акций.")
        return

    for promo in promos:
        text = f"🎁 <b>{promo.title}</b>\n\n{promo.description}"
        if promo.photo_id:
            await message.answer_photo(promo.photo_id, caption=text, parse_mode="HTML")
        else:
            await message.answer(text, parse_mode="HTML")


@router.message(F.text == "☎️ Поддержка")
async def support(message: Message):
    text = (
        f"☎️ <b>Поддержка</b>\n\n"
        f"📩 Связаться с нами: {SUPPORT_USERNAME}\n"
        f"🕐 Рабочее время: 9:00 — 23:00"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📍 Адрес доставки")
async def my_addresses(message: Message, db_user: User, session: AsyncSession):
    addresses = await get_user_addresses(session, db_user.id)
    if not addresses:
        await message.answer("У вас нет сохранённых адресов.")
        return
    await message.answer("📍 <b>Ваши адреса:</b>",
                        reply_markup=addresses_kb(addresses),
                        parse_mode="HTML")


# Callback для кнопки "Мои заказы"
@router.callback_query(F.data == "my_orders")
async def my_orders_cb(callback: CallbackQuery, db_user: User, session: AsyncSession):
    await callback.answer()
    await my_orders(callback.message, db_user, session)