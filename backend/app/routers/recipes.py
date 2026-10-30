from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db, get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.recipe import (
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    RecipeIngredientResponse,
    RecipeRecommendationResponse,
)
from app.schemas.smart_deduction import (
    RecipeDeductionRequest,
    RecipeDeductionResponse,
)
from app.services.smart_deduction_service import process_recipe_deduction
from app.services.recipe_service import (
    get_recipes,
    get_recipe_by_id,
    create_recipe,
    update_recipe,
    delete_recipe,
    get_recipe_ingredients,
)
from app.services.recipe_matcher import match_user_products_with_recipes
from app.routers.deps import get_current_user

router = APIRouter(prefix="/api/recipes", tags=["Tarif Yönetimi ve Akıllı Eşleştirme"])



@router.get(
    "",
    response_model=List[RecipeResponse],
    summary="Tarifleri listele",
    description="Sistemdeki tüm yemek tariflerini listeler. Tarif adına göre arama yapılabilir."
)
def list_recipes(
    search: Optional[str] = Query(None, description="Tarif adına göre arama"),
    db: Session = Depends(get_db),
):
    """
    Kayıtlı tarifleri döner.
    """
    return get_recipes(db, search=search)


# ==============================================================================
# AKILLI TARİF ÖNERİSİ ENDPOINT'İ (Static path, /{id}'den önce gelmelidir!)
# ==============================================================================

@router.get(
    "/recommendations",
    response_model=List[RecipeRecommendationResponse],
    summary="Kullanıcının kilerine özel tarif önerileri",
    description="Kullanıcının kilerindeki aktif ürünleri analiz eder, malzeme eşleşmelerini ve eksikleri hesaplar. Tarihi yaklaşan (öncelikli) gıdaları kullanan tarifleri en üst sıraya yerleştirir."
)
def get_recipe_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gıda israfını önleyen akıllı tarif öneri motoru.
    - STT tarihi geçmiş gıdalar kesinlikle önerilere dahil edilmez.
    - Kilerdeki öncelikli malzemeler en üstteki tariflere avantaj kazandırır.
    - Kullanıcı izolasyonunu garanti eder.
    """
    return match_user_products_with_recipes(db, user_id=current_user.id)


@router.post(
    "/smart-deduction",
    response_model=RecipeDeductionResponse,
    summary="Yapay Zekâlı Şef Ajan Tarif Onayı ve Akıllı Stok Düşümü",
    description="Şef Ajan'dan gelen tarif onayında belirtilen malzemeleri adet-gram/kg dönüşümleriyle ve ACID transaction bütünlüğünde stoktan düşer."
)
async def smart_deduct_recipe(
    request: RecipeDeductionRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Şef Ajan'ın tarif onayı sonrası (Smart Deduction):
    - Gelen 'adet' talepleri ortalama ağırlık tablosuna göre gram veya kg cinsine çevrilir.
    - Stok 'adet' ama talep 'gr' ise ters dönüşüm yapılır.
    - Kalan miktar tolerans sınırına (<= 0.005) ulaştığında ürün 'CONSUMED' yapılır.
    - Tüm işlem tek bir async transaction (ACID) içinde çalışır.
    """
    return await process_recipe_deduction(
        db=db,
        user_id=current_user.id,
        ingredients=[item.model_dump() for item in request.ingredients],
        recipe_id=request.recipe_id,
    )


# ==============================================================================
# TARİF CRUD ENDPOINT'LERİ
# ==============================================================================


@router.post(
    "",
    response_model=RecipeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni tarif oluştur",
    description="Yeni bir yemek tarifi ve malzemelerini sisteme kaydeder."
)
def add_recipe(
    recipe_in: RecipeCreate,
    db: Session = Depends(get_db),
):
    """
    Yeni tarif oluşturur.
    """
    return create_recipe(db, recipe_in=recipe_in)


@router.get(
    "/{id}",
    response_model=RecipeResponse,
    summary="Tarif detayını getir",
    description="Belirtilen ID'ye sahip tarifin detaylarını ve malzeme listesini getirir."
)
def get_recipe(
    id: int,
    db: Session = Depends(get_db),
):
    """
    Tek bir tarifin detayını döner. Tarif bulunamazsa 404 fırlatır.
    """
    recipe = get_recipe_by_id(db, recipe_id=id)
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{id} ID'li tarif bulunamadı."
        )
    return recipe


@router.put(
    "/{id}",
    response_model=RecipeResponse,
    summary="Tarifi güncelle",
    description="Belirtilen ID'ye sahip tarifin bilgilerini veya malzemelerini günceller."
)
def modify_recipe(
    id: int,
    recipe_in: RecipeUpdate,
    db: Session = Depends(get_db),
):
    """
    Tarifi günceller. Tarif bulunamazsa 404 döner.
    """
    updated = update_recipe(db, recipe_id=id, recipe_in=recipe_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{id} ID'li tarif bulunamadı."
        )
    return updated


@router.delete(
    "/{id}",
    summary="Tarifi sil",
    description="Belirtilen tarifi sistemden kaldırır. Malzemeler otomatik olarak silinir."
)
def remove_recipe(
    id: int,
    db: Session = Depends(get_db),
):
    """
    Tarifi siler. Tarif bulunamazsa 404 döner.
    """
    success = delete_recipe(db, recipe_id=id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{id} ID'li tarif bulunamadı."
        )
    return {"detail": "Tarif başarıyla silindi."}


@router.get(
    "/{id}/ingredients",
    response_model=List[RecipeIngredientResponse],
    summary="Tarifin malzemelerini getir",
    description="Belirtilen tarifin malzeme listesini getirir."
)
def list_recipe_ingredients(
    id: int,
    db: Session = Depends(get_db),
):
    """
    Yalnızca tarifin malzeme listesini döner. Tarif yoksa 404 fırlatır.
    """
    ingredients = get_recipe_ingredients(db, recipe_id=id)
    if ingredients is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{id} ID'li tarif bulunamadı."
        )
    return ingredients
