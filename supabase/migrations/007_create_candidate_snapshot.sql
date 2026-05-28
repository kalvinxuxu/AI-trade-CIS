CREATE TABLE IF NOT EXISTS candidate_snapshot (
    id              BIGSERIAL PRIMARY KEY,
    trade_date      DATE NOT NULL,
    code            VARCHAR(10) NOT NULL,
    level           VARCHAR(20) NOT NULL,  -- 'level1', 'level2', 'danger'
    action          VARCHAR(50),
    trend_confirm   BOOLEAN,
    fund_confirm    BOOLEAN,
    sector_confirm  BOOLEAN,
    danger_events   TEXT[],
    trigger_reasons TEXT[],
    ai_explanation  TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (trade_date, code)
);

CREATE INDEX IF NOT EXISTS idx_candidate_trade_date ON candidate_snapshot(trade_date);
CREATE INDEX IF NOT EXISTS idx_candidate_level ON candidate_snapshot(level);
CREATE INDEX IF NOT EXISTS idx_candidate_code ON candidate_snapshot(code);