
storage.py
----------
هر بار که ربات اجرا می‌شود، یک نقطه‌ی قیمتی جدید به فایل CSV اضافه می‌شود.
این فایل در طول زمان (هر ۵ دقیقه یک ردیف) به‌عنوان تاریخچه‌ی قیمت جمع می‌شود
و پایه‌ی محاسبه‌ی اندیکاتورهای تکنیکال (که نیازمند سری زمانی هستند) قرار می‌گیرد.

در GitHub Actions، این فایل باید در انتهای هر اجرا به‌صورت commit به ریپازیتوری
برگردانده شود تا تاریخچه بین اجراهای مختلف حفظ شود (این کار در workflow انجام می‌شود).
"""

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
