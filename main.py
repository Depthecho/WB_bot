import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db
from handlers import router
from scheduler import check_for_new_reviews

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)


async def main():
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN не установлен. Пожалуйста, добавьте его в файл .env в корне проекта.")
        print("Бот не может быть запущен без BOT_TOKEN.")
        return

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    init_db()

    logging.info("Запускаем планировщик проверки отзывов в фоновом режиме...")
    asyncio.create_task(check_for_new_reviews(bot))

    logging.info("Бот запущен. Начинаем поллинг входящих сообщений...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logging.error(f"Ошибка при запуске поллинга бота: {e}")
    finally:
        await bot.session.close()
        logging.info("Сессия бота закрыта. Бот остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем (Ctrl+C).")
    except Exception as e:
        logging.critical(f"Критическая ошибка при запуске бота: {e}", exc_info=True)