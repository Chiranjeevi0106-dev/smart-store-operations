-- Smart Store Operations — TimescaleDB Schema
-- Phase 8: Time-Series Database

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ═══════════════════════════════════════════════════════════════════
-- SHELF STATE HYPERTABLE
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE shelf_state (
    time                    TIMESTAMPTZ NOT NULL,
    event_id                UUID DEFAULT gen_random_uuid(),
    store_id                VARCHAR(20) NOT NULL,
    aisle                   VARCHAR(10) NOT NULL,
    bay                     SMALLINT NOT NULL,
    shelf_level             SMALLINT NOT NULL,
    product_id              VARCHAR(30) NOT NULL,
    sku_code                VARCHAR(30),
    
    -- Camera signals
    camera_status           VARCHAR(30),      -- product_present, empty_facing, etc.
    camera_confidence       REAL,
    
    -- Weight sensor signals
    weight_grams            REAL,
    weight_expected_grams   REAL,
    weight_ratio            REAL,
    
    -- RFID signals
    rfid_present            BOOLEAN,
    rfid_tag_count          SMALLINT,
    rfid_expected_count     SMALLINT,
    
    -- Fused result
    fused_confidence        REAL NOT NULL,
    is_out_of_stock         BOOLEAN NOT NULL DEFAULT FALSE,
    sensors_reporting       SMALLINT DEFAULT 0,
    
    -- Prediction
    predicted_stockout_min  REAL,
    
    PRIMARY KEY (time, store_id, aisle, bay, product_id)
);

