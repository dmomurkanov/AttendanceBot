import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from .middleware import DataBaseSession
from .handlers import register_handlers
from .engine import session_maker

load_dotenv()

bot = Bot(token=os.getenv('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def main():
    dp.update.middleware.register(DataBaseSession(session_pool=session_maker))

    register_handlers(dp)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
