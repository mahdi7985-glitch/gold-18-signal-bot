# ============================================
# config.py - تنظیمات اصلی تحلیل طلا
# مدل: بازه ۱ هفته تا ۱ ماه (تایم‌فریم ۴ ساعته)
# ============================================

import os
import pandas as pd

# ==================== تنظیمات زمانی ====================
RESAMPLE_RULE = "4h"  # تایم‌فریم کندل‌ها (۴ ساعته)
MIN_CANDLES_REQUIRED = 60  # حداقل کندل موردنیاز برای محاسبه اندیکاتورها

# ==================== تنظیمات اندیکاتورها (Length جدید) ====================

# EMA ها (روند اصلی)
EMA_FAST = 20   # EMA سریع برای تشخیص حرکت میان‌مدت
EMA_SLOW = 50   # EMA کند برای خط آتش (تعیین جهت اصلی)

# MACD با Length بهینه برای بازه ۱ ماهه
MACD_FAST = 10
MACD_SLOW = 22
MACD_SIGNAL = 8

# RSI با Length ۱۰ (جایگزین ۱۴ برای واکنش سریع‌تر)
RSI_LENGTH = 10

# ADX برای تشخیص قدرت روند
ADX_LENGTH = 14
ADX_THRESHOLD = 25  # بالای ۲۵ = روند قوی (مجاز به معامله)

# ==================== محدوده‌های RSI ====================
RSI_OVERBOUGHT = 70  # اشباع خرید
RSI_OVERSOLD = 30    # اشباع فروش

# ==================== تنظیمات واگرایی ====================
DIVERGENCE_MIN_BARS = 5  # حداقل فاصله بین دو قله/دره برای واگرایی
DIVERGENCE_LOOKBACK = 20  # تعداد کندل‌های برگشتی برای جستجوی واگرایی

# ==================== تنظیمات سطوح کلیدی ====================
SUPPORT_RESISTANCE_PERIOD = 20  # دوره محاسبه حمایت و مقاومت
SUPPORT_RESISTANCE_MULTIPLIER = 1.5  # ضریب انحراف معیار برای بولینگر

# ==================== تنظیمات سیگنال‌دهی ====================
SIGNAL_CONFIDENCE_THRESHOLD = 50  # حداقل اطمینان برای سیگنال معتبر
BUY_SCORE_THRESHOLD = 50  # امتیاز برای سیگنال خرید
SELL_SCORE_THRESHOLD = -50  # امتیاز برای سیگنال فروش

# ==================== تنظیمات پیام ====================
SHOW_LEVELS = True  # نمایش حمایت و مقاومت در پیام
SHOW_DOLLAR_OUNCE = True  # نمایش دلار و اونس
SHOW_HISTORY = True  # نمایش تاریخچه قیمت
SHOW_DAILY_CHANGE = True  # نمایش تغییرات روزانه
SHOW_FRIENDLY_MESSAGE = True  # نمایش پیام دوستانه

# ==================== تنظیمات تلگرام و بله ====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

BALE_BOT_TOKEN = os.getenv("BALE_BOT_TOKEN", "")
BALE_CHAT_ID = os.getenv("BALE_CHAT_ID", "")

# ==================== تنظیمات ذخیره‌سازی ====================
DATA_DIR = os.getenv("DATA_DIR", "data")
HISTORY_FILE = os.path.join(DATA_DIR, "price_history.csv")
RESULTS_FILE = os.path.join(DATA_DIR, "signals.csv")  # ذخیره سیگنال‌ها
SAVE_RESULTS = True  # نتایج در فایل ذخیره شود؟

# ==================== تنظیمات دریافت قیمت ====================
USE_MOCK_PRICE = os.getenv("USE_MOCK_PRICE", "false").lower() == "true"
GOLD_18K_URL = os.getenv("GOLD_18K_URL", "https://www.tgju.org/profile/geram18")

# ==================== تنظیمات لاگ ====================
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_FILE = os.getenv("LOG_FILE", "logs/bot.log")


# ==================== توابع کمکی ====================

def ensure_directories():
    """ایجاد دایرکتوری‌های مورد نیاز"""
    # ایجاد دایرکتوری data
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        print(f"✅ دایرکتوری {DATA_DIR} ایجاد شد")
    
    # ایجاد دایرکتوری logs
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        print(f"✅ دایرکتوری {log_dir} ایجاد شد")
    
    # اطمینان از وجود فایل history با هدرهای صحیح
    if not os.path.exists(HISTORY_FILE):
        try:
            import pandas as pd
            df = pd.DataFrame(columns=["timestamp", "price"])
            df.to_csv(HISTORY_FILE, index=False)
            print(f"✅ فایل {HISTORY_FILE} ایجاد شد")
        except Exception as e:
            print(f"⚠️ خطا در ایجاد فایل history: {e}")
    
    # اطمینان از وجود فایل signals
    if SAVE_RESULTS and not os.path.exists(RESULTS_FILE):
        try:
            import pandas as pd
            df = pd.DataFrame(columns=["timestamp", "price", "signal", "signal_text", "confidence", "trend"])
            df.to_csv(RESULTS_FILE, index=False)
            print(f"✅ فایل {RESULTS_FILE} ایجاد شد")
        except Exception as e:
            print(f"⚠️ خطا در ایجاد فایل signals: {e}")


def get_config_info() -> dict:
    """دریافت اطلاعات تنظیمات برای نمایش"""
    return {
        "تایم‌فریم": RESAMPLE_RULE,
        "حداقل کندل": MIN_CANDLES_REQUIRED,
        "EMA سریع": EMA_FAST,
        "EMA کند": EMA_SLOW,
        "RSI": RSI_LENGTH,
        "MACD": f"{MACD_FAST}, {MACD_SLOW}, {MACD_SIGNAL}",
        "ADX": ADX_LENGTH,
        "حد آستانه ADX": ADX_THRESHOLD,
        "اشباع خرید RSI": RSI_OVERBOUGHT,
        "اشباع فروش RSI": RSI_OVERSOLD,
        "حالت موک": USE_MOCK_PRICE,
        "سرویس‌ها": {
            "تلگرام": bool(TELEGRAM_BOT_TOKEN),
            "بله": bool(BALE_BOT_TOKEN),
        },
        "ذخیره‌سازی": SAVE_RESULTS,
        "دیباگ": DEBUG,
    }


def print_config():
    """چاپ تنظیمات برای دیباگ"""
    info = get_config_info()
    print("=" * 50)
    print("📊 تنظیمات ربات تحلیل طلا")
    print("=" * 50)
    for key, value in info.items():
        if isinstance(value, dict):
            print(f"\n{key}:")
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(f"{key}: {value}")
    print("=" * 50)


# ==================== اجرای خودکار در زمان import ====================
# اطمینان از وجود دایرکتوری‌ها
ensure_directories()


# ==================== تست ====================
if __name__ == "__main__":
    print_config()
    
    # تست متغیرها
    print("\n📁 مسیرهای فایل:")
    print(f"  DATA_DIR: {DATA_DIR}")
    print(f"  HISTORY_FILE: {HISTORY_FILE}")
    print(f"  RESULTS_FILE: {RESULTS_FILE}")
    print(f"  LOG_FILE: {LOG_FILE}")
