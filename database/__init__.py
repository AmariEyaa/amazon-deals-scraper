"""Database package - Exposes public API"""
from .connection import (
    DatabaseManager,
    db_manager,
    init_database,
    get_db_session
)
from .models import Product, PriceHistory, Category, ScrapingSession, Base
from .crud import (
    # Product operations
    create_product,
    get_product_by_id,
    get_product_by_db_id,
    update_product,
    upsert_product,
    delete_product,
    get_all_products,
    get_products_by_category,
    get_products_by_brand,
    get_best_deals,
    get_top_rated,
    search_products,
    get_products_in_price_range,
    
    # Price history operations
    add_price_history,
    get_price_history,
    
    # Category operations
    create_category,
    get_category_by_name,
    get_all_categories,
    update_category_stats,
    
    # Scraping session operations
    create_scraping_session,
    update_scraping_session,
    get_recent_sessions,
    
    # Bulk operations
    bulk_upsert_products,
    get_product_count,
    get_category_count
)

__all__ = [
    # Connection management
    'DatabaseManager',
    'db_manager',
    'init_database',
    'get_db_session',
    
    # Models
    'Product',
    'PriceHistory',
    'Category',
    'ScrapingSession',
    'Base',
    
    # CRUD operations
    'create_product',
    'get_product_by_id',
    'get_product_by_db_id',
    'update_product',
    'upsert_product',
    'delete_product',
    'get_all_products',
    'get_products_by_category',
    'get_products_by_brand',
    'get_best_deals',
    'get_top_rated',
    'search_products',
    'get_products_in_price_range',
    'add_price_history',
    'get_price_history',
    'create_category',
    'get_category_by_name',
    'get_all_categories',
    'update_category_stats',
    'create_scraping_session',
    'update_scraping_session',
    'get_recent_sessions',
    'bulk_upsert_products',
    'get_product_count',
    'get_category_count',
]
