# bot_handler.py
import requests
import os
import time
from datetime import datetime

# تنظیمات
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BALE_TOKEN = os.getenv("BALE_BOT_TOKEN", "")

# آخرین آیدی پیام‌ها برای جلوگیری از پاسخ تکراری
last_telegram_update = 0
last_bale_update = 0


def send_telegram(chat_id, text):
    """ارسال پیام به تلگرام"""
    if not TELEGRAM_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
        return r.ok
    except:
        return False


def send_bale(chat_id, text):
    """ارسال پیام به بله"""
    if not BALE_TOKEN:
        return False
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
        return r.ok
    except:
        return False


def get_telegram_updates(offset=0):
    """دریافت پیام‌های جدید از تلگرام"""
    if not TELEGRAM_TOKEN:
        return []
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={"offset": offset, "timeout": 20}, timeout=25)
        if r.ok:
            data = r.json()
            if data.get("ok"):
                return data.get("result", [])
    except:
        pass
    return []


def get_bale_updates(offset=0):
    """دریافت پیام‌های جدید از بله"""
    if not BALE_TOKEN:
        return []
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={"offset": offset, "timeout": 20}, timeout=25)
        if r.ok:
            data = r.json()
            if data.get("ok"):
                return data.get("result", [])
    except:
        pass
    return []


def handle_telegram_command(chat_id, text):
    """پردازش دستورات تلگرام"""
    # از main.py تابع fetch_and_send_report رو ایمپورت کن
    from main import fetch_and_send_report
    from gold_price_fetcher import get_gold_18k_price, PriceFetchError
    
    if text == "/start":
        msg = "🤖 به ربات تحلیل طلا خوش آمدید!\n\n"
        msg += "📊 دستورات:\n"
        msg += "/signal - دریافت تحلیل لحظه‌ای\n"
        msg += "/price - دریافت قیمت لحظه‌ای\n"
        msg += "/help - راهنما"
        send_telegram(chat_id, msg)
    
    elif text == "/help":
        msg = "📚 راهنمای ربات:\n\n"
        msg += "/signal - دریافت تحلیل کامل با سیگنال خرید/فروش\n"
        msg += "/price - دریافت قیمت لحظه‌ای\n"
        msg += "⏳ تحلیل هر ۴ ساعت به‌روز می‌شود"
        send_telegram(chat_id, msg)
    
    elif text == "/price":
        try:
            price = get_gold_18k_price() / 10
            send_telegram(chat_id, f"💰 قیمت لحظه‌ای: `{price:,.0f}` تومان")
        except PriceFetchError:
            send_telegram(chat_id, "❌ خطا در دریافت قیمت")
    
    elif text == "/signal":
        send_telegram(chat_id, "🔍 در حال دریافت تحلیل...")
        result = fetch_and_send_report(chat_id)
        if not result.get("telegram"):
            send_telegram(chat_id, "❌ خطا در دریافت تحلیل")
    
    else:
        send_telegram(chat_id, "❌ دستور نامعتبر. /help را بزنید.")


def handle_bale_command(chat_id, text):
    """پردازش دستورات بله"""
    from main import fetch_and_send_report
    from gold_price_fetcher import get_gold_18k_price, PriceFetchError
    
    if text == "/start":
        msg = "🤖 به ربات تحلیل طلا خوش آمدید!\n\n"
        msg += "📊 دستورات:\n"
        msg += "/signal - دریافت تحلیل لحظه‌ای\n"
        msg += "/price - دریافت قیمت لحظه‌ای\n"
        msg += "/help - راهنما"
        send_bale(chat_id, msg)
    
    elif text == "/help":
        msg = "📚 راهنمای ربات:\n\n"
        msg += "/signal - دریافت تحلیل کامل با سیگنال خرید/فروش\n"
        msg += "/price - دریافت قیمت لحظه‌ای\n"
        msg += "⏳ تحلیل هر ۴ ساعت به‌روز می‌شود"
        send_bale(chat_id, msg)
    
    elif text == "/price":
        try:
            price = get_gold_18k_price() / 10
            send_bale(chat_id, f"💰 قیمت لحظه‌ای: `{price:,.0f}` تومان")
        except PriceFetchError:
            send_bale(chat_id, "❌ خطا در دریافت قیمت")
    
    elif text == "/signal":
        send_bale(chat_id, "🔍 در حال دریافت تحلیل...")
        result = fetch_and_send_report(chat_id)
        if not result.get("bale"):
            send_bale(chat_id, "❌ خطا در دریافت تحلیل")
    
    else:
        send_bale(chat_id, "❌ دستور نامعتبر. /help را بزنید.")


def run_bot():
    """حلقه اصلی ربات"""
    global last_telegram_update, last_bale_update
    
    print(f"🤖 ربات شروع به کار کرد - {datetime.now()}")
    print("📌 در حال انتظار برای پیام‌ها...")
    
    while True:
        try:
            # ===== تلگرام =====
            updates = get_telegram_updates(last_telegram_update)
            for update in updates:
                if "message" in update:
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "")
                    if text.startswith("/"):
                        handle_telegram_command(chat_id, text)
                if "update_id" in update:
                    last_telegram_update = update["update_id"] + 1
            
            # ===== بله =====
            updates = get_bale_updates(last_bale_update)
            for update in updates:
                if "message" in update:
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "")
                    if text.startswith("/"):
                        handle_bale_command(chat_id, text)
                if "update_id" in update:
                    last_bale_update = update["update_id"] + 1
            
        except Exception as e:
            print(f"❌ خطا: {e}")
        
        time.sleep(3)


if __name__ == "__main__":
    run_bot()
