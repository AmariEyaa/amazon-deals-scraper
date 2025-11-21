"""Simple test script to run the scraper"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.amazon_scraper import AmazonScraper
from loguru import logger

async def test_scraper():
    """Test the Amazon scraper with a small sample"""
    
    logger.info("="*60)
    logger.info("AMAZON SCRAPER TEST")
    logger.info("="*60)
    
    # Create scraper instance (headless=False to see browser)
    async with AmazonScraper(headless=False) as scraper:
        
        # Test 1: Scrape first page only
        logger.info("\nTest: Scraping 1 page of 'laptop' results...")
        products = await scraper.scrape_search_page('laptop', page_num=1)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"RESULTS:")
        logger.info(f"Products found: {len(products)}")
        logger.info(f"{'='*60}\n")
        
        if products:
            # Show first 3 products
            for i, product in enumerate(products[:3], 1):
                logger.info(f"\nProduct {i}:")
                logger.info(f"  Title: {product['title'][:60]}...")
                logger.info(f"  Brand: {product['brand']}")
                logger.info(f"  Price: ${product['current_price']}")
                logger.info(f"  Original Price: ${product['original_price']}")
                logger.info(f"  Discount: {product['discount_percentage']}%")
                logger.info(f"  Rating: {product['rating']} stars")
                logger.info(f"  Reviews: {product['review_count']}")
                logger.info(f"  Sponsored: {product['is_sponsored']}")
            
            # Save results
            scraper.save_to_json(products, 'data/test_results.json')
        else:
            logger.error("No products were scraped. Check selectors!")

if __name__ == "__main__":
    asyncio.run(test_scraper())
