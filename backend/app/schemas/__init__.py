from app.schemas.user import UserBase, UserCreate, UserResponse
from app.schemas.category import CategoryBase, CategoryCreate, CategoryResponse
from app.schemas.product import (
    ProductBase,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductPriorityResponse,
)
from app.schemas.recipe import (
    RecipeIngredientBase,
    RecipeIngredientCreate,
    RecipeIngredientResponse,
    RecipeBase,
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    MatchedIngredientInfo,
    MissingIngredientInfo,
    RecipeRecommendationResponse,
)
from app.schemas.consumption import (
    ConsumptionCreate,
    ConsumptionResponse,
    CategoryConsumptionSummary,
    EnvironmentalImpactSummary,
    ConsumptionSummaryResponse,
)
from app.schemas.notification import NotificationBase, NotificationCreate, NotificationResponse
from app.schemas.dashboard import DashboardSummaryResponse, WeeklyStatItem

__all__ = [
    "UserBase",
    "UserCreate",
    "UserResponse",
    "CategoryBase",
    "CategoryCreate",
    "CategoryResponse",
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductPriorityResponse",
    "RecipeIngredientBase",
    "RecipeIngredientCreate",
    "RecipeIngredientResponse",
    "RecipeBase",
    "RecipeCreate",
    "RecipeUpdate",
    "RecipeResponse",
    "MatchedIngredientInfo",
    "MissingIngredientInfo",
    "RecipeRecommendationResponse",
    "ConsumptionCreate",
    "ConsumptionResponse",
    "CategoryConsumptionSummary",
    "EnvironmentalImpactSummary",
    "ConsumptionSummaryResponse",
    "NotificationBase",
    "NotificationCreate",
    "NotificationResponse",
    "DashboardSummaryResponse",
    "WeeklyStatItem",
]
