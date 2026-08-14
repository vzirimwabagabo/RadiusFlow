-- Migration to create app_audit_logs and app_vouchers inside radiusflow schema
BEGIN;

CREATE TABLE IF NOT EXISTS radiusflow.app_audit_logs (
    id            BIGSERIAL PRIMARY KEY,
    action        VARCHAR(64) NOT NULL,
    actor         VARCHAR(64),
    resource_type VARCHAR(64),
    resource_id   VARCHAR(128),
    details       TEXT,
    ip_address    VARCHAR(45),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_app_audit_logs_action ON radiusflow.app_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_app_audit_logs_actor ON radiusflow.app_audit_logs(actor);
CREATE INDEX IF NOT EXISTS idx_app_audit_logs_created_at ON radiusflow.app_audit_logs(created_at);

CREATE TABLE IF NOT EXISTS radiusflow.app_vouchers (
    id          BIGSERIAL PRIMARY KEY,
    code        VARCHAR(32) NOT NULL UNIQUE,
    group_name  VARCHAR(64),
    status      VARCHAR(32) NOT NULL DEFAULT 'unused',
    created_by  VARCHAR(64),
    used_by     VARCHAR(64),
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_app_vouchers_code ON radiusflow.app_vouchers(code);
CREATE INDEX IF NOT EXISTS idx_app_vouchers_status ON radiusflow.app_vouchers(status);

GRANT SELECT, INSERT, UPDATE, DELETE ON radiusflow.app_audit_logs TO radiusflow_app;
GRANT USAGE, SELECT ON SEQUENCE radiusflow.app_audit_logs_id_seq TO radiusflow_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON radiusflow.app_vouchers TO radiusflow_app;
GRANT USAGE, SELECT ON SEQUENCE radiusflow.app_vouchers_id_seq TO radiusflow_app;

COMMIT;
