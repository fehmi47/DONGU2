from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.category import CategoryResponse
from app.services.category_service import get_categories, get_category_by_id

router = APIRouter(prefix="/api/categories", tags=["Kategoriler"])


@router.get(
    "",
    response_model=List[CategoryResponse],
    summary="Tüm kategorileri listele",
    description="Sistemde tanımlı olan tüm gıda kategorilerini ID sırasına göre listeler."
)
def list_categories(db: Session = Depends(get_db)):
    """
    Tüm kategorileri döner.
    Ürün eklerken veya filtrelerken kullanılacak kategori seçeneklerini sağlar.
    """
    return get_categories(db)


@router.get(
    "/{id}",
    response_model=CategoryResponse,
    summary="Kategori detayını getir",
    description="Belirtilen ID'ye sahip kategorinin detay bilgilerini getirir."
)
def get_category(id: int, db: Session = Depends(get_db)):
    """
    Kategori detayını getirir. Kategori bulunamazsa 404 döner.
    """
    category = get_category_by_id(db, category_id=id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{id} ID'li kategori bulunamadı."
        )
    return category
