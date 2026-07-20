import os
import requests

BALE_API_URL = "https://api.bale.ai/v1/bots/{token}/sendMessage"
BALE_BOT_TOKEN = os.getenv("BALE_BOT_TOKEN")
BALE_CHAT_ID = os.getenv("BALE_CHAT_ID")

class BaleSendError(Exception):
    pass

def send_message(text: str, parse_mode: str = "HTML") -> None:
    """پیام را به chat_id تنظیم‌شده در تنظیمات ارسال می‌کند."""
    url = BALE_API_URL.format(token=BALE_BOT_TOKEN)
    payload = {
        "chat_id": BALE_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise BaleSendError(f"خطا در ارسال پیام به Bale: {e}")
