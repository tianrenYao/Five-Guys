"""
Bulk demo data generator for the Sustainability Platform.

Creates realistic-looking stores, carbon records, waste records, and optional
alert_log entries so the map / dashboard / compliance pages look lively without
hand-crafting data. Designed for rapid demo / testing setup.

Examples:
    # Add 30 random stores with 4 months of data (default)
    python3 database/generate_stores.py --count 30

    # Reproducible output (same seed -> same data every time)
    python3 database/generate_stores.py --count 50 --seed 42

    # Generate 6 months of historical data
    python3 database/generate_stores.py --count 20 --months 6

    # Target a specific year (e.g. for back-fill demos)
    python3 database/generate_stores.py --count 25 --year 2025

    # Preview plan without writing anything
    python3 database/generate_stores.py --count 10 --dry-run

    # Wipe everything this script ever generated (store.id >= --start-id)
    python3 database/generate_stores.py --purge-generated

Generated store IDs start at 100 by default, which preserves the first 20
hand-crafted demo stores (ids 1-18) so their carefully tuned ESG grades and
colour distribution stay untouched.
"""
import argparse
import os
import random
import sys
import time
from collections import Counter
from datetime import date

# ── Project bootstrap ───────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

try:
    import pymysql
except ImportError:
    print('❌ PyMySQL not installed. Run: pip3 install PyMySQL')
    sys.exit(1)


# ── City pool (city_en, region_id, lat, lng, [districts]) ───────────────────
# Region IDs match database/schema.sql + run_migrations.py Migration 6:
#   1 = North    2 = South    3 = East    4 = West    5 = Central
CITY_POOL = [
    # ── North ──
    ('Beijing',      1, 39.904, 116.407, ['Chaoyang','Haidian','Dongcheng','Xicheng','Fengtai','Shijingshan']),
    ('Tianjin',      1, 39.343, 117.361, ['Heping','Nankai','Hedong','Hexi','Hebei','Wuqing']),
    ('Qingdao',      1, 36.067, 120.382, ['Shinan','Shibei','Laoshan','Chengyang']),
    ('Shijiazhuang', 1, 38.042, 114.514, ["Chang'an",'Qiaoxi','Yuhua','Xinhua']),
    ('Jinan',        1, 36.651, 117.120, ['Lixia','Shizhong','Tianqiao','Huaiyin']),
    ('Dalian',       1, 38.914, 121.614, ['Zhongshan','Xigang','Shahekou','Ganjingzi']),
    ('Shenyang',     1, 41.805, 123.431, ['Heping','Shenhe','Tiexi','Dadong']),
    ('Hohhot',       1, 40.842, 111.751, ['Saihan','Huimin','Yuquan']),

    # ── East ──
    ('Shanghai',     3, 31.230, 121.474, ["Jing'an",'Xuhui','Huangpu','Pudong','Yangpu','Putuo']),
    ('Nanjing',      3, 32.060, 118.796, ['Xinjiekou','Gulou','Jianye','Qinhuai']),
    ('Hangzhou',     3, 30.274, 120.155, ['Xihu','Shangcheng','Binjiang','Gongshu']),
    ('Suzhou',       3, 31.299, 120.585, ['Industrial Park','Gusu','Wuzhong','Xiangcheng']),
    ('Ningbo',       3, 29.868, 121.544, ['Haishu','Jiangbei','Beilun','Yinzhou']),
    ('Wuxi',         3, 31.491, 120.312, ['Binhu','Liangxi','Xishan']),
    ('Hefei',        3, 31.820, 117.227, ['Luyang','Shushan','Baohe','Yaohai']),
    ('Fuzhou',       3, 26.074, 119.296, ['Gulou','Taijiang','Cangshan',"Jin'an"]),

    # ── South ──
    ('Guangzhou',    2, 23.129, 113.264, ['Tianhe','Yuexiu','Haizhu','Liwan','Baiyun']),
    ('Shenzhen',     2, 22.543, 114.058, ['Nanshan','Futian','Luohu',"Bao'an",'Longgang']),
    ('Foshan',       2, 23.021, 113.122, ['Chancheng','Nanhai','Shunde']),
    ('Xiamen',       2, 24.480, 118.090, ['Siming','Huli','Jimei','Haicang']),
    ('Dongguan',     2, 23.021, 113.752, ['Nancheng','Dongcheng','Wanjiang']),
    ('Zhuhai',       2, 22.271, 113.577, ['Xiangzhou','Jinwan','Doumen']),
    ('Nanning',      2, 22.817, 108.366, ['Qingxiu','Xingning','Jiangnan']),
    ('Haikou',       2, 20.044, 110.199, ['Xiuying','Longhua','Qiongshan','Meilan']),

    # ── West ──
    ('Chengdu',      4, 30.572, 104.067, ['Jinjiang','Qingyang','Jinniu','Wuhou','Chenghua']),
    ('Chongqing',    4, 29.563, 106.551, ['Yuzhong','Jiangbei','Shapingba','Jiulongpo',"Nan'an"]),
    ("Xi'an",        4, 34.343, 108.940, ['Yanta','Beilin','Lianhu','Xincheng','Weiyang']),
    ('Kunming',      4, 25.038, 102.719, ['Wuhua','Panlong','Xishan','Guandu']),
    ('Guiyang',      4, 26.647, 106.630, ['Nanming','Yunyan','Huaxi','Baiyun']),
    ('Lanzhou',      4, 36.061, 103.834, ['Chengguan','Qilihe','Xigu','Anning']),
    ('Urumqi',       4, 43.826,  87.617, ['Tianshan','Shayibake','Xinshi']),

    # ── Central ──
    ('Wuhan',        5, 30.593, 114.305, ['Wuchang','Hankou','Hanyang','Jianghan',"Jiang'an"]),
    ('Changsha',     5, 28.228, 112.939, ['Furong','Tianxin','Yuelu','Kaifu']),
    ('Zhengzhou',    5, 34.747, 113.625, ['Jinshui','Erqi','Zhongyuan','Huiji']),
    ('Nanchang',     5, 28.682, 115.858, ['Donghu','Xihu','Qingyunpu']),
    ('Taiyuan',      5, 37.870, 112.548, ['Xiaodian','Yingze','Xinghualing']),
]


