import sqlite3
from pathlib import Path

import pandas as pd


DB_PATH = Path(__file__).parent / "data" / "books.db"


def run_query(connection, query, description):
    """Run a SQL query and display the result."""

    print(f"\n{'=' * 70}")
    print(description)
    print("=" * 70)

    print(query)

    result = pd.read_sql(query, connection)

    print("\nOutput:")
    print(result.to_string(index=False))

    return result


def main():

    connection = sqlite3.connect(DB_PATH)

    # ---------------------------------------------------------
    # Query 1: SELECT + WHERE
    # ---------------------------------------------------------
    query_1 = """
        SELECT title, price_gbp, rating
        FROM books
        WHERE rating >= 4
        ORDER BY rating DESC, title
    """

    run_query(
        connection,
        query_1,
        "Query 1 - Books with rating >= 4",
    )

    # ---------------------------------------------------------
    # Query 2: ORDER BY + LIMIT
    # ---------------------------------------------------------
    query_2 = """
        SELECT title, price_gbp
        FROM books
        ORDER BY price_gbp DESC
        LIMIT 10
    """

    run_query(
        connection,
        query_2,
        "Query 2 - 10 most expensive books",
    )

    # ---------------------------------------------------------
    # Query 3: DISTINCT
    # ---------------------------------------------------------
    query_3 = """
        SELECT DISTINCT category_name AS category
        FROM categories
        ORDER BY category_name
    """

    run_query(
        connection,
        query_3,
        "Query 3 - Distinct categories",
    )

    # ---------------------------------------------------------
    # Query 4: BETWEEN
    # ---------------------------------------------------------
    query_4 = """
        SELECT title, price_gbp, rating
        FROM books
        WHERE price_gbp BETWEEN 20 AND 40
        ORDER BY price_gbp
    """

    run_query(
        connection,
        query_4,
        "Query 4 - Books priced between £20 and £40",
    )

    # ---------------------------------------------------------
    # Query 5: IN
    # ---------------------------------------------------------
    query_5 = """
        SELECT title, rating
        FROM books
        WHERE rating IN (4, 5)
        ORDER BY rating DESC, title
    """

    run_query(
        connection,
        query_5,
        "Query 5 - Books with 4 or 5 star ratings",
    )

    # ---------------------------------------------------------
    # Query 6: JOIN
    # ---------------------------------------------------------
    query_6 = """
        SELECT
            b.title,
            b.price_gbp,
            b.rating,
            c.category_name
        FROM books AS b
        JOIN categories AS c
            ON b.category_id = c.category_id
        ORDER BY b.title
        LIMIT 10
    """

    run_query(
        connection,
        query_6,
        "Query 6 - Books joined with categories",
    )

    # ---------------------------------------------------------
    # pd.read_sql requirement - Result 1
    # ---------------------------------------------------------
    high_rated = pd.read_sql(
        """
        SELECT title, rating
        FROM books
        WHERE rating = 5
        ORDER BY title
        """,
        connection,
    )

    print("\n" + "=" * 70)
    print("pd.read_sql Result 1 - 5-star books")
    print("=" * 70)

    print(
        high_rated.head(10).to_string(index=False)
    )

    # ---------------------------------------------------------
    # pd.read_sql requirement - Result 2
    # ---------------------------------------------------------
    books_with_categories = pd.read_sql(
        """
        SELECT
            book_id,
            title,
            price_gbp,
            rating,
            category_id
        FROM books
        """,
        connection,
    )

    categories = pd.read_sql(
        """
        SELECT
            category_id,
            category_name
        FROM categories
        """,
        connection,
    )

    print("\n" + "=" * 70)
    print("pd.read_sql Result 2 - Books and categories loaded")
    print("=" * 70)

    print("Books rows:", len(books_with_categories))
    print("Category rows:", len(categories))

    # ---------------------------------------------------------
    # Reproduce SQL JOIN using pandas merge
    # ---------------------------------------------------------
    merged_result = books_with_categories.merge(
        categories,
        on="category_id",
        how="inner",
    )

    print("\n" + "=" * 70)
    print("Pandas merge equivalent of SQL JOIN")
    print("=" * 70)

    print(
        merged_result[
            [
                "title",
                "price_gbp",
                "rating",
                "category_name",
            ]
        ]
        .sort_values("title")
        .head(10)
        .to_string(index=False)
    )

    connection.close()


if __name__ == "__main__":
    main()