"""
Run all pending database migrations.

Usage:
    python3 database/run_migrations.py

Reads DB credentials from the project's .env file automatically.
Safe to run multiple times — all operations are idempotent.
Tested on: macOS, Ubuntu 22.04, Windows (WSL2).
"""
import os
import sys

# Resolve project root regardless of where the script is run from
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Load .env from project root
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

try:
    import pymysql
except ImportError:
    print('❌ PyMySQL not installed. Run: pip3 install PyMySQL')
    sys.exit(1)

# ── Database connection ────────────────────────────────────────────────────────
try:
    conn = pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DB', 'sustainability_platform'),
        charset='utf8mb4'
    )
    cur = conn.cursor()
    print(f'✅ Connected to MySQL [{os.getenv("MYSQL_HOST","localhost")}:{os.getenv("MYSQL_PORT",3306)}]'
          f' — database: {os.getenv("MYSQL_DB","sustainability_platform")}\n')
except Exception as e:
    print(f'❌ Cannot connect to database: {e}')
    print('   Check your .env file: MYSQL_HOST / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DB')
    sys.exit(1)


def run(sql, params=None, label=''):
    """Execute a single SQL statement. Silently skips if resource already exists."""
    try:
        cur.execute(sql, params)
        conn.commit()
        if label:
            print(f'  ✅ {label}')
    except pymysql.err.OperationalError as e:
        code = e.args[0]
        if code in (1060, 1050, 1091):   # duplicate column / table already exists / index
            print(f'  ⏩ already exists — skip: {label}')
        else:
            print(f'  ⚠️  {label}: {e}')
    except pymysql.err.IntegrityError as e:
        code = e.args[0]
        if code == 1062:                  # duplicate entry
            print(f'  ⏩ duplicate entry — skip: {label}')
        else:
            print(f'  ⚠️  {label}: {e}')
    except Exception as e:
        print(f'  ❌ {label}: {e}')


print('=== Migration 1: notify_email ===')
run('ALTER TABLE alert_threshold ADD COLUMN notify_email VARCHAR(500) DEFAULT NULL',
    label='add notify_email to alert_threshold')

print('\n=== Migration 2: supplier table ===')
run('''CREATE TABLE IF NOT EXISTS supplier (
    id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100) DEFAULT NULL,
    country VARCHAR(100) DEFAULT NULL,
    carbon_disclosure TINYINT DEFAULT NULL,
    carbon_target TINYINT DEFAULT NULL,
    carbon_measures TINYINT DEFAULT NULL,
    carbon_certification TINYINT DEFAULT NULL,
    waste_policy TINYINT DEFAULT NULL,
    waste_recycling TINYINT DEFAULT NULL,
    waste_packaging TINYINT DEFAULT NULL,
    waste_tracking TINYINT DEFAULT NULL,
    ethics_labor TINYINT DEFAULT NULL,
    ethics_safety TINYINT DEFAULT NULL,
    ethics_working_conditions TINYINT DEFAULT NULL,
    ethics_governance TINYINT DEFAULT NULL,
    reporting_report TINYINT DEFAULT NULL,
    reporting_completeness TINYINT DEFAULT NULL,
    reporting_frequency TINYINT DEFAULT NULL,
    reporting_verification TINYINT DEFAULT NULL,
    carbon_score TINYINT DEFAULT NULL,
    waste_score TINYINT DEFAULT NULL,
    ethics_score TINYINT DEFAULT NULL,
    reporting_score TINYINT DEFAULT NULL,
    overall_grade ENUM('A','B','C','D','F') DEFAULT NULL,
    notes TEXT DEFAULT NULL,
    audited_by INT DEFAULT NULL,
    audited_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE
) ENGINE=InnoDB''', label='create supplier table')

