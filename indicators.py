import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator
from typing import Optional, Tuple, Dict, Any

import config


# ============================================
# ساخت کندل‌های OHLC
# ============================================
def build_ohlc_candles(price_series: pd.Series, rule: str = config.RESAMPLE_RULE) -> pd.DataFrame:
    """
    سری قیمت خام را به کندل‌های OHLC در بازه‌ی مشخص تبدیل می‌کند.
    
    Args:
        price_series: سری قیمت‌های خام (با ایندکس زمانی)
        rule: بازه زمانی (مثلاً '4h' برای ۴ ساعته)
    
    Returns:
        DataFrame با ستون‌های: open, high, low, close
    """
    ohlc = price_series.resample(rule).ohlc()
    ohlc = ohlc.dropna(subset=["close"])
    return ohlc


# ============================================
# محاسبه اندیکاتورها (مدل جدید)
# ============================================
def compute_indicators(candles: pd.DataFrame) -> pd.DataFrame:
    """
    محاسبه اندیکاتورهای موردنیاز با Lengthهای جدید.
    
    اندیکاتورها:
    - EMA 20 (سریع)
    - EMA 50 (کند - خط آتش)
    - RSI 10
    - MACD (10, 22, 8)
    - ADX 14
    
    Args:
        candles: DataFrame با ستون‌های: open, high, low, close
    
    Returns:
        DataFrame با اندیکاتورهای اضافه‌شده
    """
    df = candles.copy()
    close, high, low = df["close"], df["high"], df["low"]

    # ========== EMA 20 و 50 ==========
    df["ema_fast"] = EMAIndicator(close, window=config.EMA_FAST).ema_indicator()
    df["ema_slow"] = EMAIndicator(close, window=config.EMA_SLOW).ema_indicator()

    # ========== RSI با Length 10 ==========
    rsi = RSIIndicator(close, window=config.RSI_LENGTH)
    df["rsi"] = rsi.rsi()

    # ========== MACD (10, 22, 8) ==========
    macd = MACD(
        close,
        window_fast=config.MACD_FAST,
        window_slow=config.MACD_SLOW,
        window_sign=config.MACD_SIGNAL,
    )
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_hist"] = macd.macd_diff()

    # ========== ADX 14 ==========
    adx = ADXIndicator(high, low, close, window=config.ADX_LENGTH)
    df["adx"] = adx.adx()

    return df


# ============================================
# دریافت آخرین اندیکاتورها
# ============================================
def get_latest_indicators(price_series: pd.Series) -> Optional[Tuple[pd.Series, pd.DataFrame]]:
    """
    آخرین ردیف کامل اندیکاتورها را به‌همراه کل DataFrame برمی‌گرداند.
    
    Args:
        price_series: سری قیمت‌های خام
    
    Returns:
        (last_row, full_dataframe) یا None اگر داده کافی نباشد
    """
    candles = build_ohlc_candles(price_series)
    
    if len(candles) < config.MIN_CANDLES_REQUIRED:
        return None

    df = compute_indicators(candles)
    
    # حذف ردیف‌های دارای NaN
    required_cols = ["ema_fast", "ema_slow", "rsi", "macd", "macd_signal", "macd_hist", "adx"]
    df_valid = df.dropna(subset=required_cols)
    
    if df_valid.empty:
        return None

    return df_valid.iloc[-1], df_valid


# ============================================
# دریافت تحلیل کامل (برای main)
# ============================================
def get_latest_analysis(price_series: pd.Series) -> Dict[str, Any]:
    """
    دریافت تحلیل کامل با تمام اندیکاتورها و وضعیت‌ها.
    
    Args:
        price_series: سری قیمت‌های خام
    
    Returns:
        dict: {
            'error': str (اگر خطایی باشد),
            'indicators': {...},
            'trend': 'صعودی'|'نزولی'|'خنثی',
            'rsi_status': 'اشباع خرید'|'اشباع فروش'|'متعادل',
            'adx_status': 'قوی'|'ضعیف',
            'macd_status': 'صعودی'|'نزولی'|'خنثی',
        }
    """
    result = get_latest_indicators(price_series)
    
    if result is None:
        return {"error": f"داده کافی نیست (حداقل {config.MIN_CANDLES_REQUIRED} کندل)"}
    
    last_row, df = result
    
    # ===== تشخیص وضعیت‌ها =====
    # روند با EMA
    if last_row["close"] > last_row["ema_fast"] and last_row["ema_fast"] > last_row["ema_slow"]:
        trend = "صعودی"
    elif last_row["close"] < last_row["ema_fast"] and last_row["ema_fast"] < last_row["ema_slow"]:
        trend = "نزولی"
    else:
        trend = "خنثی"
    
    # وضعیت RSI
    if last_row["rsi"] > config.RSI_OVERBOUGHT:
        rsi_status = "اشباع خرید"
    elif last_row["rsi"] < config.RSI_OVERSOLD:
        rsi_status = "اشباع فروش"
    else:
        rsi_status = "متعادل"
    
    # وضعیت ADX
    adx_status = "قوی" if last_row["adx"] > config.ADX_THRESHOLD else "ضعیف"
    
    # وضعیت MACD
    if last_row["macd_hist"] > 0 and last_row["macd"] > last_row["macd_signal"]:
        macd_status = "صعودی"
    elif last_row["macd_hist"] < 0 and last_row["macd"] < last_row["macd_signal"]:
        macd_status = "نزولی"
    else:
        macd_status = "خنثی"
    
    return {
        "error": None,
        "indicators": {
            "ema_fast": last_row["ema_fast"],
            "ema_slow": last_row["ema_slow"],
            "rsi": last_row["rsi"],
            "macd": last_row["macd"],
            "macd_signal": last_row["macd_signal"],
            "macd_hist": last_row["macd_hist"],
            "adx": last_row["adx"],
        },
        "trend": trend,
        "rsi_status": rsi_status,
        "adx_status": adx_status,
        "macd_status": macd_status,
        "last_row": last_row,
        "df": df,
    }


# ============================================
# تابع کمکی برای دریافت آخرین قیمت
# ============================================
def get_last_price(price_series: pd.Series) -> Optional[float]:
    """دریافت آخرین قیمت از سری قیمت"""
    if price_series.empty:
        return None
    return price_series.iloc[-1]


# ============================================
# تابع کمکی برای دریافت قیمت قبلی
# ============================================
def get_previous_price(price_series: pd.Series) -> Optional[float]:
    """دریافت قیمت قبلی از سری قیمت"""
    if len(price_series) < 2:
        return None
    return price_series.iloc[-2]
