from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Product, Review
from config import DATABASE_URL
import asyncio

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    print("Attempting to initialize database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")

from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()