supplier_scorecard_columns = [
    ('carbon_disclosure', 'ALTER TABLE supplier ADD COLUMN carbon_disclosure TINYINT DEFAULT NULL'),
    ('carbon_target', 'ALTER TABLE supplier ADD COLUMN carbon_target TINYINT DEFAULT NULL'),
    ('carbon_measures', 'ALTER TABLE supplier ADD COLUMN carbon_measures TINYINT DEFAULT NULL'),
    ('carbon_certification', 'ALTER TABLE supplier ADD COLUMN carbon_certification TINYINT DEFAULT NULL'),
    ('waste_policy', 'ALTER TABLE supplier ADD COLUMN waste_policy TINYINT DEFAULT NULL'),
    ('waste_recycling', 'ALTER TABLE supplier ADD COLUMN waste_recycling TINYINT DEFAULT NULL'),
    ('waste_packaging', 'ALTER TABLE supplier ADD COLUMN waste_packaging TINYINT DEFAULT NULL'),
    ('waste_tracking', 'ALTER TABLE supplier ADD COLUMN waste_tracking TINYINT DEFAULT NULL'),
    ('ethics_labor', 'ALTER TABLE supplier ADD COLUMN ethics_labor TINYINT DEFAULT NULL'),
    ('ethics_safety', 'ALTER TABLE supplier ADD COLUMN ethics_safety TINYINT DEFAULT NULL'),
    ('ethics_working_conditions', 'ALTER TABLE supplier ADD COLUMN ethics_working_conditions TINYINT DEFAULT NULL'),
    ('ethics_governance', 'ALTER TABLE supplier ADD COLUMN ethics_governance TINYINT DEFAULT NULL'),
    ('reporting_report', 'ALTER TABLE supplier ADD COLUMN reporting_report TINYINT DEFAULT NULL'),
    ('reporting_completeness', 'ALTER TABLE supplier ADD COLUMN reporting_completeness TINYINT DEFAULT NULL'),
    ('reporting_frequency', 'ALTER TABLE supplier ADD COLUMN reporting_frequency TINYINT DEFAULT NULL'),
    ('reporting_verification', 'ALTER TABLE supplier ADD COLUMN reporting_verification TINYINT DEFAULT NULL'),
]
for column_name, sql in supplier_scorecard_columns:
    run(sql, label=f'add {column_name} to supplier')

print('\n=== Migration 3: esg_policy table ===')
run('''CREATE TABLE IF NOT EXISTS esg_policy (
    id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    category ENUM('environment','social','governance','sdg12','other') NOT NULL DEFAULT 'other',
    content TEXT NOT NULL,
    version VARCHAR(20) DEFAULT '1.0',
    status ENUM('draft','active','archived') NOT NULL DEFAULT 'draft',
    effective_date DATE DEFAULT NULL,
    created_by INT NOT NULL,
    updated_by INT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES `user`(id) ON DELETE CASCADE
) ENGINE=InnoDB''', label='create esg_policy table')

print('\n=== Seed: sample suppliers ===')
suppliers = [
    (1, 'GreenBean Co.', 'Coffee Beans', 'Colombia',
     100, 100, 50, 100, 50, 100, 50, 100, 100, 100, 100, 50, 100, 100, 50, 100,
     83, 73, 90, 80, 'B', 'Rainforest Alliance certified; annual sustainability report published.'),
    (1, 'EcoPack Ltd.', 'Packaging', 'China',
     50, 50, 100, 50, 100, 100, 100, 50, 100, 50, 50, 100, 50, 50, 100, 50,
     68, 83, 75, 65, 'B', 'Uses 80% recycled materials; limited carbon disclosure.'),
    (1, 'SwiftLogistics Inc.', 'Logistics', 'Ireland',
     50, 50, 50, 0, 50, 50, 50, 50, 100, 50, 50, 50, 50, 50, 50, 0,
     43, 50, 63, 45, 'C', 'Fleet electrification plan underway; no formal ESG report yet.'),
    (1, 'PureMilk Farms', 'Dairy', 'Ireland',
     100, 50, 50, 50, 50, 50, 50, 100, 100, 100, 50, 50, 50, 50, 100, 50,
     68, 60, 80, 65, 'B', 'Carbon-neutral milk pilot; moderate waste recovery rate.'),
    (1, 'CleanCup Corp.', 'Disposables', 'Germany',
     100, 100, 100, 50, 100, 100, 100, 50, 100, 100, 50, 100, 100, 100, 100, 50,
     90, 90, 85, 90, 'A', 'Industry leader in compostable cup technology; full GRI reporting.'),
]
for s in suppliers:
    run('INSERT INTO supplier (company_id,name,category,country,carbon_disclosure,carbon_target,'
        'carbon_measures,carbon_certification,waste_policy,waste_recycling,waste_packaging,waste_tracking,'
        'ethics_labor,ethics_safety,ethics_working_conditions,ethics_governance,reporting_report,'
        'reporting_completeness,reporting_frequency,reporting_verification,carbon_score,waste_score,'
        'ethics_score,reporting_score,overall_grade,notes) '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        s, label=f'supplier: {s[1]}')

