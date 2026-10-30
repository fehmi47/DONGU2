"""
DÖNGÜ AI Asistanı - Sıfır Atık ve Geri Dönüşüm Rehberi Aracı

TASARIM KARARI:
- Atığın KATEGORİSİNİ LLM seçer, ama sadece sabit bir listeden (enum).
  LLM "süt kutusu"nun kompozit olduğunu kelime aramasından daha iyi anlar.
- Kutu RENGİ ve İPUÇLARI bu dosyadaki sabit kurallardan gelir.
  LLM renk veya kural üretemez, sadece aktarır.

KAYNAKLAR (renk kodları):
- Sıfır Atık Yönetmeliği'ne ilişkin usul ve esaslar (Ocak 2022)
- Hacettepe Üni. Halk Sağlığı AD, Sıfır Atık bilgilendirme notu
Yayın öncesi sifiratik.gov.tr üzerinden teyit edilmeli.
"""

from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.agents.registry import register

# Kategori anahtarları enum olarak LLM'e gidecek; anahtarları değiştirirsen
# aşağıdaki parametre açıklamasını da güncelle.
RECYCLING_RULES: Dict[str, Dict[str, str]] = {
    "kagit_karton": {
        "kategori": "Kağıt ve karton",
        "kutu_rengi": "Mavi",
        "ipucu": "Gazete, dergi, karton koli, kese kâğıdı. Kolileri katlayıp hacmini küçült. Yağlı veya ıslak kâğıt bu kutuya girmez.",
    },
    "plastik": {
        "kategori": "Plastik",
        "kutu_rengi": "Sarı",
        "ipucu": "Plastik şişeler, yoğurt kapları, deterjan ambalajları. İçini boşaltıp kabaca durula.",
    },
    "cam": {
        "kategori": "Cam",
        "kutu_rengi": "Yeşil",
        "ipucu": "Cam şişe ve kavanozlar. Metal kapağı çıkarıp metale at. Porselen, seramik ve kırık bardak cam kutusuna girmez.",
    },
    "metal": {
        "kategori": "Metal",
        "kutu_rengi": "Gri",
        "ipucu": "Konserve kutuları, içecek kutuları, alüminyum folyo, sıvı yağ tenekeleri. İçini boşalt.",
    },
    "kompozit": {
        "kategori": "Kompozit ambalaj",
        "kutu_rengi": "Turkuaz",
        "ipucu": "Karton süt ve meyve suyu kutuları, karton bardaklar, hazır çorba, kahve, çay ve çikolata ambalajları. Birden fazla malzemenin katmanlı birleşimidir.",
    },
    "organik": {
        "kategori": "Biyobozunur (organik) atık",
        "kutu_rengi": "Kahverengi",
        "ipucu": "Meyve-sebze kabukları ve artıkları, çay ve kahve posası, yemek artıkları. İçine poşet, ambalaj veya sıvı yağ katma.",
    },
    "bitkisel_atik_yag": {
        "kategori": "Bitkisel atık yağ",
        "kutu_rengi": "Koyu mavi",
        "ipucu": "Kızartma ve yemek yağını asla lavaboya dökme. Soğuduktan sonra bir şişede biriktir; belediyenin atık getirme noktasına veya lisanslı toplayıcıya ver.",
    },
    "diger": {
        "kategori": "Diğer (geri dönüştürülemeyen)",
        "kutu_rengi": "Koyu gri",
        "ipucu": "Islak mendil, kirli peçete, seramik ve porselen kırıkları, çok kirlenmiş ambalajlar.",
    },
}

# Çoğu evde 6 ayrı kutu yoktur. Bu not her cevapla birlikte döner ki
# tavsiye gerçek hayatta uygulanabilir olsun.
IKILI_SISTEM_NOTU = (
    "Evinde ayrı renkli kutular yoksa: kağıt, plastik, cam, metal ve kompozit ambalajlar "
    "birlikte mavi geri dönüşüm kutusuna; yemek artıkları kahverengi kutuya (yoksa genel çöpe); "
    "geri kalanı genel çöpe. Atık yağ her durumda ayrı biriktirilir."
)


@register(
    name="get_recycling_guide",
    description=(
        # 1) Ne döner
        "Atıkların Sıfır Atık sistemine göre hangi renk kutuya gideceğini ve ayrıştırma ipuçlarını döner. "
        "Renkler ve ipuçları sabit kurallardan gelir; cevapta bunları AYNEN kullan, araçta olmayan renk veya kural söyleme. "
        "Ayrıca ayrı kutusu olmayan evler için 'genel_not' döner. "
        # 2) Ne zaman çağrılır
        "Şu durumlarda çağır: ambalaj, kabuk, kutu, şişe, yağ veya herhangi bir atığın nereye atılacağı sorulduğunda; "
        "kullanıcı bir yemeği yaptıktan sonra atıkları nasıl ayıracağını sorduğunda. "
        # 3) Nasıl çağrılır
        "Kullanıcı bir yemek adı söylerse (örn. menemen), o yemekten çıkacak atıkları tek tek listele ve her birini kategorize et."
    ),
    parameters={
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "description": "Ayrıştırılacak atıkların listesi. Her atık ayrı bir öğe olmalı.",
                "items": {
                    "type": "object",
                    "properties": {
                        "atik": {
                            "type": "string",
                            "description": "Atığın kısa adı (örn. 'süt kutusu', 'domates kabuğu').",
                        },
                        "kategori": {
                            "type": "string",
                            "enum": list(RECYCLING_RULES.keys()),
                            # Sınıflandırma kılavuzu: LLM'in doğru kategoriyi seçmesi bu metne bağlı
                            "description": (
                                "kagit_karton: gazete, koli, kese kâğıdı, yumurta kolisi. "
                                "plastik: plastik şişe, yoğurt kabı, plastik ambalaj, poşet. "
                                "cam: cam şişe ve kavanoz (porselen ve seramik DEĞİL). "
                                "metal: konserve, içecek kutusu, alüminyum folyo, yağ tenekesi, metal kapak. "
                                "kompozit: karton süt ve meyve suyu kutusu, karton bardak, çay/kahve/çikolata/hazır çorba paketi. "
                                "organik: kabuklar, sebze-meyve artıkları, çay ve kahve posası, yemek artığı, yumurta kabuğu. "
                                "bitkisel_atik_yag: kullanılmış kızartma ve yemek yağı. "
                                "diger: ıslak mendil, kirli peçete, seramik, porselen, kırık bardak. "
                                "Emin değilsen 'diger' seç."
                            ),
                        },
                    },
                    "required": ["atik", "kategori"],
                },
            }
        },
        "required": ["items"],
    },
)
def get_recycling_guide(db: Session, user_id: int, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Her atık için sabit kurallardan kutu rengini ve ipucunu döner."""
    rehber: List[Dict[str, Any]] = []

    for item in items:
        atik = str(item.get("atik", "")).strip()
        kategori = item.get("kategori")

        # Savunmacı kontrol: enum'a rağmen LLM geçersiz bir değer gönderirse
        # çökmek yerine 'diger'e düş ve bunu işaretle.
        gecerli = kategori in RECYCLING_RULES
        kural = RECYCLING_RULES[kategori if gecerli else "diger"]

        rehber.append({
            "atik": atik,
            "kategori": kural["kategori"],
            "kutu_rengi": kural["kutu_rengi"],
            "ipucu": kural["ipucu"],
            "emin_degil": not gecerli,
        })

    return {
        "rehber": rehber,
        "genel_not": IKILI_SISTEM_NOTU,
    }