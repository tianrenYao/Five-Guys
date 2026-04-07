-- ============================================================
-- Business Sustainability Management Platform
-- Demo seed data  (seed.sql)
-- Coverage: Jan 2026 – Apr 2026, 6 stores
-- Includes: carbon emissions (electricity + gas + transport),
--           waste records, and pre-seeded alert trigger scenarios
-- ============================================================

USE sustainability_platform;

-- ============================================================
-- Carbon emission records
-- factor_id mapping (emission_factor insert order):
--   1 = electricity / grid_china   (0.5810 kgCO2e/kWh)
--   6 = fuel / natural_gas         (2.0200 kgCO2e/cubic_m)
--   3 = transport / diesel_truck   (0.9000 kgCO2e/km)
-- ============================================================

INSERT INTO carbon_record
  (company_id, store_id, user_id, factor_id, category, activity_value, total_carbon, record_date, note)
VALUES
-- ── Chaoyang Store (store_id=1) ───────────────────────────
(1,1,1, 1,'electricity', 11000.0, 6391.00, '2026-01-31', 'Jan electricity'),
(1,1,1, 6,'fuel',          480.0,  969.60, '2026-01-31', 'Jan natural gas'),
(1,1,1, 1,'electricity', 10500.0, 6100.50, '2026-02-28', 'Feb electricity'),
(1,1,1, 6,'fuel',          460.0,  929.20, '2026-02-28', 'Feb natural gas'),
-- Mar electricity spikes ~28% MoM -> triggers carbon_mom_growth > 20% alert
(1,1,1, 1,'electricity', 13500.0, 7843.50, '2026-03-31', 'Mar electricity (pre-maintenance peak)'),
(1,1,1, 6,'fuel',          490.0,  989.80, '2026-03-31', 'Mar natural gas'),
(1,1,1, 1,'electricity',  4200.0, 2440.20, '2026-04-07', 'Apr electricity (1-7)'),

-- ── Haidian Store (store_id=2) ────────────────────────────
(1,2,1, 1,'electricity',  8500.0, 4938.50, '2026-01-31', 'Jan electricity'),
(1,2,1, 6,'fuel',          350.0,  707.00, '2026-01-31', 'Jan natural gas'),
(1,2,1, 1,'electricity',  8200.0, 4764.20, '2026-02-28', 'Feb electricity'),
(1,2,1, 6,'fuel',          330.0,  666.60, '2026-02-28', 'Feb natural gas'),
(1,2,1, 1,'electricity',  8800.0, 5112.80, '2026-03-31', 'Mar electricity'),
(1,2,1, 6,'fuel',          360.0,  727.20, '2026-03-31', 'Mar natural gas'),
(1,2,1, 1,'electricity',  2800.0, 1626.80, '2026-04-07', 'Apr electricity (1-7)'),

-- ── Tianhe Store (store_id=3) ─────────────────────────────
(1,3,1, 1,'electricity', 10000.0, 5810.00, '2026-01-31', 'Jan electricity'),
(1,3,1, 6,'fuel',          420.0,  848.40, '2026-01-31', 'Jan natural gas'),
(1,3,1, 3,'transport',     800.0,  720.00, '2026-01-31', 'Jan freight delivery'),
(1,3,1, 1,'electricity',  9500.0, 5519.50, '2026-02-28', 'Feb electricity'),
(1,3,1, 6,'fuel',          400.0,  808.00, '2026-02-28', 'Feb natural gas'),
(1,3,1, 1,'electricity', 10500.0, 6100.50, '2026-03-31', 'Mar electricity'),
(1,3,1, 6,'fuel',          430.0,  868.60, '2026-03-31', 'Mar natural gas'),
(1,3,1, 3,'transport',     850.0,  765.00, '2026-03-31', 'Mar freight delivery'),
(1,3,1, 1,'electricity',  3200.0, 1859.20, '2026-04-07', 'Apr electricity (1-7)'),

