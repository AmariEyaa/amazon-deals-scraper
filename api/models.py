"""Pydantic models for API request/response validation"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# PRODUCT MODELS
# ============================================================================

class ProductBase(BaseModel):
    """Base product schema"""
    product_id: str = Field(..., description="Amazon ASIN (10 characters)")
    title: str = Field(..., description="Product title")
    brand: Optional[str] = Field(None, description="Product brand")
    category: Optional[str] = Field(None, description="Product category")
    current_price: Optional[float] = Field(None, description="Current price in USD")
    original_price: Optional[float] = Field(None, description="Original price before discount")
    discount_percentage: Optional[float] = Field(None, description="Discount percentage (0-100)")
    rating: Optional[float] = Field(None, description="Product rating (0-5)")
    review_count: Optional[int] = Field(None, description="Number of reviews")
    product_url: Optional[str] = Field(None, description="Amazon product URL")
    image_url: Optional[str] = Field(None, description="Product image URL")
    availability: Optional[str] = Field(None, description="Stock availability status")
    is_sponsored: Optional[bool] = Field(False, description="Whether product is sponsored")


class ProductResponse(ProductBase):
    """Product response with database fields"""
    id: int = Field(..., description="Database ID")
    first_seen_at: datetime = Field(..., description="First time product was scraped")
    last_updated_at: datetime = Field(..., description="Last update timestamp")
    created_at: datetime = Field(..., description="Database creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class ProductDetail(ProductResponse):
    """Detailed product response with price history"""
    price_history: Optional[List['PriceHistoryResponse']] = Field(None, description="Price change history")


# ============================================================================
# PRICE HISTORY MODELS
# ============================================================================

class PriceHistoryResponse(BaseModel):
    """Price history record"""
    id: int
    product_id: str
    old_price: Optional[float] = None
    new_price: Optional[float] = None
    recorded_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Update forward references
ProductDetail.model_rebuild()


# ============================================================================
# CATEGORY MODELS
# ============================================================================

class CategoryResponse(BaseModel):
    """Category information"""
    id: int
    name: str
    description: Optional[str] = None
    total_products: int = 0
    last_scraped_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# BRAND MODELS
# ============================================================================

class BrandResponse(BaseModel):
    """Brand information"""
    brand: str = Field(..., description="Brand name")
    product_count: int = Field(..., description="Number of products")
    avg_rating: Optional[float] = Field(None, description="Average rating")
    avg_price: Optional[float] = Field(None, description="Average price")


# ============================================================================
# BEST DEALS MODELS
# ============================================================================

class BestDealResponse(ProductResponse):
    """Best deal product with score"""
    deal_score: float = Field(..., description="Deal score (discount × rating)")


# ============================================================================
# PAGINATION MODELS
# ============================================================================

class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_prev: bool = Field(..., description="Whether there's a previous page")


class PaginatedProductResponse(BaseModel):
    """Paginated product list"""
    products: List[ProductResponse]
    meta: PaginationMeta


class PaginatedBestDealsResponse(BaseModel):
    """Paginated best deals list"""
    deals: List[BestDealResponse]
    meta: PaginationMeta


# ============================================================================
# ERROR MODELS
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


# ============================================================================
# STATS MODELS
# ============================================================================

class StatsResponse(BaseModel):
    """Database statistics"""
    total_products: int
    total_categories: int
    total_brands: int
    avg_discount: Optional[float] = None
    avg_rating: Optional[float] = None
    last_updated: Optional[datetime] = None
