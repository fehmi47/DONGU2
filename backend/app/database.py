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

# Asenkron Motor ve Oturum Yönetimi (AsyncSession)
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

if DATABASE_URL.startswith("sqlite:///"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
elif DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in ASYNC_DATABASE_URL else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def get_db():
    """
    FastAPI endpoint'leri için senkron veritabanı oturumu sağlayan bağımlılık fonksiyonu.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI asenkron endpoint'leri için AsyncSession sağlayan bağımlılık fonksiyonu.
    """
    async with AsyncSessionLocal() as session:
        yield session



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

