"""Best deals route"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, case, func

from api.models import PaginatedBestDealsResponse, BestDealResponse, PaginationMeta
from api.dependencies import (
    get_db,
    calculate_pagination,
    validate_page,
    validate_limit,
    validate_discount,
    validate_rating
)
from database.models import Product

router = APIRouter(prefix="/best-deals", tags=["best-deals"])


# ============================================================================
# GET BEST DEALS
# ============================================================================

@router.get("", response_model=PaginatedBestDealsResponse)
async def get_best_deals(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_discount: int = Query(20, ge=0, le=100, description="Minimum discount %"),
    min_rating: float = Query(4.0, ge=0, le=5, description="Minimum rating"),
    min_reviews: int = Query(10, ge=0, description="Minimum number of reviews")
):
    """
    Get best deals with intelligent scoring algorithm
    
    **Deal Score Algorithm:**
    ```
    deal_score = discount_percentage × rating × log(review_count + 1) / 10
    ```
    
    This formula prioritizes:
    - High discount percentages
    - High ratings (4.0+ stars)
    - Products with more reviews (social proof)
    
    **Filters:**
    - category: Filter by product category
    - min_discount: Minimum discount percentage (default: 20%)
    - min_rating: Minimum product rating (default: 4.0)
    - min_reviews: Minimum number of reviews (default: 10)
    
    **Pagination:**
    - page: Page number (default: 1)
    - limit: Items per page (default: 50, max: 100)
    
    **Example:**
    ```
    GET /best-deals?category=laptop&min_discount=30&min_rating=4.5&page=1&limit=20
    ```
    """
    # Validate parameters
    validate_page(page)
    validate_limit(limit)
    validate_discount(min_discount)
    validate_rating(min_rating)
    
    # Build query with deal score calculation
    # Formula: discount × rating × log(reviews + 1) / 10
    # Using case to handle NULL values
    query = db.query(
        Product,
        (
            Product.discount_percentage * 
            Product.rating * 
            func.log(Product.review_count + 1) / 10
        ).label('deal_score')
    ).filter(
        and_(
            Product.discount_percentage >= min_discount,
            Product.rating >= min_rating,
            Product.review_count >= min_reviews,
            Product.current_price.isnot(None),
            Product.rating.isnot(None),
            Product.discount_percentage.isnot(None)
        )
    )
    
    # Apply category filter
    if category:
        query = query.filter(Product.category == category)
    
    # Get total count
    total_items = query.count()
    
    # Sort by deal score (highest first)
    query = query.order_by(case((Product.discount_percentage.isnot(None), 
                                   Product.discount_percentage * Product.rating * 
                                   func.log(Product.review_count + 1) / 10), 
                                  else_=0).desc())
    
    # Apply pagination
    offset = (page - 1) * limit
    results = query.offset(offset).limit(limit).all()
    
    # Format response
    deals = []
    for product, deal_score in results:
        product_dict = product.to_dict()
        product_dict['deal_score'] = round(deal_score if deal_score else 0, 2)
        deals.append(product_dict)
    
    # Calculate pagination metadata
    pagination_meta = calculate_pagination(page, limit, total_items)
    
    return {
        "deals": deals,
        "meta": pagination_meta
    }
