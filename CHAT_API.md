# 🌿 DÖNGÜ AI Asistanı - Frontend Entegrasyon Rehberi (`CHAT_API.md`)

Bu doküman, frontend geliştiricisinin DÖNGÜ AI Asistanı sohbet arayüzünü bağlaması için gereken tüm teknik detayları ve sözleşmeleri içerir.

---

## 1. Genel Bilgiler

- **Uç Nokta (Endpoint):** `POST /api/chat`
- **İçerik Tipi (Content-Type):** `application/json`
- **Oturum Yönetimi:** `X-User-Id` başlığı (Header) üzerinden kullanıcının ID'si iletilir (örneğin `X-User-Id: 1`).

---

## 2. İstek ve Yanıt Şemaları

### İstek Gövdesi (Request Body)
Backend stateless (durumsuz) mimaride çalışır; oturum veya Redis geçmişi tutmaz. Konuşma bağlamı (context) frontend tarafından `history` dizisiyle gönderilir.

```json
{
  "message": "Peki bu malzemelerle hangi çorbayı yapabilirim?",
  "history": [
    {
      "role": "user",
      "content": "Bugün hangi ürünlerimi tüketmeliyim?"
    },
    {
      "role": "assistant",
      "content": "Bugün öncelikle 1 günü kalan Salkım Domates ve 2 günü kalan Kırmızı Mercimek ürünlerinizi tüketmelisiniz."
    }
  ]
}
```

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| `message` | `string` | Evet | Kullanıcının girdiği yeni doğal dil soru veya talimatı (1 - 2000 karakter). |
| `history` | `ChatTurn[]` | Hayır | Son konuşma geçmişi (en fazla 10 mesaj). Boş bırakılabilir (geriye dönük uyumlu). |

#### `ChatTurn` Formatı (Sohbet Turu Nesnesi)

| Alan | Tip | Kısıt / Doğrulama | Açıklama |
|---|---|---|---|
| `role` | `string` | Yalnızca `"user"` veya `"assistant"` | Mesajı gönderen taraf. `system` veya `tool` rolleri güvenlik nedeniyle 422 ile reddedilir. |
| `content` | `string` | 1 - 4000 karakter | Mesajın metin içeriği. |

---

### Başarılı Yanıt (HTTP 200 OK)
```json
{
  "answer": "Bugün öncelikle 1 günü kalan Salkım Domates ve 2 günü kalan Süzme Yoğurt ürünlerinizi değerlendirmelisiniz.",
  "tools": [
    "get_priority_products"
  ]
}
```

| Alan | Tip | Açıklama |
|---|---|---|
| `answer` | `string` | Asistanın kullanıcıya hitaben ürettiği samimi, kısa Türkçe yanıt. |
| `tools` | `string[]` | Yanıt hazırlanırken arka planda çalıştırılan backend araçlarının adları. |

---

## 3. Frontend Araç Rozetleri (Tool Badges)

Asistan yanıt verirken arka planda hangi araçları kullandıysa yanıtın `tools` dizisinde döner. Kullanıcıya şeffaflık sağlamak için mesaj baloncuğunun altında şu rozetlerin (badge) gösterilmesi önerilir:

| Araç Adı (`tools` öğesi) | Önerilen Rozet Başlığı | İkon | Önerilen Renk Teması |
|---|---|---|---|
| `get_priority_products` | **Kiler Önceliği** | 🥬 / ⏱️ | Turuncu / Uyarı (Aciliyet) |
| `search_recipes` | **Akıllı Tarif** | 🍳 / 📖 | Yeşil / Başarı (Mutfak) |
| `get_consumption_stats` | **Etki Analizi** | 📊 / 🌱 | Mavi / Bilgi (Tasarruf) |
| `get_recycling_guide` | **Sıfır Atık Rehberi** | ♻️ / 🗑️ | Zümrüt / Ekoloji (Geri Dönüşüm) |
| `get_vacation_rescue_plan` | **Kurtarma Modu** | 🧳 | Mor / Seyahat (Tatil Öncesi) |

> **Not:** `search_recipes` aracı belirli bir malzeme sorgulandığında, o malzemenin kullanıcının mutfağında olup olmadığını `kullanicida_var: true/false` olarak döner. Kullanıcıda olmayan malzemeler için asistan mutfakta olmadığını belirtip genel katalog tariflerini sunar.

