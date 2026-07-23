import os
import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramSendError(Exception):
    pass


def send_telegram_message(text: str, chat_id: str = None, parse_mode: str = "HTML") -> bool:
    """
    ارسال پیام به تلگرام
    
    Args:
        text: متن پیام
        chat_id: شناسه کاربر (اگر None نباشد، از تنظیمات استفاده می‌شود)
        parse_mode: حالت پارس (HTML یا Markdown)
    
    Returns:
        bool: موفقیت یا شکست
    """
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️ TELEGRAM_BOT_TOKEN تنظیم نشده")
        return False
    
    target_chat = chat_id or TELEGRAM_CHAT_ID
    if not target_chat:
        print("⚠️ چت‌آیدی تلگرام مشخص نشده")
        return False
    
    url = TELEGRAM_API_URL.format(token=TELEGRAM_BOT_TOKEN)
    payload = {
        "chat_id": target_chat,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, data=payload, timeout=15)
        if response.ok:
            print("✅ پیام به تلگرام ارسال شد")
            return True
        else:
            print(f"❌ خطا از سمت تلگرام: {response.text}")
            return False
    except requests.RequestException as exc:
        print(f"❌ خطا در اتصال به تلگرام: {exc}")
        return False


# برای سازگاری با کد قبلی
send_message = send_telegram_message
