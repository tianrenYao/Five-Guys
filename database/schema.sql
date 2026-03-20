-- ============================================================
-- Business Sustainability Management Platform
-- 数据库建表脚本 v2.0
-- Group 9 - Five Guys
-- ============================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS sustainability_platform
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE sustainability_platform;

-- ============================================================
-- 1. company - 企业/组织表
--    支持多企业入驻，每个企业独立管理数据
-- ============================================================
CREATE TABLE company (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL COMMENT '企业名称',
    industry    VARCHAR(50)  DEFAULT NULL COMMENT '所属行业',
    country     VARCHAR(50)  DEFAULT NULL COMMENT '所在国家',
    address     VARCHAR(255) DEFAULT NULL COMMENT '企业地址',
    contact_email VARCHAR(100) DEFAULT NULL COMMENT '联系邮箱',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='企业/组织信息表';

-- ============================================================
-- 2. user - 用户表
--    密码使用 bcrypt/werkzeug 哈希存储，role 区分权限
-- ============================================================
CREATE TABLE `user` (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    company_id  INT          DEFAULT NULL COMMENT '所属企业（NULL 表示平台管理员）',
    username    VARCHAR(50)  NOT NULL UNIQUE COMMENT '登录用户名',
    password    VARCHAR(255) NOT NULL COMMENT '密码哈希值（bcrypt/werkzeug）',
    display_name VARCHAR(50) DEFAULT NULL COMMENT '显示名称',
    email       VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    role        ENUM('admin','business','staff') NOT NULL DEFAULT 'staff'
                COMMENT 'admin=平台管理员, business=企业管理者, staff=普通员工',
    is_active   TINYINT(1)  NOT NULL DEFAULT 1 COMMENT '账户是否启用',
    last_login  DATETIME    DEFAULT NULL COMMENT '最近登录时间',
    created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_user_company (company_id),
    INDEX idx_user_role    (role),
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='用户账户表';

-- ============================================================
-- 3. emission_factor - 碳排放因子表
--    存储各类排放源的标准换算系数（参考 GHG Protocol / IPCC）
-- ============================================================
CREATE TABLE emission_factor (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    category    VARCHAR(50)  NOT NULL COMMENT '排放类别：electricity / transport / fuel / commute 等',
    sub_type    VARCHAR(50)  DEFAULT NULL COMMENT '子类型：如 electricity→grid_cn, transport→diesel',
    factor      DECIMAL(12,6) NOT NULL COMMENT '排放因子 (kgCO2e/单位)',
    unit        VARCHAR(30)  NOT NULL COMMENT '计量单位：kWh / km / L / kg',
    source      VARCHAR(100) DEFAULT NULL COMMENT '数据来源：IPCC 2023 / GHG Protocol 等',
    valid_year  YEAR         DEFAULT NULL COMMENT '因子适用年份',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_factor_category (category, sub_type)
) ENGINE=InnoDB COMMENT='碳排放因子参照表';

-- ============================================================
-- 4. carbon_record - 碳排放记录表
--    每条记录对应一次排放数据录入，支持多类别
-- ============================================================
CREATE TABLE carbon_record (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    company_id    INT          NOT NULL COMMENT '所属企业',
    user_id       INT          NOT NULL COMMENT '录入人',
    factor_id     INT          DEFAULT NULL COMMENT '关联的排放因子',
    category      VARCHAR(50)  NOT NULL COMMENT '排放类别',
    activity_value DECIMAL(12,4) NOT NULL COMMENT '活动量（用电量/里程/燃油量等）',
    total_carbon  DECIMAL(12,4) NOT NULL COMMENT '计算后碳排放量 (kgCO2e)',
    record_date   DATE         NOT NULL COMMENT '数据所属日期',
    note          VARCHAR(255) DEFAULT NULL COMMENT '备注',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_carbon_company_date (company_id, record_date),
    INDEX idx_carbon_user         (user_id),
    INDEX idx_carbon_category     (category),
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)    REFERENCES `user`(id)  ON DELETE CASCADE,
    FOREIGN KEY (factor_id)  REFERENCES emission_factor(id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='碳排放数据记录表';

-- ============================================================
-- 5. waste_category - 垃圾分类类别表
--    支持自定义垃圾类型，而非硬编码
-- ============================================================
CREATE TABLE waste_category (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(50)  NOT NULL UNIQUE COMMENT '类别名称：一般垃圾 / 可回收 / 有害 / 厨余等',
    is_recyclable TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否可回收',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='垃圾分类类别表';

-- ============================================================
-- 6. waste_record - 垃圾管理记录表
-- ============================================================
CREATE TABLE waste_record (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    company_id    INT          NOT NULL COMMENT '所属企业',
    user_id       INT          NOT NULL COMMENT '录入人',
    category_id   INT          NOT NULL COMMENT '垃圾类别',
    weight_kg     DECIMAL(10,2) NOT NULL COMMENT '垃圾重量 (kg)',
    record_date   DATE         NOT NULL COMMENT '数据所属日期',
    note          VARCHAR(255) DEFAULT NULL COMMENT '备注',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_waste_company_date (company_id, record_date),
    INDEX idx_waste_user         (user_id),
    INDEX idx_waste_category     (category_id),
    FOREIGN KEY (company_id)  REFERENCES company(id)        ON DELETE CASCADE,
    FOREIGN KEY (user_id)     REFERENCES `user`(id)         ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES waste_category(id)  ON DELETE RESTRICT
) ENGINE=InnoDB COMMENT='垃圾管理数据记录表';

-- ============================================================
-- 7. report - 可持续发展报告表
--    增加报告类型、状态、覆盖日期范围等元数据
-- ============================================================
CREATE TABLE report (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    company_id    INT          NOT NULL COMMENT '所属企业',
    user_id       INT          NOT NULL COMMENT '生成人',
    title         VARCHAR(150) NOT NULL COMMENT '报告标题',
    report_type   ENUM('monthly','quarterly','annual','custom') NOT NULL DEFAULT 'monthly'
                  COMMENT '报告类型',
    date_from     DATE         NOT NULL COMMENT '覆盖起始日期',
    date_to       DATE         NOT NULL COMMENT '覆盖截止日期',
    content       TEXT         DEFAULT NULL COMMENT '报告正文（HTML/Markdown）',
    pdf_path      VARCHAR(255) DEFAULT NULL COMMENT '导出 PDF 文件路径',
    status        ENUM('draft','generated','exported') NOT NULL DEFAULT 'draft'
                  COMMENT '报告状态',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_report_company  (company_id),
    INDEX idx_report_user     (user_id),
    INDEX idx_report_dates    (date_from, date_to),
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)    REFERENCES `user`(id)  ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='可持续发展报告表';

-- ============================================================
-- 8. sdg_goal - 联合国可持续发展目标参照表
-- ============================================================
CREATE TABLE sdg_goal (
    id          INT PRIMARY KEY COMMENT 'SDG 编号 (1-17)',
    name        VARCHAR(100) NOT NULL COMMENT '目标名称',
    description TEXT         DEFAULT NULL COMMENT '目标描述',
    icon_url    VARCHAR(255) DEFAULT NULL COMMENT '图标路径'
) ENGINE=InnoDB COMMENT='联合国可持续发展目标 (SDG) 参照表';

-- ============================================================
-- 9. company_sdg - 企业 SDG 目标关联表
--    记录企业关注的 SDG 目标及当前进展
-- ============================================================
CREATE TABLE company_sdg (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    company_id  INT     NOT NULL,
    sdg_id      INT     NOT NULL,
    target_value DECIMAL(10,2) DEFAULT NULL COMMENT '目标值',
    current_value DECIMAL(10,2) DEFAULT NULL COMMENT '当前值',
    note        VARCHAR(255)   DEFAULT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_company_sdg (company_id, sdg_id),
    FOREIGN KEY (company_id) REFERENCES company(id)  ON DELETE CASCADE,
    FOREIGN KEY (sdg_id)     REFERENCES sdg_goal(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='企业-SDG目标关联表';

-- ============================================================
-- 10. audit_log - 操作审计日志表
--     记录关键用户操作，便于追溯
-- ============================================================
CREATE TABLE audit_log (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id     INT          DEFAULT NULL COMMENT '操作用户',
    action      VARCHAR(50)  NOT NULL COMMENT '操作类型：LOGIN / CREATE / UPDATE / DELETE / EXPORT',
    target_type VARCHAR(50)  DEFAULT NULL COMMENT '操作对象类型：carbon_record / waste_record / report',
    target_id   INT          DEFAULT NULL COMMENT '操作对象 ID',
    detail      VARCHAR(500) DEFAULT NULL COMMENT '操作详情',
    ip_address  VARCHAR(45)  DEFAULT NULL COMMENT '客户端 IP',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_audit_user   (user_id),
    INDEX idx_audit_action (action),
    INDEX idx_audit_time   (created_at),
    FOREIGN KEY (user_id) REFERENCES `user`(id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='操作审计日志表';

-- ============================================================
-- 初始化数据
-- ============================================================

-- 默认企业
INSERT INTO company (id, name, industry, country)
VALUES (1, 'Demo Corporation', 'Technology', 'Ireland');

-- 测试账号（密码 '123456' 的 werkzeug pbkdf2 哈希值）
-- 实际部署时应通过 Flask 脚本生成，此处使用占位哈希
INSERT INTO `user` (company_id, username, password, display_name, role) VALUES
(1, 'test_business', 'pbkdf2:sha256:600000$PLACEHOLDER$HASH_WILL_BE_GENERATED_BY_FLASK', 'Business Admin', 'business'),
(1, 'test_staff',    'pbkdf2:sha256:600000$PLACEHOLDER$HASH_WILL_BE_GENERATED_BY_FLASK', 'Staff User',    'staff');

-- SDG 目标参照数据（与本平台相关的 4 个）
INSERT INTO sdg_goal (id, name, description) VALUES
(9,  'Industry, Innovation and Infrastructure', '建设有弹性的基础设施，推动包容和可持续的工业化发展，促进创新'),
(11, 'Sustainable Cities and Communities',      '建设包容、安全、有弹性和可持续的城市与人类住区'),
(12, 'Responsible Consumption and Production',  '确保可持续的消费和生产模式'),
(13, 'Climate Action',                          '采取紧急行动应对气候变化及其影响');

-- 默认垃圾分类类别
INSERT INTO waste_category (name, is_recyclable) VALUES
('General Waste',    0),
('Recyclable Waste', 1),
('Hazardous Waste',  0),
('Organic Waste',    0),
('E-Waste',          1);

-- 常用碳排放因子（参考 IPCC 2023 / GHG Protocol）
INSERT INTO emission_factor (category, sub_type, factor, unit, source, valid_year) VALUES
('electricity', 'grid_ireland', 0.2960, 'kWh', 'SEAI 2023',        2023),
('electricity', 'grid_china',   0.5810, 'kWh', 'MEE China 2023',   2023),
('transport',   'petrol_car',   0.1700, 'km',  'DEFRA 2023',       2023),
('transport',   'diesel_car',   0.1710, 'km',  'DEFRA 2023',       2023),
('transport',   'bus',          0.0890, 'km',  'DEFRA 2023',       2023),
('transport',   'rail',         0.0350, 'km',  'DEFRA 2023',       2023),
('transport',   'flight_short', 0.2550, 'km',  'DEFRA 2023',       2023),
('fuel',        'natural_gas',  2.0200, 'cubic_m', 'IPCC 2023',    2023),
('fuel',        'diesel',       2.6800, 'L',   'IPCC 2023',        2023),
('commute',     'car_solo',     0.1700, 'km',  'DEFRA 2023',       2023),
('commute',     'carpool_2',    0.0850, 'km',  'Estimated',        2023),
('commute',     'bicycle',      0.0000, 'km',  'Zero emission',    2023);

-- ============================================================
-- 视图：企业碳排放月度汇总（供 Dashboard 图表使用）
-- ============================================================
CREATE OR REPLACE VIEW v_carbon_monthly_summary AS
SELECT
    cr.company_id,
    cr.category,
    YEAR(cr.record_date)  AS `year`,
    MONTH(cr.record_date) AS `month`,
    SUM(cr.activity_value) AS total_activity,
    SUM(cr.total_carbon)   AS total_carbon_kg,
    COUNT(*)               AS record_count
FROM carbon_record cr
GROUP BY cr.company_id, cr.category, YEAR(cr.record_date), MONTH(cr.record_date);

-- ============================================================
-- 视图：企业垃圾回收率月度汇总
-- ============================================================
CREATE OR REPLACE VIEW v_waste_monthly_summary AS
SELECT
    wr.company_id,
    YEAR(wr.record_date)  AS `year`,
    MONTH(wr.record_date) AS `month`,
    SUM(wr.weight_kg)     AS total_weight_kg,
    SUM(CASE WHEN wc.is_recyclable = 1 THEN wr.weight_kg ELSE 0 END) AS recyclable_kg,
    ROUND(
        SUM(CASE WHEN wc.is_recyclable = 1 THEN wr.weight_kg ELSE 0 END)
        / NULLIF(SUM(wr.weight_kg), 0) * 100, 2
    ) AS recovery_rate_pct
FROM waste_record wr
JOIN waste_category wc ON wc.id = wr.category_id
GROUP BY wr.company_id, YEAR(wr.record_date), MONTH(wr.record_date);
