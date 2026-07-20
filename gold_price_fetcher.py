
import os
import pandas as pd
from datetime import datetime, timezone

from config import HISTORY_FILE, DATA_DIR

COLUMNS = ["timestamp", "price"]


def ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def append_price(price: float, timestamp: datetime | None = None) -> None:
    """یک رکورد قیمت جدید را به فایل تاریخچه اضافه می‌کند."""
    ensure_data_dir()
    timestamp = timestamp or datetime.now(timezone.utc)

    row = pd.DataFrame([{"timestamp": timestamp.isoformat(), "price": price}])

    if os.path.exists(HISTORY_FILE):
        row.to_csv(HISTORY_FILE, mode="a", header=False, index=False)
    else:
        row.to_csv(HISTORY_FILE, mode="w", header=True, index=False)


def load_history() -> pd.DataFrame:
    """تاریخچه قیمت را به‌صورت DataFrame با ایندکس زمانی برمی‌گرداند."""
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=COLUMNS).set_index("timestamp")

    df = pd.read_csv(HISTORY_FILE)
    if df.empty:
        return pd.DataFrame(columns=COLUMNS).set_index("timestamp")

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")
    df = df.set_index("timestamp")
    return df


def trim_history(max_rows: int = 20000) -> None:
    """
    برای جلوگیری از رشد بی‌رویه‌ی فایل تاریخچه در طول ماه‌ها، تعداد ردیف‌ها
    را محدود می‌کند (قدیمی‌ترین‌ها حذف می‌شوند).
    """
    df = load_history()
    if len(df) > max_rows:
        df = df.iloc[-max_rows:]
        ensure_data_dir()
        df.reset_index().to_csv(HISTORY_FILE, index=False)

gold_price_fetcher.py

"""
gold_price_fetcher.py
----------------------
دریافت قیمت لحظه‌ای طلای ۱۸ عیار (هر گرم) از tgju.org.

نکته‌ی مهم: این ماژول با اسکرپ HTML کار می‌کند، نه یک API رسمی. سایت‌ها
ساختار HTML خود را گاه‌به‌گاه تغییر می‌دهند، پس اگر بعد از مدتی دریافت قیمت
با خطا مواجه شد، باید سلکتورهای زیر (CSS selector / data attribute) را با
مشاهده‌ی Source صفحه‌ی tgju.org/profile/geram18 به‌روزرسانی کنید.

اگر به یک منبع پایدارتر نیاز دارید، سرویس‌های API پولی مثل navasan.tech یا
brsapi.ir هم گزینه‌های مناسبی هستند (نیاز به API Key دارند).

برای تست بدون وابستگی به اینترنت/سایت مبدا، متغیر محیطی USE_MOCK_PRICE=true
را تنظیم کنید تا یک قیمت شبیه‌سازی‌شده (random walk) تولید شود.
"""

import random
import requests
from bs4 import BeautifulSoup

from config import GOLD_18K_URL, USE_MOCK_PRICE

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

# آخرین قیمت موک‌شده، برای تولید یک random-walk واقع‌نمایانه بین اجراها
last_mock_price = 35_000_000.0  # تومان به ازای هر گرم (فقط مقدار اولیه‌ی نمونه)


class PriceFetchError(Exception):
    """در صورت شکست در دریافت یا پارس قیمت raise می‌شود."""


def _parse_price_text(text: str) -> float:
    """رشته قیمت (با جداکننده هزارگان و احتمالاً واحد) را به float تبدیل می‌کند."""
    cleaned = (
        text.strip()
        .replace(",", "")
        .replace("٬", "")
        .replace("تومان", "")
        .replace("ریال", "")
        .strip()
    )
    return float(cleaned)


def _fetch_from_tgju() -> float:
    """قیمت طلای ۱۸ عیار را از صفحه‌ی tgju.org استخراج می‌کند."""
    response = requests.get(GOLD_18K_URL, headers=_HEADERS, timeout=15)
    response.raise_for_status()
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

    raise PriceFetchError(
        "قیمت طلای ۱۸ عیار در صفحه پیدا نشد. احتمالاً ساختار HTML سایت "
        "تغییر کرده است؛ سلکتورهای gold_price_fetcher.py را به‌روزرسانی کنید."
    )


def _fetch_mock_price() -> float:
    """برای تست: یک قیمت شبیه‌سازی‌شده با نوسان تصادفی کوچک تولید می‌کند."""
    global _last_mock_price
    change_pct = random.uniform(-0.004, 0.004)
    _last_mock_price = round(_last_mock_price * (1 + change_pct), 0)
    return _last_mock_price


def get_gold_18k_price() -> float:
    """
    قیمت لحظه‌ای طلای ۱۸ عیار (تومان به ازای هر گرم) را برمی‌گرداند.
    در صورت بروز خطا، PriceFetchError raise می‌شود.
    """
    if USE_MOCK_PRICE:
        return _fetch_mock_price()

    try:
        return _fetch_from_tgju()
    except requests.RequestException as exc:
        raise PriceFetchError(f"خطا در اتصال به {GOLD_18K_URL}: {exc}") from exc


if __name == "__main__":
    print(get_gold_18k_price())
