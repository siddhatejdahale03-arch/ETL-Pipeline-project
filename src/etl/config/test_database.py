from sqlalchemy import text

from etl.config.database import engine


def test_connection():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database()")
        )

        database_name = result.scalar()

        print(f"Connected to database: {database_name}")


if __name__ == "__main__":
    test_connection()
