"""
backfill_recent_data.py — Generate realistic demo data for the recent window.

Promotes the existing Apr partial carbon to full month, fills May + Jun for
all stores, and injects demo flavors (spike / silent / alert / outlier /
reports) so dashboards look alive.

Idempotent: re-running with the same --seed reproduces the same demo flavors
and skips (store, date) pairs that already exist.

Usage:
    python3 database/backfill_recent_data.py                 # defaults
    python3 database/backfill_recent_data.py --dry-run       # preview
    python3 database/backfill_recent_data.py --purge-recent  # wipe range
"""
import argparse
import os
import random
import sys
from datetime import date, datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
import pymysql

# Reuse profile constants from the original generator for consistent feel
from generate_stores import (
    SIZE_PROFILES, SIZE_WEIGHTS, ESG_PROFILES, ESG_WEIGHTS, SEASONAL,
    FACTOR_ELECTRICITY, FACTOR_GAS, FACTOR_TRANSPORT,
    pick_weighted, jitter,
)

HQ_ADMIN_USER_ID = 1


def parse_date(s):
    return datetime.strptime(s, '%Y-%m-%d').date()


def db_connect():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DB', 'sustainability_platform'),
        charset='utf8mb4',
    )


def fix_apr_partial(cur, dry_run):
    """Promote existing Apr partial (× 0.25) carbon records to full month
    by multiplying values × 4. Idempotent via note marker."""
    if dry_run:
        cur.execute(
            'SELECT COUNT(*) FROM carbon_record '
            'WHERE record_date BETWEEN "2026-04-01" AND "2026-04-07" '
            'AND (note IS NULL OR note NOT LIKE "%(full)%")'
        )
        n = cur.fetchone()[0]
        print(f'  [dry-run] would update {n} Apr partial rows')
        return n
    cur.execute(
        'UPDATE carbon_record SET '
        '  activity_value = activity_value * 4, '
        '  total_carbon   = total_carbon   * 4, '
        '  note = CONCAT(IFNULL(note, ""), " (full)") '
        'WHERE record_date BETWEEN "2026-04-01" AND "2026-04-07" '
        'AND (note IS NULL OR note NOT LIKE "%(full)%")'
    )
    return cur.rowcount


def assign_profiles(stores):
    """Deterministic per-store profile assignment (uses caller's RNG state)."""
    profiles = {}
    for sid, _rid, _cid in stores:
        size = pick_weighted(SIZE_WEIGHTS)
        esg  = pick_weighted(ESG_WEIGHTS)
        ep   = ESG_PROFILES[esg]
        rec  = random.uniform(ep['recovery_min'], ep['recovery_max'])
        profiles[sid] = (size, esg, rec, ep['has_transport'])
    return profiles


def months_to_fill(d_from, d_to):
    """Yield (year, month, record_day) tuples within [d_from, d_to].
    Uses day=28 for full months, clamps to d_to for the trailing month.
    Skips April 2026 because Phase 1 (fix_apr_partial) already promotes
    the existing Apr 1-7 partial rows to full-month values; inserting
    Apr 28 records on top would double-count April."""
    y, m = d_from.year, d_from.month
    while (y, m) <= (d_to.year, d_to.month):
        # Skip Apr 2026 — handled by Phase 1
        if (y, m) == (2026, 4):
            y, m = (y, m + 1) if m < 12 else (y + 1, 1)
            continue
        target_day = 28
        if (y, m) == (d_to.year, d_to.month) and d_to.day < 28:
            target_day = d_to.day
        yield (y, m, target_day)
        y, m = (y, m + 1) if m < 12 else (y + 1, 1)


