from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from threading import Lock
from typing import Iterator
from urllib.parse import unquote, urlparse

from mysql.connector import MySQLConnection
from mysql.connector.pooling import MySQLConnectionPool, PooledMySQLConnection

from src.config.settings import settings


DatabaseConnection = MySQLConnection | PooledMySQLConnection


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    charset: str = "utf8mb4"
    autocommit: bool = False

    @classmethod
    def from_database_url(cls, database_url: str) -> "DatabaseConfig":
        parsed = urlparse(database_url)
        if parsed.scheme not in {"mysql", "mysql+mysqlconnector"}:
            raise RuntimeError("DATABASE_URL must use the mysql+mysqlconnector scheme")

        database = parsed.path.lstrip("/")
        if not all([parsed.hostname, parsed.username, database]):
            raise RuntimeError("DATABASE_URL must include host, username, and database name")

        return cls(
            host=parsed.hostname,
            port=parsed.port or 3306,
            database=database,
            user=unquote(parsed.username),
            password=unquote(parsed.password or ""),
        )

    def as_mysql_connector_kwargs(self) -> dict[str, object]:
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "charset": self.charset,
            "autocommit": self.autocommit,
        }


database_config = DatabaseConfig.from_database_url(settings.database_url)
_pool: MySQLConnectionPool | None = None
_pool_lock = Lock()


def get_connection_pool() -> MySQLConnectionPool:
    global _pool

    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = MySQLConnectionPool(
                    pool_name="pms_mysql_pool",
                    pool_size=settings.db_pool_size,
                    pool_reset_session=True,
                    **database_config.as_mysql_connector_kwargs(),
                )

    return _pool


def get_db_connection() -> DatabaseConnection:
    return get_connection_pool().get_connection()


@contextmanager
def db_connection() -> Iterator[DatabaseConnection]:
    connection = get_db_connection()
    try:
        yield connection
    finally:
        connection.close()