-- ── Nanshan Store (store_id=4) ────────────────────────────
(1,4,1, 1,'electricity',  9000.0, 5229.00, '2026-01-31', 'Jan electricity'),
(1,4,1, 6,'fuel',          380.0,  767.60, '2026-01-31', 'Jan natural gas'),
(1,4,1, 1,'electricity',  8800.0, 5112.80, '2026-02-28', 'Feb electricity'),
(1,4,1, 6,'fuel',          365.0,  737.30, '2026-02-28', 'Feb natural gas'),
(1,4,1, 1,'electricity',  9500.0, 5519.50, '2026-03-31', 'Mar electricity'),
(1,4,1, 6,'fuel',          390.0,  787.80, '2026-03-31', 'Mar natural gas'),
(1,4,1, 1,'electricity',  3000.0, 1743.00, '2026-04-07', 'Apr electricity (1-7)'),

-- ── Jingan Store (store_id=5) ─────────────────────────────
(1,5,1, 1,'electricity', 11500.0, 6681.50, '2026-01-31', 'Jan electricity'),
(1,5,1, 6,'fuel',          500.0, 1010.00, '2026-01-31', 'Jan natural gas'),
(1,5,1, 3,'transport',     600.0,  540.00, '2026-01-31', 'Jan delivery'),
(1,5,1, 1,'electricity', 11000.0, 6391.00, '2026-02-28', 'Feb electricity'),
(1,5,1, 6,'fuel',          480.0,  969.60, '2026-02-28', 'Feb natural gas'),
(1,5,1, 1,'electricity', 11800.0, 6855.80, '2026-03-31', 'Mar electricity'),
(1,5,1, 6,'fuel',          510.0, 1030.20, '2026-03-31', 'Mar natural gas'),
(1,5,1, 3,'transport',     650.0,  585.00, '2026-03-31', 'Mar delivery'),
(1,5,1, 1,'electricity',  3500.0, 2033.50, '2026-04-07', 'Apr electricity (1-7)'),

-- ── West Lake Store (store_id=6) ──────────────────────────
(1,6,1, 1,'electricity',  7500.0, 4357.50, '2026-01-31', 'Jan electricity'),
(1,6,1, 6,'fuel',          300.0,  606.00, '2026-01-31', 'Jan natural gas'),
(1,6,1, 1,'electricity',  7200.0, 4183.20, '2026-02-28', 'Feb electricity'),
(1,6,1, 6,'fuel',          285.0,  575.70, '2026-02-28', 'Feb natural gas'),
(1,6,1, 1,'electricity',  7800.0, 4531.80, '2026-03-31', 'Mar electricity'),
(1,6,1, 6,'fuel',          310.0,  626.20, '2026-03-31', 'Mar natural gas'),
(1,6,1, 1,'electricity',  2500.0, 1452.50, '2026-04-07', 'Apr electricity (1-7)');

-- ============================================================
-- Waste records
-- category_id: 1=Paper Cups & Lids (recyclable), 3=Coffee Grounds,
--              6=General Waste, 7=Cardboard (recyclable)
-- Normal stores: recovery rate ~35-45% (above 30% threshold)
-- Tianhe Store (store_id=3): recovery rate ~4% -> triggers
--   waste_recycling_rate < 30% alert
-- ============================================================

INSERT INTO waste_record
  (company_id, store_id, user_id, category_id, source_type, weight_kg, recycled_kg,
   disposal_method, disposal_unit, record_date, note)
