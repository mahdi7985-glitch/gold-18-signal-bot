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
                "description": "قیمت سقف جدید زده ولی قدرت خریدار کم شده (ضعف)",
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
                "description": "قیمت کف جدید زده ولی قدرت فروشنده کم شده (ضعف)",
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
# تابع تولید پیام دوستانه
# ============================================
def generate_friendly_signal(analysis_result: Dict[str, Any]) -> Dict[str, str]:
    """
    تبدیل تحلیل به متن دوستانه برای کاربر
    
    Args:
        analysis_result: خروجی تابع analyze
    
    Returns:
        dict: {
            'friendly_message': 'متن صمیمی',
            'simple_reason': 'دلیل ساده',
            'advice': 'توصیه عملی'
        }
    """
    signal = analysis_result.get("signal", "WAIT")
    signal_text = analysis_result.get("signal_text", "صبر کن")
    confidence = analysis_result.get("signal_confidence", 0)
    trend = analysis_result.get("trend", "خنثی")
    indicators = analysis_result.get("indicators", {})
    
    rsi = indicators.get("rsi", 50)
    adx = indicators.get("adx", 0)
    macd_hist = indicators.get("macd_hist", 0)
    
    # پیام‌های دوستانه بر اساس سیگنال
    friendly_messages = {
        "BUY": "🚀 رفیق، امروز روز خوبیه برای خرید! همه چیز داره هموار میشه. ولی یادت باشه هیچوقت یه‌دفعه همه سرمایه‌ات رو نریزی تو کار.",
        "BUY_CAUTIOUS": "🟡 امروز به خرید مایل‌ترم، ولی با احتیاط! صبر کن تا سیگنال قوی‌تر بشه یا با یه چهارم سرمایه شروع کن.",
        "SELL": "⚠️ راستش امروز اوضاع خوش‌یمن نیست. اگه طلا داری، شاید بهتر باشه یه کم بفروشی و نقد شی. ولی این تصمیم با خودته.",
        "SELL_CAUTIOUS": "🟠 امروز کمی نگران‌کننده‌ست. اگه طلا داری، شاید بهتر باشه یه کم صبر کنی ببینی چی میشه. عجله نکن.",
        "WAIT": "🤔 امروز یه وضعیت دو پهلو داریم. من که دست نگه می‌دارم، تو هم عجله نکن. فردا صبح دوباره چک می‌کنیم.",
    }
    
    # توضیح ساده دلایل
    reasons = []
    
    # RSI
    if rsi > 70:
        reasons.append(f"بازار داغ شده (RSI: {rsi:.0f})، ممکنه برگرده پایین")
    elif rsi < 30:
        reasons.append(f"بازار سرده (RSI: {rsi:.0f})، ممکنه برگرده بالا")
    else:
        reasons.append(f"بازار متعادله (RSI: {rsi:.0f})")
    
    # ADX
    if adx > 25:
        reasons.append(f"روند با قدرت خوبی حرکت میکنه (ADX: {adx:.0f})")
    else:
        reasons.append(f"روند مشخصی نداریم (ADX: {adx:.0f})")
    
    # MACD
    if macd_hist > 0:
        reasons.append("فشار خریدار بیشتره (مکدی مثبت)")
    else:
        reasons.append("فشار فروشنده بیشتره (مکدی منفی)")
    
    # روند
    if "صعودی" in trend:
        reasons.append(f"روند کلی {trend} هست")
    elif "نزولی" in trend:
        reasons.append(f"روند کلی {trend} هست")
    else:
        reasons.append("روند کلی مشخص نیست")
    
    # ترکیب دلیل ساده
    simple_reason = " • ".join(reasons[:3])
    if len(reasons) > 3:
        simple_reason += f" • و {len(reasons)-3} مورد دیگه..."
    
    # توصیه عملی
    if "BUY" in signal:
        advice = "💡 پیشنهاد: با یه چهارم سرمایه شروع کن و اگه قیمت رفت پایین‌تر، میانگین بگیر."
    elif "SELL" in signal:
        advice = "💡 پیشنهاد: اگه سود خوبی داری، حداقل یه بخشی رو بفروش و نقد کن."
    else:
        advice = "💡 پیشنهاد: دست نگه دار و فردا دوباره چک کن."
    
    return {
        'friendly_message': friendly_messages.get(signal, "🟡 صبر کن، فعلاً وقتش نیست."),
        'simple_reason': simple_reason,
        'advice': advice,
    }


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
            "trend_simple": "خنثی",
            "indicators": {}
        }
    
    # آخرین ردیف
    row = df.iloc[-1]
    
    # ===== ۱. تشخیص روند =====
    trend_result = detect_trend(row)
    trend = trend_result["trend"]
    trend_simple = "صعودی" if "صعودی" in trend else "نزولی" if "نزولی" in trend else "خنثی"
    
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
        signal_reason = f"قیمت کف جدید زده ولی قدرت فروشنده کم شده (واگرایی مثبت) + RSI خیلی پایین اومده ({rsi:.0f}) + روند کلی صعودیه"
    
    # === سیگنال خرید محتاطانه ===
    elif div_type == "bullish" and is_oversold and is_bullish_trend:
        signal = "BUY_CAUTIOUS"
        signal_text = "خرید محتاطانه"
        signal_emoji = "🟡"
        confidence = min(100, 40 + div_strength // 2)
        signal_reason = f"قیمت کف جدید زده ولی قدرت فروشنده کم شده (واگرایی مثبت) + RSI خیلی پایین اومده ({rsi:.0f}) ولی ADX قوی نیست (احتیاط)"
    
    # === سیگنال فروش ===
    elif div_type == "bearish" and is_overbought and is_strong_trend and is_bearish_trend and macd_bearish:
        signal = "SELL"
        signal_text = "فروش"
        signal_emoji = "🔴"
        confidence = min(100, 60 + div_strength // 2 + 10)
        signal_reason = f"قیمت سقف جدید زده ولی قدرت خریدار کم شده (واگرایی منفی) + RSI خیلی بالا رفته ({rsi:.0f}) + روند کلی نزولیه"
    
    # === سیگنال فروش محتاطانه ===
    elif div_type == "bearish" and is_overbought and is_bearish_trend:
        signal = "SELL_CAUTIOUS"
        signal_text = "فروش محتاطانه"
        signal_emoji = "🟠"
        confidence = min(100, 40 + div_strength // 2)
        signal_reason = f"قیمت سقف جدید زده ولی قدرت خریدار کم شده (واگرایی منفی) + RSI خیلی بالا رفته ({rsi:.0f}) ولی ADX قوی نیست (احتیاط)"
    
    # ===== ۵. ساخت خروجی =====
    return {
        "signal": signal,
        "signal_text": signal_text,
        "signal_emoji": signal_emoji,
        "signal_reason": signal_reason,
        "signal_confidence": confidence,
        "trend": trend,
        "trend_simple": trend_simple,
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


def analyze_with_friendly(df: pd.DataFrame, chat_id: Optional[str] = None) -> Dict[str, Any]:
    """
    تحلیل کامل با خروجی دوستانه
    
    Returns:
        dict: ترکیبی از تحلیل و خروجی دوستانه
    """
    # تحلیل اصلی
    result = analyze(df, chat_id)
    
    # افزودن خروجی دوستانه
    friendly = generate_friendly_signal(result)
    result['friendly'] = friendly
    
    return result


def analyze_signal(row: pd.Series) -> Dict[str, Any]:
    """
    تحلیل سیگنال با یک ردیف (سازگاری با کد قدیمی)
    """
    # ساخت دیتافریم موقت
    df = pd.DataFrame([row])
    return {
        "signal": "WAIT",
        "signal_text": "صبر کن",
        "signal_emoji": "⚪",
        "signal_reason": "برای تحلیل نیاز به تاریخچه کامل داریم",
        "signal_confidence": 0,
        "trend": "خنثی",
        "trend_simple": "خنثی",
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


# ============================================
# تست
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("📊 تست تحلیل سیگنال")
    print("=" * 60)
    
    # ساخت داده تست
    import numpy as np
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='1h')
    prices = 35000000 + np.cumsum(np.random.randn(100) * 20000)
    
    # ساخت دیتافریم با اندیکاتورهای ساده
    df = pd.DataFrame({
        'close': prices,
        'high': prices * 1.002,
        'low': prices * 0.998,
        'ema_fast': prices * 0.98 + 50000,
        'ema_slow': prices * 0.95 + 100000,
        'rsi': 50 + np.cumsum(np.random.randn(100) * 2),
        'macd': np.cumsum(np.random.randn(100) * 0.5),
        'macd_signal': np.cumsum(np.random.randn(100) * 0.3),
        'macd_hist': np.cumsum(np.random.randn(100) * 0.2),
        'adx': 20 + np.random.randn(100) * 10,
    })
    
    # تنظیم RSI آخرین ردیف برای تست
    df.loc[df.index[-1], 'rsi'] = 25  # اشباع فروش
    
    # تست تحلیل
    result = analyze_with_friendly(df)
    
    print(f"📊 سیگنال: {result['signal_text']} ({result['signal_confidence']}%)")
    print(f"📈 روند: {result['trend']}")
    print(f"📌 دلیل: {result['signal_reason']}")
    print(f"\n💬 {result['friendly']['friendly_message']}")
    print(f"📝 {result['friendly']['simple_reason']}")
    print(f"💡 {result['friendly']['advice']}")
