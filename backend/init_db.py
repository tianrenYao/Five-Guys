"""
Database initialization script.
Run this after executing schema.sql to set up proper password hashes for test accounts.

Usage:
    python3 backend/init_db.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pymysql
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


def get_connection():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DB', 'sustainability_platform'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def init_test_accounts(conn):
    """Update test accounts with proper password hashes."""
    password_hash = generate_password_hash('123456')

    with conn.cursor() as cursor:
        # Check if test accounts exist
        cursor.execute("SELECT id, username FROM `user` WHERE username IN ('test_business', 'test_staff')")
        existing = cursor.fetchall()

        if existing:
            # Update password hashes
            for user in existing:
                cursor.execute(
                    "UPDATE `user` SET password = %s WHERE id = %s",
                    (password_hash, user['id'])
                )
                print(f"  Updated password hash for: {user['username']}")
        else:
            # Ensure default company exists
            cursor.execute("SELECT id FROM company WHERE id = 1")
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO company (id, name, industry, country) "
                    "VALUES (1, 'Demo Corporation', 'Technology', 'Ireland')"
                )
                print("  Created default company: Demo Corporation")

            # Insert test accounts
            accounts = [
                (1, 'test_business', password_hash, 'Business Admin', 'business'),
                (1, 'test_staff', password_hash, 'Staff User', 'staff'),
            ]
            for company_id, username, pwd, display_name, role in accounts:
                cursor.execute(
                    "INSERT INTO `user` (company_id, username, password, display_name, role) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (company_id, username, pwd, display_name, role)
                )
                print(f"  Created test account: {username} ({role})")

    conn.commit()


def init_sample_data(conn):
    """Insert sample data for demonstration purposes."""
    with conn.cursor() as cursor:
        # Check if sample data already exists
        cursor.execute("SELECT COUNT(*) AS cnt FROM carbon_record")
        if cursor.fetchone()['cnt'] > 0:
            print("  Sample data already exists, skipping.")
            return

        # Get user IDs
        cursor.execute("SELECT id FROM `user` WHERE username = 'test_business'")
        user = cursor.fetchone()
        if not user:
            print("  No test user found, skipping sample data.")
            return
        user_id = user['id']

        # Sample carbon records (last 6 months)
        carbon_samples = [
            # (factor_id, category, activity_value, total_carbon, record_date)
            (1, 'electricity', 1200.00, 355.20, '2026-01-15'),
            (1, 'electricity', 1050.00, 310.80, '2026-02-15'),
            (1, 'electricity', 980.00, 290.08, '2026-03-15'),
            (3, 'transport', 500.00, 85.00, '2026-01-20'),
            (3, 'transport', 620.00, 105.40, '2026-02-20'),
            (5, 'transport', 300.00, 26.70, '2026-03-10'),
            (10, 'commute', 800.00, 136.00, '2026-01-31'),
            (10, 'commute', 750.00, 127.50, '2026-02-28'),
            (10, 'commute', 700.00, 119.00, '2026-03-15'),
        ]
        for factor_id, category, activity, carbon, date in carbon_samples:
            cursor.execute(
                "INSERT INTO carbon_record (company_id, user_id, factor_id, category, "
                "activity_value, total_carbon, record_date) VALUES (1, %s, %s, %s, %s, %s, %s)",
                (user_id, factor_id, category, activity, carbon, date)
            )
        print(f"  Inserted {len(carbon_samples)} sample carbon records")

        # Sample waste records
        waste_samples = [
            # (category_id, weight_kg, record_date)
            (1, 120.5, '2026-01-15'),
            (2, 45.0, '2026-01-15'),
            (4, 30.0, '2026-01-15'),
            (1, 110.0, '2026-02-15'),
            (2, 55.0, '2026-02-15'),
            (3, 5.0, '2026-02-15'),
            (1, 95.0, '2026-03-15'),
            (2, 60.0, '2026-03-15'),
            (5, 8.0, '2026-03-15'),
        ]
        for cat_id, weight, date in waste_samples:
            cursor.execute(
                "INSERT INTO waste_record (company_id, user_id, category_id, weight_kg, record_date) "
                "VALUES (1, %s, %s, %s, %s)",
                (user_id, cat_id, weight, date)
            )
        print(f"  Inserted {len(waste_samples)} sample waste records")

    conn.commit()


def main():
    print("=" * 50)
    print("Sustainability Platform - Database Initialization")
    print("=" * 50)

    try:
        conn = get_connection()
        print(f"\nConnected to MySQL: {os.getenv('MYSQL_HOST', 'localhost')}:{os.getenv('MYSQL_PORT', 3306)}")
        print(f"Database: {os.getenv('MYSQL_DB', 'sustainability_platform')}\n")
    except Exception as e:
        print(f"\nERROR: Could not connect to MySQL: {e}")
        print("\nPlease ensure:")
        print("  1. MySQL is running")
        print("  2. You have run: mysql -u root -p < database/schema.sql")
        print("  3. Your .env file has correct credentials")
        sys.exit(1)

    print("[1/2] Initializing test accounts...")
    init_test_accounts(conn)

    print("[2/2] Inserting sample data...")
    init_sample_data(conn)

    conn.close()
    port = os.getenv('FLASK_PORT', '5001')
    print("\nDone! You can now run: python3 backend/app.py")
    print(f"Then visit: http://localhost:{port}")
    print("Login with: test_business / 123456")


if __name__ == '__main__':
    main()
