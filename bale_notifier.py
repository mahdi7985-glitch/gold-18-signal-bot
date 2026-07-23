import os
import requests

from config import BALE_BOT_TOKEN, BALE_CHAT_ID

BALE_API_URL = "https://tapi.bale.ai/bot{token}/sendMessage"


class BaleSendError(Exception):
    pass


def send_bale_message(text: str, chat_id: str = None, parse_mode: str = "HTML") -> bool:
    """
    ارسال پیام به بله
    
    Args:
        text: متن پیام
        chat_id: شناسه کاربر (اگر None نباشد، از تنظیمات استفاده می‌شود)
        parse_mode: حالت پارس (HTML یا Markdown)
    
    Returns:
        bool: موفقیت یا شکست
    """
    if not BALE_BOT_TOKEN:
        print("⚠️ BALE_BOT_TOKEN تنظیم نشده")
        return False
    
    target_chat = chat_id or BALE_CHAT_ID
    if not target_chat:
        print("⚠️ چت‌آیدی بله مشخص نشده")
        return False
    
    url = BALE_API_URL.format(token=BALE_BOT_TOKEN)
    payload = {
        "chat_id": target_chat,
        "text": text,
        "parse_mode": parse_mode,
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.ok:
            print("✅ پیام به بله ارسال شد")
            return True
        else:
            print(f"❌ خطا از سمت بله: {response.text}")
            return False
    except requests.RequestException as exc:
        print(f"❌ خطا در اتصال به بله: {exc}")
        return False


# برای سازگاری با کد قبلی
send_message = send_bale_message
