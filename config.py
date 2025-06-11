import os
from dotenv import load_dotenv
import pathlib

# Загружаем данные из файла .env.
load_dotenv()

# Получаем токен нашего Telegram-бота.
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Адрес нашей базы данных.
DATABASE_URL = "sqlite:///./wildberries_reviews.db"

# Отладочная информация
print(f"DEBUG: DATABASE_URL из config.py: {DATABASE_URL}")
try:
    db_path = pathlib.Path(DATABASE_URL.replace("sqlite:///", "")).resolve()
    print(f"DEBUG: Полный путь к файлу БД, который будет использоваться: {db_path}")
except Exception as e:
    # Если что-то пошло не так при определении пути, выводим ошибку.
    print(f"DEBUG: Не удалось определить полный путь к файлу БД: {e}")