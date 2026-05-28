"""
Market-level CIS indicators calculation.
Calculates indicators like 20-day high, trend slope, volume expansion, etc.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from data.loaders.db_loader import engine, get_latest_daily_bar
from sqlalchemy import text

def calculate_market_indicators(trade_date: str) -> dict:
    """
    Calculate market-level CIS indicators for a given date.

    Args:
        trade_date: Trade date in YYYY-MM-DD format

    Returns:
        dict with market indicators:
        - index_20d_high: bool - 是否处于20日高位
        - index_55d_high: bool - 是否处于55日高位
        - drawdown_depth: float - 回撤深度
        - trend_slope: float - 20日趋势斜率
        - volume_5d_avg: float - 5日成交额均值
        - volume_20d_avg: float - 20日成交额均值
        - volume_expanding: bool - 是否连续放量
        - sector_diffusion_rate: float - 板块扩散率
        - market_environment: str - 市场环境 (trend/震荡/high_risk/emotion_peak)
    """
    indicators = {
        'trade_date': trade_date,
        'index_20d_high': False,
        'index_55d_high': False,
        'drawdown_depth': 0.0,
        'trend_slope': 0.0,
        'volume_5d_avg': 0.0,
        'volume_20d_avg': 0.0,
        'volume_expanding': False,
        'sector_diffusion_rate': 0.0,
        'market_environment': 'unknown'
    }

    try:
        # Get index data (use 上证指数 as market proxy)
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT close, amount, high, low
                    FROM daily_bar
                    WHERE code = '000001' AND trade_date <= :date
                    ORDER BY trade_date DESC
                    LIMIT 60
                """),
                {'date': trade_date}
            )
            rows = result.fetchall()

        if not rows:
            print("No market data found for index")
            return indicators

        # Convert to DataFrame (newest first)
        df = pd.DataFrame(rows, columns=['close', 'amount', 'high', 'low'])
        df = df.iloc[::-1]  # Reverse to chronological order

        if len(df) < 20:
            print(f"Not enough data: {len(df)} days")
            return indicators

        current_close = df['close'].iloc[-1]
        current_amount = df['amount'].iloc[-1]

        # 20日高点
        high_20d = df['high'].rolling(20).max().iloc[-2]  # Shift by 1 to avoid look-ahead
        indicators['index_20d_high'] = current_close >= high_20d

        # 55日高点
        if len(df) >= 55:
            high_55d = df['high'].rolling(55).max().iloc[-2]
            indicators['index_55d_high'] = current_close >= high_55d

        # 回撤深度
        if indicators['index_20d_high']:
            indicators['drawdown_depth'] = 0.0
        else:
            indicators['drawdown_depth'] = ((high_20d - current_close) / high_20d * 100).round(2)

        # 趋势斜率 (20日线性回归)
        if len(df) >= 20:
            y = df['close'].iloc[-20:].values
            x = np.arange(20)
            slope, _ = np.polyfit(x, y, 1)
            indicators['trend_slope'] = round(slope, 4)

        # 成交额中枢
        if len(df) >= 5:
            indicators['volume_5d_avg'] = df['amount'].iloc[-5:].mean()
        if len(df) >= 20:
            indicators['volume_20d_avg'] = df['amount'].iloc[-20:].mean()

        # 是否连续放量 (今日 > 20日均量)
        indicators['volume_expanding'] = current_amount > indicators['volume_20d_avg'] * 1.2

        # 板块扩散率
        indicators['sector_diffusion_rate'] = calculate_sector_diffusion(trade_date)

        # 市场环境判断
        indicators['market_environment'] = determine_market_environment(indicators)

    except Exception as e:
        print(f"Error calculating market indicators: {e}")

    return indicators

def calculate_sector_diffusion(trade_date: str) -> float:
    """
    Calculate sector diffusion rate.
    Returns the proportion of sectors that are expanding in volume.
    """
    try:
        with engine.connect() as conn:
            # Get sectors with volume expansion
            result = conn.execute(
                text("""
                    WITH sector_stats AS (
                        SELECT
                            sector_code,
                            amount,
                            AVG(amount) OVER (PARTITION BY sector_code ORDER BY trade_date ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING) as avg_amount_20d
                        FROM sector_daily
                        WHERE trade_date = :date
                    )
                    SELECT
                        COUNT(*) FILTER (WHERE amount > avg_amount_20d * 1.2) as expanding_count,
                        COUNT(*) as total_count
                    FROM sector_stats
                """),
                {'date': trade_date}
            )
            row = result.fetchone()

            if row and row[1] > 0:
                return round(row[0] / row[1] * 100, 2)
    except Exception as e:
        print(f"Error calculating sector diffusion: {e}")

    return 0.0

def determine_market_environment(indicators: dict) -> str:
    """
    Determine market environment based on indicators.

    Returns:
        - 'trend': 趋势市 (uptrend confirmed)
        - '震荡': 震荡市 (no clear direction)
        - 'high_risk': 高风险市 (high level, showing weakness)
        - 'emotion_peak': 情绪高潮市 (euphoria, too bullish)
    """
    trend_score = 0

    # 上涨趋势加分
    if indicators['index_20d_high']:
        trend_score += 2
    if indicators['trend_slope'] > 0:
        trend_score += 1
    if indicators['volume_expanding']:
        trend_score += 1
    if indicators['sector_diffusion_rate'] > 50:
        trend_score += 2

    # 回撤过深减分
    if indicators['drawdown_depth'] > 5:
        trend_score -= 2
    elif indicators['drawdown_depth'] > 3:
        trend_score -= 1

    if trend_score >= 4:
        return 'trend'
    elif trend_score >= 2:
        return '震荡'
    elif indicators['drawdown_depth'] > 5:
        return 'high_risk'
    else:
        return '震荡'

def save_market_indicators(trade_date: str):
    """Save market indicators to cis_indicator_snapshot table"""
    indicators = calculate_market_indicators(trade_date)

    with engine.connect() as conn:
        for key, value in indicators.items():
            if key == 'trade_date' or key == 'market_environment':
                continue

            conn.execute(
                text("""
                    INSERT INTO cis_indicator_snapshot
                    (trade_date, entity_type, entity_code, indicator_name, indicator_value)
                    VALUES (:trade_date, 'market', '000001', :indicator_name, :indicator_value)
                    ON CONFLICT DO NOTHING
                """),
                {
                    'trade_date': trade_date,
                    'indicator_name': key,
                    'indicator_value': float(value) if isinstance(value, (int, float)) else 0
                }
            )
        conn.commit()

    print(f"Saved market indicators for {trade_date}")
    return indicators

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, help='Trade date (YYYY-MM-DD)')
    args = parser.parse_args()

    from datetime import datetime
    trade_date = args.date or datetime.now().strftime('%Y-%m-%d')

    indicators = calculate_market_indicators(trade_date)
    print(f"\nMarket Indicators for {trade_date}:")
    for key, value in indicators.items():
        print(f"  {key}: {value}")