"""
DÖNGÜ AI Asistanı - Sıfır Atık ve Geri Dönüşüm Rehberi Aracı

Kullanıcının sorduğu atıkların doğru geri dönüşüm kutusuna atılmasını sağlar.
Deterministik kural tabanlı çalışır; LLM tahminine dayanmaz.
"""

from typing import Dict, Any, List, Union
from sqlalchemy.orm import Session

from app.agents.registry import register
from app.agents.tools.recipes import turkish_lower

# Renk kodları Sıfır Atık sistemine göre; yayın öncesi resmi kaynaktan teyit edilmeli.
RECYCLING_RULES: Dict[str, Dict[str, str]] = {
    "cam": {
        "kategori": "Cam",
        "kutu_rengi": "Yeşil",
        "ipucu": "Cam şişe ve kavanozları çalkalayarak atın. Metal ve plastik kapakları kendi ayrı kutularına atın.",
    },
    "plastik": {
        "kategori": "Plastik",
        "kutu_rengi": "Sarı",
        "ipucu": "Şişelerin hacmini sıkıştırarak küçültün. Yağlı veya kirli ambalajları durulamadan atmayın.",
    },
    "metal": {
        "kategori": "Metal",
        "kutu_rengi": "Gri",
        "ipucu": "Konserve kutuları, meşrubat kutuları ve alüminyum tepsiler. İçini temizleyip ezin.",
    },
    "kagit_karton": {
        "kategori": "Kağıt & Karton",
        "kutu_rengi": "Mavi",
        "ipucu": "Temiz ve kuru kağıt/kartonlar. Yağlı pizza kutuları veya ıslak mendiller bu kutuya ATILMAZ.",
    },
    "organik": {
        "kategori": "Organik Atık",
        "kutu_rengi": "Kahverengi",
        "ipucu": "Meyve-sebze kabukları, çay posası ve yemek artıkları. Plastik poşetsiz atılmalı veya kompost yapılmalıdır.",
    },
    "diger": {
        "kategori": "Diğer / Genel Çöp",
        "kutu_rengi": "Siyah",
        "ipucu": "Geri dönüştürülemeyen kirli peçeteler, yağlı ambalajlar, porselen ve hijyenik atıklar.",
    },
}

# Malzeme anahtar kelimelerini kategorilere eşleme haritası
KEYWORD_MAPPING: Dict[str, str] = {
    # Cam
    "cam": "cam",
    "şişe": "cam",
    "kavanoz": "cam",
    "kadeh": "cam",
    # Plastik
    "plastik": "plastik",
    "pet": "plastik",
    "poşet": "plastik",
    "yoğurt": "plastik",
    "ambalaj": "plastik",
    "naylon": "plastik",
    # Metal
    "metal": "metal",
    "konserve": "metal",
    "kola": "metal",
    "meşrubat": "metal",
    "teneke": "metal",
    "alüminyum": "metal",
    "folyo": "metal",
    # Kağıt / Karton
    "kagit": "kagit_karton",
    "kağıt": "kagit_karton",
    "karton": "kagit_karton",
    "koli": "kagit_karton",
    "gazete": "kagit_karton",
    "dergi": "kagit_karton",
    "kitap": "kagit_karton",
    # Organik
    "organik": "organik",
    "kabuk": "organik",
    "kabuğ": "organik",
    "muz": "organik",
    "elma": "organik",
    "domates": "organik",
    "patates": "organik",
    "soğan": "organik",
    "çay": "organik",
    "kahve": "organik",
    "posa": "organik",
    "artık": "organik",
    "yemek": "organik",
    "ekmek": "organik",
    "meyve": "organik",
    "sebze": "organik",
    "yumurta": "organik",
}


@register(
    name="get_recycling_guide",
    description=(
        "Belirtilen atık maddelerinin Sıfır Atık standartlarına göre hangi renk geri dönüşüm kutusuna "
        "atılacağını ve ayrıştırma ipuçlarını verir. "
        "Kullanıcı atıkların, ambalajların veya çöplerin nasıl ayrıştırılacağını sorduğunda kullanılır."
    ),
    parameters={
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "description": "Ayrıştırma kuralı sorgulanacak atık adları veya kategorileri (örn: ['cam', 'plastik'] veya ['muz kabuğu', 'konserve kutusu']).",
                "items": {"type": "string"},
            }
        },
        "required": ["items"],
    },
)
def get_recycling_guide(
    db: Session,
    user_id: int,
    items: List[Union[str, Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Verilen atık öğeleri için deterministik kurallara göre kutu rengi ve ipuçlarını döner.
    """
    rehber_sonuclari: List[Dict[str, Any]] = []

    for raw_item in items:
        # Metin veya sözlük formatını destekle
        if isinstance(raw_item, dict):
            item_text = raw_item.get("name") or raw_item.get("kategori") or raw_item.get("item") or ""
        else:
            item_text = str(raw_item)

        item_norm = turkish_lower(item_text.strip())
        matched_category = None

        # Doğrudan kategori anahtarı mı?
        if item_norm in RECYCLING_RULES:
            matched_category = item_norm
        else:
            # Anahtar kelime taraması
            for kw, cat in KEYWORD_MAPPING.items():
                if kw in item_norm:
                    matched_category = cat
                    break

        if not matched_category:
            matched_category = "diger"

        rule = RECYCLING_RULES[matched_category]
        rehber_sonuclari.append({
            "atik": item_text,
            "kategori": rule["kategori"],
            "kutu_rengi": rule["kutu_rengi"],
            "ipucu": rule["ipucu"],
        })

    return {
        "rehber": rehber_sonuclari,
        "kural_sayisi": len(rehber_sonuclari),
        "not": "Renk kodları Sıfır Atık sistemine göre belirlenmiştir.",
    }
