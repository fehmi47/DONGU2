from app.routers.products import router as products_router
from app.routers.categories import router as categories_router
from app.routers.recipes import router as recipes_router
from app.routers.consumption import router as consumption_router
from app.routers.notifications import router as notifications_router
from app.routers.dashboard import router as dashboard_router

__all__ = [
    "products_router",
    "categories_router",
    "recipes_router",
    "consumption_router",
    "notifications_router",
    "dashboard_router",
]
