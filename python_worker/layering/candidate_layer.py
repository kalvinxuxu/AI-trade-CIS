"""
Candidate Layering Module.
Classifies stocks into Level 1 (主升候选), Level 2 (观察池), and Danger (危险区).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from typing import List, Dict
from data.loaders.db_loader import engine, upsert_candidate_snapshot
from sqlalchemy import text

# Action recommendations
ACTION_RECOMMENDATIONS = {
    'level1': '可重点观察 / 可交易候选',
    'level2': '继续观察',
    'danger_volume_stall': '减仓观察',
    'danger_trend_decay': '快速退出',
    'danger_leadership_isolation': '禁止加仓',
    'danger_rejection': '减仓观察',
    'danger_acceleration': '禁止加仓'
}

def get_stock_indicators(code: str, trade_date: str) -> dict:
    """Get all indicators for a stock from cis_indicator_snapshot"""
    indicators = {}

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT indicator_name, indicator_value
                FROM cis_indicator_snapshot
                WHERE entity_code = :code AND trade_date = :date AND entity_type = 'stock'
            """),
            {'code': code, 'date': trade_date}
        )

        for row in result.fetchall():
            indicators[row[0]] = row[1]

    return indicators

def get_stock_events(code: str, trade_date: str) -> List[str]:
    """Get all event names for a stock from cis_event_snapshot"""
    events = []

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT event_name FROM cis_event_snapshot
                WHERE code = :code AND trade_date = :date
            """),
            {'code': code, 'date': trade_date}
        )

        for row in result.fetchall():
            events.append(row[0])

    return events

def is_level1_candidate(indicators: dict, events: List[str]) -> bool:
    """
    Level 1: 主升候选
    必须同时满足：
    - 趋势确认 = true (breakout_20d or breakout_55d)
    - 资金强化 = true (fund_acceleration = true and consecutive_volume_days >= 3)
    - 板块同步 = true (sector_in_sync = true)
    - 危险事件 = false (no danger events)
    """
    # 趋势确认
    trend_confirm = indicators.get('breakout_20d', False) or indicators.get('breakout_55d', False)

    # 资金强化
    fund_acceleration = indicators.get('fund_acceleration', False)
    consecutive_volume = indicators.get('consecutive_volume_days', 0)
    fund_confirm = fund_acceleration and consecutive_volume >= 3

    # 板块同步
    sector_confirm = indicators.get('sector_in_sync', False)

    # 危险事件检查
    danger_events = ['volume_stall_detected', 'trend_decay_started', 'first_rejection_signal',
                     'leadership_isolation']
    has_danger = any(event in events for event in danger_events)

    return trend_confirm and fund_confirm and sector_confirm and not has_danger

def is_level2_candidate(indicators: dict, events: List[str]) -> bool:
    """
    Level 2: 观察池
    满足任一：
    - 趋势已成立，但资金不足
    - 趋势已成立，但板块不足
    - 接近突破（突破20日高点的80%）
    """
    # 趋势已成立
    trend_exists = indicators.get('breakout_20d', False) or indicators.get('breakout_55d', False)

    if trend_exists:
        # 趋势成立但资金或板块不足
        fund_acceleration = indicators.get('fund_acceleration', False)
        sector_in_sync = indicators.get('sector_in_sync', False)

        if not fund_acceleration or not sector_in_sync:
            return True

    # 接近突破 (breakout_20d but not confirmed, using 80% threshold)
    # This would need the actual price vs 20d high calculation
    # Simplified: if we have positive returns but no breakout
    pct_change = indicators.get('pct_change_5d', 0)
    if pct_change > 3 and not indicators.get('breakout_20d', False):
        return True

    return False

def is_in_danger_zone(indicators: dict, events: List[str]) -> tuple:
    """
    Danger Zone: 危险区
    命中任一：
    - 利好不涨代理 (first_rejection_signal)
    - 放量滞涨 (volume_stall_detected)
    - 龙头孤立 (leadership_isolation)
    - 连续加速过多 (pct_change_5d > 30)
    - 趋势衰减开始 (trend_decay_started)

    Returns: (is_danger, danger_type, action)
    """
    danger_type = None
    action = None

    if 'first_rejection_signal' in events:
        danger_type = 'first_rejection_signal'
        action = ACTION_RECOMMENDATIONS['danger_rejection']
    elif 'volume_stall_detected' in events:
        danger_type = 'volume_stall_detected'
        action = ACTION_RECOMMENDATIONS['danger_volume_stall']
    elif 'leadership_isolation' in events:
        danger_type = 'leadership_isolation'
        action = ACTION_RECOMMENDATIONS['danger_leadership_isolation']
    elif 'trend_decay_started' in events:
        danger_type = 'trend_decay_started'
        action = ACTION_RECOMMENDATIONS['danger_trend_decay']
    elif indicators.get('pct_change_5d', 0) > 30:
        danger_type = 'excessive_acceleration'
        action = ACTION_RECOMMENDATIONS['danger_acceleration']

    return danger_type is not None, danger_type, action

def classify_candidate(code: str, trade_date: str) -> Dict:
    """
    Classify a single candidate.

    Returns:
        dict with keys: code, level, action, trend_confirm, fund_confirm, sector_confirm,
                       danger_events, trigger_reasons
    """
    indicators = get_stock_indicators(code, trade_date)
    events = get_stock_events(code, trade_date)

    result = {
        'code': code,
        'trade_date': trade_date,
        'level': 'none',
        'action': None,
        'trend_confirm': False,
        'fund_confirm': False,
        'sector_confirm': False,
        'danger_events': [],
        'trigger_reasons': []
    }

    # Check danger zone first
    is_danger, danger_type, action = is_in_danger_zone(indicators, events)
    if is_danger:
        result['level'] = 'danger'
        result['action'] = action
        result['danger_events'] = [danger_type]
        result['trigger_reasons'] = [f'危险信号: {danger_type}']
        return result

    # Check Level 1
    if is_level1_candidate(indicators, events):
        result['level'] = 'level1'
        result['action'] = ACTION_RECOMMENDATIONS['level1']
        result['trend_confirm'] = True
        result['fund_confirm'] = True
        result['sector_confirm'] = True
        result['trigger_reasons'] = ['趋势确认', '资金强化', '板块同步']
        return result

    # Check Level 2
    if is_level2_candidate(indicators, events):
        result['level'] = 'level2'
        result['action'] = ACTION_RECOMMENDATIONS['level2']

        # Set partial confirmations
        result['trend_confirm'] = indicators.get('breakout_20d', False) or indicators.get('breakout_55d', False)
        result['fund_confirm'] = indicators.get('fund_acceleration', False)
        result['sector_confirm'] = indicators.get('sector_in_sync', False)

        reasons = []
        if result['trend_confirm']:
            reasons.append('趋势已成立')
        if not indicators.get('fund_acceleration', False):
            reasons.append('资金不足')
        if not indicators.get('sector_in_sync', False):
            reasons.append('板块不足')
        if not indicators.get('breakout_20d', False) and indicators.get('pct_change_5d', 0) > 3:
            reasons.append('接近突破')

        result['trigger_reasons'] = reasons
        return result

    return result

def classify_all_candidates(trade_date: str):
    """
    Classify all stocks and save to candidate_snapshot table.
    """
    print(f"Classifying candidates for {trade_date}...")

    # Get all stocks
    with engine.connect() as conn:
        result = conn.execute(text("SELECT code FROM instrument_master ORDER BY code"))
        stock_codes = [row[0] for row in result.fetchall()]

    print(f"Processing {len(stock_codes)} stocks...")

    level1_count = 0
    level2_count = 0
    danger_count = 0

    for i, code in enumerate(stock_codes):
        try:
            candidate = classify_candidate(code, trade_date)

            if candidate['level'] != 'none':
                # Save to database
                data = {
                    'trade_date': trade_date,
                    'code': code,
                    'level': candidate['level'],
                    'action': candidate['action'],
                    'trend_confirm': candidate['trend_confirm'],
                    'fund_confirm': candidate['fund_confirm'],
                    'sector_confirm': candidate['sector_confirm'],
                    'danger_events': candidate['danger_events'],
                    'trigger_reasons': candidate['trigger_reasons'],
                    'ai_explanation': None  # AI explanation added later
                }
                upsert_candidate_snapshot(data)

                if candidate['level'] == 'level1':
                    level1_count += 1
                elif candidate['level'] == 'level2':
                    level2_count += 1
                elif candidate['level'] == 'danger':
                    danger_count += 1

        except Exception as e:
            print(f"Error classifying {code}: {e}")

        if (i + 1) % 100 == 0:
            print(f"Progress: {i + 1}/{len(stock_codes)}")

    print(f"\nClassification complete for {trade_date}:")
    print(f"  Level 1 (主升候选): {level1_count}")
    print(f"  Level 2 (观察池): {level2_count}")
    print(f"  Danger (危险区): {danger_count}")

    return {'level1': level1_count, 'level2': level2_count, 'danger': danger_count}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, help='Trade date (YYYY-MM-DD)')
    parser.add_argument('--code', type=str, help='Stock code (single stock test)')
    args = parser.parse_args()

    from datetime import datetime
    trade_date = args.date or datetime.now().strftime('%Y-%m-%d')

    if args.code:
        result = classify_candidate(args.code, trade_date)
        print(f"\nClassification for {args.code} on {trade_date}:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    else:
        classify_all_candidates(trade_date)