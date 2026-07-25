import sys
from datetime import datetime
from typing import Optional, Dict, Any  # ← این خط حتماً باید باشه
import pandas as pd
import os

from config import (
    EMA_FAST, EMA_SLOW, RSI_LENGTH, MACD_FAST, MACD_SLOW, MACD_SIGNAL, ADX_LENGTH,
    RSI_OVERBOUGHT, RSI_OVERSOLD, ADX_THRESHOLD, MIN_CANDLES_REQUIRED,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BALE_BOT_TOKEN, BALE_CHAT_ID,
    SHOW_LEVELS, SHOW_DOLLAR_OUNCE, SHOW_HISTORY, SHOW_DAILY_CHANGE,
    HISTORY_FILE
)
from gold_price_fetcher import get_gold_18k_price, PriceFetchError, get_all_prices_with_change
from storage import (
    append_price, load_history, trim_history, get_previous_price, save_signal,
    get_recent_prices, get_weekly_trend, get_price_change_percent
)
from indicators import get_latest_analysis, build_ohlc_candles, calculate_support_resistance
from signal_analyzer import analyze_with_friendly
from telegram_notifier import send_telegram_message
from bale_notifier import send_bale_message


# ============================================
# بازنشانی تاریخچه (فقط یک بار)
# ============================================
def reset_history_if_needed():
    """اگر تاریخچه با فرمت جدید هماهنگ نیست، بازنشانی کن"""
    try:
        if not os.path.exists(HISTORY_FILE):
            return
            
        df = pd.read_csv(HISTORY_FILE)
        if not df.empty:
            sample = df["price"].iloc[0]
            if sample < 10_000_000:
                print("⚠️ تاریخچه قدیمی با فرمت ریال شناسایی شد. در حال بازنشانی...")
                df_new = pd.DataFrame(columns=["timestamp", "price"])
                df_new.to_csv(HISTORY_FILE, index=False)
                print("✅ تاریخچه بازنشانی شد")
    except Exception as e:
        print(f"⚠️ خطا در بازنشانی تاریخچه: {e}")

reset_history_if_needed()


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
    from datetime import datetime as dt
    from zoneinfo import ZoneInfo
    import jdatetime
    now = dt.now(ZoneInfo("Asia/Tehran"))
    return jdatetime.datetime.fromgregorian(datetime=now)


def format_jalali_datetime(jalali) -> str:
    weekday_name = PERSIAN_WEEKDAYS[jalali.weekday()]
    return f"{weekday_name} {jalali.strftime('%Y/%m/%d')} | 🕒 {jalali.strftime('%H:%M')}"


