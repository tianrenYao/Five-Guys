-- Migration: Supplier ESG Assessment + ESG Policy Management tables

-- Supplier ESG Assessment
CREATE TABLE IF NOT EXISTS supplier (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    company_id  INT NOT NULL,
    name        VARCHAR(200) NOT NULL COMMENT 'Supplier name',
    category    VARCHAR(100) DEFAULT NULL COMMENT 'e.g. Coffee Beans, Packaging, Logistics',
    country     VARCHAR(100) DEFAULT NULL,
    carbon_score     TINYINT DEFAULT NULL COMMENT '0-100: carbon emission management',
    waste_score      TINYINT DEFAULT NULL COMMENT '0-100: waste recycling capability',
    ethics_score     TINYINT DEFAULT NULL COMMENT '0-100: social/ethical standards',
    reporting_score  TINYINT DEFAULT NULL COMMENT '0-100: sustainability reporting',
    overall_grade    ENUM('A','B','C','D','F') DEFAULT NULL,
    notes       TEXT DEFAULT NULL,
    audited_by  INT DEFAULT NULL COMMENT 'User who last updated assessment',
    audited_at  DATETIME DEFAULT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,
    FOREIGN KEY (audited_by) REFERENCES `user`(id)  ON DELETE SET NULL,
    INDEX idx_supplier_company (company_id)
) ENGINE=InnoDB COMMENT='Supplier ESG evaluation records';

-- ESG Policy Management
CREATE TABLE IF NOT EXISTS esg_policy (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    company_id  INT NOT NULL,
    title       VARCHAR(255) NOT NULL,
    category    ENUM('environment','social','governance','sdg12','other') NOT NULL DEFAULT 'other',
    content     TEXT NOT NULL COMMENT 'Policy body (Markdown or plain text)',
    version     VARCHAR(20) DEFAULT '1.0',
    status      ENUM('draft','active','archived') NOT NULL DEFAULT 'draft',
    effective_date DATE DEFAULT NULL,
    created_by  INT NOT NULL,
    updated_by  INT DEFAULT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES `user`(id)  ON DELETE CASCADE,
    FOREIGN KEY (updated_by) REFERENCES `user`(id)  ON DELETE SET NULL,
    INDEX idx_policy_company (company_id)
) ENGINE=InnoDB COMMENT='ESG policy documents';

-- Seed mock suppliers for company 1
INSERT IGNORE INTO supplier (company_id, name, category, country, carbon_score, waste_score, ethics_score, reporting_score, overall_grade, notes) VALUES
(1, 'GreenBean Co.',      'Coffee Beans',  'Colombia', 82, 75, 90, 70, 'B', 'Rainforest Alliance certified; annual sustainability report published.'),
(1, 'EcoPack Ltd.',       'Packaging',     'China',    65, 88, 72, 55, 'B', 'Uses 80% recycled materials; limited carbon disclosure.'),
(1, 'SwiftLogistics Inc.','Logistics',     'Ireland',  45, 50, 68, 40, 'C', 'Fleet electrification plan underway; no formal ESG report yet.'),
(1, 'PureMilk Farms',     'Dairy',         'Ireland',  70, 60, 80, 60, 'B', 'Carbon-neutral milk pilot; moderate waste recovery rate.'),
(1, 'CleanCup Corp.',     'Disposables',   'Germany',  90, 92, 85, 88, 'A', 'Industry leader in compostable cup technology; full GRI reporting.');

-- Seed mock policies for company 1
INSERT IGNORE INTO esg_policy (company_id, title, category, content, version, status, effective_date, created_by) VALUES
(1, 'Responsible Consumption & Waste Policy', 'sdg12',
'## Purpose\nThis policy commits the company to SDG 12 targets by reducing single-use plastics, improving packaging recyclability, and achieving ≥60% waste recovery rate across all stores by 2026.\n\n## Scope\nApplies to all store operations, procurement, and supply chain partners.\n\n## Key Commitments\n- Replace all single-use plastic cups with certified compostable alternatives by Q4 2025.\n- Mandate supplier ESG assessments (minimum grade C) for all tier-1 suppliers.\n- Publish quarterly waste and recycling KPI dashboards accessible to all store managers.',
'1.2', 'active', '2025-01-01', 1),
(1, 'Carbon Reduction Roadmap', 'environment',
'## Objective\nReduce absolute carbon emissions by 30% by 2030 (baseline: 2023).\n\n## Actions\n- Transition store energy to renewable sources by 2027.\n- Partner with low-carbon logistics providers.\n- Implement monthly carbon tracking and anomaly reporting for all stores.',
'2.0', 'active', '2025-03-01', 1),
(1, 'Supplier Code of Conduct', 'governance',
'## Introduction\nAll suppliers must meet minimum ESG standards before onboarding and undergo annual assessments.\n\n## Requirements\n- Carbon disclosure: Must report Scope 1 & 2 emissions.\n- Waste: Must demonstrate a formal waste management plan.\n- Social: No child labour; fair wages; safe working conditions.\n- Reporting: Must provide an ESG or sustainability report at least biannually.',
'1.0', 'active', '2024-06-01', 1);
