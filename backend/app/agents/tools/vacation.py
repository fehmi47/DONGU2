"""
DÖNGÜ AI Asistanı - Tatil Öncesi Kurtarma Modu Aracı

Kullanıcının tatil veya uzun süreli seyahat tarihleri boyunca mutfağındaki
gıdaları korumak ve israfı önlemek için tamamen deterministik bir plan çıkarır.
Salt-okunur çalışır; veritabanında kesinlikle değişiklik yapmaz.
"""

from datetime import date, datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.agents.registry import register
from app.services.priority_service import get_user_products_with_priority
from app.agents.tools.kitchen import TETT_GECMIS_NOTU, STT_GECMIS_NOTU
from app.agents.tools.recipes import turkish_lower

# Genel saklama önerisidir; ürün bazlı istisnalar için ambalaj talimatı esas alınır.
DONDURULABILIR_KATEGORILER: Dict[str, str] = {
    "ekmek ve unlu mamuller": "Dondur",
    "et, tavuk ve balık": "Dondur",
    "et, tavuk ve yumurta": "Dondur",
    "tahıl ve unlu mamuller": "Dondur",
    "dondurulmuş ürünler": "Dondur",
}
VARSAYILAN_TATILDE_EYLEM = "Gitmeden tüket veya paylaş"


def _eylem_belirle(urun_adi: Optional[str], kategori_adi: Optional[str]) -> str:
    """
    Tatilde bozulacak bir ürün için eylemi deterministik olarak belirler.
    Belirlenen dondurulabilir kategorilerdeki ürünler için 'Dondur',
    diğer tüm kategoriler için 'Gitmeden tüket veya paylaş' döner.
    """
    kategori = turkish_lower(kategori_adi or "")

    for kat, eylem in DONDURULABILIR_KATEGORILER.items():
        if kat in kategori or (kategori and kategori in kat):
            return eylem

    return VARSAYILAN_TATILDE_EYLEM


