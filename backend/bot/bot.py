"""
Асинхронный Telegram-бот BukharaGo: WebApp-кнопка и команда /start.
Запуск: python bot/bot.py (из корня проекта backend/)
"""

from __future__ import annotations

import logging
import os
import sys
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# Корень проекта в PYTHONPATH для единообразия при запуске из любой директории
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Загружаем переменные окружения из bot/.env (если есть)
load_dotenv(_ROOT / "bot" / ".env")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("bukharago.bot")

WEB_APP_URL = os.getenv("WEBAPP_URL", "https://bukharago.netlify.app/")
BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"


def _webapp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🚀 Открыть BukharaGo",
                    web_app=WebAppInfo(url=WEB_APP_URL),
                )
            ]
        ]
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat:
        return
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Добро пожаловать в BukharaGo! Нажмите кнопку ниже, чтобы открыть приложение.",
        reply_markup=_webapp_keyboard(),
    )


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(
        "Необработанное исключение в обработчике",
        exc_info=context.error,
    )


def main() -> None:
    token = os.environ.get(BOT_TOKEN_ENV)
    if not token:
        logger.error("Задайте переменную окружения %s", BOT_TOKEN_ENV)
        sys.exit(1)

    # Python 3.14+: event loop не создаётся автоматически для MainThread.
    # python-telegram-bot внутри run_polling ожидает, что loop уже существует.
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    application = (
        Application.builder()
        .token(token)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .build()
    )

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_error_handler(on_error)

    logger.info("Бот запущен (polling)")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Остановка по Ctrl+C")
    except Exception:
        logger.exception("Критическая ошибка при запуске бота")
        sys.exit(1)
