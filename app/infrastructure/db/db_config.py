import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

load_dotenv()

DB_USERNAME = os.getenv("POSTGRES_USERNAME", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DATABASE_NAME", "postgres")


def get_async_db_url() -> str:
    ASYNC_DB_URL = (
        f"postgresql+asyncpg://{DB_USERNAME}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    return ASYNC_DB_URL


def get_sync_db_url() -> str:
    SYNC_DB_URl = (
        f"postgresql://{DB_USERNAME}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    return SYNC_DB_URl


def get_system_db_url() -> str:
    SYSTEM_URL = (
        f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:5432/postgres"
    )

    return SYSTEM_URL


engine = create_async_engine(get_async_db_url())
AsyncSession = async_sessionmaker(bind=engine)

system_engine = create_engine(
    get_system_db_url(), isolation_level="AUTOCOMMIT"
)

Base = declarative_base()
