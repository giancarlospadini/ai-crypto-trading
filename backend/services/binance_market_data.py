"""
Binance market data service as fallback using CCXT
"""
import ccxt
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class BinanceClient:
    def __init__(self):
        self.exchange = None
        self._initialize_exchange()

    def _initialize_exchange(self):
        """Initialize CCXT Binance exchange"""
        try:
            self.exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}  # Use spot market
            })
            logger.info("Binance exchange initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Binance exchange: {e}")
            raise

    def get_last_price(self, symbol: str) -> Optional[float]:
        """Get the last price for a symbol"""
        try:
            if not self.exchange:
                self._initialize_exchange()

            formatted_symbol = self._format_symbol(symbol)
            ticker = self.exchange.fetch_ticker(formatted_symbol)
            price = ticker['last']

            logger.info(f"Got price for {formatted_symbol} from Binance: {price}")
            return float(price) if price else None

        except Exception as e:
            logger.error(f"Error fetching price for {symbol} from Binance: {e}")
            return None

    def get_kline_data(self, symbol: str, period: str = '1d', count: int = 100) -> List[Dict[str, Any]]:
        """Get kline/candlestick data for a symbol"""
        try:
            if not self.exchange:
                self._initialize_exchange()

            formatted_symbol = self._format_symbol(symbol)

            timeframe_map = {
                '1m': '1m',
                '5m': '5m',
                '15m': '15m',
                '30m': '30m',
                '1h': '1h',
                '1d': '1d',
            }
            timeframe = timeframe_map.get(period, '1d')

            ohlcv = self.exchange.fetch_ohlcv(formatted_symbol, timeframe, limit=count)

            klines = []
            for candle in ohlcv:
                timestamp_ms = candle[0]
                open_price = candle[1]
                high_price = candle[2]
                low_price = candle[3]
                close_price = candle[4]
                volume = candle[5]

                change = close_price - open_price if open_price else 0
                percent = (change / open_price * 100) if open_price else 0

                klines.append({
                    'timestamp': int(timestamp_ms / 1000),
                    'datetime_str': datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).isoformat(),
                    'open': float(open_price) if open_price else None,
                    'high': float(high_price) if high_price else None,
                    'low': float(low_price) if low_price else None,
                    'close': float(close_price) if close_price else None,
                    'volume': float(volume) if volume else None,
                    'amount': float(volume * close_price) if volume and close_price else None,
                    'change': float(change),
                    'percent': float(percent),
                })

            logger.info(f"Got {len(klines)} klines for {formatted_symbol} from Binance")
            return klines

        except Exception as e:
            logger.error(f"Error fetching klines for {symbol} from Binance: {e}")
            return []

    def _format_symbol(self, symbol: str) -> str:
        """Format symbol for Binance CCXT (e.g., 'BTC' -> 'BTC/USDT')"""
        if '/' in symbol:
            return symbol

        symbol_upper = symbol.upper()
        # Binance uses USDT for most pairs
        return f"{symbol_upper}/USDT"


# Global client instance
binance_client = BinanceClient()


def get_last_price_from_binance(symbol: str) -> Optional[float]:
    """Get last price from Binance"""
    return binance_client.get_last_price(symbol)


def get_kline_data_from_binance(symbol: str, period: str = '1d', count: int = 100) -> List[Dict[str, Any]]:
    """Get kline data from Binance"""
    return binance_client.get_kline_data(symbol, period, count)
