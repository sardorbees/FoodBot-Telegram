from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.queries import (
    get_cart,
    update_cart_item,
    clear_cart,
    add_to_cart,
    get_product
)

from keyboards.user_kb import cart_kb, main_menu_kb

router = Router()

@router.callback_query(F.data.startswith("add_cart:"))
async def add_to_cart_handler(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User
):

    product_id = int(callback.data.split(":")[1])

    product = await get_product(session, product_id)

    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    # 🔥 добавляем в корзину
    await add_to_cart(
        session=session,
        user_id=db_user.id,
        product_id=product.id,
        quantity=1,
        price=product.price
    )

    await callback.answer("🛒 Добавлено в корзину!")

    # 🔥 показываем сообщение пользователю
    text = (
        f"✅ <b>{product.name}</b> добавлен в корзину\n\n"
        f"💰 Цена: {product.price:,} сум"
    )

    from keyboards.user_kb import product_detail_kb

    await callback.message.answer(
        text,
        reply_markup=product_detail_kb(product.id),
        parse_mode="HTML"
    )



# ================= SHOW CART =================
@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message, session: AsyncSession, db_user: User):

    items = await get_cart(session, db_user.id)

    if not items:
        await message.answer(
            "🛒 Корзина пуста",
            reply_markup=main_menu_kb()
        )
        return

    total = 0
    text = "🛒 <b>Ваша корзина:</b>\n\n"

    for item in items:
        product = item.product
        sum_price = item.unit_price * item.quantity
        total += sum_price

        text += (
            f"🍔 {product.name}\n"
            f"🔢 {item.quantity} x {item.unit_price:,} сум\n"
            f"💰 {sum_price:,} сум\n\n"
        )

    text += f"━━━━━━━━━━\n💵 <b>Итого: {total:,} сум</b>"

    await message.answer(
        text,
        reply_markup=cart_kb(items),
        parse_mode="HTML"
    )


# ================= INCREASE =================
@router.callback_query(F.data.startswith("cart_inc:"))
async def inc(callback: CallbackQuery, session: AsyncSession, db_user: User):

    item_id = int(callback.data.split(":")[1])

    items = await get_cart(session, db_user.id)
    item = next((i for i in items if i.id == item_id), None)

    if item:
        await update_cart_item(session, item_id, item.quantity + 1)

    await callback.answer("➕ Добавлено")

    await callback.message.delete()
    await show_cart(callback.message, session, db_user)


# ================= DECREASE =================
@router.callback_query(F.data.startswith("cart_dec:"))
async def dec(callback: CallbackQuery, session: AsyncSession, db_user: User):

    item_id = int(callback.data.split(":")[1])

    items = await get_cart(session, db_user.id)
    item = next((i for i in items if i.id == item_id), None)

    if item and item.quantity > 1:
        await update_cart_item(session, item_id, item.quantity - 1)
    else:
        await update_cart_item(session, item_id, 0)

    await callback.answer("➖ Уменьшено")

    await callback.message.delete()
    await show_cart(callback.message, session, db_user)


# ================= DELETE ITEM =================
@router.callback_query(F.data.startswith("cart_del:"))
async def delete_item(callback: CallbackQuery, session: AsyncSession, db_user: User):

    item_id = int(callback.data.split(":")[1])

    await update_cart_item(session, item_id, 0)

    await callback.answer("❌ Удалено")

    await callback.message.delete()
    await show_cart(callback.message, session, db_user)


# ================= CLEAR CART =================
@router.callback_query(F.data == "cart_clear")
async def clear(callback: CallbackQuery, session: AsyncSession, db_user: User):

    await clear_cart(session, db_user.id)

    await callback.answer("🗑 Очищено")

    await callback.message.edit_text(
        "🛒 Корзина пуста",
        reply_markup=main_menu_kb()
    )