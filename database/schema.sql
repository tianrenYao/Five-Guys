-- ============================================================
-- Business Sustainability Management Platform
-- Database schema v3.0
-- Group 9 - Five Guys
-- ============================================================

-- Create database
CREATE DATABASE IF NOT EXISTS sustainability_platform
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE sustainability_platform;

-- Drop existing tables (reverse foreign key dependency order)
DROP TABLE IF EXISTS alert_log;
DROP TABLE IF EXISTS alert_threshold;
DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS company_sdg;
DROP TABLE IF EXISTS sdg_goal;
DROP TABLE IF EXISTS report;
DROP TABLE IF EXISTS waste_record;
DROP TABLE IF EXISTS waste_category;
DROP TABLE IF EXISTS carbon_record;
DROP TABLE IF EXISTS emission_factor;
DROP TABLE IF EXISTS `user`;
DROP TABLE IF EXISTS store;
DROP TABLE IF EXISTS region;
DROP TABLE IF EXISTS company;

-- Drop existing views
DROP VIEW IF EXISTS v_carbon_monthly_summary;
DROP VIEW IF EXISTS v_waste_monthly_summary;
DROP VIEW IF EXISTS v_store_carbon_summary;
DROP VIEW IF EXISTS v_store_waste_summary;

-- ============================================================
-- 1. company - organisation / HQ
-- ============================================================
CREATE TABLE company (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    name          VARCHAR(100) NOT NULL COMMENT 'Company name',
    industry      VARCHAR(50)  DEFAULT NULL COMMENT 'Industry sector',
    country       VARCHAR(50)  DEFAULT NULL COMMENT 'Country',
    address       VARCHAR(255) DEFAULT NULL COMMENT 'Registered address',
    contact_email VARCHAR(100) DEFAULT NULL COMMENT 'Contact email',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='Company / organisation master table';

-- ============================================================
-- 2. region - regional division (below HQ, manages multiple stores)
-- ============================================================
CREATE TABLE region (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    company_id  INT          NOT NULL COMMENT 'Owning company',
    name        VARCHAR(100) NOT NULL COMMENT 'Region name, e.g. North Region, South Region',
    description VARCHAR(255) DEFAULT NULL COMMENT 'Region description',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_region_company (company_id),
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='Regional division table';

-- ============================================================
-- 3. store - individual store (below region, base unit for data entry)
-- ============================================================
CREATE TABLE store (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    company_id  INT          NOT NULL COMMENT 'Owning company',
    region_id   INT          NOT NULL COMMENT 'Owning region',
    name        VARCHAR(100) NOT NULL COMMENT 'Store name',
    address     VARCHAR(255) DEFAULT NULL COMMENT 'Store address',
    city        VARCHAR(50)  DEFAULT NULL COMMENT 'City',
    opened_date DATE         DEFAULT NULL COMMENT 'Opening date',
    is_active   TINYINT(1)   NOT NULL DEFAULT 1 COMMENT 'Whether currently operational',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_store_company (company_id),
    INDEX idx_store_region  (region_id),
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,
    FOREIGN KEY (region_id)  REFERENCES region(id)  ON DELETE RESTRICT
) ENGINE=InnoDB COMMENT='Store table';

-- ============================================================
-- 4. user - user accounts (four roles: admin / hq_manager / region_manager / store_staff)
-- ============================================================
CREATE TABLE `user` (
    id           INT PRIMARY KEY AUTO_INCREMENT,
    company_id   INT          DEFAULT NULL COMMENT 'Owning company (NULL for platform admin)',
    region_id    INT          DEFAULT NULL COMMENT 'Assigned region (region_manager only; NULL = unrestricted)',
    store_id     INT          DEFAULT NULL COMMENT 'Assigned store (store_staff only; NULL = not store-level)',
    username     VARCHAR(50)  NOT NULL UNIQUE COMMENT 'Login username',
    password     VARCHAR(255) NOT NULL COMMENT 'Password hash (werkzeug pbkdf2)',
    display_name VARCHAR(50)  DEFAULT NULL COMMENT 'Display name',
    email        VARCHAR(100) DEFAULT NULL COMMENT 'Email address',
    role         ENUM('admin','hq_manager','region_manager','store_staff') NOT NULL DEFAULT 'store_staff'
                 COMMENT 'admin=platform admin, hq_manager=HQ ESG manager, region_manager=region admin, store_staff=store employee',
    is_active    TINYINT(1)   NOT NULL DEFAULT 1 COMMENT 'Whether account is enabled',
    last_login   DATETIME     DEFAULT NULL COMMENT 'Last login timestamp',
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_user_company (company_id),
    INDEX idx_user_region  (region_id),
    INDEX idx_user_store   (store_id),
    INDEX idx_user_role    (role),
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE SET NULL,
    FOREIGN KEY (region_id)  REFERENCES region(id)  ON DELETE SET NULL,
    FOREIGN KEY (store_id)   REFERENCES store(id)   ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='User account table';

-- ============================================================
-- 5. emission_factor - static emission factor reference table
--    Pre-seeded by developers; not editable via UI (course project decision)
-- ============================================================
CREATE TABLE emission_factor (
    id         INT PRIMARY KEY AUTO_INCREMENT,
    category   VARCHAR(50)   NOT NULL COMMENT 'Emission category: electricity / transport / fuel',
    sub_type   VARCHAR(50)   DEFAULT NULL COMMENT 'Sub-type: grid_cn / diesel_truck / natural_gas etc.',
    factor     DECIMAL(12,6) NOT NULL COMMENT 'Emission factor (kgCO2e per unit)',
    unit       VARCHAR(30)   NOT NULL COMMENT 'Unit of measurement: kWh / km / L / cubic_m',
    source     VARCHAR(100)  DEFAULT NULL COMMENT 'Data source: IPCC 2023 / GHG Protocol etc.',
    valid_year YEAR          DEFAULT NULL COMMENT 'Year the factor applies to',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_factor_category (category, sub_type)
) ENGINE=InnoDB COMMENT='Emission factor reference table (static, no UI editing)';

-- ============================================================
-- 6. carbon_record - carbon emission records
-- ============================================================
CREATE TABLE carbon_record (
    id             INT PRIMARY KEY AUTO_INCREMENT,
    company_id     INT           NOT NULL COMMENT 'Owning company',
    store_id       INT           NOT NULL COMMENT 'Owning store (smallest data entry unit)',
    user_id        INT           NOT NULL COMMENT 'Recorded by',
    factor_id      INT           DEFAULT NULL COMMENT 'Associated emission factor',
    category       VARCHAR(50)   NOT NULL COMMENT 'Emission category',
    activity_value DECIMAL(12,4) NOT NULL COMMENT 'Activity amount (kWh / km / litres etc.)',
    total_carbon   DECIMAL(12,4) NOT NULL COMMENT 'Calculated carbon emissions (kgCO2e)',
    record_date    DATE          NOT NULL COMMENT 'Record date',
    attachment_url VARCHAR(255)  DEFAULT NULL COMMENT 'Bill attachment path (electricity / gas bill etc.)',
    note           VARCHAR(255)  DEFAULT NULL COMMENT 'Notes',
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_carbon_company_date (company_id, record_date),
    INDEX idx_carbon_store        (store_id),
    INDEX idx_carbon_user         (user_id),
    INDEX idx_carbon_category     (category),
    FOREIGN KEY (company_id) REFERENCES company(id)         ON DELETE CASCADE,
    FOREIGN KEY (store_id)   REFERENCES store(id)           ON DELETE CASCADE,
    FOREIGN KEY (user_id)    REFERENCES `user`(id)          ON DELETE CASCADE,
    FOREIGN KEY (factor_id)  REFERENCES emission_factor(id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='Carbon emission data records';

-- ============================================================
-- 7. waste_category - waste type categories (Luckin Coffee scenario)
-- ============================================================
CREATE TABLE waste_category (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    name          VARCHAR(50)  NOT NULL UNIQUE COMMENT 'Category name',
    is_recyclable TINYINT(1)   NOT NULL DEFAULT 0 COMMENT 'Whether recyclable',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='Waste type category table';

-- ============================================================
-- 8. waste_record - waste management records
-- ============================================================
CREATE TABLE waste_record (
    id             INT PRIMARY KEY AUTO_INCREMENT,
    company_id     INT           NOT NULL COMMENT 'Owning company',
    store_id       INT           NOT NULL COMMENT 'Owning store',
    user_id        INT           NOT NULL COMMENT 'Recorded by',
    category_id    INT           NOT NULL COMMENT 'Waste category',
    source_type    ENUM('packaging','food_residue','hazardous','other') NOT NULL DEFAULT 'other'
                   COMMENT 'Waste source: packaging=drink packaging, food_residue=food waste, hazardous=hazardous waste',
    weight_kg      DECIMAL(10,2) NOT NULL COMMENT 'Total weight generated (kg)',
    recycled_kg    DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT 'Recycled weight (kg)',
    disposal_method ENUM('recycling','landfill','incineration','composting','hazardous_disposal') DEFAULT NULL
                   COMMENT 'Disposal method',
    disposal_unit  VARCHAR(100)  DEFAULT NULL COMMENT 'Disposal contractor / recycler',
    record_date    DATE          NOT NULL COMMENT 'Record date',
    attachment_url VARCHAR(255)  DEFAULT NULL COMMENT 'Recycling proof attachment path',
    note           VARCHAR(255)  DEFAULT NULL COMMENT 'Notes',
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_waste_company_date (company_id, record_date),
    INDEX idx_waste_store        (store_id),
    INDEX idx_waste_user         (user_id),
    INDEX idx_waste_category     (category_id),
    FOREIGN KEY (company_id)  REFERENCES company(id)       ON DELETE CASCADE,
    FOREIGN KEY (store_id)    REFERENCES store(id)         ON DELETE CASCADE,
    FOREIGN KEY (user_id)     REFERENCES `user`(id)        ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES waste_category(id) ON DELETE RESTRICT
) ENGINE=InnoDB COMMENT='Waste management data records';

-- ============================================================
-- 9. report - sustainability report table (store / region / company level)
-- ============================================================
CREATE TABLE report (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    company_id    INT          NOT NULL COMMENT 'Owning company',
    user_id       INT          NOT NULL COMMENT 'Generated by',
    title         VARCHAR(150) NOT NULL COMMENT 'Report title',
    report_type   ENUM('monthly','quarterly','annual','custom') NOT NULL DEFAULT 'monthly',
    report_scope  ENUM('store','region','company') NOT NULL DEFAULT 'company'
                  COMMENT 'Report scope: store=single store, region=regional rollup, company=company-wide',
    scope_id      INT          DEFAULT NULL COMMENT 'Corresponding store_id or region_id (NULL for company scope)',
    date_from     DATE         NOT NULL COMMENT 'Period start date',
    date_to       DATE         NOT NULL COMMENT 'Period end date',
    content       TEXT         DEFAULT NULL COMMENT 'Report body (text summary)',
    ai_comment    TEXT         DEFAULT NULL COMMENT 'AI-generated evaluation and recommendations (DeepSeek)',
    pdf_path      VARCHAR(255) DEFAULT NULL COMMENT 'Exported PDF file path',
    status        ENUM('draft','generated','exported') NOT NULL DEFAULT 'draft',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_report_company (company_id),
    INDEX idx_report_user    (user_id),
    INDEX idx_report_dates   (date_from, date_to),
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)    REFERENCES `user`(id)  ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='Sustainability report table';

-- ============================================================
-- 10. sdg_goal - UN Sustainable Development Goals reference table
-- ============================================================
CREATE TABLE sdg_goal (
    id          INT PRIMARY KEY COMMENT 'SDG number (1-17)',
    name        VARCHAR(100) NOT NULL COMMENT 'Goal name',
    description TEXT         DEFAULT NULL COMMENT 'Goal description',
    icon_url    VARCHAR(255) DEFAULT NULL COMMENT 'Icon path'
) ENGINE=InnoDB COMMENT='UN Sustainable Development Goals (SDG) reference table';

-- ============================================================
-- 11. company_sdg - company SDG goal alignment and progress tracking
-- ============================================================
CREATE TABLE company_sdg (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    company_id    INT           NOT NULL,
    sdg_id        INT           NOT NULL,
    target_value  DECIMAL(10,2) DEFAULT NULL COMMENT 'Target value',
    current_value DECIMAL(10,2) DEFAULT NULL COMMENT 'Current value',
    note          VARCHAR(255)  DEFAULT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_company_sdg (company_id, sdg_id),
    FOREIGN KEY (company_id) REFERENCES company(id)  ON DELETE CASCADE,
    FOREIGN KEY (sdg_id)     REFERENCES sdg_goal(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='Company-SDG goal association table';

-- ============================================================
-- 12. alert_threshold - alert threshold config (configurable by hq_manager)
-- ============================================================
CREATE TABLE alert_threshold (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    company_id      INT          NOT NULL COMMENT 'Owning company',
    metric_type     ENUM('waste_recycling_rate','carbon_mom_growth','waste_weight_daily') NOT NULL
                    COMMENT 'waste_recycling_rate=recovery rate, carbon_mom_growth=carbon MoM growth, waste_weight_daily=daily waste weight',
    scope           ENUM('company','region','store') NOT NULL DEFAULT 'company'
                    COMMENT 'Threshold scope',
    scope_id        INT          DEFAULT NULL COMMENT 'Specific region_id or store_id (NULL for company scope)',
    threshold_value DECIMAL(10,2) NOT NULL COMMENT 'Threshold value (e.g. 30.00 = 30%)',
    comparison      ENUM('lt','gt') NOT NULL DEFAULT 'lt'
                    COMMENT 'lt=trigger when below threshold, gt=trigger when above threshold',
    is_active       TINYINT(1)   NOT NULL DEFAULT 1 COMMENT 'Whether active',
    created_by      INT          NOT NULL COMMENT 'Created by (must be hq_manager)',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_threshold_company (company_id),
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES `user`(id)  ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='Alert threshold configuration table';

-- ============================================================
-- 13. alert_log - alert trigger records
-- ============================================================
CREATE TABLE alert_log (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    company_id      INT           NOT NULL COMMENT 'Owning company',
    store_id        INT           DEFAULT NULL COMMENT 'Store that triggered the alert',
    threshold_id    INT           DEFAULT NULL COMMENT 'Associated threshold configuration',
    metric_type     VARCHAR(50)   NOT NULL COMMENT 'Metric type',
    current_value   DECIMAL(10,2) NOT NULL COMMENT 'Actual value at trigger time',
    threshold_value DECIMAL(10,2) NOT NULL COMMENT 'Threshold value at trigger time',
    triggered_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Trigger timestamp',
    is_read         TINYINT(1)    NOT NULL DEFAULT 0 COMMENT 'Whether read',
    read_by         INT           DEFAULT NULL COMMENT 'Read by (user id)',
    read_at         DATETIME      DEFAULT NULL COMMENT 'Read timestamp',

    INDEX idx_alert_company    (company_id),
    INDEX idx_alert_store      (store_id),
    INDEX idx_alert_unread     (company_id, is_read),
    FOREIGN KEY (company_id)   REFERENCES company(id)          ON DELETE CASCADE,
    FOREIGN KEY (store_id)     REFERENCES store(id)            ON DELETE SET NULL,
    FOREIGN KEY (threshold_id) REFERENCES alert_threshold(id)  ON DELETE SET NULL,
    FOREIGN KEY (read_by)      REFERENCES `user`(id)           ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='Alert trigger log table';

-- ============================================================
-- 14. audit_log - operation audit log
-- ============================================================
CREATE TABLE audit_log (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id     INT          DEFAULT NULL COMMENT 'Acting user',
    action      VARCHAR(50)  NOT NULL COMMENT 'LOGIN / CREATE / UPDATE / DELETE / EXPORT',
    target_type VARCHAR(50)  DEFAULT NULL COMMENT 'carbon_record / waste_record / report etc.',
    target_id   INT          DEFAULT NULL COMMENT 'Target record ID',
    detail      VARCHAR(500) DEFAULT NULL COMMENT 'Action detail',
    ip_address  VARCHAR(45)  DEFAULT NULL COMMENT 'Client IP address',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_audit_user   (user_id),
    INDEX idx_audit_action (action),
    INDEX idx_audit_time   (created_at),
    FOREIGN KEY (user_id) REFERENCES `user`(id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='Operation audit log table';

-- ============================================================
-- Initial seed data
-- ============================================================

-- Demo company
INSERT INTO company (id, name, industry, country)
VALUES (1, 'Luckin Coffee', 'Food & Beverage', 'China');

-- Three regions
INSERT INTO region (id, company_id, name, description) VALUES
(1, 1, 'North Region',  'Covers Beijing, Tianjin, Hebei stores'),
(2, 1, 'South Region',  'Covers Guangzhou, Shenzhen, and other Guangdong stores'),
(3, 1, 'East Region',   'Covers Shanghai, Nanjing, Hangzhou stores');

-- Six demo stores (two per region)
INSERT INTO store (id, company_id, region_id, name, city, opened_date) VALUES
(1, 1, 1, 'Chaoyang Store',   'Beijing',   '2022-03-15'),
(2, 1, 1, 'Haidian Store',    'Beijing',   '2022-07-01'),
(3, 1, 2, 'Tianhe Store',     'Guangzhou', '2021-11-20'),
(4, 1, 2, 'Nanshan Store',    'Shenzhen',  '2022-01-10'),
(5, 1, 3, 'Jingan Store',     'Shanghai',  '2021-06-01'),
(6, 1, 3, 'West Lake Store',  'Hangzhou',  '2022-09-08');

-- Test accounts (password: '123456'; hash generated by werkzeug pbkdf2)
-- Run database/init_users.py to generate correct hashes, then replace placeholders below
INSERT INTO `user` (id, company_id, region_id, store_id, username, password, display_name, role) VALUES
(1, 1, NULL, NULL, 'test_business', 'PLACEHOLDER_RUN_INIT_USERS', 'HQ ESG Manager', 'hq_manager'),
(2, 1, 1,    NULL, 'test_region',   'PLACEHOLDER_RUN_INIT_USERS', 'North Region Manager', 'region_manager'),
(3, 1, 1,    1,    'test_staff',    'PLACEHOLDER_RUN_INIT_USERS', 'Beijing Chaoyang Staff', 'store_staff');

-- SDG goal reference data
INSERT INTO sdg_goal (id, name, description) VALUES
(9,  'Industry, Innovation and Infrastructure', 'Build resilient infrastructure, promote inclusive and sustainable industrialisation'),
(11, 'Sustainable Cities and Communities',      'Make cities and human settlements inclusive, safe, resilient and sustainable'),
(12, 'Responsible Consumption and Production',  'Ensure sustainable consumption and production patterns'),
(13, 'Climate Action',                          'Take urgent action to combat climate change and its impacts');

-- Waste categories (Luckin Coffee scenario)
INSERT INTO waste_category (name, is_recyclable) VALUES
('Paper Cups & Lids',      1),
('Plastic Packaging',      1),
('Coffee Grounds',         0),
('Food Residue',           0),
('Hazardous Waste',        0),
('General Waste',          0),
('Cardboard / Paper',      1),
('E-Waste',                1);

-- Emission factors (Luckin Coffee stores, China context)
INSERT INTO emission_factor (category, sub_type, factor, unit, source, valid_year) VALUES
('electricity', 'grid_china',       0.5810, 'kWh',     'MEE China 2023',  2023),
('electricity', 'grid_ireland',     0.2960, 'kWh',     'SEAI 2023',       2023),
('transport',   'diesel_truck',     0.9000, 'km',      'IPCC 2023',       2023),
('transport',   'electric_truck',   0.2400, 'km',      'Estimated 2023',  2023),
('transport',   'petrol_car',       0.1700, 'km',      'DEFRA 2023',      2023),
('fuel',        'natural_gas',      2.0200, 'cubic_m', 'IPCC 2023',       2023),
('fuel',        'diesel',           2.6800, 'L',       'IPCC 2023',       2023);

-- Default alert thresholds (company-wide)
INSERT INTO alert_threshold (company_id, metric_type, scope, threshold_value, comparison, created_by) VALUES
(1, 'waste_recycling_rate', 'company', 30.00, 'lt', 1),
(1, 'carbon_mom_growth',    'company', 20.00, 'gt', 1);

-- SDG alignment (Luckin focuses on SDG12 and SDG13)
INSERT INTO company_sdg (company_id, sdg_id, target_value, note) VALUES
(1, 12, 80.00, 'Packaging recovery rate target: 80%'),
(1, 13, NULL,  'Annual carbon emission reduction target');

-- ============================================================
-- View: company-level monthly carbon emission summary (with store dimension)
-- ============================================================
CREATE OR REPLACE VIEW v_carbon_monthly_summary AS
SELECT
    cr.company_id,
    cr.store_id,
    s.region_id,
    cr.category,
    YEAR(cr.record_date)   AS `year`,
    MONTH(cr.record_date)  AS `month`,
    SUM(cr.activity_value) AS total_activity,
    SUM(cr.total_carbon)   AS total_carbon_kg,
    COUNT(*)               AS record_count
FROM carbon_record cr
JOIN store s ON s.id = cr.store_id
GROUP BY cr.company_id, cr.store_id, s.region_id, cr.category,
         YEAR(cr.record_date), MONTH(cr.record_date);

-- ============================================================
-- View: monthly waste recovery rate summary (with store dimension)
-- ============================================================
CREATE OR REPLACE VIEW v_waste_monthly_summary AS
SELECT
    wr.company_id,
    wr.store_id,
    s.region_id,
    YEAR(wr.record_date)   AS `year`,
    MONTH(wr.record_date)  AS `month`,
    SUM(wr.weight_kg)      AS total_weight_kg,
    SUM(wr.recycled_kg)    AS total_recycled_kg,
    ROUND(
        SUM(wr.recycled_kg) / NULLIF(SUM(wr.weight_kg), 0) * 100, 2
    ) AS recovery_rate_pct
FROM waste_record wr
JOIN store s ON s.id = wr.store_id
GROUP BY wr.company_id, wr.store_id, s.region_id,
         YEAR(wr.record_date), MONTH(wr.record_date);

-- ============================================================
-- View: store carbon MoM comparison (used for MoM growth alert calculation)
-- ============================================================
CREATE OR REPLACE VIEW v_store_carbon_summary AS
SELECT
    company_id, store_id, region_id, `year`, `month`,
    SUM(total_carbon_kg) AS total_carbon_kg
FROM v_carbon_monthly_summary
GROUP BY company_id, store_id, region_id, `year`, `month`;

-- ============================================================
-- View: store monthly waste summary (used for recovery rate alert calculation)
-- ============================================================
CREATE OR REPLACE VIEW v_store_waste_summary AS
SELECT
    company_id, store_id, region_id, `year`, `month`,
    SUM(total_weight_kg)   AS total_weight_kg,
    SUM(total_recycled_kg) AS total_recycled_kg,
    ROUND(
        SUM(total_recycled_kg) / NULLIF(SUM(total_weight_kg), 0) * 100, 2
    ) AS recovery_rate_pct
FROM v_waste_monthly_summary
GROUP BY company_id, store_id, region_id, `year`, `month`;
