import re
from decimal import Decimal
from typing import Dict, Optional, Union

# ==============================================================================
# ORTALAMA BİRİM AĞIRLIK VE HACİM TABLOLARI (GRAM / ML CİNSİNDEN)
# ==============================================================================

# 1. Adet Bazlı Ürünlerin Ortalama Birim Ağırlıkları (Gram)
AVERAGE_PIECE_WEIGHTS_GR: Dict[str, int] = {
    # Sebzeler
    "domates": 150,
    "soğan": 120,
    "sogan": 120,
    "patates": 200,
    "limon": 100,
    "yumurta": 50,
    "sarımsak": 5,
    "sarimsak": 5,
    "biber": 40,
    "yeşil biber": 30,
    "yesil biber": 30,
    "kapya biber": 70,
    "havuç": 100,
    "havuc": 100,
    "salatalık": 120,
    "salatalik": 120,
    "patlıcan": 200,
    "patlican": 200,
    "kabak": 250,
    "mantar": 20,
    "avokado": 170,
    "enginar": 200,
    "kereviz": 300,
    "pırasa": 150,
    "pirasa": 150,

    # Meyveler
    "elma": 180,
    "armut": 180,
    "muz": 150,
    "portakal": 200,
    "mandalina": 80,
    "şeftali": 150,
    "seftali": 150,
    "çilek": 20,
    "cilek": 20,
    "erik": 35,
    "kivi": 100,

    # Unlu & Temel Gıdalar
    "ekmek": 250,
    "yufka": 150,
    "simit": 100,
    "lavaş": 60,
    "lavas": 60,
}
DEFAULT_PIECE_WEIGHT_GR = 100  # Bilinmeyen adet ürünleri için varsayılan ağırlık


# 2. Yemek Kaşığı Ortalama Ağırlıkları (Gram)
# 1 standart yemek kaşığı pirinç ~20g, un ~15g, yağ ~15g vb.
SPOON_WEIGHTS_GR: Dict[str, int] = {
    # Bakliyat & Tahıl
    "pirinç": 20,
    "pirinc": 20,
    "bulgur": 20,
    "mercimek": 20,
    "kırmızı mercimek": 20,
    "yeşil mercimek": 20,
    "nohut": 20,
    "fasulye": 20,
    "makarna": 15,
    "şehriye": 15,
    "sehriye": 15,
    "arpa şehriye": 15,
    "tel şehriye": 15,
    "yulaf": 12,

    # Un, Şeker, Tuz & Kuru Malzemeler
    "un": 15,
    "buğday unu": 15,
    "şeker": 20,
    "seker": 20,
    "toz şeker": 20,
    "pudra şekeri": 15,
    "tuz": 18,
    "kaya tuzu": 18,
    "tarhana": 15,
    "irmik": 15,
    "nişasta": 12,
    "nisasta": 12,
    "kakao": 10,
    "kahve": 10,
    "karbonat": 10,
    "kabartma tozu": 10,

    # Yağlar
    "zeytinyağı": 15,
    "zeytinyagi": 15,
    "sıvı yağ": 15,
    "sivi yag": 15,
    "ayçiçek yağı": 15,
    "aycicek yagi": 15,
    "yağ": 15,
    "yag": 15,
    "tereyağı": 15,
    "tereyagi": 15,
    "margarin": 15,

    # Soslar, Salçalar ve Süt Ürünleri
    "salça": 25,
    "salca": 25,
    "domates salçası": 25,
    "biber salçası": 25,
    "yoğurt": 25,
    "yogurt": 25,
    "süzme yoğurt": 25,
    "bal": 25,
    "pekmez": 25,
    "tahin": 20,
    "sirke": 15,
    "limon suyu": 15,
    "hardal": 18,
    "mayonez": 18,
    "ketçap": 20,
    "ketcap": 20,
    "süt": 15,
    "sut": 15,
    "su": 15,

    # Baharatlar (Kurutulmuş otlar ve toz baharatlar)
    "karabiber": 10,
    "pul biber": 10,
    "kırmızı biber": 10,
    "kekik": 8,
    "nane": 8,
    "kuru nane": 8,
    "kimyon": 10,
    "sumak": 10,
    "tarçın": 10,
    "tarcin": 10,
    "zencefil": 10,
    "zerdeçal": 10,
    "zerdecal": 10,
    "baharat": 10,
}
DEFAULT_SPOON_WEIGHT_GR = 15  # Varsayılan yemek kaşığı 15 gram


