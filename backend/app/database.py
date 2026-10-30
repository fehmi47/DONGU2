import os
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Proje dizinini ve SQLite veritabanı dosyasının konumunu belirleme
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "dongu.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# SQLite bağlantısı ve FastAPI eşzamanlı istekleri için thread ayarı
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# SQLite'ta ilişkisel veri bütünlüğünü korumak için her bağlantıda Foreign Key desteğini aktif etme
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    SQLite veritabanı bağlantısı açıldığında PRAGMA foreign_keys=ON komutunu çalıştırır.
    Bu işlem, geçersiz foreign key girişlerini ve veri tutarsızlıklarını engeller.
    """
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Oturum yönetimi ve ORM temel sınıfı
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    FastAPI endpoint'leri için veritabanı oturumu sağlayan bağımlılık (dependency) fonksiyonu.
    İşlem tamamlandığında veya hata oluştuğunda oturumu güvenli bir şekilde kapatır.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Tanımlı tüm SQLAlchemy modellerini kontrol eder ve veritabanında henüz
    oluşturulmamış olan tabloları otomatik olarak oluşturur.
    """
    from app.models import (  # noqa: F401
        User,
        Category,
        Product,
        Recipe,
        RecipeIngredient,
        ConsumptionLog,
        Notification,
    )
    Base.metadata.create_all(bind=engine)