def get_iran_day() -> str:
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
    analysis: Dict[str, Any],
    dollar_price: Optional[float] = None,
    dollar_change: Optional[float] = None,
    ounce_price: Optional[float] = None,
    ounce_change: Optional[float] = None
) -> str:
    # ===== زمان =====
    jalali = get_jalali_now()
    day_name = get_iran_day()
    
    # ===== قیمت‌ها =====
    price_toman = price
    
    # ===== تاریخچه قیمت =====
    recent_prices = get_recent_prices(5)
    weekly_trend_data = get_weekly_trend()
    
    # ===== تغییرات =====
    change_text = ""
    advice = "🤔 امروز تازه شروع کردیم، بذار چند روز بگذره تا روند مشخص بشه."
    trend_emoji = "⚪"
    trend_word = "ثابت"
    
    if previous_price is not None and previous_price > 0:
        prev_toman = previous_price
        change_amount = price - previous_price
        change_percent = (change_amount / previous_price) * 100
        
        if change_amount > 0:
            trend_emoji = "🟢"
            trend_word = "صعود"
            if change_percent > 3:
                advice = "🚀 امروز داره پرواز می‌کنه! ولی زیاد ذوق نکن، ممکنه یه اصلاح کوچیک بیاد."
            elif change_percent > 1:
                advice = "😊 امروز روز خوبیه، آروم آروم داره می‌ره بالا. محتاط باش ولی خوش‌بین."
            else:
                advice = "📈 یه رشد ملایم، اوضاع داره آروم آروم خوب میشه."
        elif change_amount < 0:
            trend_emoji = "🔻"
            trend_word = "نزول"
            if abs(change_percent) > 5:
                advice = "😬 وای امروز ریزش سنگینی داشتیم! صبر کن تا بازار آروم بشه."
            elif abs(change_percent) > 2:
                advice = "📉 یه ریزش معمولی، نگران نباش. بذار ببینیم کفش کجاست."
            else:
                advice = "🔻 یه کم داره پایین میاد، ولی خیلی عادی‌ست."
        else:
            advice = "⚪ امروز تکون خاصی نداریم، همه منتظر یه خبر جدید هستن."
        
        change_text = f"""
📊 دیروز این ساعت: **{prev_toman:,.0f}** تومان
📉 تغییر: {trend_emoji} **{trend_word} {abs(change_amount):,.0f}** تومان ({change_percent:.2f}%)
"""
    
    # ===== تاریخچه قیمت =====
    history_text = ""
    if SHOW_HISTORY and len(recent_prices) >= 2:
        history_text = "\n📅 قیمت‌های اخیر:\n"
        labels = ["امروز", "دیروز", "پریروز", "۳ روز پیش", "۴ روز پیش", "۵ روز پیش"]
        for i, (label, price_val) in enumerate(zip(labels, recent_prices)):
            if i == 0:
                history_text += f"• {label}: {price_val:,.0f} تومان\n"
            elif i < len(recent_prices):
                history_text += f"• {label}: {recent_prices[i]:,.0f} تومان\n"
    
    # ===== روند هفتگی =====
    weekly_text = ""
    if weekly_trend_data['trend'] != "داده کافی نیست":
        weekly_text = f"📈 روند هفتگی: از {weekly_trend_data['start']:,.0f} به {weekly_trend_data['end']:,.0f}"
        if weekly_trend_data['change'] > 0:
            weekly_text += f" (صعود {weekly_trend_data['change']:.1f}%)"
        else:
            weekly_text += f" (نزول {abs(weekly_trend_data['change']):.1f}%)"
    
    # ===== سیگنال =====
    signal_text = analysis.get("signal_text", "صبر کن")
    signal_emoji = analysis.get("signal_emoji", "🟡")
    signal_confidence = analysis.get("signal_confidence", 35)
    trend = analysis.get("trend", "خنثی")
    signal_reason = analysis.get("signal_reason", "دلیل خاصی نداریم")
    
    if signal_confidence == 0:
        signal_confidence = 35
        signal_reason = "🔸 وضعیت نامشخص، بهتره صبر کنی تا بازار تکلیفش مشخص بشه."
    
    friendly = analysis.get("friendly", {})
    friendly_message = friendly.get("friendly_message", "🟡 صبر کن، فعلاً وقتش نیست.")
    
    indicators = analysis.get("indicators", {})
    rsi_val = indicators.get('rsi', 50)
    
    if "نزول" in trend_word or change_amount < 0:
        if rsi_val > 70:
            advice = "🔴 RSI اشباع خرید رو نشون میده. با توجه به ریزش امروز، احتمالاً این یه اصلاح موقتیه. بهتره صبر کنی تا قیمت به حمایت برسه و بعد تصمیم بگیری."
        elif rsi_val < 30:
            advice = "🟢 RSI اشباع فروش رو نشون میده. ممکنه کف نزدیک باشه، ولی بازم صبر کن تا برگشت رو تأیید کنی."
        else:
            advice = "🟡 بازار در منطقه تعادله. صبر کن ببینیم روند مشخص میشه."
    
    # ===== سطوح حمایت و مقاومت =====
    history = load_history()
    support_raw, resistance_raw = calculate_support_resistance(history["price"], period=14)
    
    support = support_raw / 10 if support_raw else None
    resistance = resistance_raw / 10 if resistance_raw else None
    
    support2 = support * 0.98 if support else None
    resistance2 = resistance * 1.02 if resistance else None
    
    # ===== ساخت پیام =====
    message = f"""سلام رفیق! 👋
برات تحلیل امروز طلا رو گرفتم:

📅 {format_jalali_datetime(jalali)}
━━━━━━━━━━━━━━━━━━━━
💰 قیمت الان: **{price_toman:,.0f}** تومان
{change_text}
{weekly_text}
{history_text}
━━━━━━━━━━━━━━━━━━━━

🎯 نظر من:
{signal_emoji} **{signal_text}** (با {signal_confidence}% اطمینان)

{signal_reason}

{friendly_message}

━━━━━━━━━━━━━━━━━━━━
📊 یه نگاه به اعداد بندازیم:

• میانگین ۲۰ روزه: {indicators.get('ema_fast', 0)/10:,.0f} تومان
• میانگین ۵۰ روزه: {indicators.get('ema_slow', 0)/10:,.0f} تومان
• RSI: {indicators.get('rsi', 0):.1f} """

    if rsi_val > 70:
        message += "🔴 اشباع خرید\n"
    elif rsi_val < 30:
        message += "🟢 اشباع فروش\n"
    else:
        message += "🟡 متعادل\n"
    
    message += f"""• قدرت روند (ADX): {indicators.get('adx', 0):.1f} """
    
    adx_val = indicators.get('adx', 0)
    if adx_val > 25:
        message += "💪 قوی\n"
    elif adx_val > 20:
        message += "🤔 متوسط\n"
    else:
        message += "😶 ضعیف\n"
    
    if 'macd' in indicators and 'macd_signal' in indicators:
        if indicators['macd'] > indicators['macd_signal']:
            message += "• مکدی: مثبت 📈 (مومنتوم صعودی)\n"
        else:
            message += "• مکدی: منفی 📉 (مومنتوم نزولی)\n"
    
    if SHOW_LEVELS and support and resistance:
        dist_to_support = ((price - support) / price) * 100
        dist_to_resistance = ((resistance - price) / price) * 100
        
        message += f"""
━━━━━━━━━━━━━━━━━━━━
📍 سطح‌های مهم امروز:

اگه بره پایین‌تر:
🛡️ **حمایت اول:** {support:,.0f} تومان ({dist_to_support:.1f}% پایین‌تر)
🛡️ **حمایت دوم:** {support2:,.0f} تومان ({dist_to_support - 2:.1f}% پایین‌تر)

اگه برگرده بالا:
🚀 **مقاومت اول:** {resistance:,.0f} تومان ({dist_to_resistance:.1f}% بالاتر)
🚀 **مقاومت دوم:** {resistance2:,.0f} تومان ({dist_to_resistance + 2:.1f}% بالاتر)
"""
    
    if SHOW_DOLLAR_OUNCE and dollar_price:
        dollar_emoji = "🟢" if dollar_change and dollar_change > 0 else "🔻" if dollar_change and dollar_change < 0 else "⚪"
        message += f"""
━━━━━━━━━━━━━━━━━━━━
💎 دو تا فاکتور مهم دیگه:

💵 دلار آزاد: {dollar_price:,.0f} تومان ({dollar_emoji} {'صعودی' if dollar_change and dollar_change > 0 else 'نزولی' if dollar_change and dollar_change < 0 else 'ثابت'})
"""
        if ounce_price:
            ounce_emoji = "🟢" if ounce_change and ounce_change > 0 else "🔻" if ounce_change and ounce_change < 0 else "⚪"
            message += f"""🏅 انس جهانی: ${ounce_price:,.2f} ({ounce_emoji} {'صعودی' if ounce_change and ounce_change > 0 else 'نزولی' if ounce_change and ounce_change < 0 else 'ثابت'})
"""
            if dollar_change and ounce_change:
                if dollar_change > 0 and ounce_change > 0:
                    message += "🔺 تأثیر روی طلا: **مثبت قوی** (هر دو صعودی)"
                elif dollar_change > 0 and ounce_change < 0:
                    message += "🔄 تأثیر روی طلا: **مختلط** (دلار بالا، انس پایین)"
                elif dollar_change < 0 and ounce_change > 0:
                    message += "🔄 تأثیر روی طلا: **مختلط** (دلار پایین، انس بالا)"
                else:
                    message += "🔻 تأثیر روی طلا: **منفی** (هر دو نزولی)"
    
    message += f"""
━━━━━━━━━━━━━━━━━━━━
🗣️ حرف آخر:

{advice}
"""
    
    return message


