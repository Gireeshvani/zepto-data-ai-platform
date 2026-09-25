import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


BASE_URL = "https://books.toscrape.com/"


def get_soup(url):
    """Download a page and return BeautifulSoup."""
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def extract_book_details(soup, category):
    """Extract book details from an already downloaded book page."""

    title = soup.find("h1").get_text(strip=True)

    price_element = soup.select_one(".price_color")
    price = price_element.get_text(strip=True) if price_element else None

    rating = None
    rating_element = soup.select_one(".star-rating")

    if rating_element:
        rating_classes = rating_element.get("class", [])
        rating_words = {"One", "Two", "Three", "Four", "Five"}

        for word in rating_classes:
            if word in rating_words:
                rating = word
                break

    availability_element = soup.select_one(".availability")
    availability = (
        availability_element.get_text(" ", strip=True)
        if availability_element
        else None
    )

    return {
        "title": title,
        "price_gbp": price,
        "star_rating": rating,
        "availability": availability,
        "category": category,
    }


def scrape_books(max_pages=5):
    """Scrape books from the first five catalogue pages."""

    books = []

    for page_number in range(1, max_pages + 1):

        if page_number == 1:
            url = BASE_URL
        else:
            url = urljoin(
                BASE_URL,
                f"catalogue/page-{page_number}.html"
            )

        print(f"Scraping page {page_number}: {url}")

        soup = get_soup(url)

        book_links = soup.select("article.product_pod h3 a")

        for link in book_links:

            book_url = urljoin(url, link.get("href"))
            book_soup = get_soup(book_url)

            breadcrumb = book_soup.select("ul.breadcrumb li")

            category = (
                breadcrumb[2].get_text(strip=True)
                if len(breadcrumb) >= 3
                else "Unknown"
            )

            book_data = extract_book_details(
                book_soup,
                category
            )

            books.append(book_data)

    return books


if __name__ == "__main__":

    books = scrape_books(max_pages=5)

    print(f"\nTotal books scraped: {len(books)}")

    for book in books[:5]:
        print(book)