from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class RecipeIngredientBase(BaseModel):
    ingredient_name: str = Field(..., min_length=1, max_length=100)
    quantity: Decimal = Field(..., gt=0, decimal_places=2)
    unit: str = Field(..., min_length=1, max_length=20)
    is_optional: bool = False


class RecipeIngredientCreate(RecipeIngredientBase):
    pass


class RecipeIngredientResponse(RecipeIngredientBase):
    id: int
    recipe_id: int

    model_config = ConfigDict(from_attributes=True)


class RecipeBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: str
    instructions: str
    preparation_time: int = Field(..., ge=0)
    cooking_time: int = Field(..., ge=0)
    servings: int = Field(..., gt=0)
    difficulty: str = Field(..., min_length=1, max_length=20)
    image_url: Optional[str] = None


class RecipeCreate(RecipeBase):
    ingredients: List[RecipeIngredientCreate] = []


class RecipeResponse(RecipeBase):
    id: int
    ingredients: List[RecipeIngredientResponse] = []

    model_config = ConfigDict(from_attributes=True)