@register(
    name="get_vacation_rescue_plan",
    description=(
        "Kullanıcının tatil veya seyahat tarihleri boyunca mutfağındaki gıdaları korumak için "
        "deterministik kurtarma planı çıkarır. Ürünleri dört ana gruba ayırır: "
        "'tatilden_once_bitmeli' (tatile çıkmadan dolanlar -> 'Gitmeden tüket'), "
        "'tatilde_bozulacak' (tatil sürecinde dolacaklar -> araçtan gelen eylem), "
        "'guvende' (tatil dönüşü sonrasına kalan güvenli ürünlerin sayısı) ve "
        "'tarihsiz' (tarihi olmayanlar -> 'Gitmeden kontrol et'). "
        "STT'si geçmiş ürünler hiçbir gruba dahil edilmez, ayrı 'tarihi_gecmis' listesinde sadece ad olarak verilir. "
        "Şu durumlarda çağır: tatile çıkma, seyahate gitme, uzun süre evde olmama ve "
        "'şu tarihte gidip şu tarihte döneceğim' soruları. "
        "Tarihleri mutlaka YYYY-AA-GG formatında gönder. Kullanıcı göreli süre verirse ('yarın gidiyorum, 1 hafta yokum') "
        "bugünün tarihine göre start_date ve end_date'i kendin hesapla. "
        "Eylemleri ARAÇTAN AYNEN kullanıcıya aktar, kendi saklama/dondurma tavsiyeni uydurma. "
        "Bu araç stokta değişiklik yapmaz."
    ),
    parameters={
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "description": "Tatile veya seyahate çıkış tarihi (YYYY-AA-GG formatında, örn: '2026-07-15').",
            },
            "end_date": {
                "type": "string",
                "description": "Tatilden veya seyahatten dönüş tarihi (YYYY-AA-GG formatında, örn: '2026-07-22').",
            },
        },
        "required": ["start_date", "end_date"],
    },
)
def get_vacation_rescue_plan(
    db: Session,
    user_id: int,
    start_date: str,
    end_date: str,
    reference_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Kullanıcının tatil tarihleri aralığında mutfak envanterini inceleyerek
    gıda israfını önleme planı hazırlar.

    Args:
        db: Aktif veritabanı oturumu
        user_id: Kullanıcı ID'si
        start_date: Tatil başlangıç tarihi (YYYY-AA-GG)
        end_date: Tatil bitiş tarihi (YYYY-AA-GG)
        reference_date: Testler için sabit referans tarihi (varsayılan: date.today())

    Returns:
        Hata durumunda {"hata": "..."}, başarılıysa kurtarma planı dict nesnesi.
    """
    bugun = reference_date or date.today()

    # 1. Doğrulama: Tarih formatı (YYYY-AA-GG) kontrolü
    try:
        s_date = datetime.strptime(start_date.strip(), "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date.strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError, AttributeError):
        return {
            "hata": "Tarih formatı geçersiz. Lütfen tarihleri YYYY-AA-GG (örn: 2026-07-15) formatında belirtin."
        }

    # 2. Doğrulama: end_date <= start_date kontrolü
    if e_date <= s_date:
        return {
            "hata": "Dönüş tarihi (end_date), tatile çıkış tarihinden (start_date) sonra olmalıdır."
        }

    # 3. Doğrulama: start_date bugünden önce olamaz
    if s_date < bugun:
        return {
            "hata": "Tatile çıkış tarihi (start_date) bugünden önceki bir tarih olamaz."
        }

    # 4. Doğrulama: Tatil 60 günden uzun olamaz
    tatil_gun = (e_date - s_date).days
    if tatil_gun > 60:
        return {
            "hata": "Tatil planı 60 günden uzun olamaz."
        }

    # 5. Mevcut servisten kullanıcının ürünlerini al (yeni sorgu yazılmadı)
    evaluated_items = get_user_products_with_priority(db=db, user_id=user_id, reference_date=bugun)

    tatilden_once_bitmeli: List[Dict[str, Any]] = []
    tatilde_bozulacak: List[Dict[str, Any]] = []
    guvende_sayisi: int = 0
    tarihsiz: List[Dict[str, Any]] = []
    tarihi_gecmis: List[Dict[str, str]] = []

    for item in evaluated_items:
        # Kural: STT'si zaten geçmiş ürünleri hiçbir ana gruba koyma; ayrı listede sadece ad olarak ver
        if not item.can_be_recommended:
            tarihi_gecmis.append({
                "ad": item.name,
                "uyari": STT_GECMIS_NOTU,
            })
            continue

        # Miktar biçimlendirme (3.0 yerine 3 görünsün)
        qty = float(item.quantity) if item.quantity is not None else 0.0
        if qty.is_integer():
            qty = int(qty)

        # TETT ürünlerine mevcut TETT notu mantığını uygula (varsa uyarı)
        uyari = None
        if item.date_type == "TETT" and item.days_remaining is not None and item.days_remaining < 0:
            uyari = TETT_GECMIS_NOTU

        # Kategori adını güvenle al
        cat_name = item.category.name if item.category and hasattr(item.category, "name") else ""

        # Grup 4: Tarihsiz ürünler -> Eylem: "Gitmeden kontrol et"
        if item.date_type == "NONE" or item.expiry_date is None:
            tarihsiz.append({
                "ad": item.name,
                "miktar": qty,
                "birim": item.unit,
                "tarih_tipi": item.date_type,
                "tarihe_kalan_gun": item.days_remaining,
                "kalan_gun": item.days_remaining,
                "eylem": "Gitmeden kontrol et",
                "uyari": uyari,
            })
            continue

        # Grup 1: Tarihi start_date'ten ÖNCE dolan ürünler -> Eylem: "Gitmeden tüket"
        if item.expiry_date < s_date:
            tatilden_once_bitmeli.append({
                "ad": item.name,
                "miktar": qty,
                "birim": item.unit,
                "tarih_tipi": item.date_type,
                "tarihe_kalan_gun": item.days_remaining,
                "kalan_gun": item.days_remaining,
                "eylem": "Gitmeden tüket",
                "uyari": uyari,
            })
        # Grup 2: Tarihi tatil süresince dolan ürünler -> Eylem: ürün adı + kategoriye göre
        elif s_date <= item.expiry_date <= e_date:
            eylem = _eylem_belirle(item.name, cat_name)
            tatilde_bozulacak.append({
                "ad": item.name,
                "miktar": qty,
                "birim": item.unit,
                "tarih_tipi": item.date_type,
                "tarihe_kalan_gun": item.days_remaining,
                "kalan_gun": item.days_remaining,
                "eylem": eylem,
                "uyari": uyari,
            })
        # Grup 3: Tarihi dönüşten sonra dolan ürünler -> SADECE sayısını dön
        else:
            guvende_sayisi += 1

    return {
        "tatil_gun_sayisi": tatil_gun,
        "tatilden_once_bitmeli": tatilden_once_bitmeli,
        "tatilde_bozulacak": tatilde_bozulacak,
        "guvende": guvende_sayisi,
        "tarihsiz": tarihsiz,
        "tarihi_gecmis": tarihi_gecmis,
        "ozet": {
            "tatilden_once_bitmeli": len(tatilden_once_bitmeli),
            "tatilde_bozulacak": len(tatilde_bozulacak),
            "guvende": guvende_sayisi,
            "tarihsiz": len(tarihsiz),
            "tarihi_gecmis": len(tarihi_gecmis),
        },
        "sonraki_adim": "'tatilden_once_bitmeli' ve 'tatilde_bozulacak' gruplarındaki ürünler için search_recipes ile tarif önerilebilir.",
    }