# 3. Su Bardağı Ortalama Ağırlıkları (Gram / ML)
# 1 standart su bardağı ~200 ml / 200 gram
CUP_WEIGHTS_GR: Dict[str, int] = {
    "un": 130,
    "şeker": 190,
    "seker": 190,
    "pirinç": 180,
    "pirinc": 180,
    "bulgur": 170,
    "mercimek": 180,
    "kırmızı mercimek": 180,
    "nohut": 170,
    "fasulye": 170,
    "yulaf": 100,
    "sıvı yağ": 180,
    "sivi yag": 180,
    "zeytinyağı": 180,
    "zeytinyagi": 180,
    "yoğurt": 220,
    "yogurt": 220,
    "süt": 200,
    "sut": 200,
    "su": 200,
    "sirke": 200,
    "meyve suyu": 200,
}
DEFAULT_CUP_WEIGHT_GR = 200  # Varsayılan su bardağı 200 gram


# 4. Diğer Mutfak Ölçüleri Sabitleri
DEFAULT_TEA_SPOON_WEIGHT_GR = 5     # Çay kaşığı 5 gram
DEFAULT_DESSERT_SPOON_WEIGHT_GR = 10  # Tatlı kaşığı 10 gram
DEFAULT_TEA_CUP_WEIGHT_GR = 100     # Çay bardağı 100 gram / ml
DEFAULT_COFFEE_CUP_WEIGHT_GR = 75   # Kahve fincanı 75 gram / ml
DEFAULT_BUNCH_WEIGHT_GR = 100       # Demet (maydanoz, dereotu vb.) 100 gram
DEFAULT_SLICE_WEIGHT_GR = 30        # Dilim (ekmek, peynir vb.) 30 gram
DEFAULT_PACK_WEIGHT_GR = 400        # Paket / kutu 400 gram
DEFAULT_JAR_WEIGHT_GR = 500         # Kavanoz 500 gram
DEFAULT_PORTION_WEIGHT_GR = 250     # Porsiyon 250 gram


# ==============================================================================
# METİN VE BİRİM NORMALİZASYONU
# ==============================================================================

def normalize_string(text: str) -> str:
    """Metni küçük harfe ve Türkçe karakter eşleniklerine göre temizler."""
    if not text:
        return ""
    t = text.strip().lower()
    mapping = {
        "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u", "İ": "i", "I": "i"
    }
    for tr, en in mapping.items():
        t = t.replace(tr, en)
    # Noktalama işaretlerini ve fazla boşlukları temizle
    t = re.sub(r"[^\w\s]", " ", t)
    return " ".join(t.split())


def normalize_unit(unit_str: str) -> str:
    """
    Birim adını standart sisteme normalize eder.
    Kabul edilen standart birimler:
    - Kütle: 'gr', 'kg'
    - Hacim: 'ml', 'l'
    - Kaşık: 'kaşık', 'tatlı kaşığı', 'çay kaşığı'
    - Bardak: 'bardak', 'çay bardağı', 'fincan'
    - Sayı / Porsiyon: 'adet', 'demet', 'dilim', 'paket', 'kutu', 'kavanoz', 'porsiyon'
    """
    if not unit_str:
        return "adet"

    u = normalize_string(unit_str)

    # 1. Kütle
    if u in ["g", "gr", "gram", "grams", "gramm"]:
        return "gr"
    if u in ["kg", "kilo", "kilogram", "kilograms"]:
        return "kg"

    # 2. Hacim
    if u in ["ml", "mililitre", "milliliter"]:
        return "ml"
    if u in ["l", "lt", "litre", "liter", "liters"]:
        return "l"

    # 3. Kaşık Çeşitleri
    if u in ["cay kasigi", "ck", "tsp", "teaspoon"]:
        return "çay kaşığı"
    if u in ["tatli kasigi", "tk", "dessert spoon"]:
        return "tatlı kaşığı"
    if u in [
        "kasik", "yemek kasigi", "yk", "corba kasigi",
        "spoon", "tbsp", "tablespoon"
    ]:
        return "kaşık"

    # 4. Bardak & Fincan
    if u in ["cay bardagi", "cb"]:
        return "çay bardağı"
    if u in ["fincan", "kahve fincani"]:
        return "fincan"
    if u in ["bardak", "su bardagi", "sb", "cup", "kupa"]:
        return "bardak"

    # 5. Parça / Adet / Paket
    if u in ["adet", "tane", "ad", "piece", "pieces"]:
        return "adet"
    if u in ["demet", "bunch"]:
        return "demet"
    if u in ["dilim", "slice", "slices"]:
        return "dilim"
    if u in ["paket", "pkt", "pack", "packet"]:
        return "paket"
    if u in ["kutu", "can", "box"]:
        return "kutu"
    if u in ["kavanoz", "jar"]:
        return "kavanoz"
    if u in ["porsiyon", "portion"]:
        return "porsiyon"

    return u


