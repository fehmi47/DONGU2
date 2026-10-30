"""
DÖNGÜ AI Asistanı - Mutfak ve Ürün Araçları

Kullanıcının aktif ürünlerini ve tüketim önceliklerini listeler.
Salt-okunur (read-only) çalışır; veritabanında kesinlikle değişiklik yapmaz.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.agents.registry import register
from app.services.priority_service import get_user_products_with_priority

# Sabit gıda güvenliği uyarı metinleri (LLM'in kendi yorumunu yapmasını engellemek için)
TETT_GECMIS_NOTU = "Tavsiye edilen tüketim tarihi geçmiş. Kalitesi düşmüş olabilir; tüketmeden önce ürünü kontrol et."
STT_GECMIS_NOTU = "Son tüketim tarihi geçmiş. Tüketim için önerilmez."


@register(
    name="get_priority_products",
    # Açıklamanın 3 görevi var: (1) aracın ne döndüğünü anlatmak,
    # (2) NE ZAMAN çağrılacağını söylemek, (3) ne YAPMADIĞINI söylemek.
    # LLM araç seçimini neredeyse tamamen bu metne bakarak yapar.
    description=(
        # 1) Ne döner: alan adları koddakilerle birebir aynı olmalı
        "Kullanıcının mutfağındaki aktif ürünleri tüketim önceliğine göre sıralı döner (en fazla 10). "
        "Her üründe: ad, miktar, birim, tarih tipi (STT/TETT), kalan gün, aciliyet (yuksek/orta/dusuk) "
        "ve varsa 'uyari' metni bulunur. Son tüketim tarihi geçmiş ürünler ayrı bir "
        "'tarihi_gecmis_stt' listesinde yalnızca ad olarak gelir; bunları asla önerme. "
        # 2) Ne zaman çağrılır: system prompt'taki strateji ile aynı
        "Şu durumlarda çağır: bugün/bu hafta ne tüketilmeli; hangi ürünler bozulmak üzere; "
        "belirli bir ürünün durumu, miktarı veya kalan günü; belirli bir ürünle tarif aramadan önce "
        "o ürünün mutfakta olup olmadığını kontrol etmek. "
        # 3) Ne yapmaz: LLM'in bu araçtan yanlış beklentiye girmesini engeller
        "Bu araç tarif döndürmez ve stokta değişiklik yapmaz."
    ),
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def get_priority_products(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Kullanıcının ürünlerini öncelik sırasına göre hesaplayarak döner.
    
    Kurallar:
    - can_be_recommended=False olan (STT'si geçmiş) ürünler ayrı bir 'tarihi_gecmis_stt' listesinde ad ve sabit uyarıyla verilir.
    - 'oncelikli_urunler' listesinde en fazla 10 ürün yer alır.
    - Tarihi geçmiş veya TETT dolmuş ürünler için sabit 'uyari' metinleri atanır.
    """
    evaluated_items = get_user_products_with_priority(db=db, user_id=user_id)

    tarihi_gecmis_stt: List[Dict[str, str]] = []
    oncelikli_urunler: List[Dict[str, Any]] = []

    for item in evaluated_items:
        # Pydantic modelinden güvenli veri çıkarma
        if not item.can_be_recommended:
            tarihi_gecmis_stt.append({
                "ad": item.name,
                "uyari": STT_GECMIS_NOTU,
            })
        else:
            if len(oncelikli_urunler) < 10:
                qty = float(item.quantity) if item.quantity is not None else 0.0
                if qty.is_integer():
                    qty = int(qty)

                # Sabit güvenlik uyarı kontrolü
                uyari = None
                if item.date_type == "TETT" and item.days_remaining is not None and item.days_remaining < 0:
                    uyari = TETT_GECMIS_NOTU

                oncelikli_urunler.append({
                    "ad": item.name,
                    "miktar": qty,
                    "birim": item.unit,
                    "tarih_tipi": item.date_type,
                    "kalan_gun": item.days_remaining,
                    "oncelik_seviyesi": item.priority_level,
                    "uyari": uyari,
                })

    return {
        "oncelikli_urunler": oncelikli_urunler,
        "tarihi_gecmis_stt": [x["ad"] for x in tarihi_gecmis_stt],
        "tarihi_gecmis_stt_detay": tarihi_gecmis_stt,
        "toplam_guvenli_urun": len(oncelikli_urunler),
    }