VALUES
-- ── Chaoyang Store (normal, recovery ~42%) ────────────────
(1,1,1, 1,'packaging',   28.0, 22.0, 'recycling',  'GreenCycle Ltd.',  '2026-01-31', 'Paper cups & lids'),
(1,1,1, 3,'food_residue',62.0,  0.0, 'composting', NULL,               '2026-01-31', 'Coffee grounds'),
(1,1,1, 7,'packaging',   18.0, 15.0, 'recycling',  'GreenCycle Ltd.',  '2026-01-31', 'Cardboard boxes'),
(1,1,1, 6,'other',       22.0,  0.0, 'landfill',   NULL,               '2026-01-31', 'General waste'),
(1,1,1, 1,'packaging',   26.0, 21.0, 'recycling',  'GreenCycle Ltd.',  '2026-02-28', 'Paper cups & lids'),
(1,1,1, 3,'food_residue',58.0,  0.0, 'composting', NULL,               '2026-02-28', 'Coffee grounds'),
(1,1,1, 7,'packaging',   16.0, 13.0, 'recycling',  'GreenCycle Ltd.',  '2026-02-28', 'Cardboard boxes'),
(1,1,1, 6,'other',       20.0,  0.0, 'landfill',   NULL,               '2026-02-28', 'General waste'),
(1,1,1, 1,'packaging',   30.0, 24.0, 'recycling',  'GreenCycle Ltd.',  '2026-03-31', 'Paper cups & lids'),
(1,1,1, 3,'food_residue',65.0,  0.0, 'composting', NULL,               '2026-03-31', 'Coffee grounds'),
(1,1,1, 7,'packaging',   20.0, 16.0, 'recycling',  'GreenCycle Ltd.',  '2026-03-31', 'Cardboard boxes'),
(1,1,1, 6,'other',       25.0,  0.0, 'landfill',   NULL,               '2026-03-31', 'General waste'),

-- ── Haidian Store (normal, recovery ~40%) ─────────────────
(1,2,1, 1,'packaging',   22.0, 18.0, 'recycling',  'GreenCycle Ltd.',  '2026-01-31', 'Paper cups & lids'),
(1,2,1, 3,'food_residue',50.0,  0.0, 'composting', NULL,               '2026-01-31', 'Coffee grounds'),
(1,2,1, 7,'packaging',   14.0, 11.0, 'recycling',  'GreenCycle Ltd.',  '2026-01-31', 'Cardboard boxes'),
(1,2,1, 6,'other',       18.0,  0.0, 'landfill',   NULL,               '2026-01-31', 'General waste'),
(1,2,1, 1,'packaging',   21.0, 17.0, 'recycling',  'GreenCycle Ltd.',  '2026-02-28', 'Paper cups & lids'),
(1,2,1, 3,'food_residue',48.0,  0.0, 'composting', NULL,               '2026-02-28', 'Coffee grounds'),
(1,2,1, 7,'packaging',   13.0, 10.0, 'recycling',  'GreenCycle Ltd.',  '2026-02-28', 'Cardboard boxes'),
(1,2,1, 6,'other',       17.0,  0.0, 'landfill',   NULL,               '2026-02-28', 'General waste'),
(1,2,1, 1,'packaging',   24.0, 19.0, 'recycling',  'GreenCycle Ltd.',  '2026-03-31', 'Paper cups & lids'),
(1,2,1, 3,'food_residue',55.0,  0.0, 'composting', NULL,               '2026-03-31', 'Coffee grounds'),
(1,2,1, 7,'packaging',   15.0, 12.0, 'recycling',  'GreenCycle Ltd.',  '2026-03-31', 'Cardboard boxes'),
(1,2,1, 6,'other',       20.0,  0.0, 'landfill',   NULL,               '2026-03-31', 'General waste'),

-- ── Tianhe Store ⚠️ recovery ~4% -> triggers waste_recycling_rate alert ──
(1,3,1, 1,'packaging',   30.0,  1.5, 'landfill',   NULL,               '2026-01-31', 'Paper cups (recycler service suspended)'),
(1,3,1, 3,'food_residue',68.0,  0.0, 'landfill',   NULL,               '2026-01-31', 'Coffee grounds'),
(1,3,1, 7,'packaging',   20.0,  2.0, 'landfill',   NULL,               '2026-01-31', 'Cardboard (temporary landfill)'),
(1,3,1, 6,'other',       25.0,  0.0, 'landfill',   NULL,               '2026-01-31', 'General waste'),
(1,3,1, 1,'packaging',   28.0,  1.0, 'landfill',   NULL,               '2026-02-28', 'Paper cups & lids'),
(1,3,1, 3,'food_residue',64.0,  0.0, 'landfill',   NULL,               '2026-02-28', 'Coffee grounds'),
(1,3,1, 7,'packaging',   18.0,  1.5, 'landfill',   NULL,               '2026-02-28', 'Cardboard boxes'),
(1,3,1, 6,'other',       22.0,  0.0, 'landfill',   NULL,               '2026-02-28', 'General waste'),
(1,3,1, 1,'packaging',   32.0,  1.5, 'landfill',   NULL,               '2026-03-31', 'Paper cups & lids'),
(1,3,1, 3,'food_residue',70.0,  0.0, 'landfill',   NULL,               '2026-03-31', 'Coffee grounds'),
(1,3,1, 7,'packaging',   22.0,  2.0, 'landfill',   NULL,               '2026-03-31', 'Cardboard boxes'),
(1,3,1, 6,'other',       28.0,  0.0, 'landfill',   NULL,               '2026-03-31', 'General waste'),

