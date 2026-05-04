-- ============================================================
-- Demo seed data: waste records (multi-month) + training records
-- Run: mysql -u <user> -p sustainability_platform < seed_demo_data.sql
-- ============================================================

USE sustainability_platform;

-- ============================================================
-- WASTE RECORDS  (category_id: 1=Paper Cups, 2=Plastic, 3=Coffee Grounds,
--                             4=Cardboard, 5=General Waste, 6=E-Waste)
-- Covers Feb / Mar / Apr 2026 so comparison modal shows meaningful MoM data
-- ============================================================

INSERT INTO waste_record
  (company_id, store_id, user_id, category_id, source_type, weight_kg, recycled_kg, disposal_method, record_date)
VALUES
-- ---- February 2026 ----
(1, 1, 1, 1, 'packaging',    22.0, 17.0, 'recycling',   '2026-02-28'),
(1, 1, 1, 3, 'food_residue', 45.0,  0.0, 'composting',  '2026-02-28'),
(1, 1, 1, 4, 'packaging',    14.0, 13.0, 'recycling',   '2026-02-28'),
(1, 1, 1, 5, 'other',        18.0,  0.0, 'landfill',    '2026-02-28'),
(1, 2, 1, 1, 'packaging',    20.0, 15.0, 'recycling',   '2026-02-28'),
(1, 2, 1, 3, 'food_residue', 40.0,  0.0, 'composting',  '2026-02-28'),
(1, 2, 1, 4, 'packaging',    12.0, 11.0, 'recycling',   '2026-02-28'),
(1, 3, 1, 1, 'packaging',    25.0, 19.0, 'recycling',   '2026-02-28'),
(1, 3, 1, 3, 'food_residue', 50.0,  0.0, 'composting',  '2026-02-28'),
(1, 4, 1, 1, 'packaging',    18.0, 14.0, 'recycling',   '2026-02-28'),
(1, 4, 1, 5, 'other',        22.0,  2.0, 'landfill',    '2026-02-28'),
(1, 5, 1, 4, 'packaging',    16.0, 15.0, 'recycling',   '2026-02-28'),
(1, 6, 1, 1, 'packaging',    21.0, 16.0, 'recycling',   '2026-02-28'),
(1, 6, 1, 3, 'food_residue', 48.0,  0.0, 'composting',  '2026-02-28'),

-- ---- March 2026 ----
(1, 1, 1, 1, 'packaging',    24.0, 18.0, 'recycling',   '2026-03-31'),
(1, 1, 1, 3, 'food_residue', 52.0,  0.0, 'composting',  '2026-03-31'),
(1, 1, 1, 4, 'packaging',    15.0, 14.0, 'recycling',   '2026-03-31'),
(1, 1, 1, 5, 'other',        20.0,  2.0, 'landfill',    '2026-03-31'),
(1, 2, 1, 1, 'packaging',    22.0, 17.0, 'recycling',   '2026-03-31'),
(1, 2, 1, 3, 'food_residue', 44.0,  0.0, 'composting',  '2026-03-31'),
(1, 3, 1, 1, 'packaging',    26.0, 20.0, 'recycling',   '2026-03-31'),
(1, 3, 1, 3, 'food_residue', 55.0,  0.0, 'composting',  '2026-03-31'),
(1, 4, 1, 1, 'packaging',    19.0, 15.0, 'recycling',   '2026-03-31'),
(1, 4, 1, 4, 'packaging',    13.0, 12.0, 'recycling',   '2026-03-31'),
(1, 5, 1, 1, 'packaging',    23.0, 18.0, 'recycling',   '2026-03-31'),
(1, 5, 1, 5, 'other',        19.0,  1.0, 'landfill',    '2026-03-31'),
(1, 6, 1, 1, 'packaging',    22.0, 17.0, 'recycling',   '2026-03-31'),
(1, 6, 1, 3, 'food_residue', 48.0,  0.0, 'composting',  '2026-03-31');

