from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mysql.connector import Error as MySQLError

from src.config.database_config import database_config, db_connection


def test_database_connection() -> bool:
    try:
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE(), VERSION()")
            database_name, mysql_version = cursor.fetchone()
            cursor.close()

        print("Database connection successful.")
        print(f"Host: {database_config.host}:{database_config.port}")
        print(f"Database: {database_name or database_config.database}")
        print(f"MySQL version: {mysql_version}")
        return True
    except MySQLError as exc:
        print("Database connection failed.")
        print(f"Host: {database_config.host}:{database_config.port}")
        print(f"Database: {database_config.database}")
        print(f"Error: {exc}")
        return False


if __name__ == "__main__":
    raise SystemExit(0 if test_database_connection() else 1)
