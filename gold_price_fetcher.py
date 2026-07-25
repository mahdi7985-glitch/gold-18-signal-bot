import random
import requests
from bs4 import BeautifulSoup
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
import time
import re

from config import GOLD_18K_URL, USE_MOCK_PRICE

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fa,en-US;q=0.7,en;q=0.3",
    "Connection": "keep-alive",
}

# موک‌ها برای تست
last_mock_price = 35_000_000.0  # تومان
last_mock_dollar = 189_700.0    # تومان (اصلاح شد)
last_mock_ounce = 2400.0        # دلار

# تاریخچه برای محاسبه تغییرات
_dollar_history = []
_ounce_history = []


class PriceFetchError(Exception):
    """در صورت شکست در دریافت یا پارس قیمت raise می‌شود."""


# ============================================
# توابع کمکی برای پارس قیمت
# ============================================
def _parse_price_text(text: str) -> float:
    """رشته قیمت (با جداکننده هزارگان و احتمالاً واحد) را به float تبدیل می‌کند."""
    cleaned = (
        text.strip()
        .replace(",", "")
        .replace("٬", "")
        .replace("تومان", "")
        .replace("ریال", "")
        .replace("$", "")
        .replace("دلار", "")
        .strip()
    )
    return float(cleaned)


def _extract_number_from_text(text: str) -> Optional[float]:
    """استخراج عدد از متن (برای مواقعی که قیمت در متن پنهان شده)"""
    numbers = re.findall(r'[\d,]+', text.replace(",", ""))
    if numbers:
        try:
            return float(numbers[0])
        except ValueError:
            return None
    return None


