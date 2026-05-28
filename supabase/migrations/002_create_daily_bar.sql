CREATE TABLE IF NOT EXISTS daily_bar (
    id              BIGSERIAL PRIMARY KEY,
    code            VARCHAR(10) NOT NULL,
    trade_date      DATE NOT NULL,
    open            NUMERIC(10, 3),
    high            NUMERIC(10, 3),
    low             NUMERIC(10, 3),
    close           NUMERIC(10, 3),
    volume          BIGINT,
    amount          NUMERIC(20, 2),
    turnover_rate   NUMERIC(10, 4),
    pct_change      NUMERIC(10, 4),
    amplitude       NUMERIC(10, 4),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (code, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_bar_code ON daily_bar(code);
CREATE INDEX IF NOT EXISTS idx_daily_bar_trade_date ON daily_bar(trade_date);
CREATE INDEX IF NOT EXISTS idx_daily_bar_code_date ON daily_bar(code, trade_date);