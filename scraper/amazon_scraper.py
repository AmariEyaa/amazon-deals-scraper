"""Main Amazon Scraper using Playwright"""
import asyncio
import json
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser
from loguru import logger
from datetime import datetime

from config import (
    AMAZON_BASE_URL,
    SCRAPER_DELAY_MIN,
    SCRAPER_DELAY_MAX,
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    USER_AGENTS,
    SELECTORS,
)
from utils import (
    clean_price,
    clean_rating,
    clean_review_count,
    calculate_discount,
    extract_product_id,
    extract_brand,
    random_delay,
    is_sponsored,
)
from robots_checker import RobotsChecker


class AmazonScraper:
    """Amazon product scraper using Playwright"""
    
    def __init__(self, headless: bool = True, respect_robots: bool = True):
        self.headless = headless
        self.respect_robots = respect_robots
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.products_scraped = 0
        self.robots_checker: Optional[RobotsChecker] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def start(self):
        """Initialize browser and page"""
        logger.info("Starting Playwright browser...")
        
        playwright = await async_playwright().start()
        
        # Launch browser with stealth settings
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        # Create context with random user agent
        import random
        user_agent = random.choice(USER_AGENTS)
        
        context = await self.browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1920, 'height': 1080},
        )
        
        # Hide automation flags
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        self.page = await context.new_page()
        logger.success("Browser started successfully")
        
        # Initialize robots.txt checker
        if self.respect_robots:
            self.robots_checker = RobotsChecker(AMAZON_BASE_URL, user_agent)
            self.robots_checker.load()
            
            # Check if there's a crawl delay in robots.txt
            crawl_delay = self.robots_checker.get_crawl_delay()
            if crawl_delay and crawl_delay > SCRAPER_DELAY_MAX:
                logger.warning(f"⚠️ robots.txt suggests {crawl_delay}s delay (we use {SCRAPER_DELAY_MIN}-{SCRAPER_DELAY_MAX}s)")
        else:
            logger.info("ℹ️ robots.txt checking disabled")
    
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")
    
    async def scrape_search_page(self, keyword: str, page_num: int = 1) -> List[Dict]:
        """Scrape products from a search results page"""
        url = f"{AMAZON_BASE_URL}/s?k={keyword}&page={page_num}"
        logger.info(f"Scraping: {url}")
        
        # Check robots.txt compliance
        if self.robots_checker and not self.robots_checker.can_fetch(url):
            logger.error(f"🚫 Blocked by robots.txt: {url}")
            return []
        
        # Navigate to page with retry logic
        for attempt in range(MAX_RETRIES):
            try:
                await self.page.goto(url, timeout=REQUEST_TIMEOUT * 1000, wait_until='domcontentloaded')
                break
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to load page after {MAX_RETRIES} attempts")
                    return []
        
        # Wait for products to load
        try:
            await self.page.wait_for_selector(SELECTORS['product_container'], timeout=10000)
        except Exception as e:
            logger.error(f"Products not found on page: {e}")
            return []
        
        # Scroll to load all dynamically loaded products
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await self.page.wait_for_timeout(1500)
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await self.page.wait_for_timeout(1500)
        
        # Get all product containers
        product_elements = await self.page.query_selector_all(SELECTORS['product_container'])
        logger.info(f"Found {len(product_elements)} products on page")
        
        products = []
        for idx, element in enumerate(product_elements):
            try:
                product_data = await self._extract_product_data(element, keyword)
                if product_data:
                    products.append(product_data)
                    self.products_scraped += 1
                    logger.success(f"Scraped product {idx + 1}: {product_data.get('title', 'Unknown')[:50]}...")
            except Exception as e:
                logger.error(f"Error extracting product {idx + 1}: {e}")
                continue
        
        # Add delay before next page
        random_delay(SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX)
        
        return products
    
    async def _extract_product_data(self, element, category: str) -> Optional[Dict]:
        """Extract data from a single product element"""
        try:
            # Check if sponsored
            try:
                sponsored_text = await element.inner_text()
                is_sponsored_product = 'Sponsored' in sponsored_text
            except:
                is_sponsored_product = False
            
            # Extract title using h2 span selector
            title_element = await element.query_selector(SELECTORS['title'])
            if not title_element:
                return None
            
            title = await title_element.inner_text()
            if not title:
                return None
            
            # Extract product URL from link element
            link_element = await element.query_selector(SELECTORS['product_link'])
            if not link_element:
                return None
            
            product_url = await link_element.get_attribute('href')
            if not product_url:
                return None
            
            # Make URL absolute
            if not product_url.startswith('http'):
                product_url = f"{AMAZON_BASE_URL}{product_url}"
            
            # Extract product ID from data-asin attribute (more reliable)
            product_id = await element.get_attribute('data-asin')
            if not product_id:
                product_id = extract_product_id(product_url)
            
            # Extract brand
            brand = extract_brand(title)
            
            # Extract price (using offscreen span for accuracy)
            price_element = await element.query_selector(SELECTORS['price'])
            current_price_text = await price_element.inner_text() if price_element else None
            current_price = clean_price(current_price_text)
            
            # Extract original price
            original_price_element = await element.query_selector(SELECTORS['original_price'])
            original_price_text = await original_price_element.inner_text() if original_price_element else None
            original_price = clean_price(original_price_text)
            
            # Calculate discount
            discount_percentage = calculate_discount(original_price, current_price)
            
            # Extract rating from span.a-icon-alt (contains "X.X out of 5 stars")
            rating_element = await element.query_selector(SELECTORS['rating'])
            rating = None
            if rating_element:
                rating_text = await rating_element.inner_text()
                rating = clean_rating(rating_text)
            
            # Extract review count - look for format like "(3.9K)" or "(117)"
            review_count = None
            review_elements = await element.query_selector_all(SELECTORS['review_count'])
            for rev_elem in review_elements:
                try:
                    rev_text = await rev_elem.inner_text()
                    # Look for text in parentheses with numbers
                    if '(' in rev_text and ')' in rev_text:
                        cleaned = clean_review_count(rev_text)
                        if cleaned and cleaned > 0:
                            review_count = cleaned
                            break
                except:
                    continue
            
            # Extract image URL
            image_element = await element.query_selector(SELECTORS['image'])
            image_url = await image_element.get_attribute('src') if image_element else None
            
            # Build product data
            product_data = {
                'product_id': product_id,
                'title': title.strip() if title else None,
                'brand': brand,
                'category': category,
                'current_price': current_price,
                'original_price': original_price,
                'discount_percentage': discount_percentage,
                'rating': rating,
                'review_count': review_count,
                'product_url': product_url,
                'image_url': image_url,
                'availability': None,  # Will be enhanced later
                'is_sponsored': is_sponsored_product,
                'scraped_at': datetime.utcnow().isoformat(),
            }
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error in _extract_product_data: {e}")
            return None
    
    async def scrape_multiple_pages(self, keyword: str, max_pages: int = 5) -> List[Dict]:
        """Scrape multiple pages of search results"""
        all_products = []
        
        for page_num in range(1, max_pages + 1):
            logger.info(f"Scraping page {page_num}/{max_pages}")
            products = await self.scrape_search_page(keyword, page_num)
            
            if not products:
                logger.warning(f"No products found on page {page_num}, stopping...")
                break
            
            all_products.extend(products)
            logger.info(f"Total products scraped so far: {len(all_products)}")
        
        return all_products
    
    def save_to_json(self, products: List[Dict], filename: str = 'amazon_products.json'):
        """Save products to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            logger.success(f"Saved {len(products)} products to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")


async def main():
    """Main function for testing"""
    logger.info("Amazon Scraper Starting...")
    
    async with AmazonScraper(headless=False) as scraper:
        # Test with "laptop" search, scrape 2 pages
        products = await scraper.scrape_multiple_pages('laptop', max_pages=2)
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Scraping Complete!")
        logger.info(f"Total products scraped: {len(products)}")
        logger.info(f"{'='*50}\n")
        
        # Save to file
        scraper.save_to_json(products, 'data/amazon_products.json')
        
        # Display sample
        if products:
            logger.info("Sample product:")
            print(json.dumps(products[0], indent=2))


if __name__ == "__main__":
    asyncio.run(main())
