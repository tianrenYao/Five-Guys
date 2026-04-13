-- Migration: add notify_email column to alert_threshold
-- Run once against the sustainability_platform database

ALTER TABLE alert_threshold
    ADD COLUMN notify_email VARCHAR(500) DEFAULT NULL
    COMMENT 'Comma-separated recipient emails for alert notifications'
    AFTER is_active;
