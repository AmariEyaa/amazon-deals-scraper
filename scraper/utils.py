"""Utility functions for scraping"""
import re
import time
import random
from typing import Optional
from loguru import logger


def clean_price(price_text: Optional[str]) -> Optional[float]:
    """Extract numeric price from text like '$1,369.99'"""
    if not price_text:
        return None
    
    try:
        # Remove currency symbols, commas, spaces
        cleaned = re.sub(r'[^\d.]', '', price_text)
        return float(cleaned) if cleaned else None
    except (ValueError, AttributeError):
        return None


def clean_rating(rating_text: Optional[str]) -> Optional[float]:
    """Extract rating from text like '4.5 out of 5 stars'"""
    if not rating_text:
        return None
    
    try:
        match = re.search(r'(\d+\.?\d*)\s*out of', rating_text)
        if match:
            return float(match.group(1))
        return None
    except (ValueError, AttributeError):
        return None


def clean_review_count(review_text: Optional[str]) -> Optional[int]:
    """Extract review count from text like '(117)' or '1,234'"""
    if not review_text:
        return None
    
    try:
        # Remove parentheses and commas
        cleaned = re.sub(r'[(),]', '', review_text)
        return int(cleaned) if cleaned.isdigit() else None
    except (ValueError, AttributeError):
        return None


def calculate_discount(original_price: Optional[float], current_price: Optional[float]) -> Optional[int]:
    """Calculate discount percentage"""
    if not original_price or not current_price or original_price <= current_price:
        return None
    
    try:
        discount = ((original_price - current_price) / original_price) * 100
        return int(round(discount))
    except (ValueError, ZeroDivisionError):
        return None


def extract_product_id(url: Optional[str]) -> Optional[str]:
    """Extract product ID from Amazon URL"""
    if not url:
        return None
    
    try:
        match = re.search(r'/dp/([A-Z0-9]+)', url)
        return match.group(1) if match else None
    except AttributeError:
        return None


def extract_brand(title: Optional[str]) -> Optional[str]:
    """Extract brand from product title (first word/phrase)"""
    if not title:
        return None
    
    # Common brand patterns
    brands = ['HP', 'Lenovo', 'Dell', 'ASUS', 'Acer', 'MSI', 'Samsung', 'Apple', 
              'Microsoft', 'LG', 'Razer', 'Alienware', 'AOC', 'ThinkPad']
    
    for brand in brands:
        if brand.lower() in title.lower():
            return brand
    
    # If no known brand, take first word
    words = title.split()
    return words[0] if words else None


def random_delay(min_seconds: int = 2, max_seconds: int = 5):
    """Add random delay between requests"""
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"Waiting {delay:.2f} seconds...")
    time.sleep(delay)


def is_sponsored(element_text: Optional[str]) -> bool:
    """Check if product is sponsored"""
    if not element_text:
        return False
    return 'sponsored' in element_text.lower()
