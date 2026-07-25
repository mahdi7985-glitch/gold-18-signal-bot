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
    price_toman = price / 10
    
    # ===== تاریخچه قیمت (۵ روز اخیر برای روند هفتگی) =====
    history = load_history()
    price_history = history["price"]
    recent_prices = []
    weekly_trend = ""
    
    if len(price_history) >= 5:
        recent_prices = [
            price_history[-1] / 10,  # دیروز
            price_history[-2] / 10,  # پریروز
            price_history[-3] / 10,  # ۳ روز پیش
            price_history[-4] / 10,  # ۴ روز پیش
            price_history[-5] / 10,  # ۵ روز پیش
        ]
        
        # محاسبه روند هفتگی
        weekly_high = max(recent_prices)
        weekly_low = min(recent_prices)
        weekly_range = ((weekly_high - weekly_low) / weekly_low) * 100
        weekly_trend = f"📈 روند هفتگی: از {weekly_low:,.0f} به {weekly_high:,.0f} اومده بود"
        if price_toman < weekly_high * 0.98:
            weekly_trend += f"، الان داره اصلاح می‌کنه"
        elif price_toman > weekly_low * 1.02:
            weekly_trend += f"، داره از کف فاصله می‌گیره"
        else:
            weekly_trend += f"، در محدوده تعادل"
    elif len(price_history) >= 2:
        recent_prices = [price_history[-1] / 10, price_history[-2] / 10]
        weekly_trend = f"📈 روند کوتاه‌مدت: از {recent_prices[1]:,.0f} به {recent_prices[0]:,.0f}"
    else:
        weekly_trend = "📈 روند: داده کافی برای تحلیل هفتگی نیست"
    
    # ===== تغییرات =====
    change_text = ""
    advice = "🤔 امروز تازه شروع کردیم، بذار چند روز بگذره تا روند مشخص بشه."
    trend_emoji = "⚪"
    trend_word = "ثابت"
    
    if previous_price is not None and previous_price > 0:
        prev_toman = previous_price / 10
        change_amount = price - previous_price
        change_toman = change_amount / 10
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
                advice = "😬 وای امروز ریزش سنگینی داشتیم! نترس، تو بازار این چیزا طبیعیه. بهترین خریدا همین موقعا انجام میشه."
            elif abs(change_percent) > 2:
                advice = "📉 یه ریزش معمولی، نگران نباش. بذار ببینیم کفش کجاست."
            else:
                advice = "🔻 یه کم داره پایین میاد، ولی خیلی عادی‌ست."
        else:
            advice = "⚪ امروز تکون خاصی نداریم، همه منتظر یه خبر جدید هستن."
        
        change_text = f"""
📊 دیروز این ساعت: **{prev_toman:,.0f}** تومان
📉 تغییر: {trend_emoji} **{trend_word} {abs(change_toman):,.0f}** تومان ({abs(change_percent):.2f}%)
"""
    
    # ===== تاریخچه قیمت =====
    history_text = ""
    if len(recent_prices) >= 5:
        history_text = f"""
📅 قیمت‌های اخیر:
• امروز: {price_toman:,.0f} تومان
• دیروز: {recent_prices[0]:,.0f} تومان
• پریروز: {recent_prices[1]:,.0f} تومان
• ۳ روز پیش: {recent_prices[2]:,.0f} تومان
• ۴ روز پیش: {recent_prices[3]:,.0f} تومان
• ۵ روز پیش: {recent_prices[4]:,.0f} تومان
"""
    elif len(recent_prices) >= 2:
        history_text = f"""
📅 قیمت‌های اخیر:
• امروز: {price_toman:,.0f} تومان
• دیروز: {recent_prices[0]:,.0f} تومان
"""
    
    # ===== سیگنال =====
    signal_text = analysis.get("signal_text", "صبر کن")
    signal_emoji = analysis.get("signal_emoji", "🟡")
    signal_confidence = analysis.get("signal_confidence", 45)
    trend = analysis.get("trend", "خنثی")
    signal_reason = analysis.get("signal_reason", "دلیل خاصی نداریم")
    score = analysis.get("score", 0)
    
    # ===== اندیکاتورها =====
    indicators = analysis.get("indicators", {})
    
    # ===== سطوح حمایت و مقاومت =====
    support, resistance = calculate_support_resistance(price, price_history)
    support2, resistance2 = None, None
    
    # سطوح دوم (برای پیش‌بینی)
    if support and resistance:
        support2 = support * 0.98
        resistance2 = resistance * 1.02
    
    # ===== متن دوستانه برای سیگنال =====
    friendly_messages = {
        "خرید": "🚀 رفیق، امروز روز خوبیه! همه چیز داره هموار میشه برای یه رشد خوب. ولی یادت باشه هیچوقت یه‌دفعه همه سرمایه‌ات رو نریزی تو کار.",
        "فروش": "⚠️ راستش امروز اوضاع خوش‌یمن نیست. اگه طلا داری، شاید بهتر باشه یه کم بفروشی و نقد شی. ولی این تصمیم با خودته عزیزم.",
        "صبر کن": "🤔 امروز یه وضعیت دو پهلو داریم. من که دست نگه می‌دارم، تو هم عجله نکن. فردا صبح دوباره چک می‌کنیم.",
        "صبر با تمایل به خرید": "🟡 امروز نه خریداریم نه فروشنده، ولی یه کم به خرید مایل‌ترم. اگه قیمت یه کم پایین‌تر بیاد، شاید وقتش باشه.",
        "صبر با تمایل به فروش": "🟠 امروز کمی نگران‌کننده‌ست. اگه طلا داری، شاید بهتر باشه یه کم صبر کنی ببینی چی میشه. عجله نکن.",
    }
    friendly_message = friendly_messages.get(signal_text, "🟡 صبر کن، فعلاً وقتش نیست.")
    
    # ===== توضیح دلایل سیگنال به زبان ساده =====
    reason_text = ""
    reasons_list = []
    
    # تحلیل EMA
    ema_fast = indicators.get('ema_fast', 0)
    ema_slow = indicators.get('ema_slow', 0)
    if ema_fast and ema_slow:
        if price > ema_fast:
            reasons_list.append(f"قیمت از میانگین ۲۰ روزه ({ema_fast/10:,.0f}) بالاتر")
            if price > ema_slow:
                reasons_list.append(f"و از میانگین ۵۰ روزه ({ema_slow/10:,.0f}) بالاتر")
            else:
                reasons_list.append(f"ولی از میانگین ۵۰ روزه ({ema_slow/10:,.0f}) پایین‌تر")
        else:
            reasons_list.append(f"قیمت از میانگین ۲۰ روزه ({ema_fast/10:,.0f}) پایین‌تر")
            if price < ema_slow:
                reasons_list.append(f"و از میانگین ۵۰ روزه ({ema_slow/10:,.0f}) پایین‌تر")
            else:
                reasons_list.append(f"ولی از میانگین ۵۰ روزه ({ema_slow/10:,.0f}) بالاتر")
    
    # تحلیل RSI
    rsi_val = indicators.get('rsi', 50)
    if rsi_val:
        if rsi_val > 70:
            reasons_list.append(f"RSI اشباع خرید ({rsi_val:.1f})، بازار نیاز به نفس‌گیری داره")
        elif rsi_val < 30:
            reasons_list.append(f"RSI اشباع فروش ({rsi_val:.1f})، احتمال برگشت")
        elif 40 < rsi_val < 60:
            reasons_list.append(f"RSI متعادل ({rsi_val:.1f})")
        else:
            reasons_list.append(f"RSI در محدوده {rsi_val:.1f}")
    
    # تحلیل MACD
    if 'macd' in indicators and 'macd_signal' in indicators:
        macd_diff = indicators['macd'] - indicators['macd_signal']
        if macd_diff > 0:
            reasons_list.append("مومنتوم صعودی (مکدی مثبت)")
        else:
            reasons_list.append("مومنتوم نزولی (مکدی منفی)")
    
    # ترکیب دلایل
    if reasons_list:
        reason_text = "چرا؟\n" + "\n".join([f"• {r}" for r in reasons_list[:4]])
        if len(reasons_list) > 4:
            reason_text += f"\n• و {len(reasons_list)-4} مورد دیگه..."
    
    # ===== فاصله قیمت از EMA =====
    ema_distance_text = ""
    if ema_fast:
        distance = ((price - ema_fast) / ema_fast) * 100
        if abs(distance) > 3:
            ema_distance_text = f"قیمت {abs(distance):.1f}٪ از میانگین ۲۰ روزه فاصله داره"
            if distance > 3:
                ema_distance_text += " (کشیدگی به بالا)"
            else:
                ema_distance_text += " (کشیدگی به پایین)"
        elif abs(distance) > 1:
            ema_distance_text = f"قیمت {abs(distance):.1f}٪ از میانگین ۲۰ روزه فاصله داره (تعادل نسبی)"
        else:
            ema_distance_text = "قیمت روی میانگین ۲۰ روزه (تعادل کامل)"
    
    # ===== ساخت پیام نهایی =====
    message = f"""سلام رفیق! 👋
برات تحلیل امروز طلا رو گرفتم:

📅 {format_jalali_datetime(jalali)}
━━━━━━━━━━━━━━━━━━━━
💰 قیمت الان: **{price_toman:,.0f}** تومان
{change_text}
{weekly_trend}
━━━━━━━━━━━━━━━━━━━━

🎯 نظر من (سیگنال):
{signal_emoji} **{signal_text}** (با {signal_confidence}٪ اطمینان)

{signal_reason}

{friendly_message}

━━━━━━━━━━━━━━━━━━━━
📊 یه نگاه به اعداد بندازیم:

• میانگین ۲۰ روزه: {ema_fast/10:,.0f} تومان ({'بالاتر از قیمت' if price < ema_fast else 'پایین‌تر از قیمت'})
• میانگین ۵۰ روزه: {ema_slow/10:,.0f} تومان ({'بالاتر از قیمت' if price < ema_slow else 'پایین‌تر از قیمت'})
• RSI: {rsi_val:.1f} {'🔴 اشباع خرید' if rsi_val > 70 else '🟢 اشباع فروش' if rsi_val < 30 else '🟡 متعادل'}
• قدرت روند (ADX): {indicators.get('adx', 0):.1f} {'💪 قوی' if indicators.get('adx', 0) > 25 else '🤔 متوسط' if indicators.get('adx', 0) > 20 else '😶 ضعیف'}
• مکدی: {'مثبت 📈' if indicators.get('macd', 0) > indicators.get('macd_signal', 0) else 'منفی 📉'}
{ema_distance_text}

━━━━━━━━━━━━━━━━━━━━
📍 سطح‌های مهم امروز:
"""

    # سطوح حمایت و مقاومت
    if support and resistance:
        message += f"""
اگه بره پایین‌تر:
🛡️ **حمایت اول:** {support/10:,.0f} تومان"""
        if support2:
            message += f"""
🛡️ **حمایت دوم:** {support2/10:,.0f} تومان (اگه بشکنه می‌ره پایین‌تر)"""
        
        message += f"""

اگه برگرده بالا:
🚀 **مقاومت اول:** {resistance/10:,.0f} تومان"""
        if resistance2:
            message += f"""
🚀 **مقاومت دوم:** {resistance2/10:,.0f} تومان (اگه پاس کنه می‌ره بالاتر)"""
    
    # ===== فاکتورهای کلیدی (دلار و انس) =====
    dollar_text = ""
    if dollar_price is not None:
        dollar_emoji = "🟢" if dollar_change and dollar_change > 0 else "🔻" if dollar_change and dollar_change < 0 else "⚪"
        dollar_text = f"""
━━━━━━━━━━━━━━━━━━━━
💎 دو تا فاکتور مهم دیگه:

💵 دلار آزاد: {dollar_price:,.0f} تومان ({dollar_emoji} {'صعودی' if dollar_change and dollar_change > 0 else 'نزولی' if dollar_change and dollar_change < 0 else 'ثابت'})
"""
        if ounce_price is not None:
            ounce_emoji = "🟢" if ounce_change and ounce_change > 0 else "🔻" if ounce_change and ounce_change < 0 else "⚪"
            dollar_text += f"""🏅 انس جهانی: ${ounce_price:,.2f} ({ounce_emoji} {'صعودی' if ounce_change and ounce_change > 0 else 'نزولی' if ounce_change and ounce_change < 0 else 'ثابت'})
"""
            # تأثیر ترکیبی
            if dollar_change and ounce_change:
                if dollar_change > 0 and ounce_change > 0:
                    dollar_text += "🔺 تأثیر روی طلا: **مثبت قوی** (هر دو صعودی)"
                elif dollar_change > 0 and ounce_change < 0:
                    dollar_text += "🔄 تأثیر روی طلا: **مختلط** (دلار بالا، انس پایین)"
                elif dollar_change < 0 and ounce_change > 0:
                    dollar_text += "🔄 تأثیر روی طلا: **مختلط** (دلار پایین، انس بالا)"
                else:
                    dollar_text += "🔻 تأثیر روی طلا: **منفی** (هر دو نزولی)"
    
    # ===== حرف آخر =====
    message += f"""
━━━━━━━━━━━━━━━━━━━━
🗣️ حرف آخر:

{advice}

هر سوالی داری، بپرس. کنارت هستم 🤝
"""
    
    return message
