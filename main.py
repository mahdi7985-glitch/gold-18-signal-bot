def format_full_report(
    price: float,
    previous_price: Optional[float],
    analysis: Dict[str, Any],
    dollar_price: Optional[float] = None,
    dollar_change: Optional[float] = None,
    ounce_price: Optional[float] = None,
    ounce_change: Optional[float] = None
) -> str:
    """
    تولید گزارش کامل و دوستانه با تاریخچه، تحلیل و فاکتورهای کلیدی
    """
    # ===== زمان =====
    jalali = get_jalali_now()
    day_name = get_iran_day()
    
    # ===== قیمت‌ها =====
    price_toman = price
    
    # ===== تاریخچه قیمت =====
    recent_prices = get_recent_prices(5)
    weekly_trend_data = get_weekly_trend()
    
    # ===== تغییرات =====
    change_text = ""
    advice = "🤔 امروز تازه شروع کردیم، بذار چند روز بگذره تا روند مشخص بشه."
    trend_emoji = "⚪"
    trend_word = "ثابت"
    
    if previous_price is not None and previous_price > 0:
        prev_toman = previous_price
        change_amount = price - previous_price
        change_percent = (change_amount / previous_price) * 100
        
        if change_amount > 0:
            trend_emoji = "🟢"
            trend_word = "صعود"
            if change_percent > 3:
                advice = "🚀 امروز داره پرواز می‌کنه! ولی زیاد ذوق نکن، ممکنه یه اصلاح کوچیک بیاد."
            elif change_percent > 1:
                advice = "😊 امروز روز خوبیه، آروم آروم داره می‌ره بالا. محتاط باش ولی خوش‌بین."
            else:
                advice = "📈 یه رشد ملایم، اوضاع داره آروم آروم خوب میشه."
        elif change_amount < 0:
            trend_emoji = "🔻"
            trend_word = "نزول"
            if abs(change_percent) > 5:
                advice = "😬 وای امروز ریزش سنگینی داشتیم! صبر کن تا بازار آروم بشه."
            elif abs(change_percent) > 2:
                advice = "📉 یه ریزش معمولی، نگران نباش. بذار ببینیم کفش کجاست."
            else:
                advice = "🔻 یه کم داره پایین میاد، ولی خیلی عادی‌ست."
        else:
            advice = "⚪ امروز تکون خاصی نداریم، همه منتظر یه خبر جدید هستن."
        
        change_text = f"""
📊 دیروز این ساعت: **{prev_toman:,.0f}** تومان
📉 تغییر: {trend_emoji} **{trend_word} {abs(change_amount):,.0f}** تومان ({change_percent:.2f}%)
"""
    
    # ===== تاریخچه قیمت =====
    history_text = ""
    if SHOW_HISTORY and len(recent_prices) >= 2:
        history_text = "\n📅 قیمت‌های اخیر:\n"
        labels = ["امروز", "دیروز", "پریروز", "۳ روز پیش", "۴ روز پیش", "۵ روز پیش"]
        for i, (label, price_val) in enumerate(zip(labels, recent_prices)):
            if i == 0:
                history_text += f"• {label}: {price_val:,.0f} تومان\n"
            elif i < len(recent_prices):
                history_text += f"• {label}: {recent_prices[i]:,.0f} تومان\n"
    
    # ===== روند هفتگی =====
    weekly_text = ""
    if weekly_trend_data['trend'] != "داده کافی نیست":
        weekly_text = f"📈 روند هفتگی: از {weekly_trend_data['start']:,.0f} به {weekly_trend_data['end']:,.0f}"
        if weekly_trend_data['change'] > 0:
            weekly_text += f" (صعود {weekly_trend_data['change']:.1f}%)"
        else:
            weekly_text += f" (نزول {abs(weekly_trend_data['change']):.1f}%)"
    
    # ===== سیگنال =====
    signal_text = analysis.get("signal_text", "صبر کن")
    signal_emoji = analysis.get("signal_emoji", "🟡")
    signal_confidence = analysis.get("signal_confidence", 35)
    trend = analysis.get("trend", "خنثی")
    signal_reason = analysis.get("signal_reason", "دلیل خاصی نداریم")
    
    # اگر اطمینان ۰ بود، به ۳۵ تغییر بده
    if signal_confidence == 0:
        signal_confidence = 35
        signal_reason = "🔸 وضعیت نامشخص، بهتره صبر کنی تا بازار تکلیفش مشخص بشه."
    
    # ===== پیام دوستانه =====
    friendly = analysis.get("friendly", {})
    friendly_message = friendly.get("friendly_message", "🟡 صبر کن، فعلاً وقتش نیست.")
    
    # ===== اندیکاتورها =====
    indicators = analysis.get("indicators", {})
    rsi_val = indicators.get('rsi', 50)
    
    # ===== تنظیم متن حرف آخر بر اساس RSI =====
    if "نزول" in trend_word or change_amount < 0:
        if rsi_val > 70:
            advice = "🔴 RSI اشباع خرید رو نشون میده. با توجه به ریزش امروز، احتمالاً این یه اصلاح موقتیه. بهتره صبر کنی تا قیمت به حمایت برسه و بعد تصمیم بگیری."
        elif rsi_val < 30:
            advice = "🟢 RSI اشباع فروش رو نشون میده. ممکنه کف نزدیک باشه، ولی بازم صبر کن تا برگشت رو تأیید کنی."
        else:
            advice = "🟡 بازار در منطقه تعادله. صبر کن ببینیم روند مشخص میشه."
    
    # ===== سطوح حمایت و مقاومت =====
    history = load_history()
    support, resistance = calculate_support_resistance(history["price"], period=14)
    support2 = support * 0.98 if support else None
    resistance2 = resistance * 1.02 if resistance else None
    
    # ===== ساخت پیام =====
    message = f"""سلام رفیق! 👋
برات تحلیل امروز طلا رو گرفتم:

📅 {format_jalali_datetime(jalali)}
━━━━━━━━━━━━━━━━━━━━
💰 قیمت الان: **{price_toman:,.0f}** تومان
{change_text}
{weekly_text}
{history_text}
━━━━━━━━━━━━━━━━━━━━

🎯 نظر من:
{signal_emoji} **{signal_text}** (با {signal_confidence}% اطمینان)

{signal_reason}

{friendly_message}

━━━━━━━━━━━━━━━━━━━━
📊 یه نگاه به اعداد بندازیم:

• میانگین ۲۰ روزه: {indicators.get('ema_fast', 0)/10:,.0f} تومان
• میانگین ۵۰ روزه: {indicators.get('ema_slow', 0)/10:,.0f} تومان
• RSI: {indicators.get('rsi', 0):.1f} """

    # توضیح RSI
    if rsi_val > 70:
        message += "🔴 اشباع خرید\n"
    elif rsi_val < 30:
        message += "🟢 اشباع فروش\n"
    else:
        message += "🟡 متعادل\n"
    
    message += f"""• قدرت روند (ADX): {indicators.get('adx', 0):.1f} """
    
    # توضیح ADX
    adx_val = indicators.get('adx', 0)
    if adx_val > 25:
        message += "💪 قوی\n"
    elif adx_val > 20:
        message += "🤔 متوسط\n"
    else:
        message += "😶 ضعیف\n"
    
    # MACD
    if 'macd' in indicators and 'macd_signal' in indicators:
        if indicators['macd'] > indicators['macd_signal']:
            message += "• مکدی: مثبت 📈 (مومنتوم صعودی)\n"
        else:
            message += "• مکدی: منفی 📉 (مومنتوم نزولی)\n"
    
    # ===== سطوح کلیدی با فاصله درصدی =====
    if SHOW_LEVELS and support and resistance:
        # محاسبه فاصله درصدی
        dist_to_support = ((price - support) / price) * 100
        dist_to_resistance = ((resistance - price) / price) * 100
        
        message += f"""
━━━━━━━━━━━━━━━━━━━━
📍 سطح‌های مهم امروز:

اگه بره پایین‌تر:
🛡️ **حمایت اول:** {support/10:,.0f} تومان ({dist_to_support:.1f}% پایین‌تر)
🛡️ **حمایت دوم:** {support2/10:,.0f} تومان ({dist_to_support + 2:.1f}% پایین‌تر)

اگه برگرده بالا:
🚀 **مقاومت اول:** {resistance/10:,.0f} تومان ({dist_to_resistance:.1f}% بالاتر)
🚀 **مقاومت دوم:** {resistance2/10:,.0f} تومان ({dist_to_resistance + 2:.1f}% بالاتر)
"""
    
    # ===== دلار و انس =====
    if SHOW_DOLLAR_OUNCE and dollar_price:
        dollar_emoji = "🟢" if dollar_change and dollar_change > 0 else "🔻" if dollar_change and dollar_change < 0 else "⚪"
        message += f"""
━━━━━━━━━━━━━━━━━━━━
💎 دو تا فاکتور مهم دیگه:

💵 دلار آزاد: {dollar_price:,.0f} تومان ({dollar_emoji} {'صعودی' if dollar_change and dollar_change > 0 else 'نزولی' if dollar_change and dollar_change < 0 else 'ثابت'})
"""
        if ounce_price:
            ounce_emoji = "🟢" if ounce_change and ounce_change > 0 else "🔻" if ounce_change and ounce_change < 0 else "⚪"
            message += f"""🏅 انس جهانی: ${ounce_price:,.2f} ({ounce_emoji} {'صعودی' if ounce_change and ounce_change > 0 else 'نزولی' if ounce_change and ounce_change < 0 else 'ثابت'})
"""
            # تأثیر ترکیبی
            if dollar_change and ounce_change:
                if dollar_change > 0 and ounce_change > 0:
                    message += "🔺 تأثیر روی طلا: **مثبت قوی** (هر دو صعودی)"
                elif dollar_change > 0 and ounce_change < 0:
                    message += "🔄 تأثیر روی طلا: **مختلط** (دلار بالا، انس پایین)"
                elif dollar_change < 0 and ounce_change > 0:
                    message += "🔄 تأثیر روی طلا: **مختلط** (دلار پایین، انس بالا)"
                else:
                    message += "🔻 تأثیر روی طلا: **منفی** (هر دو نزولی)"
    
    # ===== حرف آخر (بدون عبارت اضافی) =====
    message += f"""
━━━━━━━━━━━━━━━━━━━━
🗣️ حرف آخر:

{advice}
"""
    
    return message
