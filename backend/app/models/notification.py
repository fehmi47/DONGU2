from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base


class Notification(Base):
    """
    Kullanıcıya STT yaklaşması, TETT uyarısı veya sistem bilgilendirmesi göndermek için kullanılan model.
    Kullanıcının hangi ürünle ilgili uyarı aldığını ve bildirimi okuyup okumadığını takip eder.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(30), nullable=False)  # expiry_warning, stt_alert, system, etc.
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="notifications")
    product = relationship("Product", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, title='{self.title}', read={self.is_read})>"
