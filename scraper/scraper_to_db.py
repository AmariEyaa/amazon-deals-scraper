"""
Amazon Scraper to Database Pipeline
Connects scraper → validator → database for automated data collection
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.amazon_scraper import AmazonScraper
from database.validator import validate_product_data, clean_product_data
from database.crud import (
    create_product,
    create_category,
    get_product_by_id,
    get_category_by_name,
    add_price_history,
    update_product,
    create_scraping_session,
    update_scraping_session
)
from database.connection import get_db_session
from database.models import Product


class ScraperDatabasePipeline:
    """Pipeline to scrape Amazon data and store in PostgreSQL"""
    
    def __init__(self, headless: bool = True):
        """
        Initialize pipeline
        
        Args:
            headless: Run browser in headless mode
        """
        self.scraper = AmazonScraper(headless=headless)
        self.session_id: Optional[int] = None
        
        logger.info("Scraper-Database Pipeline initialized")
    
    def start_scraping_session(self, search_query: str) -> int:
        """
        Start a new scraping session in database
        
        Args:
            search_query: The search query being scraped
            
        Returns:
            Session ID
        """
        with get_db_session() as db:
            session_data = {
                'session_id': str(uuid4()),
                'category': search_query,
                'pages_scraped': 0,
                'products_found': 0,
                'products_saved': 0,
                'errors_count': 0,
                'status': 'running',
                'started_at': datetime.utcnow()
            }
            
            session = create_scraping_session(db, session_data)
            self.session_id = session.session_id
            
            logger.info(f"Started scraping session {self.session_id} for: {search_query}")
            return self.session_id
    
    def end_scraping_session(self, status: str = 'completed'):
        """
        End the scraping session
        
        Args:
            status: Final status (completed/failed)
        """
        if not self.session_id:
            return
        
        with get_db_session() as db:
            update_data = {
                'status': status,
                'completed_at': datetime.utcnow()
            }
            update_scraping_session(db, str(self.session_id), update_data)
            logger.info(f"Ended scraping session {self.session_id}: {status}")
    
    def process_category(self, category_name: str) -> int:
        """
        Get or create category in database
        
        Args:
            category_name: Name of the category
            
        Returns:
            Category ID
        """
        with get_db_session() as db:
            # Check if category exists
            category = get_category_by_name(db, category_name)
            
            if not category:
                # Create new category
                category = create_category(db, category_name, f'Products in {category_name} category')
                logger.info(f"Created new category: {category_name}")
            
            return category.id
    
    def save_product_to_db(
        self, 
        product_data: Dict[str, Any], 
        category_id: int
    ) -> Optional[Product]:
        """
        Validate and save product to database
        
        Args:
            product_data: Raw product data from scraper
            category_id: ID of the category
            
        Returns:
            Saved Product object or None if validation failed
        """
        try:
            with get_db_session() as db:
                # Clean and validate data
                cleaned_data = clean_product_data(product_data)
                is_valid, error_message = validate_product_data(cleaned_data)
                
                if not is_valid:
                    logger.warning(f"Validation failed for ASIN {product_data.get('product_id', 'unknown')}: {error_message}")
                    return None
                
                # Add category
                cleaned_data['category_id'] = category_id
                
                # Check if product exists (use product_id as ASIN)
                product_id = cleaned_data.get('product_id')
                existing_product = get_product_by_id(db, product_id)
                
                if existing_product:
                    # Product exists - update price history
                    new_price = cleaned_data.get('current_price')
                    if new_price:
                        # Add price history record
                        price_history_data = {
                            'product_id': product_id,
                            'price': new_price,
                            'discount_percent': cleaned_data.get('discount_percentage', 0.0),
                            'recorded_at': datetime.utcnow()
                        }
                        add_price_history(db, price_history_data)
                        
                        # Update product's current price
                        update_product(db, product_id, {'current_price': new_price})
                        logger.info(f"Updated price for {product_id}: ${new_price}")
                    return existing_product
                else:
                    # Create new product
                    product = create_product(db, cleaned_data)
                    logger.success(f"Saved new product: {product_id} - {cleaned_data['title'][:50]}")
                    return product
                    
        except Exception as e:
            logger.error(f"Error saving product: {e}")
            return None
    
    def scrape_and_store(
        self,
        search_query: str,
        max_pages: int = 3,
        category_name: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Main pipeline: Scrape Amazon and store in database
        
        Args:
            search_query: What to search for on Amazon
            max_pages: Maximum pages to scrape
            category_name: Category name (defaults to search_query)
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'scraped': 0,
            'saved': 0,
            'updated': 0,
            'failed': 0
        }
        
        try:
            # Start session
            self.session_id = self.start_scraping_session(search_query)
            
            # Process category
            if not category_name:
                category_name = search_query.title()
            
            category_id = self.process_category(category_name)
            
            # Scrape products
            logger.info(f"Starting scrape for: {search_query} (max {max_pages} pages)")
            products = self.scraper.scrape_products(search_query, max_pages=max_pages)
            stats['scraped'] = len(products)
            
            logger.info(f"Scraped {len(products)} products, processing...")
            
            # Save to database
            for product_data in products:
                result = self.save_product_to_db(product_data, category_id)
                
                if result:
                    # Check if new or existing
                    if hasattr(result, '_sa_instance_state'):
                        stats['saved'] += 1
                    else:
                        stats['updated'] += 1
                else:
                    stats['failed'] += 1
                
                # Update session stats
                with get_db_session() as db:
                    update_scraping_session(db, str(self.session_id), {
                        'products_found': stats['scraped'],
                        'products_saved': stats['saved'] + stats['updated'],
                        'errors_count': stats['failed']
                    })
            
            # End session
            self.end_scraping_session('completed')
            
            logger.success(f"Pipeline completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            self.end_scraping_session('failed')
            raise
    
    def close(self):
        """Close scraper resources"""
        self.scraper.close()
        logger.info("Pipeline closed")


def main():
    """Example usage"""
    pipeline = ScraperDatabasePipeline(headless=True)
    
    try:
        # Example: Scrape laptops
        stats = pipeline.scrape_and_store(
            search_query="laptop",
            max_pages=2,
            category_name="Laptops"
        )
        
        print("\n" + "="*50)
        print("SCRAPING COMPLETE")
        print("="*50)
        print(f"Products Scraped: {stats['scraped']}")
        print(f"Products Saved: {stats['saved']}")
        print(f"Products Updated: {stats['updated']}")
        print(f"Failed: {stats['failed']}")
        print("="*50 + "\n")
        
    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
