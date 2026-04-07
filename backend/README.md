# BukharaGo — Django API + Telegram Bot

Backend на Django REST Framework и асинхронный бот на `python-telegram-bot` v20+.

## Архитектура (разделение)

```text
bukhara-backend/
├── config/
├── api/
│   ├── views.py
│   └── services/
│       └── auth_service.py
├── users/
├── .env.example
└── manage.py

bukhara-bot/
├── bot.py
└── .env.example
```

В репозитории это реализовано каталогами `config/`, `api/`, `users/`, `bot/`.

## Установка

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Переменные окружения через `.env`:

- `./.env` (см. `./.env.example`): `DJANGO_SECRET_KEY`, `DEBUG`
- `./bot/.env` (см. `./bot/.env.example`): `TELEGRAM_BOT_TOKEN`, `WEBAPP_URL`

## Запуск

1. Применить миграции и поднять сервер API:

```bash
python manage.py migrate
python manage.py runserver
```

2. В другом терминале — бот (из каталога `backend`):

```bash
cd bot
cp .env.example .env   # заполните TELEGRAM_BOT_TOKEN и WEBAPP_URL
cd ..
python bot/bot.py
```

## API

- `POST /api/auth/` — тело JSON:

```json
{
  "init_data": "<tg.initData>",
  "user": {
    "id": 123456789,
    "first_name": "Имя",
    "last_name": "Фамилия",
    "username": "nickname"
  }
}
```

Ответ: `{"status": "ok", "user_id": 1, "is_active": true}`.

Проверка подписи `initData` — реализована в `api/telegram_auth.py` (`validate_telegram_data`).
Бизнес-логика авторизации вынесена в `api/services/auth_service.py`.

## Фронт

- React: `examples/WebAppAuthExample.jsx`
- Без сборщика: `examples/webapp_static_example.html`

Подключите `https://telegram.org/js/telegram-web-app.js`, используйте `window.Telegram.WebApp.initDataUnsafe.user` и отправляйте POST на ваш `API_BASE`.

## Админка

```bash
python manage.py createsuperuser
```

Откройте `http://127.0.0.1:8000/admin/`.
