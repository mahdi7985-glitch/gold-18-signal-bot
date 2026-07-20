
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
    response = requests.get(GOLD_18K_URL, headers=HEADERS, timeout=15)
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


if __name__ == "__main__":
    print(get_gold_18k_price())
