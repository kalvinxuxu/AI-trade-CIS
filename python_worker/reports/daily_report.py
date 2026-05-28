"""
Daily Report Generator.
Generates the complete daily market scan report.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime
from data.loaders.db_loader import engine
from sqlalchemy import text
from indicators.market_indicators import calculate_market_indicators

def generate_market_summary(trade_date: str) -> dict:
    """
    Generate market summary for the day.

    Returns:
        dict with:
        - market_environment: str
        - main_sectors: list of sector names with expanding volume
        - level1_count, level2_count, danger_count: int
        - market_indicators: dict
    """
    summary = {
        'trade_date': trade_date,
        'market_environment': 'unknown',
        'main_sectors': [],
        'level1_count': 0,
        'level2_count': 0,
        'danger_count': 0,
        'total_stocks': 0
    }

    # Get market indicators
    try:
        market_indicators = calculate_market_indicators(trade_date)
        summary['market_environment'] = market_indicators.get('market_environment', 'unknown')
    except Exception as e:
        print(f"Error getting market indicators: {e}")

    # Get main sectors (top 5 by amount)
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT sector_name, amount
                    FROM sector_daily
                    WHERE trade_date = :date
                    ORDER BY amount DESC
                    LIMIT 5
                """),
                {'date': trade_date}
            )
            summary['main_sectors'] = [row[0] for row in result.fetchall()]
    except Exception as e:
        print(f"Error getting main sectors: {e}")

    # Get candidate counts
    try:
        with engine.connect() as conn:
            # Level 1 count
            result = conn.execute(
                text("SELECT COUNT(*) FROM candidate_snapshot WHERE trade_date = :date AND level = 'level1'"),
                {'date': trade_date}
            )
            summary['level1_count'] = result.scalar() or 0

            # Level 2 count
            result = conn.execute(
                text("SELECT COUNT(*) FROM candidate_snapshot WHERE trade_date = :date AND level = 'level2'"),
                {'date': trade_date}
            )
            summary['level2_count'] = result.scalar() or 0

            # Danger count
            result = conn.execute(
                text("SELECT COUNT(*) FROM candidate_snapshot WHERE trade_date = :date AND level = 'danger'"),
                {'date': trade_date}
            )
            summary['danger_count'] = result.scalar() or 0

            # Total stocks
            result = conn.execute(text("SELECT COUNT(*) FROM instrument_master"))
            summary['total_stocks'] = result.scalar() or 0
    except Exception as e:
        print(f"Error getting candidate counts: {e}")

    return summary

def get_level1_candidates(trade_date: str, limit: int = 20) -> list:
    """Get Level 1 candidates with details"""
    candidates = []

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        cs.code,
                        im.name,
                        cs.trend_confirm,
                        cs.fund_confirm,
                        cs.sector_confirm,
                        cs.trigger_reasons,
                        db.close,
                        db.pct_change
                    FROM candidate_snapshot cs
                    JOIN instrument_master im ON cs.code = im.code
                    LEFT JOIN daily_bar db ON cs.code = db.code AND cs.trade_date = db.trade_date
                    WHERE cs.trade_date = :date AND cs.level = 'level1'
                    ORDER BY db.pct_change DESC
                    LIMIT :limit
                """),
                {'date': trade_date, 'limit': limit}
            )

            for row in result.fetchall():
                candidates.append({
                    'code': row[0],
                    'name': row[1],
                    'trend_confirm': row[2],
                    'fund_confirm': row[3],
                    'sector_confirm': row[4],
                    'trigger_reasons': row[5],
                    'close': row[6],
                    'pct_change': row[7]
                })
    except Exception as e:
        print(f"Error getting Level 1 candidates: {e}")

    return candidates

def get_danger_stocks(trade_date: str, limit: int = 20) -> list:
    """Get danger zone stocks with details"""
    stocks = []

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        cs.code,
                        im.name,
                        cs.danger_events,
                        cs.action,
                        db.close,
                        db.pct_change
                    FROM candidate_snapshot cs
                    JOIN instrument_master im ON cs.code = im.code
                    LEFT JOIN daily_bar db ON cs.code = db.code AND cs.trade_date = db.trade_date
                    WHERE cs.trade_date = :date AND cs.level = 'danger'
                    ORDER BY db.pct_change ASC
                    LIMIT :limit
                """),
                {'date': trade_date, 'limit': limit}
            )

            for row in result.fetchall():
                stocks.append({
                    'code': row[0],
                    'name': row[1],
                    'danger_events': row[2],
                    'action': row[3],
                    'close': row[4],
                    'pct_change': row[5]
                })
    except Exception as e:
        print(f"Error getting danger stocks: {e}")

    return stocks

def generate_daily_report(trade_date: str) -> str:
    """
    Generate the complete daily report as a formatted string.
    """
    summary = generate_market_summary(trade_date)
    level1_list = get_level1_candidates(trade_date)
    danger_list = get_danger_stocks(trade_date)

    report = []
    report.append("=" * 60)
    report.append(f"CIS 每日趋势报告 - {trade_date}")
    report.append("=" * 60)

    # Market Environment
    report.append(f"\n【市场环境】: {summary['market_environment']}")
    report.append(f"今日主线板块: {', '.join(summary['main_sectors']) if summary['main_sectors'] else '暂无数据'}")

    # Candidate Summary
    report.append(f"\n【候选概览】")
    report.append(f"  Level 1 (主升候选): {summary['level1_count']} 只")
    report.append(f"  Level 2 (观察池): {summary['level2_count']} 只")
    report.append(f"  危险区: {summary['danger_count']} 只")
    report.append(f"  市场总股票数: {summary['total_stocks']} 只")

    # Level 1 Candidates
    report.append(f"\n【Level 1 主升候选】(Top {len(level1_list)})")
    if level1_list:
        for i, c in enumerate(level1_list, 1):
            reasons = ', '.join(c['trigger_reasons']) if c['trigger_reasons'] else '趋势确认'
            report.append(f"  {i}. {c['code']} {c['name']} 涨幅:{c['pct_change']:.2f}%")
            report.append(f"     信号: {reasons}")
    else:
        report.append("  暂无")

    # Danger Zone
    report.append(f"\n【危险区】(Top {len(danger_list)})")
    if danger_list:
        for i, s in enumerate(danger_list, 1):
            events = ', '.join(s['danger_events']) if s['danger_events'] else '未知'
            report.append(f"  {i}. {s['code']} {s['name']} 涨幅:{s['pct_change']:.2f}%")
            report.append(f"     危险: {events} | 建议: {s['action']}")
    else:
        report.append("  暂无")

    report.append("\n" + "=" * 60)

    return '\n'.join(report)

def save_daily_report(trade_date: str):
    """Save daily report to job_logs"""
    report = generate_daily_report(trade_date)

    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO job_logs (job_name, trade_date, status, message, started_at, finished_at)
                VALUES (:job_name, :trade_date, :status, :message, NOW(), NOW())
            """),
            {
                'job_name': 'daily_report',
                'trade_date': trade_date,
                'status': 'success',
                'message': report[:4000]  # Truncate if too long
            }
        )
        conn.commit()

    print(report)
    return report

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, help='Trade date (YYYY-MM-DD)')
    parser.add_argument('--save', action='store_true', help='Save report to job_logs')
    args = parser.parse_args()

    trade_date = args.date or datetime.now().strftime('%Y-%m-%d')

    if args.save:
        save_daily_report(trade_date)
    else:
        print(generate_daily_report(trade_date))