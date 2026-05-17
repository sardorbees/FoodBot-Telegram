# middlewares/user_middleware.py
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable

from database.queries import get_or_create_user


class UserMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:

        session = data.get("session")
        if not session:
            return await handler(event, data)

        tg_user = getattr(event, "from_user", None)
        if tg_user:
            db_user = await get_or_create_user(
                session=session,
                tg_id=tg_user.id,  # ← правильно
                username=tg_user.username,
                full_name=tg_user.full_name
            )
            data["db_user"] = db_user

        return await handler(event, data)