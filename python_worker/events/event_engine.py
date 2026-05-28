"""
CIS Event Detection Engine.
Identifies 7 types of events that indicate stock trend changes.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from data.loaders.db_loader import engine
from sqlalchemy import text
from typing import List, Dict

# Event definitions
EVENT_DEFINITIONS = {
    'breakout_confirmed': {
        'name': '突破确认',
        'description': '突破20日高点 + 放量 + 2日未跌回',
        'severity': 'positive'
    },
    'acceleration_started': {
        'name': '加速启动',
        'description': '5日斜率明显高于20日斜率 + 连续上涨',
        'severity': 'positive'
    },
    'sector_diffusion_expanding': {
        'name': '板块扩散',
        'description': '板块跟涨率提升 + 板块成交额扩张',
        'severity': 'positive'
    },
    'first_rejection_signal': {
        'name': '首次拒绝信号',
        'description': '高开低走 + 放量不涨（替代新闻利好反馈）',
        'severity': 'warning'
    },
    'volume_stall_detected': {
        'name': '量价stall',
        'description': '成交额 > 20日均量2倍，但涨幅很小',
        'severity': 'warning'
    },
    'leadership_isolation': {
        'name': '龙头孤立',
        'description': '个股强，但板块跟涨率低',
        'severity': 'danger'
    },
    'trend_decay_started': {
        'name': '趋势衰减',
        'description': '资金衰减 + 板块衰减 + 不再创新高',
        'severity': 'danger'
    }
}

def detect_breakout_confirmed(code: str, trade_date: str, df: pd.DataFrame) -> bool:
    """
    Detect breakout_confirmed event.
    Conditions: 突破20日高点 + 放量 + 2日未跌回
    """
    if len(df) < 3:
        return False

    current = df.iloc[-1]
    prev2 = df.iloc[-3]

    # 突破20日高点
    high_20d = df['high'].iloc[-21:-1].max()
    breakout = current['close'] > high_20d

    # 放量 (今日成交额 > 20日均量 * 1.5)
    amount_20d_avg = df['amount'].iloc[-20:].mean()
    volume_expanded = current['amount'] > amount_20d_avg * 1.5

    # 2日未跌回突破位
    not_rejected = prev2['close'] >= high_20d * 0.98  # 允许2%回撤

    return breakout and volume_expanded and not_rejected

def detect_acceleration_started(code: str, trade_date: str, df: pd.DataFrame) -> bool:
    """
    Detect acceleration_started event.
    Conditions: 5日斜率 > 20日斜率 * 1.5 + 连续3日上涨
    """
    if len(df) < 20:
        return False

    # 20日斜率
    y_20 = df['close'].iloc[-20:].values
    x_20 = np.arange(20)
    slope_20, _ = np.polyfit(x_20, y_20, 1)

    # 5日斜率
    y_5 = df['close'].iloc[-5:].values
    x_5 = np.arange(5)
    slope_5, _ = np.polyfit(x_5, y_5, 1)

    # 加速条件
    accelerating = slope_5 > slope_20 * 1.5 if slope_20 > 0 else slope_5 > slope_20

    # 连续3日上涨
    consecutive_up = (df['pct_change'].iloc[-3:] > 0).all()

    return accelerating and consecutive_up

def detect_sector_diffusion_expanding(code: str, trade_date: str, df: pd.DataFrame) -> bool:
    """
    Detect sector_diffusion_expanding event.
    Simplified: Check if stock is rising AND sector is also rising strongly.
    """
    if len(df) < 5:
        return False

    stock_rising = df['pct_change'].iloc[-1] > 2  # 个股涨幅 > 2%

    # Check sector performance (simplified)
    try:
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

            sector_result = conn.execute(
                text("""
                    SELECT pct_change FROM sector_daily
                    WHERE sector_code = :sector AND trade_date = :date
                """),
                {'sector': row[0], 'date': trade_date}
            )
            sector_row = sector_result.fetchone()

            if sector_row:
                sector_rising = sector_row[0] > 1.5  # 板块涨幅 > 1.5%
                return stock_rising and sector_rising
    except:
        pass

    return False

def detect_first_rejection_signal(code: str, trade_date: str, df: pd.DataFrame) -> bool:
    """
    Detect first_rejection_signal event.
    Conditions: 高开低走 + 放量不涨（替代利好不涨）
    """
    if len(df) < 2:
        return False

    current = df.iloc[-1]
    prev = df.iloc[-2]

    # 高开低走: 开盘价 > 收盘价, 且收盘价下跌
    high_open_close = current['open'] > current['close'] and current['close'] < prev['close']

    # 放量: 成交额 > 20日均量 * 1.5
    amount_20d_avg = df['amount'].iloc[-20:].mean()
    volume_expanded = current['amount'] > amount_20d_avg * 1.5

    # 不涨: 涨幅很小
    not_rising = current['pct_change'] < 1

    return high_open_close and volume_expanded and not_rising

def detect_volume_stall_detected(code: str, trade_date: str, df: pd.DataFrame) -> bool:
    """
    Detect volume_stall_detected event.
    Conditions: 成交额 > 20日均量2倍，但涨幅很小
    """
    if len(df) < 20:
        return False

    current = df.iloc[-1]
    amount_20d_avg = df['amount'].iloc[-20:].mean()

    # 放量但涨幅小
    volume_large = current['amount'] > amount_20d_avg * 2
    price_stall = abs(current['pct_change']) < 1

    return volume_large and price_stall

def detect_leadership_isolation(code: str, trade_date: str, df: pd.DataFrame) -> bool:
    """
    Detect leadership_isolation event.
    Conditions: 个股涨幅 > 5% + 板块跟涨率低
    """
    if len(df) < 1:
        return False

    current = df.iloc[-1]

    # 个股强
    strong_leadership = current['pct_change'] > 5

    if not strong_leadership:
        return False

    # 板块跟涨率低
    try:
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

            # Get sector stocks that are rising
            sector_result = conn.execute(
                text("""
                    SELECT COUNT(*) FROM daily_bar db
                    JOIN instrument_master im ON db.code = im.code
                    WHERE im.sector = :sector AND db.trade_date = :date AND db.pct_change > 0
                """),
                {'sector': row[0], 'date': trade_date}
            )
            rising_count = sector_result.scalar() or 0

            # Get total sector stocks
            total_result = conn.execute(
                text("SELECT COUNT(*) FROM instrument_master WHERE sector = :sector"),
                {'sector': row[0]}
            )
            total_count = total_result.scalar() or 1

            follow_rate = rising_count / total_count
            return follow_rate < 0.3  # 跟涨率 < 30%
    except:
        return False

def detect_trend_decay_started(code: str, trade_date: str, df: pd.DataFrame) -> bool:
    """
    Detect trend_decay_started event.
    Conditions: 资金衰减 + 板块衰减 + 不再创新高
    """
    if len(df) < 20:
        return False

    current = df.iloc[-1]

    # 不再创新高
    high_20d = df['high'].iloc[-21:-1].max()
    not_breaking_high = current['close'] < high_20d * 0.95

    # 资金衰减 (成交额 < 20日均量)
    amount_20d_avg = df['amount'].iloc[-20:].mean()
    amount_decaying = current['amount'] < amount_20d_avg * 0.8

    # 板块衰减
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT sector_code FROM instrument_master WHERE code = :code
                """),
                {'code': code}
            )
            row = result.fetchone()
            if row and row[0]:
                sector_result = conn.execute(
                    text("""
                        SELECT pct_change FROM sector_daily
                        WHERE sector_code = :sector AND trade_date = :date
                    """),
                    {'sector': row[0], 'date': trade_date}
                )
                sector_row = sector_result.fetchone()
                sector_decaying = sector_row and sector_row[0] < -1
            else:
                sector_decaying = False
    except:
        sector_decaying = False

    return not_breaking_high and amount_decaying and sector_decaying

