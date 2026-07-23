# ============================================
# config.py - تنظیمات اصلی تحلیل طلا
# مدل: بازه ۱ هفته تا ۱ ماه (تایم‌فریم ۴ ساعته)
# ============================================

import os

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

# ==================== تنظیمات تلگرام و بله ====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

BALE_BOT_TOKEN = os.getenv("BALE_BOT_TOKEN", "")
BALE_CHAT_ID = os.getenv("BALE_CHAT_ID", "")

# ==================== تنظیمات ذخیره‌سازی ====================
DATA_DIR = os.getenv("DATA_DIR", "data")
HISTORY_FILE = os.path.join(DATA_DIR, "price_history.csv")
RESULTS_FILE = os.getenv("RESULTS_FILE", "results/signals.json")  # ذخیره سیگنال‌ها
SAVE_RESULTS = True  # نتایج در فایل ذخیره شود؟

# ==================== تنظیمات دریافت قیمت ====================
USE_MOCK_PRICE = os.getenv("USE_MOCK_PRICE", "false").lower() == "true"
GOLD_18K_URL = os.getenv("GOLD_18K_URL", "https://www.tgju.org/profile/geram18")

# ==================== تنظیمات لاگ ====================
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_FILE = os.getenv("LOG_FILE", "logs/bot.log")
