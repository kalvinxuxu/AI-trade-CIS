CREATE TABLE IF NOT EXISTS job_logs (
    id              BIGSERIAL PRIMARY KEY,
    job_name        VARCHAR(100) NOT NULL,
    trade_date      DATE,
    status          VARCHAR(20) NOT NULL,  -- 'started', 'success', 'failed'
    message         TEXT,
    error_details   TEXT,
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    finished_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_job_logs_trade_date ON job_logs(trade_date);
CREATE INDEX IF NOT EXISTS idx_job_logs_status ON job_logs(status);