import sqlite3
from pathlib import Path

import pandas as pd


DB_PATH = Path(__file__).parent / "data" / "books.db"


def create_database():
    """Create a fresh normalized SQLite database."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Remove an existing database so pipeline runs are reproducible.
    if DB_PATH.exists():
        DB_PATH.unlink()

    connection = sqlite3.connect(DB_PATH)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price_gbp REAL NOT NULL,
            price_inr REAL NOT NULL,
            rating INTEGER NOT NULL,
            in_stock INTEGER NOT NULL,
            availability TEXT,
            category_id INTEGER NOT NULL,
            FOREIGN KEY (category_id)
                REFERENCES categories(category_id)
        )
    """)

    connection.commit()
    connection.close()


def insert_data(df):
    """Insert cleaned data into normalized SQLite tables."""

    connection = sqlite3.connect(DB_PATH)

    # Insert unique categories.
    categories = df[["category"]].drop_duplicates()

    connection.executemany(
        """
        INSERT INTO categories (category_name)
        VALUES (?)
        """,
        [(category,) for category in categories["category"]],
    )

    # Read category IDs using pandas.
    category_map = pd.read_sql(
        """
        SELECT category_id, category_name
        FROM categories
        """,
        connection,
    )

    # Add category_id to books.
    df = df.merge(
        category_map,
        left_on="category",
        right_on="category_name",
        how="left",
    )

    records = df[
        [
            "title",
            "price_gbp",
            "price_inr",
            "rating",
            "in_stock",
            "availability",
            "category_id",
        ]
    ].itertuples(index=False, name=None)

    connection.executemany(
        """
        INSERT INTO books (
            title,
            price_gbp,
            price_inr,
            rating,
            in_stock,
            availability,
            category_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )

    connection.commit()
    connection.close()