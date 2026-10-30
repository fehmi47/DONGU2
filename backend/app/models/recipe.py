from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Recipe(Base):
    """
    Eldeki malzemeleri değerlendirmek için sunulan yemek tariflerini tutan model.
    Hazırlık süresi, pişirme süresi, porsiyon, zorluk derecesi ve adımları barındırır.
    """
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=False)
    instructions = Column(Text, nullable=False)
    preparation_time = Column(Integer, nullable=False)  # in minutes
    cooking_time = Column(Integer, nullable=False)      # in minutes
    servings = Column(Integer, nullable=False)
    difficulty = Column(String(20), nullable=False)     # e.g., Kolay, Orta, Zor
    image_url = Column(String(500), nullable=True)

    # Relationships
    ingredients = relationship(
        "RecipeIngredient",
        back_populates="recipe",
        cascade="all, delete-orphan"
    )
    consumption_logs = relationship("ConsumptionLog", back_populates="recipe")

    def __repr__(self):
        return f"<Recipe(id={self.id}, name='{self.name}', difficulty='{self.difficulty}')>"
