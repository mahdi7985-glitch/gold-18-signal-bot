
import pandas as pd
from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange

import config


def build_ohlc_candles(price_series: pd.Series, rule: str = config.RESAMPLE_RULE) -> pd.DataFrame:
    """
    سری قیمت خام (تیک‌های ۵ دقیقه‌ای) را به کندل‌های OHLC در بازه‌ی `rule`
    (مثلاً '15min' یا '1H') تبدیل می‌کند.
    """
    ohlc = price_series.resample(rule).ohlc()
    ohlc = ohlc.dropna(subset=["close"])
    return ohlc


def compute_indicators(candles: pd.DataFrame) -> pd.DataFrame:
    """تمام اندیکاتورهای موردنیاز را به DataFrame کندل‌ها اضافه می‌کند."""
    df = candles.copy()
    close, high, low = df["close"], df["high"], df["low"]

    df["sma"] = SMAIndicator(close, window=config.SMA_PERIOD).sma_indicator()
    df["ema"] = EMAIndicator(close, window=config.EMA_PERIOD).ema_indicator()

    rsi = RSIIndicator(close, window=config.RSI_PERIOD)
    df["rsi"] = rsi.rsi()

    macd = MACD(
        close,
        window_fast=config.MACD_FAST,
        window_slow=config.MACD_SLOW,
        window_sign=config.MACD_SIGNAL,
    )
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_hist"] = macd.macd_diff()

    bb = BollingerBands(close, window=config.BBANDS_PERIOD, window_dev=config.BBANDS_STD)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_mid"] = bb.bollinger_mavg()
    df["bb_percent"] = bb.bollinger_pband()

    adx = ADXIndicator(high, low, close, window=config.ADX_PERIOD)
    df["adx"] = adx.adx()

    atr = AverageTrueRange(high, low, close, window=config.ATR_PERIOD)
    df["atr"] = atr.average_true_range()

    return df


def get_latest_indicators(price_series: pd.Series):
    """
    آخرین ردیف کامل اندیکاتورها را برمی‌گرداند، به‌همراه کل DataFrame.
    اگر داده کافی نباشد None برمی‌گرداند.
    """
    candles = build_ohlc_candles(price_series)
    if len(candles) < config.MIN_CANDLES_REQUIRED:
        return None

    df = compute_indicators(candles)
    df_valid = df.dropna(subset=["sma", "ema", "rsi", "macd", "adx", "atr", "bb_upper"])
    if df_valid.empty:
        return None

    return df_valid.iloc[-1], df_valid