# ── Store size profiles (monthly baseline) ──────────────────────────────────
SIZE_PROFILES = {
    'small':  {'kwh':  6000, 'gas': 250, 'cups': 15, 'food': 35, 'card': 10, 'gen': 12},
    'medium': {'kwh': 10000, 'gas': 420, 'cups': 25, 'food': 58, 'card': 16, 'gen': 21},
    'large':  {'kwh': 15000, 'gas': 620, 'cups': 40, 'food': 85, 'card': 25, 'gen': 30},
}
SIZE_WEIGHTS = [('small', 30), ('medium', 50), ('large', 20)]


# ── ESG profiles ────────────────────────────────────────────────────────────
ESG_PROFILES = {
    'excellent': {'recovery_min': 60, 'recovery_max': 80, 'has_transport': True,  'alert_prob': 0.05},
    'good':      {'recovery_min': 45, 'recovery_max': 60, 'has_transport': True,  'alert_prob': 0.10},
    'average':   {'recovery_min': 30, 'recovery_max': 45, 'has_transport': False, 'alert_prob': 0.25},
    'poor':      {'recovery_min': 10, 'recovery_max': 30, 'has_transport': False, 'alert_prob': 0.55},
}
ESG_WEIGHTS = [('excellent', 20), ('good', 40), ('average', 25), ('poor', 15)]


# Seasonal electricity scale (cold winter / hot summer = higher usage)
SEASONAL = {1: 1.15, 2: 1.10, 3: 1.05, 4: 1.00, 5: 0.95, 6: 1.05,
            7: 1.20, 8: 1.18, 9: 1.05, 10: 0.98, 11: 1.05, 12: 1.15}

# Emission factors (must match carbon_factor rows in schema.sql)
FACTOR_ELECTRICITY = (1, 0.581)   # (factor_id, kgCO2/kWh)
FACTOR_GAS         = (6, 2.02)    # kgCO2/m3
FACTOR_TRANSPORT   = (3, 0.9)     # kgCO2/km


# ── Utilities ───────────────────────────────────────────────────────────────
def pick_weighted(weighted_pairs):
    labels, weights = zip(*weighted_pairs)
    return random.choices(labels, weights=weights, k=1)[0]


def jitter(base, pct=0.08):
    """Return base * (1 ± pct random)."""
    return base * (1 + random.uniform(-pct, pct))


def gen_coord(lat, lng, spread=0.045):
    return (round(lat + random.uniform(-spread, spread), 6),
            round(lng + random.uniform(-spread, spread), 6))


def gen_opened_date(current_year):
    """Random opening date 2021-01-01 .. (current_year - 1)-12-28."""
    y = random.randint(2021, max(2021, current_year - 1))
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    return date(y, m, d)


HQ_ADMIN_USER_ID = 1  # test_business — stable across all envs


