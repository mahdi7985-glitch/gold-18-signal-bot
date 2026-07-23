import sys
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd

from config import (
    EMA_FAST, EMA_SLOW, RSI_LENGTH, MACD_FAST, MACD_SLOW, MACD_SIGNAL, ADX_LENGTH,
    RSI_OVERBOUGHT, RSI_OVERSOLD, ADX_THRESHOLD, MIN_CANDLES_REQUIRED,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BALE_BOT_TOKEN, BALE_CHAT_ID
)
from gold_price_fetcher import get_gold_18k_price, PriceFetchError
from storage import append_price, load_history, trim_history, get_previous_price, save_signal
from indicators import get_latest_analysis, build_ohlc_candles
from signal_analyzer import analyze
from telegram_notifier import send_telegram_message
from bale_notifier import send_bale_message


# ============================================
# توابع کمکی برای فرمت‌دهی زمان (ایران)
# ============================================
PERSIAN_WEEKDAYS = {
    0: "شنبه",
    1: "یکشنبه",
    2: "دوشنبه",
    3: "سه شنبه",
    4: "چهارشنبه",
    5: "پنجشنبه",
    6: "جمعه",
}


def get_jalali_now():
    """دریافت تاریخ و زمان جلالی با منطقه زمانی ایران"""
    from datetime import datetime as dt
    from zoneinfo import ZoneInfo
    import jdatetime
    now = dt.now(ZoneInfo("Asia/Tehran"))
    return jdatetime.datetime.fromgregorian(datetime=now)


def format_jalali_datetime(jalali) -> str:
    """فرمت تاریخ جلالی با نام روز هفته"""
    weekday_name = PERSIAN_WEEKDAYS[jalali.weekday()]
    return f"{weekday_name} {jalali.strftime('%Y/%m/%d')} | 🕒 {jalali.strftime('%H:%M')}"


def get_iran_day() -> str:
    """دریافت نام روز هفته به فارسی"""
    from datetime import datetime as dt
    from zoneinfo import ZoneInfo
    days = {
        0: "دوشنبه",
        1: "سه‌شنبه",
        2: "چهارشنبه",
        3: "پنجشنبه",
        4: "جمعه",
        5: "شنبه",
        6: "یکشنبه"
    }
    now = dt.now(ZoneInfo("Asia/Tehran"))
    return days[now.weekday()]


# ============================================
# تابع ارسال به هر دو سرویس
# ============================================
def send_to_both(message: str, chat_id: Optional[str] = None) -> Dict[str, bool]:
    """ارسال پیام به هر دو سرویس تلگرام و بله"""
    results = {
        "telegram": send_telegram_message(message, chat_id),
        "bale": send_bale_message(message, chat_id)
    }

    success_count = sum(results.values())
    if success_count == 2:
        print("✅ پیام به هر دو سرویس (تلگرام و بله) ارسال شد.")
    elif success_count == 1:
        print("⚠️ پیام فقط به یکی از سرویس‌ها ارسال شد.")
        failed = [k for k, v in results.items() if not v]
        print(f"   سرویس‌های ناموفق: {', '.join(failed)}")
    else:
        print("❌ پیام به هیچکدام از سرویس‌ها ارسال نشد.")

    return results


