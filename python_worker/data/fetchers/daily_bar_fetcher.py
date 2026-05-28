"""
Fetch daily bar data for all stocks and save to database.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from data.fetchers.akshare_fetcher import get_daily_bar as akshare_get_daily
from data.fetchers.tushare_fetcher import get_daily_bar as tushare_get_daily
from data.loaders.db_loader import engine, upsert_daily_bar
from sqlalchemy import text
from datetime import datetime, timedelta
import time

def fetch_daily_for_date(trade_date: str, batch_size: int = 50):
    """
    Fetch daily bar data for all stocks for a specific date.

    Args:
        trade_date: Trade date in YYYY-MM-DD format
        batch_size: Number of stocks to fetch per batch (to avoid rate limiting)
    """
    print(f"Starting daily fetch for {trade_date}...")

    # Get all stock codes
    with engine.connect() as conn:
        result = conn.execute(text("SELECT code FROM instrument_master ORDER BY code"))
        stock_codes = [row[0] for row in result.fetchall()]

    print(f"Fetching daily data for {len(stock_codes)} stocks...")

    success_count = 0
    error_count = 0

    for i, code in enumerate(stock_codes):
        try:
            # Try Tushare first
            df = tushare_get_daily(code, trade_date, trade_date)

            # Fallback to AkShare if Tushare empty
            if df.empty:
                df = akshare_get_daily(code, trade_date, trade_date)

            if not df.empty:
                row = df.iloc[0]
                data = {
                    'code': code,
                    'trade_date': trade_date,
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume']),
                    'amount': float(row['amount']),
                    'turnover_rate': float(row.get('turnover_rate', 0)),
                    'pct_change': float(row.get('pct_change', 0)),
                    'amplitude': float(row.get('amplitude', 0))
                }
                upsert_daily_bar(data)
                success_count += 1
            else:
                error_count += 1

        except Exception as e:
            print(f"Error fetching {code}: {e}")
            error_count += 1

        # Progress report every 100 stocks
        if (i + 1) % 100 == 0:
            print(f"Progress: {i + 1}/{len(stock_codes)} - Success: {success_count}, Error: {error_count}")

        # Rate limiting - small delay between requests
        if (i + 1) % batch_size == 0:
            time.sleep(1)

    print(f"\nDaily fetch complete for {trade_date}")
    print(f"Success: {success_count}, Error: {error_count}")

    return success_count > 0

def fetch_latest_daily():
    """Fetch daily data for the latest trading date"""
    # Get latest trading date from database or use yesterday
    today = datetime.now()
    trade_date = today.strftime('%Y-%m-%d')
    return fetch_daily_for_date(trade_date)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, help='Trade date (YYYY-MM-DD)')
    args = parser.parse_args()

    if args.date:
        success = fetch_daily_for_date(args.date)
    else:
        success = fetch_latest_daily()

    sys.exit(0 if success else 1)