# ── Purge mode ──────────────────────────────────────────────────────────────
def purge_generated(cur, conn, start_id):
    print(f'Purging all generated data (store.id >= {start_id})...')
    for table in ('carbon_record', 'waste_record', 'training_record', 'alert_log'):
        try:
            cur.execute(f'DELETE FROM {table} WHERE store_id >= %s', (start_id,))
            print(f'  ✓ cleared {table}: {cur.rowcount} rows')
        except Exception as e:
            print(f'  ⚠️ {table}: {e}')
    cur.execute('DELETE FROM store WHERE id >= %s', (start_id,))
    print(f'  ✓ cleared store: {cur.rowcount} rows')
    conn.commit()
    print('\n✅ Purge complete.')


# ── Single-store generator ──────────────────────────────────────────────────
def _unique_name(base, used_names):
    """Append #2, #3, ... when the same `City District Store` is drawn twice."""
    if base not in used_names:
        used_names[base] = 1
        return base
    used_names[base] += 1
    return f'{base} #{used_names[base]}'


def generate_one_store(cur, store_id, months, year, used_names, dry_run=False):
    """Insert one store + its carbon/waste/alert records. Returns metrics tuple."""
    city_en, region_id, lat_c, lng_c, districts = random.choice(CITY_POOL)
    district = random.choice(districts)
    name = _unique_name(f'{city_en} {district} Store', used_names)
    lat, lng = gen_coord(lat_c, lng_c)
    opened = gen_opened_date(year)

    size = pick_weighted(SIZE_WEIGHTS)
    esg  = pick_weighted(ESG_WEIGHTS)
    sp = SIZE_PROFILES[size]
    ep = ESG_PROFILES[esg]
    recovery_pct = random.uniform(ep['recovery_min'], ep['recovery_max'])
    user_id = HQ_ADMIN_USER_ID

    if dry_run:
        print(f'  [{store_id:>4}] {name:<38} R{region_id} {size:<6} {esg:<9} rec={recovery_pct:5.1f}%')
        return size, esg, 0, 0, 0

    # ── Store row ──
    cur.execute(
        'INSERT INTO store (id, company_id, region_id, name, city, '
        'latitude, longitude, opened_date) '
        'VALUES (%s, 1, %s, %s, %s, %s, %s, %s)',
        (store_id, region_id, name, city_en, lat, lng, opened)
    )

    carbon_count = waste_count = alert_count = 0

    # ── Carbon records per month ──
    for i, month in enumerate(range(1, months + 1)):
        scale = SEASONAL.get(month, 1.0)
        # Last month is "partial" (ongoing) — scale down
        if month == months:
            scale *= 0.25
            day = 7
        else:
            day = 28
        record_date = f'{year}-{month:02d}-{day:02d}'

        kwh = round(jitter(sp['kwh'] * scale), 0)
        cur.execute(
            'INSERT INTO carbon_record (company_id, store_id, user_id, factor_id, '
            'category, activity_value, total_carbon, record_date, note) '
            'VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s)',
            (store_id, user_id, FACTOR_ELECTRICITY[0], 'electricity',
             kwh, round(kwh * FACTOR_ELECTRICITY[1], 2),
             record_date, f'Month {month} electricity')
        )
        carbon_count += 1

        gas = round(jitter(sp['gas'] * scale), 0)
        cur.execute(
            'INSERT INTO carbon_record (company_id, store_id, user_id, factor_id, '
            'category, activity_value, total_carbon, record_date, note) '
            'VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s)',
            (store_id, user_id, FACTOR_GAS[0], 'fuel',
             gas, round(gas * FACTOR_GAS[1], 2),
             record_date, f'Month {month} natural gas')
        )
        carbon_count += 1

        if ep['has_transport']:
            km = round(jitter(700 * scale), 0)
            cur.execute(
                'INSERT INTO carbon_record (company_id, store_id, user_id, factor_id, '
                'category, activity_value, total_carbon, record_date, note) '
                'VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s)',
                (store_id, user_id, FACTOR_TRANSPORT[0], 'transport',
                 km, round(km * FACTOR_TRANSPORT[1], 2),
                 record_date, f'Month {month} delivery')
            )
            carbon_count += 1

    # ── Waste records for the first (months-1) full months ──
    full_months = max(1, months - 1)
    for month in range(1, full_months + 1):
        record_date = f'{year}-{month:02d}-28'

        cup_w = round(jitter(sp['cups']), 1)
        card_w = round(jitter(sp['card']), 1)
        food_w = round(jitter(sp['food']), 1)
        gen_w = round(jitter(sp['gen']), 1)

        is_recycler = recovery_pct >= 30
        cup_r  = round(cup_w  * recovery_pct / 100, 1) if is_recycler else 0.0
        card_r = round(card_w * recovery_pct / 100, 1) if is_recycler else 0.0
        method  = 'recycling' if is_recycler else 'landfill'
        vendor  = 'GreenCycle Ltd.' if is_recycler else None

        waste_rows = [
            (1, 'packaging', cup_w,  cup_r,  method,      vendor, f'Month {month} cups'),
            (3, 'food_residue', food_w, 0.0, 'composting', None,   f'Month {month} food'),
            (7, 'packaging', card_w, card_r, method,      vendor, f'Month {month} cardboard'),
            (6, 'other',     gen_w,  0.0,   'landfill',    None,   f'Month {month} general'),
        ]
        for cat_id, src, w, r, method_, unit, note in waste_rows:
            cur.execute(
                'INSERT INTO waste_record (company_id, store_id, user_id, category_id, '
                'source_type, weight_kg, recycled_kg, disposal_method, disposal_unit, '
                'record_date, note) '
                'VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (store_id, user_id, cat_id, src, w, r, method_, unit, record_date, note)
            )
            waste_count += 1

    # ── Optional alert (probabilistic) ──
    if random.random() < ep['alert_prob']:
        triggered = f'{year}-{months:02d}-03 09:00:00'
        cur.execute(
            'INSERT INTO alert_log (company_id, store_id, threshold_id, metric_type, '
            'current_value, threshold_value, triggered_at, is_read) '
            'VALUES (1, %s, NULL, %s, %s, %s, %s, 0)',
            (store_id, 'waste_recycling_rate',
             round(recovery_pct, 1), 30.0, triggered)
        )
        alert_count = 1

    return size, esg, carbon_count, waste_count, alert_count


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description='Bulk-generate demo stores with realistic ESG data.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('--count',    type=int, default=30,   help='Number of stores to generate (default 30)')
    parser.add_argument('--seed',     type=int, default=None, help='Random seed for reproducible runs')
    parser.add_argument('--months',   type=int, default=4,    help='Months of historical data (1-12, default 4)')
    parser.add_argument('--year',     type=int, default=2026, help='Year for generated records (default 2026)')
    parser.add_argument('--start-id', type=int, default=100,  help='First store ID to use (default 100)')
    parser.add_argument('--purge-generated', action='store_true',
                        help='Delete all generated rows (id >= --start-id) and exit')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print plan without touching the database')
    args = parser.parse_args()

    if not (1 <= args.months <= 12):
        parser.error('--months must be between 1 and 12')
    if args.count < 0:
        parser.error('--count must be >= 0')

    if args.seed is not None:
        random.seed(args.seed)
        print(f'🎲 Random seed fixed to {args.seed} (reproducible run)')

    # ── Database connection ──
    try:
        conn = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DB', 'sustainability_platform'),
            charset='utf8mb4',
        )
        cur = conn.cursor()
    except Exception as e:
        print(f'❌ Cannot connect to database: {e}')
        sys.exit(1)

    if args.purge_generated:
        purge_generated(cur, conn, args.start_id)
        conn.close()
        return

    # Pick next available ID
    cur.execute('SELECT COALESCE(MAX(id), 0) FROM store')
    max_id = cur.fetchone()[0]
    start_id = max(args.start_id, max_id + 1)

    # Pre-seed name registry with existing store names so we never collide
    cur.execute('SELECT name FROM store')
    used_names = {row[0]: 1 for row in cur.fetchall()}

    print(f'\n🏗  Generating {args.count} stores starting at id={start_id}')
    print(f'    Year={args.year}  Months={args.months}  Dry-run={args.dry_run}')
    print(f'    Existing stores in DB: {len(used_names)}')
    print('-' * 78)

    size_counts = Counter()
    esg_counts  = Counter()
    total_carbon = total_waste = total_alerts = 0
    t0 = time.time()

    for i in range(args.count):
        sid = start_id + i
        size, esg, c, w, a = generate_one_store(
            cur, sid, args.months, args.year, used_names, args.dry_run
        )
        size_counts[size] += 1
        esg_counts[esg]   += 1
        total_carbon += c
        total_waste  += w
        total_alerts += a

        # Commit in batches of 50 to keep transactions small
        if not args.dry_run and (i + 1) % 50 == 0:
            conn.commit()
            print(f'  … {i+1}/{args.count} committed')

    if not args.dry_run:
        conn.commit()

    conn.close()

    elapsed = time.time() - t0
    print('-' * 78)
    if args.dry_run:
        print(f'\n🔍 Dry-run complete. No changes written.')
    else:
        print(f'\n✅ Generated {args.count} stores in {elapsed:.1f}s.')
        print(f'   Inserted : {total_carbon} carbon records | {total_waste} waste records '
              f'| {total_alerts} alerts')
    print(f'   Size     : {dict(size_counts)}')
    print(f'   ESG      : {dict(esg_counts)}')
    print()
    print('Tip: run with "--purge-generated" to remove them later.')


if __name__ == '__main__':
    main()
