import asyncio
from datetime import datetime
from aiogram import Bot
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Product, Review
from database import SessionLocal
from wildberries_api import get_product_reviews

CHECK_INTERVAL_SECONDS = 30 * 60 # Интервал проверки: 30 минут

# Главная функция-планировщик для проверки отзывов.
async def check_for_new_reviews(bot: Bot):
    while True:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Начинаем проверку новых отзывов...")
        db: Session = SessionLocal()
        try:
            # Получаем список всех товаров, которые мы отслеживаем.
            products = db.execute(select(Product)).scalars().all()

            if not products: # Если товаров нет
                print("Нет товаров для мониторинга в базе данных.")

            for product in products: # Проходим по каждому товару
                print(f"Проверяем товар: '{product.name}' (артикул: {product.article})")
                # Получаем отзывы для этого товара за последние 3 дня.
                reviews = await get_product_reviews(product.article, days_ago=3)

                if not reviews: # Если нет новых отзывов
                    print(f"Для товара {product.article} новых негативных отзывов за последние 3 дня не найдено.")

                for review_data in reviews: # Проходим по каждому найденному отзыву
                    # Проверяем, есть ли такой отзыв уже в нашей базе данных.
                    existing_review = db.execute(
                        select(Review).filter_by(external_id=review_data['external_id'])
                    ).scalar_one_or_none()

                    if not existing_review: # Если отзыв новый
                        # Создаем новую запись об отзыве.
                        new_review = Review(
                            product_id=product.id,
                            external_id=review_data['external_id'],
                            rating=review_data['rating'],
                            text=review_data['text'],
                            author=review_data['author'],
                            review_date=review_data['review_date'],
                            is_notified=False # Помечаем, что уведомление еще не отправлено
                        )
                        db.add(new_review)
                        db.commit()
                        db.refresh(new_review)

                        # Формируем текст уведомления.
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
                        new_review.is_notified = True # Помечаем отзыв как уведомленный.
                        db.commit()
                        print(
                            f"Новый негативный отзыв для {product.name} успешно обработан и отмечен как уведомленный.")
                    else:
                        print(
                            f"DEBUG_SCHEDULER: Отзыв {review_data['external_id']} для {product.name} уже существует в БД.")
        except Exception as e: # Если произошла ошибка во время проверки
            print(f"ERROR_SCHEDULER: Произошла ошибка в планировщике проверки отзывов: {e}")
            db.rollback() # Отменяем все незавершенные изменения в базе данных.
        finally:
            db.close() # Всегда закрываем сессию базы данных.

        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Завершили проверку. Ожидаем {CHECK_INTERVAL_SECONDS / 60} минут до следующей проверки...")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)