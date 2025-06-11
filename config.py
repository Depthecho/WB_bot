import os
from dotenv import load_dotenv
import pathlib

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

DATABASE_URL = "sqlite:///./wildberries_reviews.db"

print(f"DEBUG: DATABASE_URL из config.py: {DATABASE_URL}")
try:
    db_path = pathlib.Path(DATABASE_URL.replace("sqlite:///", "")).resolve()
    print(f"DEBUG: Полный путь к файлу БД, который будет использоваться: {db_path}")
except Exception as e:
    print(f"DEBUG: Не удалось определить полный путь к файлу БД: {e}")