# ============================================
# تابع تولید گزارش کامل
# ============================================
def format_full_report(
    price: float,
    previous_price: Optional[float],
    analysis: Dict[str, Any]
) -> str:
    """
    تولید گزارش کامل و ساده با سیگنال واضح
    
    Args:
        price: قیمت فعلی (به ریال)
        previous_price: قیمت قبلی (به ریال) یا None
        analysis: دیکشنری خروجی از get_latest_analysis
    
    Returns:
        str: متن گزارش فرمت‌شده
    """
    # ===== زمان =====
    jalali = get_jalali_now()
    day_name = get_iran_day()
    
    # ===== قیمت‌ها و تغییرات =====
    price_toman = price / 10  # تبدیل ریال به تومان
    
    price_text = f"💰 قیمت لحظه‌ای: `{price_toman:,.0f}` تومان"
    
    # محاسبه تغییرات نسبت به قیمت قبلی
    change_text = ""
    if previous_price is not None and previous_price > 0:
        prev_toman = previous_price / 10
        change_amount = price - previous_price  # به ریال
        change_toman = change_amount / 10
        change_percent = (change_amount / previous_price) * 100
        
        # ایموجی برای جهت تغییر
        if change_amount > 0:
            arrow = "🟢▲"
            sign = "+"
        elif change_amount < 0:
            arrow = "🔻▼"
            sign = ""
        else:
            arrow = "⚪"
            sign = ""
        
        change_text = (
            f"📉 قیمت قبلی: `{prev_toman:,.0f}` تومان\n"
            f"📊 تغییر: {arrow} `{sign}{change_toman:,.0f}` تومان ({sign}{change_percent:.2f}%)"
        )
    else:
        change_text = "📊 تغییر: ⚪ بدون داده قبلی"
    
    # ===== سیگنال =====
    signal = analysis.get("signal", "WAIT")
    signal_text = analysis.get("signal_text", "صبر کن")
    signal_emoji = analysis.get("signal_emoji", "⚪")
    signal_reason = analysis.get("signal_reason", "هیچ سیگنالی تشخیص داده نشد")
    signal_confidence = analysis.get("signal_confidence", 0)
    
    # ===== روند کلی =====
    trend = analysis.get("trend", "خنثی")
    trend_emoji = {
        "صعودی قوی": "🟢🟢",
        "صعودی": "🟢",
        "خنثی": "🟡",
        "نزولی": "🔴",
        "نزولی قوی": "🔴🔴",
    }.get(trend, "⚪")
    
    # ===== اندیکاتورها =====
    indicators = analysis.get("indicators", {})
    
    # ===== ساخت پیام نهایی =====
    message = (
        f"<b>📊 تحلیل طلای ۱۸ عیار</b>\n"
        f"📅 {format_jalali_datetime(jalali)}\n"
        f"📍 {day_name}\n\n"
        f"{price_text}\n"
        f"{change_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>سیگنال نهایی:</b>\n"
        f"{signal_emoji} <b>{signal_text}</b> (با اطمینان {signal_confidence}%)\n"
        f"📌 {signal_reason}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{trend_emoji} روند کلی: <b>{trend}</b>\n\n"
        f"<b>📈 اندیکاتورها:</b>\n"
    )
    
    # اضافه کردن اندیکاتورها (فقط موارد جدید)
    if "ema_fast" in indicators:
        message += f"• EMA 20: `{indicators['ema_fast']/10:,.0f}`\n"
    if "ema_slow" in indicators:
        message += f"• EMA 50: `{indicators['ema_slow']/10:,.0f}`\n"
    if "rsi" in indicators:
        message += f"• RSI(10): {indicators['rsi']:.1f}\n"
    if "macd" in indicators:
        message += f"• MACD: {indicators['macd']:.2f} | سیگنال: {indicators['macd_signal']:.2f}\n"
    if "adx" in indicators:
        message += f"• ADX: {indicators['adx']:.1f}\n"
    
    # اضافه کردن وضعیت ADX (قوی/ضعیف)
    if indicators.get("adx", 0) > ADX_THRESHOLD:
        message += f"   ✅ ADX قوی (>{ADX_THRESHOLD})\n"
    else:
        message += f"   ⚠️ ADX ضعیف (<{ADX_THRESHOLD})\n"
    
    # اضافه کردن وضعیت RSI
    rsi_val = indicators.get("rsi", 50)
    if rsi_val > RSI_OVERBOUGHT:
        message += f"   🔴 RSI اشباع خرید (>{RSI_OVERBOUGHT})\n"
    elif rsi_val < RSI_OVERSOLD:
        message += f"   🟢 RSI اشباع فروش (<{RSI_OVERSOLD})\n"
    else:
        message += f"   🟡 RSI در محدوده متعادل\n"
    
    message += (
        f"\n━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>⚠️ این تحلیل فقط جنبه آموزشی دارد و توصیه مالی نیست.</i>"
    )
    
    return message


