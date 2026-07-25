import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator

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
# محاسبه اندیکاتورها
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
    
    # حذف ردی
