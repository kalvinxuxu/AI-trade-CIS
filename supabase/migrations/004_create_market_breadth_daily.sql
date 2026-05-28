CREATE TABLE IF NOT EXISTS market_breadth_daily (
    id                  BIGSERIAL PRIMARY KEY,
    trade_date          DATE NOT NULL UNIQUE,
    index_code          VARCHAR(20),
    index_name          VARCHAR(50),
    advance_count       INTEGER,
    decline_count       INTEGER,
    unchanged_count     INTEGER,
    advance_rate        NUMERIC(10, 4),
    total_amount        NUMERIC(20, 2),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_market_breadth_trade_date ON market_breadth_daily(trade_date);