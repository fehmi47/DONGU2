from app.routers.products import router as products_router
from app.routers.categories import router as categories_router
from app.routers.recipes import router as recipes_router

__all__ = ["products_router", "categories_router", "recipes_router"]
