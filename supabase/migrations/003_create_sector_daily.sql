CREATE TABLE IF NOT EXISTS sector_daily (
    id              BIGSERIAL PRIMARY KEY,
    sector_code     VARCHAR(20) NOT NULL,
    sector_name     VARCHAR(50) NOT NULL,
    trade_date      DATE NOT NULL,
    amount          NUMERIC(20, 2),
    volume          BIGINT,
    pct_change      NUMERIC(10, 4),
    member_count    INTEGER,
    avg_pct_change  NUMERIC(10, 4),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (sector_code, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_sector_daily_trade_date ON sector_daily(trade_date);
CREATE INDEX IF NOT EXISTS idx_sector_daily_sector ON sector_daily(sector_code);