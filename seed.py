"""
Скрипт для заполнения БД начальными данными.
Запуск: python seed.py
"""
import asyncio
from database.connection import init_db, async_session
from database.models import Category, Product, Promocode, User, UserRole
from config.settings import ADMIN_IDS


async def seed():
    await init_db()
    async with async_session() as session:

        # Категории
        categories = [
            Category(name="Пицца", emoji="🍕", sort_order=1),
            Category(name="Бургеры", emoji="🍔", sort_order=2),
            Category(name="Суши", emoji="🍣", sort_order=3),
            Category(name="Напитки", emoji="🥤", sort_order=4),
            Category(name="Десерты", emoji="🍰", sort_order=5),
            Category(name="Комбо", emoji="🎁", sort_order=6),
        ]
        session.add_all(categories)
        await session.flush()

        # Блюда
        products = [
            Product(category_id=categories[0].id, name="Маргарита",
                    description="Классика: томатный соус, моцарелла", price=45000, weight=400, cook_time=20),
            Product(category_id=categories[0].id, name="Пепперони",
                    description="Пикантная пицца с колбасой пепперони", price=55000, weight=450, cook_time=25),
            Product(category_id=categories[1].id, name="Классический бургер",
                    description="Говяжья котлета, салат, томат, соус", price=35000, weight=300, cook_time=15),
            Product(category_id=categories[1].id, name="Чизбургер",
                    description="Двойной сыр, говядина, маринованный огурец", price=40000, weight=320, cook_time=15),
            Product(category_id=categories[2].id, name="Сет Калифорния",
                    description="8 роллов с крабом и авокадо", price=65000, weight=250, cook_time=30),
            Product(category_id=categories[3].id, name="Кола",
                    description="Coca-Cola 0.5л", price=10000, weight=500, cook_time=0),
            Product(category_id=categories[4].id, name="Чизкейк",
                    description="Нежный сливочный чизкейк", price=25000, weight=150, cook_time=0),
        ]
        session.add_all(products)

        # Промокод
        promo = Promocode(
            code="WELCOME",
            discount_percent=10,
            min_order=50000,
            usage_limit=100,
            is_active=True
        )
        session.add(promo)

        # Добавляем администраторов
        import random, string
        for admin_tg_id in ADMIN_IDS:
            if admin_tg_id:
                ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                admin_user = User(
                    telegram_id=admin_tg_id,
                    full_name="Admin",
                    role=UserRole.admin,
                    referral_code=ref_code
                )
                session.add(admin_user)

        await session.commit()
        print("✅ База данных заполнена начальными данными!")
        print(f"   Категорий: {len(categories)}")
        print(f"   Блюд: {len(products)}")
        print(f"   Промокод: WELCOME (скидка 10%, мин. заказ 50 000 сум)")


if __name__ == "__main__":
    asyncio.run(seed())
