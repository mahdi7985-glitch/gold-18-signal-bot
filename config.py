
import os

# ---------------------------------------------------------------------------
# تلگرام
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------------------------------------------------------------------------
# منبع قیمت
# ---------------------------------------------------------------------------
USE_MOCK_PRICE = os.getenv("USE_MOCK_PRICE", "false").lower() == "true"
GOLD_18K_URL = os.getenv("GOLD_18K_URL", "https://www.tgju.org/profile/geram18")

# ---------------------------------------------------------------------------
# ذخیره‌سازی تاریخچه قیمت
# ---------------------------------------------------------------------------
DATA_DIR = os.getenv("DATA_DIR", "data")
HISTORY_FILE = os.path.join(DATA_DIR, "price_history.csv")

# ---------------------------------------------------------------------------
# تحلیل تکنیکال
# ---------------------------------------------------------------------------
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


def validate_telegram_config() -> None:
    """بررسی می‌کند که توکن و چت‌آیدی تلگرام تنظیم شده باشند."""
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    if missing:
        raise RuntimeError(
            "متغیرهای محیطی زیر تنظیم نشده‌اند: " + ", ".join(missing)
        )
