"""
database/init_users.py
Run this script ONCE after applying schema.sql to set correct password hashes.
Usage: python database/init_users.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from werkzeug.security import generate_password_hash
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host':     os.getenv('MYSQL_HOST', '127.0.0.1'),
    'port':     int(os.getenv('MYSQL_PORT', 3306)),
    'user':     os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DB', 'sustainability_platform'),
    'charset':  'utf8mb4',
}

ACCOUNTS = [
    {'username': 'test_business', 'password': '123456'},
    {'username': 'test_region',   'password': '123456'},
    {'username': 'test_staff',    'password': '123456'},
    {'username': 'test_admin',    'password': '123456'},
]

def main():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            for acc in ACCOUNTS:
                hashed = generate_password_hash(acc['password'])
                cur.execute(
                    'UPDATE `user` SET password = %s WHERE username = %s',
                    (hashed, acc['username'])
                )
                print(f"  [OK] {acc['username']} → hash updated")
        conn.commit()
        print("\nAll passwords set. You can now log in with password: 123456")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
