import json
from database.models import Product


async def load_products_from_json(session):

    with open("data/products.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    for block in data:

        # 🔥 защита от ошибки
        category = block.get("category")
        if not category:
            continue

        category_id = category.get("id")
        if not category_id:
            continue

        products = block.get("products", [])

        for item in products:

            product = Product(
                name=item.get("name"),
                price=item.get("price", 0),
                description=item.get("description"),
                photo_id=item.get("photo"),
                category_id=category_id
            )

            session.add(product)

    await session.commit()