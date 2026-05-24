CREATE TABLE IF NOT EXISTS telemetry_metrics (
    id SERIAL PRIMARY KEY,
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

CREATE INDEX IF NOT EXISTS telemetry_metrics_target_ts_idx
ON telemetry_metrics(target, ts DESC);
