"""
Insert demo waste and training records for documentation screenshots.

Usage:
    python3 database/seed_demo_data.py

Reads DB credentials from the project root .env file automatically.
Safe to run multiple times (skips duplicates).
"""
import os, sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

try:
    import pymysql
except ImportError:
    print('❌ PyMySQL not installed. Run: pip3 install PyMySQL')
    sys.exit(1)

conn = pymysql.connect(
    host=os.getenv('MYSQL_HOST', 'localhost'),
    port=int(os.getenv('MYSQL_PORT', 3306)),
    user=os.getenv('MYSQL_USER', 'root'),
    password=os.getenv('MYSQL_PASSWORD', ''),
    database=os.getenv('MYSQL_DB', 'sustainability_platform'),
    charset='utf8mb4'
)
cur = conn.cursor()
print(f'✅ Connected to MySQL — {os.getenv("MYSQL_DB","sustainability_platform")}\n')


def run(sql, params=None, label=''):
    try:
        cur.execute(sql, params)
        conn.commit()
        if label:
            print(f'  ✅ {label}')
    except pymysql.err.IntegrityError as e:
        if e.args[0] == 1062:
            print(f'  ⏩ skip (duplicate): {label}')
        else:
            print(f'  ⚠️  {label}: {e}')
    except Exception as e:
        print(f'  ❌ {label}: {e}')


