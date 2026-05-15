-- Migration: add comment_source column to report table
-- Distinguishes whether the evaluation was AI-generated or rule-based template.
-- Idempotent: uses information_schema check + prepared statement (works on MySQL 5.7 / 8.x).

SET @col_exists := (
    SELECT COUNT(*)
      FROM information_schema.columns
     WHERE table_schema = DATABASE()
       AND table_name   = 'report'
       AND column_name  = 'comment_source'
);

SET @ddl := IF(
    @col_exists = 0,
    'ALTER TABLE `report` ADD COLUMN `comment_source` VARCHAR(16) DEFAULT NULL COMMENT ''Source of ai_comment: ai (DeepSeek) or template (rule-based)'' AFTER `ai_comment`',
    'SELECT ''comment_source column already exists, skipping ADD COLUMN'' AS msg'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Backfill: existing reports with non-null ai_comment are assumed to be AI-generated
UPDATE `report`
   SET `comment_source` = 'ai'
 WHERE `ai_comment` IS NOT NULL
   AND `comment_source` IS NULL;
