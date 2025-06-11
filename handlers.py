from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Product
from database import get_db
from wildberries_api import get_product_info
from typing import AsyncGenerator

router = Router()

# Эта функция помогает получать сессию базы данных.
async def get_db_session() -> AsyncGenerator[Session, None]:
    async for session in get_db():
        yield session

# Обработчик команды /start.
# Бот отвечает приветствием и подсказками.
@router.message(Command("start"))
async def command_start_handler(message: Message):
    print(f"DEBUG_HANDLER: Получена команда /start от пользователя {message.from_user.id}")
    await message.answer(
        "Привет! Я бот для мониторинга негативных отзывов Wildberries. "
        "Чтобы начать мониторинг, используй команду /article [артикул товара]."
        "\nНапример: `/article 12345678`\n"
        "Используй /help для получения списка команд."
    )

# Обработчик команды /help.
# Бот показывает список всех доступных команд.
@router.message(Command("help"))
async def command_help_handler(message: Message):
    print(f"DEBUG_HANDLER: Получена команда /help от пользователя {message.from_user.id}")
    await message.answer(
        "Доступные команды:\n"
        "/start - Приветствие\n"
        "/article [артикул] - Добавить товар для мониторинга\n"
        "/stop_monitoring [артикул] - Удалить товар из мониторинга\n"
        "/help - Справка по командам"
    )

# Обработчик команды /article.
# Добавляет товар для отслеживания негативных отзывов.
@router.message(Command("article"))
async def add_article_handler(message: Message):
    print(f"DEBUG_HANDLER: Получена команда /article от пользователя {message.from_user.id}: '{message.text}'")
    parts = message.text.split()
    if len(parts) < 2: # Если артикул не указан
        await message.answer("Пожалуйста, укажите артикул товара. Например: `/article 12345678`")
        return

    article = parts[1].strip() # Получаем артикул из сообщения

    if not article.isdigit(): # Проверяем, что артикул состоит только из цифр
        await message.answer("Артикул должен состоять только из цифр. Пожалуйста, проверьте ввод.")
        return

    async with get_db() as db: # Открываем сессию базы данных
        try:
            print(f"DEBUG_HANDLER: Пытаемся найти артикул {article} в БД.")
            # Ищем товар в базе данных по артикулу.
            existing_product = db.execute(select(Product).filter_by(article=article)).scalar_one_or_none()

            print(f"DEBUG_HANDLER: Результат поиска existing_product для артикула {article}: {existing_product}")
            print(f"DEBUG_HANDLER: Тип existing_product: {type(existing_product)}")

            if existing_product: # Если товар уже отслеживается
                print(f"DEBUG_HANDLER: Товар с артикулом {article} уже найден в БД.")
                await message.answer(f"Товар с артикулом {article} уже отслеживается.")
                return

            print(f"DEBUG_HANDLER: Товар {article} не найден в нашей БД, запрашиваем информацию у Wildberries API.")
            # Запрашиваем информацию о товаре у Wildberries.
            product_info = await get_product_info(article)

            if not product_info: # Если Wildberries не дал информацию о товаре
                print(f"DEBUG_HANDLER: Не удалось получить информацию о товаре {article} от Wildberries API.")
                await message.answer(f"Не удалось найти информацию о товаре с артикулом {article}. Проверьте артикул.")
                return

            # Создаем новую запись о товаре и добавляем её в базу данных.
            new_product = Product(article=article, name=product_info.get('name', 'Неизвестное название'))
            db.add(new_product)
            db.commit()
            db.refresh(new_product) # Обновляем объект, чтобы получить ID из базы данных.

            print(f"DEBUG_HANDLER: Товар '{new_product.name}' (артикул: {new_product.article}) успешно добавлен в БД.")
            await message.answer(
                f"Товар '{new_product.name}' (артикул: {new_product.article}) добавлен для мониторинга.\n"
                "Я буду проверять новые негативные отзывы каждые 30 минут."
            )
        except Exception as e: # Если произошла какая-то ошибка
            db.rollback() # Отменяем все изменения в базе данных.
            print(f"ERROR_HANDLER: Произошла ошибка при добавлении/проверке товара: {e}")
            await message.answer(f"Произошла ошибка при добавлении товара: {e}")

# Обработчик команды /stop_monitoring.
# Удаляет товар из списка отслеживаемых.
@router.message(Command("stop_monitoring"))
async def stop_monitoring_handler(message: Message):
    print(f"DEBUG_HANDLER: Получена команда /stop_monitoring от пользователя {message.from_user.id}: '{message.text}'")
    parts = message.text.split()
    if len(parts) < 2: # Если артикул не указан
        await message.answer(
            "Пожалуйста, укажите артикул товара, который нужно удалить из мониторинга. Например: `/stop_monitoring 12345678`")
        return

    article = parts[1].strip() # Получаем артикул

    async with get_db() as db: # Открываем сессию базы данных
        try:
            # Ищем товар для удаления.
            product_to_delete = db.execute(select(Product).filter_by(article=article)).scalar_one_or_none()
            if product_to_delete: # Если товар найден
                db.delete(product_to_delete) # Удаляем товар из сессии.
                db.commit() # Сохраняем изменения (удаление) в базе данных.
                print(f"DEBUG_HANDLER: Товар с артикулом {article} успешно удален из мониторинга.")
                await message.answer(f"Мониторинг для товара с артикулом {article} остановлен.")
            else: # Если товар не найден
                print(f"DEBUG_HANDLER: Товар с артикулом {article} не найден в списке мониторинга.")
                await message.answer(f"Товар с артикулом {article} не найден в списке мониторинга.")
        except Exception as e: # Если произошла ошибка
            db.rollback() # Отменяем изменения.
            print(f"ERROR_HANDLER: Произошла ошибка при удалении товара: {e}")
            await message.answer(f"Произошла ошибка при удалении товара: {e}")