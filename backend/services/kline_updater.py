"""
Kline Data Updater Service - Automatically updates historical candlestick data
"""
import logging
from typing import List
from sqlalchemy.orm import Session

from database.connection import SessionLocal
from services.market_data import get_kline_data
from repositories.kline_repo import KlineRepository

logger = logging.getLogger(__name__)


def update_klines_for_all_symbols(symbols: List[str], market: str = "CRYPTO", period: str = "1d", count: int = 100) -> None:
    """Update kline data for all trading symbols

    Args:
        symbols: List of symbols to update (e.g., ["BTC", "ETH", "SOL"])
        market: Market type (default: "CRYPTO")
        period: Candlestick period (default: "1d" for daily)
        count: Number of candles to fetch (default: 100)
    """
    db = SessionLocal()
    try:
        kline_repo = KlineRepository(db)

        total_updated = 0
        total_failed = 0

        logger.info(f"Starting kline data update for {len(symbols)} symbols...")

        for symbol in symbols:
            try:
                # Fetch kline data from exchange
                kline_data = get_kline_data(symbol, market, period, count)

                if not kline_data:
                    logger.warning(f"No kline data returned for {symbol}")
                    total_failed += 1
                    continue

                # Save to database (upsert mode)
                result = kline_repo.save_kline_data(symbol, market, period, kline_data)

                inserted = result.get('inserted', 0)
                updated = result.get('updated', 0)
                total = result.get('total', 0)

                if total > 0:
                    logger.info(f"✓ {symbol}: {total} candles saved (inserted: {inserted}, updated: {updated})")
                    total_updated += 1
                else:
                    logger.warning(f"✗ {symbol}: No new data to save")

            except Exception as e:
                logger.error(f"✗ Failed to update klines for {symbol}: {e}")
                total_failed += 1
                continue

        logger.info(f"Kline update completed: {total_updated} symbols updated, {total_failed} failed")

    except Exception as e:
        logger.error(f"Kline update task failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


def update_klines_for_trading_symbols() -> None:
    """Update klines for all active trading symbols"""
    try:
        # Import here to avoid circular dependency
        from services.trading_commands import AI_TRADING_SYMBOLS

        logger.info("=" * 80)
        logger.info("SCHEDULED TASK: Kline Data Update")
        logger.info("=" * 80)

        update_klines_for_all_symbols(AI_TRADING_SYMBOLS)

        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Failed to update klines for trading symbols: {e}", exc_info=True)
