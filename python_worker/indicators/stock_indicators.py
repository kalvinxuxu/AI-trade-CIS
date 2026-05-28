"""
Stock-level CIS indicators calculation.
Calculates indicators like breakout, volume acceleration, sector consensus, etc.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from data.loaders.db_loader import engine
from sqlalchemy import text

def calculate_stock_indicators(code: str, trade_date: str) -> dict:
    """
    Calculate stock-level CIS indicators for a given stock and date.

    Args:
        code: Stock code (e.g., '000001')
        trade_date: Trade date in YYYY-MM-DD format

    Returns:
        dict with stock indicators:
        - breakout_20d: bool - 突破20日高点
        - breakout_55d: bool - 突破55日高点
        - rs_strength: float - RS强度 (relative strength vs market)
        - drawdown_depth: float - 回撤深度
        - fund_acceleration: bool - 资金强化 (volume expansion)
        - consecutive_volume_days: int - 连续放量天数
        - trend_acceleration: float - 趋势加速 (5日斜率/20日斜率)
        - sector_in_sync: bool - 板块同步
        - pct_change_5d: float - 5日涨跌幅
        - pct_change_20d: float - 20日涨跌幅
    """
    indicators = {
        'code': code,
        'trade_date': trade_date,
        'breakout_20d': False,
        'breakout_55d': False,
        'rs_strength': 1.0,
        'drawdown_depth': 0.0,
        'fund_acceleration': False,
        'consecutive_volume_days': 0,
        'trend_acceleration': 0.0,
        'sector_in_sync': False,
        'pct_change_5d': 0.0,
        'pct_change_20d': 0.0,
        'amount_ratio_20d': 1.0  # 成交额/20日均量
    }

    try:
        # Get stock data (60 days for calculations)
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT trade_date, open, high, low, close, volume, amount, pct_change
                    FROM daily_bar
                    WHERE code = :code AND trade_date <= :date
                    ORDER BY trade_date DESC
                    LIMIT 60
                """),
                {'code': code, 'date': trade_date}
            )
            rows = result.fetchall()

        if not rows or len(rows) < 20:
            return indicators

        # Convert to DataFrame (newest last)
        df = pd.DataFrame(rows, columns=['trade_date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_change'])
        df = df.iloc[::-1]

        current = df.iloc[-1]
        current_close = current['close']
        current_amount = current['amount']

        # 20日高点 (previous day)
        high_20d = df['high'].iloc[-21:-1].max() if len(df) > 20 else df['high'].max()
        indicators['breakout_20d'] = current_close > high_20d

        # 55日高点 (previous day)
        if len(df) >= 55:
            high_55d = df['high'].iloc[-56:-1].max()
            indicators['breakout_55d'] = current_close > high_55d
        else:
            indicators['breakout_55d'] = current_close > df['high'].max()

        # 回撤深度
        if indicators['breakout_20d']:
            indicators['drawdown_depth'] = 0.0
        else:
            indicators['drawdown_depth'] = ((high_20d - current_close) / high_20d * 100).round(2)

        # 成交额相关
        if len(df) >= 20:
            amount_20d_avg = df['amount'].iloc[-20:].mean()
            indicators['amount_ratio_20d'] = round(current_amount / amount_20d_avg, 2) if amount_20d_avg > 0 else 1.0
            indicators['fund_acceleration'] = indicators['amount_ratio_20d'] > 1.5

            # 连续放量天数
            volume_above_avg = df['amount'].iloc[-5:] > df['amount'].iloc[-20:].mean()
            indicators['consecutive_volume_days'] = int(volume_above_avg.sum())

        # 趋势加速 (5日斜率 / 20日斜率)
        if len(df) >= 20:
            # 20日斜率
            y_20 = df['close'].iloc[-20:].values
            x_20 = np.arange(20)
            slope_20, _ = np.polyfit(x_20, y_20, 1)

            # 5日斜率
            if len(df) >= 5:
                y_5 = df['close'].iloc[-5:].values
                x_5 = np.arange(5)
                slope_5, _ = np.polyfit(x_5, y_5, 1)

                if slope_20 > 0:
                    indicators['trend_acceleration'] = round(slope_5 / slope_20, 2)
                else:
                    indicators['trend_acceleration'] = 0.0

        # 5日/20日涨跌幅
        if len(df) >= 5:
            indicators['pct_change_5d'] = ((df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5] * 100).round(2)
        if len(df) >= 20:
            indicators['pct_change_20d'] = ((df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20] * 100).round(2)

        # RS强度 (相对大盘强弱)
        try:
            # Get market index data
            with engine.connect() as conn:
                market_result = conn.execute(
                    text("""
                        SELECT close FROM daily_bar
                        WHERE code = '000001' AND trade_date <= :date
                        ORDER BY trade_date DESC LIMIT 20
                    """),
                    {'date': trade_date}
                )
                market_rows = market_result.fetchall()

            if market_rows and len(market_rows) >= 5:
                market_df = pd.DataFrame(market_rows, columns=['close'])
                market_df = market_df.iloc[::-1]

                stock_pct = indicators['pct_change_5d']
                market_pct = ((market_df['close'].iloc[-1] - market_df['close'].iloc[-5]) / market_df['close'].iloc[-5] * 100)

                if market_pct != 0:
                    indicators['rs_strength'] = round(stock_pct / market_pct, 2)
        except Exception as e:
            print(f"Error calculating RS strength: {e}")

        # 板块同步 (简化版：检查板块是否跟涨)
        indicators['sector_in_sync'] = calculate_sector_sync(code, trade_date, df)

    except Exception as e:
        print(f"Error calculating stock indicators for {code}: {e}")

    return indicators

