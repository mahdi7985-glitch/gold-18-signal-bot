import requests

from config import BALE_BOT_TOKEN, BALE_CHAT_ID

BALE_API_URL = "https://tapi.bale.ai/bot{token}/sendMessage"


class BaleSendError(Exception):
    pass


def send_message(text: str) -> None:
    """پیام را به chat_id تنظیم‌شده در بله ارسال می‌کند."""
    url = BALE_API_URL.format(token=BALE_BOT_TOKEN)
    payload = {
        "chat_id": BALE_CHAT_ID,
        "text": text,
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
    except requests.RequestException as exc:
        raise BaleSendError(f"خطا در اتصال به بله: {exc}") from exc

    if not response.ok:
        raise BaleSendError(
            f"بله خطا برگرداند ({response.status_code}): {response.text}"
        )
