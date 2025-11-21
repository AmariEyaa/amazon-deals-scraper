"""API dependencies and shared utilities"""
from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger

from database import db_manager


# ============================================================================
# DATABASE SESSION DEPENDENCY
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    
    Usage:
        @app.get("/products")
        def get_products(db: Session = Depends(get_db)):
            ...
    """
    with db_manager.get_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )


# ============================================================================
# PAGINATION HELPER
# ============================================================================

def calculate_pagination(
    page: int, 
    limit: int, 
    total_items: int
) -> dict:
    """
    Calculate pagination metadata
    
    Args:
        page: Current page number (1-indexed)
        limit: Items per page
        total_items: Total number of items
        
    Returns:
        Dictionary with pagination metadata
    """
    total_pages = (total_items + limit - 1) // limit  # Ceiling division
    
    return {
        "page": page,
        "limit": limit,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


# ============================================================================
# QUERY PARAMETER VALIDATORS
# ============================================================================

def validate_page(page: int) -> int:
    """Validate page number"""
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be >= 1"
        )
    return page


def validate_limit(limit: int, max_limit: int = 100) -> int:
    """Validate limit parameter"""
    if limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be >= 1"
        )
    if limit > max_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Limit cannot exceed {max_limit}"
        )
    return limit


def validate_price_range(min_price: float, max_price: float):
    """Validate price range"""
    if min_price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price must be >= 0"
        )
    if max_price < min_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_price must be >= min_price"
        )


def validate_rating(rating: float):
    """Validate rating value"""
    if not (0 <= rating <= 5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 0 and 5"
        )


def validate_discount(discount: int):
    """Validate discount percentage"""
    if not (0 <= discount <= 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Discount must be between 0 and 100"
        )
