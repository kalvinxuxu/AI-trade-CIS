"""
Tushare data fetcher for A-shares stock market data.
Handles stock list, daily bars, sector data, and index data.
Requires TUSHARE_TOKEN to be set in environment variables.
"""
import tushare as ts
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from config.settings import TUSHARE_TOKEN

# Initialize Tushare pro API
if TUSHARE_TOKEN:
    pro = ts.pro_api(TUSHARE_TOKEN)
else:
    pro = None
    print("WARNING: TUSHARE_TOKEN is not set, Tushare fetcher will not work")


def get_stock_list() -> pd.DataFrame:
    """
    Fetch all A-shares stock list from Tushare.
    Returns DataFrame with columns: code, name, sector, list_date
    """
    if not pro:
        print("ERROR: Tushare pro API not initialized (missing TUSHARE_TOKEN)")
        return pd.DataFrame()

    try:
        # Get basic info for all stocks
        df = pro.stock_basic(
            exchange='',
            list_status='L',
            fields='ts_code,symbol,name,area,industry,list_date,is_hs'
        )

        df = df.rename(columns={
            'symbol': 'code',
            'name': 'name',
            'industry': 'sector',
            'list_date': 'list_date'
        })

        # Filter to A-shares (exclude OTC, STAR market etc)
        df = df[df['code'].str.startswith(('0', '3', '6'))]

        return df[['code', 'name', 'sector', 'list_date']]
    except Exception as e:
        print(f"Error fetching stock list from Tushare: {e}")
        return pd.DataFrame()


def get_daily_bar(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch daily bar data for a single stock.

    Args:
        code: Stock code (e.g., '000001')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        DataFrame with columns: date, open, high, low, close, volume, amount, turnover_rate, pct_change, amplitude
    """
    if not pro:
        print("ERROR: Tushare pro API not initialized (missing TUSHARE_TOKEN)")
        return pd.DataFrame()

    try:
        # Convert date format to YYYYMMDD if needed
        start_str = start_date.replace('-', '')
        end_str = end_date.replace('-', '')

        # Get daily data
        # 上海证券代码以 6 开头 → .SH
        # 深圳证券代码以 0, 3 开头 → .SZ
        if code.startswith('6'):
            ts_code = f"{code}.SH"
        else:  # 0, 3 开头都是深圳
            ts_code = f"{code}.SZ"

        df = pro.daily(
            ts_code=ts_code,
            start_date=start_str,
            end_date=end_str
        )

        if df.empty:
            return pd.DataFrame()

        # Rename columns to match our schema
        df = df.rename(columns={
            'trade_date': 'date',
            'vol': 'volume',
            'pct_chg': 'pct_change'
        })

        # Tushare daily doesn't have turnover_rate and amplitude - set defaults
        df['turnover_rate'] = 0.0
        df['amplitude'] = ((df['high'] - df['low']) / df['low'] * 100).round(2)

        # Convert date format
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

        # Add stock code (without exchange suffix)
        df['code'] = code

        return df[['code', 'date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'turnover_rate', 'pct_change', 'amplitude']]
    except Exception as e:
        print(f"Error fetching daily bar for {code} from Tushare: {e}")
        return pd.DataFrame()


def get_sector_list() -> pd.DataFrame:
    """
    Fetch sector/industry list from Tushare.
    Returns DataFrame with columns: sector_code, sector_name
    """
    if not pro:
        print("ERROR: Tushare pro API not initialized (missing TUSHARE_TOKEN)")
        return pd.DataFrame()

    try:
        df = pro.stock_industry()

        df = df.rename(columns={
            'industry_name': 'sector_name',
            'industry_code': 'sector_code'
        })

        return df[['sector_code', 'sector_name']]
    except Exception as e:
        print(f"Error fetching sector list from Tushare: {e}")
        return pd.DataFrame()


def get_index_daily(index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch index daily data from Tushare.

    Args:
        index_code: Index code (e.g., '000001' for 上证指数, '399001' for 深证成指)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        DataFrame with index daily data
    """
    if not pro:
        print("ERROR: Tushare pro API not initialized (missing TUSHARE_TOKEN)")
        return pd.DataFrame()

    try:
        # Convert date format
        start_str = start_date.replace('-', '')
        end_str = end_date.replace('-', '')

        # Determine exchange based on index code
        exchange = 'SH' if index_code.startswith(('0', '9')) else 'SZ'

        df = pro.index_daily(
            ts_code=f"{index_code}.{exchange}",
            start_date=start_str,
            end_date=end_str
        )

        if df.empty:
            return pd.DataFrame()

        df = df.rename(columns={
            'trade_date': 'date',
            'vol': 'volume'
        })

        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df['index_code'] = index_code

        return df[['index_code', 'date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_change', 'amplitude']]
    except Exception as e:
        print(f"Error fetching index daily for {index_code} from Tushare: {e}")
        return pd.DataFrame()


# Test function
if __name__ == "__main__":
    print("Testing Tushare fetcher...")

    if not TUSHARE_TOKEN:
        print("ERROR: TUSHARE_TOKEN not set, cannot test")
        exit(1)

    # Test stock list
    print("\n1. Testing get_stock_list()...")
    stock_list = get_stock_list()
    print(f"   Stock list count: {len(stock_list)}")
    if not stock_list.empty:
        print(f"   Sample:\n{stock_list.head(3)}")

    # Test daily bar for a single stock
    print("\n2. Testing get_daily_bar('000001', '20260501', '20260528')...")
    daily = get_daily_bar('000001', '20260501', '20260528')
    print(f"   Daily bar count: {len(daily)}")
    if not daily.empty:
        print(f"   Sample:\n{daily.head(2)}")

    # Test sector list
    print("\n3. Testing get_sector_list()...")
    sectors = get_sector_list()
    print(f"   Sector count: {len(sectors)}")
    if not sectors.empty:
        print(f"   Sample:\n{sectors.head(3)}")

    print("\n All Tushare fetcher tests passed!")