print('\n=== Seed: sample ESG policies ===')
policies = [
    (1, 'Responsible Consumption & Waste Policy', 'sdg12',
     'Commits the company to SDG 12 targets: reduce single-use plastics, '
     'improve packaging recyclability, achieve 60% waste recovery rate by 2026.\n\n'
     'Key Commitments:\n- Replace all single-use plastic cups by Q4 2025.\n'
     '- Mandate supplier ESG assessments (min grade C).\n'
     '- Publish quarterly waste KPI dashboards.',
     '1.2', 'active', '2025-01-01', 1),
    (1, 'Carbon Reduction Roadmap', 'environment',
     'Reduce absolute carbon emissions by 30% by 2030 (baseline: 2023).\n\n'
     'Actions:\n- Transition store energy to renewables by 2027.\n'
     '- Partner with low-carbon logistics providers.\n'
     '- Implement monthly carbon tracking for all stores.',
     '2.0', 'active', '2025-03-01', 1),
    (1, 'Supplier Code of Conduct', 'governance',
     'All suppliers must meet minimum ESG standards before onboarding.\n\n'
     'Requirements:\n- Carbon disclosure: Scope 1 & 2 emissions report.\n'
     '- Waste: Formal waste management plan.\n'
     '- Social: No child labour, fair wages, safe working conditions.\n'
     '- Reporting: Biannual ESG or sustainability report.',
     '1.0', 'active', '2024-06-01', 1),
]
for p in policies:
    run('INSERT INTO esg_policy (company_id,title,category,content,version,status,effective_date,created_by) '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
        p, label=f'policy: {p[1]}')

print('\n=== Migration 4: training_record table ===')
run('''CREATE TABLE IF NOT EXISTS training_record (
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
) ENGINE=InnoDB COMMENT='Employee sustainability training completion records' ''',
    label='create training_record table')

print('\n=== Seed: sample training records ===')
training_records = [
    (1, 1, 3, 'Carbon Footprint Basics',           'carbon_awareness',          2.0, '2026-01-15', 85, 'completed', None, 1),
    (1, 1, 3, 'Waste Sorting & Recycling',          'waste_management',          1.5, '2026-02-10', 90, 'completed', None, 1),
    (1, 2, 4, 'Energy Efficiency in Stores',         'energy_efficiency',         3.0, '2026-02-20', 78, 'completed', None, 1),
    (1, 2, 4, 'Sustainability Reporting Standards',   'sustainability_reporting',  2.5, '2026-03-05', 82, 'completed', None, 1),
    (1, 1, 3, 'Green Procurement Guidelines',         'green_procurement',         1.0, '2026-03-18', 88, 'completed', None, 1),
    (1, 3, 5, 'Carbon Footprint Basics',              'carbon_awareness',          2.0, '2026-04-01', None, 'in_progress', 'Enrolled in online course', 1),
]
for t in training_records:
    run('INSERT INTO training_record (company_id,store_id,trainee_user_id,course_name,course_type,'
        'duration_hours,completion_date,score,status,note,created_by) '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        t, label=f'training: {t[3]}')

