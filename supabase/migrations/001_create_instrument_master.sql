CREATE TABLE IF NOT EXISTS instrument_master (
    id          BIGSERIAL PRIMARY KEY,
    code        VARCHAR(10) NOT NULL UNIQUE,
    name        VARCHAR(50) NOT NULL,
    sector      VARCHAR(50),
    list_date   DATE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_instrument_master_code ON instrument_master(code);
CREATE INDEX IF NOT EXISTS idx_instrument_master_sector ON instrument_master(sector);