from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from database.models import User

CASHBACK_PERCENT = 3      # 3% кэшбек
BONUS_PER_ORDER = 50      # бонусы за каждый заказ
VIP_THRESHOLDS = [0, 5, 15, 30]   # кол-во заказов для уровней VIP


async def add_cashback(session: AsyncSession, user: User, order_total: int):
    cashback = int(order_total * CASHBACK_PERCENT / 100)
    bonus = BONUS_PER_ORDER
    await session.execute(
        update(User).where(User.id == user.id).values(
            cashback_balance=User.cashback_balance + cashback,
            bonus_points=User.bonus_points + bonus
        )
    )
    await session.commit()
    return cashback, bonus


async def use_bonus_points(session: AsyncSession, user: User, points: int) -> bool:
    if user.bonus_points < points:
        return False
    await session.execute(
        update(User).where(User.id == user.id).values(
            bonus_points=User.bonus_points - points
        )
    )
    await session.commit()
    return True


async def update_vip_level(session: AsyncSession, user: User, total_orders: int):
    new_level = 0
    for i, threshold in enumerate(VIP_THRESHOLDS):
        if total_orders >= threshold:
            new_level = i
    if new_level != user.vip_level:
        await session.execute(
            update(User).where(User.id == user.id).values(vip_level=new_level)
        )
        await session.commit()
    return new_level


def get_vip_label(level: int) -> str:
    labels = {0: "Стандарт", 1: "Серебро 🥈", 2: "Золото 🥇", 3: "VIP 👑"}
    return labels.get(level, "Стандарт")


async def process_referral(session: AsyncSession, new_user: User, referral_code: str):
    from sqlalchemy import select
    result = await session.execute(
        select(User).where(User.referral_code == referral_code)
    )
    referrer = result.scalar_one_or_none()
    if referrer and referrer.id != new_user.id:
        await session.execute(
            update(User).where(User.id == referrer.id).values(
                bonus_points=User.bonus_points + 200
            )
        )
        await session.execute(
            update(User).where(User.id == new_user.id).values(
                referred_by=referrer.id,
                bonus_points=User.bonus_points + 100
            )
        )
        await session.commit()
        return referrer
    return None
