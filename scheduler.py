import asyncio
from datetime import datetime
from aiogram import Bot
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Product, Review
from database import SessionLocal
from wildberries_api import get_product_reviews

CHECK_INTERVAL_SECONDS = 30 * 60


async def check_for_new_reviews(bot: Bot):
    while True:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Начинаем проверку новых отзывов...")
        db: Session = SessionLocal()
        try:
            products = db.execute(select(Product)).scalars().all()

            if not products:
                print("Нет товаров для мониторинга в базе данных.")

            for product in products:
                print(f"Проверяем товар: '{product.name}' (артикул: {product.article})")
                reviews = await get_product_reviews(product.article, days_ago=3)

                if not reviews:
                    print(f"Для товара {product.article} новых негативных отзывов за последние 3 дня не найдено.")

                for review_data in reviews:
                    existing_review = db.execute(
                        select(Review).filter_by(external_id=review_data['external_id'])
                    ).scalar_one_or_none()

                    if not existing_review:
                        new_review = Review(
                            product_id=product.id,
                            external_id=review_data['external_id'],
                            rating=review_data['rating'],
                            text=review_data['text'],
                            author=review_data['author'],
                            review_date=review_data['review_date'],
                            is_notified=False
                        )
                        db.add(new_review)
                        db.commit()
                        db.refresh(new_review)

                        notification_text = (
                            f"🔴 Новый негативный отзыв!\n"
                            f"Товар: {product.name}\n"
                            f"Оценка: {'⭐' * new_review.rating} ({new_review.rating}/5)\n"
                            f"Отзыв: \"{new_review.text}\"\n"
                            f"Автор: {new_review.author}\n"
                            f"Дата отзыва: {new_review.review_date.strftime('%d.%m.%Y %H:%M')}"
                        )

                        print(f"--- [УВЕДОМЛЕНИЕ] Новый негативный отзыв для '{product.name}' ---")
                        print(notification_text)
                        new_review.is_notified = True
                        db.commit()
                        print(
                            f"Новый негативный отзыв для {product.name} успешно обработан и отмечен как уведомленный.")
                    else:
                        print(
                            f"DEBUG_SCHEDULER: Отзыв {review_data['external_id']} для {product.name} уже существует в БД.")
        except Exception as e:
            print(f"ERROR_SCHEDULER: Произошла ошибка в планировщике проверки отзывов: {e}")
            db.rollback()
        finally:
            db.close()

        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Завершили проверку. Ожидаем {CHECK_INTERVAL_SECONDS / 60} минут до следующей проверки...")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)