# middlewares/auth.py
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable

from database.queries import get_or_create_user


class AuthMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:

        db_user = data.get("db_user")
        if not db_user:
            session = data.get("session")
            user = event.from_user if hasattr(event, "from_user") else None

            if session and user:
                db_user = await get_or_create_user(
                    session=session,
                    tg_id=user.id,  # ← правильно
                    username=user.username,
                    full_name=user.full_name
                )
                data["db_user"] = db_user

        return await handler(event, data)