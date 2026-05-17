from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User, UserRole, Order, OrderStatus, Product, Category
from database.queries import (
    get_new_orders, get_order, update_order_status,
    get_categories, get_products_by_category, get_sales_stats
)
from keyboards.admin_kb import (
    admin_menu_kb, admin_orders_kb, admin_order_detail_kb,
    admin_assign_courier_kb, admin_product_kb
)
from utils.notifications import notify_user_order_status, broadcast_message

router = Router()


def admin_only(role: UserRole):
    return role == UserRole.admin


# ─── МЕНЮ АДМИНА ────────────────────────────────────────────────

@router.message(F.text == "📋 Заказы")
async def admin_orders(message: Message, db_user: User, session: AsyncSession):
    if not admin_only(db_user.role):
        return
    orders = await get_new_orders(session)
    if not orders:
        await message.answer("Нет новых заказов ✅")
        return
    await message.answer(
        f"📋 <b>Новые заказы ({len(orders)}):</b>",
        reply_markup=admin_orders_kb(orders),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_orders")
async def admin_orders_cb(callback: CallbackQuery, db_user: User, session: AsyncSession):
    if not admin_only(db_user.role):
        return
    orders = await get_new_orders(session)
    await callback.answer()
    await callback.message.edit_text(
        f"📋 <b>Заказы ({len(orders)}):</b>",
        reply_markup=admin_orders_kb(orders),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_order:"))
async def admin_order_detail(callback: CallbackQuery, db_user: User, session: AsyncSession):
    if not admin_only(db_user.role):
        return
    order_id = int(callback.data.split(":")[1])
    order = await get_order(session, order_id)
    if not order:
        await callback.answer("Заказ не найден")
        return

    await callback.answer()
    items_text = "\n".join(
        f"  • {i.product_name} × {i.quantity} = {i.unit_price * i.quantity:,} сум"
        for i in order.items
    )
    text = (
        f"📦 <b>Заказ #{order.id}</b>\n\n"
        f"👤 Пользователь: {order.user_id}\n"
        f"📍 Адрес: {order.address}\n"
        f"📞 Телефон: {order.phone}\n"
        f"💳 Оплата: {order.payment_method.value}\n"
        f"⏰ Время: {order.delivery_time}\n"
        f"💬 Комментарий: {order.comment or '—'}\n\n"
        f"🛒 Состав:\n{items_text}\n\n"
        f"💰 Итого: <b>{order.total:,} сум</b>\n"
        f"📊 Статус: {order.status.value}"
    )
    await callback.message.edit_text(
        text, reply_markup=admin_order_detail_kb(order_id), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_status:"))
async def admin_change_status(callback: CallbackQuery, db_user: User,
                              session: AsyncSession, bot: Bot):
    if not admin_only(db_user.role):
        return
    parts = callback.data.split(":")
    order_id = int(parts[1])
    new_status = OrderStatus(parts[2])

    await update_order_status(session, order_id, new_status)
    order = await get_order(session, order_id)

    user = await session.get(User, order.user_id)
    if user:
        await notify_user_order_status(bot, order, user.telegram_id)

    await callback.answer(f"✅ Статус обновлён: {new_status.value}")
    await callback.message.edit_text(
        f"📦 Заказ #{order_id}\nНовый статус: <b>{new_status.value}</b>",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_assign:"))
async def admin_assign(callback: CallbackQuery, db_user: User, session: AsyncSession):
    if not admin_only(db_user.role):
        return
    order_id = int(callback.data.split(":")[1])
    from database.queries import get_all_couriers
    couriers = await get_all_couriers(session)
    if not couriers:
        await callback.answer("Нет доступных курьеров!", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(
        "🚴 Выберите курьера:",
        reply_markup=admin_assign_courier_kb(order_id, couriers)
    )


@router.callback_query(F.data.startswith("assign_courier:"))
async def do_assign_courier(callback: CallbackQuery, db_user: User,
                             session: AsyncSession, bot: Bot):
    if not admin_only(db_user.role):
        return
    parts = callback.data.split(":")
    order_id = int(parts[1])
    courier_db_id = int(parts[2])

    from database.queries import assign_courier
    await assign_courier(session, order_id, courier_db_id)
    order = await get_order(session, order_id)

    courier = await session.get(User, courier_db_id)
    order_user = await session.get(User, order.user_id)

    if order_user:
        await notify_user_order_status(bot, order, order_user.telegram_id)

    await callback.answer("✅ Курьер назначен!")
    await callback.message.edit_text(
        f"✅ Курьер <b>{courier.full_name}</b> назначен на заказ #{order_id}",
        parse_mode="HTML"
    )


# ─── СТАТИСТИКА ─────────────────────────────────────────────────

@router.message(F.text == "📊 Статистика")
async def admin_stats(message: Message, db_user: User, session: AsyncSession):
    if not admin_only(db_user.role):
        return
    stats = await get_sales_stats(session)
    text = (
        f"📊 <b>Статистика продаж</b>\n\n"
        f"📦 Всего заказов: {stats['total_orders']}\n"
        f"🗓 Сегодня: {stats['today_orders']}\n"
        f"💰 Общая выручка: {stats['total_revenue']:,} сум"
    )
    await message.answer(text, parse_mode="HTML")


# ─── УПРАВЛЕНИЕ МЕНЮ ────────────────────────────────────────────

class AddProductState(StatesGroup):
    category = State()
    name = State()
    description = State()
    price = State()
    weight = State()
    cook_time = State()
    photo = State()


@router.message(F.text == "🍽 Меню")
async def admin_menu_products(message: Message, db_user: User, session: AsyncSession):
    if not admin_only(db_user.role):
        return
    categories = await get_categories(session)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=f"{cat.emoji} {cat.name}", callback_data=f"admin_cat:{cat.id}")
    builder.button(text="➕ Добавить блюдо", callback_data="admin_add_product")
    builder.adjust(2)
    await message.answer("🍽 <b>Управление меню:</b>",
                         reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "admin_add_product")
async def start_add_product(callback: CallbackQuery, db_user: User,
                             session: AsyncSession, state: FSMContext):
    if not admin_only(db_user.role):
        return
    await callback.answer()
    categories = await get_categories(session)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=f"{cat.emoji} {cat.name}", callback_data=f"newprod_cat:{cat.id}")
    builder.adjust(2)
    await state.set_state(AddProductState.category)
    await callback.message.answer("Выберите категорию:", reply_markup=builder.as_markup())


@router.callback_query(AddProductState.category, F.data.startswith("newprod_cat:"))
async def add_product_name(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split(":")[1])
    await state.update_data(category_id=cat_id)
    await state.set_state(AddProductState.name)
    await callback.answer()
    await callback.message.answer("✏️ Введите название блюда:")


@router.message(AddProductState.name)
async def add_product_description(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProductState.description)
    await message.answer("📝 Введите описание:")


@router.message(AddProductState.description)
async def add_product_price(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddProductState.price)
    await message.answer("💰 Введите цену (в сумах):")


@router.message(AddProductState.price)
async def add_product_weight(message: Message, state: FSMContext):
    try:
        price = int(message.text.replace(" ", "").replace(",", ""))
        await state.update_data(price=price)
        await state.set_state(AddProductState.weight)
        await message.answer("⚖️ Введите вес (в граммах):")
    except ValueError:
        await message.answer("❌ Введите число:")


@router.message(AddProductState.weight)
async def add_product_cook_time(message: Message, state: FSMContext):
    try:
        weight = int(message.text)
        await state.update_data(weight=weight)
        await state.set_state(AddProductState.cook_time)
        await message.answer("⏱ Время приготовления (в минутах):")
    except ValueError:
        await message.answer("❌ Введите число:")


@router.message(AddProductState.cook_time)
async def add_product_photo(message: Message, state: FSMContext):
    try:
        cook_time = int(message.text)
        await state.update_data(cook_time=cook_time)
        await state.set_state(AddProductState.photo)
        await message.answer("🖼 Отправьте фото блюда (или напишите 'пропустить'):")
    except ValueError:
        await message.answer("❌ Введите число:")


@router.message(AddProductState.photo)
async def save_new_product(message: Message, state: FSMContext,
                            db_user: User, session: AsyncSession):
    data = await state.get_data()
    photo_id = None

    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text and message.text.lower() != "пропустить":
        await message.answer("❌ Отправьте фото или напишите 'пропустить'")
        return

    product = Product(
        category_id=data["category_id"],
        name=data["name"],
        description=data["description"],
        price=data["price"],
        weight=data["weight"],
        cook_time=data["cook_time"],
        photo_id=photo_id
    )
    session.add(product)
    await session.commit()
    await state.clear()

    await message.answer(
        f"✅ Блюдо <b>{product.name}</b> добавлено!",
        reply_markup=admin_menu_kb(),
        parse_mode="HTML"
    )


# ─── РАССЫЛКА ───────────────────────────────────────────────────

class BroadcastState(StatesGroup):
    message = State()


@router.message(F.text == "📣 Рассылка")
async def start_broadcast(message: Message, db_user: User, state: FSMContext):
    if not admin_only(db_user.role):
        return
    await state.set_state(BroadcastState.message)
    await message.answer(
        "📣 Введите текст рассылки (можно с фото).\n"
        "Сообщение будет отправлено всем пользователям:"
    )


@router.message(BroadcastState.message)
async def do_broadcast(message: Message, state: FSMContext,
                        db_user: User, session: AsyncSession, bot: Bot):
    result = await session.execute(select(User.telegram_id).where(User.role == UserRole.user))
    user_ids = [row[0] for row in result.fetchall()]

    text = message.caption or message.text or ""
    photo_id = message.photo[-1].file_id if message.photo else None

    sent, failed = await broadcast_message(bot, user_ids, text, photo_id)
    await state.clear()
    await message.answer(
        f"📣 Рассылка завершена!\n✅ Отправлено: {sent}\n❌ Ошибок: {failed}"
    )


# ─── УПРАВЛЕНИЕ КУРЬЕРАМИ ────────────────────────────────────────

@router.message(F.text == "👥 Курьеры")
async def admin_couriers(message: Message, db_user: User, session: AsyncSession):
    if not admin_only(db_user.role):
        return
    from database.queries import get_all_couriers
    couriers = await get_all_couriers(session)
    if not couriers:
        await message.answer("Нет зарегистрированных курьеров.")
        return
    text = "👥 <b>Курьеры:</b>\n\n"
    for c in couriers:
        text += f"• {c.full_name or c.username} — @{c.username}\n"
    await message.answer(text, parse_mode="HTML")
