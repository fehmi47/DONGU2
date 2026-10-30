import os
from dotenv import load_dotenv
load_dotenv()
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db, SessionLocal
from app.services.category_service import seed_categories
from app.services.user_service import seed_users
from app.data.seed_recipes import seed_recipes
from app.data.seed_sample_products import seed_demo_products

# API Router'ları
from app.routers.products import router as products_router
from app.routers.categories import router as categories_router
from app.routers.recipes import router as recipes_router
from app.routers.consumption import router as consumption_router
from app.routers.notifications import router as notifications_router
from app.routers.dashboard import router as dashboard_router
from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router


# Dizin yollarını belirleme
APP_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(APP_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")
INDEX_HTML = os.path.join(TEMPLATES_DIR, "index.html")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Uygulama yaşam döngüsü yöneticisi.
    Uygulama açılırken veritabanı tablolarını, varsayılan kullanıcıları,
    kategorileri, 20 temel yemek tarifini ve demo ürünleri hazır eder.
    """
    init_db()
    db = SessionLocal()
    try:
        seed_users(db)
        seed_categories(db)
        seed_recipes(db)
        seed_demo_products(db, user_id=1)
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
    * **Tüketim ve Etki Takibi:** Gerçek gıda tüketimlerini kaydetme, karbon ve su ayak izi tasarrufunu ölçme.
    * **Bildirimler:** Yaklaşan tüketim tarihleri ve acil değerlendirilmesi gereken ürün uyarıları.
    * **Veri Güvenliği ve İzolasyonu:** Her kullanıcı yalnızca kendi mutfağındaki ürünlere erişebilir.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Statik dosyaları (/static) bağlama
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# API Router'larını uygulamaya dahil etme
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(categories_router)
app.include_router(recipes_router)
app.include_router(consumption_router)
app.include_router(notifications_router)
app.include_router(dashboard_router)
app.include_router(chat_router)



# ==============================================================================
# FRONTEND SAYFA ROTALARI
# ==============================================================================

@app.get("/", tags=["Arayüz"], summary="Ana Sayfa (Landing & Giriş)")
@app.get("/home", tags=["Arayüz"], summary="Ana Sayfa")
@app.get("/login", tags=["Arayüz"], summary="Giriş Sayfası")
@app.get("/register", tags=["Arayüz"], summary="Kayıt Sayfası")
def serve_home():
    """DÖNGÜ tek sayfa arayüzünü (SPA) döner."""
    return FileResponse(INDEX_HTML)



@app.get("/pantry", tags=["Arayüz"], summary="Mutfağım Sayfası")
def serve_pantry():
    return FileResponse(INDEX_HTML)


@app.get("/recipes-view", tags=["Arayüz"], summary="Tarifler Sayfası")
def serve_recipes():
    return FileResponse(INDEX_HTML)


@app.get("/impact", tags=["Arayüz"], summary="Etki Paneli Sayfası")
def serve_impact():
    return FileResponse(INDEX_HTML)


@app.get("/notifications-view", tags=["Arayüz"], summary="Bildirimler Sayfası")
def serve_notifications():
    return FileResponse(INDEX_HTML)


@app.get("/health", tags=["Sistem"])
def health_check():
    """Sistem sağlık kontrolü endpoint'i."""
    return {"status": "ok", "project": "DÖNGÜ", "version": "1.0.0"}
