import os
import requests
from typing import Dict, Optional
from datetime import datetime
import pytz

# ============================================
# تنظیمات منطقه زمانی ایران
# ============================================
IRAN_TZ = pytz.timezone("Asia/Tehran")

# ============================================
# تلگرام (عمومی - با قابلیت پاسخ به کاربر)
# ============================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")  # برای ارسال خودکار (اختیاری)

def validate_telegram_config() -> None:
    """بررسی می‌کند که توکن تلگرام تنظیم شده باشد."""
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN تنظیم نشده است")

def send_telegram_message(text: str, chat_id: Optional[str] = None) -> bool:
    """
    ارسال پیام به تلگرام.
    
    Args:
        text: متن پیام
        chat_id: اگر وارد نشود، به CHAT_ID پیش‌فرض ارسال می‌شود
    
    Returns:
        bool: موفقیت یا شکست
    """
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️ تلگرام تنظیم نشده، پیام ارسال نشد.")
        return False

    # اگر chat_id داده نشده، از مقدار پیش‌فرض استفاده کن
    target_chat = chat_id or TELEGRAM_CHAT_ID
    if not target_chat:
        print("⚠️ چت‌آیدی تلگرام مشخص نشده است.")
        return False

    # ✅ جلوگیری از لینک شدن قیمت‌ها با بک‌تیک
    # (اعداد با کاما را در بک‌تیک قرار می‌دهیم)
    formatted_text = _format_message(text)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": formatted_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True  # ✅ جلوگیری از لینک شدن
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.ok:
            print("✅ پیام به تلگرام ارسال شد.")
            return True
        else:
            print(f"❌ خطا از سمت تلگرام: {response.text}")
            return False
    except Exception as e:
        print(f"❌ خطا در ارسال پیام به تلگرام: {e}")
        return False

# ============================================
# بله (عمومی - با قابلیت پاسخ به کاربر)
# ============================================
BALE_BOT_TOKEN = os.getenv("BALE_BOT_TOKEN", "")
BALE_CHAT_ID = os.getenv("BALE_CHAT_ID", "")  # برای ارسال خودکار (اختیاری)

def validate_bale_config() -> None:
    """بررسی می‌کند که توکن بله تنظیم شده باشد."""
    if not BALE_BOT_TOKEN:
        raise RuntimeError("BALE_BOT_TOKEN تنظیم نشده است")

def send_bale_message(text: str, chat_id: Optional[str] = None) -> bool:
    """
    ارسال پیام به بله.
    
    Args:
        text: متن پیام
        chat_id: اگر وارد نشود، به CHAT_ID پیش‌فرض ارسال می‌شود
    
    Returns:
        bool: موفقیت یا شکست
    """
    if not BALE_BOT_TOKEN:
        print("⚠️ بله تنظیم نشده، پیام ارسال نشد.")
        return False

    target_chat = chat_id or BALE_CHAT_ID
    if not target_chat:
        print("⚠️ چت‌آیدی بله مشخص نشده است.")
        return False

    formatted_text = _format_message(text)

    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": formatted_text,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.ok:
            print("✅ پیام به بله ارسال شد.")
            return True
        else:
            print(f"❌ خطا از سمت بله: {response.text}")
            return False
    except Exception as e:
        print(f"❌ خطا در ارسال پیام به بله: {e}")
        return False

# ============================================
# تابع کمکی برای فرمت‌دهی پیام
# ============================================
def _format_message(text: str) -> str:
    """
    جلوگیری از لینک شدن اعداد و فرمت‌دهی بهتر.
    اعداد با کاما را در بک‌تیک قرار می‌دهد.
    """
    # اگر متن حاوی اعداد با کاما بود، آنها را در بک‌تیک بگذار
    # (این یک راه‌حل ساده است، برای دقت بیشتر از regex استفاده کن)
    import re
    # اعداد با کاما را پیدا کن (مثل ۴,۲۵۰,۰۰۰)
    pattern = r'(\d{1,3}(?:,\d{3})*)'
    formatted = re.sub(pattern, r'`\1`', text)
    return formatted

# ============================================
# ارسال همزمان به هر دو (با قابلیت پاسخ به کاربر)
# ============================================
def send_to_both(
    text: str,
    chat_id: Optional[str] = None,
    require_both: bool = False
) -> Dict[str, bool]:
    """
    ارسال پیام به هر دو سرویس تلگرام و بله.

    Args:
        text: متن پیام
        chat_id: شناسه کاربر (برای پاسخ به شخص خاص)
        require_both: اگر True باشد، هر دو باید موفق شوند

    Returns:
        دیکشنری شامل نتیجه هر سرویس
    """
    results = {
        "telegram": send_telegram_message(text, chat_id),
        "bale": send_bale_message(text, chat_id)
    }

    # چاپ خلاصه
    success_count = sum(results.values())
    if success_count == 2:
        print("✅ پیام به هر دو سرویس (تلگرام و بله) ارسال شد.")
    elif success_count == 1:
        print("⚠️ پیام فقط به یکی از سرویس‌ها ارسال شد.")
        failed = [k for k, v in results.items() if not v]
        print(f"   سرویس‌های ناموفق: {', '.join(failed)}")
    else:
        print("❌ پیام به هیچکدام از سرویس‌ها ارسال نشد.")

    if require_both and not all(results.values()):
        failed = [k for k, v in results.items() if not v]
        raise RuntimeError(f"ارسال به همه سرویس‌ها ناموفق بود: {', '.join(failed)}")
    
    return results

