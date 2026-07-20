from dataclasses import dataclass, field
import pandas as pd


@dataclass
class SignalResult:
    trend: str
    strength: int
    reasons: list = field(default_factory=list)


def _score_macd(row):
    diff = row["macd_hist"]
    threshold = abs(row["macd"])  0.15
    if diff > 0 and row["macd"] > row["macd_signal"]:
        return (2 if diff > threshold else 1), "MACD بالای خط سیگنال (مومنتوم صعودی)"
    if diff < 0 and row["macd"] < row["macd_signal"]:
        return (-2 if abs(diff) > threshold else -1), "MACD زیر خط سیگنال (مومنتوم نزولی)"
    return 0, "MACD در وضعیت خنثی/تقاطع"


def _score_rsi(row):
    rsi = row["rsi"]
    if rsi >= 70:
        return -1, f"RSI={rsi:.1f} در محدوده اشباع خرید (احتمال اصلاح)"
    if rsi <= 30:
        return 1, f"RSI={rsi:.1f} در محدوده اشباع فروش (احتمال برگشت)"
    if rsi > 55:
        return 1, f"RSI={rsi:.1f} تمایل صعودی"
    if rsi < 45:
        return -1, f"RSI={rsi:.1f} تمایل نزولی"
    return 0, f"RSI={rsi:.1f} خنثی"


def _score_ma_cross(row):
    price, sma, ema = row["close"], row["sma"], row["ema"]
    if price > ema > sma:
        return 2, "قیمت بالای EMA و EMA بالای SMA (روند صعودی)"
    if price < ema < sma:
        return -2, "قیمت زیر EMA و EMA زیر SMA (روند نزولی)"
    if price > sma:
        return 1, "قیمت بالای میانگین متحرک ساده"
    if price < sma:
        return -1, "قیمت زیر میانگین متحرک ساده"
    return 0, "قیمت نزدیک میانگین‌های متحرک"


def _score_bbands(row):
    pct = row["bb_percent"]
    if pct >= 1:
        return -1, "قیمت بالای باند بالایی بولینگر (احتمال اصلاح)"
    if pct <= 0:
        return 1, "قیمت زیر باند پایینی بولینگر (احتمال برگشت)"
    if pct > 0.8:
        return -0.5, "قیمت نزدیک باند بالایی بولینگر"
    if pct < 0.2:
        return 0.5, "قیمت نزدیک باند پایینی بولینگر"
    return 0, "قیمت در میانه باندهای بولینگر"


def _adx_strength_multiplier(row):
    adx = row["adx"]
    if adx >= 40:
        return 1.3, f"ADX={adx:.1f} روند بسیار قوی"
    if adx >= 25:
        return 1.15, f"ADX={adx:.1f} روند قابل‌اتکا"
    if adx >= 15:
        return 1.0, f"ADX={adx:.1f} روند متوسط"
    return 0.7, f"ADX={adx:.1f} روند ضعیف/بدون روند مشخص"


def _volatility_note(row):
    atr = row["atr"]
    atr_pct = (atr / row["close"])  100 if row["close"] else 0
    return f"ATR={atr:,.0f} (~{atr_pct:.2f}% از قیمت) به‌عنوان معیار نوسان"


def analyze(row) -> SignalResult:
    reasons = []
    total_score = 0.0
    max_possible = 0.0

    for score_fn, weight in (
        (_score_macd, 2),
        (_score_rsi, 1.5),
        (_score_ma_cross, 2),
        (_score_bbands, 1),
    ):
        score, reason = score_fn(row)
        total_score += score  weight
        max_possible += 2  weight
        reasons.append(reason)

    multiplier, adx_reason = _adx_strength_multiplier(row)
    reasons.append(adx_reason)
    reasons.append(_volatility_note(row))

    total_score = total_score  multiplier

    normalized = max(-1.0, min(1.0, total_score / max_possible)) if max_possible else 0.0
    strength = round(abs(normalized)  100)

    if normalized >= 0.5:
        trend = "صعودی قوی"
    elif normalized >= 0.15:
        trend = "صعودی"
    elif normalized <= -0.5:
        trend = "نزولی قوی"
    elif normalized <= -0.15:
        trend = "نزولی"
    else:
        trend = "خنثی"

    return SignalResult(trend=trend, strength=strength, reasons=reasons)
