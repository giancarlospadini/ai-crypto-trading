"""
Technical Indicators Service - Calculates technical analysis indicators for trading decisions
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from database.models import CryptoKline
from repositories.kline_repo import KlineRepository

logger = logging.getLogger(__name__)


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """Calculate Relative Strength Index (RSI)

    Args:
        prices: Series of closing prices
        period: RSI period (default 14)

    Returns:
        RSI value (0-100)
    """
    if len(prices) < period + 1:
        return 50.0  # Neutral value if not enough data

    # Calculate price changes
    delta = prices.diff()

    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)

    # Calculate average gains and losses
    avg_gain = gains.rolling(window=period).mean()
    avg_loss = losses.rolling(window=period).mean()

    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # Return the latest RSI value
    return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0


def calculate_sma(prices: pd.Series, period: int) -> float:
    """Calculate Simple Moving Average

    Args:
        prices: Series of closing prices
        period: SMA period

    Returns:
        SMA value
    """
    if len(prices) < period:
        return float(prices.mean())

    sma = prices.rolling(window=period).mean()
    return float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else float(prices.iloc[-1])


def calculate_ema(prices: pd.Series, period: int) -> float:
    """Calculate Exponential Moving Average

    Args:
        prices: Series of closing prices
        period: EMA period

    Returns:
        EMA value
    """
    if len(prices) < period:
        return float(prices.mean())

    ema = prices.ewm(span=period, adjust=False).mean()
    return float(ema.iloc[-1]) if not pd.isna(ema.iloc[-1]) else float(prices.iloc[-1])


def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
    """Calculate Bollinger Bands

    Args:
        prices: Series of closing prices
        period: Period for moving average
        std_dev: Number of standard deviations

    Returns:
        Dict with upper, middle, and lower bands
    """
    if len(prices) < period:
        current_price = float(prices.iloc[-1])
        return {
            "upper": current_price,
            "middle": current_price,
            "lower": current_price
        }

    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()

    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)

    return {
        "upper": float(upper_band.iloc[-1]) if not pd.isna(upper_band.iloc[-1]) else float(prices.iloc[-1]),
        "middle": float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else float(prices.iloc[-1]),
        "lower": float(lower_band.iloc[-1]) if not pd.isna(lower_band.iloc[-1]) else float(prices.iloc[-1])
    }


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    """Calculate MACD (Moving Average Convergence Divergence)

    Args:
        prices: Series of closing prices
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period

    Returns:
        Dict with MACD line, signal line, and histogram
    """
    if len(prices) < slow:
        return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}

    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return {
        "macd": float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0.0,
        "signal": float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0.0,
        "histogram": float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0.0
    }


def calculate_momentum_simple(df: pd.DataFrame) -> float:
    """Calculate simple momentum: (recent low - earlier low) / longest candle

    Args:
        df: DataFrame with OHLC data

    Returns:
        Momentum value
    """
    if len(df) < 2:
        return 0.0

    # Sort by timestamp
    df_sorted = df.sort_values("timestamp", ascending=True).reset_index(drop=True)

    # Split into halves
    half_idx = len(df_sorted) // 2
    first_half_low = df_sorted.iloc[:half_idx]["low_price"].min()
    second_half_low = df_sorted.iloc[half_idx:]["low_price"].min()

    # Maximum candle body
    max_daily_change = (df_sorted["close_price"] - df_sorted["open_price"]).abs().max()

    if pd.isna(first_half_low) or pd.isna(second_half_low) or pd.isna(max_daily_change) or max_daily_change == 0:
        return 0.0

    return float((second_half_low - first_half_low) / max_daily_change)


def calculate_support_level(df: pd.DataFrame, window_size: int = 30) -> Dict[str, float]:
    """Calculate support level based on distance from longest candle

    Args:
        df: DataFrame with OHLC data
        window_size: Number of periods to analyze

    Returns:
        Dict with support factor and days from longest candle
    """
    if len(df) < window_size + 1:
        return {"support_factor": 0.0, "days_from_longest": 0}

    # Sort by timestamp
    df_sorted = df.sort_values("timestamp", ascending=True)

    # Get the window
    df_window = df_sorted.iloc[-(window_size + 1):]

    if len(df_window) < 2:
        return {"support_factor": 0.0, "days_from_longest": 0}

    # Calculate body lengths relative to first close
    first_close = df_window.iloc[0]['close_price']
    body_lengths = (df_window.iloc[1:]['close_price'] - df_window.iloc[1:]['open_price']).abs() * 100 / first_close

    # Find index of maximum body
    max_idx_rev = body_lengths.iloc[::-1].idxmax()
    days_from_longest = len(df_window) - 1 - max_idx_rev + 1

    # Calculate support factor
    support_factor_base = (days_from_longest / (window_size - 1)) if window_size > 1 else 0

    # Price ratio calculation
    if len(df_window) >= 2:
        yesterday = df_window.iloc[-2]
        today = df_window.iloc[-1]

        denominator = yesterday['low_price'] - today['low_price']
        if denominator != 0:
            price_ratio = (yesterday['open_price'] - yesterday['close_price']) * 2 / denominator
        else:
            price_ratio = 1.0
    else:
        price_ratio = 1.0

    support_factor = support_factor_base * price_ratio

    return {
        "support_factor": float(support_factor),
        "days_from_longest": int(days_from_longest)
    }


def get_kline_dataframe(db: Session, symbol: str, market: str = "CRYPTO", period: str = "1d", limit: int = 100) -> Optional[pd.DataFrame]:
    """Get kline data as pandas DataFrame

    Args:
        db: Database session
        symbol: Symbol to fetch
        market: Market type
        period: Time period
        limit: Number of candles to fetch

    Returns:
        DataFrame with OHLC data or None
    """
    try:
        kline_repo = KlineRepository(db)
        klines = kline_repo.get_kline_data(symbol, market, period, limit)

        if not klines:
            return None

        # Convert to DataFrame
        data = []
        for kline in klines:
            data.append({
                "timestamp": kline.timestamp,
                "datetime": kline.datetime_str,
                "open_price": float(kline.open_price) if kline.open_price else 0.0,
                "high_price": float(kline.high_price) if kline.high_price else 0.0,
                "low_price": float(kline.low_price) if kline.low_price else 0.0,
                "close_price": float(kline.close_price) if kline.close_price else 0.0,
                "volume": float(kline.volume) if kline.volume else 0.0,
            })

        df = pd.DataFrame(data)
        # Sort by timestamp ascending (oldest first)
        df = df.sort_values("timestamp", ascending=True).reset_index(drop=True)

        return df

    except Exception as e:
        logger.error(f"Error fetching kline data for {symbol}: {e}")
        return None


def calculate_technical_indicators(db: Session, symbol: str, current_price: float) -> Dict:
    """Calculate all technical indicators for a symbol

    Args:
        db: Database session
        symbol: Symbol to analyze
        current_price: Current price of the symbol

    Returns:
        Dict with all technical indicators
    """
    try:
        # Get kline data (last 100 days)
        df = get_kline_dataframe(db, symbol, market="CRYPTO", period="1d", limit=100)

        if df is None or len(df) < 10:
            logger.warning(f"Insufficient data for technical analysis of {symbol}")
            return {
                "available": False,
                "reason": "Insufficient historical data"
            }

        # Get price series
        prices = df["close_price"]

        # Calculate all indicators
        indicators = {
            "available": True,
            "current_price": current_price,
            "rsi_14": calculate_rsi(prices, 14),
            "sma_20": calculate_sma(prices, 20),
            "sma_50": calculate_sma(prices, 50),
            "ema_12": calculate_ema(prices, 12),
            "ema_26": calculate_ema(prices, 26),
            "bollinger_bands": calculate_bollinger_bands(prices, 20, 2.0),
            "macd": calculate_macd(prices, 12, 26, 9),
            "momentum": calculate_momentum_simple(df),
            "support": calculate_support_level(df, 30)
        }

        # Add interpretations
        indicators["price_vs_sma20"] = "above" if current_price > indicators["sma_20"] else "below"
        indicators["price_vs_sma50"] = "above" if current_price > indicators["sma_50"] else "below"

        bb = indicators["bollinger_bands"]
        if current_price > bb["upper"]:
            indicators["bollinger_position"] = "above upper band (potentially overbought)"
        elif current_price < bb["lower"]:
            indicators["bollinger_position"] = "below lower band (potentially oversold)"
        else:
            indicators["bollinger_position"] = "within bands"

        rsi = indicators["rsi_14"]
        if rsi > 70:
            indicators["rsi_interpretation"] = "overbought"
        elif rsi < 30:
            indicators["rsi_interpretation"] = "oversold"
        else:
            indicators["rsi_interpretation"] = "neutral"

        macd = indicators["macd"]
        if macd["histogram"] > 0:
            indicators["macd_signal"] = "bullish"
        elif macd["histogram"] < 0:
            indicators["macd_signal"] = "bearish"
        else:
            indicators["macd_signal"] = "neutral"

        return indicators

    except Exception as e:
        logger.error(f"Error calculating technical indicators for {symbol}: {e}", exc_info=True)
        return {
            "available": False,
            "reason": f"Error: {str(e)}"
        }


def get_technical_analysis_summary(db: Session, symbols: List[str], prices: Dict[str, float]) -> Dict[str, Dict]:
    """Get technical analysis for multiple symbols

    Args:
        db: Database session
        symbols: List of symbols to analyze
        prices: Dict of current prices

    Returns:
        Dict mapping symbol to technical indicators
    """
    analysis = {}

    for symbol in symbols:
        current_price = prices.get(symbol, 0.0)
        if current_price > 0:
            analysis[symbol] = calculate_technical_indicators(db, symbol, current_price)
        else:
            analysis[symbol] = {
                "available": False,
                "reason": "No current price data"
            }

    return analysis
