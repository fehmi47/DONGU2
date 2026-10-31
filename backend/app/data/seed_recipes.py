from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient

SEED_RECIPES: List[Dict[str, Any]] = [
    {
        "name": "Menemen",
        "description": "Domates, biber ve yumurtanın mükemmel uyumuyla hazırlanan geleneksel lezzet.",
        "instructions": "1. Biberleri ince doğrayıp zeytinyağında soteleyin.\n2. Küp doğranmış domatesleri ekleyip suyunu çekene kadar pişirin.\n3. Yumurtaları kırın, tuzunu ekleyip hafifçe karıştırarak pişirin.",
        "preparation_time": 5,
        "cooking_time": 10,
        "servings": 2,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1594998893017-36147cbcae05?w=600",
        "ingredients": [
            {"ingredient_name": "Domates", "quantity": Decimal("3.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Biber", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Yumurta", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Zeytinyağı", "quantity": Decimal("2.00"), "unit": "kaşık", "is_optional": True},
            {"ingredient_name": "Tuz", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Sebzeli Omlet",
        "description": "Ispanak, peynir ve yumurta ile zenginleştirilmiş besleyici kahvaltılık.",
        "instructions": "1. Ispanakları yıkayıp zeytinyağında 2 dakika soteleyin.\n2. Yumurtaları bir kapta çırpın, tuz ekleyin.\n3. Ispanakların üzerine dökün, peynir parçalarını serpip kapağı kapalı pişirin.",
        "preparation_time": 5,
        "cooking_time": 7,
        "servings": 1,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=600",
        "ingredients": [
            {"ingredient_name": "Yumurta", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Ispanak", "quantity": Decimal("100.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Beyaz Peynir", "quantity": Decimal("50.00"), "unit": "gram", "is_optional": True},
            {"ingredient_name": "Zeytinyağı", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Patates Yemeği",
        "description": "Kilerdeki patates ve soğanları değerlendirmenin en lezzetli ve doyurucu yolu.",
        "instructions": "1. Soğanları yemeklik doğrayıp sıvı yağda pembeleşene kadar kavurun.\n2. Salçayı ekleyip kokusu çıkana kadar karıştırın.\n3. Küp doğranmış patatesleri ve üzerini geçecek kadar sıcak suyu ekleyip patatesler yumuşayana dek kaynatın.",
        "preparation_time": 10,
        "cooking_time": 25,
        "servings": 4,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=600",
        "ingredients": [
            {"ingredient_name": "Patates", "quantity": Decimal("4.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Soğan", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Salça", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": False},
            {"ingredient_name": "Sıvı Yağ", "quantity": Decimal("2.00"), "unit": "kaşık", "is_optional": True},
            {"ingredient_name": "Tuz", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Kırmızı Mercimek Çorbası",
        "description": "Evdeki temel bakliyat ve sebzelerle yapılan sıcacık klasik Türk çorbası.",
        "instructions": "1. Soğan, havuç ve patatesi iri doğrayıp yağda kavurun.\n2. Yıkanmış kırmızı mercimeği ekleyin.\n3. Sıcak su ekleyip sebzeler yumuşayana kadar pişirin ve pürüzsüz olana kadar blenderdan geçirin.",
        "preparation_time": 10,
        "cooking_time": 25,
        "servings": 4,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=600",
        "ingredients": [
            {"ingredient_name": "Kırmızı Mercimek", "quantity": Decimal("200.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Havuç", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Soğan", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Patates", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": True},
            {"ingredient_name": "Zeytinyağı", "quantity": Decimal("2.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Domates Çorbası",
        "description": "Olgunlaşmış ve yumuşamaya başlamış domatesleri değerlendirmek için birebir.",
        "instructions": "1. Tereyağında unu hafif kokusu çıkana dek kavurun.\n2. Rendelenmiş veya püre yapılmış domatesleri ekleyip 3-4 dakika kaynatın.\n3. Süt ve sıcak su ilave edin, kaynayana kadar karıştırıp üzerine kaşar peyniri rendeleyin.",
        "preparation_time": 10,
        "cooking_time": 15,
        "servings": 4,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1547592180-85f173990554?w=600",
        "ingredients": [
            {"ingredient_name": "Domates", "quantity": Decimal("4.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Un", "quantity": Decimal("2.00"), "unit": "kaşık", "is_optional": False},
            {"ingredient_name": "Tereyağı", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": False},
            {"ingredient_name": "Süt", "quantity": Decimal("200.00"), "unit": "ml", "is_optional": True},
            {"ingredient_name": "Kaşar Peyniri", "quantity": Decimal("50.00"), "unit": "gram", "is_optional": True},
        ]
    },
    {
        "name": "Sebzeli Makarna",
        "description": "Dolaptaki domates ve biberleri hızlıca değerlendirebileceğiniz pratik öğün.",
        "instructions": "1. Makarnayı tuzlu suda haşlayıp süzün.\n2. Ayrı bir tavada zeytinyağında ince kıyılmış sarımsak, biber ve domatesleri soteleyin.\n3. Sos koyulaşınca haşlanmış makarnayla harmanlayın.",
        "preparation_time": 10,
        "cooking_time": 12,
        "servings": 3,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1621996346565-e3d5d6281729?w=600",
        "ingredients": [
            {"ingredient_name": "Makarna", "quantity": Decimal("250.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Domates", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Biber", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Sarımsak", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": True},
            {"ingredient_name": "Zeytinyağı", "quantity": Decimal("2.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Kabak Yemeği",
        "description": "Hafif, zeytinyağlı ve pirinçli klasik Türk sebze yemeği.",
        "instructions": "1. Soğanları zeytinyağında kavurun, küp doğranmış kabakları ekleyin.\n2. Domates ve yıkanmış pirinci ilave edin.\n3. Kısık ateşte kabaklar yumuşayana kadar pişirip üzerine dereotu serpin.",
        "preparation_time": 15,
        "cooking_time": 25,
        "servings": 4,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600",
        "ingredients": [
            {"ingredient_name": "Kabak", "quantity": Decimal("3.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Soğan", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Domates", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Pirinç", "quantity": Decimal("2.00"), "unit": "kaşık", "is_optional": True},
            {"ingredient_name": "Dereotu", "quantity": Decimal("1.00"), "unit": "demet", "is_optional": True},
            {"ingredient_name": "Zeytinyağı", "quantity": Decimal("3.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Fırında Mücver",
        "description": "Kabak, dereotu, beyaz peynir ve yumurtayla hazırlanan hafif ve leziz mücver.",
        "instructions": "1. Kabakları rendeleyip suyunu iyice sıkın.\n2. Yumurta, un, ufalanmış peynir ve kıyılmış dereotunu ekleyip karıştırın.\n3. Yağlanmış borcama döküp 180 derece fırında üzeri kızarana kadar 30 dakika pişirin.",
        "preparation_time": 15,
        "cooking_time": 30,
        "servings": 4,
        "difficulty": "Orta",
        "image_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=600",
        "ingredients": [
            {"ingredient_name": "Kabak", "quantity": Decimal("3.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Yumurta", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Un", "quantity": Decimal("3.00"), "unit": "kaşık", "is_optional": False},
            {"ingredient_name": "Beyaz Peynir", "quantity": Decimal("100.00"), "unit": "gram", "is_optional": True},
            {"ingredient_name": "Dereotu", "quantity": Decimal("1.00"), "unit": "demet", "is_optional": True},
        ]
    },
    {
        "name": "Peynirli Sigara Böreği",
        "description": "Kalan beyaz peynirleri ve yufkayı çıtır bir atıştırmalığa dönüştürün.",
        "instructions": "1. Peyniri çatalla ezin ve ince kıyılmış maydanozla karıştırın.\n2. Üçgen kesilmiş yufkanın geniş kenarına harçtan koyup sıkıca sarın.\n3. Az yağda veya fırında altın sarısı olana dek kızartın.",
        "preparation_time": 15,
        "cooking_time": 10,
        "servings": 4,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1608039829572-78524f79c4c7?w=600",
        "ingredients": [
            {"ingredient_name": "Yufka", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Beyaz Peynir", "quantity": Decimal("150.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Maydanoz", "quantity": Decimal("1.00"), "unit": "demet", "is_optional": True},
            {"ingredient_name": "Sıvı Yağ", "quantity": Decimal("3.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Sarımsaklı Yoğurtlu Makarna",
        "description": "Dolaptaki yoğurt ve sarımsakla sadece 15 dakikada hazırlanan kurtarıcı lezzet.",
        "instructions": "1. Makarnayı haşlayıp süzün.\n2. Yoğurda ezilmiş sarımsak ve tuz ekleyip çırpın.\n3. Makarnanın üzerine yoğurdu gezdirin, tereyağında kızdırılmış pul biber sosunu dökün.",
        "preparation_time": 5,
        "cooking_time": 10,
        "servings": 2,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1608897013039-887f21d8c804?w=600",
        "ingredients": [
            {"ingredient_name": "Makarna", "quantity": Decimal("250.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Yoğurt", "quantity": Decimal("300.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Sarımsak", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Tereyağı", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Şakşuka",
        "description": "Kızarmış patlıcan ve biberlerin domates sosuyla buluştuğu harika bir meze.",
        "instructions": "1. Patlıcan ve biberleri küp doğrayıp az yağda soteleyin/kızartın.\n2. Ayrı bir tavada domates, sarımsak ve zeytinyağını pişirip sos haline getirin.\n3. Sosu sebzelerin üzerine döküp ılık veya soğuk servis edin.",
        "preparation_time": 15,
        "cooking_time": 20,
        "servings": 4,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1592417817098-8f3d69109853?w=600",
        "ingredients": [
            {"ingredient_name": "Patlıcan", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Biber", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Domates", "quantity": Decimal("3.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Sarımsak", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Zeytinyağı", "quantity": Decimal("3.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Yayla Çorbası",
        "description": "Yoğurt, pirinç ve mis gibi naneli sos ile ferahlatıcı geleneksel lezzet.",
        "instructions": "1. Pirinci suda yumuşayana kadar haşlayın.\n2. Yoğurt, yumurta ve unu bir kasede pürüzsüz çırpın.\n3. Çorbanın suyundan ılıtıp yoğurda ekleyin, tencereye azar azar döküp kaynatın, naneli tereyağı gezdirin.",
        "preparation_time": 10,
        "cooking_time": 20,
        "servings": 4,
        "difficulty": "Orta",
        "image_url": "https://images.unsplash.com/photo-1547592180-85f173990554?w=600",
        "ingredients": [
            {"ingredient_name": "Yoğurt", "quantity": Decimal("400.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Pirinç", "quantity": Decimal("3.00"), "unit": "kaşık", "is_optional": False},
            {"ingredient_name": "Yumurta", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Un", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": False},
            {"ingredient_name": "Tereyağı", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Zeytinyağlı Ispanak Yemeği",
        "description": "Demir deposu taze ıspanakların hafif ve sağlıklı akşam yemeğine dönüşümü.",
        "instructions": "1. Soğanı doğrayıp zeytinyağında pembeleştirin, salçayı ekleyin.\n2. Yıkanmış doğranmış ıspanakları ve pirinci ilave edin.\n3. Az miktarda sıcak su ekleyip pirinçler pişene kadar kapağı kapalı tutun.",
        "preparation_time": 15,
        "cooking_time": 20,
        "servings": 4,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=600",
        "ingredients": [
            {"ingredient_name": "Ispanak", "quantity": Decimal("500.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Soğan", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Pirinç", "quantity": Decimal("2.00"), "unit": "kaşık", "is_optional": False},
            {"ingredient_name": "Salça", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": True},
            {"ingredient_name": "Zeytinyağı", "quantity": Decimal("2.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Zeytinyağlı Taze Fasulye",
        "description": "Yaz aylarının vazgeçilmezi, soğuk servis edilen taze fasulye.",
        "instructions": "1. Fasulyeleri ayıklayıp boyuna ikiye bölün.\n2. Tencereye soğan, fasulye ve küp domatesleri kat kat dizin.\n3. Zeytinyağı, tuz ve yarım çay bardağı su ekleyip kısık ateşte pişirin.",
        "preparation_time": 15,
        "cooking_time": 35,
        "servings": 4,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1551248429-40975aa4de74?w=600",
        "ingredients": [
            {"ingredient_name": "Taze Fasulye", "quantity": Decimal("500.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Domates", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Soğan", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Zeytinyağı", "quantity": Decimal("3.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Klasik Kısır",
        "description": "İnce bulgur, salça ve taze yeşilliklerle hazırlanan pratik Türk lezzeti.",
        "instructions": "1. İnce bulguru sıcak suyla ıslatıp kapağını kapatın, 10 dakika şişsin.\n2. Salçayı, zeytinyağını ve limonu ekleyip iyice yoğurun.\n3. İnce doğranmış maydanoz ve yeşillikleri ilave edip harmanlayın.",
        "preparation_time": 15,
        "cooking_time": 0,
        "servings": 4,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600",
        "ingredients": [
            {"ingredient_name": "Bulgur", "quantity": Decimal("200.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Salça", "quantity": Decimal("2.00"), "unit": "kaşık", "is_optional": False},
            {"ingredient_name": "Maydanoz", "quantity": Decimal("1.00"), "unit": "demet", "is_optional": False},
            {"ingredient_name": "Zeytinyağı", "quantity": Decimal("3.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Sebzeli Bulgur Pilavı",
        "description": "Domates ve biberle zenginleştirilmiş tane tane nefis bulgur pilavı.",
        "instructions": "1. Soğan ve biberleri tereyağında soteleyin.\n2. Domatesleri ekleyip 2 dakika pişirin.\n3. Bulguru ve 2 katı sıcak suyu ekleyip suyunu çekene kadar kısık ateşte demleyin.",
        "preparation_time": 10,
        "cooking_time": 20,
        "servings": 4,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1536304929831-ee1ca9d44906?w=600",
        "ingredients": [
            {"ingredient_name": "Bulgur", "quantity": Decimal("200.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Domates", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Biber", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Tereyağı", "quantity": Decimal("2.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Kıymalı Yumurta",
        "description": "Kıymayı ve yumurtayı buluşturan doyurucu ve protein dolu geleneksel tarif.",
        "instructions": "1. Kıymayı ve soğanı tavada suyunu çekene kadar kavurun.\n2. Tuz ve baharatları ekleyin.\n3. Kıymada çukurlar açıp yumurtaları kırın ve beyazları katılaşana kadar pişirin.",
        "preparation_time": 5,
        "cooking_time": 12,
        "servings": 2,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=600",
        "ingredients": [
            {"ingredient_name": "Kıyma", "quantity": Decimal("200.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Yumurta", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Soğan", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": True},
            {"ingredient_name": "Tereyağı", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Fırında Karışık Sebze",
        "description": "Buzdolabındaki her türlü sebzeyi değerlendirmenin en kolay ve sağlıklı yolu.",
        "instructions": "1. Patates, kabak, havuç ve biberleri iri parçalar halinde doğrayın.\n2. Zeytinyağı, tuz ve baharatlarla harmanlayın.\n3. Fırın tepsisine yayıp 200 derece fırında sebzeler yumuşayıp kızarana dek pişirin.",
        "preparation_time": 15,
        "cooking_time": 30,
        "servings": 4,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600",
        "ingredients": [
            {"ingredient_name": "Patates", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Kabak", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Havuç", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Biber", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": True},
            {"ingredient_name": "Zeytinyağı", "quantity": Decimal("3.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Tarhana Çorbası",
        "description": "Geleneksel kurutulmuş tarhanayla kış aylarında şifa veren çorba.",
        "instructions": "1. Tarhanayı 1 bardak ılık suyla ıslatıp çözdürün.\n2. Tencerede tereyağı ve salçayı hafifçe kavurun.\n3. Çözünen tarhanayı ve suyunu ekleyip kaynayana kadar sürekli karıştırın.",
        "preparation_time": 5,
        "cooking_time": 15,
        "servings": 4,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=600",
        "ingredients": [
            {"ingredient_name": "Tarhana", "quantity": Decimal("4.00"), "unit": "kaşık", "is_optional": False},
            {"ingredient_name": "Tereyağı", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": False},
            {"ingredient_name": "Salça", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": True},
            {"ingredient_name": "Sarımsak", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": True},
        ]
    },
    {
        "name": "Klasik Cacık",
        "description": "Salatalık, yoğurt ve sarımsakla serinletici nefis tamamlayıcı meze.",
        "instructions": "1. Salatalıkları rendeleyin veya minik küpler halinde doğrayın.\n2. Yoğurdu, ezilmiş sarımsağı ve tuzu hafif suyla kıvam alana dek çırpın.\n3. Salatalıkları ekleyip üzerine zeytinyağı ve kuru nane gezdirin.",
        "preparation_time": 10,
        "cooking_time": 0,
        "servings": 3,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1505253716362-afaea1d3d1af?w=600",
        "ingredients": [
            {"ingredient_name": "Salatalık", "quantity": Decimal("2.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Yoğurt", "quantity": Decimal("350.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Sarımsak", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": True},
            {"ingredient_name": "Zeytinyağı", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Nohutlu Tavuklu Pilav",
        "description": "Haşlanmış tavuk göğsü ve nohutla zenginleştirilmiş, tane tane dökülen geleneksel bir ana yemek.",
        "instructions": "1. Tavuk göğsünü haşlayıp didikleyin, suyunu kenara ayırın.\n2. Tereyağında yıkanmış pirinç veya bulguru kavurun.\n3. Haşlanmış nohut, didiklenmiş tavuk eti ve sıcak tavuk suyunu ekleyin.\n4. Kısık ateşte suyunu çekene kadar pişirip 15 dakika demlendirin.",
        "preparation_time": 10,
        "cooking_time": 25,
        "servings": 4,
        "difficulty": "Orta",
        "image_url": "https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600",
        "ingredients": [
            {"ingredient_name": "Tavuk Göğsü", "quantity": Decimal("300.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Nohut", "quantity": Decimal("200.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Bulgur", "quantity": Decimal("250.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Tereyağı", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": True},
            {"ingredient_name": "Tuz", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Kıymalı Bezelye Yemeği",
        "description": "Dondurucudaki bezelyeleri ve sebzeleri değerlendiren hafif, leziz bir tencere yemeği.",
        "instructions": "1. Yemeklik doğranmış soğanları yağda kavurun.\n2. Varsa kıymayı veya tavuk parçasını ekleyip rengi dönene kadar soteleyin.\n3. Salça, küp doğranmış havuç ve dondurulmuş bezelyeyi ekleyin.\n4. Sıcak su ve tuz ilave edip sebzeler yumuşayana dek kısık ateşte pişirin.",
        "preparation_time": 10,
        "cooking_time": 25,
        "servings": 4,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600",
        "ingredients": [
            {"ingredient_name": "Bezelye", "quantity": Decimal("300.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Havuç", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Soğan", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Salça", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": False},
            {"ingredient_name": "Zeytinyağı", "quantity": Decimal("2.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Fırında Kaşarlı Bayat Ekmek Dilimleri",
        "description": "Evdeki bayat ekmekleri, kaşar peyniri ve domatesle çıtır çıtır bir kahvaltı ziyafetine dönüştürün.",
        "instructions": "1. Bayat ekmekleri dilimleyip fırın tepsisine dizin.\n2. Bir kapta yumurta, rendelenmiş kaşar, minik doğranmış domates ve kekiği karıştırın.\n3. Harcı ekmeklerin üzerine yayın.\n4. 200 derece fırında peynirler eriyip kızarana kadar 8-10 dakika pişirin.",
        "preparation_time": 5,
        "cooking_time": 10,
        "servings": 3,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1509722747041-616f39b57569?w=600",
        "ingredients": [
            {"ingredient_name": "Ekmek", "quantity": Decimal("4.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Kaşar Peyniri", "quantity": Decimal("100.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Yumurta", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Domates", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": True},
            {"ingredient_name": "Zeytinyağı", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Yoğurtlu Havuç Tarator",
        "description": "Dolaptaki havuç ve yoğurdu cevizle buluşturan ferahlatıcı ve pratik bir meze.",
        "instructions": "1. Havuçları rendeleyip zeytinyağında yumuşayana kadar 5-6 dakika soteleyin ve soğumaya bırakın.\n2. Bir kasede süzme yoğurt, ezilmiş sarımsak ve tuzu çırpın.\n3. Havuçları yoğurda ekleyip karıştırın, üzerine iri kıyılmış ceviz içi serpip servis yapın.",
        "preparation_time": 10,
        "cooking_time": 6,
        "servings": 4,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600",
        "ingredients": [
            {"ingredient_name": "Havuç", "quantity": Decimal("3.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Yoğurt", "quantity": Decimal("300.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Zeytinyağı", "quantity": Decimal("2.00"), "unit": "kaşık", "is_optional": False},
            {"ingredient_name": "Ceviz İçi", "quantity": Decimal("50.00"), "unit": "gram", "is_optional": True},
            {"ingredient_name": "Sarımsak", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": True},
        ]
    },
    {
        "name": "Elmalı Tarçınlı Yulaf Kasesi",
        "description": "Kalan elmaları ve yulafı değerlendiren, sindirimi kolay ve besleyici hafif bir tatlı/kahvaltı.",
        "instructions": "1. Elmaları küp küp doğrayıp bir tavada azıcık su ve tarçınla yumuşayana kadar soteleyin.\n2. Yulafı süt veya su ile ocakta lapa haline gelene kadar pişirin.\n3. Lapayı kaseye alın, üzerine sotelenmiş elma dilimlerini ve cevizleri yerleştirip servis edin.",
        "preparation_time": 5,
        "cooking_time": 8,
        "servings": 1,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1517673132405-a56a62b18caf?w=600",
        "ingredients": [
            {"ingredient_name": "Elma", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Süt", "quantity": Decimal("200.00"), "unit": "ml", "is_optional": False},
            {"ingredient_name": "Ceviz İçi", "quantity": Decimal("30.00"), "unit": "gram", "is_optional": True},
            {"ingredient_name": "Tarçın", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": True},
        ]
    },
    {
        "name": "Ezogelin Çorbası",
        "description": "Kırmızı mercimek, bulgur ve pirincin nane ve salçayla uyumundan doğan doyurucu sıcacık çorba.",
        "instructions": "1. Tencereye yıkanmış kırmızı mercimek, bulgur, pirinç ve sıcak suyu alıp yumuşayana kadar kaynatın.\n2. Ayrı bir tavada tereyağında rendelenmiş soğan ve sarımsağı kavurun, salça ve naneyi ekleyip kokusu çıkınca çorbaya ilave edin.\n3. 10 dakika daha kısık ateşte kaynatıp sıcak servis yapın.",
        "preparation_time": 10,
        "cooking_time": 25,
        "servings": 5,
        "difficulty": "Kolay",
        "image_url": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=600",
        "ingredients": [
            {"ingredient_name": "Kırmızı Mercimek", "quantity": Decimal("150.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Bulgur", "quantity": Decimal("50.00"), "unit": "gram", "is_optional": False},
            {"ingredient_name": "Soğan", "quantity": Decimal("1.00"), "unit": "adet", "is_optional": False},
            {"ingredient_name": "Salça", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": False},
            {"ingredient_name": "Tereyağı", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": True},
            {"ingredient_name": "Nane", "quantity": Decimal("1.00"), "unit": "kaşık", "is_optional": True},
        ]
    }
]


def seed_recipes(db: Session) -> List[Recipe]:
    """
    Doğrulanmış yemek tariflerini ve malzemelerini veritabanına ekler.
    
    İdempotent Mantık:
    - Veritabanında kayıtlı mevcut tarif isimlerini çeker.
    - Sadece henüz eklenmemiş olan tarifleri ekler.
    - Mevcut tarif kayıtlarını ve ilişkili malzemelerini asla mükerrer eklemez.
    """
    existing_recipe_names = {r.name for r in db.query(Recipe).all()}
    added_recipes = []

    for item in SEED_RECIPES:
        if item["name"] not in existing_recipe_names:
            recipe = Recipe(
                name=item["name"],
                description=item["description"],
                instructions=item["instructions"],
                preparation_time=item["preparation_time"],
                cooking_time=item["cooking_time"],
                servings=item["servings"],
                difficulty=item["difficulty"],
                image_url=item.get("image_url"),
            )
            db.add(recipe)
            db.flush()  # recipe.id oluşması için flush

            for ing in item["ingredients"]:
                ingredient = RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_name=ing["ingredient_name"],
                    quantity=ing["quantity"],
                    unit=ing["unit"],
                    is_optional=ing.get("is_optional", False),
                )
                db.add(ingredient)

            added_recipes.append(recipe)

    if added_recipes:
        db.commit()
        for r in added_recipes:
            db.refresh(r)

    return db.query(Recipe).order_by(Recipe.id).all()
