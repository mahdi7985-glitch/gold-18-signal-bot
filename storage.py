def get_price_change_percent() -> Optional[float]:
    """
    محاسبه تغییرات درصدی قیمت طلا نسبت به قیمت قبلی
    
    Returns:
        float: تغییرات درصدی (مثلاً 1.5- یا 2.3+) یا None اگر داده کافی نباشد
    """
    history = load_history()
    if len(history) < 2:
        return None
    
    last_price = history["price"].iloc[-1]
    prev_price = history["price"].iloc[-2]
    
    if prev_price == 0:
        return None
    
    change = ((last_price - prev_price) / prev_price) * 100
    return change
