from aiogram.utils.keyboard import InlineKeyboardBuilder


def categories_kb(categories):
    builder = InlineKeyboardBuilder()

    for category in categories:
        builder.button(
            text=category.name,
            callback_data=f"cat:{category.id}"
        )

    builder.adjust(1)

    return builder.as_markup()


def products_kb(products):

    builder = InlineKeyboardBuilder()

    for p in products:
        builder.button(
            text=f"{p.name} • {p.price} сум",
            callback_data=f"product:{p.id}"
        )

    builder.adjust(1)
    return builder.as_markup()