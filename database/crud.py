"""CRUD operations for database"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime
from loguru import logger

from .models import Product, PriceHistory, Category, ScrapingSession


# ============================================================================
# PRODUCT OPERATIONS
# ============================================================================

def create_product(session: Session, product_data: Dict) -> Product:
    """Create a new product"""
    product = Product(**product_data)
    session.add(product)
    session.flush()
    return product


def get_product_by_id(session: Session, product_id: str) -> Optional[Product]:
    """Get product by Amazon ASIN"""
    return session.query(Product).filter(Product.product_id == product_id).first()


def get_product_by_db_id(session: Session, id: int) -> Optional[Product]:
    """Get product by database ID"""
    return session.query(Product).filter(Product.id == id).first()


def update_product(session: Session, product_id: str, product_data: Dict) -> Optional[Product]:
    """Update existing product"""
    product = get_product_by_id(session, product_id)
    if product:
        for key, value in product_data.items():
            if hasattr(product, key):
                setattr(product, key, value)
        product.last_updated_at = datetime.utcnow()
        session.flush()
    return product


def upsert_product(session: Session, product_data: Dict) -> tuple[Product, bool]:
    """
    Insert or update product (duplicate detection)
    
    Returns:
        (product, is_new) - product object and boolean indicating if it's new
    """
    product_id = product_data.get('product_id')
    existing = get_product_by_id(session, product_id)
    
    if existing:
        # Update existing product
        for key, value in product_data.items():
            if hasattr(existing, key) and key not in ['id', 'first_seen_at', 'created_at']:
                setattr(existing, key, value)
        existing.last_updated_at = datetime.utcnow()
        session.flush()
        return existing, False
    else:
        # Create new product
        product = create_product(session, product_data)
        return product, True


def delete_product(session: Session, product_id: str) -> bool:
    """Delete product by ASIN"""
    product = get_product_by_id(session, product_id)
    if product:
        session.delete(product)
        session.flush()
        return True
    return False


def get_all_products(session: Session, limit: int = 100, offset: int = 0) -> List[Product]:
    """Get all products with pagination"""
    return session.query(Product).limit(limit).offset(offset).all()


def get_products_by_category(
    session: Session, 
    category: str, 
    limit: int = 100, 
    offset: int = 0
) -> List[Product]:
    """Get products by category"""
    return (
        session.query(Product)
        .filter(Product.category == category)
        .order_by(desc(Product.last_updated_at))
        .limit(limit)
        .offset(offset)
        .all()
    )


def get_products_by_brand(
    session: Session, 
    brand: str, 
    limit: int = 100, 
    offset: int = 0
) -> List[Product]:
    """Get products by brand"""
    return (
        session.query(Product)
        .filter(Product.brand == brand)
        .order_by(desc(Product.last_updated_at))
        .limit(limit)
        .offset(offset)
        .all()
    )


def get_best_deals(
    session: Session,
    min_discount: int = 20,
    limit: int = 50,
    category: str = None
) -> List[Product]:
    """Get products with best discounts"""
    query = session.query(Product).filter(
        and_(
            Product.discount_percentage >= min_discount,
            Product.current_price.isnot(None)
        )
    )
    
    if category:
        query = query.filter(Product.category == category)
    
    return query.order_by(desc(Product.discount_percentage)).limit(limit).all()


def get_top_rated(
    session: Session,
    min_rating: float = 4.5,
    min_reviews: int = 100,
    limit: int = 50,
    category: str = None
) -> List[Product]:
    """Get top rated products"""
    query = session.query(Product).filter(
        and_(
            Product.rating >= min_rating,
            Product.review_count >= min_reviews
        )
    )
    
    if category:
        query = query.filter(Product.category == category)
    
    return query.order_by(
        desc(Product.rating), 
        desc(Product.review_count)
    ).limit(limit).all()


def search_products(
    session: Session,
    search_term: str,
    limit: int = 50
) -> List[Product]:
    """Search products by title or brand"""
    search_pattern = f"%{search_term}%"
    return (
        session.query(Product)
        .filter(
            or_(
                Product.title.ilike(search_pattern),
                Product.brand.ilike(search_pattern)
            )
        )
        .limit(limit)
        .all()
    )


def get_products_in_price_range(
    session: Session,
    min_price: float,
    max_price: float,
    category: str = None,
    limit: int = 100
) -> List[Product]:
    """Get products within price range"""
    query = session.query(Product).filter(
        and_(
            Product.current_price >= min_price,
            Product.current_price <= max_price
        )
    )
    
    if category:
        query = query.filter(Product.category == category)
    
    return query.order_by(Product.current_price).limit(limit).all()


# ============================================================================
# PRICE HISTORY OPERATIONS
# ============================================================================

def add_price_history(session: Session, history_data: Dict) -> PriceHistory:
    """Add price history record"""
    history = PriceHistory(**history_data)
    session.add(history)
    session.flush()
    return history


def get_price_history(
    session: Session, 
    product_id: str, 
    limit: int = 100
) -> List[PriceHistory]:
    """Get price history for a product"""
    return (
        session.query(PriceHistory)
        .filter(PriceHistory.product_id == product_id)
        .order_by(desc(PriceHistory.recorded_at))
        .limit(limit)
        .all()
    )


# ============================================================================
# CATEGORY OPERATIONS
# ============================================================================

def create_category(session: Session, name: str, description: str = None) -> Category:
    """Create a new category"""
    category = Category(name=name, description=description)
    session.add(category)
    session.flush()
    return category


def get_category_by_name(session: Session, name: str) -> Optional[Category]:
    """Get category by name"""
    return session.query(Category).filter(Category.name == name).first()


def get_all_categories(session: Session) -> List[Category]:
    """Get all categories"""
    return session.query(Category).all()


def update_category_stats(session: Session, category_name: str):
    """Update category product count and last scraped time"""
    category = get_category_by_name(session, category_name)
    if category:
        count = session.query(Product).filter(Product.category == category_name).count()
        category.total_products = count
        category.last_scraped_at = datetime.utcnow()
        session.flush()


# ============================================================================
# SCRAPING SESSION OPERATIONS
# ============================================================================

def create_scraping_session(session: Session, session_data: Dict) -> ScrapingSession:
    """Create a new scraping session"""
    scrape_session = ScrapingSession(**session_data)
    session.add(scrape_session)
    session.flush()
    return scrape_session


def update_scraping_session(
    session: Session, 
    session_id: str, 
    session_data: Dict
) -> Optional[ScrapingSession]:
    """Update scraping session"""
    scrape_session = session.query(ScrapingSession).filter(
        ScrapingSession.session_id == session_id
    ).first()
    
    if scrape_session:
        for key, value in session_data.items():
            if hasattr(scrape_session, key):
                setattr(scrape_session, key, value)
        session.flush()
    
    return scrape_session


def get_recent_sessions(session: Session, limit: int = 10) -> List[ScrapingSession]:
    """Get recent scraping sessions"""
    return (
        session.query(ScrapingSession)
        .order_by(desc(ScrapingSession.started_at))
        .limit(limit)
        .all()
    )


# ============================================================================
# BULK OPERATIONS
# ============================================================================

def bulk_upsert_products(session: Session, products_data: List[Dict]) -> tuple[int, int]:
    """
    Bulk insert/update products
    
    Returns:
        (created_count, updated_count)
    """
    created = 0
    updated = 0
    
    for product_data in products_data:
        try:
            _, is_new = upsert_product(session, product_data)
            if is_new:
                created += 1
            else:
                updated += 1
        except Exception as e:
            logger.error(f"Error upserting product {product_data.get('product_id')}: {e}")
            continue
    
    session.flush()
    return created, updated


def get_product_count(session: Session) -> int:
    """Get total number of products"""
    return session.query(Product).count()


def get_category_count(session: Session) -> int:
    """Get total number of categories"""
    return session.query(Category).count()
