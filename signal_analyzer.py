def analyze_signal(indicators):
    score = 0
    reasons = []

    # RSI
    rsi = indicators.get("RSI", 50)
    if rsi < 30:
        score += 2
        reasons.append("RSI اشباع فروش")
    elif rsi > 70:
        score -= 2
        reasons.append("RSI اشباع خرید")

    # MACD
    macd = indicators.get("MACD", 0)
    macd_signal = indicators.get("MACD_SIGNAL", 0)

    if macd > macd_signal:
        score += 2
        reasons.append("تقاطع صعودی MACD")
    else:
        score -= 2
        reasons.append("تقاطع نزولی MACD")

    # EMA
    ema20 = indicators.get("EMA20", 0)
    ema50 = indicators.get("EMA50", 0)

    if ema20 > ema50:
        score += 1
        reasons.append("EMA20 بالای EMA50")
    else:
        score -= 1
        reasons.append("EMA20 پایین EMA50")

    # ADX
    adx = indicators.get("ADX", 0)
    if adx > 25:
        score += 1
        reasons.append("روند قوی")

    # Bollinger Bands
    close = indicators.get("CLOSE", 0)
    upper = indicators.get("BB_UPPER", 0)
    lower = indicators.get("BB_LOWER", 0)

    if lower and close < lower:
        score += 1
        reasons.append("زیر باند پایینی بولینگر")
    elif upper and close > upper:
        score -= 1
        reasons.append("بالای باند بالایی بولینگر")

    # نتیجه نهایی
    if score >= 4:
        signal = "🟢 خرید قوی"
    elif score >= 2:
        signal = "🟢 خرید"
    elif score <= -4:
        signal = "🔴 فروش قوی"
    elif score <= -2:
        signal = "🔴 فروش"
    else:
        signal = "🟡 خنثی"

    return {
        "signal": signal,
        "score": score,
        "reasons": reasons
    }
