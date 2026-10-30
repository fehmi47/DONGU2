from app.services.category_service import (
    seed_categories,
    get_categories,
    get_category_by_id,
    DEFAULT_CATEGORIES,
)
from app.services.product_service import (
    create_product,
    get_user_products,
    get_product_by_id,
    update_product,
    delete_product,
    consume_product,
    InsufficientQuantityError,
    ProductNotFoundError,
)
from app.services.priority_service import (
    evaluate_product_priority,
    get_user_products_with_priority,
    get_user_expiring_products,
    get_single_product_priority,
)
from app.services.recipe_service import (
    get_recipes,
    get_recipe_by_id,
    create_recipe,
    update_recipe,
    delete_recipe,
    get_recipe_ingredients,
)
from app.services.recipe_matcher import match_user_products_with_recipes
from app.services.consumption_service import (
    record_consumption,
    get_user_consumptions,
    get_consumption_by_id,
    calculate_consumption_summary,
    convert_to_kg,
)
from app.services.notification_service import (
    check_and_generate_notifications,
    get_user_notifications,
    get_notification_by_id,
    mark_notification_as_read,
    mark_all_notifications_as_read,
)
from app.services.dashboard_service import get_dashboard_summary

__all__ = [
    "seed_categories",
    "get_categories",
    "get_category_by_id",
    "DEFAULT_CATEGORIES",
    "create_product",
    "get_user_products",
    "get_product_by_id",
    "update_product",
    "delete_product",
    "consume_product",
    "InsufficientQuantityError",
    "ProductNotFoundError",
    "evaluate_product_priority",
    "get_user_products_with_priority",
    "get_user_expiring_products",
    "get_single_product_priority",
    "get_recipes",
    "get_recipe_by_id",
    "create_recipe",
    "update_recipe",
    "delete_recipe",
    "get_recipe_ingredients",
    "match_user_products_with_recipes",
    "record_consumption",
    "get_user_consumptions",
    "get_consumption_by_id",
    "calculate_consumption_summary",
    "convert_to_kg",
    "check_and_generate_notifications",
    "get_user_notifications",
    "get_notification_by_id",
    "mark_notification_as_read",
    "mark_all_notifications_as_read",
    "get_dashboard_summary",
]
