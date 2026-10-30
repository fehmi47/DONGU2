from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    CheckConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class ConsumptionLog(Base):
    __tablename__ = "consumption_logs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    recipe_id = Column(
        Integer,
        ForeignKey("recipes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    quantity_used = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20), nullable=False)
    action_type = Column(String(20), nullable=False)  # consumed, discarded, recipe_used
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        CheckConstraint("quantity_used > 0", name="chk_consumption_quantity_positive"),
    )

    # Relationships
    product = relationship("Product", back_populates="consumption_logs")
    recipe = relationship("Recipe", back_populates="consumption_logs")

    def __repr__(self):
        return f"<ConsumptionLog(id={self.id}, product_id={self.product_id}, quantity={self.quantity_used} {self.unit}, action='{self.action_type}')>"
