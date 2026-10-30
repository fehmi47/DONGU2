from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True)
    ingredient_name = Column(String(100), nullable=False, index=True)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20), nullable=False)
    is_optional = Column(Boolean, default=False, nullable=False)

    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")

    def __repr__(self):
        return f"<RecipeIngredient(id={self.id}, name='{self.ingredient_name}', quantity={self.quantity} {self.unit})>"
