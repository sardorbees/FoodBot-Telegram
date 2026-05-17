from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.queries import get_product_with_details

router = Router()


@router.callback_query(F.data.startswith("product:"))
async def show_product(callback: CallbackQuery, session: AsyncSession):

    product_id = int(callback.data.split(":")[1])

    product = await get_product_with_details(session, product_id)

    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    text = (
        f"🍔 <b>{product.name}</b>\n\n"
        f"💰 Цена: {product.price} сум\n\n"
        f"📝 {product.description or 'Нет описания'}"
    )

    await callback.message.answer_photo(
        photo=product.photo_id,   # 👈 ВАЖНО
        caption=text,
        parse_mode="HTML"
    )

    await callback.answer()