from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import (
    create_product,
    get_user_products,
    get_product_by_id,
    update_product,
    delete_product,
    CategoryNotFoundError,
)
from app.routers.deps import get_current_user

router = APIRouter(prefix="/api/products", tags=["Ürün Yönetimi"])


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni ürün ekle",
    description="Kullanıcının kilerine veya buzdolabına yeni bir gıda ürünü ekler. STT/TETT seçildiğinde tarih zorunludur."
)
def add_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Kullanıcıya özel yeni ürün oluşturur.
    Kategori bulunamazsa 400, geçersiz veri girişinde 422 döner.
    """
    try:
        product = create_product(db, user_id=current_user.id, product_in=product_in)
        return product
    except CategoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=List[ProductResponse],
    summary="Ürünleri listele ve filtrele",
    description="Giriş yapan kullanıcının mutfağındaki ürünleri listeler. Kategori, durum, saklama alanı ve isim aramasıyla kombine filtreleme yapılabilir."
)
def list_products(
    category_id: Optional[int] = Query(None, description="Kategoriye göre filtreleme"),
    status: Optional[str] = Query("active", description="Ürün durumuna göre filtreleme (active, consumed, discarded)"),
    storage_location: Optional[str] = Query(None, description="Saklama alanına göre filtreleme (fridge, freezer, pantry)"),
    search: Optional[str] = Query(None, description="Ürün adına göre arama"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Kullanıcının kendi ürünlerini getirir. Diğer kullanıcıların ürünleri asla listelenmez.
    """
    return get_user_products(
        db,
        user_id=current_user.id,
        category_id=category_id,
        status=status,
        storage_location=storage_location,
        search=search,
    )


@router.get(
    "/{id}",
    response_model=ProductResponse,
    summary="Tek ürün detayı getir",
    description="Belirtilen ID'ye sahip ürünün detayını getirir. Ürün kullanıcıya ait değilse veya yoksa 404 döner."
)
def get_product(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tek bir ürünün detayını getirir. Kullanıcı izolasyonunu denetler.
    """
    product = get_product_by_id(db, user_id=current_user.id, product_id=id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{id} ID'li ürün bulunamadı veya bu kullanıcıya ait değil."
        )
    return product


@router.put(
    "/{id}",
    response_model=ProductResponse,
    summary="Ürün bilgilerini güncelle",
    description="Belirtilen ID'ye sahip ürünün miktarını, saklama alanını veya son tarihini günceller."
)
def modify_product(
    id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ürün güncelleme işlemi. Ürün mevcut değilse 404, güncellenen kategori geçersizse 400 döner.
    """
    try:
        updated = update_product(db, user_id=current_user.id, product_id=id, product_in=product_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{id} ID'li ürün bulunamadı veya bu kullanıcıya ait değil."
            )
        return updated
    except CategoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{id}",
    summary="Ürünü sil",
    description="Belirtilen ürünü kilerden kaldırır. Tüketim geçmişini koruyacak şekilde işlem yapar."
)
def remove_product(
    id: int,
    soft: bool = Query(False, description="True ise ürünü 'discarded' durumuna çeker, False ise tablodan siler"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ürün silme işlemi. Geçmiş tüketim logları kaybolmaz.
    """
    success = delete_product(db, user_id=current_user.id, product_id=id, soft=soft)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{id} ID'li ürün bulunamadı veya bu kullanıcıya ait değil."
        )
    return {"detail": "Ürün başarıyla silindi."}
