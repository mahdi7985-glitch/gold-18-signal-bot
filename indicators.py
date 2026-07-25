def calculate_support_resistance(
    price_series: pd.Series, 
    period: int = 20,
    multiplier: float = 1.5
) -> Tuple[Optional[float], Optional[float]]:
    """
    محاسبه حمایت و مقاومت با استفاده از باندهای بولینگر
    
    Args:
        price_series: سری قیمت‌ها
        period: دوره محاسبه (پیش‌فرض ۲۰)
        multiplier: ضریب انحراف معیار (پیش‌فرض ۱.۵)
    
    Returns:
        tuple: (support, resistance) یا (None, None) اگر داده کافی نباشد
    """
    if len(price_series) < period:
        return None, None
    
    # گرفتن آخرین 'period' قیمت
    recent_prices = price_series.iloc[-period:]
    
    # محاسبه میانگین و انحراف معیار
    mean = recent_prices.mean()
    std = recent_prices.std()
    
    # محاسبه حمایت و مقاومت
    support = mean - (multiplier * std)
    resistance = mean + (multiplier * std)
    
    # اطمینان از منطقی بودن سطوح
    last_price = price_series.iloc[-1]
    
    # اگر حمایت از قیمت فعلی بالاتر بود، اصلاح کن
    if support > last_price:
        support = last_price * 0.97
    
    # اگر مقاومت از قیمت فعلی پایین‌تر بود، اصلاح کن
    if resistance < last_price:
        resistance = last_price * 1.03
    
    # اگر حمایت و مقاومت خیلی نزدیک بودن، اصلاح کن
    if support and resistance and (resistance - support) < (last_price * 0.02):
        support = support * 0.98
        resistance = resistance * 1.02
    
    return support, resistance


def calculate_key_levels(
    price_series: pd.Series,
    period: int = 20
) -> Dict[str, Optional[float]]:
    """
    محاسبه سطوح کلیدی (حمایت و مقاومت با چند روش)
    
    Returns:
        dict: {
            'support_1': float,
            'support_2': float,
            'resistance_1': float,
            'resistance_2': float,
            'pivot': float,
        }
    """
    if len(price_series) < period:
        return {
            'support_1': None,
            'support_2': None,
            'resistance_1': None,
            'resistance_2': None,
            'pivot': None,
        }
    
    # قیمت‌های اخیر
    recent = price_series.iloc[-period:]
    last_price = price_series.iloc[-1]
    
    # روش ۱: بولینگر
    support_1, resistance_1 = calculate_support_resistance(price_series, period)
    
    # روش ۲: سطوح کلاسیک (High/Low)
    high = recent.max()
    low = recent.min()
    pivot = (high + low + last_price) / 3
    
    support_2 = pivot - (high - low)
    resistance_2 = pivot + (high - low)
    
    # اگر روش بولینگر جواب نداد، از روش کلاسیک استفاده کن
    if support_1 is None:
        support_1 = support_2
    if resistance_1 is None:
        resistance_1 = resistance_2
    
    return {
        'support_1': support_1,
        'support_2': support_2,
        'resistance_1': resistance_1,
        'resistance_2': resistance_2,
        'pivot': pivot,
    }
