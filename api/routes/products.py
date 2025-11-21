"""Product routes"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from api.models import (
    ProductResponse,
    ProductDetail,
    PaginatedProductResponse,
    PaginationMeta
)
from api.dependencies import (
    get_db,
    calculate_pagination,
    validate_page,
    validate_limit,
    validate_price_range,
    validate_rating,
    validate_discount
)
from database import (
    get_all_products,
    get_product_by_id,
    get_products_by_category,
    get_products_by_brand,
    get_products_in_price_range,
    search_products,
    get_product_count,
    get_price_history
)
from database.models import Product

router = APIRouter(prefix="/products", tags=["products"])


# ============================================================================
# GET ALL PRODUCTS WITH FILTERS
# ============================================================================

@router.get("", response_model=PaginatedProductResponse)
async def list_products(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
    min_discount: Optional[int] = Query(None, ge=0, le=100, description="Minimum discount %"),
    search: Optional[str] = Query(None, description="Search in title/brand"),
    sort_by: str = Query("last_updated_at", description="Sort field: price, rating, discount, last_updated_at"),
    order: str = Query("desc", description="Sort order: asc or desc")
):
    """
    Get all products with optional filters, pagination, and sorting
    
    **Filters:**
    - category: Filter by product category
    - brand: Filter by brand name
    - min_price, max_price: Price range filter
    - min_rating: Minimum product rating (0-5)
    - min_discount: Minimum discount percentage (0-100)
    - search: Search in title or brand
    
    **Pagination:**
    - page: Page number (default: 1)
    - limit: Items per page (default: 50, max: 100)
    
    **Sorting:**
    - sort_by: Field to sort by (price, rating, discount, last_updated_at)
    - order: Sort order (asc or desc)
    """
    # Validate parameters
    validate_page(page)
    validate_limit(limit)
    
    if min_price is not None and max_price is not None:
        validate_price_range(min_price, max_price)
    
    if min_rating is not None:
        validate_rating(min_rating)
    
    if min_discount is not None:
        validate_discount(min_discount)
    
    # Build query
    query = db.query(Product)
    
    # Apply filters
    if category:
        query = query.filter(Product.category == category)
    
    if brand:
        query = query.filter(Product.brand == brand)
    
    if min_price is not None:
        query = query.filter(Product.current_price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.current_price <= max_price)
    
    if min_rating is not None:
        query = query.filter(Product.rating >= min_rating)
    
    if min_discount is not None:
        query = query.filter(Product.discount_percentage >= min_discount)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Product.title.ilike(search_pattern)) | 
            (Product.brand.ilike(search_pattern))
        )
    
    # Get total count before pagination
    total_items = query.count()
    
    # Apply sorting
    sort_field_map = {
        "price": Product.current_price,
        "rating": Product.rating,
        "discount": Product.discount_percentage,
        "last_updated_at": Product.last_updated_at
    }
    
    if sort_by not in sort_field_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_by field. Choose from: {', '.join(sort_field_map.keys())}"
        )
    
    sort_field = sort_field_map[sort_by]
    
    if order.lower() == "desc":
        query = query.order_by(sort_field.desc())
    elif order.lower() == "asc":
        query = query.order_by(sort_field.asc())
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must be 'asc' or 'desc'"
        )
    
    # Apply pagination
    offset = (page - 1) * limit
    products = query.offset(offset).limit(limit).all()
    
    # Calculate pagination metadata
    pagination_meta = calculate_pagination(page, limit, total_items)
    
    return {
        "products": products,
        "meta": pagination_meta
    }


# ============================================================================
# GET SINGLE PRODUCT BY ID
# ============================================================================

@router.get("/{product_id}", response_model=ProductDetail)
async def get_product(
    product_id: str = Path(..., description="Amazon ASIN (10 characters)"),
    db: Session = Depends(get_db),
    include_history: bool = Query(True, description="Include price history")
):
    """
    Get detailed information for a single product by ASIN
    
    **Parameters:**
    - product_id: Amazon ASIN (product identifier)
    - include_history: Whether to include price history (default: true)
    
    **Returns:**
    Product details with optional price history
    """
    product = get_product_by_id(db, product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Convert to dict
    product_dict = product.to_dict()
    
    # Add price history if requested
    if include_history:
        price_history = get_price_history(db, product_id, limit=10)
        product_dict['price_history'] = [ph.to_dict() for ph in price_history]
    else:
        product_dict['price_history'] = None
    
    return product_dict