-- ── Nanshan Store (normal, recovery ~38%) ─────────────────
(1,4,1, 1,'packaging',   25.0, 20.0, 'recycling',  'SZ Recycling Alliance', '2026-01-31', 'Paper cups & lids'),
(1,4,1, 3,'food_residue',58.0,  0.0, 'composting', NULL,                    '2026-01-31', 'Coffee grounds'),
(1,4,1, 7,'packaging',   16.0, 13.0, 'recycling',  'SZ Recycling Alliance', '2026-01-31', 'Cardboard boxes'),
(1,4,1, 6,'other',       20.0,  0.0, 'landfill',   NULL,                    '2026-01-31', 'General waste'),
(1,4,1, 1,'packaging',   24.0, 19.0, 'recycling',  'SZ Recycling Alliance', '2026-02-28', 'Paper cups & lids'),
(1,4,1, 3,'food_residue',56.0,  0.0, 'composting', NULL,                    '2026-02-28', 'Coffee grounds'),
(1,4,1, 7,'packaging',   15.0, 12.0, 'recycling',  'SZ Recycling Alliance', '2026-02-28', 'Cardboard boxes'),
(1,4,1, 6,'other',       19.0,  0.0, 'landfill',   NULL,                    '2026-02-28', 'General waste'),
(1,4,1, 1,'packaging',   27.0, 21.0, 'recycling',  'SZ Recycling Alliance', '2026-03-31', 'Paper cups & lids'),
(1,4,1, 3,'food_residue',60.0,  0.0, 'composting', NULL,                    '2026-03-31', 'Coffee grounds'),
(1,4,1, 7,'packaging',   17.0, 14.0, 'recycling',  'SZ Recycling Alliance', '2026-03-31', 'Cardboard boxes'),
(1,4,1, 6,'other',       22.0,  0.0, 'landfill',   NULL,                    '2026-03-31', 'General waste'),

-- ── Jingan Store (excellent, recovery ~55%) ───────────────
(1,5,1, 1,'packaging',   32.0, 28.0, 'recycling',  'SH GreenSource Co.', '2026-01-31', 'Paper cups & lids'),
(1,5,1, 3,'food_residue',70.0,  0.0, 'composting', NULL,                  '2026-01-31', 'Coffee grounds (composting)'),
(1,5,1, 7,'packaging',   22.0, 20.0, 'recycling',  'SH GreenSource Co.', '2026-01-31', 'Cardboard boxes'),
(1,5,1, 6,'other',       18.0,  2.0, 'landfill',   NULL,                  '2026-01-31', 'General waste (partially sorted)'),
(1,5,1, 1,'packaging',   30.0, 26.0, 'recycling',  'SH GreenSource Co.', '2026-02-28', 'Paper cups & lids'),
(1,5,1, 3,'food_residue',66.0,  0.0, 'composting', NULL,                  '2026-02-28', 'Coffee grounds'),
(1,5,1, 7,'packaging',   20.0, 18.0, 'recycling',  'SH GreenSource Co.', '2026-02-28', 'Cardboard boxes'),
(1,5,1, 6,'other',       16.0,  2.0, 'landfill',   NULL,                  '2026-02-28', 'General waste'),
(1,5,1, 1,'packaging',   34.0, 30.0, 'recycling',  'SH GreenSource Co.', '2026-03-31', 'Paper cups & lids'),
(1,5,1, 3,'food_residue',72.0,  0.0, 'composting', NULL,                  '2026-03-31', 'Coffee grounds'),
(1,5,1, 7,'packaging',   24.0, 22.0, 'recycling',  'SH GreenSource Co.', '2026-03-31', 'Cardboard boxes'),
(1,5,1, 6,'other',       20.0,  2.0, 'landfill',   NULL,                  '2026-03-31', 'General waste'),