print('\n=== Migration 5: store geocoordinates ===')
run('ALTER TABLE store ADD COLUMN latitude DECIMAL(9,6) DEFAULT NULL',
    label='add latitude to store')
run('ALTER TABLE store ADD COLUMN longitude DECIMAL(9,6) DEFAULT NULL',
    label='add longitude to store')

print('\n=== Seed: store coordinates (Luckin demo stores) ===')
# (store_id, latitude, longitude)  — district-level approximate coordinates
store_coords = [
    (1, 39.921400, 116.443900),  # Chaoyang Store, Beijing
    (2, 39.959000, 116.298000),  # Haidian Store, Beijing
    (3, 23.125200, 113.360400),  # Tianhe Store, Guangzhou
    (4, 22.533300, 113.930500),  # Nanshan Store, Shenzhen
    (5, 31.228000, 121.448000),  # Jingan Store, Shanghai
    (6, 30.258900, 120.130000),  # West Lake Store, Hangzhou
]
for sid, lat, lng in store_coords:
    run('UPDATE store SET latitude = %s, longitude = %s '
        'WHERE id = %s AND (latitude IS NULL OR longitude IS NULL)',
        (lat, lng, sid), label=f'coords for store id={sid}')

print('\n=== Migration 6: expanded multi-region demo dataset ===')

# ── New regions (West + Central) ────────────────────────────────────────────
new_regions = [
    (4, 1, 'West Region',    'Covers Chengdu, Chongqing, Xi\'an stores'),
    (5, 1, 'Central Region', 'Covers Wuhan, Changsha, Zhengzhou stores'),
]
for r in new_regions:
    run('INSERT IGNORE INTO region (id, company_id, name, description) VALUES (%s, %s, %s, %s)',
        r, label=f'region: {r[2]}')

# ── 12 additional demo stores ──────────────────────────────────────────────
# (id, region_id, name, city, lat, lng, opened_date)
new_stores = [
    # North Region
    (7,  1, 'Tianjin Wuqing Store',  'Tianjin',   39.384300, 117.044300, '2023-04-12'),
    (8,  1, 'Qingdao Shibei Store',  'Qingdao',   36.087300, 120.374600, '2023-08-22'),
    # East Region
    (9,  3, 'Nanjing Xinjiekou',     'Nanjing',   32.043200, 118.778300, '2022-12-05'),
    (10, 3, 'Suzhou Industrial Park','Suzhou',    31.323400, 120.683800, '2023-05-18'),
    # South Region
    (11, 2, 'Xiamen Siming Store',   'Xiamen',    24.479900, 118.089500, '2023-02-15'),
    (12, 2, 'Foshan Chancheng',      'Foshan',    23.024900, 113.106500, '2024-01-08'),
    # West Region
    (13, 4, 'Chengdu Jinjiang',      'Chengdu',   30.657000, 104.081300, '2022-11-11'),
    (14, 4, 'Chongqing Yuzhong',     'Chongqing', 29.555200, 106.554200, '2023-03-20'),
    (15, 4, 'Xi\'an Yanta Store',    'Xi\'an',    34.222500, 108.949800, '2023-09-10'),
    # Central Region
    (16, 5, 'Wuhan Wuchang Store',   'Wuhan',     30.554100, 114.314300, '2022-10-01'),
    (17, 5, 'Changsha Furong',       'Changsha',  28.227800, 112.939100, '2023-06-25'),
    (18, 5, 'Zhengzhou Jinshui',     'Zhengzhou', 34.800500, 113.665400, '2023-11-30'),
]
for s in new_stores:
    run('INSERT IGNORE INTO store (id, company_id, region_id, name, city, latitude, longitude, opened_date) '
        'VALUES (%s, 1, %s, %s, %s, %s, %s, %s)',
        s, label=f'store: {s[2]}')

# ── 4 months of carbon records for new stores ──────────────────────────────
# Pattern: electricity (factor_id=1) + natural gas (factor_id=6).
# Each store gets a base level scaled by store id; some are "performers", some "issues".
# Idempotency: ON DUPLICATE KEY would need a unique index; instead we check first.

