"""SQLAlchemy database models"""
from sqlalchemy import (
    Column, Integer, String, Text, DECIMAL, Boolean, 
    DateTime, ForeignKey, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Product(Base):
    """Product model - main table for scraped products"""
    
    __tablename__ = 'products'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Amazon ASIN (unique identifier)
    product_id = Column(String(20), unique=True, nullable=False, index=True)
    
    # Product details
    title = Column(Text, nullable=False)
    brand = Column(String(255), index=True)
    category = Column(String(100), nullable=False, index=True)
    
    # Pricing
    current_price = Column(DECIMAL(10, 2), index=True)
    original_price = Column(DECIMAL(10, 2))
    discount_percentage = Column(Integer, index=True)
    
    # Reviews
    rating = Column(DECIMAL(3, 2), index=True)  # 0.00 to 5.00
    review_count = Column(Integer)
    
    # URLs
    product_url = Column(Text, nullable=False)
    image_url = Column(Text)
    
    # Status
    availability = Column(String(50))
    is_sponsored = Column(Boolean, default=False)
    
    # Timestamps
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    price_history = relationship('PriceHistory', back_populates='product', cascade='all, delete-orphan')
    
    # Composite indexes
    __table_args__ = (
        Index('idx_category_price', 'category', 'current_price'),
        Index('idx_category_rating', 'category', 'rating'),
        Index('idx_category_discount', 'category', 'discount_percentage'),
    )
    
    def __repr__(self):
        return f"<Product(id={self.product_id}, title='{self.title[:30]}...', price={self.current_price})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'title': self.title,
            'brand': self.brand,
            'category': self.category,
            'current_price': float(self.current_price) if self.current_price else None,
            'original_price': float(self.original_price) if self.original_price else None,
            'discount_percentage': self.discount_percentage,
            'rating': float(self.rating) if self.rating else None,
            'review_count': self.review_count,
            'product_url': self.product_url,
            'image_url': self.image_url,
            'availability': self.availability,
            'is_sponsored': self.is_sponsored,
            'first_seen_at': self.first_seen_at.isoformat() if self.first_seen_at else None,
            'last_updated_at': self.last_updated_at.isoformat() if self.last_updated_at else None,
        }


class PriceHistory(Base):
    """Price history model - tracks price changes over time"""
    
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(20), ForeignKey('products.product_id', ondelete='CASCADE'), nullable=False, index=True)
    
    price = Column(DECIMAL(10, 2), nullable=False)
    original_price = Column(DECIMAL(10, 2))
    discount_percentage = Column(Integer)
    
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    product = relationship('Product', back_populates='price_history')
    
    def __repr__(self):
        return f"<PriceHistory(product_id={self.product_id}, price={self.price}, recorded_at={self.recorded_at})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'price': float(self.price) if self.price else None,
            'original_price': float(self.original_price) if self.original_price else None,
            'discount_percentage': self.discount_percentage,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
        }


class Category(Base):
    """Category model - stores product categories"""
    
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    total_products = Column(Integer, default=0)
    last_scraped_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Category(name='{self.name}', products={self.total_products})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'total_products': self.total_products,
            'last_scraped_at': self.last_scraped_at.isoformat() if self.last_scraped_at else None,
        }


class ScrapingSession(Base):
    """Scraping session model - tracks scraping runs"""
    
    __tablename__ = 'scraping_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), unique=True, index=True)  # UUID
    category = Column(String(100))
    pages_scraped = Column(Integer, default=0)
    products_found = Column(Integer, default=0)
    products_saved = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    status = Column(String(20), default='running', index=True)  # running, completed, failed
    
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)
    
    def __repr__(self):
        return f"<ScrapingSession(id={self.session_id}, category='{self.category}', status='{self.status}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'category': self.category,
            'pages_scraped': self.pages_scraped,
            'products_found': self.products_found,
            'products_saved': self.products_saved,
            'errors_count': self.errors_count,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
