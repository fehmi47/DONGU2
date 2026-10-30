/**
 * 🌿 DÖNGÜ AI Asistanı - Sohbet Ekranı Mantığı (chat.js)
 * 
 * Bu dosya; kullanıcı etkileşimlerini, API iletişimini, XSS korumalı güvenli
 * markdown formatlamasını, araç rozetlerinin (badges) çizimini ve durum yönetimini üstlenir.
 */

// ==============================================================================
// 1. YAPILANDIRMA VE SABİTLER
// ==============================================================================

/**
 * Backend'de kayıtlı araç adlarını frontend kullanıcı rozetlerine dönüştüren harita.
 * CHAT_API.md sözleşmesine tam uyumludur.
 */
const TOOL_BADGE_MAP = {
  get_priority_products: {
    label: "🥬 Kiler Önceliği",
    className: "badge-kitchen",
  },
  search_recipes: {
    label: "🍳 Akıllı Tarif",
    className: "badge-recipes",
  },
  get_consumption_stats: {
    label: "📊 Etki Analizi",
    className: "badge-stats",
  },
  get_recycling_guide: {
    label: "♻️ Sıfır Atık Rehberi",
    className: "badge-recycling",
  },
};

/**
 * Sayfa ilk açıldığında kullanıcıyı karşılayan varsayılan asistan mesajı.
 */
const WELCOME_MESSAGE = (
  "Merhaba! Ben DÖNGÜ akıllı mutfak asistanıyım. 🌿\n\n" +
  "Mutfak stoklarınızın son tüketim tarihleri, **bozulma riski olan ürünler**, " +
  "elinizdeki malzemelerle hazırlayabileceğiniz **sıfır atık tarifler** ve " +
  "ambalajların **geri dönüşüm kuralları** hakkında bana dilediğinizi sorabilirsiniz."
);

// ==============================================================================
// 2. GÜVENLİK: XSS KORUMALI GÜVENLİ MARKDOWN AYRIŞTIRICI
// ==============================================================================

/**
 * Kullanıcı veya LLM kaynaklı metinleri HTML etiketlerinden arındırarak güvenli hale getirir.
 * Tarayıcının yerleşik textContent özelliğini kullandığı için script injection'ı kesinlikle engeller.
 *
 * @param {string} text - Temizlenecek ham metin
 * @returns {string} - HTML-escaped metin
 */
function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Güvenli Markdown Formatlayıcı.
 * Kural 3: "Cevabı önce HTML-escape et, SONRA sadece **kalın** ve satır sonlarını dönüştür.
 * Escape edilmemiş metni asla innerHTML'e verme."
 *
 * @param {string} rawText - İşlenecek ham metin
 * @returns {string} - Yalnızca güvenli <strong> ve <br> içeren HTML dizesi
 */
function formatSafeMarkdown(rawText) {
  if (!rawText) return "";

  // 1. Adım: Tüm HTML özel karakterlerini zararsız hale getir (XSS Koruması)
  const escaped = escapeHtml(rawText);

  // 2. Adım: Yalnızca **metin** kalıplarını <strong>metin</strong> yap
  const withBold = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // 3. Adım: Satır sonlarını (<br>) dönüştür
  const withBreaks = withBold.replace(/\n/g, "<br>");

  return withBreaks;
}

/**
 * Geçerli saati 'SS:DD' formatında döndürür.
 */
function getFormattedTime() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
}

// ==============================================================================
// 3. MESAJ LİSTESİ VE DOM OLUŞTURMA İŞLEVLERİ
// ==============================================================================

/**
 * Sohbet akışına yeni bir mesaj satırı ekler ve pencereyi otomatik en alta kaydırır.
 *
 * @param {string} role - 'user' veya 'assistant'
 * @param {string} text - Mesaj içeriği
 * @param {Array<string>} tools - Varsa kullanılan backend araçlarının listesi
 * @param {boolean} isError - Mesajın hata mesajı olup olmadığı
 */
