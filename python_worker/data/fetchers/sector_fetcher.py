"""
Fetch sector/industry data and save to database.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from data.fetchers.akshare_fetcher import get_sector_list, get_sector_daily
from data.fetchers.tushare_fetcher import get_index_daily
from data.loaders.db_loader import engine
from sqlalchemy import text
from datetime import datetime

def sync_sector_list():
    """Sync sector list to database (stored in memory for now as sector_daily is computed)"""
    print("Starting sector list sync...")
    df = get_sector_list()
    print(f"Fetched {len(df)} sectors")
    return df

def fetch_sector_daily_for_date(trade_date: str):
    """
    Fetch daily data for all sectors for a specific date.

    Args:
        trade_date: Trade date in YYYY-MM-DD format
    """
    print(f"Starting sector daily fetch for {trade_date}...")

    # Get sector list
    sectors = sync_sector_list()
    if sectors.empty:
        print("No sectors found")
        return False

    trade_date_str = trade_date.replace('-', '')
    success_count = 0

    with engine.connect() as conn:
        for _, sector in sectors.iterrows():
            try:
                sector_name = sector['sector_name']
                df = get_sector_daily(sector_name, trade_date_str, trade_date_str)

                if not df.empty:
                    row = df.iloc[0]
                    conn.execute(
                        text("""
                            INSERT INTO sector_daily
                            (sector_code, sector_name, trade_date, amount, volume, pct_change, member_count, avg_pct_change)
                            VALUES (:sector_code, :sector_name, :trade_date, :amount, :volume, :pct_change, :member_count, :avg_pct_change)
                            ON CONFLICT (sector_code, trade_date) DO UPDATE SET
                                amount = EXCLUDED.amount,
                                volume = EXCLUDED.volume,
                                pct_change = EXCLUDED.pct_change
                        """),
                        {
                            'sector_code': sector_name,
                            'sector_name': sector_name,
                            'trade_date': trade_date,
                            'amount': float(row.get('amount', 0)),
                            'volume': int(row.get('volume', 0)),
                            'pct_change': float(row.get('pct_change', 0)),
                            'member_count': 0,  # AkShare doesn't provide this directly
                            'avg_pct_change': float(row.get('pct_change', 0))
                        }
                    )
                    success_count += 1
            except Exception as e:
                print(f"Error fetching sector {sector.get('sector_name')}: {e}")

        conn.commit()

    print(f"Successfully fetched {success_count}/{len(sectors)} sector data")
    return success_count > 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, help='Trade date (YYYY-MM-DD)')
    args = parser.parse_args()

    trade_date = args.date or datetime.now().strftime('%Y-%m-%d')
    success = fetch_sector_daily_for_date(trade_date)
    sys.exit(0 if success else 1)