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
