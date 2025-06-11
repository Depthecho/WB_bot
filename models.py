from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base() # Это основа для всех наших таблиц.

# Модель для таблицы "products" (товаров).
# Здесь мы храним информацию о каждом товаре, который отслеживаем.
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    article = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    last_checked = Column(DateTime, default=datetime.utcnow)

    # Связь с отзывами: один товар может иметь много отзывов.
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")

    # Как показывать объект Product, если его вывести в консоль.
    def __repr__(self):
        return f"<Product(id={self.id}, article='{self.article}', name='{self.name}')>"

# Модель для таблицы "reviews" (отзывов).
# Здесь мы храним каждый отзыв, который нашли.
class Review(Base):
    __tablename__ = "reviews" # Имя таблицы в базе данных.

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    external_id = Column(String, unique=True, nullable=False)
    rating = Column(Integer, nullable=False)
    text = Column(String)
    author = Column(String)
    review_date = Column(DateTime)
    is_notified = Column(Boolean, default=False)

    # Связь с товаром: каждый отзыв относится к одному товару.
    product = relationship("Product", back_populates="reviews")

    # Как показывать объект Review, если его вывести в консоль.
    def __repr__(self):
        return f"<Review(id={self.id}, product_id={self.product_id}, rating={self.rating}, text='{self.text[:50]}...')>"