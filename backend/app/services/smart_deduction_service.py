import re
from decimal import Decimal
from typing import Dict, List, Optional, Union
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.consumption_log import ConsumptionLog
from app.schemas.smart_deduction import (
    IngredientDeductionInput,
    DeductionResultItem,
    RecipeDeductionResponse,
)

from app.services.unit_converter import (
    AVERAGE_PIECE_WEIGHTS_GR,
    get_piece_weight_gr,
    get_spoon_weight_gr,
    get_cup_weight_gr,
    convert_unit,
    normalize_string,
    normalize_unit,
)

# Geriye dönük uyumluluk için statik ortalama birim ağırlık sözlüğü (Gram cinsinden)
AVERAGE_UNIT_WEIGHTS_GR: Dict[str, int] = AVERAGE_PIECE_WEIGHTS_GR

# Tolerans sabiti (0 veya bu değerin altı tam 0 kabul edilip CONSUMED yapılır)
TOLERANCE: Decimal = Decimal("0.005")


def get_unit_weight_gr(ingredient_name: str) -> Optional[int]:
    """
    Malzeme adına göre AVERAGE_UNIT_WEIGHTS_GR tablosundan ağırlığı bulur.
    Birebir eşleşme, Türkçe normalize eşleşme ve alt kelime eşleşmelerini destekler.
    """
    return get_piece_weight_gr(ingredient_name)


def calculate_converted_deduction(
    requested_qty: Decimal,
    requested_unit: str,
    stock_unit: str,
    ingredient_name: str,
) -> Decimal:
    """
    Gelen malzeme talebini stok birimine çevirir.
    
    Senaryolar:
    - Kaşık (yemek kaşığı, tatlı kaşığı, çay kaşığı) <-> kg, gr, ml, l
    - Bardak (su bardağı, çay bardağı, fincan) <-> kg, gr, ml, l
    - Adet <-> kg, gr (AVERAGE_PIECE_WEIGHTS_GR ve mutfak standartları)
    - Demet, Dilim, Paket, Kutu, Kavanoz, Porsiyon <-> kg, gr
    - Metrik kütle ve hacim dönüşümleri (gr <-> kg, ml <-> l)
    - Aynı birimler doğrudan döndürülür.
    """
    try:
        return convert_unit(
            quantity=requested_qty,
            from_unit=requested_unit,
            to_unit=stock_unit,
            item_name=ingredient_name,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{ingredient_name}' için birim dönüşümü desteklenmiyor: {requested_unit} -> {stock_unit} ({str(e)})",
        )


def resolve_user_id(user_id: Union[UUID, str, int]) -> int:
    """
    Gelen UUID veya Integer kullanıcı kimliğini integer tabanlı veritabanı ID'sine normalize eder.
    """
    if isinstance(user_id, int):
        return user_id
    if isinstance(user_id, str):
        if user_id.isdigit():
            return int(user_id)
        try:
            val = UUID(user_id)
            return (val.int % 1000000) or 1
        except ValueError:
            return 1
    if isinstance(user_id, UUID):
        return (user_id.int % 1000000) or 1
    return 1


