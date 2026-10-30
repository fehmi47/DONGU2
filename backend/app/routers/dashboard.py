from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import get_dashboard_summary
from app.routers.deps import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Kontrol Paneli (Dashboard)"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Dashboard özet verilerini getir",
    description="Aktif ürün sayılarını, yaklaşan STT/TETT sayılarını, öncelik durumlarını, haftalık tüketim trendini, kategori dağılımını ve çevresel fayda analizini tek seferde getirir."
)
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Oturum açmış kullanıcıya ait ana kontrol paneli verilerini döner.
    """
    return get_dashboard_summary(db, user_id=current_user.id)
