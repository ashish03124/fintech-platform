CREATE DATABASE IF NOT EXISTS fintech;

CREATE TABLE IF NOT EXISTS fintech.transactions_log (
    id String,
    amount Float64,
    currency String,
    merchant String,
    category String,
    status String,
    timestamp DateTime
) ENGINE = MergeTree()
ORDER BY timestamp;
