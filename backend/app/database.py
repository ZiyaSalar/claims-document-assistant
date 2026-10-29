import os
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()


def get_database_backend() -> str:
    return os.getenv("DB_BACKEND", "memory").strip().lower()


@lru_cache(maxsize=1)
def get_engine():
    if get_database_backend() != "azure":
        raise RuntimeError("Azure SQL is not enabled")

    required = [
        "AZURE_SQL_SERVER",
        "AZURE_SQL_DATABASE",
        "AZURE_SQL_USERNAME",
        "AZURE_SQL_PASSWORD",
    ]
    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise RuntimeError(
            "Missing database configuration: " + ", ".join(missing)
        )

    url = URL.create(
        drivername="mssql+pymssql",
        username=os.environ["AZURE_SQL_USERNAME"],
        password=os.environ["AZURE_SQL_PASSWORD"],
        host=os.environ["AZURE_SQL_SERVER"],
        port=1433,
        database=os.environ["AZURE_SQL_DATABASE"],
    )

    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={
            "login_timeout": 15,
            "timeout": 30,
            "encryption": "require",
        },
    )


def check_database_connection() -> bool:
    with get_engine().connect() as connection:
        return connection.execute(text("SELECT 1")).scalar_one() == 1