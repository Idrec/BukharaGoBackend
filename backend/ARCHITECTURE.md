# Архитектура проекта

## Общее назначение

Проект представляет собой Django backend для Telegram WebApp и отдельный Telegram-бот, который открывает это WebApp пользователю.

Основной сценарий:

1. Пользователь открывает Telegram-бота.
2. Бот отправляет кнопку с `WebApp`.
3. Frontend получает `initData` и данные пользователя из Telegram.
4. Frontend отправляет `POST /api/auth/` на Django API.
5. Backend проверяет подпись Telegram, валидирует payload и создает или обновляет пользователя в базе.

## Высокоуровневая схема

```text
+-------------------+
| Telegram User     |
+---------+---------+
          |
          v
+-------------------+
| Telegram Bot      |
| bot/bot.py        |
+---------+---------+
          |
          | open WebApp
          v
+-------------------+
| Telegram WebApp   |
| frontend client   |
+---------+---------+
          |
          | POST /api/auth/
          | init_data + user
          v
+-------------------+
| Django API        |
| api/views.py      |
+---------+---------+
          |
          | validate payload
          v
+-------------------+
| Serializer Layer  |
| api/serializers.py|
+---------+---------+
          |
          | verify initData
          v
+-------------------+
| Telegram Auth     |
| api/telegram_auth |
+---------+---------+
          |
          | create/update user
          v
+-------------------+
| Service Layer     |
| api/services/*    |
+---------+---------+
          |
          v
+-------------------+
| User Model        |
| users/models.py   |
+---------+---------+
          |
          v
+-------------------+
| SQLite / DB       |
| db.sqlite3        |
+-------------------+
```

## Слои системы

### 1. Точка входа и конфигурация

- `manage.py`:
  стандартная точка входа Django-команд.
- `config/settings.py`:
  настройки приложения, подключение `.env`, DRF, CORS, база данных.
- `config/urls.py`:
  корневые маршруты, подключает `admin/` и `api/`.
- `config/asgi.py`, `config/wsgi.py`:
  серверные entry points для деплоя.

### 2. API слой

- `api/urls.py`:
  маршруты API.
- `api/views.py`:
  HTTP-обработчики DRF.
  Сейчас основной endpoint: `POST /api/auth/`.
- `api/serializers.py`:
  валидация входных данных пользователя из Telegram WebApp.

Роль слоя:

- принять HTTP-запрос;
- проверить обязательные поля;
- вернуть корректный HTTP-ответ;
- передать бизнес-логику в сервисный слой.

### 3. Слой интеграции с Telegram

- `api/telegram_auth.py`:
  проверяет подпись `init_data`, полученную от Telegram WebApp.

Роль слоя:

- гарантировать, что запрос действительно пришел из Telegram;
- не допустить подмены пользователя на клиенте.

### 4. Сервисный слой

- `api/services/auth_service.py`:
  содержит бизнес-логику авторизации и синхронизации пользователя.

Сейчас сервис делает:

- поиск пользователя по `telegram_id`;
- создание нового пользователя, если его нет;
- обновление `username`, `first_name`, `last_name`, если пользователь уже существует.

### 5. Доменный слой

- `users/models.py`:
  модель `TelegramUser`.
- `users/admin.py`:
  регистрация модели в Django admin.

Модель хранит:

- `telegram_id`
- `username`
- `first_name`
- `last_name`
- `is_active`
- `created_at`

### 6. Telegram-бот

- `bot/bot.py`:
  отдельный асинхронный бот на `python-telegram-bot`.

Роль бота:

- обработать `/start`;
- показать кнопку открытия WebApp;
- направить пользователя в frontend.

Бот не занимается сохранением пользователя напрямую.
Сохранение пользователя происходит через backend API после открытия WebApp.

## Структура каталогов

```text
backend/
|-- config/                 # настройки Django и корневые URL
|   |-- settings.py
|   |-- urls.py
|   |-- asgi.py
|   `-- wsgi.py
|
|-- api/                    # HTTP API и логика авторизации через Telegram
|   |-- urls.py
|   |-- views.py
|   |-- serializers.py
|   |-- telegram_auth.py
|   |-- services/
|   |   `-- auth_service.py
|   `-- migrations/
|
|-- users/                  # доменные модели пользователей
|   |-- models.py
|   |-- admin.py
|   `-- migrations/
|
|-- bot/                    # Telegram bot
|   `-- bot.py
|
|-- examples/               # примеры frontend-интеграции
|   |-- WebAppAuthExample.jsx
|   `-- webapp_static_example.html
|
|-- .env                    # backend env
|-- .env.example
|-- db.sqlite3
|-- manage.py
|-- requirements.txt
|-- README.md
`-- ARCHITECTURE.md
```

## Поток запроса авторизации

```text
Frontend/WebApp
    |
    | POST /api/auth/
    | { init_data, user }
    v
api/views.py::auth_telegram_user
    |
    |-- check init_data and user presence
    |-- validate_telegram_data(init_data)
    |-- TelegramWebAppUserSerializer(user_payload)
    v
api/services/auth_service.py::upsert_telegram_user
    |
    |-- TelegramUser.objects.get_or_create(...)
    |-- update fields if user exists
    v
users.models.TelegramUser
    |
    v
Database
```

## Архитектурные плюсы текущей структуры

- Логика разделена по ответственности: `views` не содержит всю бизнес-логику.
- Проверка подписи Telegram вынесена отдельно и не смешана с HTTP-слоем.
- Работа с моделью пользователя инкапсулирована в сервисе.
- Бот физически отделен от Django API, поэтому его проще развивать независимо.

## Что можно улучшить дальше

1. Добавить отдельный слой `repositories` или `selectors`, если логика работы с БД станет сложнее.
2. Вынести настройки бота и API в единый конфигурационный модуль.
3. Добавить тесты на:
   - `api/telegram_auth.py`
   - `api/services/auth_service.py`
   - `POST /api/auth/`
4. Разделить API на модули по use-case, если появятся новые endpoints.
5. Подготовить PostgreSQL-конфиг как основной вариант для production.

## Краткий вывод

Сейчас архитектура проекта выглядит как:

- `config` — инфраструктура Django;
- `api` — внешний REST API и orchestration;
- `api/services` — бизнес-логика;
- `users` — доменная модель пользователя;
- `bot` — отдельный входной канал через Telegram;
- `examples` — примеры клиента, который вызывает backend.

Это хорошая базовая layered architecture для небольшого Telegram WebApp backend.