-- ============================================================
-- TRAINING RECORDS
-- Covers Jan–Apr 2026, multiple stores, all course types
-- user_id=1 (test_business) as created_by; trainee=3 (test_staff) or NULL for company-wide
-- ============================================================

INSERT INTO training_record
  (company_id, store_id, trainee_user_id, course_name, course_type,
   duration_hours, completion_date, score, status, note, created_by)
VALUES
-- January 2026
(1, 1, 3, 'Carbon Footprint Basics',              'carbon_awareness',        2.0, '2026-01-10', 85, 'completed', 'Intro session for new staff', 1),
(1, 2, NULL, 'Waste Sorting & Recycling Workshop','waste_management',        3.0, '2026-01-15', 90, 'completed', 'All-store mandatory session', 1),
(1, 3, NULL, 'Energy Saving in Store Operations', 'energy_efficiency',       2.5, '2026-01-20', 78, 'completed', NULL,                          1),
(1, 4, NULL, 'Green Procurement Principles',      'green_procurement',       2.0, '2026-01-22', 82, 'completed', NULL,                          1),

-- February 2026
(1, 1, 3, 'Scope 1 & 2 Emissions Tracking',      'carbon_awareness',        3.0, '2026-02-05', 88, 'completed', NULL,                          1),
(1, 2, NULL, 'GRI Reporting Framework Overview',  'sustainability_reporting', 4.0, '2026-02-10', 91, 'completed', 'Region-wide workshop',        1),
(1, 3, NULL, 'Packaging Waste Reduction',         'waste_management',        2.0, '2026-02-14', 76, 'completed', NULL,                          1),
(1, 5, NULL, 'LED & Equipment Efficiency',        'energy_efficiency',       1.5, '2026-02-18', 84, 'completed', NULL,                          1),
(1, 6, NULL, 'Sustainable Supplier Evaluation',   'green_procurement',       2.5, '2026-02-25', 80, 'completed', NULL,                          1),

-- March 2026
(1, 1, 3, 'Monthly Carbon Record Entry',          'carbon_awareness',        1.0, '2026-03-03', 92, 'completed', 'Hands-on practice session',   1),
(1, 2, NULL, 'Composting & Food Waste',           'waste_management',        2.0, '2026-03-07', 87, 'completed', NULL,                          1),
(1, 3, NULL, 'ESG Report Writing Workshop',       'sustainability_reporting', 3.5, '2026-03-12', 89, 'completed', 'Cross-region session',        1),
(1, 4, NULL, 'Carbon Neutrality Roadmap',         'carbon_awareness',        2.0, '2026-03-15', 83, 'completed', NULL,                          1),
(1, 5, NULL, 'Energy Audit Fundamentals',         'energy_efficiency',       3.0, '2026-03-20', 77, 'completed', NULL,                          1),
(1, 6, NULL, 'Eco-Certified Supplier Sourcing',   'green_procurement',       2.0, '2026-03-25', 86, 'completed', NULL,                          1),

-- April 2026
(1, 1, 3, 'Q1 Carbon Review & Action Planning',   'carbon_awareness',        2.0, '2026-04-02', 90, 'completed', 'Quarterly review session',    1),
(1, 2, NULL, 'Recycling Rate Improvement Plan',   'waste_management',        1.5, '2026-04-08', 88, 'completed', NULL,                          1),
(1, 3, NULL, 'SDG 12 Alignment Workshop',         'sustainability_reporting', 2.5, '2026-04-10', 94, 'completed', 'SDG target setting session',  1),
(1, 4, NULL, 'Smart Thermostat & HVAC Basics',    'energy_efficiency',       2.0, '2026-04-15', 81, 'completed', NULL,                          1),
(1, 5, NULL, 'Low-Carbon Procurement Guide',      'green_procurement',       1.5, '2026-04-18', 85, 'completed', NULL,                          1),
(1, 6, NULL, 'Carbon Awareness Refresher',        'carbon_awareness',        1.0, '2026-04-20', 79, 'in_progress', 'Second half pending',       1);
