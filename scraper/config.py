"""Scraper Configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

# Amazon Configuration
AMAZON_BASE_URL = os.getenv("AMAZON_BASE_URL", "https://www.amazon.com")

# Scraping Delays (seconds)
SCRAPER_DELAY_MIN = int(os.getenv("SCRAPER_MIN_DELAY", "2"))
SCRAPER_DELAY_MAX = int(os.getenv("SCRAPER_MAX_DELAY", "5"))

# Retry Configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# Scraping Limits
MAX_PRODUCTS_PER_SESSION = int(os.getenv("MAX_PRODUCTS_PER_SESSION", "100"))
MAX_PAGES = int(os.getenv("MAX_PAGES", "5"))

# User Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# CSS Selectors (refined after testing with live Amazon pages - November 2025)
SELECTORS = {
    "product_container": "div.s-result-item[data-asin]:not([data-asin=''])",  # Captures all 33+ products
    "title": "h2 span",
    "price": "span.a-price span.a-offscreen",
    "original_price": "span[data-a-strike='true'] span.a-offscreen",
    "rating": "span.a-icon-alt",  # Contains "X.X out of 5 stars"
    "review_count": "div[data-cy='reviews-block'] span",  # Review count like "(3.9K)"
    "image": "img.s-image",
    "product_link": "a.a-link-normal",  # Direct link element
    "sponsored": "span:has-text('Sponsored')",
}