def format_collecting_data_message(price: float, have: int, need: int) -> str:
    """پیام در حال جمع‌آوری داده"""
    jalali = get_jalali_now()
    price_toman = price / 10
    
    return (
        f"<b>📊 قیمت طلای ۱۸ عیار</b>\n"
        f"📅 {format_jalali_datetime(jalali)}\n\n"
        f"💰 قیمت لحظه‌ای: `{price_toman:,.0f}` تومان\n\n"
        f"⏳ در حال جمع‌آوری داده برای تحلیل تکنیکال ({have}/{need} کندل).\n"
        f"به‌محض کافی‌شدن داده، گزارش کامل ارسال می‌شود."
    )


# ============================================
# تابع اصلی fetch_and_send_report
# ============================================
def fetch_and_send_report(chat_id: Optional[str] = None) -> Dict[str, bool]:
    """
    دریافت قیمت و ارسال گزارش
    
    Args:
        chat_id: شناسه کاربر برای پاسخ (اختیاری)
    
    Returns:
        dict: نتایج ارسال به هر سرویس
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] شروع دریافت گزارش...")

    try:
        price = get_gold_18k_price()
    except PriceFetchError as exc:
        print(f"[ERROR] دریافت قیمت ناموفق بود: {exc}", file=sys.stderr)
        return {"telegram": False, "bale": False}

    print(f"[INFO] قیمت دریافت‌شده: {price/10:,.0f} تومان")

    # ذخیره در تاریخچه
    append_price(price)
    trim_history()

    # دریافت قیمت قبلی
    previous_price = get_previous_price()
    
    # دریافت تاریخچه و تحلیل
    history = load_history()
    analysis_result = get_latest_analysis(history["price"])
    
    # اگر تحلیل نداریم
    if analysis_result is None or "error" in analysis_result:
        candles_count = len(build_ohlc_candles(history["price"]))
        message = format_collecting_data_message(
            price, 
            candles_count, 
            MIN_CANDLES_REQUIRED
        )
        result = send_to_both(message, chat_id)
        return result
    
    # ساخت گزارش کامل
    message = format_full_report(price, previous_price, analysis_result)
    print(f"[INFO] سیگنال: {analysis_result.get('signal', 'WAIT')} | اطمینان: {analysis_result.get('signal_confidence', 0)}%")
    
    # ذخیره سیگنال در تاریخچه
    try:
        signal_data = {
            "price": price,
            "signal": analysis_result.get("signal", "WAIT"),
            "signal_text": analysis_result.get("signal_text", ""),
            "signal_confidence": analysis_result.get("signal_confidence", 0),
            "trend": analysis_result.get("trend", ""),
        }
        save_signal(signal_data)
    except Exception as e:
        print(f"⚠️ خطا در ذخیره سیگنال: {e}")
    
    # ارسال به هر دو
    result = send_to_both(message, chat_id)
    return result


def run(chat_id: Optional[str] = None) -> Dict[str, bool]:
    """
    نقطه ورود اصلی
    
    Args:
        chat_id: شناسه کاربر برای پاسخ (اختیاری)
    
    Returns:
        dict: نتایج ارسال به هر سرویس
    """
    # بررسی تنظیمات
    if not TELEGRAM_BOT_TOKEN and not BALE_BOT_TOKEN:
        print("[ERROR] هیچ سرویسی (تلگرام یا بله) تنظیم نشده است!", file=sys.stderr)
        return {"telegram": False, "bale": False}
    
    if TELEGRAM_BOT_TOKEN and not TELEGRAM_CHAT_ID:
        print("[WARNING] TELEGRAM_BOT_TOKEN تنظیم شده ولی TELEGRAM_CHAT_ID خالی است!")
    
    if BALE_BOT_TOKEN and not BALE_CHAT_ID:
        print("[WARNING] BALE_BOT_TOKEN تنظیم شده ولی BALE_CHAT_ID خالی است!")

    return fetch_and_send_report(chat_id)


if __name__ == "__main__":
    run()
