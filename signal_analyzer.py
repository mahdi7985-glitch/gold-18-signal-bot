from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from config import (
    RSI_OVERBOUGHT, RSI_OVERSOLD, ADX_THRESHOLD,
    EMA_FAST, EMA_SLOW
)


# ============================================
# دیتاکلاس سیگنال (ساده‌شده)
# ============================================
@dataclass
class SignalResult:
    """نتیجه تحلیل سیگنال"""
    signal: str  # BUY, SELL, WAIT
    signal_text: str  # متن ساده فارسی
    signal_emoji: str  # ایموجی
    signal_reason: str  # دلیل یک‌خطی
    signal_confidence: int  # درصد اطمینان (۰-۱۰۰)
    trend: str  # روند کلی
    indicators: Dict[str, Any] = field(default_factory=dict)


# ============================================
# توابع تشخیص واگرایی RSI
# ============================================
def find_rsi_divergence(df: pd.DataFrame, lookback: int = 20) -> Dict[str, Any]:
    """
    تشخیص واگرایی RSI با قوانین کامل
    
    Returns:
        dict: {
            'type': 'bullish' | 'bearish' | 'none',
            'description': 'توضیح ساده',
            'strength': 0-100
        }
    """
    if len(df) < lookback:
        return {"type": "none", "description": "داده کافی نیست", "strength": 0}
    
    close = df["close"].values
    rsi_vals = df["rsi"].values
    length = len(close)
    
    peaks = []    # (اندیس, قیمت, RSI)
    troughs = []  # (اندیس, قیمت, RSI)
    
    # پیدا کردن قله‌ها و دره‌های محلی
    for i in range(2, length - 2):
        # قله: RSI بالای ۷۰ و بالاتر از همسایه‌ها
        if rsi_vals[i] > RSI_OVERBOUGHT and rsi_vals[i] > rsi_vals[i-1] and rsi_vals[i] > rsi_vals[i+1]:
            peaks.append((i, close[i], rsi_vals[i]))
        
        # دره: RSI زیر ۳۰ و پایین‌تر از همسایه‌ها
        if rsi_vals[i] < RSI_OVERSOLD and rsi_vals[i] < rsi_vals[i-1] and rsi_vals[i] < rsi_vals[i+1]:
            troughs.append((i, close[i], rsi_vals[i]))
    
    # ===== واگرایی منفی (قیمت بالاتر میرود ولی RSI پایین‌تر) =====
    if len(peaks) >= 2:
        p1, p2 = peaks[-2], peaks[-1]
        # شرط: قیمت بالاتر، RSI پایین‌تر، فاصله حداقل ۵ کندل
        if p2[1] > p1[1] and p2[2] < p1[2] and (p2[0] - p1[0]) >= 5:
            # محاسبه قدرت واگرایی (تفاوت RSI)
            strength = min(100, int((p1[2] - p2[2]) * 5))
            return {
                "type": "bearish",
                "description": "قیمت سقف جدید زده ولی RSI پایین‌تر آمده (ضعف خریدار)",
                "strength": strength
            }
    
    # ===== واگرایی مثبت (قیمت پایین‌تر میرود ولی RSI بالاتر) =====
    if len(troughs) >= 2:
        t1, t2 = troughs[-2], troughs[-1]
        # شرط: قیمت پایین‌تر، RSI بالاتر، فاصله حداقل ۵ کندل
        if t2[1] < t1[1] and t2[2] > t1[2] and (t2[0] - t1[0]) >= 5:
            strength = min(100, int((t2[2] - t1[2]) * 5))
            return {
                "type": "bullish",
                "description": "قیمت کف جدید زده ولی RSI بالاتر آمده (ضعف فروشنده)",
                "strength": strength
            }
    
    return {"type": "none", "description": "واگرایی تشخیص داده نشد", "strength": 0}


# ============================================
# تابع تشخیص روند با EMA
# ============================================
def detect_trend(row: pd.Series) -> Dict[str, Any]:
    """
    تشخیص روند با استفاده از EMA 20 و 50
    
    Returns:
        dict: {'trend': 'صعودی'|'نزولی'|'خنثی', 'strength': 0-100}
    """
    price = row["close"]
    ema_fast = row["ema_fast"]
    ema_slow = row["ema_slow"]
    
    # فاصله قیمت از EMA ها
    price_above_fast = price > ema_fast
    price_above_slow = price > ema_slow
    fast_above_slow = ema_fast > ema_slow
    
    # محاسبه قدرت روند (بر اساس فاصله از EMA 50)
    if ema_slow > 0:
        distance_pct = abs((price - ema_slow) / ema_slow) * 100
        strength = min(100, int(distance_pct * 2))
    else:
        strength = 50
    
    # تشخیص روند
    if price_above_fast and price_above_slow and fast_above_slow:
        if strength > 60:
            return {"trend": "صعودی قوی", "strength": strength}
        return {"trend": "صعودی", "strength": strength}
    
    if not price_above_fast and not price_above_slow and not fast_above_slow:
        if strength > 60:
            return {"trend": "نزولی قوی", "strength": strength}
        return {"trend": "نزولی", "strength": strength}
    
    return {"trend": "خنثی", "strength": strength}


