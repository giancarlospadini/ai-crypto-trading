from typing import Dict, List, Any
import logging
from .binance_market_data import (
    get_last_price_from_binance,
    get_kline_data_from_binance,
)

logger = logging.getLogger(__name__)


def get_last_price(symbol: str, market: str = "CRYPTO") -> float:
    key = f"{symbol}.{market}"

    # Check cache first
    from .price_cache import get_cached_price, cache_price
    cached_price = get_cached_price(symbol, market)
    if cached_price is not None:
        logger.debug(f"Using cached price for {key}: {cached_price}")
        return cached_price

    logger.info(f"Getting real-time price for {key} from Binance...")

    # Use Binance only
    try:
        price = get_last_price_from_binance(symbol)
        if price and price > 0:
            logger.info(f"Got real-time price for {key} from Binance: {price}")
            cache_price(symbol, market, price)
            return price
    except Exception as bin_err:
        logger.error(f"Binance failed for {key}: {bin_err}")

    # Failed to get price
    raise Exception(f"Unable to get real-time price for {key} from Binance")


def get_kline_data(symbol: str, market: str = "CRYPTO", period: str = "1d", count: int = 100) -> List[Dict[str, Any]]:
    key = f"{symbol}.{market}"

    logger.info(f"Getting K-line data for {key} from Binance...")

    # Use Binance only
    try:
        data = get_kline_data_from_binance(symbol, period, count)
        if data:
            logger.info(f"Got K-line data for {key} from Binance, total {len(data)} items")
            return data
    except Exception as bin_err:
        logger.error(f"Binance failed for {key}: {bin_err}")

    # Failed to get kline data
    raise Exception(f"Unable to get K-line data for {key} from Binance")


def get_market_status(symbol: str, market: str = "CRYPTO") -> Dict[str, Any]:
    """Get market status for a symbol (simplified for Binance)"""
    # Binance is 24/7 for crypto, return open status
    return {
        'market_status': 'OPEN',
        'is_trading': True,
        'symbol': symbol,
        'exchange': 'Binance',
        'market_type': 'crypto',
    }


def get_all_symbols() -> List[str]:
    """Get all available trading pairs (default popular pairs)"""
    return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'DOGE/USDT', 'XRP/USDT', 'BNB/USDT', 'ADA/USDT', 'LTC/USDT']