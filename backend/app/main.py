from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db, SessionLocal
from app.services.category_service import seed_categories
from app.routers.products import router as products_router
from app.routers.categories import router as categories_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Uygulama yaşam döngüsü yöneticisi.
    Uygulama açılırken veritabanı tablolarını ve varsayılan kategorileri hazırlar.
    """
    init_db()
    db = SessionLocal()
    try:
        seed_categories(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="DÖNGÜ API",
    description="""
    ## 🌿 DÖNGÜ - Sürdürülebilir Akıllı Mutfak ve Gıda Yönetim Sistemi API

    DÖNGÜ, evlerdeki gıda israfını önlemeye yönelik akıllı takip ve sürdürülebilirlik platformudur.

    ### 📦 Sunulan Yetenekler:
    * **Ürün Yönetimi:** Kiler, buzdolabı ve dondurucudaki gıdaların STT/TETT takibi ve miktarsal yönetimi.
    * **Gelişmiş Filtreleme:** Kategori, saklama yeri, durum ve serbest metin arama filtreleri.
    * **Kategori Sistemi:** Doğrulanmış gıda kategorileri listeleme.
    * **Veri Güvenliği ve İzolasyonu:** Her kullanıcı yalnızca kendi mutfağındaki ürünlere erişebilir.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Router'ları uygulamaya dahil etme
app.include_router(products_router)
app.include_router(categories_router)


@app.get("/health", tags=["Sistem"])
def health_check():
    """Sistem sağlık kontrolü endpoint'i."""
    return {"status": "ok", "project": "DÖNGÜ", "version": "1.0.0"}