# ============================================
# دریافت پیام‌های کاربران (برای دستورات)
# ============================================
def get_telegram_updates(offset: int = 0) -> list:
    """
    دریافت پیام‌های جدید از تلگرام (برای پاسخ به دستورات).
    این تابع برای Webhook یا Polling استفاده می‌شود.
    """
    if not TELEGRAM_BOT_TOKEN:
        return []

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"offset": offset, "timeout": 30}

    try:
        response = requests.get(url, params=params, timeout=35)
        if response.ok:
            data = response.json()
            if data.get("ok"):
                return data.get("result", [])
        return []
    except Exception as e:
        print(f"❌ خطا در دریافت پیام‌های تلگرام: {e}")
        return []

def get_bale_updates(offset: int = 0) -> list:
    """
    دریافت پیام‌های جدید از بله (برای پاسخ به دستورات).
    """
    if not BALE_BOT_TOKEN:
        return []

    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/getUpdates"
    params = {"offset": offset, "timeout": 30}

    try:
        response = requests.get(url, params=params, timeout=35)
        if response.ok:
            data = response.json()
            if data.get("ok"):
                return data.get("result", [])
        return []
    except Exception as e:
        print(f"❌ خطا در دریافت پیام‌های بله: {e}")
        return []

# ============================================
# تابع اعتبارسنجی جامع
# ============================================
def validate_all_configs(raise_on_missing: bool = False) -> Dict[str, bool]:
    """
    اعتبارسنجی همه تنظیمات.

    Args:
        raise_on_missing: اگر True باشد، در صورت Missing Exception می‌دهد

    Returns:
        دیکشنری شامل وضعیت هر سرویس
    """
    results = {
        "telegram": bool(TELEGRAM_BOT_TOKEN),
        "bale": bool(BALE_BOT_TOKEN)
    }

    if raise_on_missing and not all(results.values()):
        missing = [k for k, v in results.items() if not v]
        raise RuntimeError(f"سرویس‌های زیر تنظیم نشده‌اند: {', '.join(missing)}")

    return results

# ============================================
# تابع دریافت زمان ایران
# ============================================
def get_iran_time() -> str:
    """برگرداندن زمان فعلی به‌صورت رشته با منطقه زمانی ایران"""
    now = datetime.now(IRAN_TZ)
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_iran_day() -> str:
    """برگرداندن نام روز هفته به فارسی"""
    days = {
        0: "دوشنبه",
        1: "سه‌شنبه",
        2: "چهارشنبه",
        3: "پنج‌شنبه",
        4: "جمعه",
        5: "شنبه",
        6: "یک‌شنبه"
    }
    now = datetime.now(IRAN_TZ)
    return days[now.weekday()]

# ============================================
# تنظیمات دیگر (مربوط به پروژه شما)
# ============================================
USE_MOCK_PRICE = os.getenv("USE_MOCK_PRICE", "false").lower() == "true"
GOLD_18K_URL = os.getenv("GOLD_18K_URL", "https://www.tgju.org/profile/geram18")

DATA_DIR = os.getenv("DATA_DIR", "data")
HISTORY_FILE = os.path.join(DATA_DIR, "price_history.csv")

# تنظیمات جدید (مدل بهینه)
RESAMPLE_RULE = os.getenv("RESAMPLE_RULE", "4h")  # تغییر به ۴ ساعته
MIN_CANDLES_REQUIRED = int(os.getenv("MIN_CANDLES_REQUIRED", "60"))

# Lengthهای جدید
EMA_FAST = int(os.getenv("EMA_FAST", "20"))
EMA_SLOW = int(os.getenv("EMA_SLOW", "50"))
RSI_LENGTH = int(os.getenv("RSI_LENGTH", "10"))
MACD_FAST = int(os.getenv("MACD_FAST", "10"))
MACD_SLOW = int(os.getenv("MACD_SLOW", "22"))
MACD_SIGNAL = int(os.getenv("MACD_SIGNAL", "8"))
ADX_LENGTH = int(os.getenv("ADX_LENGTH", "14"))
ADX_THRESHOLD = int(os.getenv("ADX_THRESHOLD", "25"))

# محدوده‌های RSI
RSI_OVERBOUGHT = int(os.getenv("RSI_OVERBOUGHT", "70"))
RSI_OVERSOLD = int(os.getenv("RSI_OVERSOLD", "30"))

# تنظیمات واگرایی
DIVERGENCE_MIN_BARS = int(os.getenv("DIVERGENCE_MIN_BARS", "5"))
DIVERGENCE_LOOKBACK = int(os.getenv("DIVERGENCE_LOOKBACK", "20"))