# ==============================================================================
# MALZEMEYE ÖZEL AĞIRLIK BULUCULAR
# ==============================================================================

def get_piece_weight_gr(item_name: str, fallback_default: bool = False) -> Optional[int]:
    """Malzeme adına göre 1 adet ağırlığını gram cinsinden döner."""
    if not item_name:
        return DEFAULT_PIECE_WEIGHT_GR if fallback_default else None

    norm = normalize_string(item_name)
    # 1. Tam eşleşme
    for key, weight in AVERAGE_PIECE_WEIGHTS_GR.items():
        if normalize_string(key) == norm:
            return weight

    # 2. Alt dize eşleşmesi (Örn: "salkım domates" -> "domates")
    for key, weight in AVERAGE_PIECE_WEIGHTS_GR.items():
        key_norm = normalize_string(key)
        if key_norm in norm or norm in key_norm:
            return weight

    return DEFAULT_PIECE_WEIGHT_GR if fallback_default else None


def get_spoon_weight_gr(item_name: str) -> int:
    """Malzeme adına göre 1 yemek kaşığı ağırlığını gram cinsinden döner."""
    if not item_name:
        return DEFAULT_SPOON_WEIGHT_GR

    norm = normalize_string(item_name)
    # 1. Tam eşleşme
    for key, weight in SPOON_WEIGHTS_GR.items():
        if normalize_string(key) == norm:
            return weight

    # 2. Alt dize eşleşmesi (Örn: "baldo pirinç" -> "pirinç", "sızma zeytinyağı" -> "zeytinyağı")
    for key, weight in SPOON_WEIGHTS_GR.items():
        key_norm = normalize_string(key)
        if key_norm in norm or norm in key_norm:
            return weight

    return DEFAULT_SPOON_WEIGHT_GR


def get_cup_weight_gr(item_name: str) -> int:
    """Malzeme adına göre 1 su bardağı ağırlığını gram cinsinden döner."""
    if not item_name:
        return DEFAULT_CUP_WEIGHT_GR

    norm = normalize_string(item_name)
    # 1. Tam eşleşme
    for key, weight in CUP_WEIGHTS_GR.items():
        if normalize_string(key) == norm:
            return weight

    # 2. Alt dize eşleşmesi
    for key, weight in CUP_WEIGHTS_GR.items():
        key_norm = normalize_string(key)
        if key_norm in norm or norm in key_norm:
            return weight

    return DEFAULT_CUP_WEIGHT_GR


# ==============================================================================
# EVRENSEL BİRİM DÖNÜŞTÜRÜCÜ MOTOR (UNIVERSAL UNIT CONVERTER)
# ==============================================================================

