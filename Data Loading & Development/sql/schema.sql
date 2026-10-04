-- =========================================================
-- Enterprise ETL Pipeline — Data Warehouse Schema
-- Target: PostgreSQL 15+ (Snowflake compatible with minor edits)
-- =========================================================

-- ---------------------------------------------------------
-- Customers (unified from Stripe customers + Salesforce accounts)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id        VARCHAR(64)  NOT NULL,
    source_system      VARCHAR(32)  NOT NULL,
    email              VARCHAR(255),
    full_name          VARCHAR(255),
    industry           VARCHAR(128),
    annual_revenue_usd NUMERIC(18, 2),
    is_delinquent      BOOLEAN      DEFAULT FALSE,
    created_at         TIMESTAMPTZ,
    updated_at         TIMESTAMPTZ,
    ingested_at        TIMESTAMPTZ  DEFAULT NOW(),
    PRIMARY KEY (customer_id, source_system)
);

-- ---------------------------------------------------------
-- Transactions (unified from Stripe charges + Salesforce opportunities)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id  VARCHAR(64)   NOT NULL,
    source_system   VARCHAR(32)   NOT NULL,
    customer_id     VARCHAR(64),
    amount_usd      NUMERIC(18, 2) NOT NULL,
    status          VARCHAR(64),
    description     TEXT,
    occurred_at     TIMESTAMPTZ,
    ingested_at     TIMESTAMPTZ   DEFAULT NOW(),
    PRIMARY KEY (transaction_id, source_system)
);

-- ---------------------------------------------------------
-- Indexes for BI / analytics query performance
-- ---------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_customers_email     ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_source    ON customers(source_system);
CREATE INDEX IF NOT EXISTS idx_tx_customer         ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_tx_occurred         ON transactions(occurred_at);
CREATE INDEX IF NOT EXISTS idx_tx_source           ON transactions(source_system);