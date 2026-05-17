import json
from sqlalchemy import select

from database.models import Category, Product


# ================= CATEGORY SEED =================
async def seed_categories(session):

    existing = await session.execute(select(Category))
    existing = existing.scalars().all()

    if existing:
        return

    categories = [
        Category(id=1, name="Бургеры", emoji="🍔"),
        Category(id=2, name="Лаваш", emoji="🌯"),
    ]

    session.add_all(categories)
    await session.commit()


# ================= PRODUCT SEED (SAFE UPSERT) =================
async def seed_products_from_json(session, file_path="data/products.json"):

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for block in data:

        category = block.get("category")
        if not category:
            continue

        category_id = category.get("id")
        if not category_id:
            continue

        for item in block.get("products", []):

            name = item.get("name")

            # 🔥 CHECK DUPLICATE
            result = await session.execute(
                select(Product).where(Product.name == name)
            )
            existing = result.scalars().first()

            if existing:
                # можно обновлять цену/описание если хочешь
                existing.price = item.get("price", existing.price)
                existing.description = item.get("description", existing.description)
                existing.photo_id = item.get("photo", existing.photo_id)
                continue

            product = Product(
                name=name,
                price=item.get("price", 0),
                description=item.get("description"),
                photo_id=item.get("photo"),
                category_id=category_id
            )

            session.add(product)

    await session.commit()