from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def create_database_engine(connection_string: str) -> Engine:
    """
    Create a SQLAlchemy engine for SQL Server.
    """

    return create_engine(
        connection_string,
        pool_pre_ping=True,
        future=True,
    )


def test_connection(engine: Engine):
    """
    Test that the database connection works.
    """

    with engine.connect() as connection:
        connection.exec_driver_sql("SELECT 1")