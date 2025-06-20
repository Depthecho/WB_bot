WB-Review-Monitor-Bot — это Telegram-бот, предназначенный для отслеживания новых негативных отзывов на товары Wildberries. Пользователи могут добавить артикул интересующего товара, и бот будет периодически проверять наличие новых отзывов. В случае обнаружения негативных отзывов (с низким рейтингом), бот отправит уведомление в Telegram с деталями отзыва и ссылкой на него.

Проект разработан с использованием Python и асинхронных фреймворков `aiogram` (для Telegram-бота) и `aiohttp` (для HTTP-запросов к API Wildberries), а также `SQLAlchemy` для работы с базой данных SQLite.

## Функционал:
* Добавление товара для мониторинга по артикулу.
* Получение уведомлений о новых негативных отзывах (рейтинг 1 или 2 звезды, настраивается).
* **Остановка мониторинга для конкретного товара.**
* Периодическая автоматическая проверка отзывов (интервал настраивается).

## Требования:
* Python 3.10 или выше