from typing import Dict, Callable, Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker


class DataBaseSession(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable,
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        async with self.session_pool() as session:
            data['session'] = session
            return await handler(event, data)

