import hashlib
import hmac
import os
from pathlib import Path
from urllib.parse import parse_qs

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent

# Пытаемся взять токен из env процесса.
# Если его нет (например, пользователь положил TELEGRAM_BOT_TOKEN только в bot/.env) —
# подгружаем bot/.env как fallback.
load_dotenv(_ROOT / "bot" / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def validate_telegram_data(init_data: str) -> bool:
    """
    Полная проверка подписи Telegram WebApp initData.
    См. https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
    if not BOT_TOKEN or not init_data:
        return False

    parsed_data = parse_qs(init_data)

    hash_ = parsed_data.get("hash", [None])[0]
    if not hash_:
        return False

    data_check_string = "\n".join(
        f"{key}={value[0]}"
        for key, value in sorted(parsed_data.items())
        if key != "hash"
    )

    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()

    hmac_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(hmac_hash, hash_)

