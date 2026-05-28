from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from config.settings import SUPABASE_DB_URL

if not SUPABASE_DB_URL:
    raise ValueError("SUPABASE_DB_URL is not set in environment variables")

engine = create_engine(
    SUPABASE_DB_URL,
    poolclass=NullPool,
    echo=False
)

def get_stock_daily(code: str, start_date: str, end_date: str):
    """Fetch daily bar data for a stock within date range"""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT code, trade_date, open, high, low, close,
                       volume, amount, turnover_rate, pct_change, amplitude
                FROM daily_bar
                WHERE code = :code AND trade_date BETWEEN :start AND :end
                ORDER BY trade_date
            """),
            {"code": code, "start": start_date, "end": end_date}
        )
        return result.fetchall()

def get_latest_daily_bar(trade_date: str):
    """Fetch all daily bars for a specific trade date"""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT code, trade_date, open, high, low, close,
                       volume, amount, turnover_rate, pct_change, amplitude
                FROM daily_bar
                WHERE trade_date = :trade_date
            """),
            {"trade_date": trade_date}
        )
        return result.fetchall()

def upsert_daily_bar(data: dict):
    """Insert or update a daily bar record"""
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO daily_bar (code, trade_date, open, high, low, close, volume, amount, turnover_rate, pct_change, amplitude)
                VALUES (:code, :trade_date, :open, :high, :low, :close, :volume, :amount, :turnover_rate, :pct_change, :amplitude)
                ON CONFLICT (code, trade_date) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    amount = EXCLUDED.amount,
                    turnover_rate = EXCLUDED.turnover_rate,
                    pct_change = EXCLUDED.pct_change,
                    amplitude = EXCLUDED.amplitude
            """),
            data
        )
        conn.commit()

def upsert_candidate_snapshot(data: dict):
    """Insert or update a candidate snapshot record"""
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO candidate_snapshot
                (trade_date, code, level, action, trend_confirm, fund_confirm, sector_confirm, danger_events, trigger_reasons, ai_explanation)
                VALUES (:trade_date, :code, :level, :action, :trend_confirm, :fund_confirm, :sector_confirm, :danger_events, :trigger_reasons, :ai_explanation)
                ON CONFLICT (trade_date, code) DO UPDATE SET
                    level = EXCLUDED.level,
                    action = EXCLUDED.action,
                    trend_confirm = EXCLUDED.trend_confirm,
                    fund_confirm = EXCLUDED.fund_confirm,
                    sector_confirm = EXCLUDED.sector_confirm,
                    danger_events = EXCLUDED.danger_events,
                    trigger_reasons = EXCLUDED.trigger_reasons,
                    ai_explanation = EXCLUDED.ai_explanation
            """),
            data
        )
        conn.commit()

def log_job(job_name: str, trade_date: str, status: str, message: str = "", error_details: str = ""):
    """Log job execution to job_logs table"""
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO job_logs (job_name, trade_date, status, message, error_details, started_at, finished_at)
                VALUES (:job_name, :trade_date, :status, :message, :error_details, NOW(), NOW())
            """),
            {"job_name": job_name, "trade_date": trade_date, "status": status, "message": message, "error_details": error_details}
        )
        conn.commit()