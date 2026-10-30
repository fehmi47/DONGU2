import pytest
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.services.smart_deduction_service import (
    AVERAGE_UNIT_WEIGHTS_GR,
    process_recipe_deduction,
    calculate_converted_deduction,
)

# Testler için izole asenkron SQLite motoru
TEST_ASYNC_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def async_test_session():
    engine = create_async_engine(
        TEST_ASYNC_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        # Test kullanıcısı ve kategorisi oluştur
        user = User(
            id=1,
            username="sef_kullanici",
            email="sef@dongu.org",
            password_hash="pass123",
        )
        cat = Category(id=1, name="Sebze ve Meyve", description="Taze sebzeler")
        session.add_all([user, cat])

        await session.commit()
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def test_average_unit_weights_constants():
    """Statik sözlüğün varlığını ve kritik gıda gramajlarını doğrular."""
    assert "domates" in AVERAGE_UNIT_WEIGHTS_GR
    assert AVERAGE_UNIT_WEIGHTS_GR["domates"] == 150
    assert AVERAGE_UNIT_WEIGHTS_GR["soğan"] == 120
    assert AVERAGE_UNIT_WEIGHTS_GR["patates"] == 200
    assert AVERAGE_UNIT_WEIGHTS_GR["yumurta"] == 50
    assert AVERAGE_UNIT_WEIGHTS_GR["limon"] == 100


def test_unit_conversion_calculations():
    """calculate_converted_deduction fonksiyonunun adet-gr-kg dönüşümlerini test eder."""
    # 2 adet domates -> gr cinsinden stok (2 * 150 = 300 gr)
    res_gr = calculate_converted_deduction(
        requested_qty=Decimal("2"),
        requested_unit="adet",
        stock_unit="gr",
        ingredient_name="domates"
    )
    assert res_gr == Decimal("300")

    # 2 adet domates -> kg cinsinden stok (300 gr = 0.30 kg)
    res_kg = calculate_converted_deduction(
        requested_qty=Decimal("2"),
        requested_unit="adet",
        stock_unit="kg",
        ingredient_name="domates"
    )
    assert res_kg == Decimal("0.30")

    # 240 gr soğan -> adet cinsinden stok (240 / 120 = 2 adet)
    res_adet = calculate_converted_deduction(
        requested_qty=Decimal("240"),
        requested_unit="gr",
        stock_unit="adet",
        ingredient_name="soğan"
    )
    assert res_adet == Decimal("2")

    # Bilinmeyen birim dönüşümünde hata fırlatmalı
    with pytest.raises(HTTPException):
        calculate_converted_deduction(
            requested_qty=Decimal("1"),
            requested_unit="adet",
            stock_unit="kg",
            ingredient_name="bilinmeyen_ejder_meyvesi"
        )


@pytest.mark.anyio
async def test_deduction_adet_to_kg(async_test_session: AsyncSession):
    """
    Talep 'adet', Stok 'kg' durumu:
    Kilerde 1.00 kg domates var. Tarif için 2 adet (2 * 150gr = 0.30 kg) düşülür.
    Kalan: 0.70 kg, statü: active.
    """
    prod = Product(
        id=10,
        user_id=1,
        category_id=1,
        name="Domates",
        quantity=Decimal("1.00"),
        unit="kg",
        status="active"
    )
    async_test_session.add(prod)
    await async_test_session.commit()

    ingredients = [
        {"name": "Domates", "quantity": 2, "unit": "adet"}
    ]

    response = await process_recipe_deduction(
        db=async_test_session,
        user_id=1,
        ingredients=ingredients,
    )

    assert response.success is True
    assert len(response.deductions) == 1
    d = response.deductions[0]
    assert d.deducted_quantity == Decimal("0.30")
    assert d.remaining_stock == Decimal("0.70")
    assert d.status == "active"


@pytest.mark.anyio
async def test_deduction_gr_to_adet_reverse(async_test_session: AsyncSession):
    """
    Ters Dönüşüm: Talep 'gr', Stok 'adet':
    Kilerde 5 adet soğan var. Şef 240 gr soğan istiyor (240 / 120 = 2 adet).
    Kalan: 3 adet, statü: active.
    """
    prod = Product(
        id=11,
        user_id=1,
        category_id=1,
        name="Soğan",
        quantity=Decimal("5.00"),
        unit="adet",
        status="active"
    )
    async_test_session.add(prod)
    await async_test_session.commit()

    ingredients = [
        {"name": "Soğan", "quantity": 240, "unit": "gr"}
    ]

    response = await process_recipe_deduction(
        db=async_test_session,
        user_id=1,
        ingredients=ingredients,
    )

    assert response.success is True
    d = response.deductions[0]
    assert d.deducted_quantity == Decimal("2.00")
    assert d.remaining_stock == Decimal("3.00")
    assert d.status == "active"


@pytest.mark.anyio
async def test_deduction_to_consumed_status(async_test_session: AsyncSession):
    """
    Tolerans ve Tam Tüketim (CONSUMED):
    Kilerde 0.30 kg domates var. Şef 2 adet (0.30 kg) istiyor.
    Kalan miktar 0 olur, statü 'CONSUMED' olarak güncellenir.
    """
    prod = Product(
        id=12,
        user_id=1,
        category_id=1,
        name="Domates",
        quantity=Decimal("0.30"),
        unit="kg",
        status="active"
    )
    async_test_session.add(prod)
    await async_test_session.commit()

    ingredients = [
        {"name": "Domates", "quantity": 2, "unit": "adet"}
    ]

    response = await process_recipe_deduction(
        db=async_test_session,
        user_id=1,
        ingredients=ingredients,
    )

    assert response.success is True
    d = response.deductions[0]
    assert d.remaining_stock == Decimal("0.00")
    assert d.status == "CONSUMED"
    assert "Domates" in response.consumed_products


@pytest.mark.anyio
async def test_deduction_insufficient_stock_rollback(async_test_session: AsyncSession):
    """
    ACID ve Yetersiz Stok Rollback Kontrolü:
    1. Ürünün stoku yeterli, 2. Ürünün stoku yetersiz.
    İşlem HTTPException (400) vermeli ve ilk ürünün stoku DEĞİŞMEMELİ (Rollback).
    """
    prod1 = Product(
        id=13,
        user_id=1,
        category_id=1,
        name="Yumurta",
        quantity=Decimal("10.00"),
        unit="adet",
        status="active"
    )
    prod2 = Product(
        id=14,
        user_id=1,
        category_id=1,
        name="Patates",
        quantity=Decimal("0.10"),  # Sadece 100 gr patates var
        unit="kg",
        status="active"
    )
    async_test_session.add_all([prod1, prod2])
    await async_test_session.commit()

    # 2 adet yumurta (yeterli) ve 2 adet patates (2 * 200g = 400g = 0.40 kg yetersiz)
    ingredients = [
        {"name": "Yumurta", "quantity": 2, "unit": "adet"},
        {"name": "Patates", "quantity": 2, "unit": "adet"},
    ]

    with pytest.raises(HTTPException) as exc_info:
        await process_recipe_deduction(
            db=async_test_session,
            user_id=1,
            ingredients=ingredients,
        )

    assert exc_info.value.status_code == 400
    assert "yetersiz stok" in exc_info.value.detail.lower()

    # Rollback doğrulaması: Yumurta stoku hâlâ 10 olmalıdır
    res = await async_test_session.get(Product, 13)
    assert res.quantity == Decimal("10.00")


@pytest.mark.anyio
async def test_deduction_with_uuid_user_id(async_test_session: AsyncSession):
    """UUID formatındaki user_id parametresini başarıyla kabul eder."""
    test_uuid = uuid4()
    prod = Product(
        id=15,
        user_id=1,
        category_id=1,
        name="Limon",
        quantity=Decimal("5.00"),
        unit="adet",
        status="active"
    )
    async_test_session.add(prod)
    await async_test_session.commit()

    ingredients = [
        {"name": "Limon", "quantity": 1, "unit": "adet"}
    ]

    response = await process_recipe_deduction(
        db=async_test_session,
        user_id=test_uuid,
        ingredients=ingredients,
    )
    assert response.success is True
    assert response.deductions[0].remaining_stock == Decimal("4.00")


@pytest.mark.anyio
async def test_spoon_to_kg_deduction_rice_flour_butter(async_test_session: AsyncSession):
    """
    3 kaşık pirinç (3 * 20g = 60g = 0.06 kg), 1 kaşık un (15g = 0.015 kg)
    ve 1 kaşık tereyağı (15g = 0.015 kg) kg cinsindeki stoktan hatasız düşülür.
    Kesinlikle 3 kaşık 3 kilo olarak hesaplanmaz!
    """
    pirinc = Product(
        id=20,
        user_id=1,
        category_id=1,
        name="Baldo Pirinç",
        quantity=Decimal("1.00"),
        unit="kg",
        status="active"
    )
    un = Product(
        id=21,
        user_id=1,
        category_id=1,
        name="Buğday Unu",
        quantity=Decimal("2.00"),
        unit="kg",
        status="active"
    )
    tereyagi = Product(
        id=22,
        user_id=1,
        category_id=1,
        name="Köy Tereyağı",
        quantity=Decimal("2.00"),
        unit="kg",
        status="active"
    )
    async_test_session.add_all([pirinc, un, tereyagi])
    await async_test_session.commit()

    ingredients = [
        {"name": "Baldo Pirinç", "quantity": 3, "unit": "kaşık"},
        {"name": "Buğday Unu", "quantity": 1, "unit": "kaşık"},
        {"name": "Köy Tereyağı", "quantity": 1, "unit": "kaşık"},
    ]

    response = await process_recipe_deduction(
        db=async_test_session,
        user_id=1,
        ingredients=ingredients,
    )

    assert response.success is True
    assert len(response.deductions) == 3

    # Pirinç: 1.00 kg - 0.06 kg = 0.94 kg
    ded_pirinc = response.deductions[0]
    assert ded_pirinc.deducted_quantity == Decimal("0.06")
    assert ded_pirinc.remaining_stock == Decimal("0.94")

    # Un: 2.00 kg - 0.015 kg -> 0.02 kg (quantized) = 1.98 kg
    ded_un = response.deductions[1]
    assert ded_un.remaining_stock < Decimal("2.00")
    assert ded_un.remaining_stock > Decimal("1.97")

    # Tereyağı: 2.00 kg - 0.015 kg -> 0.02 kg (quantized) = 1.98 kg
    ded_tereyagi = response.deductions[2]
    assert ded_tereyagi.remaining_stock < Decimal("2.00")
    assert ded_tereyagi.remaining_stock > Decimal("1.97")


@pytest.mark.anyio
async def test_cup_and_bunch_conversions(async_test_session: AsyncSession):
    """Su bardağı ve demet gibi mutfak ölçüleri doğru gram/kg katsayılarıyla dönüştürülür."""
    from app.services.unit_converter import convert_unit

    # 1 su bardağı pirinç -> gr
    assert convert_unit(1, "bardak", "gr", "Pirinç") == Decimal("180")
    # 2 su bardağı un -> kg
    assert convert_unit(2, "bardak", "kg", "Un") == Decimal("0.26")
    # 1 demet maydanoz -> kg
    assert convert_unit(1, "demet", "kg", "Maydanoz") == Decimal("0.10")
    # 2 kaşık zeytinyağı -> litre
    assert convert_unit(2, "kaşık", "l", "Zeytinyağı") == Decimal("0.03")

