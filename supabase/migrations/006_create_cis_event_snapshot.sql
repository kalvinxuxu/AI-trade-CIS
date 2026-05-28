CREATE TABLE IF NOT EXISTS cis_event_snapshot (
    id              BIGSERIAL PRIMARY KEY,
    trade_date      DATE NOT NULL,
    code            VARCHAR(10) NOT NULL,
    event_name      VARCHAR(50) NOT NULL,
    event_params    JSONB,
    triggered_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cis_event_date ON cis_event_snapshot(trade_date);
CREATE INDEX IF NOT EXISTS idx_cis_event_code ON cis_event_snapshot(code);
CREATE INDEX IF NOT EXISTS idx_cis_event_name ON cis_event_snapshot(event_name);