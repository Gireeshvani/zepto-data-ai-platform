import pandas as pd

from scraper import scrape_books
from database import create_database, insert_data


EXCHANGE_RATE = 105.50

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def clean_price(value):
    """Convert raw GBP price to float."""

    if pd.isna(value):
        return None

    cleaned = str(value).replace("£", "").replace("Â", "").strip()

    try:
        return float(cleaned)
    except ValueError:
        return None


def clean_rating(value):
    """Convert textual rating into integer 1-5."""

    if pd.isna(value):
        return None

    return RATING_MAP.get(str(value).strip())


def clean_stock(value):
    """Convert availability text into boolean stock status."""

    if pd.isna(value):
        return False

    return "in stock" in str(value).lower()


def clean_data(raw_books):
    """Clean and transform scraped book records."""

    df = pd.DataFrame(raw_books)

    print("\nRaw data shape:", df.shape)

    # Clean price
    df["price_gbp"] = df["price_gbp"].apply(clean_price)

    # Clean rating
    df["rating"] = df["star_rating"].apply(clean_rating)

    # Convert availability to boolean
    df["in_stock"] = df["availability"].apply(clean_stock)

    # Fixed artificial exchange rate required by assignment
    df["price_inr"] = df["price_gbp"] * EXCHANGE_RATE

    # Check numeric parsing failures
    price_failures = df["price_gbp"].isna().sum()
    rating_failures = df["rating"].isna().sum()

    print("Price parsing failures:", price_failures)
    print("Rating parsing failures:", rating_failures)

    # Assignment allows median imputation for numeric parsing failures.
    if price_failures > 0:
        median_price = df["price_gbp"].median()
        df["price_gbp"] = df["price_gbp"].fillna(median_price)
        df["price_inr"] = df["price_gbp"] * EXCHANGE_RATE

    # Rating is required to be an integer from 1-5.
    # If parsing fails, drop those rows.
    if rating_failures > 0:
        df = df.dropna(subset=["rating"])

    df["rating"] = df["rating"].astype(int)
    df["in_stock"] = df["in_stock"].astype(bool)

    return df


def validate_data(df):
    """Validate cleaned dataset against assignment requirements."""

    assert len(df) >= 60, "Dataset must contain at least 60 books."

    assert df["price_gbp"].notna().all()
    assert df["price_inr"].notna().all()

    assert df["rating"].between(1, 5).all()

    assert df["in_stock"].dtype == bool

    assert df["category"].notna().all()

    print("\nValidation successful!")
    print("Rows:", len(df))
    print("Categories:", df["category"].nunique())
    print("Rating range:", df["rating"].min(), "-", df["rating"].max())


def main():

    print("Starting Books-to-Scrape pipeline...\n")

    # 1. Scrape
    raw_books = scrape_books(max_pages=5)

    # 2. Clean
    df = clean_data(raw_books)

    # 3. Validate
    validate_data(df)

    print("\nCleaned data preview:")
    print(
        df[
            [
                "title",
                "price_gbp",
                "price_inr",
                "rating",
                "in_stock",
                "category",
            ]
        ].head()
    )

    # 4. Create database
    create_database()

    # 5. Insert records
    insert_data(df)

    print("\nSQLite database created successfully.")


if __name__ == "__main__":
    main()