def gen_carbon_waste(cur, conn, stores, profiles, months, spike_stores,
                     silent_stores, existing_carbon, existing_waste, dry_run):
    """Insert carbon + waste records for the given month list. Returns counts."""
    carbon_n = waste_n = skip_n = 0

    for idx, (sid, _rid, _cid) in enumerate(stores):
        if sid in silent_stores:
            continue
        size, _esg, rec_pct, has_transport = profiles[sid]
        sp = SIZE_PROFILES[size]
        is_recycler = rec_pct >= 30

        for (y, m, day) in months:
            rec_date = f'{y}-{m:02d}-{day:02d}'

            seasonal = SEASONAL.get(m, 1.0)
            # Trailing month is partial — scale down proportionally
            if day < 28:
                seasonal *= (day / 28.0)
            spike_mult = 1.6 if (sid in spike_stores and (y, m) == (2026, 5)) else 1.0
            scale = seasonal * spike_mult

            # ── Carbon (skip if exact (sid, date) exists for any category) ──
            if (sid, rec_date) in existing_carbon:
                skip_n += 1
            else:
                rows = []
                kwh = round(jitter(sp['kwh'] * scale), 0)
                rows.append((FACTOR_ELECTRICITY[0], 'electricity', kwh,
                             round(kwh * FACTOR_ELECTRICITY[1], 2),
                             f'{rec_date} electricity'))
                gas = round(jitter(sp['gas'] * scale), 0)
                rows.append((FACTOR_GAS[0], 'fuel', gas,
                             round(gas * FACTOR_GAS[1], 2),
                             f'{rec_date} natural gas'))
                if has_transport:
                    km = round(jitter(700 * seasonal), 0)  # transport ignores spike
                    rows.append((FACTOR_TRANSPORT[0], 'transport', km,
                                 round(km * FACTOR_TRANSPORT[1], 2),
                                 f'{rec_date} delivery'))
                if not dry_run:
                    for fid, cat, av, tc, note in rows:
                        cur.execute(
                            'INSERT INTO carbon_record (company_id, store_id, user_id, '
                            'factor_id, category, activity_value, total_carbon, '
                            'record_date, note) VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s)',
                            (sid, HQ_ADMIN_USER_ID, fid, cat, av, tc, rec_date, note)
                        )
                carbon_n += len(rows)

            # ── Waste ──
            if (sid, rec_date) in existing_waste:
                skip_n += 1
            else:
                cup_w  = round(jitter(sp['cups'] * (day / 28.0 if day < 28 else 1.0)), 1)
                card_w = round(jitter(sp['card'] * (day / 28.0 if day < 28 else 1.0)), 1)
                food_w = round(jitter(sp['food'] * (day / 28.0 if day < 28 else 1.0)), 1)
                gen_w  = round(jitter(sp['gen']  * (day / 28.0 if day < 28 else 1.0)), 1)
                cup_r  = round(cup_w  * rec_pct / 100, 1) if is_recycler else 0.0
                card_r = round(card_w * rec_pct / 100, 1) if is_recycler else 0.0
                method = 'recycling' if is_recycler else 'landfill'
                vendor = 'GreenCycle Ltd.' if is_recycler else None
                rows = [
                    (1, 'packaging',    cup_w,  cup_r,  method,       vendor, f'{rec_date} cups'),
                    (3, 'food_residue', food_w, 0.0,    'composting', None,   f'{rec_date} food'),
                    (7, 'packaging',    card_w, card_r, method,       vendor, f'{rec_date} cardboard'),
                    (6, 'other',        gen_w,  0.0,    'landfill',   None,   f'{rec_date} general'),
                ]
                if not dry_run:
                    for cat_id, src, w, r, mthd, unit, note in rows:
                        cur.execute(
                            'INSERT INTO waste_record (company_id, store_id, user_id, '
                            'category_id, source_type, weight_kg, recycled_kg, '
                            'disposal_method, disposal_unit, record_date, note) '
                            'VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                            (sid, HQ_ADMIN_USER_ID, cat_id, src, w, r, mthd, unit, rec_date, note)
                        )
                waste_n += len(rows)

        # Commit in batches of 50 stores
        if not dry_run and (idx + 1) % 50 == 0:
            conn.commit()
            print(f'  … {idx+1}/{len(stores)} stores committed')

    if not dry_run:
        conn.commit()
    return carbon_n, waste_n, skip_n