# ============================================
# دریافت قیمت از منابع مختلف
# ============================================
def _fetch_from_tgju(url: str = None) -> float:
    """قیمت طلای ۱۸ عیار را از صفحه‌ی tgju.org استخراج می‌کند (خروجی به ریال)."""
    url = url or GOLD_18K_URL
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise PriceFetchError(f"خطا در اتصال به {url}: {e}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # سلکتورهای مختلف برای پیدا کردن قیمت
    candidates = [
        soup.select_one("span#last-price-value"),
        soup.select_one("[data-col='info.last_trade.PDrCotVal']"),
        soup.select_one("table.table-condensed tbody tr td.text-left"),
        soup.select_one(".fs-txt-black .value"),
        soup.select_one("span[data-last-price]"),
        soup.select_one(".price-value"),
        soup.select_one(".last-price"),
    ]
    
    for tag in candidates:
        if tag and tag.get_text(strip=True):
            text = tag.get_text(strip=True)
            try:
                return _parse_price_text(text)
            except ValueError:
                continue
    
    # اگر با سلکتورها پیدا نشد، جستجوی کلی در متن (بهبودیافته)
    all_text = soup.get_text()
    numbers = []
    for word in all_text.split():
        cleaned = word.replace(",", "").replace("٬", "")
        if cleaned.replace(".", "").isdigit() and len(cleaned) > 4:
            try:
                numbers.append(float(cleaned))
            except:
                continue
    
    if numbers:
        # فقط اعداد بزرگتر از ۱۰۰ هزار رو در نظر بگیر
        large_numbers = [n for n in numbers if n > 100000]
        if large_numbers:
            large_numbers.sort(reverse=True)
            # میانگین ۳ عدد بزرگتر (احتمالاً قیمت طلا)
            probable_price = sum(large_numbers[:3]) / len(large_numbers[:3])
            return probable_price
    
    raise PriceFetchError(
        "قیمت طلای ۱۸ عیار در صفحه پیدا نشد. احتمالاً ساختار HTML سایت "
        "تغییر کرده است؛ سلکتورهای gold_price_fetcher.py را به‌روزرسانی کنید."
    )


def fetch_dollar_price() -> float:
    """دریافت قیمت دلار آزاد از tgju.org (خروجی به تومان)"""
    dollar_url = "https://www.tgju.org/%D9%82%DB%8C%D9%85%D8%AA-%D8%AF%D9%84%D8%A7%D8%B1"
    
    try:
        response = requests.get(dollar_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise PriceFetchError(f"خطا در دریافت قیمت دلار: {e}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    candidates = [
        soup.select_one("span#last-price-value"),
        soup.select_one("[data-col='info.last_trade.PDrCotVal']"),
        soup.select_one("table.table-condensed tbody tr td.text-left"),
        soup.select_one(".fs-txt-black .value"),
    ]
    
    for tag in candidates:
        if tag and tag.get_text(strip=True):
            text = tag.get_text(strip=True)
            try:
                price_raw = _parse_price_text(text)
                # قیمت دلار در tgju به ریال هست، تبدیل به تومان
                price_toman = price_raw / 10
                # بررسی منطقی: اگه قیمت بیشتر از ۱ میلیون تومان بود، اشتباهه
                if price_toman > 1_000_000:
                    price_toman = price_toman / 10
                return price_toman
            except ValueError:
                continue
    
    raise PriceFetchError("قیمت دلار در صفحه پیدا نشد")


def fetch_ounce_price() -> float:
    """دریافت قیمت جهانی طلا (اونس) از سایت goldprice.org"""
    ounce_url = "https://www.goldprice.org/fa/"

    try:
        response = requests.get(ounce_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        # منبع پشتیبان
        try:
            return _fetch_ounce_from_alternative()
        except:
            raise PriceFetchError("خطا در دریافت قیمت اونس جهانی")
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # تلاش برای پیدا کردن قیمت اونس
    candidates = [
        soup.select_one(".gold-price .price"),
        soup.select_one("#goldPrice"),
        soup.select_one(".xau-price"),
        soup.select_one("[data-price]"),
    ]
    
    for tag in candidates:
        if tag and tag.get_text(strip=True):
            text = tag.get_text(strip=True)
            try:
                price = _parse_price_text(text)
                if 1000 < price < 5000:  # محدوده منطقی برای اونس
                    return price
            except ValueError:
                continue
    
    raise PriceFetchError("قیمت اونس در صفحه پیدا نشد")


def _fetch_ounce_from_alternative() -> float:
    """دریافت قیمت اونس از منبع پشتیبان"""
    alt_url = "https://api.gold-api.com/price/XAU"
    try:
        response = requests.get(alt_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "price" in data:
            return float(data["price"])
    except:
        pass
    
    raise PriceFetchError("منبع پشتیبان اونس در دسترس نیست")


# ============================================
# توابع قیمت موک (برای تست)
# ============================================
def _fetch_mock_price() -> float:
    """برای تست: یک قیمت شبیه‌سازی‌شده با نوسان تصادفی کوچک تولید می‌کند."""
    global last_mock_price
    change_pct = random.uniform(-0.004, 0.004)
    last_mock_price = round(last_mock_price * (1 + change_pct), 0)
    return last_mock_price


def _fetch_mock_dollar() -> float:
    """موک قیمت دلار (به تومان)"""
    global last_mock_dollar
    change_pct = random.uniform(-0.003, 0.003)
    last_mock_dollar = round(last_mock_dollar * (1 + change_pct), 0)
    return last_mock_dollar


def _fetch_mock_ounce() -> float:
    """موک قیمت اونس"""
    global last_mock_ounce
    change_pct = random.uniform(-0.002, 0.002)
    last_mock_ounce = round(last_mock_ounce * (1 + change_pct), 2)
    return last_mock_ounce


# ============================================
# توابع اصلی برای دریافت قیمت
# ============================================
def get_gold_18k_price() -> float:
    """
    قیمت لحظه‌ای طلای ۱۸ عیار (تومان به ازای هر گرم) را برمی‌گرداند.
    در صورت بروز خطا، PriceFetchError raise می‌شود.
    
    توجه: خروجی به تومان است (نه ریال)
    """
    if USE_MOCK_PRICE:
        return _fetch_mock_price()

    try:
        price_raw = _fetch_from_tgju()
        # تشخیص خودکار: اگه قیمت زیر ۱۰ میلیون باشه، احتمالاً ریال گرفته شده
        if price_raw < 10_000_000:
            # احتمالاً ریال هست، تبدیل به تومان
            return price_raw / 10
        else:
            # احتمالاً تومان هست
            return price_raw
            
    except PriceFetchError:
        raise
    except Exception as exc:
        raise PriceFetchError(f"خطای غیرمنتظره در دریافت قیمت: {exc}") from exc


def get_dollar_price() -> float:
    """دریافت قیمت لحظه‌ای دلار آزاد (تومان)"""
    if USE_MOCK_PRICE:
        return _fetch_mock_dollar()
    
    try:
        return fetch_dollar_price()
    except PriceFetchError:
        raise
    except Exception as exc:
        raise PriceFetchError(f"خطا در دریافت قیمت دلار: {exc}") from exc


def get_dollar_with_change() -> Tuple[float, float]:
    """
    دریافت قیمت دلار و تغییرات درصدی نسبت به قیمت قبلی
    
    Returns:
        tuple: (price, change_percent)
    """
    global _dollar_history
    
    price = get_dollar_price()
    change = 0
    
    if _dollar_history:
        prev = _dollar_history[-1]
        change = ((price - prev) / prev) * 100
    
    _dollar_history.append(price)
    if len(_dollar_history) > 100:
        _dollar_history.pop(0)
    
    return price, change


def get_ounce_price() -> float:
    """دریافت قیمت لحظه‌ای اونس جهانی (دلار)"""
    if USE_MOCK_PRICE:
        return _fetch_mock_ounce()
    
    try:
        return fetch_ounce_price()
    except PriceFetchError:
        raise
    except Exception as exc:
        raise PriceFetchError(f"خطا در دریافت قیمت اونس: {exc}") from exc


def get_ounce_with_change() -> Tuple[float, float]:
    """
    دریافت قیمت اونس و تغییرات درصدی نسبت به قیمت قبلی
    
    Returns:
        tuple: (price, change_percent)
    """
    global _ounce_history
    
    price = get_ounce_price()
    change = 0
    
    if _ounce_history:
        prev = _ounce_history[-1]
        change = ((price - prev) / prev) * 100
    
    _ounce_history.append(price)
    if len(_ounce_history) > 100:
        _ounce_history.pop(0)
    
    return price, change


def get_all_prices() -> Dict[str, float]:
    """
    دریافت همزمان همه قیمت‌ها: طلا، دلار، اونس
    
    Returns:
        dict: {'gold_18k': float, 'dollar': float, 'ounce': float}
    """
    if USE_MOCK_PRICE:
        return {
            'gold_18k': _fetch_mock_price(),
            'dollar': _fetch_mock_dollar(),
            'ounce': _fetch_mock_ounce(),
        }
    
    results = {}
    errors = []
    
    # دریافت قیمت طلا
    try:
        results['gold_18k'] = get_gold_18k_price()
    except PriceFetchError as e:
        errors.append(f"طلا: {e}")
        results['gold_18k'] = 0
    
    # دریافت قیمت دلار
    try:
        results['dollar'] = get_dollar_price()
    except PriceFetchError as e:
        errors.append(f"دلار: {e}")
        results['dollar'] = 0
    
    # دریافت قیمت اونس
    try:
        results['ounce'] = get_ounce_price()
    except PriceFetchError as e:
        errors.append(f"اونس: {e}")
        results['ounce'] = 0
    
    if errors:
        print(f"⚠️ برخی قیمت‌ها دریافت نشدند: {', '.join(errors)}")
    
    return results


def get_all_prices_with_change() -> Dict[str, Any]:
    """
    دریافت همزمان همه قیمت‌ها همراه با تغییرات درصدی
    
    Returns:
        dict: {
            'gold_18k': float,
            'gold_18k_change': float,
            'dollar': float,
            'dollar_change': float,
            'ounce': float,
            'ounce_change': float,
        }
    """
    if USE_MOCK_PRICE:
        return {
            'gold_18k': _fetch_mock_price(),
            'gold_18k_change': random.uniform(-2, 2),
            'dollar': _fetch_mock_dollar(),
            'dollar_change': random.uniform(-1, 1),
            'ounce': _fetch_mock_ounce(),
            'ounce_change': random.uniform(-0.5, 0.5),
        }
    
    results = {
        'gold_18k': 0,
        'gold_18k_change': 0,
        'dollar': 0,
        'dollar_change': 0,
        'ounce': 0,
        'ounce_change': 0,
    }
    
    # دریافت طلا
    try:
        results['gold_18k'] = get_gold_18k_price()
    except:
        pass
    
    # دریافت دلار با تغییرات
    try:
        results['dollar'], results['dollar_change'] = get_dollar_with_change()
    except:
        pass
    
    # دریافت اونس با تغییرات
    try:
        results['ounce'], results['ounce_change'] = get_ounce_with_change()
    except:
        pass
    
    return results


# ============================================
# تست
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("📊 دریافت قیمت‌های لحظه‌ای")
    print("=" * 60)
    
    try:
        gold = get_gold_18k_price()
        print(f"💰 طلای ۱۸ عیار: {gold:,.0f} تومان")
    except PriceFetchError as e:
        print(f"❌ خطا: {e}")
    
    try:
        dollar = get_dollar_price()
        print(f"💵 دلار آزاد: {dollar:,.0f} تومان")
    except PriceFetchError as e:
        print(f"❌ خطا: {e}")
    
    try:
        ounce = get_ounce_price()
        print(f"🏅 اونس جهانی: {ounce:,.2f} دلار")
    except PriceFetchError as e:
        print(f"❌ خطا: {e}")