# ============================================
# تابع اصلی تحلیل سیگنال
# ============================================
def analyze(df: pd.DataFrame, chat_id: Optional[str] = None) -> Dict[str, Any]:
    """
    تحلیل کامل با مدل جدید
    
    Args:
        df: DataFrame با اندیکاتورهای محاسبه‌شده
        chat_id: برای لاگ (اختیاری)
    
    Returns:
        dict: {
            'signal': 'BUY'|'SELL'|'WAIT',
            'signal_text': '...',
            'signal_emoji': '...',
            'signal_reason': '...',
            'signal_confidence': 0-100,
            'trend': '...',
            'indicators': {...}
        }
    """
    if df.empty or len(df) < 10:
        return {
            "signal": "WAIT",
            "signal_text": "صبر کن",
            "signal_emoji": "⚪",
            "signal_reason": "داده کافی برای تحلیل وجود ندارد",
            "signal_confidence": 0,
            "trend": "خنثی",
            "indicators": {}
        }
    
    # آخرین ردیف
    row = df.iloc[-1]
    
    # ===== ۱. تشخیص روند =====
    trend_result = detect_trend(row)
    trend = trend_result["trend"]
    
    # ===== ۲. تشخیص واگرایی =====
    divergence = find_rsi_divergence(df)
    div_type = divergence["type"]
    div_desc = divergence["description"]
    div_strength = divergence["strength"]
    
    # ===== ۳. بررسی شرایط =====
    rsi = row["rsi"]
    adx = row["adx"]
    macd_hist = row["macd_hist"]
    macd = row["macd"]
    macd_signal = row["macd_signal"]
    
    # وضعیت‌ها
    is_overbought = rsi > RSI_OVERBOUGHT
    is_oversold = rsi < RSI_OVERSOLD
    is_strong_trend = adx > ADX_THRESHOLD
    is_bullish_trend = "صعودی" in trend
    is_bearish_trend = "نزولی" in trend
    macd_bullish = macd_hist > 0 and macd > macd_signal
    macd_bearish = macd_hist < 0 and macd < macd_signal
    
    # ===== ۴. تولید سیگنال =====
    signal = "WAIT"
    signal_text = "صبر کن"
    signal_emoji = "⚪"
    signal_reason = "هیچ سیگنالی تشخیص داده نشد"
    confidence = 0
    
    # === سیگنال خرید ===
    if div_type == "bullish" and is_oversold and is_strong_trend and is_bullish_trend and macd_bullish:
        signal = "BUY"
        signal_text = "خرید"
        signal_emoji = "🟢"
        confidence = min(100, 60 + div_strength // 2 + 10)
        signal_reason = f"✅ واگرایی مثبت + RSI اشباع فروش ({rsi:.0f}) + ADX قوی ({adx:.0f})"
    
    # === سیگنال خرید محتاطانه ===
    elif div_type == "bullish" and is_oversold and is_bullish_trend:
        signal = "BUY_CAUTIOUS"
        signal_text = "خرید محتاطانه"
        signal_emoji = "🟡"
        confidence = min(100, 40 + div_strength // 2)
        signal_reason = f"🟡 واگرایی مثبت + RSI اشباع فروش ({rsi:.0f}) (ADX ضعیف، احتیاط)"
    
    # === سیگنال فروش ===
    elif div_type == "bearish" and is_overbought and is_strong_trend and is_bearish_trend and macd_bearish:
        signal = "SELL"
        signal_text = "فروش"
        signal_emoji = "🔴"
        confidence = min(100, 60 + div_strength // 2 + 10)
        signal_reason = f"❌ واگرایی منفی + RSI اشباع خرید ({rsi:.0f}) + ADX قوی ({adx:.0f})"
    
    # === سیگنال فروش محتاطانه ===
    elif div_type == "bearish" and is_overbought and is_bearish_trend:
        signal = "SELL_CAUTIOUS"
        signal_text = "فروش محتاطانه"
        signal_emoji = "🟠"
        confidence = min(100, 40 + div_strength // 2)
        signal_reason = f"🟠 واگرایی منفی + RSI اشباع خرید ({rsi:.0f}) (ADX ضعیف، احتیاط)"
    
    # ===== ۵. ساخت خروجی =====
    return {
        "signal": signal,
        "signal_text": signal_text,
        "signal_emoji": signal_emoji,
        "signal_reason": signal_reason,
        "signal_confidence": confidence,
        "trend": trend,
        "indicators": {
            "ema_fast": row["ema_fast"],
            "ema_slow": row["ema_slow"],
            "rsi": row["rsi"],
            "macd": row["macd"],
            "macd_signal": row["macd_signal"],
            "macd_hist": row["macd_hist"],
            "adx": row["adx"],
        },
        # اطلاعات اضافی برای دیباگ
        "_debug": {
            "divergence": div_type,
            "divergence_desc": div_desc,
            "is_overbought": is_overbought,
            "is_oversold": is_oversold,
            "is_strong_trend": is_strong_trend,
            "macd_bullish": macd_bullish,
            "macd_bearish": macd_bearish,
        }
    }


# ============================================
# تابع تحلیل ساده برای استفاده در main
# ============================================
def analyze_signal(row: pd.Series) -> Dict[str, Any]:
    """
    تحلیل سیگنال با یک ردیف (سازگاری با کد قدیمی)
    """
    # ساخت دیتافریم موقت
    df = pd.DataFrame([row])
    # محاسبه اندیکاتورهای موردنیاز برای واگرایی (نیاز به تاریخچه دارد)
    # این تابع فقط برای سازگاری با کد قدیمی است
    return {
        "signal": "WAIT",
        "signal_text": "صبر کن",
        "signal_emoji": "⚪",
        "signal_reason": "برای تحلیل نیاز به تاریخچه کامل داریم",
        "signal_confidence": 0,
        "trend": "خنثی",
        "indicators": {
            "ema_fast": row.get("ema_fast", 0),
            "ema_slow": row.get("ema_slow", 0),
            "rsi": row.get("rsi", 50),
            "macd": row.get("macd", 0),
            "macd_signal": row.get("macd_signal", 0),
            "macd_hist": row.get("macd_hist", 0),
            "adx": row.get("adx", 0),
        }
        }
