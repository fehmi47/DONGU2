"""
DÖNGÜ AI Asistanı - Tüketim ve Çevresel Etki İstatistikleri Aracı

Kullanıcının kurtardığı gıda miktarlarını ve çevresel tasarruf verilerini getirir.
Salt-okunur (read-only) çalışır; veritabanında kesinlikle değişiklik yapmaz.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session

from app.agents.registry import register
from app.services.consumption_service import calculate_consumption_summary


@register(
    name="get_consumption_stats",
    description=(
        "Kullanıcının bugüne kadar değerlendirdiği/kurtardığı gerçek gıda miktarlarını, tamamladığı tarif sayısını "
        "ve bunlara bağlı hesaplanan tahmini çevresel kazanımları (CO2 ve su tasarrufu) getirir. "
        "Kullanıcı ne kadar gıda kurtardığını veya ne kadar tasarruf sağladığını sorduğunda çağrılmalıdır."
    ),
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def get_consumption_stats(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Kullanıcının tüketim istatistiklerini hesaplar ve döner.
    
    Kurallar:
    - Sonuç iki ayrı anahtarla döner: 'gercek' (ölçülen kg ve tarif sayıları) ve 'tahmini' (çevresel modeller).
    - Asistan bu verileri kullanırken tahmini olanlar için mutlaka 'tahmini' ifadesini kullanır.
    """
    summary = calculate_consumption_summary(db=db, user_id=user_id)

    gercek_veriler = {
        "toplam_kurtarilan_kg": float(summary.total_evaluated_kg),
        "haftalik_kurtarilan_kg": float(summary.weekly_evaluated_kg),
        "aylik_kurtarilan_kg": float(summary.monthly_evaluated_kg),
        "tamamlanan_tarif_sayisi": int(summary.completed_recipes_count),
        "toplam_kayit_sayisi": int(summary.total_logs_count),
        "kategori_bazli_kurtarilan": [
            {
                "kategori": item.category_name,
                "miktar_kg": float(item.total_quantity_kg),
                "islem_sayisi": int(item.log_count),
            }
            for item in summary.category_breakdown
        ],
    }

    tahmini_veriler = {
        "tahmini_onlenen_co2_kg": float(summary.environmental_impact.estimated_co2_saved_kg),
        "tahmini_tasarruf_su_litre": float(summary.environmental_impact.estimated_water_saved_liters),
        "hesaplama_notu": "Bu değerler değerlendirilen gıdaların standart karbon ve su ayak izi katsayılarına göre hesaplanmış tahmini verilerdir.",
    }

    return {
        "gercek": gercek_veriler,
        "tahmini": tahmini_veriler,
    }