# ── Waste records: Feb / Mar 2026 historical data ──────────────────────────
# category_id: 1=Paper Cups, 2=Plastic, 3=Coffee Grounds, 4=Cardboard, 5=General, 6=E-Waste
print('=== Waste records (Feb 2026) ===')
waste_feb = [
    (1, 1, 1, 1, 'packaging',    22.0, 17.0, 'recycling',  '2026-02-28'),
    (1, 1, 1, 3, 'food_residue', 45.0,  0.0, 'composting', '2026-02-28'),
    (1, 1, 1, 4, 'packaging',    14.0, 13.0, 'recycling',  '2026-02-28'),
    (1, 1, 1, 5, 'other',        18.0,  0.0, 'landfill',   '2026-02-28'),
    (1, 2, 1, 1, 'packaging',    20.0, 15.0, 'recycling',  '2026-02-28'),
    (1, 2, 1, 3, 'food_residue', 40.0,  0.0, 'composting', '2026-02-28'),
    (1, 2, 1, 4, 'packaging',    12.0, 11.0, 'recycling',  '2026-02-28'),
    (1, 3, 1, 1, 'packaging',    25.0, 19.0, 'recycling',  '2026-02-28'),
    (1, 3, 1, 3, 'food_residue', 50.0,  0.0, 'composting', '2026-02-28'),
    (1, 4, 1, 1, 'packaging',    18.0, 14.0, 'recycling',  '2026-02-28'),
    (1, 4, 1, 5, 'other',        22.0,  2.0, 'landfill',   '2026-02-28'),
    (1, 5, 1, 4, 'packaging',    16.0, 15.0, 'recycling',  '2026-02-28'),
    (1, 6, 1, 1, 'packaging',    21.0, 16.0, 'recycling',  '2026-02-28'),
    (1, 6, 1, 3, 'food_residue', 48.0,  0.0, 'composting', '2026-02-28'),
]
for w in waste_feb:
    run('INSERT INTO waste_record (company_id,store_id,user_id,category_id,source_type,'
        'weight_kg,recycled_kg,disposal_method,record_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        w, label=f'waste Feb store={w[1]} cat={w[3]}')

print('\n=== Waste records (Mar 2026) ===')
waste_mar = [
    (1, 1, 1, 1, 'packaging',    24.0, 18.0, 'recycling',  '2026-03-31'),
    (1, 1, 1, 3, 'food_residue', 52.0,  0.0, 'composting', '2026-03-31'),
    (1, 1, 1, 4, 'packaging',    15.0, 14.0, 'recycling',  '2026-03-31'),
    (1, 1, 1, 5, 'other',        20.0,  2.0, 'landfill',   '2026-03-31'),
    (1, 2, 1, 1, 'packaging',    22.0, 17.0, 'recycling',  '2026-03-31'),
    (1, 2, 1, 3, 'food_residue', 44.0,  0.0, 'composting', '2026-03-31'),
    (1, 3, 1, 1, 'packaging',    26.0, 20.0, 'recycling',  '2026-03-31'),
    (1, 3, 1, 3, 'food_residue', 55.0,  0.0, 'composting', '2026-03-31'),
    (1, 4, 1, 1, 'packaging',    19.0, 15.0, 'recycling',  '2026-03-31'),
    (1, 4, 1, 4, 'packaging',    13.0, 12.0, 'recycling',  '2026-03-31'),
    (1, 5, 1, 1, 'packaging',    23.0, 18.0, 'recycling',  '2026-03-31'),
    (1, 5, 1, 5, 'other',        19.0,  1.0, 'landfill',   '2026-03-31'),
    (1, 6, 1, 1, 'packaging',    22.0, 17.0, 'recycling',  '2026-03-31'),
    (1, 6, 1, 3, 'food_residue', 48.0,  0.0, 'composting', '2026-03-31'),
]
for w in waste_mar:
    run('INSERT INTO waste_record (company_id,store_id,user_id,category_id,source_type,'
        'weight_kg,recycled_kg,disposal_method,record_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        w, label=f'waste Mar store={w[1]} cat={w[3]}')

# ── Training records: Jan–Apr 2026, stores 1-6, only users 1/2/3 ──────────
print('\n=== Training records ===')
training = [
    # (company_id, store_id, trainee_user_id, course_name, course_type, hours, date, score, status, note, created_by)
    (1, 1, 3, 'Carbon Footprint Basics',              'carbon_awareness',        2.0, '2026-01-10', 85, 'completed', None, 1),
    (1, 2, None, 'Waste Sorting & Recycling Workshop','waste_management',        3.0, '2026-01-15', 90, 'completed', 'All-store mandatory', 1),
    (1, 3, None, 'Energy Saving in Store Operations', 'energy_efficiency',       2.5, '2026-01-20', 78, 'completed', None, 1),
    (1, 4, None, 'Green Procurement Principles',      'green_procurement',       2.0, '2026-01-22', 82, 'completed', None, 1),
    (1, 1, 3, 'Scope 1 & 2 Emissions Tracking',       'carbon_awareness',        3.0, '2026-02-05', 88, 'completed', None, 1),
    (1, 2, None, 'GRI Reporting Framework Overview',  'sustainability_reporting', 4.0, '2026-02-10', 91, 'completed', 'Region-wide workshop', 1),
    (1, 3, None, 'Packaging Waste Reduction',         'waste_management',        2.0, '2026-02-14', 76, 'completed', None, 1),
    (1, 5, None, 'LED & Equipment Efficiency',        'energy_efficiency',       1.5, '2026-02-18', 84, 'completed', None, 1),
    (1, 6, None, 'Sustainable Supplier Evaluation',   'green_procurement',       2.5, '2026-02-25', 80, 'completed', None, 1),
    (1, 1, 3, 'Monthly Carbon Record Entry',          'carbon_awareness',        1.0, '2026-03-03', 92, 'completed', 'Hands-on session', 1),
    (1, 2, None, 'Composting & Food Waste',           'waste_management',        2.0, '2026-03-07', 87, 'completed', None, 1),
    (1, 3, None, 'ESG Report Writing Workshop',       'sustainability_reporting', 3.5, '2026-03-12', 89, 'completed', 'Cross-region', 1),
    (1, 4, None, 'Carbon Neutrality Roadmap',         'carbon_awareness',        2.0, '2026-03-15', 83, 'completed', None, 1),
    (1, 5, None, 'Energy Audit Fundamentals',         'energy_efficiency',       3.0, '2026-03-20', 77, 'completed', None, 1),
    (1, 6, None, 'Eco-Certified Supplier Sourcing',   'green_procurement',       2.0, '2026-03-25', 86, 'completed', None, 1),
    (1, 1, 3, 'Q1 Carbon Review & Action Planning',   'carbon_awareness',        2.0, '2026-04-02', 90, 'completed', 'Quarterly review', 1),
    (1, 2, None, 'Recycling Rate Improvement Plan',   'waste_management',        1.5, '2026-04-08', 88, 'completed', None, 1),
    (1, 3, None, 'SDG 12 Alignment Workshop',         'sustainability_reporting', 2.5, '2026-04-10', 94, 'completed', 'SDG target setting', 1),
    (1, 4, None, 'Smart Thermostat & HVAC Basics',    'energy_efficiency',       2.0, '2026-04-15', 81, 'completed', None, 1),
    (1, 5, None, 'Low-Carbon Procurement Guide',      'green_procurement',       1.5, '2026-04-18', 85, 'completed', None, 1),
    (1, 6, None, 'Carbon Awareness Refresher',        'carbon_awareness',        1.0, '2026-04-20', 79, 'in_progress', 'Second half pending', 1),
]
for t in training:
    run('INSERT INTO training_record (company_id,store_id,trainee_user_id,course_name,course_type,'
        'duration_hours,completion_date,score,status,note,created_by) '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        t, label=f'{t[3][:40]} ({t[6]})')

conn.close()
print('\n✅ Done! Refresh the Training and Waste pages to see the new data.')
