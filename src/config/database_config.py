from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator
from urllib.parse import unquote, urlparse

import mysql.connector
from mysql.connector import MySQLConnection

from src.config.settings import settings


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
        if parsed.scheme not in {"mysql", "mysql+mysqlconnector", "mysql+aiomysql"}:
            raise RuntimeError("DATABASE_URL must use a MySQL connection scheme")

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


def get_db_connection() -> MySQLConnection:
    return mysql.connector.connect(**database_config.as_mysql_connector_kwargs())


@contextmanager
def db_connection() -> Iterator[MySQLConnection]:
    connection = get_db_connection()
    try:
        yield connection
    finally:
        connection.close()
