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
// 5. API İLETİŞİMİ
// ==============================================================================

/**
 * Kullanıcının mesajını POST /api/chat uç noktasına gönderir ve yanıtı ekrana yansıtır.
 *
 * @param {string} rawMessage - Kullanıcının yazdığı metin
 */
async function handleSendMessage(rawMessage) {
  const message = (rawMessage || "").trim();
  // Kural 5: Boş veya yalnızca boşluklardan oluşan mesajlar engellenir
  if (!message) return;

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
      body: JSON.stringify({ message: message }),
    });

    // Kural 6: 503 durumunda API'nin sadeleştirilmiş 'detail' mesajını göster
    if (response.status === 503) {
      let detailMsg = "Asistan şu an ulaşılamıyor, birazdan tekrar dene.";
      try {
        const errJson = await response.json();
        if (errJson && errJson.detail) {
          detailMsg = errJson.detail;
        }
      } catch {
        // Yanıt JSON değilse varsayılan mesaj kalır
      }
      appendMessage("assistant", detailMsg, [], true);
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
      return;
    }

    // Başarılı yanıt (HTTP 200)
    const data = await response.json();
    appendMessage("assistant", data.answer || "Yanıt alınamadı.", data.tools || []);

  } catch (networkError) {
    // Kural 6: Ağ bağlantısı koptuğunda sayfa kırılmaz, kullanıcı bilgilendirilir
    console.error("[Sohbet Ağ Hatası]:", networkError);
    appendMessage(
      "assistant",
      "Sunucuya ulaşılamadı. Lütfen sunucunun (FastAPI) çalıştığından ve internet bağlantınızdan emin olun.",
      [],
      true
    );
  } finally {
    setLoading(false);
  }
}

// Global olarak erişilebilir form gönderme işlevi (Sayfanın reload olmasını %100 engeller)
window.handleChatSubmit = function(event) {
  if (event && event.preventDefault) {
    event.preventDefault();
  }
  const chatInput = document.getElementById("chatInput");
  if (chatInput) {
    handleSendMessage(chatInput.value);
  }
  return false;
};

// Global hazır soru çipi tıklama işlevi
window.handleChipClick = function(chipOrText) {
  let text = "";
  if (typeof chipOrText === "string") {
    text = chipOrText;
  } else if (chipOrText && chipOrText.getAttribute) {
    text = chipOrText.getAttribute("data-question") || chipOrText.textContent.trim();
  }
  if (text) {
    handleSendMessage(text);
  }
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
