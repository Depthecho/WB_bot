import aiohttp
import logging
import json
from datetime import datetime, timezone

# Настраиваем, как будут выводиться сообщения из этого файла.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Адрес API Wildberries для получения информации о товаре.
# К этому адресу мы будем добавлять артикул товара.
WB_API_URL = "https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1965487&spp=30&hide_dtype=13&ab_testing=false&lang=ru&nm="

# Адрес API Wildberries для получения отзывов.
# К этому адресу тоже будем добавлять артикул.
WB_REVIEWS_API_URL_BASE = "https://feedbacks2.wb.ru/feedbacks/v2/"


# Функция для получения названия товара и его артикула с Wildberries.
async def get_product_info(article: str):
    full_url = f"{WB_API_URL}{article}" # Собираем полный адрес для запроса.
    logger.info(f"Запрос информации о продукте: {full_url}")

    async with aiohttp.ClientSession() as session: # Открываем интернет-сессию.
        try:
            async with session.get(full_url) as response: # Отправляем запрос.
                response.raise_for_status() # Проверяем, нет ли ошибок в ответе (например, 404).
                response_json = await response.json() # Получаем ответ в виде JSON.
                logger.debug(
                    f"Получен ответ API для артикула {article}: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
        except aiohttp.ClientError as e: # Если произошла ошибка сети.
            logger.error(f"HTTP ошибка при запросе WB API для артикула {article}: {e}")
            return None
        except Exception as e: # Если произошла другая, неизвестная ошибка.
            logger.error(f"Неизвестная ошибка при запросе WB API для артикула {article}: {e}")
            return None

    try:
        # Пытаемся найти название и артикул в полученном ответе.
        if response_json and 'data' in response_json and 'products' in response_json['data'] and response_json['data'][
            'products']:
            product_data = response_json['data']['products'][0] # Берем первый найденный товар.
            logger.debug(f"Получены данные продукта: {product_data}")

            product_name = product_data.get("name") # Получаем название.
            product_id = product_data.get("id") # Получаем артикул (ID).

            if product_name and product_id: # Если название и артикул найдены.
                logger.info(f"Найден продукт: '{product_name}' (ID: {product_id})")
                return { # Возвращаем их.
                    "article": str(product_id),
                    "name": product_name,
                }
            else: # Если название или артикул не найдены в ответе.
                logger.debug(
                    f"Отсутствуют 'name' или 'id' в данных продукта для артикула {article}. Product data: {product_data}")
                logger.info(f"Не удалось получить информацию о товаре {article} от Wildberries API.")
                return None
        else: # Если товар не найден в ответе Wildberries.
            logger.debug(
                f"Продукт с артикулом {article} не найден в ответе API (пустая data.products или нет таких ключей).")
            logger.info(f"Не удалось получить информацию о товаре {article} от Wildberries API.")
            return None
    except Exception as e: # Если произошла ошибка при разборе ответа.
        logger.error(f"Ошибка при парсинге JSON ответа для артикула {article}: {e}")
        logger.debug(
            f"Полный ответ API, вызвавший ошибку парсинга: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
        return None


# Функция для получения отзывов о товаре с Wildberries.
async def get_product_reviews(article: str, last_checked: datetime = None):
    full_url = f"{WB_REVIEWS_API_URL_BASE}{article}" # Собираем полный адрес для запроса.
    logger.info(f"Запрос отзывов для артикула: {article} по URL: {full_url}")

    reviews_list = [] # Список для хранения найденных отзывов.

    async with aiohttp.ClientSession() as session: # Открываем интернет-сессию.
        try:
            async with session.get(full_url) as response: # Отправляем запрос.
                response.raise_for_status() # Проверяем, нет ли ошибок.
                reviews_json = await response.json() # Получаем ответ в виде JSON.
                logger.debug(
                    f"Получен JSON отзывов для артикула {article}: {json.dumps(reviews_json, indent=2, ensure_ascii=False)}")

                if reviews_json and 'feedbacks' in reviews_json: # Если отзывы найдены.
                    for review_data in reviews_json['feedbacks']: # Проходим по каждому отзыву.
                        review_date_str = review_data.get('createdDate') # Получаем дату отзыва.

                        review_date = datetime.min.replace(tzinfo=timezone.utc) # Дата по умолчанию.
                        if review_date_str:
                            try:
                                # Преобразуем текст даты в правильный формат.
                                review_date = datetime.fromisoformat(review_date_str).replace(tzinfo=timezone.utc)
                            except ValueError: # Если формат даты непонятен.
                                logger.warning(
                                    f"Неизвестный формат даты отзыва '{review_date_str}' для артикула {article}. Используем datetime.min.")
                                review_date = datetime.min.replace(tzinfo=timezone.utc)

                        # Проверяем, не является ли отзыв старым (если указана дата последней проверки).
                        if last_checked and review_date <= last_checked.replace(tzinfo=timezone.utc):
                            logger.debug(
                                f"Отзыв {review_data.get('id')} от {review_date} старее {last_checked.replace(tzinfo=timezone.utc)}, пропускаем.")
                            continue # Пропускаем старый отзыв.

                        review_text = review_data.get('text') # Получаем текст отзыва.
                        if not review_text: # Если текста нет, пытаемся собрать его из "плюсов" и "минусов".
                            pros = review_data.get('pros')
                            cons = review_data.get('cons')
                            if pros or cons:
                                review_text = f"Достоинства: {pros}" if pros else ""
                                if cons:
                                    review_text += f"\nНедостатки: {cons}" if pros else f"Недостатки: {cons}"
                            else:
                                review_text = "" # Если текста все равно нет.

                        if review_text or review_data.get('productValuation') is not None: # Если есть текст или оценка.
                            reviews_list.append({ # Добавляем отзыв в список.
                                "external_id": review_data.get('id'),
                                "rating": review_data.get('productValuation'),
                                "text": review_text,
                                "author": review_data.get('wbUserDetails', {}).get('name') or "Аноним",
                                "review_date": review_date,
                            })

                else: # Если отзывы не найдены или ответ пустой.
                    logger.debug(
                        f"Отзывы для артикула {article} не найдены в ответе API или структура JSON изменилась.")
                    logger.debug(f"Полный ответ API отзывов: {json.dumps(reviews_json, indent=2, ensure_ascii=False)}")

        except aiohttp.ClientError as e: # Если ошибка сети.
            logger.error(f"HTTP ошибка при запросе WB Reviews API для артикула {article}: {e}")
        except Exception as e: # Если другая ошибка.
            logger.error(f"Неизвестная ошибка при запросе WB Reviews API для артикула {article}: {e}")

    logger.info(f"Найдено {len(reviews_list)} новых/обновленных отзывов для артикула {article}.")
    return reviews_list