def calculate_sector_sync(code: str, trade_date: str, stock_df: pd.DataFrame) -> bool:
    """
    Check if stock's sector is in sync (sector is expanding along with stock).
    Simplified: Check if stock's trend matches average sector trend.
    """
    try:
        # Get sector data for this stock
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT sector_code FROM instrument_master WHERE code = :code
                """),
                {'code': code}
            )
            row = result.fetchone()
            if not row or not row[0]:
                return False
            sector_code = row[0]

        # Get sector daily data
        with engine.connect() as conn:
            sector_result = conn.execute(
                text("""
                    SELECT pct_change FROM sector_daily
                    WHERE sector_code = :sector AND trade_date <= :date
                    ORDER BY trade_date DESC LIMIT 5
                """),
                {'sector': sector_code, 'date': trade_date}
            )
            sector_rows = sector_result.fetchall()

        if not sector_rows or len(sector_rows) < 3:
            return False

        # Average sector performance
        sector_avg_pct = np.mean([r[0] for r in sector_rows])
        stock_avg_pct = stock_df['pct_change'].iloc[-5:].mean()

        # Stock in sync if both positive or stock outperforming
        return sector_avg_pct > 0 or stock_avg_pct > sector_avg_pct

    except Exception as e:
        return False

def calculate_all_stock_indicators(trade_date: str):
    """
    Calculate indicators for all stocks and save to database.
    This is the main function called by --step calc_all_indicators.
    """
    print(f"Calculating stock indicators for {trade_date}...")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT code FROM instrument_master ORDER BY code"))
        stock_codes = [row[0] for row in result.fetchall()]

    print(f"Processing {len(stock_codes)} stocks...")

    success_count = 0
    for i, code in enumerate(stock_codes):
        try:
            indicators = calculate_stock_indicators(code, trade_date)
            save_stock_indicators(indicators)
            success_count += 1
        except Exception as e:
            print(f"Error processing {code}: {e}")

        if (i + 1) % 100 == 0:
            print(f"Progress: {i + 1}/{len(stock_codes)}")

    print(f"\nCompleted: {success_count}/{len(stock_codes)} stocks processed")
    return success_count

def save_stock_indicators(indicators: dict):
    """Save stock indicators to cis_indicator_snapshot table"""
    with engine.connect() as conn:
        for key, value in indicators.items():
            if key in ('code', 'trade_date'):
                continue

            conn.execute(
                text("""
                    INSERT INTO cis_indicator_snapshot
                    (trade_date, entity_type, entity_code, indicator_name, indicator_value)
                    VALUES (:trade_date, 'stock', :entity_code, :indicator_name, :indicator_value)
                    ON CONFLICT DO NOTHING
                """),
                {
                    'trade_date': indicators['trade_date'],
                    'entity_code': indicators['code'],
                    'indicator_name': key,
                    'indicator_value': float(value) if isinstance(value, (int, float)) else 0
                }
            )
        conn.commit()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, help='Trade date (YYYY-MM-DD)')
    parser.add_argument('--code', type=str, help='Stock code (single stock test)')
    args = parser.parse_args()

    from datetime import datetime
    trade_date = args.date or datetime.now().strftime('%Y-%m-%d')

    if args.code:
        indicators = calculate_stock_indicators(args.code, trade_date)
        print(f"\nStock Indicators for {args.code} on {trade_date}:")
        for key, value in indicators.items():
            print(f"  {key}: {value}")
    else:
        calculate_all_stock_indicators(trade_date)