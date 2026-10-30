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
        # 1) Ne döner: yapı ve dönemlerin TAM anlamı
        "Kullanıcının kayıtlı tüketim verilerinden istatistik döner. İki bölüm vardır: "
        "'gercek' (toplam, son 7 gün ve son 30 gün kurtarılan kg; tamamlanan tarif sayısı; kategori dökümü) ve "
        "'tahmini' (CO2 ve su). 'tahmini' bölümündeki her değeri söylerken 'tahmini' kelimesini kullan. "
        # 2) Dönem kuralı: takvim ayı ile son 30 gün aynı şey değil
        "Dönemler takvim haftası/ayı değil, kayan pencerelerdir: 'bu ay' sorulursa 'son 30 günde' diye cevap ver. "
        # 3) Ne zaman çağrılır
        "Şu durumlarda çağır: ne kadar gıda kurtardım; kaç tarif tamamladım; en çok hangi kategoriyi tüketiyorum; "
        "çevresel etkim ne. "
        # 4) Ne YAPMAZ: veri olmayan sorularda uydurmayı engeller
        "Bu araçta para (TL) verisi ve atılan/israf edilen ürün kaydı YOKTUR; bunlar sorulursa sistemin "
        "bunu henüz takip etmediğini söyle. 'veri_yok' true ise kullanıcıya tüketim kaydettikçe "
        "istatistiklerin oluşacağını söyle."
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