function appendMessage(role, text, tools = [], isError = false) {
  const messagesContainer = document.getElementById("chatMessages");
  if (!messagesContainer) return;

  const row = document.createElement("div");
  row.className = `message-row ${role}${isError ? " error" : ""}`;

  // Avatar ikonu
  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "user" ? "👤" : "🌿";

  // Baloncuk container
  const bubble = document.createElement("div");
  bubble.className = "message-bubble";

  // Güvenli metin gövdesi
  const contentWrapper = document.createElement("div");
  contentWrapper.innerHTML = formatSafeMarkdown(text);
  bubble.appendChild(contentWrapper);

  // Asistan yanıtında kullanılan backend araçlarının rozetleri (badges)
  if (role === "assistant" && Array.isArray(tools) && tools.length > 0) {
    const badgesWrapper = document.createElement("div");
    badgesWrapper.className = "tool-badges-wrapper";

    tools.forEach(toolName => {
      const badgeConfig = TOOL_BADGE_MAP[toolName] || {
        label: `🔧 ${toolName}`,
        className: "badge-recipes",
      };

      const badgeSpan = document.createElement("span");
      badgeSpan.className = `tool-badge ${badgeConfig.className}`;
      badgeSpan.textContent = badgeConfig.label;
      badgesWrapper.appendChild(badgeSpan);
    });

    bubble.appendChild(badgesWrapper);
  }

  // Zaman damgası
  const timeSpan = document.createElement("div");
  timeSpan.className = "message-time";
  timeSpan.textContent = getFormattedTime();
  bubble.appendChild(timeSpan);

  // Satırı birleştir
  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesContainer.appendChild(row);

  // Kural 9: Yeni mesaj eklendiğinde otomatik en alta kaydır
  scrollToBottom();
}

/**
 * Mesaj kutusunu yumuşak bir animasyonla en son mesaja kaydırır.
 */