def format_collecting_data_message(price: float, have: int, need: int) -> str:
    jalali = get_jalali_now()
    price_toman = price
    day_name = get_iran_day()
    
    return f"""سلام رفیق! 👋
در حال راه‌اندازی تحلیلگر طلا هستم...

📅 {format_jalali_datetime(jalali)}
📍 {day_name}

💰 قیمت لحظه‌ای: **{price_toman:,.0f}** تومان

⏳ در حال جمع‌آوری داده برای تحلیل تکنیکال ({have}/{need} کندل).

📊 هر چی داده بیشتر باشه، تحلیل دقیق‌تر میشه.
به‌محض کافی‌شدن داده، گزارش کامل رو برات می‌فرستم.

صبر کن تا بهت خبر بدم 🤝
"""


# ============================================
# تابع اصلی fetch_and_send_report
# ============================================
def fetch_and_send_report(chat_id: Optional[str] = None) -> Dict[str, bool]:
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] شروع دریافت گزارش...")

    try:
        price = get_gold_18k_price()
    except PriceFetchError as exc:
        print(f"[ERROR] دریافت قیمت ناموفق بود: {exc}", file=sys.stderr)
        return {"telegram": False, "bale": False}

    print(f"[INFO] قیمت دریافت‌شده: {price:,.0f} تومان")

    all_data = get_all_prices_with_change()
    dollar_price = all_data.get('dollar', 0)
    dollar_change = all_data.get('dollar_change', 0)
    ounce_price = all_data.get('ounce', 0)
    ounce_change = all_data.get('ounce_change', 0)

    append_price(price)
    trim_history()

    previous_price = get_previous_price()
    
    history = load_history()
    analysis_result = get_latest_analysis(history["price"])
    
    if analysis_result is None:
        candles_count = len(build_ohlc_candles(history["price"]))
        message = format_collecting_data_message(
            price, 
            candles_count, 
            MIN_CANDLES_REQUIRED
        )
        result = send_to_both(message, chat_id)
        return result
    
    from signal_analyzer import analyze_with_friendly
    df = analysis_result.get("df")
    if df is not None:
        friendly_result = analyze_with_friendly(df)
        analysis_result['friendly'] = friendly_result.get('friendly', {})
    
    message = format_full_report(
        price, 
        previous_price, 
        analysis_result,
        dollar_price,
        dollar_change,
        ounce_price,
        ounce_change
    )
    
    print(f"[INFO] سیگنال: {analysis_result.get('signal', 'WAIT')} | اطمینان: {analysis_result.get('signal_confidence', 0)}%")
    
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
    
    result = send_to_both(message, chat_id)
    return result


def run(chat_id: Optional[str] = None) -> Dict[str, bool]:
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
