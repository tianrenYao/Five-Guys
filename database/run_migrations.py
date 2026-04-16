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

conn.close()
print('\n✅ All migrations complete!')
