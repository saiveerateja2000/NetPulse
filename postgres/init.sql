-- Sessions table for tracking monitoring sessions
CREATE TABLE IF NOT EXISTS monitoring_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    target VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- active, paused, stopped
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    stopped_at TIMESTAMPTZ,
    paused_at TIMESTAMPTZ,
    resumed_at TIMESTAMPTZ,
    description TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enhanced telemetry metrics with session reference
CREATE TABLE IF NOT EXISTS telemetry_metrics (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES monitoring_sessions(session_id) ON DELETE CASCADE,
    target VARCHAR(255) NOT NULL,
    latency_ms DOUBLE PRECISION,
    packet_loss DOUBLE PRECISION,
    jitter DOUBLE PRECISION,
    dns_lookup_time DOUBLE PRECISION,
    cpu_usage DOUBLE PRECISION,
    memory_usage DOUBLE PRECISION,
    bandwidth_usage DOUBLE PRECISION,
    active_connections INTEGER,
    traceroute_hops TEXT,
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS telemetry_metrics_target_ts_idx
ON telemetry_metrics(target, ts DESC);

CREATE INDEX IF NOT EXISTS telemetry_metrics_session_idx
ON telemetry_metrics(session_id);

CREATE INDEX IF NOT EXISTS telemetry_metrics_ts_idx
ON telemetry_metrics(ts DESC);

CREATE INDEX IF NOT EXISTS monitoring_sessions_target_idx
ON monitoring_sessions(target);

CREATE INDEX IF NOT EXISTS monitoring_sessions_status_idx
ON monitoring_sessions(status);

-- Traceroute results table
CREATE TABLE IF NOT EXISTS traceroute_results (
    id SERIAL PRIMARY KEY,
    target VARCHAR(255) NOT NULL,
    hops JSONB NOT NULL,  -- Array of {hop_number, ip, latency_ms, hostname}
    total_hops INTEGER,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    success BOOLEAN DEFAULT TRUE
);

-- HTTP Status Check results table
CREATE TABLE IF NOT EXISTS http_check_results (
    id SERIAL PRIMARY KEY,
    target VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,
    status_code INTEGER,
    response_time_ms DOUBLE PRECISION,
    ssl_valid BOOLEAN,
    ssl_expiry_date VARCHAR(50),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Bandwidth test results table
CREATE TABLE IF NOT EXISTS bandwidth_test_results (
    id SERIAL PRIMARY KEY,
    target VARCHAR(255) NOT NULL,
    test_size_mb DOUBLE PRECISION NOT NULL,
    download_speed_mbps DOUBLE PRECISION,
    upload_speed_mbps DOUBLE PRECISION,
    test_duration_seconds DOUBLE PRECISION,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    tested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS traceroute_results_target_idx
ON traceroute_results(target);

CREATE INDEX IF NOT EXISTS http_check_results_target_idx
ON http_check_results(target);

CREATE INDEX IF NOT EXISTS bandwidth_test_results_target_idx
ON bandwidth_test_results(target);