def _carbon_records_exist(store_id):
    row = query_db_simple(
        'SELECT COUNT(*) AS cnt FROM carbon_record WHERE store_id = %s', (store_id,)
    )
    return row and row[0] > 0


def query_db_simple(sql, params):
    """Lightweight query — returns first row tuple or None."""
    cur.execute(sql, params)
    return cur.fetchone()


# Profiles: (electricity_kwh_base, gas_m3_base, has_transport, recycle_rate_pct)
# Designed to produce a mix of green/amber/red ESG grades for visual variety.
store_profiles = {
    7:  (8800,  370, False, 45),   # Tianjin — normal
    8:  (9200,  390, False, 40),   # Qingdao — normal
    9:  (10500, 440, True,  50),   # Nanjing — good
    10: (11800, 490, True,  55),   # Suzhou — good
    11: (8500,  350, False, 25),   # Xiamen — issue (low recycling)
    12: (9700,  410, False, 38),   # Foshan — normal
    13: (12000, 510, True,  18),   # Chengdu — issue (low recycling)
    14: (10200, 420, False, 42),   # Chongqing — normal
    15: (8800,  370, False, 48),   # Xi'an — normal
    16: (13500, 580, True,  20),   # Wuhan — issue (high carbon + low recycling)
    17: (9500,  400, False, 52),   # Changsha — good
    18: (8000,  340, False, 35),   # Zhengzhou — normal
}

months = [(1, 31, 'Jan'), (2, 28, 'Feb'), (3, 31, 'Mar'), (4, 7, 'Apr')]

print('\n=== Seed: carbon & waste records for new stores ===')
for store_id, (kwh, gas, has_transport, recycle_pct) in store_profiles.items():
    if _carbon_records_exist(store_id):
        print(f'  ⏩ records already exist — skip store id={store_id}')
        continue

    # Carbon records — month-over-month slight variation (+/- 5%)
    for i, (m, d, label) in enumerate(months):
        scale = 1.0 + (i - 1.5) * 0.04           # gentle MoM curve
        if i == 3:  # April partial month → reduce
            scale *= 0.25

        elec_kwh = round(kwh * scale, 0)
        elec_co2 = round(elec_kwh * 0.581, 2)    # grid factor
        gas_m3   = round(gas * scale, 0)
        gas_co2  = round(gas_m3 * 2.02, 2)
        date     = f'2026-{m:02d}-{d:02d}'

        run('INSERT INTO carbon_record (company_id, store_id, user_id, factor_id, '
            'category, activity_value, total_carbon, record_date, note) '
            'VALUES (1, %s, 1, 1, %s, %s, %s, %s, %s)',
            (store_id, 'electricity', elec_kwh, elec_co2, date, f'{label} electricity'),
            label=f'carbon[{store_id}] {label} elec')

        run('INSERT INTO carbon_record (company_id, store_id, user_id, factor_id, '
            'category, activity_value, total_carbon, record_date, note) '
            'VALUES (1, %s, 1, 6, %s, %s, %s, %s, %s)',
            (store_id, 'fuel', gas_m3, gas_co2, date, f'{label} natural gas'),
            label=f'carbon[{store_id}] {label} gas')

        if has_transport:
            t_km = round(700 * scale, 0)
            t_co2 = round(t_km * 0.9, 2)
            run('INSERT INTO carbon_record (company_id, store_id, user_id, factor_id, '
                'category, activity_value, total_carbon, record_date, note) '
                'VALUES (1, %s, 1, 3, %s, %s, %s, %s, %s)',
                (store_id, 'transport', t_km, t_co2, date, f'{label} freight'),
                label=f'carbon[{store_id}] {label} transport')

    # Waste records — for first 3 full months only (Jan-Mar)
    for i, (m, d, label) in enumerate(months[:3]):
        # Weights scale with store size, recycled portion follows recycle_pct
        cup_w = round(22 + i * 1.5, 1)
        cup_r = round(cup_w * recycle_pct / 100, 1)
        food_w = round(55 + i * 2, 1)
        card_w = round(15 + i, 1)
        card_r = round(card_w * recycle_pct / 100, 1)
        gen_w = round(20 + i, 1)
        date = f'2026-{m:02d}-{d:02d}'

        method = 'recycling' if recycle_pct >= 30 else 'landfill'
        recycler = 'GreenCycle Ltd.' if recycle_pct >= 30 else None

        run('INSERT INTO waste_record (company_id, store_id, user_id, category_id, '
            'source_type, weight_kg, recycled_kg, disposal_method, disposal_unit, record_date, note) '
            'VALUES (1, %s, 1, 1, %s, %s, %s, %s, %s, %s, %s)',
            (store_id, 'packaging', cup_w, cup_r, method, recycler, date,
             f'{label} paper cups & lids'),
            label=f'waste[{store_id}] {label} cups')

        run('INSERT INTO waste_record (company_id, store_id, user_id, category_id, '
            'source_type, weight_kg, recycled_kg, disposal_method, disposal_unit, record_date, note) '
            'VALUES (1, %s, 1, 3, %s, %s, %s, %s, %s, %s, %s)',
            (store_id, 'food_residue', food_w, 0.0, 'composting', None, date,
             f'{label} coffee grounds'),
            label=f'waste[{store_id}] {label} food')

        run('INSERT INTO waste_record (company_id, store_id, user_id, category_id, '
            'source_type, weight_kg, recycled_kg, disposal_method, disposal_unit, record_date, note) '
            'VALUES (1, %s, 1, 7, %s, %s, %s, %s, %s, %s, %s)',
            (store_id, 'packaging', card_w, card_r, method, recycler, date,
             f'{label} cardboard'),
            label=f'waste[{store_id}] {label} cardboard')

        run('INSERT INTO waste_record (company_id, store_id, user_id, category_id, '
            'source_type, weight_kg, recycled_kg, disposal_method, disposal_unit, record_date, note) '
            'VALUES (1, %s, 1, 6, %s, %s, %s, %s, %s, %s, %s)',
            (store_id, 'other', gen_w, 0.0, 'landfill', None, date,
             f'{label} general waste'),
            label=f'waste[{store_id}] {label} general')

