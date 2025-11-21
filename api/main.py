"""FastAPI application entry point"""
import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from loguru import logger
from dotenv import load_dotenv

from database import db_manager
from api.routes import products_router, metadata_router, deals_router

# Load environment variables
load_dotenv()


# ============================================================================
# LIFESPAN CONTEXT MANAGER
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events
    """
    # Startup
    logger.info("Starting Amazon Deals API...")
    
    # Test database connection (optional - works without DB for JSON-only demo)
    # try:
    #     is_connected = db_manager.test_connection()
    #     if is_connected:
    #         logger.success("✅ Database connection successful")
    #     else:
    #         logger.error("❌ Database connection failed")
    # except Exception as e:
    #     logger.error(f"Database connection error: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Amazon Deals API...")
    db_manager.close()
    logger.success("✅ Database connections closed")


# ============================================================================
# CREATE FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Amazon Deals API",
    description="""
    # Amazon Deals Scraper API
    
    A comprehensive REST API for querying Amazon product deals, prices, and ratings.
    
    ## Features
    
    - **Product Search**: Filter by category, brand, price, rating, and discount
    - **Best Deals**: Intelligent scoring algorithm for finding the best deals
    - **Pagination**: Efficient data retrieval with customizable page sizes
    - **Sorting**: Sort by price, rating, discount, or last updated
    - **Price History**: Track price changes over time
    
    ## Authentication
    
    Currently, no authentication is required. This is a demo API.
    
    ## Rate Limiting
    
    Please be respectful with API usage. Consider implementing rate limiting for production use.
    
    ## Data Source
    
    Product data is scraped from Amazon with respect to robots.txt and rate limiting policies.
    Last updated data may vary based on scraping frequency.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    contact={
        "name": "Amazon Deals Scraper",
        "url": "https://github.com/AmariEyaa/amazon-deals-scraper",
    },
    license_info={
        "name": "MIT",
    }
)


# ============================================================================
# CORS MIDDLEWARE
# ============================================================================

# Get allowed origins from environment variable (comma-separated)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc)
        }
    )


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

app.include_router(products_router)
app.include_router(metadata_router)
app.include_router(deals_router)


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["root"])
async def root():
    """
    API root endpoint with basic information
    """
    return {
        "name": "Amazon Deals API",
        "version": "1.0.0",
        "status": "online",
        "documentation": "/docs",
        "endpoints": {
            "products": "/products",
            "product_detail": "/products/{id}",
            "categories": "/categories",
            "brands": "/brands",
            "best_deals": "/best-deals"
        }
    }


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint
    """
    try:
        is_connected = db_manager.test_connection()
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "database": "connected" if is_connected else "disconnected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e)
        }


# ============================================================================
# STATS ENDPOINT
# ============================================================================

@app.get("/demo/best-deals", tags=["demo"])
async def get_demo_best_deals(limit: int = 10):
    """
    Demo endpoint - Returns best deals from sample JSON file
    Calculates score: (discount * 0.6) + (rating * 10)
    """
    import json
    from pathlib import Path
    
    try:
        # Read sample data
        data_file = Path(__file__).parent.parent / "data" / "sample_products.json"
        with open(data_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        # Calculate deal score for each product
        deals = []
        for product in products:
            discount = product.get('discount_percent', 0) or 0
            rating = product.get('rating', 0) or 0
            
            # Best deals algorithm: (discount * 0.6) + (rating * 10)
            score = (discount * 0.6) + (rating * 10)
            
            deals.append({
                **product,
                'deal_score': round(score, 2)
            })
        
        # Sort by score descending
        deals.sort(key=lambda x: x['deal_score'], reverse=True)
        
        # Return top deals
        return {
            "deals": deals[:limit],
            "total": len(deals),
            "algorithm": "(discount_percent * 0.6) + (rating * 10)"
        }
    
    except Exception as e:
        return {"error": str(e)}


@app.get("/stats", tags=["stats"])
async def get_stats():
    """
    Get API statistics
    """
    from database import get_product_count, get_category_count, get_db_session
    from sqlalchemy import func
    from database.models import Product
    
    try:
        with get_db_session() as session:
            total_products = get_product_count(session)
            total_categories = get_category_count(session)
            
            # Get brand count
            total_brands = session.query(func.count(func.distinct(Product.brand))).scalar()
            
            # Get average discount and rating
            avg_discount = session.query(func.avg(Product.discount_percentage)).filter(
                Product.discount_percentage.isnot(None)
            ).scalar()
            
            avg_rating = session.query(func.avg(Product.rating)).filter(
                Product.rating.isnot(None)
            ).scalar()
            
            # Get last updated
            last_updated = session.query(func.max(Product.last_updated_at)).scalar()
            
            return {
                "total_products": total_products,
                "total_categories": total_categories,
                "total_brands": total_brands,
                "avg_discount": round(avg_discount, 2) if avg_discount else None,
                "avg_rating": round(avg_rating, 2) if avg_rating else None,
                "last_updated": last_updated
            }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "error": "Failed to retrieve stats",
            "detail": str(e)
        }


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
