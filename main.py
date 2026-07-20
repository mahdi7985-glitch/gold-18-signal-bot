import sys
from datetime import datetime
from zoneinfo import ZoneInfo
import jdatetime

import config
from gold_price_fetcher import get_gold_18k_price, PriceFetchError
from storage import append_price, load_history, trim_history
from indicators import get_latest_indicators
from signal_analyzer import analyze
from config import send_to_both  # 👈 این رو اضافه کنید


PERSIAN_WEEKDAYS = {
    0: "دوشنبه",
    1: "سه‌شنبه",
    2: "چهارشنبه",
    3: "پنجشنبه",
    4: "جمعه",
    5: "شنبه",
    6: "یکشنبه",
}


def get_tehran_jalali_now() -> jdatetime.datetime:
    """زمان فعلی به وقت تهران، تبدیل‌شده به تاریخ شمسی."""
    now = datetime.now(ZoneInfo("Asia/Tehran"))
    return jdatetime.datetime.fromgregorian(datetime=now)


def format_jalali_datetime(jalali: jdatetime.datetime) -> str:
    """قالب‌بندی تاریخ/ساعت شمسی همراه با نام روز هفته فارسی (مستقل از لوکیل سیستم)."""
    weekday_name = PERSIAN_WEEKDAYS[jalali.weekday()]
    return f"{weekday_name} {jalali.strftime('%Y/%m/%d')} | 🕒 {jalali.strftime('%H:%M')}"


def format_full_report(price: float, row, signal) -> str:
    trend_emoji = {
        "صعودی قوی": "🟢🟢",
        "صعودی": "🟢",
        "خنثی": "🟡",
        "نزولی": "🔴",
        "نزولی قوی": "🔴🔴",
    }.get(signal.trend, "⚪️")

    reasons_text = "\n".join(f"• {r}" for r in signal.reasons)
    jalali = get_tehran_jalali_now()

    return (
        f"<b>📊 گزارش قیمت طلای ۱۸ عیار</b>\n"
        f"📅 {format_jalali_datetime(jalali)}\n\n"
        f"💰 قیمت لحظه‌ای: <b>{price:,.0f}</b> تومان\n\n"
        f"{trend_emoji} روند: <b>{signal.trend}</b>\n"
        f"⚡️ قدرت سیگنال: <b>{signal.strength}٪</b>\n\n"
        f"<b>اندیکاتورها:</b>\n"
        f"• SMA({config.SMA_PERIOD}): {row['sma']:,.0f}\n"
        f"• EMA({config.EMA_PERIOD}): {row['ema']:,.0f}\n"
        f"• RSI({config.RSI_PERIOD}): {row['rsi']:.1f}\n"
        f"• MACD: {row['macd']:.2f} | سیگنال: {row['macd_signal']:.2f}\n"
        f"• ADX({config.ADX_PERIOD}): {row['adx']:.1f}\n"
        f"• ATR({config.ATR_PERIOD}): {row['atr']:,.0f}\n"
        f"• باند بولینگر: {row['bb_lower']:,.0f} — {row['bb_upper']:,.0f}\n\n"
        f"<b>دلایل تحلیل:</b>\n{reasons_text}\n\n"
        f"<i>⚠️ این تحلیل صرفاً جنبه‌ی آموزشی/کمکی دارد و توصیه مالی نیست.</i>"
    )


def format_collecting_data_message(price: float, have: int, need: int) -> str:
    jalali = get_tehran_jalali_now()

    price_in_toman = price / 10

    return (
        f"<b>📊 قیمت طلای ۱۸ عیار</b>\n"
        f"📅 {format_jalali_datetime(jalali)}\n\n"
        f"💰 قیمت لحظه‌ای: <b>{price:,.0f}</b> تومان\n\n"
        f"⏳ در حال جمع‌آوری داده برای تحلیل تکنیکال ({have}/{need} کندل).\n"
        f"به‌محض کافی‌شدن داده، گزارش کامل با MACD/RSI/EMA/SMA/ADX/ATR/Bollinger ارسال می‌شود."
    )


def run() -> None:
    # اعتبارسنجی تنظیمات (اختیاری)
    # config.validate_all_configs(raise_on_missing=True)

    # ۱. دریافت قیمت
    try:
        price = get_gold_18k_price()
    except PriceFetchError as exc:
        print(f"[ERROR] دریافت قیمت ناموفق بود: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] قیمت دریافت‌شده: {price:,.0f} تومان")

    # ۲. ذخیره در تاریخچه
    append_price(price)
    trim_history()

    # ۳. تلاش برای محاسبه اندیکاتورها
    history = load_history()
    result = get_latest_indicators(history["price"])

    if result is None:
        from indicators import build_ohlc_candles
        candles_count = len(build_ohlc_candles(history["price"]))
        message = format_collecting_data_message(
            price, candles_count, config.MIN_CANDLES_REQUIRED
        )
    else:
        row, _ = result
        signal = analyze(row)
        message = format_full_report(price, row, signal)
        print(f"[INFO] روند: {signal.trend} | قدرت سیگنال: {signal.strength}٪")

    # ۴. ارسال به هر دو (تلگرام + بله) با یک تابع
    results = send_to_both(message, require_both=False)  # اگر یکی fail شد، دیگری کار کنه

    # اگر می‌خواهید حتماً هر دو موفق شوند:
    # results = send_to_both(message, require_both=True)

    # بررسی نتیجه
    if all(results.values()):
        print("[INFO] پیام با موفقیت به هر دو سرویس ارسال شد.")

    else:
        failed = [k for k, v in results.items() if not v]
        print(f"[WARNING] سرویس‌های ناموفق: {', '.join(failed)}")


if __name__ == "__main__":
    run()
