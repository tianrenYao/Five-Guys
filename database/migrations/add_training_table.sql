-- Migration: Add employee sustainability training table
-- Run once against the sustainability_platform database

CREATE TABLE IF NOT EXISTS training_record (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    company_id       INT          NOT NULL,
    store_id         INT          DEFAULT NULL,
    trainee_user_id  INT          DEFAULT NULL COMMENT 'Staff who completed training',
    course_name      VARCHAR(150) NOT NULL,
    course_type      ENUM('carbon_awareness','waste_management','energy_efficiency',
                         'sustainability_reporting','green_procurement','other')
                     NOT NULL DEFAULT 'other',
    duration_hours   DECIMAL(5,1) NOT NULL DEFAULT 0,
    completion_date  DATE         NOT NULL,
    score            TINYINT UNSIGNED DEFAULT NULL COMMENT '0-100 assessment score',
    status           ENUM('completed','in_progress','cancelled') NOT NULL DEFAULT 'completed',
    note             TEXT         DEFAULT NULL,
    created_by       INT          NOT NULL COMMENT 'User who logged this record',
    created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_training_company  (company_id),
    INDEX idx_training_store    (store_id),
    INDEX idx_training_trainee  (trainee_user_id),
    INDEX idx_training_date     (completion_date),
    FOREIGN KEY (company_id)      REFERENCES company(id) ON DELETE CASCADE,
    FOREIGN KEY (store_id)        REFERENCES store(id)   ON DELETE SET NULL,
    FOREIGN KEY (trainee_user_id) REFERENCES `user`(id)  ON DELETE SET NULL,
    FOREIGN KEY (created_by)      REFERENCES `user`(id)  ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='Employee sustainability training completion records';
