-- =============================================================
-- RadiusFlow Enterprise Session Migration
-- Run this on your VPS as the postgres superuser or radiusflow_app owner:
--   psql -U postgres -d radius -f migration_admin_sessions.sql
-- =============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS radiusflow.admin_sessions (
    id            BIGSERIAL PRIMARY KEY,
    admin_user_id BIGINT      NOT NULL
                  REFERENCES radiusflow.admin_users(id) ON DELETE CASCADE,
    token_hash    CHAR(64)    NOT NULL UNIQUE,
    ip_address    VARCHAR(45),
    user_agent    VARCHAR(255),
    role_name     VARCHAR(64) NOT NULL DEFAULT 'super_admin',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at    TIMESTAMPTZ NOT NULL,
    revoked_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_admin_sessions_token_hash
    ON radiusflow.admin_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires_at
    ON radiusflow.admin_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_admin_user
    ON radiusflow.admin_sessions(admin_user_id);

-- Grant access to the application user
GRANT SELECT, INSERT, UPDATE, DELETE
    ON radiusflow.admin_sessions TO radiusflow_app;
GRANT USAGE, SELECT
    ON SEQUENCE radiusflow.admin_sessions_id_seq TO radiusflow_app;

COMMIT;
