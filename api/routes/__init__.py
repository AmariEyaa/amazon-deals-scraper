"""Router package initialization"""
from api.routes.products import router as products_router
from api.routes.metadata import router as metadata_router
from api.routes.deals import router as deals_router

__all__ = ['products_router', 'metadata_router', 'deals_router']