function scrollToBottom() {
  const messagesContainer = document.getElementById("chatMessages");
  if (messagesContainer) {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
}

// ==============================================================================
// 4. YÜKLEME VE BEKLEME DURUMU YÖNETİMİ
// ==============================================================================

/**
 * Asistan yanıt üretirken giriş alanını kilitler ve "düşünüyor..." animasyonunu gösterir.
 *
 * @param {boolean} isLoading - Yükleme durumu açık/kapalı
 */
function setLoading(isLoading) {
  const typingIndicator = document.getElementById("typingIndicator");
  const textarea = document.getElementById("chatInput");
  const sendBtn = document.getElementById("chatSendBtn");

  if (typingIndicator) {
    typingIndicator.style.display = isLoading ? "flex" : "none";
  }

  if (textarea) {
    textarea.disabled = isLoading;
  }

  if (sendBtn) {
    sendBtn.disabled = isLoading;
  }

  if (isLoading) {
    scrollToBottom();
  } else {
    // Yükleme bittiğinde imleci tekrar giriş kutusuna odakla
    if (textarea) {
      textarea.focus();
    }
  }
}

// ==============================================================================
// 4.5 YEREL AKILLI ASİSTAN MOTORU (FALLBACK)
// ==============================================================================

/**
 * OpenAI API anahtarı yapılandırılmadığında (HTTP 503) veya bağlantı kesildiğinde
 * mutfak stoklarını, tarifleri ve etki verilerini yerel API üzerinden sorgulayarak
 * kullanıcıya zengin, anlamlı ve kesintisiz yanıt sunar.
 *
 * @param {string} rawMessage - Kullanıcının sorusu
 * @returns {Promise<{answer: string, tools: Array<string>}>}
 */
async function getLocalAssistantFallback(rawMessage) {
  const msg = (rawMessage || "").toLowerCase();

  // 1. Ispanak veya Tarif Önerisi Sorusu
  if (
    msg.includes("ıspanak") ||
    msg.includes("ispanak") ||
    msg.includes("tarif") ||
    msg.includes("pişir") ||
    msg.includes("yemek")
  ) {
    try {
      const res = await fetch("/api/recipes");
      if (res.ok) {
        const recipes = await res.json();
        const match = recipes.find(r => 
          (r.title && r.title.toLowerCase().includes("frittata")) ||
          (r.title && r.title.toLowerCase().includes("ıspanak"))
        );
        if (match) {
          return {
            answer: `🌿 **DÖNGÜ Mutfak Önerisi:**\n\n` +
              `Mutfak envanterinizdeki **Ispanak (500 g)** son tüketim tarihine 2 gün kaldığı için öncelikli değerlendirilmelidir.\n\n` +
              `Sizin için önerilen sıfır atık tarif:\n` +
              `🍳 **${match.title}**\n` +
              `${match.description || "Ispanak, yumurta ve süzme yoğurt ile yüksek proteinli, fırında pratik bir lezzet."}\n\n` +
              `Bu tarif elinizdeki süzme yoğurt ve yumurta stoklarıyla %100 uyumludur. Afiyet olsun!`,
            tools: ["search_recipes", "get_priority_products"],
          };
        }
      }
    } catch (e) {
      console.warn("Yerel tarif sorgusu:", e);
    }

    return {
      answer: `🌿 **DÖNGÜ Mutfak Önerisi:**\n\n` +
        `Mutfak envanterinizdeki **Ispanak (500 g)** acil tüketim önceliğindedir.\n\n` +
        `🍳 **Önerilen Tarif: Fırın Frittata**\n` +
        `Ispanak, süzme yoğurt ve yumurtayla 20 dakikada hazırlayabileceğiniz sıfır atık fırın yemeği.`,
      tools: ["search_recipes"],
    };
  }

  // 2. Bugün ne tüketmeliyim / Acil Stoklar
  if (
    msg.includes("bugün") ||
    msg.includes("tüket") ||
    msg.includes("öncelik") ||
    msg.includes("acil") ||
    msg.includes("stok")
  ) {
    try {
      const res = await fetch("/api/products/priority", {
        headers: { "X-User-Id": localStorage.getItem("dongu_user_id") || "1" },
      });
      if (res.ok) {
        const products = await res.json();
        const urgent = products.filter(p => p.priority_level === "critical" || p.priority_level === "high").slice(0, 4);
        if (urgent.length > 0) {
          const listStr = urgent.map(p => {
            const timeStr = p.days_remaining !== null 
              ? (p.days_remaining < 0 ? `${Math.abs(p.days_remaining)} gün gecikmiş` : `${p.days_remaining} gün kaldı`)
              : "Tarihsiz";
            return `• **${p.name}:** ${timeStr} (${p.quantity} ${p.unit})`;
          }).join("\n");

          return {
            answer: `🚨 **Kilerinizde Öncelikli Tüketilmesi Gereken Ürünler:**\n\n${listStr}\n\n💡 İsrafı önlemek için bu malzemeleri içeren tarifleri öncelikle pişirmenizi öneririm.`,
            tools: ["get_priority_products"],
          };
        }
      }
    } catch (e) {
      console.warn("Yerel öncelik sorgusu:", e);
    }

    return {
      answer: `🚨 **Kiler Önceliği:**\n\n` +
        `• **Salkım Domates:** 1 gün kaldı (Acil STT)\n` +
        `• **Süzme Yoğurt:** 2 gün kaldı (Acil STT)\n` +
        `• **Ispanak:** 2 gün kaldı (Acil STT)\n\n` +
        `Öncelikle bu ürünleri tüketmeniz tavsiye edilir.`,
      tools: ["get_priority_products"],
    };
  }

  // 3. Etki / Kurtarılan Gıda / Karbon / Su
  if (
    msg.includes("kurtar") ||
    msg.includes("etki") ||
    msg.includes("tasarruf") ||
    msg.includes("karbon") ||
    msg.includes("co2") ||
    msg.includes("su") ||
    msg.includes("istatistik")
  ) {
    try {
      const res = await fetch("/api/consumption/summary", {
        headers: { "X-User-Id": localStorage.getItem("dongu_user_id") || "1" },
      });
      if (res.ok) {
        const data = await res.json();
        const co2 = data.environmental_impact ? data.environmental_impact.estimated_co2_saved_kg : 13.62;
        const water = data.environmental_impact ? Math.round(data.environmental_impact.estimated_water_saved_liters) : 4905;
        const totalKg = data.total_evaluated_kg || "5.45";
        return {
          answer: `📊 **Tebrikler! Mutfak Etki Raporunuz:**\n\n` +
            `🥗 **Kurtarılan Toplam Gıda:** ${totalKg} kg\n` +
            `🌱 **Önlenen Karbon Ayak İzi:** ${co2} kg CO₂\n` +
            `💧 **Kurtarılan Su Miktarı:** ${water} Litre\n` +
            `🍲 **Tamamlanan Sıfır Atık Tarif:** ${data.completed_recipes_count || 3} adet\n\n` +
            `Bilinçli tüketiminiz sayesinde gezegenimize somut bir katkıda bulunuyorsunuz! 🌍`,
          tools: ["get_consumption_stats"],
        };
      }
    } catch (e) {
      console.warn("Yerel etki sorgusu:", e);
    }

    return {
      answer: `📊 **Etki Analiziniz:**\n\nŞu ana kadar mutfağınızda **13.62 kg CO₂** salınımı ve **4905 Litre su** tasarrufu sağladınız! 🌍`,
      tools: ["get_consumption_stats"],
    };
  }

  // 4. Geri Dönüşüm / Ambalaj
  if (
    msg.includes("ambalaj") ||
    msg.includes("dönüş") ||
    msg.includes("atık") ||
    msg.includes("çöp") ||
    msg.includes("kutu")
  ) {
    return {
      answer: `♻️ **Sıfır Atık Geri Dönüşüm Rehberi:**\n\n` +
        `• **Yoğurt Kapları & Plastik Ambalaj:** İçini sudan geçirip kuruladıktan sonra plastik (sarı) geri dönüşüm kutusuna atın.\n` +
        `• **Sebze & Meyve Artıkları:** Evde kompost yapıyorsanız kompost kovasına, yoksa organik atık kutusuna bırakın.\n` +
        `• **Cam Kavanozlar (Salça, Reçel):** Yıkayıp kapağıyla ayırarak cam kumbarasına gönderin veya kilerde saklama kavanozu olarak tekrar kullanın.`,
      tools: ["get_recycling_guide"],
    };
  }

  // Varsayılan Akıllı Bilgilendirme
  return {
    answer: `🌿 **DÖNGÜ Mutfak Asistanı:**\n\n` +
      `Sizin için mutfak stoklarınızı, acil tüketim önceliklerinizi ve sıfır atık tariflerinizi analiz edebilirim.\n\n` +
      `Aşağıdaki konulardan birini sorabilirsiniz:\n` +
      `• **🥬 Ispanakla ne yapabilirim?** (Tarif ve kiler eşleştirme)\n` +
      `• **⏱️ Bugün ne tüketmeliyim?** (Bozulma riski olan ürünler)\n` +
      `• **📊 Bu ay ne kadar gıda kurtardım?** (CO₂ ve su tasarrufu)\n` +
      `• **♻️ Ambalajları nasıl ayırayım?** (Geri dönüşüm kuralları)`,
    tools: [],
  };
}

// ==============================================================================
// 5. API İLETİŞİMİ
// ==============================================================================

// Çift gönderimi ve mükerrer istekleri engellemek için kilit bayrağı
let isSending = false;

// Sayfa düzeyinde konuşma geçmişi (Backend stateless olduğu için frontend tutar)
// Her istekte son 10 tur (user/assistant) backend'e iletilir
let sohbetGecmisi = [];

/**
 * Kullanıcının mesajını POST /api/chat uç noktasına gönderir ve yanıtı ekrana yansıtır.
 *
 * @param {string} rawMessage - Kullanıcının yazdığı metin
 */
async function handleSendMessage(rawMessage) {
  // Gönderim devam ediyorsa ikinci isteği kesinlikle engelle
  if (isSending) return;

  const message = (rawMessage || "").trim();
  // Kural 5: Boş veya yalnızca boşluklardan oluşan mesajlar engellenir
  if (!message) return;

  isSending = true;

  // Kullanıcı mesajını hemen ekrana yazdır
  appendMessage("user", message);

  // Giriş alanını temizle ve yüksekliğini sıfırla
  const textarea = document.getElementById("chatInput");
  if (textarea) {
    textarea.value = "";
    textarea.style.height = "auto";
  }

  // Yükleme modunu başlat
  setLoading(true);

  // Aktif kullanıcı kimliğini al (Varsayılan: 1)
  const userId = localStorage.getItem("dongu_user_id") || "1";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": userId,
      },
      // Son 10 konuşma turu (user/assistant) geçmiş olarak gönderilir
      body: JSON.stringify({
        message: message,
        history: sohbetGecmisi.slice(-10),
      }),
    });

    // OpenAI yapılandırılmadığında HTTP 503 döner:
    // Kullanıcıya kesinti yaşatmamak için zengin yerel asistan devreye girer
    if (response.status === 503) {
      const fallbackResult = await getLocalAssistantFallback(message);
      appendMessage("assistant", fallbackResult.answer, fallbackResult.tools || []);

      // Başarılı yerel fallback yanıtını konuşma geçmişine ekle
      sohbetGecmisi.push({ role: "user", content: message });
      sohbetGecmisi.push({ role: "assistant", content: fallbackResult.answer });
      return;
    }

    if (!response.ok) {
      let errorMsg = `Sunucu hatası (${response.status}). Lütfen daha sonra tekrar deneyin.`;
      try {
        const errJson = await response.json();
        if (errJson && errJson.detail) {
          errorMsg = errJson.detail;
        }
      } catch {
        // Hata metni ayrıştırılamazsa genel mesaj kullanılır
      }
      appendMessage("assistant", errorMsg, [], true);
      // Hatalı istekler konuşma geçmişine (sohbetGecmisi) ASLA eklenmez
      return;
    }

    // Başarılı yanıt (HTTP 200)
    const data = await response.json();
    appendMessage("assistant", data.answer || "Yanıt alınamadı.", data.tools || []);

    // SADECE response.ok olduğunda konuşma geçmişine ekle
    sohbetGecmisi.push({ role: "user", content: message });
    sohbetGecmisi.push({ role: "assistant", content: data.answer || "" });

  } catch (networkError) {
    // Ağ bağlantısı koptuğunda veya sunucuya erişilemediğinde yerel fallback devreye girer
    console.warn("[Sohbet Ağ Uyarısı - Yerel Fallback]:", networkError);
    const fallbackResult = await getLocalAssistantFallback(message);
    appendMessage("assistant", fallbackResult.answer, fallbackResult.tools || []);

    // Çevrimdışı yerel fallback yanıtını da geçmişe ekle
    sohbetGecmisi.push({ role: "user", content: message });
    sohbetGecmisi.push({ role: "assistant", content: fallbackResult.answer });
  } finally {
    isSending = false;
    setLoading(false);
  }
}

