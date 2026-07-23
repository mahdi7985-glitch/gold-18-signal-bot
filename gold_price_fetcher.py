import random
import requests
from bs4 import BeautifulSoup
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
import time

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

# آخرین قیمت موک‌شده، برای تولید یک random-walk واقع‌نمایانه بین اجراها
last_mock_price = 35_000_000.0  # تومان به ازای هر گرم (فقط مقدار اولیه‌ی نمونه)
last_mock_dollar = 850_000.0  # تومان به ازای هر دلار
last_mock_ounce = 2400.0  # دلار به ازای هر اونس


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
    import re
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
    """قیمت طلای ۱۸ عیار را از صفحه‌ی tgju.org استخراج می‌کند."""
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
    
    # اگر با سلکتورها پیدا نشد، جستجوی کلی در متن
    all_text = soup.get_text()
    numbers = [float(n.replace(",", "")) for n in all_text.split() 
               if n.replace(",", "").replace(".", "").isdigit() and len(n) > 4]
    
    if numbers:
        # معمولاً قیمت طلا عدد بزرگ است
        probable_price = max(numbers)  # بزرگترین عدد را به عنوان قیمت در نظر بگیر
        if probable_price > 100000:  # باید بالای ۱۰۰ هزار تومان باشد
            return probable_price
    
    raise PriceFetchError(
        "قیمت طلای ۱۸ عیار در صفحه پیدا نشد. احتمالاً ساختار HTML سایت "
        "تغییر کرده است؛ سلکتورهای gold_price_fetcher.py را به‌روزرسانی کنید."
    )


def fetch_dollar_price() -> float:
    """دریافت قیمت دلار آزاد از tgju.org"""
    dollar_url = "https://www.tgju.org/profile/price_dollar_rl"
    
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
            try:
                return _parse_price_text(tag.get_text())
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
    ]
    
    for tag in candidates:
        if tag and tag.get_text(strip=True):
            text = tag.get_text(strip=True)
            try:
                # قیمت معمولاً به صورت "۲۴۰۰.۵۰" است
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
    """موک قیمت دلار"""
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
    """
    if USE_MOCK_PRICE:
        return _fetch_mock_price()

    try:
        return _fetch_from_tgju()
    except PriceFetchError:
        raise
    except Exception as exc:
        raise PriceFetchError(f"خطای غیرمنتظره در دریافت قیمت: {exc}") from exc


def get_dollar_price() -> float:
    """دریافت قیمت لحظه‌ای دلار آزاد"""
    if USE_MOCK_PRICE:
        return _fetch_mock_dollar()
    
    try:
        return fetch_dollar_price()
    except PriceFetchError:
        raise
    except Exception as exc:
        raise PriceFetchError(f"خطا در دریافت قیمت دلار: {exc}") from exc


def get_ounce_price() -> float:
    """دریافت قیمت لحظه‌ای اونس جهانی"""
    if USE_MOCK_PRICE:
        return _fetch_mock_ounce()
    
    try:
        return fetch_ounce_price()
    except PriceFetchError:
        raise
    except Exception as exc:
        raise PriceFetchError(f"خطا در دریافت قیمت اونس: {exc}") from exc


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


# ============================================
# تست
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("📊 دریافت قیمت‌های لحظه‌ای")
    print("=" * 60)
    
    try:
        gold = get_gold_18k_price()
        print(f"💰 طلای ۱۸ عیار: {gold/10:,.0f} تومان")
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
    
    print("\n📋 همه قیمت‌ها با هم:")
    all_prices = get_all_prices()
    for key, value in all_prices.items():
        print(f"  {key}: {value}")