*Örnek UI Gösterimi:*
```html
<div class="chat-message assistant">
  <p>{{ response.answer }}</p>
  <div class="tool-badges">
    <span class="badge badge-warning">⏱️ Kiler Önceliği</span>
    <span class="badge badge-success">🍳 Akıllı Tarif</span>
  </div>
</div>
```

---

## 4. Hata Yönetimi ve Durum Kodları

### HTTP 503 Service Unavailable (Asistan Geçici Olarak Hizmet Dışı)
OpenAI API bağlantı sorunu olduğunda veya sistemde API anahtarı tanımlanmadığında döner:

**Yanıt Gövdesi:**
```json
{
  "detail": "Asistan şu an ulaşılamıyor, birazdan tekrar dene."
}
```

### HTTP 401 Unauthorized
`X-User-Id` başlığı eksikse veya sistemde böyle bir kullanıcı bulunamadığında döner.

---

## 5. Örnek Kullanım Senaryoları

### Senaryo 1: Kiler Önceliklerini Sorma
- **İstek:** `{"message": "Bugün hangi ürünlerimi tüketmeliyim?"}`
- **Yanıt:**
  ```json
  {
    "answer": "Bugün öncelikle 1 günü kalan Salkım Domates (3 adet) ve 2 günü kalan Süzme Yoğurt (500 gram) ürünlerinizi tüketmelisiniz. Kırmızı Mercimek için: Tavsiye edilen tüketim tarihi geçmiş. Kalitesi düşmüş olabilir; tüketmeden önce ürünü kontrol et.",
    "tools": ["get_priority_products"]
  }
  ```

### Senaryo 2: Akıllı Tarif Önerisi
- **İstek:** `{"message": "Elimdeki malzemelerle ne pişirebilirim?"}`
- **Yanıt:**
  ```json
  {
    "answer": "Elinizdeki malzemelerle Menemen (%80 malzeme eşleşmesi) yapabilirsiniz; sadece 20 dakikanızı alır. Alternatif olarak Sebzeli Bulgur Pilavı hazırlayabilirsiniz.",
    "tools": ["search_recipes"]
  }
  ```

### Senaryo 3: Gıda Kurtarma ve Çevresel Etki
- **İstek:** `{"message": "Bu ay ne kadar gıda kurtardım?"}`
- **Yanıt:**
  ```json
  {
    "answer": "Bu ay toplam 5.45 kg gıda kurtardınız ve 3 tarif tamamladınız. Bu sayede tahmini 13.62 kg CO2 emisyonunu önlediniz ve tahmini 4905 litre su tasarrufu sağladınız!",
    "tools": ["get_consumption_stats"]
  }
  ```

### Senaryo 4: Sıfır Atık ve Geri Dönüşüm
- **İstek:** `{"message": "Yumurta kabuğu ve konserve kutusunu hangi çöpe atmalıyım?"}`
- **Yanıt:**
  ```json
  {
    "answer": "Yumurta kabuğunu kahverengi organik atık kutusuna, konserve kutusunu ise içini durulayıp gri metal kutusuna atmalısınız.",
    "tools": ["get_recycling_guide"]
  }
  ```

### Senaryo 5: Kapsam Dışı Soru
- **İstek:** `{"message": "Yarın hava nasıl olacak?"}`
- **Yanıt:**
  ```json
  {
    "answer": "Ben DÖNGÜ asistanıyım; yalnızca mutfak stoklarınız, yemek tarifleri, gıda tüketimi ve geri dönüşüm konularında yardımcı olabilirim. Kileriniz veya tariflerinizle ilgili bir sorunuz var mı?",
    "tools": []
  }
  ```

---

## 6. Örnek Frontend Fetch Çağrısı (JavaScript)

```javascript
async function sendChatMessage(userText) {
  const userId = localStorage.getItem("dongu_user_id") || "1";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": userId,
      },
      body: JSON.stringify({ message: userText }),
    });

    if (response.status === 503) {
      const errData = await response.json();
      showToast(errData.detail || "Asistan şu an ulaşılamıyor, birazdan tekrar dene.");
      return;
    }

    if (!response.ok) {
      throw new Error("Sunucu hatası: " + response.status);
    }

    const data = await response.json();
    renderAssistantMessage(data.answer, data.tools);
  } catch (error) {
    console.error("Chat isteği başarısız:", error);
    showToast("Bir hata oluştu. Lütfen tekrar deneyin.");
  }
}
```
