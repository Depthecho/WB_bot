from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from config import DATABASE_URL

# Создаем "движок" для подключения к базе данных.
engine = create_engine(DATABASE_URL, echo=False)

# Создаем класс для создания "сессий".
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Функция для создания всех таблиц в базе данных.
def init_db():
    print("Attempting to initialize database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")

from contextlib import asynccontextmanager

# Это специальная функция для получения сессии базы данных.
@asynccontextmanager
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()