SELECT create_hypertable('shelf_state', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Compression policy: compress data older than 7 days
ALTER TABLE shelf_state SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'store_id, aisle, bay, product_id',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('shelf_state', INTERVAL '7 days', if_not_exists => TRUE);

-- Indexes
CREATE INDEX idx_shelf_state_store_oos ON shelf_state (store_id, is_out_of_stock, time DESC);
CREATE INDEX idx_shelf_state_product ON shelf_state (product_id, time DESC);


-- ═══════════════════════════════════════════════════════════════════
-- QUEUE EVENTS HYPERTABLE
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE queue_events (
    time                    TIMESTAMPTZ NOT NULL,
    event_id                UUID DEFAULT gen_random_uuid(),
    store_id                VARCHAR(20) NOT NULL,
    lane_id                 SMALLINT NOT NULL,
    lane_type               VARCHAR(20) NOT NULL,   -- manned, self_checkout
    is_open                 BOOLEAN NOT NULL,
    cashier_id              VARCHAR(20),
    queue_length            SMALLINT NOT NULL DEFAULT 0,
    estimated_wait_seconds  REAL NOT NULL DEFAULT 0,
    total_people_in_store   SMALLINT,
    
    PRIMARY KEY (time, store_id, lane_id)
);

SELECT create_hypertable('queue_events', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

ALTER TABLE queue_events SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'store_id, lane_id',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('queue_events', INTERVAL '7 days', if_not_exists => TRUE);

CREATE INDEX idx_queue_store_time ON queue_events (store_id, time DESC);


-- ═══════════════════════════════════════════════════════════════════
-- LP ALERTS HYPERTABLE
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE lp_alerts (
    time                    TIMESTAMPTZ NOT NULL,
    alert_id                UUID DEFAULT gen_random_uuid(),
    store_id                VARCHAR(20) NOT NULL,
    zone                    VARCHAR(30) NOT NULL,
    alert_type              VARCHAR(30) NOT NULL,   -- behaviour, dwell, rfid_discrepancy
    behaviour_class         VARCHAR(30),
    confidence              REAL NOT NULL,
    customer_tracking_id    VARCHAR(30),
    dwell_time_seconds      REAL,
    rfid_discrepancy        BOOLEAN DEFAULT FALSE,
    rfid_unmatched_tags     SMALLINT,
    video_clip_url          TEXT,
    severity                VARCHAR(10) NOT NULL DEFAULT 'medium',
    
    -- Resolution
    acknowledged            BOOLEAN DEFAULT FALSE,
    acknowledged_by         VARCHAR(30),
    acknowledged_at         TIMESTAMPTZ,
    action_taken            VARCHAR(20),             -- acknowledge, dismiss, escalate
    resolution_reason       TEXT,
    
    PRIMARY KEY (time, alert_id)
);

SELECT create_hypertable('lp_alerts', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

ALTER TABLE lp_alerts SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'store_id',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('lp_alerts', INTERVAL '7 days', if_not_exists => TRUE);

CREATE INDEX idx_lp_alerts_store_severity ON lp_alerts (store_id, severity, time DESC);
CREATE INDEX idx_lp_alerts_unresolved ON lp_alerts (store_id, acknowledged, time DESC);


-- ═══════════════════════════════════════════════════════════════════
-- LP AUDIT TRAIL (APPEND-ONLY — NO UPDATE/DELETE ALLOWED)
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE lp_audit_trail (
    time                    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    record_id               UUID DEFAULT gen_random_uuid(),
    alert_id                UUID NOT NULL,
    officer_id              VARCHAR(30) NOT NULL,
    action                  VARCHAR(20) NOT NULL,   -- created, acknowledge, dismiss, escalate, review
    reason                  TEXT,
    metadata                JSONB,
    
    PRIMARY KEY (time, record_id)
);

SELECT create_hypertable('lp_audit_trail', 'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Revoke UPDATE and DELETE to enforce append-only
-- REVOKE UPDATE, DELETE ON lp_audit_trail FROM app_user;

CREATE INDEX idx_audit_alert ON lp_audit_trail (alert_id, time);
CREATE INDEX idx_audit_officer ON lp_audit_trail (officer_id, time DESC);


-- ═══════════════════════════════════════════════════════════════════
-- SENSOR TELEMETRY HYPERTABLE
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE sensor_telemetry (
    time                    TIMESTAMPTZ NOT NULL,
    store_id                VARCHAR(20) NOT NULL,
    sensor_id               VARCHAR(30) NOT NULL,
    sensor_type             VARCHAR(20) NOT NULL,   -- weight, rfid, camera, eas
    
    -- Readings (type-dependent)
    value_numeric           REAL,
    value_text              VARCHAR(100),
    value_json              JSONB,
    
    -- Health
    battery_pct             SMALLINT,
    signal_strength_dbm     SMALLINT,
    is_healthy              BOOLEAN DEFAULT TRUE,
    
    PRIMARY KEY (time, store_id, sensor_id)
);

SELECT create_hypertable('sensor_telemetry', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

ALTER TABLE sensor_telemetry SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'store_id, sensor_id, sensor_type',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('sensor_telemetry', INTERVAL '7 days', if_not_exists => TRUE);


-- ═══════════════════════════════════════════════════════════════════
-- RESTOCK TASKS TABLE (regular table, not time-series)
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE restock_tasks (
    task_id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id                VARCHAR(20) NOT NULL,
    aisle                   VARCHAR(10) NOT NULL,
    bay                     SMALLINT NOT NULL,
    shelf_level             SMALLINT NOT NULL,
    product_id              VARCHAR(30) NOT NULL,
    sku_code                VARCHAR(30),
    product_name            VARCHAR(100),
    current_quantity_est    SMALLINT,
    restock_quantity        SMALLINT,
    priority                VARCHAR(10) NOT NULL DEFAULT 'normal',
    fused_confidence        REAL,
    predicted_stockout_min  REAL,
    assigned_to             VARCHAR(30),
    status                  VARCHAR(20) NOT NULL DEFAULT 'pending',
    auto_dispatched         BOOLEAN DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_by                  TIMESTAMPTZ,
    completed_at            TIMESTAMPTZ,
    completion_photo_url    TEXT,
    wms_sync_status         VARCHAR(20) DEFAULT 'pending'
);

CREATE INDEX idx_restock_store_status ON restock_tasks (store_id, status, created_at DESC);
CREATE INDEX idx_restock_priority ON restock_tasks (priority, created_at);


-- ═══════════════════════════════════════════════════════════════════
-- CONTINUOUS AGGREGATES (pre-computed rollups)
-- ═══════════════════════════════════════════════════════════════════

-- Hourly shelf stockout rate
CREATE MATERIALIZED VIEW hourly_stockout_rate
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    store_id,
    COUNT(*) FILTER (WHERE is_out_of_stock = TRUE) AS oos_count,
    COUNT(*) AS total_readings,
    AVG(fused_confidence) AS avg_confidence,
    ROUND(
        COUNT(*) FILTER (WHERE is_out_of_stock = TRUE)::NUMERIC / 
        NULLIF(COUNT(*), 0) * 100, 2
    ) AS stockout_rate_pct
FROM shelf_state
GROUP BY bucket, store_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('hourly_stockout_rate',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '30 minutes',
    if_not_exists => TRUE
);

-- Hourly queue wait times
CREATE MATERIALIZED VIEW hourly_queue_stats
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    store_id,
    AVG(estimated_wait_seconds) AS avg_wait_seconds,
    MAX(estimated_wait_seconds) AS max_wait_seconds,
    AVG(queue_length) AS avg_queue_length,
    MAX(queue_length) AS max_queue_length,
    COUNT(*) AS sample_count
FROM queue_events
GROUP BY bucket, store_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('hourly_queue_stats',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '30 minutes',
    if_not_exists => TRUE
);

-- Daily LP alert summary
CREATE MATERIALIZED VIEW daily_lp_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    store_id,
    COUNT(*) AS total_alerts,
    COUNT(*) FILTER (WHERE severity = 'critical') AS critical_alerts,
    COUNT(*) FILTER (WHERE severity = 'high') AS high_alerts,
    COUNT(*) FILTER (WHERE acknowledged = TRUE) AS acknowledged,
    COUNT(*) FILTER (WHERE action_taken = 'escalate') AS escalated,
    AVG(confidence) AS avg_confidence
FROM lp_alerts
GROUP BY bucket, store_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('daily_lp_summary',
    start_offset => INTERVAL '2 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);


-- ═══════════════════════════════════════════════════════════════════
-- DATA RETENTION POLICIES
-- ═══════════════════════════════════════════════════════════════════

-- Raw sensor telemetry: retain 30 days
SELECT add_retention_policy('sensor_telemetry', INTERVAL '30 days', if_not_exists => TRUE);

-- Shelf state: retain 90 days (compressed after 7)
SELECT add_retention_policy('shelf_state', INTERVAL '90 days', if_not_exists => TRUE);

-- Queue events: retain 90 days
SELECT add_retention_policy('queue_events', INTERVAL '90 days', if_not_exists => TRUE);

-- LP alerts: retain 1 year (regulatory requirement)
SELECT add_retention_policy('lp_alerts', INTERVAL '365 days', if_not_exists => TRUE);

-- Audit trail: retain 7 years (compliance)
-- No retention policy — keep indefinitely for compliance
