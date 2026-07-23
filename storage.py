import os
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import json

from config import HISTORY_FILE, DATA_DIR, RESULTS_FILE

COLUMNS = ["timestamp", "price"]
SIGNAL_COLUMNS = ["timestamp", "price", "signal", "signal_text", "confidence", "trend"]


# ============================================
# توابع پایه برای مدیریت دایرکتوری
# ============================================
def ensure_data_dir() -> None:
    """اطمینان از وجود دایرکتوری داده"""
    os.makedirs(DATA_DIR, exist_ok=True)


def ensure_file_exists(file_path: str, columns: List[str]) -> None:
    """اطمینان از وجود فایل با هدرهای مشخص"""
    ensure_data_dir()
    if not os.path.exists(file_path):
        pd.DataFrame(columns=columns).to_csv(file_path, index=False)


# ============================================
# ذخیره و بارگذاری تاریخچه قیمت
# ============================================
def append_price(price: float, timestamp: Optional[datetime] = None) -> None:
    """
    یک رکورد قیمت جدید را به فایل تاریخچه اضافه می‌کند.
    
    Args:
        price: قیمت به ریال
        timestamp: زمان (اگر None نباشد، از زمان فعلی استفاده می‌شود)
    """
    ensure_data_dir()
    timestamp = timestamp or datetime.now(timezone.utc)
    
    # تبدیل به منطقه زمانی ایران برای ذخیره‌سازی
    from zoneinfo import ZoneInfo
    iran_time = timestamp.astimezone(ZoneInfo("Asia/Tehran"))
    
    row = pd.DataFrame([{
        "timestamp": iran_time.isoformat(),
        "price": price
    }])

    if os.path.exists(HISTORY_FILE):
        row.to_csv(HISTORY_FILE, mode="a", header=False, index=False)
    else:
        row.to_csv(HISTORY_FILE, mode="w", header=True, index=False)


def load_history() -> pd.DataFrame:
    """
    تاریخچه قیمت را به‌صورت DataFrame با ایندکس زمانی برمی‌گرداند.
    
    Returns:
        DataFrame با ایندکس زمانی (منطقه زمانی ایران)
    """
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=COLUMNS).set_index("timestamp")

    try:
        df = pd.read_csv(HISTORY_FILE)
        if df.empty:
            return pd.DataFrame(columns=COLUMNS).set_index("timestamp")

        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp")
        df = df.set_index("timestamp")
        return df
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری تاریخچه: {e}")
        return pd.DataFrame(columns=COLUMNS).set_index("timestamp")


def get_previous_price() -> Optional[float]:
    """
    دریافت قیمت قبلی (آخرین قیمت قبل از قیمت فعلی)
    
    Returns:
        float: قیمت قبلی یا None اگر وجود نداشته باشد
    """
    history = load_history()
    if len(history) < 2:
        return None
    return history["price"].iloc[-2]


def get_last_price() -> Optional[float]:
    """
    دریافت آخرین قیمت ذخیره‌شده
    
    Returns:
        float: آخرین قیمت یا None اگر وجود نداشته باشد
    """
    history = load_history()
    if history.empty:
        return None
    return history["price"].iloc[-1]


def get_price_by_index(index: int = -1) -> Optional[float]:
    """
    دریافت قیمت در ایندکس مشخص
    
    Args:
        index: ایندکس (مثلاً -1 برای آخرین، -2 برای قبلی)
    
    Returns:
        float: قیمت یا None اگر وجود نداشته باشد
    """
    history = load_history()
    if len(history) < abs(index):
        return None
    return history["price"].iloc[index]


def get_history_for_period(days: int = 30) -> pd.DataFrame:
    """
    دریافت تاریخچه برای یک بازه زمانی مشخص
    
    Args:
        days: تعداد روزهای گذشته
    
    Returns:
        DataFrame با تاریخچه محدود شده
    """
    history = load_history()
    if history.empty:
        return history
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return history[history.index >= cutoff]


def trim_history(max_rows: int = 20000) -> None:
    """
    برای جلوگیری از رشد بی‌رویه‌ی فایل تاریخچه، تعداد ردیف‌ها را محدود می‌کند.
    
    Args:
        max_rows: حداکثر تعداد ردیف‌ها
    """
    df = load_history()
    if len(df) > max_rows:
        df = df.iloc[-max_rows:]
        ensure_data_dir()
        df.reset_index().to_csv(HISTORY_FILE, index=False)
        print(f"✅ تاریخچه به {max_rows} ردیف محدود شد")


def trim_history_by_date(days: int = 90) -> None:
    """
    حذف تاریخچه‌های قدیمی‌تر از تعداد روز مشخص
    
    Args:
        days: تعداد روزهایی که نگهداری شوند
    """
    df = load_history()
    if df.empty:
        return
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    df_filtered = df[df.index >= cutoff]
    
    if len(df_filtered) < len(df):
        ensure_data_dir()
        df_filtered.reset_index().to_csv(HISTORY_FILE, index=False)
        print(f"✅ تاریخچه به {days} روز محدود شد (حذف {len(df) - len(df_filtered)} ردیف)")


