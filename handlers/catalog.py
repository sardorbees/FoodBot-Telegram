from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Product
from database.queries import (
    get_categories, get_products_by_category,
    get_product_with_details, get_product,
    toggle_favorite, add_to_cart
)
from keyboards.user_kb import (
    categories_kb, products_kb, product_detail_kb,
    sizes_kb, main_menu_kb
)

router = Router()


@router.message(F.text.lower().contains("меню"))
async def show_menu(
    message: Message,
    session: AsyncSession
):
    categories = await get_categories(session)

    await message.answer(
        "🍔 <b>Выберите категорию:</b>",
        parse_mode="HTML",
        reply_markup=categories_kb(categories)
    )



@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()
    categories = await get_categories(session)
    await callback.message.edit_text(
        "🍔 <b>Выберите категорию:</b>",
        reply_markup=categories_kb(categories),
        parse_mode="HTML"
    )

from sqlalchemy import select

@router.callback_query(F.data.startswith("cat:"))
async def show_products(callback: CallbackQuery, session: AsyncSession):

    category_id = int(callback.data.split(":")[1])

    products = await get_products_by_category(session, category_id)

    await callback.message.edit_text(
        "🍽 <b>Выберите товар:</b>",
        parse_mode="HTML",
        reply_markup=products_kb(products, category_id)  # 👈 FIX
    )

    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def show_product(callback: CallbackQuery, session: AsyncSession):

    product_id = int(callback.data.split(":")[1])

    product = await get_product_with_details(session, product_id)

    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    text = (
        f"🍔 <b>{product.name}</b>\n\n"
        f"💰 {product.price} сум\n\n"
        f"📝 {product.description or ''}"
    )

    await callback.message.answer_photo(
        photo=product.photo_id,   # 👈 FIX
        caption=text,
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data.startswith("sizes:"))
async def show_sizes(callback: CallbackQuery, session: AsyncSession):
    product_id = int(callback.data.split(":")[1])
    product = await get_product_with_details(session, product_id)

    if not product or not product.sizes:
        await callback.answer("Размеры недоступны", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(
        f"📏 <b>Выберите размер для «{product.name}»:</b>",
        reply_markup=sizes_kb(product_id, product.sizes),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("add_cart:"))
async def add_to_cart_cb(callback: CallbackQuery, db_user: User, session: AsyncSession):
    parts = callback.data.split(":")
    product_id = int(parts[1])
    size_id = int(parts[2]) if len(parts) > 2 and parts[2] != "0" else None

    product = await get_product_with_details(session, product_id)
    if not product:
        await callback.answer("❌ Блюдо не найдено", show_alert=True)
        return

    price = product.price
    size_name = ""

    if size_id:
        for size in product.sizes:
            if size.id == size_id:
                price += size.price_modifier
                size_name = f" ({size.name})"
                break

    await add_to_cart(
        session=session,
        user_id=db_user.id,
        product_id=product.id,
        quantity=1,
        price=price,
        size_id=size_id
    )

    await callback.answer(f"✅ «{product.name}{size_name}» добавлен в корзину!", show_alert=False)


@router.callback_query(F.data.startswith("fav:"))
async def toggle_fav(callback: CallbackQuery, db_user: User, session: AsyncSession):
    product_id = int(callback.data.split(":")[1])
    is_added = await toggle_favorite(session, db_user.id, product_id)

    if is_added:
        await callback.answer("❤️ Добавлено в избранное!")
    else:
        await callback.answer("💔 Удалено из избранного")


@router.callback_query(F.data.startswith("back_products:"))
async def back_to_products(callback: CallbackQuery, session: AsyncSession):
    category_id = int(callback.data.split(":")[1])  # лучше передавать category_id
    products = await get_products_by_category(session, category_id)

    await callback.answer()
    await callback.message.edit_text(
        "🍽 <b>Выберите блюдо:</b>",
        reply_markup=products_kb(products, category_id),
        parse_mode="HTML"
    )