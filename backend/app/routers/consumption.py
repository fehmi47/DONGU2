from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.consumption import (
    ConsumptionCreate,
    ConsumptionResponse,
    ConsumptionSummaryResponse,
)
from app.services.consumption_service import (
    record_consumption,
    get_user_consumptions,
    get_consumption_by_id,
    calculate_consumption_summary,
)
from app.services.product_service import (
    InsufficientQuantityError,
    ProductNotFoundError,
)
from app.routers.deps import get_current_user

router = APIRouter(prefix="/api/consumption", tags=["Tüketim ve Etki Yönetimi"])


@router.post(
    "",
    response_model=ConsumptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tüketim kaydı oluştur",
    description="Ürünün kısmen veya tamamen tüketildiğini ya da bir tarifte kullanıldığını kaydeder. Miktar kilerden düşülür; 0 olursa durum 'consumed' yapılır."
)
def add_consumption(
    consumption_in: ConsumptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tüketim işlemi kaydeder.
    - Stok yetersizse 400 Bad Request döner.
    - Ürün kullanıcıya ait değilse 404 döner.
    """
    try:
        return record_consumption(db, user_id=current_user.id, consumption_in=consumption_in)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientQuantityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=List[ConsumptionResponse],
    summary="Tüketim geçmişini listele",
    description="Giriş yapan kullanıcının tüm tüketim kayıtlarını en yeniden eskiye sıralı olarak getirir."
)
def list_consumptions(
    limit: int = Query(50, ge=1, le=100, description="Kayıt limiti"),
    offset: int = Query(0, ge=0, description="Başlangıç ötelemesi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Kullanıcının geçmiş tüketimlerini listeler.
    """
    return get_user_consumptions(db, user_id=current_user.id, limit=limit, offset=offset)


@router.get(
    "/summary",
    response_model=ConsumptionSummaryResponse,
    summary="Gıda değerlendirme ve etki paneli özeti",
    description="Toplam değerlendirilen gıda miktarını, haftalık/aylık istatistikleri, kategori dökümünü ve tahmini çevresel kazanımları (CO2 ve su tasarrufu) döner."
)
def get_consumption_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Etki paneli özet verilerini döner.
    """
    return calculate_consumption_summary(db, user_id=current_user.id)


@router.get(
    "/{id}",
    response_model=ConsumptionResponse,
    summary="Tüketim detayını getir",
    description="Belirtilen ID'ye sahip tüketim kaydının detayını döner."
)
def get_consumption(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tek bir tüketim kaydını getirir.
    """
    log = get_consumption_by_id(db, user_id=current_user.id, log_id=id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{id} ID'li tüketim kaydı bulunamadı."
        )
    return log
