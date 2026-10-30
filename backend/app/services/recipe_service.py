from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient
from app.schemas.recipe import RecipeCreate, RecipeUpdate


def get_recipes(db: Session, search: Optional[str] = None) -> List[Recipe]:
    """
    Sistemde kayıtlı olan tüm tarifleri listeler.
    İsteğe bağlı olarak tarif adında büyük/küçük harf duyarsız arama yapar.
    """
    query = db.query(Recipe)
    if search and search.strip():
        query = query.filter(Recipe.name.ilike(f"%{search.strip()}%"))
    return query.order_by(Recipe.name).all()


def get_recipe_by_id(db: Session, recipe_id: int) -> Optional[Recipe]:
    """
    Belirli bir tarifin detayını ve malzemelerini getirir.
    Tarif bulunamazsa None döner.
    """
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()


def create_recipe(db: Session, recipe_in: RecipeCreate) -> Recipe:
    """
    Yeni bir yemek tarifi oluşturur ve varsa tarif malzemelerini
    tek bir işlemde (transaction) kaydeder.
    """
    recipe = Recipe(
        name=recipe_in.name.strip(),
        description=recipe_in.description.strip(),
        instructions=recipe_in.instructions.strip(),
        preparation_time=recipe_in.preparation_time,
        cooking_time=recipe_in.cooking_time,
        servings=recipe_in.servings,
        difficulty=recipe_in.difficulty.strip(),
        image_url=recipe_in.image_url,
    )
    db.add(recipe)
    db.flush()

    for ing in recipe_in.ingredients:
        ingredient = RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_name=ing.ingredient_name.strip(),
            quantity=ing.quantity,
            unit=ing.unit.strip(),
            is_optional=ing.is_optional,
        )
        db.add(ingredient)

    db.commit()
    db.refresh(recipe)
    return recipe


def update_recipe(
    db: Session,
    recipe_id: int,
    recipe_in: RecipeUpdate
) -> Optional[Recipe]:
    """
    Mevcut bir tarifin bilgilerini günceller.
    Malzeme listesi gönderildiyse eski malzemeler silinip yenileri kaydedilir.
    """
    recipe = get_recipe_by_id(db, recipe_id)
    if not recipe:
        return None

    update_data = recipe_in.model_dump(exclude_unset=True)

    # Malzemeleri güncelleme
    if "ingredients" in update_data and update_data["ingredients"] is not None:
        db.query(RecipeIngredient).filter(RecipeIngredient.recipe_id == recipe.id).delete()
        for ing in recipe_in.ingredients:
            ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_name=ing.ingredient_name.strip(),
                quantity=ing.quantity,
                unit=ing.unit.strip(),
                is_optional=ing.is_optional,
            )
            db.add(ingredient)

    # Diğer alanları güncelleme
    for field in ["name", "description", "instructions", "preparation_time", "cooking_time", "servings", "difficulty", "image_url"]:
        if field in update_data:
            setattr(recipe, field, update_data[field])

    db.commit()
    db.refresh(recipe)
    return recipe


def delete_recipe(db: Session, recipe_id: int) -> bool:
    """
    Tarifi veritabanından siler. CASCADE kuralı gereği ilişkili malzemeler de silinir.
    Tüketim loglarındaki recipe_id alanı ise SET NULL kuralıyla korunur.
    """
    recipe = get_recipe_by_id(db, recipe_id)
    if not recipe:
        return False

    db.delete(recipe)
    db.commit()
    return True


def get_recipe_ingredients(db: Session, recipe_id: int) -> Optional[List[RecipeIngredient]]:
    """
    Belirli bir tarifin malzeme listesini getirir.
    Tarif bulunamazsa None döner.
    """
    recipe = get_recipe_by_id(db, recipe_id)
    if not recipe:
        return None
    return recipe.ingredients
