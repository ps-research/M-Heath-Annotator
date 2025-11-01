-- ============================================================================
-- M-Heath Annotator Database Schema
-- SQLite database for worker progress tracking, logging, and state management
-- ============================================================================

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;

-- ============================================================================
-- WORKERS TABLE - Core worker state and configuration
-- ============================================================================
CREATE TABLE IF NOT EXISTS workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    annotator_id INTEGER NOT NULL,
    domain TEXT NOT NULL,

    -- State tracking
    status TEXT NOT NULL DEFAULT 'not_started',
    enabled BOOLEAN NOT NULL DEFAULT 1,
    target_count INTEGER NOT NULL DEFAULT 0,

    -- Process tracking
    pid INTEGER NULL,
    started_at TIMESTAMP NULL,
    stopped_at TIMESTAMP NULL,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Progress statistics
    total_completed INTEGER NOT NULL DEFAULT 0,
    total_malformed INTEGER NOT NULL DEFAULT 0,
    samples_per_min REAL NOT NULL DEFAULT 0.0,
    last_speed_check TIMESTAMP NULL,

    -- Constraints
    UNIQUE(annotator_id, domain),
    CHECK(status IN ('not_started', 'running', 'paused', 'stopped', 'completed', 'crashed'))
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_workers_status ON workers(status);
CREATE INDEX IF NOT EXISTS idx_workers_pid ON workers(pid);
CREATE INDEX IF NOT EXISTS idx_workers_enabled ON workers(enabled);
CREATE INDEX IF NOT EXISTS idx_workers_annotator ON workers(annotator_id);

-- ============================================================================
-- COMPLETED_SAMPLES - Fast lookup for processed sample IDs
-- ============================================================================
CREATE TABLE IF NOT EXISTS completed_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER NOT NULL,
    sample_id TEXT NOT NULL,
    label TEXT NOT NULL,
    is_malformed BOOLEAN NOT NULL DEFAULT 0,
    completed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE,
    UNIQUE(worker_id, sample_id)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_completed_worker ON completed_samples(worker_id);
CREATE INDEX IF NOT EXISTS idx_completed_sample ON completed_samples(sample_id);
CREATE INDEX IF NOT EXISTS idx_completed_malformed ON completed_samples(is_malformed);

-- ============================================================================
-- ANNOTATIONS - Full annotation results (JSONL equivalent)
-- ============================================================================
CREATE TABLE IF NOT EXISTS annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER NOT NULL,

    -- Sample data
    sample_id TEXT NOT NULL,
    sample_text TEXT NOT NULL,

    -- Results
    label TEXT NOT NULL,
    response TEXT,
    is_malformed BOOLEAN NOT NULL DEFAULT 0,
    parsing_error TEXT NULL,
    validity_error TEXT NULL,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE
);

-- Indexes for querying
CREATE INDEX IF NOT EXISTS idx_annotations_worker ON annotations(worker_id);
CREATE INDEX IF NOT EXISTS idx_annotations_sample ON annotations(sample_id);
CREATE INDEX IF NOT EXISTS idx_annotations_created ON annotations(created_at);

-- ============================================================================
-- HEARTBEATS - Worker health monitoring
-- ============================================================================
CREATE TABLE IF NOT EXISTS heartbeats (
    worker_id INTEGER PRIMARY KEY,
    pid INTEGER NOT NULL,
    iteration INTEGER NOT NULL DEFAULT 0,
    heartbeat_status TEXT NOT NULL DEFAULT 'running',
    heartbeat_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_heartbeats_time ON heartbeats(heartbeat_time);

-- ============================================================================
-- WORKER_EVENTS - Audit trail and event history
-- ============================================================================
CREATE TABLE IF NOT EXISTS worker_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_details TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE,
    CHECK(event_type IN ('started', 'stopped', 'paused', 'resumed', 'crashed', 'completed', 'reset'))
);

-- Indexes for event queries
CREATE INDEX IF NOT EXISTS idx_events_worker ON worker_events(worker_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON worker_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_time ON worker_events(created_at);

-- ============================================================================
-- SYSTEM_STATE - Global configuration and metadata
-- ============================================================================
CREATE TABLE IF NOT EXISTS system_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- RATE_LIMITER_STATE - API rate limiting state
-- ============================================================================
CREATE TABLE IF NOT EXISTS rate_limiter_state (
    api_key_id TEXT PRIMARY KEY,
    minute_window_start TIMESTAMP NOT NULL,
    minute_requests INTEGER NOT NULL DEFAULT 0,
    day_window_start TIMESTAMP NOT NULL,
    day_requests INTEGER NOT NULL DEFAULT 0,
    last_request TIMESTAMP NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rate_limiter_updated ON rate_limiter_state(updated_at);

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert system state defaults
INSERT OR IGNORE INTO system_state (key, value) VALUES
    ('schema_version', '1'),
    ('last_factory_reset', 'never'),
    ('database_created', CURRENT_TIMESTAMP);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Active workers with health status
CREATE VIEW IF NOT EXISTS v_active_workers AS
SELECT
    w.id,
    w.annotator_id,
    w.domain,
    w.status,
    w.pid,
    w.total_completed,
    w.total_malformed,
    w.target_count,
    w.samples_per_min,
    w.last_updated,
    h.heartbeat_time,
    h.iteration,
    CASE
        WHEN h.heartbeat_time IS NULL THEN 0
        WHEN (JULIANDAY('now') - JULIANDAY(h.heartbeat_time)) * 1440 > 2 THEN 0
        ELSE 1
    END as heartbeat_alive,
    (JULIANDAY('now') - JULIANDAY(h.heartbeat_time)) * 1440 as minutes_since_heartbeat
FROM workers w
LEFT JOIN heartbeats h ON w.id = h.worker_id
WHERE w.status IN ('running', 'paused');

-- System overview statistics
CREATE VIEW IF NOT EXISTS v_system_overview AS
SELECT
    COUNT(*) as total_workers,
    SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as enabled_workers,
    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running_workers,
    SUM(CASE WHEN status = 'paused' THEN 1 ELSE 0 END) as paused_workers,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_workers,
    SUM(CASE WHEN status = 'crashed' THEN 1 ELSE 0 END) as crashed_workers,
    SUM(total_completed) as total_completed_samples,
    SUM(total_malformed) as total_malformed_samples,
    SUM(target_count) as total_target_samples,
    ROUND(AVG(CASE WHEN samples_per_min > 0 THEN samples_per_min END), 2) as avg_speed
FROM workers;

-- Recent events
CREATE VIEW IF NOT EXISTS v_recent_events AS
SELECT
    e.id,
    w.annotator_id,
    w.domain,
    e.event_type,
    e.event_details,
    e.created_at
FROM worker_events e
JOIN workers w ON e.worker_id = w.id
ORDER BY e.created_at DESC
LIMIT 100;
