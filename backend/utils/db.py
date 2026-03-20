import pymysql
from flask import g, current_app


def get_db():
    """Get a database connection for the current request context."""
    if 'db' not in g:
        g.db = pymysql.connect(
            host=current_app.config['MYSQL_HOST'],
            port=current_app.config['MYSQL_PORT'],
            user=current_app.config['MYSQL_USER'],
            password=current_app.config['MYSQL_PASSWORD'],
            database=current_app.config['MYSQL_DB'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    return g.db


def close_db(e=None):
    """Close database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query_db(sql, args=None, one=False):
    """Execute a SELECT query and return results."""
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(sql, args or ())
        results = cursor.fetchone() if one else cursor.fetchall()
    return results


def execute_db(sql, args=None):
    """Execute an INSERT/UPDATE/DELETE query and return affected rows."""
    db = get_db()
    with db.cursor() as cursor:
        affected = cursor.execute(sql, args or ())
        db.commit()
    return affected


def insert_db(sql, args=None):
    """Execute an INSERT query and return the last inserted ID."""
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(sql, args or ())
        db.commit()
        return cursor.lastrowid
