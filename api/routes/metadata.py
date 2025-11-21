"""Category and brand routes"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from api.models import CategoryResponse, BrandResponse
from api.dependencies import get_db
from database import get_all_categories
from database.models import Product, Category

router = APIRouter(tags=["metadata"])


# ============================================================================
# GET ALL CATEGORIES
# ============================================================================

@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(db: Session = Depends(get_db)):
    """
    Get all available product categories
    
    **Returns:**
    List of categories with metadata:
    - name: Category name
    - description: Category description
    - total_products: Number of products in category
    - last_scraped_at: Last scraping timestamp
    """
    categories = get_all_categories(db)
    
    if not categories:
        # If no categories in category table, get from products
        categories_from_products = (
            db.query(
                Product.category.label('name'),
                func.count(Product.id).label('total_products')
            )
            .filter(Product.category.isnot(None))
            .group_by(Product.category)
            .all()
        )
        
        return [
            {
                "id": idx + 1,
                "name": cat.name,
                "description": None,
                "total_products": cat.total_products,
                "last_scraped_at": None,
                "created_at": None
            }
            for idx, cat in enumerate(categories_from_products)
        ]
    
    return categories


# ============================================================================
# GET ALL BRANDS
# ============================================================================

@router.get("/brands", response_model=List[BrandResponse])
async def list_brands(
    db: Session = Depends(get_db),
    category: str = None
):
    """
    Get all available brands with statistics
    
    **Parameters:**
    - category: Optional filter by category
    
    **Returns:**
    List of brands with:
    - brand: Brand name
    - product_count: Number of products
    - avg_rating: Average product rating
    - avg_price: Average product price
    """
    query = db.query(
        Product.brand.label('brand'),
        func.count(Product.id).label('product_count'),
        func.avg(Product.rating).label('avg_rating'),
        func.avg(Product.current_price).label('avg_price')
    ).filter(Product.brand.isnot(None))
    
    if category:
        query = query.filter(Product.category == category)
    
    brands = query.group_by(Product.brand).order_by(func.count(Product.id).desc()).all()
    
    return [
        {
            "brand": brand.brand,
            "product_count": brand.product_count,
            "avg_rating": round(brand.avg_rating, 2) if brand.avg_rating else None,
            "avg_price": round(brand.avg_price, 2) if brand.avg_price else None
        }
        for brand in brands
    ]
