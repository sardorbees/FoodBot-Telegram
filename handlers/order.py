from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, PaymentMethod
from database.queries import get_cart, create_order, get_cart_total
from keyboards.user_kb import (
    location_kb, phone_kb, payment_kb,
    delivery_time_kb, main_menu_kb
)
from utils.notifications import notify_couriers_new_order, notify_admins_new_order
from config.settings import ADMIN_IDS

router = Router()


class CheckoutState(StatesGroup):
    address = State()
    phone = State()
    delivery_time = State()
    payment = State()
    comment = State()
    confirm = State()


@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, db_user: User,
                         session: AsyncSession, state: FSMContext):
    cart = await get_cart(session, db_user.id)
    if not cart:
        await callback.answer("Корзина пуста!", show_alert=True)
        return

    await callback.answer()
    await state.set_state(CheckoutState.address)

    # Если есть номер телефона — сохраняем сразу
    if db_user.phone:
        await state.update_data(phone=db_user.phone)

    await callback.message.answer(
        "📍 <b>Шаг 1/4: Адрес доставки</b>\n\n"
        "Отправьте геолокацию или введите адрес текстом:",
        reply_markup=location_kb(),
        parse_mode="HTML"
    )


# ─── ШАГ 1: АДРЕС ───────────────────────────────────────────────

@router.message(CheckoutState.address, F.location)
async def got_location(message: Message, state: FSMContext, db_user: User, session: AsyncSession):
    lat = message.location.latitude
    lon = message.location.longitude
    address = f"📍 Геолокация: {lat:.4f}, {lon:.4f}"

    await state.update_data(address=address, latitude=lat, longitude=lon)
    from database.queries import save_address
    await save_address(session, db_user.id, address, lat, lon)

    await _ask_phone(message, state, db_user)


@router.message(CheckoutState.address, F.text == "✏️ Ввести адрес вручную")
async def manual_address_prompt(message: Message):
    await message.answer("✏️ Введите адрес доставки текстом:")


@router.message(CheckoutState.address, F.text & ~F.text.startswith("/"))
async def got_address_text(message: Message, state: FSMContext, db_user: User, session: AsyncSession):
    address = message.text.strip()
    if len(address) < 5:
        await message.answer("❌ Слишком короткий адрес. Введите подробнее:")
        return

    await state.update_data(address=address)
    from database.queries import save_address
    await save_address(session, db_user.id, address)
    await _ask_phone(message, state, db_user)


async def _ask_phone(message: Message, state: FSMContext, db_user: User):
    data = await state.get_data()
    if data.get("phone"):
        await state.set_state(CheckoutState.delivery_time)
        await message.answer(
            "⏰ <b>Шаг 2/4: Время доставки</b>\n\nВыберите удобное время:",
            reply_markup=delivery_time_kb(),
            parse_mode="HTML"
        )
    else:
        await state.set_state(CheckoutState.phone)
        await message.answer(
            "📱 <b>Шаг 2/4: Номер телефона</b>\n\n"
            "Отправьте ваш номер для связи курьера:",
            reply_markup=phone_kb(),
            parse_mode="HTML"
        )


# ─── ШАГ 2: ТЕЛЕФОН ─────────────────────────────────────────────

@router.message(CheckoutState.phone, F.contact)
async def got_contact(message: Message, state: FSMContext, session: AsyncSession):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    from database.queries import update_user_phone
    await update_user_phone(session, message.from_user.id, phone)
    await _ask_delivery_time(message, state)


@router.message(CheckoutState.phone, F.text & ~F.text.startswith("/"))
async def got_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    # Простая валидация
    digits = ''.join(c for c in phone if c.isdigit())
    if len(digits) < 9:
        await message.answer("❌ Неверный номер. Введите в формате +998901234567:")
        return
    await state.update_data(phone=phone)
    await _ask_delivery_time(message, state)


async def _ask_delivery_time(message: Message, state: FSMContext):
    await state.set_state(CheckoutState.delivery_time)
    await message.answer(
        "⏰ <b>Шаг 3/4: Время доставки</b>\n\nВыберите удобное время:",
        reply_markup=delivery_time_kb(),
        parse_mode="HTML"
    )


# ─── ШАГ 3: ВРЕМЯ ───────────────────────────────────────────────

@router.callback_query(CheckoutState.delivery_time, F.data.startswith("time:"))
async def got_delivery_time(callback: CallbackQuery, state: FSMContext):
    time_slot = callback.data.split(":", 1)[1]
    await state.update_data(delivery_time=time_slot)
    await callback.answer()
    await callback.message.answer(
        "💳 <b>Шаг 4/4: Способ оплаты</b>\n\nВыберите удобный способ:",
        reply_markup=payment_kb(),
        parse_mode="HTML"
    )
    await state.set_state(CheckoutState.payment)


# ─── ШАГ 4: ОПЛАТА ──────────────────────────────────────────────

@router.callback_query(CheckoutState.payment, F.data.startswith("pay:"))
async def got_payment(callback: CallbackQuery, state: FSMContext,
                      db_user: User, session: AsyncSession):
    method_str = callback.data.split(":")[1]
    await state.update_data(payment_method=method_str)
    await callback.answer()

    await callback.message.answer(
        "💬 Добавьте комментарий к заказу (или нажмите «Пропустить»):",
        reply_markup=_skip_comment_kb()
    )
    await state.set_state(CheckoutState.comment)


def _skip_comment_kb():
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="Пропустить ➡️", callback_data="skip_comment")
    return builder.as_markup()


@router.message(CheckoutState.comment, F.text)
async def got_comment(message: Message, state: FSMContext, bot: Bot,
                      db_user: User, session: AsyncSession):
    await state.update_data(comment=message.text)
    await _confirm_order(message, state, bot, db_user, session)


@router.callback_query(CheckoutState.comment, F.data == "skip_comment")
async def skip_comment(callback: CallbackQuery, state: FSMContext, bot: Bot,
                       db_user: User, session: AsyncSession):
    await callback.answer()
    await state.update_data(comment="")
    await _confirm_order(callback.message, state, bot, db_user, session)


async def _confirm_order(message: Message, state: FSMContext, bot: Bot,
                         db_user: User, session: AsyncSession):
    data = await state.get_data()

    payment_labels = {
        "click": "💳 Click", "payme": "💳 Payme",
        "uzum": "🏦 Uzum Bank", "cash": "💵 Наличные", "card": "🃏 Карта"
    }

    order = await create_order(session, db_user.id, {
        "payment_method": data["payment_method"],
        "address": data["address"],
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "phone": data["phone"],
        "comment": data.get("comment", ""),
        "delivery_time": data.get("delivery_time", "Как можно скорее"),
        "discount": data.get("discount", 0),
    })

    await state.clear()

    text = (
        f"✅ <b>Заказ #{order.id} принят!</b>\n\n"
        f"📍 Адрес: {order.address}\n"
        f"📞 Телефон: {order.phone}\n"
        f"⏰ Доставка: {order.delivery_time}\n"
        f"💳 Оплата: {payment_labels.get(order.payment_method.value, '')}\n"
        f"💰 Итого: <b>{order.total:,} сум</b>\n\n"
        f"⏳ Ожидайте — мы уже готовим ваш заказ!"
    )

    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")

    # Уведомления
    await notify_couriers_new_order(bot, order, session)
    await notify_admins_new_order(bot, order, ADMIN_IDS)
