from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    article = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    last_checked = Column(DateTime, default=datetime.utcnow)

    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(id={self.id}, article='{self.article}', name='{self.name}')>"

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    external_id = Column(String, unique=True, nullable=False)
    rating = Column(Integer, nullable=False)
    text = Column(String)
    author = Column(String)
    review_date = Column(DateTime)
    is_notified = Column(Boolean, default=False)

    product = relationship("Product", back_populates="reviews")

    def __repr__(self):
        return f"<Review(id={self.id}, product_id={self.product_id}, rating={self.rating}, text='{self.text[:50]}...')>"