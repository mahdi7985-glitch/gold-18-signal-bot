import os
import requests
from typing import Dict

# ---------------------------------------------------------------------------
# تلگرام
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def validate_telegram_config() -> None:
    """بررسی می‌کند که توکن و چت‌آیدی تلگرام تنظیم شده باشند."""
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    if missing:
        raise RuntimeError(
            "متغیرهای محیطی تلگرام تنظیم نشده‌اند: " + ", ".join(missing)
        )

def send_telegram_message(text: str) -> bool:
    """ارسال پیام به تلگرام. در صورت موفقیت True برمی‌گرداند."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ تلگرام تنظیم نشده، پیام ارسال نشد.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}

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

# ---------------------------------------------------------------------------
# بله
# ---------------------------------------------------------------------------
BALE_BOT_TOKEN = os.getenv("BALE_BOT_TOKEN", "")
BALE_CHAT_ID = os.getenv("BALE_CHAT_ID", "")

def validate_bale_config() -> None:
    """بررسی می‌کند که توکن و چت‌آیدی بله تنظیم شده باشند."""
    missing = []
    if not BALE_BOT_TOKEN:
        missing.append("BALE_BOT_TOKEN")
    if not BALE_CHAT_ID:
        missing.append("BALE_CHAT_ID")
    if missing:
        raise RuntimeError(
            "متغیرهای محیطی بله تنظیم نشده‌اند: " + ", ".join(missing)
        )

def send_bale_message(text: str) -> bool:
    """ارسال پیام به بله. در صورت موفقیت True برمی‌گرداند."""
    if not BALE_BOT_TOKEN or not BALE_CHAT_ID:
        print("⚠️ بله تنظیم نشده، پیام ارسال نشد.")
        return False

    url = f"https://api.bale.ai/v1/bot{BALE_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": BALE_CHAT_ID, "text": text, "parse_mode": "HTML"}

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

# ---------------------------------------------------------------------------
# ارسال همزمان به هر دو
# ---------------------------------------------------------------------------
def send_to_both(text: str, require_both: bool = False) -> Dict[str, bool]:
    """
    ارسال پیام به هر دو سرویس تلگرام و بله.

    Args:
        text: متن پیام
        require_both: اگر True باشد، هر دو باید موفق شوند وگرنه Exception می‌دهد

    Returns:
        دیکشنری شامل نتیجه هر سرویس
    """
    results = {
        "telegram": send_telegram_message(text),
        "bale": send_bale_message(text)
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

# ---------------------------------------------------------------------------
# تابع اعتبارسنجی جامع (اختیاری)
# ---------------------------------------------------------------------------
def validate_all_configs(raise_on_missing: bool = False) -> Dict[str, bool]:
    """
    اعتبارسنجی همه تنظیمات.

    Args:
        raise_on_missing: اگر True باشد، در صورت Missing Exception می‌دهد

    Returns:
        دیکشنری شامل وضعیت هر سرویس
    """
    results = {
        "telegram": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID),
        "bale": bool(BALE_BOT_TOKEN and BALE_CHAT_ID)
    }

    if raise_on_missing and not all(results.values()):
        missing = [k for k, v in results.items() if not v]
        raise RuntimeError(f"سرویس‌های زیر تنظیم نشده‌اند: {', '.join(missing)}")

    return results

# ---------------------------------------------------------------------------
# تنظیمات دیگر (مربوط به پروژه شما)
# ---------------------------------------------------------------------------
USE_MOCK_PRICE = os.getenv("USE_MOCK_PRICE", "false").lower() == "true"
GOLD_18K_URL = os.getenv("GOLD_18K_URL", "https://www.tgju.org/profile/geram18")

DATA_DIR = os.getenv("DATA_DIR", "data")
HISTORY_FILE = os.path.join(DATA_DIR, "price_history.csv")

RESAMPLE_RULE = os.getenv("RESAMPLE_RULE", "15min")
MIN_CANDLES_REQUIRED = int(os.getenv("MIN_CANDLES_REQUIRED", "35"))

SMA_PERIOD = int(os.getenv("SMA_PERIOD", "20"))
EMA_PERIOD = int(os.getenv("EMA_PERIOD", "20"))
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
MACD_FAST = int(os.getenv("MACD_FAST", "12"))
MACD_SLOW = int(os.getenv("MACD_SLOW", "26"))
MACD_SIGNAL = int(os.getenv("MACD_SIGNAL", "9"))
BBANDS_PERIOD = int(os.getenv("BBANDS_PERIOD", "20"))
BBANDS_STD = float(os.getenv("BBANDS_STD", "2"))
ADX_PERIOD = int(os.getenv("ADX_PERIOD", "14"))
ATR_PERIOD = int(os.getenv("ATR_PERIOD", "14"))
