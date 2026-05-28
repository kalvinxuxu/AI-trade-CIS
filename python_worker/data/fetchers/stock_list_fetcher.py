"""
Sync stock list from data sources to database.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from data.fetchers.akshare_fetcher import get_stock_list as akshare_get_list
from data.fetchers.tushare_fetcher import get_stock_list as tushare_get_list
from data.loaders.db_loader import engine
from sqlalchemy import text
import pandas as pd

def sync_stock_list():
    """
    Sync stock list from data sources to instrument_master table.
    Uses Tushare as primary, AkShare as fallback.
    """
    print("Starting stock list sync...")

    # Try Tushare first
    df = tushare_get_list()
    if df.empty:
        print("Tushare stock list empty, trying AkShare...")
        df = akshare_get_list()

    if df.empty:
        print("ERROR: Both Tushare and AkShare returned empty stock list")
        return False

    print(f"Fetched {len(df)} stocks from data source")

    # Insert to database
    with engine.connect() as conn:
        # Clear existing data
        conn.execute(text("DELETE FROM instrument_master"))

        # Insert new data
        for _, row in df.iterrows():
            try:
                conn.execute(
                    text("""
                        INSERT INTO instrument_master (code, name, sector, list_date)
                        VALUES (:code, :name, :sector, :list_date)
                        ON CONFLICT (code) DO UPDATE SET
                            name = EXCLUDED.name,
                            sector = EXCLUDED.sector,
                            list_date = EXCLUDED.list_date
                    """),
                    {
                        'code': str(row['code']),
                        'name': str(row['name']) if pd.notna(row.get('name')) else '',
                        'sector': str(row.get('sector', '')) if pd.notna(row.get('sector')) else '',
                        'list_date': row.get('list_date', None)
                    }
                )
            except Exception as e:
                print(f"Error inserting {row.get('code')}: {e}")

        conn.commit()

    print(f"Successfully synced {len(df)} stocks to database")

    # Verify
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM instrument_master"))
        count = result.scalar()
        print(f"Database now has {count} stocks")

    return True

if __name__ == "__main__":
    success = sync_stock_list()
    sys.exit(0 if success else 1)