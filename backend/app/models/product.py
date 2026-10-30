from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index
)
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    """
    Kullanıcının kiler veya buzdolabında bulunan gıda ürünlerini temsil eden veritabanı modeli.
    
    Temel Sorumlulukları:
    - Ürünün miktarını, birimini ve saklama yerini (buzdolabı, dondurucu, kiler) takip etmek.
    - STT (Son Tüketim Tarihi) veya TETT (Tavsiye Edilen Tüketim Tarihi) takibini sağlamak.
    - Ürünün yaşam döngüsünü ('active', 'consumed', 'discarded') yönetmek.
    - Tüketim logları ve bildirimlerle olan ilişkileri kurmak.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20), nullable=False)
    expiry_date = Column(Date, nullable=True, index=True)
    date_type = Column(String(10), nullable=False, default="STT")  # STT, TETT, NONE
    storage_location = Column(String(20), nullable=False, default="fridge")  # fridge, freezer, pantry
    status = Column(String(20), nullable=False, default="active", index=True)  # active, consumed, discarded
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="chk_product_quantity_non_negative"),
        CheckConstraint("date_type IN ('STT', 'TETT', 'NONE')", name="chk_product_date_type"),
        CheckConstraint("storage_location IN ('fridge', 'freezer', 'pantry')", name="chk_product_storage_location"),
        CheckConstraint("status IN ('active', 'consumed', 'discarded')", name="chk_product_status"),
        Index("idx_product_user_status", "user_id", "status"),
        Index("idx_product_user_category", "user_id", "category_id"),
    )

    # Relationships
    user = relationship("User", back_populates="products")
    category = relationship("Category", back_populates="products")
    consumption_logs = relationship("ConsumptionLog", back_populates="product")
    notifications = relationship("Notification", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', quantity={self.quantity} {self.unit}, status='{self.status}')>"