async def process_recipe_deduction(
    db: AsyncSession,
    user_id: Union[UUID, str, int],
    ingredients: List[dict],
    recipe_id: Optional[int] = None,
) -> RecipeDeductionResponse:
    """
    Yapay Zekâlı Şef Ajan'dan gelen tarif onayında belirtilen malzemeleri
    stoktan akıllı birim dönüşümleriyle düşer.
    
    İşlem ACID prensiplerine uygun olarak 'async with session.begin():' bloğu
    içinde tek bir atomik transaction olarak icra edilir.
    """
    if not ingredients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Düşülecek malzeme listesi boş olamaz.",
        )

    # Girdi doğrulaması: List[dict] -> List[IngredientDeductionInput]
    parsed_ingredients: List[IngredientDeductionInput] = []
    for item in ingredients:
        if isinstance(item, IngredientDeductionInput):
            parsed_ingredients.append(item)
        elif isinstance(item, dict):
            try:
                # Olası alternatif anahtar isimlerini eşle
                name = item.get("name") or item.get("ingredient_name")
                qty = item.get("quantity") or item.get("amount") or item.get("quantity_used")
                unit = item.get("unit")
                prod_id = item.get("product_id")
                if not name or qty is None or not unit:
                    raise ValueError("Eksik alan")
                parsed_ingredients.append(
                    IngredientDeductionInput(
                        name=str(name),
                        quantity=Decimal(str(qty)),
                        unit=str(unit),
                        product_id=int(prod_id) if prod_id is not None else None,
                    )
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Geçersiz malzeme formatı: {item} - Hata: {str(e)}",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Desteklenmeyen malzeme girdisi tipi: {type(item)}",
            )

    target_user_id = resolve_user_id(user_id)

    async def _execute_deduction_tx():
        deductions: List[DeductionResultItem] = []
        consumed_product_names: List[str] = []

        for ing in parsed_ingredients:
            # 1. Ürünü bul (ID varsa doğrudan ID, yoksa isme göre aktif stoktan)
            product: Optional[Product] = None
            if ing.product_id is not None:
                stmt = select(Product).where(
                    Product.id == ing.product_id,
                    Product.user_id == target_user_id,
                    Product.status.in_(["active", "ACTIVE"]),
                )
                res = await db.execute(stmt)
                product = res.scalar_one_or_none()
                if not product and isinstance(user_id, UUID):
                    stmt_fb = select(Product).where(
                        Product.id == ing.product_id,
                        Product.status.in_(["active", "ACTIVE"]),
                    )
                    res_fb = await db.execute(stmt_fb)
                    product = res_fb.scalar_one_or_none()
            else:
                # İsme göre arama (STT'si en yakın olanı ilk sırada tüketmek için order by)
                stmt = (
                    select(Product)
                    .where(
                        Product.user_id == target_user_id,
                        func.lower(Product.name) == ing.name.strip().lower(),
                        Product.status.in_(["active", "ACTIVE"]),
                    )
                    .order_by(Product.expiry_date.asc().nulls_last())
                )
                res = await db.execute(stmt)
                product = res.scalars().first()

                # UUID ile eşleşmediyse (SQLite Integer user_id uyumluluğu için)
                if not product and isinstance(user_id, UUID):
                    stmt_fb = (
                        select(Product)
                        .where(
                            func.lower(Product.name) == ing.name.strip().lower(),
                            Product.status.in_(["active", "ACTIVE"]),
                        )
                        .order_by(Product.expiry_date.asc().nulls_last())
                    )
                    res_fb = await db.execute(stmt_fb)
                    product = res_fb.scalars().first()

                # Tam eşleşmediyse normalize isimle dene
                if not product:
                    stmt_all = select(Product).where(
                        Product.status.in_(["active", "ACTIVE"]),
                    )
                    res_all = await db.execute(stmt_all)
                    all_prods = res_all.scalars().all()
                    norm_target = normalize_string(ing.name)
                    for p in all_prods:
                        if normalize_string(p.name) == norm_target or norm_target in normalize_string(p.name):
                            product = p
                            break


            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"'{ing.name}' adlı aktif kiler/buzdolabı ürünü bulunamadı.",
                )

            # 2. Akıllı birim dönüşümü hesapla
            deduction_in_stock_unit = calculate_converted_deduction(
                requested_qty=ing.quantity,
                requested_unit=ing.unit,
                stock_unit=product.unit,
                ingredient_name=product.name,
            )

            # 3. Yetersiz stok kontrolü
            prev_qty = Decimal(str(product.quantity))
            if prev_qty < deduction_in_stock_unit:
                # Tolerans kontrolü: Çok ufak fark varsa kabul et
                if (deduction_in_stock_unit - prev_qty) > TOLERANCE:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"'{product.name}' için yetersiz stok! "
                            f"Mevcut Stok: {prev_qty} {product.unit}, "
                            f"Gereken Düşüm: {deduction_in_stock_unit.quantize(Decimal('0.01'))} {product.unit} "
                            f"(Talep edilen: {ing.quantity} {ing.unit})."
                        ),
                    )

            # 4. Kalan miktarı hesapla ve Tolerans Kontrolü
            remaining_qty = prev_qty - deduction_in_stock_unit

            # 0 veya toleransın altına düşerse tam 0 yap ve CONSUMED olarak güncelle
            if remaining_qty <= TOLERANCE:
                product.quantity = Decimal("0.00")
                product.status = "CONSUMED"
                consumed_product_names.append(product.name)
            else:
                product.quantity = remaining_qty.quantize(Decimal("0.01"))

            # 5. Tüketim geçmiş kaydı (ConsumptionLog) oluştur
            log_entry = ConsumptionLog(
                product_id=product.id,
                recipe_id=recipe_id,
                quantity_used=deduction_in_stock_unit.quantize(Decimal("0.01")),
                unit=product.unit,
                action_type="recipe_used",
            )
            db.add(log_entry)

            deductions.append(
                DeductionResultItem(
                    product_id=product.id,
                    product_name=product.name,
                    requested_quantity=ing.quantity,
                    requested_unit=ing.unit,
                    deducted_quantity=deduction_in_stock_unit.quantize(Decimal("0.01")),
                    stock_unit=product.unit,
                    previous_stock=prev_qty,
                    remaining_stock=product.quantity,
                    status=product.status,
                )
            )

        return RecipeDeductionResponse(
            success=True,
            message=f"Tarif onayı sonrası {len(deductions)} malzeme başarıyla stoktan düşüldü.",
            deductions=deductions,
            consumed_products=consumed_product_names,
        )

    # ACID prensiplerine uygun olarak transaction bloğu içinde çalıştır
    if not db.in_transaction():
        async with db.begin():
            return await _execute_deduction_tx()
    else:
        async with db.begin_nested():
            return await _execute_deduction_tx()