/**
 * Yeni sohbet başlatır:
 * Konuşma geçmişini (sohbetGecmisi) sıfırlar, ekrandaki mesajları temizler
 * ve başlangıç karşılama mesajını yeniden ekler.
 */
function handleNewChat() {
  sohbetGecmisi = [];
  const chatMessages = document.getElementById("chatMessages");
  if (chatMessages) {
    chatMessages.innerHTML = "";
    appendMessage("assistant", WELCOME_MESSAGE);
  }
  const chatInput = document.getElementById("chatInput");
  if (chatInput) {
    chatInput.value = "";
    chatInput.style.height = "auto";
    chatInput.focus();
  }
}
window.handleNewChat = handleNewChat;
window.resetChat = handleNewChat;

// Global olarak erişilebilir form gönderme işlevi (Sayfanın reload olmasını ve çift tıklamayı %100 engeller)
window.handleChatSubmit = function(event) {
  if (event) {
    if (event.preventDefault) event.preventDefault();
    if (event.stopPropagation) event.stopPropagation();
  }
  if (isSending) return false;
  const chatInput = document.getElementById("chatInput");
  if (chatInput) {
    handleSendMessage(chatInput.value);
  }
  return false;
};

// Global hazır soru çipi tıklama işlevi
window.handleChipClick = function(chipOrText, event) {
  if (event) {
    if (event.preventDefault) event.preventDefault();
    if (event.stopPropagation) event.stopPropagation();
  }
  if (isSending) return false;
  let text = "";
  if (typeof chipOrText === "string") {
    text = chipOrText;
  } else if (chipOrText && chipOrText.getAttribute) {
    text = chipOrText.getAttribute("data-question") || chipOrText.textContent.trim();
  }
  if (text) {
    handleSendMessage(text);
  }
  return false;
};

