CREATE TABLE IF NOT EXISTS cis_indicator_snapshot (
    id              BIGSERIAL PRIMARY KEY,
    trade_date      DATE NOT NULL,
    entity_type     VARCHAR(20) NOT NULL,  -- 'market', 'sector', 'stock'
    entity_code     VARCHAR(20) NOT NULL,
    indicator_name  VARCHAR(50) NOT NULL,
    indicator_value NUMERIC(20, 6),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cis_indicator_date ON cis_indicator_snapshot(trade_date);
CREATE INDEX IF NOT EXISTS idx_cis_indicator_entity ON cis_indicator_snapshot(entity_type, entity_code);
CREATE INDEX IF NOT EXISTS idx_cis_indicator_name ON cis_indicator_snapshot(indicator_name);