def inject_outliers(cur, conn, stores, profiles, silent_stores, count, d_from, d_to, dry_run):
    if count <= 0:
        return 0
    eligible = [s for s in stores if s[0] not in silent_stores]
    if not eligible:
        return 0
    inserted = 0
    for _ in range(count):
        sid, _rid, _cid = random.choice(eligible)
        size = profiles[sid][0]
        sp = SIZE_PROFILES[size]
        # Pick a date within May (most visible window)
        odate = date(2026, 5, random.randint(10, 25))
        if not (d_from <= odate <= d_to):
            continue
        kwh = round(sp['kwh'] * random.uniform(5.0, 6.5), 0)
        if not dry_run:
            cur.execute(
                'INSERT INTO carbon_record (company_id, store_id, user_id, factor_id, '
                'category, activity_value, total_carbon, record_date, note) '
                'VALUES (1, %s, %s, %s, "electricity", %s, %s, %s, "ANOMALY: equipment malfunction")',
                (sid, HQ_ADMIN_USER_ID, FACTOR_ELECTRICITY[0],
                 kwh, round(kwh * FACTOR_ELECTRICITY[1], 2), odate.strftime('%Y-%m-%d'))
            )
        inserted += 1
    if not dry_run:
        conn.commit()
    return inserted


def inject_alerts(cur, conn, alert_stores, dry_run):
    if not alert_stores:
        return 0
    metric_choices = [
        ('waste_recycling_rate', lambda: (round(random.uniform(10, 28), 1), 30.0)),
        ('carbon_spike',         lambda: (round(random.uniform(150, 250), 1), 100.0)),
        ('energy_consumption',   lambda: (round(random.uniform(12000, 18000), 0), 10000.0)),
        ('water_usage',          lambda: (round(random.uniform(800, 1200), 0), 600.0)),
    ]
    inserted = 0
    for sid in alert_stores:
        for _ in range(random.randint(3, 5)):
            mt, val_fn = random.choice(metric_choices)
            cv, tv = val_fn()
            triggered = datetime.now() - timedelta(
                days=random.randint(0, 13),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            if not dry_run:
                cur.execute(
                    'INSERT INTO alert_log (company_id, store_id, threshold_id, metric_type, '
                    'current_value, threshold_value, triggered_at, is_read) '
                    'VALUES (1, %s, NULL, %s, %s, %s, %s, 0)',
                    (sid, mt, cv, tv, triggered)
                )
            inserted += 1
    if not dry_run:
        conn.commit()
    return inserted


def inject_reports(cur, conn, stores, silent_stores, count, dry_run):
    if count <= 0:
        return 0
    eligible = [s[0] for s in stores if s[0] not in silent_stores]
    inserted = 0
    for _ in range(count):
        roll = random.random()
        if roll < 0.6:
            scope, scope_id = 'store', random.choice(eligible)
            label = f'Store #{scope_id}'
        elif roll < 0.85:
            scope, scope_id = 'region', random.randint(1, 5)
            label = f'Region {scope_id}'
        else:
            scope, scope_id = 'company', None
            label = 'Company-wide'

        rmonth = random.choice([4, 5])  # only generated months that have full data
        rfrom = date(2026, rmonth, 1)
        rto   = date(2026, rmonth, 28)
        title = f'{label} Sustainability Report - {rfrom.strftime("%b %Y")}'
        content = (
            f'Auto-generated demo report for {label} covering '
            f'{rfrom} to {rto}. Includes carbon emissions, waste management, '
            f'recycling rates, and SDG 12 alignment metrics.'
        )
        ai_comment = None
        if random.random() < 0.6:
            ai_comment = (
                'AI Analysis: Performance trending positively this period. '
                'Recycling rate is on track to meet 60% target. '
                'Recommendation: continue current practices and expand '
                'partnerships with certified recyclers.'
            )
        created = datetime.now() - timedelta(
            days=random.randint(0, 25), hours=random.randint(0, 23)
        )
        if not dry_run:
            cur.execute(
                'INSERT INTO report (company_id, user_id, title, report_type, '
                'report_scope, scope_id, date_from, date_to, content, ai_comment, '
                'status, created_at) VALUES (1, %s, %s, "monthly", %s, %s, %s, %s, '
                '%s, %s, "generated", %s)',
                (HQ_ADMIN_USER_ID, title, scope, scope_id, rfrom, rto,
                 content, ai_comment, created)
            )
        inserted += 1
    if not dry_run:
        conn.commit()
    return inserted


def fill_apr_waste(cur, conn, stores, profiles, dry_run):
    """Phase 6 — backfill Apr waste so recycling rate can be computed.
    Inserts a single Apr-28 waste batch per store (cups/food/cardboard/general).
    Silent stores are INCLUDED here — they are only silent for May-Jun.
    Idempotent: skips stores that already have any waste row on 2026-04-28.
    """
    apr28 = '2026-04-28'
    cur.execute(
        'SELECT DISTINCT store_id FROM waste_record WHERE record_date = %s',
        (apr28,)
    )
    have = {row[0] for row in cur.fetchall()}
    inserted = 0
    for idx, (sid, _rid, _cid) in enumerate(stores):
        if sid in have:
            continue
        size, _esg, rec_pct, _has_tr = profiles[sid]
        sp = SIZE_PROFILES[size]
        is_recycler = rec_pct >= 30
        seasonal = SEASONAL.get(4, 1.0)
        cup_w  = round(jitter(sp['cups'] * seasonal), 1)
        card_w = round(jitter(sp['card'] * seasonal), 1)
        food_w = round(jitter(sp['food'] * seasonal), 1)
        gen_w  = round(jitter(sp['gen']  * seasonal), 1)
        cup_r  = round(cup_w  * rec_pct / 100, 1) if is_recycler else 0.0
        card_r = round(card_w * rec_pct / 100, 1) if is_recycler else 0.0
        method = 'recycling' if is_recycler else 'landfill'
        vendor = 'GreenCycle Ltd.' if is_recycler else None
        rows = [
            (1, 'packaging',    cup_w,  cup_r,  method,       vendor, f'{apr28} cups'),
            (3, 'food_residue', food_w, 0.0,    'composting', None,   f'{apr28} food'),
            (7, 'packaging',    card_w, card_r, method,       vendor, f'{apr28} cardboard'),
            (6, 'other',        gen_w,  0.0,    'landfill',   None,   f'{apr28} general'),
        ]
        if not dry_run:
            for cat_id, src, w, r, mthd, unit, note in rows:
                cur.execute(
                    'INSERT INTO waste_record (company_id, store_id, user_id, '
                    'category_id, source_type, weight_kg, recycled_kg, '
                    'disposal_method, disposal_unit, record_date, note) '
                    'VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (sid, HQ_ADMIN_USER_ID, cat_id, src, w, r, mthd, unit, apr28, note)
                )
        inserted += len(rows)
        if not dry_run and (idx + 1) % 100 == 0:
            conn.commit()
    if not dry_run:
        conn.commit()
    return inserted


def boost_spike_visibility(cur, conn, spike_stores, profiles, dry_run):
    """Phase 7 — make spike stores clearly higher in May/Jun vs April.
    For each spike store, insert two extra peak electricity records
    (May 15 ± and Jun 5 ±) at ~3× the store's baseline daily kwh.
    Idempotent: keyed on note marker 'BACKFILL_PEAK'.
    """
    if not spike_stores:
        return 0
    cur.execute(
        'SELECT DISTINCT store_id FROM carbon_record '
        'WHERE note LIKE %s AND record_date >= "2026-05-01"',
        ('%BACKFILL_PEAK%',)
    )
    have = {row[0] for row in cur.fetchall()}
    inserted = 0
    for sid in sorted(spike_stores):
        if sid in have:
            continue
        size, _esg, _rec, _ht = profiles[sid]
        sp = SIZE_PROFILES[size]
        peak_dates = [
            date(2026, 5, random.randint(12, 18)),
            date(2026, 6,  random.randint(3, 8)),
        ]
        for pdate in peak_dates:
            kwh = round(sp['kwh'] * random.uniform(2.8, 3.4), 0)
            tc = round(kwh * FACTOR_ELECTRICITY[1], 2)
            if not dry_run:
                cur.execute(
                    'INSERT INTO carbon_record (company_id, store_id, user_id, '
                    'factor_id, category, activity_value, total_carbon, '
                    'record_date, note) VALUES (1, %s, %s, %s, "electricity", '
                    '%s, %s, %s, %s)',
                    (sid, HQ_ADMIN_USER_ID, FACTOR_ELECTRICITY[0],
                     kwh, tc, pdate.strftime('%Y-%m-%d'),
                     f'{pdate} BACKFILL_PEAK HVAC overrun')
                )
            inserted += 1
    if not dry_run:
        conn.commit()
    return inserted


def purge_recent(cur, conn, d_from, d_to):
    print(f'Purging data in [{d_from}..{d_to}]...')
    cur.execute(
        'DELETE FROM carbon_record WHERE record_date BETWEEN %s AND %s AND ('
        '  note LIKE "%%electricity%%" OR note LIKE "%%natural gas%%" '
        '  OR note LIKE "%%delivery%%" OR note LIKE "ANOMALY:%%" '
        '  OR note LIKE "%%BACKFILL_PEAK%%")',
        (d_from, d_to)
    )
    print(f'  carbon_record (in range): {cur.rowcount} rows deleted')
    cur.execute('DELETE FROM waste_record WHERE record_date BETWEEN %s AND %s',
                (d_from, d_to))
    print(f'  waste_record (in range):  {cur.rowcount} rows deleted')
    cur.execute('DELETE FROM waste_record WHERE record_date = "2026-04-28"')
    print(f'  waste_record (Apr-28 gap): {cur.rowcount} rows deleted')
    cur.execute('DELETE FROM alert_log WHERE triggered_at >= %s',
                (datetime.now() - timedelta(days=14),))
    print(f'  alert_log (last 14 days): {cur.rowcount} rows deleted')
    cur.execute('DELETE FROM report WHERE title LIKE "%%Sustainability Report%%"')
    print(f'  report (auto-generated):  {cur.rowcount} rows deleted')
    # Also revert the Apr partial → full marker so fix_apr_partial can re-run
    cur.execute(
        'UPDATE carbon_record SET '
        '  activity_value = activity_value / 4, '
        '  total_carbon   = total_carbon   / 4, '
        '  note = REPLACE(note, " (full)", "") '
        'WHERE record_date BETWEEN "2026-04-01" AND "2026-04-07" '
        'AND note LIKE "%(full)%"'
    )
    print(f'  Apr full → partial revert: {cur.rowcount} rows')
    conn.commit()
    print('\n✅ Purge complete.')


def main():
    parser = argparse.ArgumentParser(
        description='Backfill recent demo data for the Sustainability Platform.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('--from', dest='date_from', default='2026-04-08',
                        help='Start date inclusive (default 2026-04-08)')
    parser.add_argument('--to',   dest='date_to',   default='2026-06-15',
                        help='End date inclusive (default 2026-06-15)')
    parser.add_argument('--inject-spikes',   type=int, default=5)
    parser.add_argument('--inject-silent',   type=int, default=3)
    parser.add_argument('--inject-alerts',   type=int, default=8)
    parser.add_argument('--inject-outliers', type=int, default=5)
    parser.add_argument('--inject-reports',  type=int, default=12)
    parser.add_argument('--seed',            type=int, default=42)
    parser.add_argument('--dry-run',     action='store_true')
    parser.add_argument('--purge-recent', action='store_true',
                        help='Wipe data generated by this script and exit')
    args = parser.parse_args()

    d_from = parse_date(args.date_from)
    d_to   = parse_date(args.date_to)
    if d_from > d_to:
        parser.error('--from must be <= --to')

    random.seed(args.seed)
    print(f'🎲 Seed = {args.seed}')

    conn = db_connect()
    cur  = conn.cursor()

    if args.purge_recent:
        purge_recent(cur, conn, d_from, d_to)
        conn.close()
        return

    # ── Load stores ──
    cur.execute('SELECT id, region_id, company_id FROM store ORDER BY id')
    stores = cur.fetchall()
    if not stores:
        sys.exit('❌ No stores in database. Run init_db.py / generate_stores.py first.')
    store_ids = [s[0] for s in stores]
    print(f'\n📊 Loaded {len(stores)} stores')

    # ── Profile assignment ──
    profiles = assign_profiles(stores)

    # ── Pick demo flavor stores (mutually exclusive) ──
    pool = list(store_ids)
    random.shuffle(pool)
    spike_n  = min(args.inject_spikes,  len(pool))
    silent_n = min(args.inject_silent,  len(pool) - spike_n)
    alert_n  = min(args.inject_alerts,  len(pool) - spike_n - silent_n)
    spike_stores  = set(pool[:spike_n])
    silent_stores = set(pool[spike_n : spike_n + silent_n])
    alert_stores  = set(pool[spike_n + silent_n : spike_n + silent_n + alert_n])

    print(f'\n🎯 Demo flavors:')
    print(f'   Spike  ({len(spike_stores)}): {sorted(spike_stores)[:10]}'
          + (' …' if len(spike_stores) > 10 else ''))
    print(f'   Silent ({len(silent_stores)}): {sorted(silent_stores)}')
    print(f'   Alerts ({len(alert_stores)}): {sorted(alert_stores)}')

    # ── Phase 1: Apr partial → full ──
    print('\n━━━ Phase 1: promote Apr partial-month carbon to full ━━━')
    fixed = fix_apr_partial(cur, args.dry_run)
    if not args.dry_run:
        conn.commit()
    print(f'  ✓ {fixed} Apr rows scaled × 4 (note marked "(full)")')

    # ── Pre-load existing (sid, date) pairs to skip duplicates ──
    cur.execute(
        'SELECT DISTINCT store_id, DATE_FORMAT(record_date, "%%Y-%%m-%%d") '
        'FROM carbon_record WHERE record_date BETWEEN %s AND %s',
        (d_from, d_to)
    )
    existing_carbon = {(sid, dt) for sid, dt in cur.fetchall()}
    cur.execute(
        'SELECT DISTINCT store_id, DATE_FORMAT(record_date, "%%Y-%%m-%%d") '
        'FROM waste_record WHERE record_date BETWEEN %s AND %s',
        (d_from, d_to)
    )
    existing_waste = {(sid, dt) for sid, dt in cur.fetchall()}
    print(f'\n  Existing pairs in window: '
          f'carbon={len(existing_carbon)}, waste={len(existing_waste)}')

    # ── Phase 2: generate carbon + waste for all months ──
    months = list(months_to_fill(d_from, d_to))
    print(f'\n━━━ Phase 2: generate records for months {months} ━━━')
    carbon_n, waste_n, skip_n = gen_carbon_waste(
        cur, conn, stores, profiles, months,
        spike_stores, silent_stores,
        existing_carbon, existing_waste, args.dry_run
    )
    print(f'  ✓ carbon: +{carbon_n}   waste: +{waste_n}   skipped (existing): {skip_n}')

    # ── Phase 3: outliers ──
    print('\n━━━ Phase 3: inject anomaly outliers ━━━')
    out_n = inject_outliers(cur, conn, stores, profiles, silent_stores,
                            args.inject_outliers, d_from, d_to, args.dry_run)
    print(f'  ✓ {out_n} anomaly carbon records inserted (~6× normal)')

    # ── Phase 4: alerts ──
    print('\n━━━ Phase 4: inject unread alerts ━━━')
    al_n = inject_alerts(cur, conn, alert_stores, args.dry_run)
    print(f'  ✓ {al_n} unread alerts inserted across {len(alert_stores)} stores')

    # ── Phase 5: reports ──
    print('\n━━━ Phase 5: insert sample reports ━━━')
    rp_n = inject_reports(cur, conn, stores, silent_stores,
                          args.inject_reports, args.dry_run)
    print(f'  ✓ {rp_n} reports inserted (mix of store/region/company scope)')

    # ── Phase 6: fill Apr waste gap so recycling rate is computable ──
    print('\n━━━ Phase 6: fill Apr waste gap ━━━')
    apr_w = fill_apr_waste(cur, conn, stores, profiles, args.dry_run)
    print(f'  ✓ {apr_w} Apr-28 waste rows inserted')

    # ── Phase 7: boost spike visibility (May/Jun peak loads) ──
    print('\n━━━ Phase 7: boost spike-store visibility ━━━')
    pk_n = boost_spike_visibility(cur, conn, spike_stores, profiles, args.dry_run)
    print(f'  ✓ {pk_n} peak carbon records inserted across {len(spike_stores)} spike stores')

    conn.close()
    print('\n' + '═' * 70)
    if args.dry_run:
        print('  DRY RUN — no changes written.')
    else:
        print(f'  ✅ Backfill complete: {d_from} → {d_to}')
        print(f'     carbon +{carbon_n}  waste +{waste_n}  outliers +{out_n}  '
              f'alerts +{al_n}  reports +{rp_n}  apr_waste +{apr_w}  peaks +{pk_n}')
    print('═' * 70)


if __name__ == '__main__':
    main()
