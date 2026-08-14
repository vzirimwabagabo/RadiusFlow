-- Migration to create radiusflow.payments table for Safaricom Daraja M-Pesa transactions
BEGIN;

CREATE TABLE IF NOT EXISTS radiusflow.payments (
    id                   BIGSERIAL PRIMARY KEY,
    merchant_request_id  VARCHAR(128) NOT NULL,
    checkout_request_id  VARCHAR(128) NOT NULL UNIQUE,
    phone_number         VARCHAR(20) NOT NULL,
    amount               NUMERIC(10,2) NOT NULL,
    mpesa_receipt_number VARCHAR(64),
    transaction_date     TIMESTAMPTZ,
    status               VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    result_code          INTEGER,
    result_desc          TEXT,
    user_id              BIGINT,
    package_name         VARCHAR(64),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payments_checkout_req ON radiusflow.payments(checkout_request_id);
CREATE INDEX IF NOT EXISTS idx_payments_phone ON radiusflow.payments(phone_number);
CREATE INDEX IF NOT EXISTS idx_payments_status ON radiusflow.payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_receipt ON radiusflow.payments(mpesa_receipt_number);

GRANT SELECT, INSERT, UPDATE, DELETE ON radiusflow.payments TO radiusflow_app;
GRANT USAGE, SELECT ON SEQUENCE radiusflow.payments_id_seq TO radiusflow_app;

COMMIT;
