from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db, SessionLocal
from app.services.category_service import seed_categories


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize schema and seed default categories
    init_db()
    db = SessionLocal()
    try:
        seed_categories(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="DÖNGÜ API",
    description="Gıda İsrafını Önleme ve Sürdürülebilirlik Platformu API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    return {"status": "ok", "project": "DÖNGÜ", "version": "0.1.0"}