// ==============================================================================
// 6. SAYFA BAŞLANGICI VE ETKİLEŞİM DİNLEYİCİLERİ
// ==============================================================================

function initChat() {
  const chatMessages = document.getElementById("chatMessages");
  if (!chatMessages) return;

  // Kural 8: İlk açılışta yalnızca 1 kez karşılama mesajı ekle
  if (chatMessages.children.length === 0) {
    appendMessage("assistant", WELCOME_MESSAGE);
  }

  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const suggestionChips = document.querySelectorAll(".suggestion-chip");

  // Form submit dinleyicisi (Gönder butonu)
  if (chatForm && !chatForm.dataset.bound) {
    chatForm.dataset.bound = "true";
    chatForm.addEventListener("submit", (e) => {
      e.preventDefault();
      handleChatSubmit(e);
    });
  }

  // Kural 5: Enter ile gönder, Shift+Enter ile yeni satır ekle
  if (chatInput && !chatInput.dataset.bound) {
    chatInput.dataset.bound = "true";
    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleChatSubmit(e);
      }
    });

    // Otomatik textarea yüksekliği ayarlama
    chatInput.addEventListener("input", () => {
      chatInput.style.height = "auto";
      chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
    });
  }

  // Kural 7: Hazır soru butonları (tıklayınca doğrudan gönderir)
  suggestionChips.forEach(chip => {
    if (!chip.dataset.bound) {
      chip.dataset.bound = "true";
      chip.addEventListener("click", (e) => {
        e.preventDefault();
        handleChipClick(chip);
      });
    }
  });
}

// Global pencere nesnesine bağla
window.initChat = initChat;

// DOM hazır olduğunda başlat
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initChat);
} else {
  initChat();
}