def convert_unit(
    quantity: Union[Decimal, float, int, str],
    from_unit: str,
    to_unit: str,
    item_name: str = ""
) -> Decimal:
    """
    Herhangi bir kaynak birimdeki gıda miktarını, hedef stok veya tarif birimine
    malzeme yoğunluğunu ve mutfak standartlarını gözeterek dönüştürür.
    
    Örnekler:
    - 3 kaşık Pirinç -> kg = 0.06 kg (3 * 20 gr = 60 gr = 0.06 kg)
    - 1 kaşık Un -> kg = 0.015 kg (1 * 15 gr = 15 gr = 0.015 kg)
    - 1 su bardağı Un -> gr = 130 gr
    - 150 gr Domates -> adet = 1 adet
    - 2 adet Yumurta -> gr = 100 gr
    - 500 gr Yoğurt -> kg = 0.50 kg
    """
    qty = Decimal(str(quantity))
    if qty == 0:
        return Decimal("0.00")

    u_from = normalize_unit(from_unit)
    u_to = normalize_unit(to_unit)

    # 1. Birebir aynı birim
    if u_from == u_to:
        return qty

    # 2. Doğrudan standart metrik dönüşümler (Adım atlamadan hassas işlem)
    if u_from == "gr" and u_to == "kg":
        return qty / Decimal("1000")
    if u_from == "kg" and u_to == "gr":
        return qty * Decimal("1000")
    if u_from == "ml" and u_to == "l":
        return qty / Decimal("1000")
    if u_from == "l" and u_to == "ml":
        return qty * Decimal("1000")

    # 3. Adım 1: Kaynak birimi GRAM (veya sıvı için ML) tabanına çevir
    base_grams: Decimal

    if u_from == "gr":
        base_grams = qty
    elif u_from == "kg":
        base_grams = qty * Decimal("1000")
    elif u_from == "ml":
        base_grams = qty  # 1 ml ~ 1 gr
    elif u_from == "l":
        base_grams = qty * Decimal("1000")
    elif u_from == "kaşık":
        spoon_weight = Decimal(str(get_spoon_weight_gr(item_name)))
        base_grams = qty * spoon_weight
    elif u_from == "tatlı kaşığı":
        base_grams = qty * Decimal(str(DEFAULT_DESSERT_SPOON_WEIGHT_GR))
    elif u_from == "çay kaşığı":
        base_grams = qty * Decimal(str(DEFAULT_TEA_SPOON_WEIGHT_GR))
    elif u_from == "bardak":
        cup_weight = Decimal(str(get_cup_weight_gr(item_name)))
        base_grams = qty * cup_weight
    elif u_from == "çay bardağı":
        base_grams = qty * Decimal(str(DEFAULT_TEA_CUP_WEIGHT_GR))
    elif u_from == "fincan":
        base_grams = qty * Decimal(str(DEFAULT_COFFEE_CUP_WEIGHT_GR))
    elif u_from == "demet":
        base_grams = qty * Decimal(str(DEFAULT_BUNCH_WEIGHT_GR))
    elif u_from == "dilim":
        base_grams = qty * Decimal(str(DEFAULT_SLICE_WEIGHT_GR))
    elif u_from in ["paket", "kutu"]:
        base_grams = qty * Decimal(str(DEFAULT_PACK_WEIGHT_GR))
    elif u_from == "kavanoz":
        base_grams = qty * Decimal(str(DEFAULT_JAR_WEIGHT_GR))
    elif u_from == "porsiyon":
        base_grams = qty * Decimal(str(DEFAULT_PORTION_WEIGHT_GR))
    elif u_from == "adet":
        pw = get_piece_weight_gr(item_name, fallback_default=False)
        if pw is None:
            raise ValueError(
                f"'{item_name}' malzemesi için ortalama birim ağırlık (AVERAGE_UNIT_WEIGHTS_GR) bulunamadı. Lütfen gram cinsinden talep edin."
            )
        base_grams = qty * Decimal(str(pw))
    else:
        # Bilinmeyen birimlerde varsayılan tolerans
        base_grams = qty * Decimal("100")

    # 4. Adım 2: GRAM tabanındaki değeri HEDEF birime çevir
    if u_to == "gr":
        return base_grams
    elif u_to == "kg":
        return base_grams / Decimal("1000")
    elif u_to == "ml":
        return base_grams
    elif u_to == "l":
        return base_grams / Decimal("1000")
    elif u_to == "kaşık":
        spoon_weight = Decimal(str(get_spoon_weight_gr(item_name)))
        return base_grams / spoon_weight
    elif u_to == "tatlı kaşığı":
        return base_grams / Decimal(str(DEFAULT_DESSERT_SPOON_WEIGHT_GR))
    elif u_to == "çay kaşığı":
        return base_grams / Decimal(str(DEFAULT_TEA_SPOON_WEIGHT_GR))
    elif u_to == "bardak":
        cup_weight = Decimal(str(get_cup_weight_gr(item_name)))
        return base_grams / cup_weight
    elif u_to == "çay bardağı":
        return base_grams / Decimal(str(DEFAULT_TEA_CUP_WEIGHT_GR))
    elif u_to == "fincan":
        return base_grams / Decimal(str(DEFAULT_COFFEE_CUP_WEIGHT_GR))
    elif u_to == "demet":
        return base_grams / Decimal(str(DEFAULT_BUNCH_WEIGHT_GR))
    elif u_to == "dilim":
        return base_grams / Decimal(str(DEFAULT_SLICE_WEIGHT_GR))
    elif u_to in ["paket", "kutu"]:
        return base_grams / Decimal(str(DEFAULT_PACK_WEIGHT_GR))
    elif u_to == "kavanoz":
        return base_grams / Decimal(str(DEFAULT_JAR_WEIGHT_GR))
    elif u_to == "porsiyon":
        return base_grams / Decimal(str(DEFAULT_PORTION_WEIGHT_GR))
    elif u_to == "adet":
        pw = get_piece_weight_gr(item_name, fallback_default=False)
        if pw is None:
            raise ValueError(
                f"'{item_name}' malzemesi için ortalama birim ağırlık (AVERAGE_UNIT_WEIGHTS_GR) bulunamadı. Lütfen adet cinsinden talep edin."
            )
        return base_grams / Decimal(str(pw))
    else:
        return base_grams / Decimal("100")
