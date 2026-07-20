
import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_API_URL = "https://api.telegram.org/bot8890210647:AAE_64GUSExXMA7klRvAzQVqtWvlU0L5EXw/sendMessage"


class TelegramSendError(Exception):
    pass


def send_message(text: str, parse_mode: str = "HTML") -> None:
    """پیام را به chat_id تنظیم‌شده در تنظیمات ارسال می‌کند."""
    url = TELEGRAM_API_URL.format(token=8890210647:AAE_64GUSExXMA7klRvAzQVqtWvlU0L5EXw)
    payload = {
        "chat_id": 292739287,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, data=payload, timeout=15)
    except requests.RequestException as exc:
        raise TelegramSendError(f"خطا در اتصال به تلگرام: {exc}") from exc

    if not response.ok:
        raise TelegramSendError(
            f"تلگرام خطا برگرداند ({response.status_code}): {response.text}"
        )
