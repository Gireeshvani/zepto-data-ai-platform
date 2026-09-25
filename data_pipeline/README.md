# Module 1 - Books Data Pipeline

## 1. Objective

This module implements an end-to-end data pipeline using the
[Books to Scrape](https://books.toscrape.com/) website.

The pipeline:

1. Scrapes book information from the website.
2. Cleans and transforms the scraped data.
3. Converts GBP prices to INR using a fixed exchange rate.
4. Stores the cleaned data in a normalized SQLite database.
5. Executes SQL queries for analysis.
6. Loads SQL results using Pandas.
7. Reproduces the SQL JOIN operation using `pandas.merge()`.

---

## 2. Data Source

The data source is:

https://books.toscrape.com/

The pipeline scrapes the first five pages of the website.

Each page contains 20 books, resulting in:

- **100 books scraped**
- **29 unique categories**

The scraper captures the following fields:

- `title`
- `price_gbp`
- `star_rating`
- `availability`
- `category`

---

## 3. Project Files

```text
data_pipeline/
├── scraper.py
├── database.py
├── queries.py
├── run_pipeline.py
├── requirements.txt
├── README.md
└── data/
    └── books.db