# ============================================
# ذخیره و بارگذاری سیگنال‌ها (جدید)
# ============================================
def save_signal(signal_data: Dict[str, Any]) -> None:
    """
    ذخیره سیگنال تولید شده برای بررسی دقت در آینده
    
    Args:
        signal_data: دیکشنری شامل signal, price, trend, confidence و ...
    """
    ensure_data_dir()
    
    # ایجاد فایل اگر وجود نداشت
    if not os.path.exists(RESULTS_FILE):
        pd.DataFrame(columns=SIGNAL_COLUMNS).to_csv(RESULTS_FILE, index=False)
    
    # زمان فعلی به منطقه زمانی ایران
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo("Asia/Tehran"))
    
    row = pd.DataFrame([{
        "timestamp": now.isoformat(),
        "price": signal_data.get("price", 0),
        "signal": signal_data.get("signal", "WAIT"),
        "signal_text": signal_data.get("signal_text", ""),
        "confidence": signal_data.get("signal_confidence", 0),
        "trend": signal_data.get("trend", ""),
    }])
    
    row.to_csv(RESULTS_FILE, mode="a", header=False, index=False)
    print(f"✅ سیگنال در {RESULTS_FILE} ذخیره شد")


def load_signals() -> pd.DataFrame:
    """
    بارگذاری تاریخچه سیگنال‌ها
    
    Returns:
        DataFrame با تاریخچه سیگنال‌ها
    """
    if not os.path.exists(RESULTS_FILE):
        return pd.DataFrame(columns=SIGNAL_COLUMNS)
    
    try:
        df = pd.read_csv(RESULTS_FILE)
        if df.empty:
            return pd.DataFrame(columns=SIGNAL_COLUMNS)
        
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp")
        return df
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری سیگنال‌ها: {e}")
        return pd.DataFrame(columns=SIGNAL_COLUMNS)


def get_signal_stats() -> Dict[str, Any]:
    """
    دریافت آمار سیگنال‌های ذخیره‌شده
    
    Returns:
        dict: {'total': int, 'buy': int, 'sell': int, 'wait': int, 'avg_confidence': float}
    """
    df = load_signals()
    if df.empty:
        return {
            "total": 0,
            "buy": 0,
            "sell": 0,
            "wait": 0,
            "avg_confidence": 0,
            "latest": None
        }
    
    # آمار
    stats = {
        "total": len(df),
        "buy": len(df[df["signal"] == "BUY"]),
        "sell": len(df[df["signal"] == "SELL"]),
        "wait": len(df[df["signal"] == "WAIT"]),
        "avg_confidence": df["confidence"].mean() if "confidence" in df else 0,
        "latest": df.iloc[-1].to_dict() if not df.empty else None
    }
    
    return stats


# ============================================
# پاک‌سازی و نگهداری
# ============================================
def cleanup_old_files(days: int = 30) -> None:
    """
    پاک‌سازی فایل‌های قدیمی (اختیاری)
    """
    # حذف تاریخچه قدیمی
    trim_history_by_date(days)
    
    # حذف سیگنال‌های قدیمی (اگر بیش از حد باشند)
    signals = load_signals()
    if len(signals) > 1000:
        signals = signals.iloc[-1000:]
        ensure_data_dir()
        signals.reset_index().to_csv(RESULTS_FILE, index=False)
        print("✅ سیگنال‌های قدیمی پاک‌سازی شدند")


# ============================================
# تست
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("📊 تست ذخیره‌سازی")
    print("=" * 60)
    
    # تست ذخیره قیمت
    test_price = 35_000_000
    append_price(test_price)
    print(f"✅ قیمت {test_price:,.0f} ذخیره شد")
    
    # تست بارگذاری
    history = load_history()
    print(f"📊 تعداد رکوردها: {len(history)}")
    
    if len(history) >= 2:
        last = get_last_price()
        prev = get_previous_price()
        print(f"💰 آخرین قیمت: {last:,.0f}")
        print(f"💰 قیمت قبلی: {prev:,.0f}")
        if prev and last:
            change = ((last - prev) / prev) * 100
            print(f"📊 تغییر: {change:.2f}%")
    
    # تست ذخیره سیگنال
    test_signal = {
        "price": 35_000_000,
        "signal": "BUY",
        "signal_text": "خرید",
        "signal_confidence": 75,
        "trend": "صعودی"
    }
    save_signal(test_signal)
    print("✅ سیگنال تست ذخیره شد")
    
    # تست آمار
    stats = get_signal_stats()
    print(f"📊 آمار سیگنال‌ها: {stats}")
