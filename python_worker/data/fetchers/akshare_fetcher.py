"""
AkShare data fetcher for A-shares stock market data.
Handles stock list, daily bars, sector data, and index data.
"""
import akshare as ak
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta

def get_stock_list() -> pd.DataFrame:
    """
    Fetch all A-shares stock list from AkShare.
    Returns DataFrame with columns: code, name
    """
    df = ak.stock_info_a_code_name()
    df.columns = ['code', 'name']
    # Filter out ST stocks and ensure valid codes
    df = df[df['code'].str.startswith(('0', '3', '6'))]
    return df

def get_daily_bar(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch daily bar data for a single stock.

    Args:
        code: Stock code (e.g., '000001')
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format

    Returns:
        DataFrame with columns: date, open, high, low, close, volume, amount, turnover_rate, pct_change, amplitude
    """
    try:
        # AkShare stock daily data
        df = ak.stock_zh_a_hist(symbol=code, start_date=start_date, end_date=end_date, adjust="qfq")

        # Rename columns to standard format
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '换手率': 'turnover_rate',
            '涨跌幅': 'pct_change',
            '振幅': 'amplitude'
        })

        # Convert date format
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

        # Add stock code
        df['code'] = code

        return df[['code', 'date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'turnover_rate', 'pct_change', 'amplitude']]
    except Exception as e:
        print(f"Error fetching daily bar for {code}: {e}")
        return pd.DataFrame()

def get_sector_list() -> pd.DataFrame:
    """
    Fetch sector/industry list from AkShare.
    Returns DataFrame with columns: sector_code, sector_name
    """
    try:
        df = ak.stock_board_industry_name_em()
        df = df.rename(columns={
            '板块名称': 'sector_name',
            '涨跌幅': 'pct_change',
            '总市值': 'total_market_cap',
            '成交额': 'amount'
        })
        df['sector_code'] = df['sector_name']  # Use name as code for now
        return df[['sector_code', 'sector_name', 'pct_change', 'amount']]
    except Exception as e:
        print(f"Error fetching sector list: {e}")
        return pd.DataFrame()

def get_sector_daily(sector_name: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch sector daily data from AkShare.

    Args:
        sector_name: Sector/industry name
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format

    Returns:
        DataFrame with sector daily data
    """
    try:
        df = ak.stock_board_industry_hist_em(symbol=sector_name, start_date=start_date, end_date=end_date, period="日k")
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '涨跌幅': 'pct_change'
        })
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df['sector_name'] = sector_name
        return df
    except Exception as e:
        print(f"Error fetching sector daily for {sector_name}: {e}")
        return pd.DataFrame()

def get_index_daily(index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch index daily data from AkShare.

    Args:
        index_code: Index code (e.g., '000001' for 上证指数, '399001' for 深证成指)
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format

    Returns:
        DataFrame with index daily data
    """
    try:
        df = ak.index_zh_a_hist(symbol=index_code, start_date=start_date, end_date=end_date, adjust="qfq")
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '涨跌幅': 'pct_change',
            '振幅': 'amplitude'
        })
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df['index_code'] = index_code
        return df[['index_code', 'date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_change', 'amplitude']]
    except Exception as e:
        print(f"Error fetching index daily for {index_code}: {e}")
        return pd.DataFrame()

def get_market_breadth(trade_date: str) -> Dict:
    """
    Fetch market breadth data (advance/decline counts) for a specific date.

    Args:
        trade_date: Trade date in YYYYMMDD format

    Returns:
        Dict with advance_count, decline_count, unchanged_count, advance_rate
    """
    try:
        df = ak.stock_market_bid_award_em()
        # Filter to the specific date
        df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y%m%d')
        df = df[df['日期'] == trade_date.replace('-', '')]

        if df.empty:
            # Return zeros if no data for that date
            return {
                'trade_date': trade_date,
                'advance_count': 0,
                'decline_count': 0,
                'unchanged_count': 0,
                'advance_rate': 0.0
            }

        return {
            'trade_date': trade_date,
            'advance_count': int(df['上涨家数'].iloc[0]) if '上涨家数' in df.columns else 0,
            'decline_count': int(df['下跌家数'].iloc[0]) if '下跌家数' in df.columns else 0,
            'unchanged_count': int(df['平盘家数'].iloc[0]) if '平盘家数' in df.columns else 0,
            'advance_rate': float(df['上涨家数'].iloc[0] / (df['上涨家数'].iloc[0] + df['下跌家数'].iloc[0])) if '上涨家数' in df.columns and '下跌家数' in df.columns else 0.0
        }
    except Exception as e:
        print(f"Error fetching market breadth for {trade_date}: {e}")
        return {
            'trade_date': trade_date,
            'advance_count': 0,
            'decline_count': 0,
            'unchanged_count': 0,
            'advance_rate': 0.0
        }

# Test function
if __name__ == "__main__":
    print("Testing AkShare fetcher...")

    # Test stock list
    print("\n1. Testing get_stock_list()...")
    stock_list = get_stock_list()
    print(f"   Stock list count: {len(stock_list)}")
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

    print("\n All AkShare fetcher tests passed!")