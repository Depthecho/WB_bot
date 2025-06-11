import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db
from handlers import router
from scheduler import check_for_new_reviews

# Настраиваем, как будут выводиться сообщения о работе бота.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)


# Основная функция, которая запускает бота.
async def main():
    # Проверяем, есть ли токен бота. Без него бот не сможет работать.
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN не установлен. Пожалуйста, добавьте его в файл .env в корне проекта.")
        print("Бот не может быть запущен без BOT_TOKEN.")
        return

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router) # Подключаем все наши команды (из handlers.py) к боту.

    init_db() # Запускаем настройку базы данных

    logging.info("Запускаем планировщик проверки отзывов в фоновом режиме...")
    # Запускаем проверку отзывов в отдельном режиме, чтобы она работала "в фоне"
    # и не мешала боту отвечать на команды.
    asyncio.create_task(check_for_new_reviews(bot))

    logging.info("Бот запущен. Начинаем поллинг входящих сообщений...")
    try:
        # Запускаем бота
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        # Если при запуске бота произошла ошибка, выводим её.
        logging.error(f"Ошибка при запуске поллинга бота: {e}")
    finally:
        # Этот код выполнится, когда бот останавливается.
        await bot.session.close() # Закрываем соединение бота с Telegram.
        logging.info("Сессия бота закрыта. Бот остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем (Ctrl+C).")
    except Exception as e:
        # Если произошла какая-то очень серьезная ошибка.
        logging.critical(f"Критическая ошибка при запуске бота: {e}", exc_info=True)