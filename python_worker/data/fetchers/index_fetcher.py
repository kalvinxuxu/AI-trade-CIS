"""
Fetch index data and save to database.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from data.fetchers.akshare_fetcher import get_index_daily as akshare_get_index
from data.fetchers.tushare_fetcher import get_index_daily as tushare_get_index
from data.loaders.db_loader import engine
from sqlalchemy import text
from datetime import datetime

# Index codes to fetch (Tushare format)
INDICES = [
    ('000001.SH', '上证指数'),
    ('399001.SZ', '深证成指'),
    ('399006.SZ', '创业板指'),
    ('000300.SH', '沪深300'),
    ('000016.SH', '上证50'),
    ('000905.SH', '中证500'),
]

def fetch_index_daily_for_date(trade_date: str):
    """
    Fetch daily data for major indices for a specific date.

    Args:
        trade_date: Trade date in YYYY-MM-DD format
    """
    print(f"Starting index daily fetch for {trade_date}...")

    trade_date_str = trade_date.replace('-', '')
    success_count = 0

    for ts_code, index_name in INDICES:
        try:
            # Try Tushare first
            df = tushare_get_index(ts_code, trade_date_str, trade_date_str)

            # Fallback to AkShare if empty
            if df.empty:
                # Convert Tushare code to AkShare format
                akshare_code = ts_code.split('.')[0]
                df = akshare_get_index(akshare_code, trade_date_str, trade_date_str)

            if not df.empty:
                row = df.iloc[0]

                with engine.connect() as conn:
                    conn.execute(
                        text("""
                            INSERT INTO market_breadth_daily
                            (trade_date, index_code, index_name, advance_count, decline_count, unchanged_count, advance_rate, total_amount)
                            VALUES (:trade_date, :index_code, :index_name, :advance_count, :decline_count, :unchanged_count, :advance_rate, :total_amount)
                            ON CONFLICT (trade_date) DO UPDATE SET
                                index_code = EXCLUDED.index_code,
                                index_name = EXCLUDED.index_name,
                                total_amount = EXCLUDED.total_amount
                        """),
                        {
                            'trade_date': trade_date,
                            'index_code': ts_code,
                            'index_name': index_name,
                            'advance_count': 0,  # Index data doesn't have this
                            'decline_count': 0,
                            'unchanged_count': 0,
                            'advance_rate': 0.0,
                            'total_amount': float(row.get('amount', 0))
                        }
                    )
                    conn.commit()

                print(f"  Fetched {index_name}: close={row.get('close')}, pct_change={row.get('pct_change')}")
                success_count += 1
            else:
                print(f"  No data for {index_name}")

        except Exception as e:
            print(f"Error fetching index {ts_code}: {e}")

    print(f"\nSuccessfully fetched {success_count}/{len(INDICES)} index data")
    return success_count > 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, help='Trade date (YYYY-MM-DD)')
    args = parser.parse_args()

    trade_date = args.date or datetime.now().strftime('%Y-%m-%d')
    success = fetch_index_daily_for_date(trade_date)
    sys.exit(0 if success else 1)