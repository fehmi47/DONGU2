from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db, SessionLocal
from app.services.category_service import seed_categories
from app.data.seed_recipes import seed_recipes
from app.routers.products import router as products_router
from app.routers.categories import router as categories_router
from app.routers.recipes import router as recipes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Uygulama yaşam döngüsü yöneticisi.
    Uygulama açılırken veritabanı tablolarını, varsayılan kategorileri ve
    20 temel yemek tarifini idempotent olarak hazırlar.
    """
    init_db()
    db = SessionLocal()
    try:
        seed_categories(db)
        seed_recipes(db)
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
    * **Akıllı Öncelik Sistemi:** Son tüketim tarihi yaklaşan gıdaları tespit etme ve güvenlik sınıflandırması.
    * **Tarif Yönetimi & Akıllı Eşleştirme:** Eldeki malzemelerle yapılabilecek tarifleri önceliklendirerek gıda israfını önleme.
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
app.include_router(recipes_router)


@app.get("/health", tags=["Sistem"])
def health_check():
    """Sistem sağlık kontrolü endpoint'i."""
    return {"status": "ok", "project": "DÖNGÜ", "version": "1.0.0"}