def detect_all_events(code: str, trade_date: str) -> List[Dict]:
    """
    Detect all events for a given stock and date.

    Returns:
        List of event dicts with keys: event_name, severity, triggered_at
    """
    events = []

    # Get stock data
    try:
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
            return events

        df = pd.DataFrame(rows, columns=['trade_date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_change'])
        df = df.iloc[::-1]

        # Detect each event
        event_detectors = {
            'breakout_confirmed': detect_breakout_confirmed,
            'acceleration_started': detect_acceleration_started,
            'sector_diffusion_expanding': detect_sector_diffusion_expanding,
            'first_rejection_signal': detect_first_rejection_signal,
            'volume_stall_detected': detect_volume_stall_detected,
            'leadership_isolation': detect_leadership_isolation,
            'trend_decay_started': detect_trend_decay_started
        }

        for event_name, detector_func in event_detectors.items():
            try:
                if detector_func(code, trade_date, df):
                    events.append({
                        'event_name': event_name,
                        'severity': EVENT_DEFINITIONS[event_name]['severity'],
                        'description': EVENT_DEFINITIONS[event_name]['description']
                    })
            except Exception as e:
                print(f"Error detecting {event_name} for {code}: {e}")

    except Exception as e:
        print(f"Error in detect_all_events for {code}: {e}")

    return events

def save_events(code: str, trade_date: str, events: List[Dict]):
    """Save detected events to cis_event_snapshot table"""
    if not events:
        return

    with engine.connect() as conn:
        for event in events:
            conn.execute(
                text("""
                    INSERT INTO cis_event_snapshot (trade_date, code, event_name, event_params)
                    VALUES (:trade_date, :code, :event_name, :event_params)
                    ON CONFLICT DO NOTHING
                """),
                {
                    'trade_date': trade_date,
                    'code': code,
                    'event_name': event['event_name'],
                    'event_params': {'severity': event['severity'], 'description': event['description']}
                }
            )
        conn.commit()

def detect_all_events_for_date(trade_date: str):
    """Detect events for all stocks on a given date"""
    print(f"Detecting events for {trade_date}...")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT code FROM instrument_master ORDER BY code"))
        stock_codes = [row[0] for row in result.fetchall()]

    print(f"Processing {len(stock_codes)} stocks...")

    total_events = 0
    for i, code in enumerate(stock_codes):
        try:
            events = detect_all_events(code, trade_date)
            if events:
                save_events(code, trade_date, events)
                total_events += len(events)
        except Exception as e:
            print(f"Error processing {code}: {e}")

        if (i + 1) % 100 == 0:
            print(f"Progress: {i + 1}/{len(stock_codes)} - Events found: {total_events}")

    print(f"\nEvent detection complete. Total events: {total_events}")
    return total_events

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, help='Trade date (YYYY-MM-DD)')
    parser.add_argument('--code', type=str, help='Stock code (single stock test)')
    args = parser.parse_args()

    from datetime import datetime
    trade_date = args.date or datetime.now().strftime('%Y-%m-%d')

    if args.code:
        events = detect_all_events(args.code, trade_date)
        print(f"\nEvents for {args.code} on {trade_date}:")
        if events:
            for event in events:
                print(f"  - {event['event_name']} ({event['severity']}): {event['description']}")
        else:
            print("  No events detected")
    else:
        detect_all_events_for_date(trade_date)