import logging

import typer
from dotenv import load_dotenv
from sqlalchemy import text

from app.infrastructure.db.db_config import DB_NAME, system_engine

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def main(
    operation: str = typer.Option(
        "check", "-op", "--operation", help="выбор операции"
    ),
):
    if operation == "create":
        create_db()
    elif operation == "drop":
        drop_db()
    else:
        check_db()


def create_db() -> None:
    """создает базу данных на основе env"""

    if not check_db():
        with system_engine.connect() as conn:
            stmt = text(f"CREATE DATABASE {DB_NAME}")
            conn.execute(stmt)

        logger.info(f"База данных {DB_NAME} создана успешно")
    else:
        logger.warning("Ошибка создания база существует")


def drop_db() -> None:
    """Удаляет базу данных на основе env"""

    if not check_db():
        logger.warning("Ошибка удаления базы не существует")
        return
    with system_engine.connect() as conn:
        logger.info(DB_NAME)
        stmt = text(f'DROP DATABASE IF EXISTS "{DB_NAME}"')
        conn.execute(stmt)

    logger.info("База данных Удалена успешно")


def check_db() -> bool:
    try:
        with system_engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": DB_NAME},
            )
            db_exists = result.scalar() is not None
    except Exception as e:
        logger.error("Ошибка базы данных")
        logger.error(e)
        return False

    if db_exists:
        logger.info("база существует")
        return True
    else:
        logger.info(f"база {DB_NAME} не существует")
        return False


if __name__ == "__main__":
    typer.run(main)