-- ── West Lake Store (normal, recovery ~40%) ───────────────
(1,6,1, 1,'packaging',   20.0, 16.0, 'recycling',  'HZ Recycling Co.', '2026-01-31', 'Paper cups & lids'),
(1,6,1, 3,'food_residue',45.0,  0.0, 'composting', NULL,                '2026-01-31', 'Coffee grounds'),
(1,6,1, 7,'packaging',   12.0,  9.0, 'recycling',  'HZ Recycling Co.', '2026-01-31', 'Cardboard boxes'),
(1,6,1, 6,'other',       16.0,  0.0, 'landfill',   NULL,                '2026-01-31', 'General waste'),
(1,6,1, 1,'packaging',   19.0, 15.0, 'recycling',  'HZ Recycling Co.', '2026-02-28', 'Paper cups & lids'),
(1,6,1, 3,'food_residue',43.0,  0.0, 'composting', NULL,                '2026-02-28', 'Coffee grounds'),
(1,6,1, 7,'packaging',   11.0,  9.0, 'recycling',  'HZ Recycling Co.', '2026-02-28', 'Cardboard boxes'),
(1,6,1, 6,'other',       15.0,  0.0, 'landfill',   NULL,                '2026-02-28', 'General waste'),
(1,6,1, 1,'packaging',   22.0, 17.0, 'recycling',  'HZ Recycling Co.', '2026-03-31', 'Paper cups & lids'),
(1,6,1, 3,'food_residue',48.0,  0.0, 'composting', NULL,                '2026-03-31', 'Coffee grounds'),
(1,6,1, 7,'packaging',   13.0, 10.0, 'recycling',  'HZ Recycling Co.', '2026-03-31', 'Cardboard boxes'),
(1,6,1, 6,'other',       17.0,  0.0, 'landfill',   NULL,                '2026-03-31', 'General waste');

-- ============================================================
-- Pre-seeded alert log entries (demo scenarios)
-- Scenario 1: Tianhe Store Jan recovery rate 3.3% < 30% threshold
-- Scenario 2: Chaoyang Store Mar carbon MoM growth 28.6% > 20% threshold
-- ============================================================

INSERT INTO alert_log
  (company_id, store_id, threshold_id, metric_type, current_value, threshold_value, triggered_at)
VALUES
(1, 3, 1, 'waste_recycling_rate', 3.30,  30.00, '2026-02-01 08:05:00'),
(1, 3, 1, 'waste_recycling_rate', 3.50,  30.00, '2026-03-01 08:05:00'),
(1, 3, 1, 'waste_recycling_rate', 3.82,  30.00, '2026-04-01 08:05:00'),
(1, 1, 2, 'carbon_mom_growth',   28.60,  20.00, '2026-04-01 08:10:00');

-- ============================================================
-- Demo reports (HQ-level)
-- ============================================================

INSERT INTO report
  (company_id, user_id, title, report_type, report_scope, scope_id,
   date_from, date_to, status)
VALUES
(1, 1, 'Jan 2026 Sustainability Monthly Report',  'monthly',   'company', NULL, '2026-01-01', '2026-01-31', 'generated'),
(1, 1, 'Feb 2026 Sustainability Monthly Report',  'monthly',   'company', NULL, '2026-02-01', '2026-02-28', 'generated'),
(1, 1, '2026 Q1 Sustainability Report',           'quarterly', 'company', NULL, '2026-01-01', '2026-03-31', 'draft');