print('\n=== Migration 7: anomaly_review table ===')
run('''CREATE TABLE IF NOT EXISTS anomaly_review (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    company_id      INT          NOT NULL,
    record_type     ENUM('carbon','waste') NOT NULL,
    record_id       INT          NOT NULL,
    store_id        INT          DEFAULT NULL,
    record_date     DATE         DEFAULT NULL,
    severity        ENUM('high','medium') DEFAULT 'medium',
    direction       ENUM('above','below','rule') DEFAULT 'above',
    value           DECIMAL(14,4) DEFAULT NULL,
    mean_value      DECIMAL(14,4) DEFAULT NULL,
    std_value       DECIMAL(14,4) DEFAULT NULL,
    z_score         DECIMAL(8,3)  DEFAULT NULL,
    risk_category   VARCHAR(64)   DEFAULT NULL,
    ai_insight      TEXT          DEFAULT NULL,
    label           VARCHAR(255)  DEFAULT NULL,
    note            VARCHAR(255)  DEFAULT NULL,
    status          ENUM('open','reviewed','false_positive','resolved')
                    NOT NULL DEFAULT 'open',
    detected_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_by     INT           DEFAULT NULL,
    reviewed_at     DATETIME      DEFAULT NULL,
    review_notes    TEXT          DEFAULT NULL,
    UNIQUE KEY uq_record (record_type, record_id),
    INDEX idx_anomaly_company (company_id),
    INDEX idx_anomaly_status  (status),
    INDEX idx_anomaly_detected (detected_at),
    FOREIGN KEY (company_id)  REFERENCES company(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES `user`(id)  ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='AI Anomaly Detection: detected anomalies + LLM insight + review workflow' ''',
    label='create anomaly_review table')

conn.close()
print('\n✅ All migrations complete!')
