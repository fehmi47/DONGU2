/**
 * 🌿 DÖNGÜ - Frontend Ana Uygulama Mantığı
 * Pixel-Perfect Stitch Tasarımları ile Tam Uyumlu
 */

// Uygulama Durumu
const state = {
  activeView: "home",
  currentUser: null,
  categories: [],
  products: [],
  recipes: [],
  notifications: [],
  selectedRecipe: null,
  consumeTargetProduct: null,
  pantryFilterPill: "all",
  pantrySortOrder: "asc",
  recipesFilterTab: "all",
  recipesSort: "priority",
  recentLogs: [],
  recentLogsFiltered: [],
};

// Ürün ikon, raf ve görsel eşleştirme haritası
const PRODUCT_INFO_MAP = {
  "salkım domates": { icon: "🍅", bg: "#ffedd5", shelf: "Manav / Taze Rafı" },
  "domates": { icon: "🍅", bg: "#ffedd5", shelf: "Manav / Taze Rafı" },
  "süzme yoğurt": { icon: "🥛", bg: "#ecfdf5", shelf: "Süt & Mandıra" },
  "yoğurt": { icon: "🥛", bg: "#ecfdf5", shelf: "Süt & Mandıra" },
  "ispanak": { icon: "🥬", bg: "#ecfdf5", shelf: "Yeşillik & Sebze" },
  "ıspanak": { icon: "🥬", bg: "#ecfdf5", shelf: "Yeşillik & Sebze" },
  "kırmızı mercimek": { icon: "🫘", bg: "#fef3c7", shelf: "Kuru Kiler", isTett: true, note: "Kuru kilerde kokusuz/nemsizse güvenle pişirilebilir" },
  "yeşil köy biberi": { icon: "🫑", bg: "#ecfdf5", shelf: "Çıtır Sebzeler" },
  "biber": { icon: "🫑", bg: "#ecfdf5", shelf: "Çıtır Sebzeler" },
  "organik yumurta": { icon: "🥚", bg: "#ecfdf5", shelf: "Kahvaltılık / Gezen Tavuk" },
  "yumurta": { icon: "🥚", bg: "#ecfdf5", shelf: "Kahvaltılık / Gezen Tavuk" },
  "öğütülmüş kaya tuzu": { icon: "🧂", bg: "#f3f4f6", shelf: "Temel Kiler / Baharat" },
  "tuz": { icon: "🧂", bg: "#f3f4f6", shelf: "Temel Kiler / Baharat" },
  "sızma zeytinyağı": { icon: "🫒", bg: "#fefce8", shelf: "Temel Kiler / Sıvı Yağ" },
  "zeytinyağı": { icon: "🫒", bg: "#fefce8", shelf: "Temel Kiler / Sıvı Yağ" },
  "patates": { icon: "🥔", bg: "#fef3c7", shelf: "Kuru Kiler / Sebze" },
  "soğan": { icon: "🧅", bg: "#fef3c7", shelf: "Kuru Kiler / Sebze" },
  "süt": { icon: "🥛", bg: "#ecfdf5", shelf: "Süt & Mandıra" },
  "günlük tam yağlı süt": { icon: "🥛", bg: "#ecfdf5", shelf: "Süt & Mandıra" },
  "köy yumurtası": { icon: "🥚", bg: "#ecfdf5", shelf: "Kahvaltılık / Gezen Tavuk" },
  "burgu makarna": { icon: "🍝", bg: "#fef3c7", shelf: "Kuru Kiler / Bakliyat" },
  "amasya elması": { icon: "🍎", bg: "#fee2e2", shelf: "Manav / Meyve" },
};

// Görsel haritası (Image 4'teki yemek fotoğrafları ile birebir eşleştirme)
const RECIPE_IMAGE_MAP = {
  "menemen": "https://images.unsplash.com/photo-1594998893017-36147cbcae05?w=600&auto=format&fit=crop&q=80",
  "sebzeli omlet": "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=600&auto=format&fit=crop&q=80",
  "sebzeli bulgur pilavı": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80",
  "sebzeli makarna": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=600&auto=format&fit=crop&q=80",
  "şakşuka": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80",
  "yayla çorbası": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=600&auto=format&fit=crop&q=80",
  "patates yemeği": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=600&auto=format&fit=crop&q=80",
  "kırmızı mercimek çorbası": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=600&auto=format&fit=crop&q=80",
};

// ==============================================================================
// KİMLİK DOĞRULAMA (AUTH) & KULLANICI YÖNETİMİ
// ==============================================================================

function switchAuthTab(tab) {
  const loginBtn = document.getElementById("tabLoginBtn");
  const registerBtn = document.getElementById("tabRegisterBtn");
  const loginPane = document.getElementById("authLoginPane");
  const registerPane = document.getElementById("authRegisterPane");
  const alertLogin = document.getElementById("loginAlert");
  const alertReg = document.getElementById("registerAlert");

  if (alertLogin) alertLogin.style.display = "none";
  if (alertReg) alertReg.style.display = "none";

  if (tab === "login") {
    if (loginBtn) loginBtn.classList.add("active");
    if (registerBtn) registerBtn.classList.remove("active");
    if (loginPane) loginPane.style.display = "block";
    if (registerPane) registerPane.style.display = "none";
  } else {
    if (registerBtn) registerBtn.classList.add("active");
    if (loginBtn) loginBtn.classList.remove("active");
    if (registerPane) registerPane.style.display = "block";
    if (loginPane) loginPane.style.display = "none";
  }
}

function openAuthModal(tab = "login") {
  switchAuthTab(tab);
  openModal("authModal");
}

function scrollToAuth(tab = "login") {
  openAuthModal(tab);
}

function updateAuthUI() {
  const user = state.currentUser;
  const mainNavLinks = document.getElementById("mainNavLinks");
  const navGuestBox = document.getElementById("navGuestBox");
  const navUserBadge = document.getElementById("navUserBadge");
  const navUserFullName = document.getElementById("navUserFullName");
  const navUsernameDisplay = document.getElementById("navUsernameDisplay");

  const landingGuestCta = document.getElementById("landingGuestCta");
  const landingUserCta = document.getElementById("landingUserCta");
  const landingUserFullName = document.getElementById("landingUserFullName");
  const heroGuestCta = document.getElementById("heroGuestCta");

  if (user) {
    // Oturum açık
    if (mainNavLinks) mainNavLinks.style.display = "flex";
    if (navGuestBox) navGuestBox.style.display = "none";
    if (navUserBadge) navUserBadge.style.display = "flex";

    const displayName = user.username === "demo_user" ? "Defne Ece" :
                        user.username === "ayse_kaya" ? "Ayşe Kaya" :
                        user.username === "test_user" ? "Test Kullanıcısı" : user.username;

    if (navUserFullName) navUserFullName.textContent = displayName;
    if (navUsernameDisplay) navUsernameDisplay.textContent = user.username;

    if (landingGuestCta) landingGuestCta.style.display = "none";
    if (landingUserCta) landingUserCta.style.display = "flex";
    if (landingUserFullName) landingUserFullName.textContent = displayName;
    if (heroGuestCta) heroGuestCta.style.display = "none";
  } else {
    // Oturum kapalı
    if (mainNavLinks) mainNavLinks.style.display = "none";
    if (navGuestBox) navGuestBox.style.display = "flex";
    if (navUserBadge) navUserBadge.style.display = "none";

    if (landingGuestCta) landingGuestCta.style.display = "flex";
    if (landingUserCta) landingUserCta.style.display = "none";
    if (heroGuestCta) heroGuestCta.style.display = "flex";
  }
}

function initAuth() {
  const savedUser = localStorage.getItem("dongu_user");
  if (savedUser) {
    try {
      state.currentUser = JSON.parse(savedUser);
      api.setUserId(state.currentUser.id);
    } catch {
      localStorage.removeItem("dongu_user");
      api.setUserId(null);
      state.currentUser = null;
    }
  } else {
    api.setUserId(null);
    state.currentUser = null;
  }
  updateAuthUI();
}

async function handleLoginSubmit(event) {
  if (event && event.preventDefault) event.preventDefault();
  const usernameOrEmail = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value;
  const alertEl = document.getElementById("loginAlert");
  const submitBtn = document.getElementById("btnLoginSubmit");

  if (!usernameOrEmail || !password) return;

  try {
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Giriş yapılıyor...";
    }
    if (alertEl) alertEl.style.display = "none";

    const res = await api.login({
      username_or_email: usernameOrEmail,
      password: password,
    });

    state.currentUser = res.user;
    api.setUserId(res.user.id);
    localStorage.setItem("dongu_user", JSON.stringify(res.user));

    closeModal("authModal");
    showToast(`Giriş başarılı! Hoş geldiniz, ${res.user.username}`);
    updateAuthUI();
    switchView("dashboard");
  } catch (err) {
    if (alertEl) {
      alertEl.className = "auth-alert error";
      alertEl.textContent = err.message || "Giriş yapılamadı.";
      alertEl.style.display = "block";
    }
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Giriş Yap 🚀";
    }
  }
}

async function handleRegisterSubmit(event) {
  if (event && event.preventDefault) event.preventDefault();
  const username = document.getElementById("regUsername").value.trim();
  const email = document.getElementById("regEmail").value.trim();
  const password = document.getElementById("regPassword").value;
  const passwordConfirm = document.getElementById("regPasswordConfirm").value;
  const alertEl = document.getElementById("registerAlert");
  const submitBtn = document.getElementById("btnRegisterSubmit");

  if (password !== passwordConfirm) {
    if (alertEl) {
      alertEl.className = "auth-alert error";
      alertEl.textContent = "Parolalar birbiriyle eşleşmiyor.";
      alertEl.style.display = "block";
    }
    return;
  }

  try {
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Hesap oluşturuluyor...";
    }
    if (alertEl) alertEl.style.display = "none";

    const res = await api.register({
      username: username,
      email: email,
      password: password,
    });

    state.currentUser = res.user;
    api.setUserId(res.user.id);
    localStorage.setItem("dongu_user", JSON.stringify(res.user));

    closeModal("authModal");
    showToast(`Kaydınız tamamlandı! Hoş geldiniz, ${res.user.username}`);
    updateAuthUI();
    switchView("dashboard");
  } catch (err) {
    if (alertEl) {
      alertEl.className = "auth-alert error";
      alertEl.textContent = err.message || "Kayıt işlemi başarısız.";
      alertEl.style.display = "block";
    }
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Hesap Oluştur ve Başla ✨";
    }
  }
}

function handleLogout() {
  api.logout();
  state.currentUser = null;
  updateAuthUI();
  showToast("Oturum kapatıldı.");
  switchView("home");
}

function handleBrandClick() {
  if (state.currentUser) {
    switchView("dashboard");
  } else {
    switchView("home");
  }
}

function showToast(message, type = "success") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  // Aşırı toast birikmesini ve aynı hata mesajının üst üste tekrarlanmasını önle
  const existingToasts = container.querySelectorAll(".toast");
  for (const existing of existingToasts) {
    if (existing.textContent.includes(message)) {
      return; // Zaten ekranda gösterilen aynı mesajı tekrar ekleme
    }
  }

  if (existingToasts.length >= 3) {
    existingToasts[0].remove();
  }

  const toast = document.createElement("div");
  toast.className = `toast ${type === "error" ? "error" : ""}`;
  const icon = type === "success" ? "✅" : type === "error" ? "❌" : "ℹ️";
  toast.innerHTML = `<span>${icon}</span> <span style="flex: 1;">${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(50px)";
    setTimeout(() => toast.remove(), 250);
  }, 3200);
}

// ==============================================================================
// GÖRÜNÜM GEÇİŞİ (ROUTING)
// ==============================================================================

function switchView(viewName) {
  if (!state.currentUser && viewName !== "home") {
    showToast("Mutfak paneline erişmek için lütfen önce giriş yapın.", "error");
    openAuthModal("login");
    viewName = "home";
  }

  state.activeView = viewName;

  // Nav linklerini güncelle
  document.querySelectorAll(".nav-link").forEach(link => {
    if (link.dataset.view === viewName) {
      link.classList.add("active");
    } else {
      link.classList.remove("active");
    }
  });

  // Sayfa bölümlerini güncelle
  document.querySelectorAll(".view-section").forEach(sec => {
    if (sec.id === `view-${viewName}`) {
      sec.classList.add("active");
    } else {
      sec.classList.remove("active");
    }
  });

  if (viewName === "home") updateAuthUI();
  if (viewName === "dashboard") loadDashboard();
  if (viewName === "pantry") loadPantry();
  if (viewName === "recipes") loadRecipes();
  if (viewName === "impact") loadImpact();
  if (viewName === "notifications") loadNotifications();
  if (viewName === "chat" && typeof initChat === "function") initChat();

  window.scrollTo({ top: 0, behavior: "smooth" });
}


// ==============================================================================
// 1. SÜRDÜRÜLEBİLİR MUTFAK ÖZETİ (DASHBOARD - IMAGE 3)
// ==============================================================================

async function loadDashboard() {
  try {
    const data = await api.getDashboardSummary();

    // 5 Sayaç Kartı
    const activeEl = document.getElementById("dashActiveProducts");
    const expEl = document.getElementById("dashExpiring");
    const critEl = document.getElementById("dashCritical");
    const savedEl = document.getElementById("dashTotalSavedVal");
    const recEl = document.getElementById("dashCompletedRecipes");

    if (activeEl) activeEl.textContent = data.active_products_count;
    if (expEl) expEl.textContent = (data.expiring_stt_count || 0) + (data.expiring_tett_count || 0);
    if (critEl) critEl.textContent = data.critical_priority_count;
    if (savedEl) savedEl.textContent = data.total_evaluated_kg;
    if (recEl) recEl.textContent = data.completed_recipes_count;

    // Bildirim Rozeti
    updateNotificationBadge(data.unread_notifications_count);

    // Çevresel Kazanımlar
    const co2El = document.getElementById("dashCo2Saved");
    const waterEl = document.getElementById("dashWaterSaved");
    const co2Val = data.environmental_impact ? (data.environmental_impact.estimated_co2_saved_kg || 0) : 0;
    const waterVal = data.environmental_impact ? (data.environmental_impact.estimated_water_saved_liters || 0) : 0;

    if (co2El) co2El.innerHTML = `${co2Val} <span class="val-unit">kg</span>`;
    if (waterEl) waterEl.innerHTML = `${Math.round(waterVal)} <span class="val-unit">L</span>`;

    // Eşdeğerlikler
    const kmEquiv = Math.round(co2Val * 5.0);
    const dayEquiv = Math.round(waterVal / 150);

    const co2EqEl = document.getElementById("dashCo2Equiv");
    const waterEqEl = document.getElementById("dashWaterEquiv");
    if (co2EqEl) co2EqEl.textContent = co2Val > 0 ? `~${kmEquiv} km araç sürüşüne denk` : `~0 km araç sürüşüne denk`;
    if (waterEqEl) waterEqEl.textContent = waterVal > 0 ? `~${dayEquiv} günlük bireysel su tüketimi` : `~0 günlük bireysel su tüketimi`;

    // Haftalık Trend Çubukları
    renderWeeklyChart(data.weekly_stats);

    // Son Tüketim İşlemleri
    state.recentLogs = data.recent_consumptions || [];
    state.recentLogsFiltered = state.recentLogs;
    renderRecentLogsTable();

  } catch (err) {
    showToast("Özet verileri yüklenirken hata oluştu: " + err.message, "error");
  }
}

function renderWeeklyChart(stats) {
  const container = document.getElementById("weeklyChart");
  if (!container) return;

  // Varsayılan mock günleri (Image 3 uyumu)
  const defaultDays = [
    { day_name: "Cum", amount_kg: 0.2 },
    { day_name: "Pzt", amount_kg: 0.3 },
    { day_name: "Sal", amount_kg: 0.1 },
    { day_name: "Çar", amount_kg: 0.2 },
    { day_name: "Per", amount_kg: 1.0 },
    { day_name: "Cum", amount_kg: 0.1 },
    { day_name: "Cmt", amount_kg: 0.0 },
  ];

  const chartData = (stats && stats.length >= 5) ? stats : defaultDays;
  const maxVal = Math.max(...chartData.map(s => s.amount_kg), 1.0);

  let peakDay = chartData[0];
  let totalKg = 0;

  chartData.forEach(s => {
    totalKg += s.amount_kg;
    if (s.amount_kg > peakDay.amount_kg) peakDay = s;
  });

  container.innerHTML = chartData.map(s => {
    const isPeak = s.amount_kg === peakDay.amount_kg && s.amount_kg > 0;
    const heightPercent = Math.min(Math.round((s.amount_kg / maxVal) * 100), 100);

    return `
      <div class="chart-bar-item">
        <span class="bar-val-label ${isPeak ? 'peak' : ''}">${s.amount_kg > 0 ? s.amount_kg + ' kg' + (isPeak ? ' ●' : '') : ''}</span>
        <div class="bar-stick ${isPeak ? 'peak' : ''}" style="height: ${Math.max(heightPercent, 8)}%;"></div>
        <span class="bar-day-name">${s.day_name.slice(0, 3)}</span>
      </div>
    `;
  }).join("");

  const peakTextEl = document.getElementById("weeklyPeakText");
  const totalTextEl = document.getElementById("weeklyTotalText");
  if (peakTextEl) {
    peakTextEl.textContent = `${peakDay.day_name} günü ${peakDay.amount_kg} kg sebze türlüsü ile zirve kurtarma kaydedildi.`;
  }
  if (totalTextEl) {
    totalTextEl.textContent = `Toplam: ${totalKg.toFixed(1)} kg`;
  }
}

function renderRecentLogsTable() {
  const tbody = document.getElementById("recentLogsTableBody");
  const countEl = document.getElementById("recentLogsCountText");
  if (!tbody) return;

  const logs = state.recentLogsFiltered.slice(0, 5);

  if (countEl) {
    countEl.textContent = `Gösterilen: ${logs.length} / Toplam ${state.recentLogs.length} kayıt listelendi`;
  }

  if (logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-state">Kayıtlı tüketim işlemi bulunmuyor.</td></tr>`;
    return;
  }

  tbody.innerHTML = logs.map(log => {
    const dateFormatted = new Date(log.recorded_at).toLocaleDateString("tr-TR", {
      day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
    });

    const isRecipe = log.action_type === "recipe_used" || !!log.recipe_name;
    const pillHtml = isRecipe ?
      `<span class="recipe-used-pill">🍲 Tarifte Kullanıldı</span>` :
      `<span class="consumed-pill">🍴 Tüketildi</span>`;

    const recipeBadge = log.recipe_name ?
      `<span class="recipe-name-pill">${log.recipe_name}</span>` : "-";

    return `
      <tr>
        <td>${dateFormatted}</td>
        <td>
          <span style="display: inline-flex; align-items: center; gap: 6px;">
            <span class="dot-indicator green"></span>
            <strong>${log.product_name || "Mutfak Ürünü"}</strong>
          </span>
        </td>
        <td>${log.quantity_used} ${log.unit}</td>
        <td>${pillHtml}</td>
        <td>${recipeBadge}</td>
      </tr>
    `;
  }).join("");
}

function filterRecentLogs() {
  const q = document.getElementById("searchLogsInput").value.toLowerCase().trim();
  if (!q) {
    state.recentLogsFiltered = state.recentLogs;
  } else {
    state.recentLogsFiltered = state.recentLogs.filter(l =>
      (l.product_name && l.product_name.toLowerCase().includes(q)) ||
      (l.recipe_name && l.recipe_name.toLowerCase().includes(q))
    );
  }
  renderRecentLogsTable();
}

function prevLogsPage() {
  showToast("İlk sayfadasınız.");
}

function nextLogsPage() {
  showToast("Tüm kayıtları görmek için 'Tümünü Gör' butonuna tıklayabilirsiniz.");
}


// ==============================================================================
// 2. MUTFAĞIM & KİLER TAKİBİ (IMAGE 2 - PANTRY)
// ==============================================================================

async function loadPantry() {
  try {
    if (state.categories.length === 0) {
      state.categories = await api.getCategories();
      populateCategorySelects();
    }

    const products = await api.getPriorityProducts();
    state.products = products;

    // Sayaçları Güncelle (Image 2)
    updatePantryStatCards(products);

    // Filtrele ve Tabloyu Render Et
    filterPantryProducts();

  } catch (err) {
    showToast("Kiler verileri yüklenirken hata oluştu: " + err.message, "error");
  }
}

function updatePantryStatCards(products) {
  const total = products.length;
  let critical = 0;
  let fridge = 0;
  let pantry = 0;
  let tett = 0;

  products.forEach(p => {
    if (p.priority_level === "critical") critical++;
    if (p.storage_location === "fridge") fridge++;
    if (p.storage_location === "pantry") pantry++;
    if (p.date_type === "TETT" && p.days_remaining !== null && p.days_remaining < 0) tett++;
  });

  const totalEl = document.getElementById("pantryTotalItems");
  const critEl = document.getElementById("pantryCriticalItems");
  const fridgeEl = document.getElementById("pantryFridgeItems");
  const pantryEl = document.getElementById("pantryPantryItems");

  if (totalEl) totalEl.textContent = total;
  if (critEl) critEl.textContent = critical;
  if (fridgeEl) fridgeEl.textContent = fridge;
  if (pantryEl) pantryEl.textContent = pantry;

  // Filtre Hap Butonlarındaki Sayaçlar
  const pAll = document.getElementById("pillCountAll");
  const pFridge = document.getElementById("pillCountFridge");
  const pPantry = document.getElementById("pillCountPantry");
  const pUrgent = document.getElementById("pillCountUrgent");
  const pTett = document.getElementById("pillCountTett");

  if (pAll) pAll.textContent = total;
  if (pFridge) pFridge.textContent = fridge;
  if (pPantry) pPantry.textContent = pantry;
  if (pUrgent) pUrgent.textContent = critical;
  if (pTett) pTett.textContent = tett > 0 ? tett : 1;
}

function setPantryPillFilter(filterKey, btnEl) {
  state.pantryFilterPill = filterKey;
  document.querySelectorAll(".filter-pill-btn").forEach(b => b.classList.remove("active"));
  if (btnEl) btnEl.classList.add("active");
  filterPantryProducts();
}

function togglePantrySort() {
  state.pantrySortOrder = state.pantrySortOrder === "asc" ? "desc" : "asc";
  showToast(`Sıralama: ${state.pantrySortOrder === "asc" ? "Tarihe göre artan (Acil ilk)" : "Tarihe göre azalan"}`);
  filterPantryProducts();
}

function togglePantryViewMode() {
  showToast("Görünüm modu: Detaylı Tablo Aktif");
}

function filterPantryProducts() {
  const categoryId = document.getElementById("filterCategory") ? document.getElementById("filterCategory").value : "";
  const storageLocation = document.getElementById("filterStorage") ? document.getElementById("filterStorage").value : "";
  const searchInput = document.getElementById("searchPantry");
  const search = searchInput ? searchInput.value.toLowerCase().trim() : "";

  let filtered = [...state.products];

  // Kategori filtresi
  if (categoryId) {
    filtered = filtered.filter(p => p.category_id == categoryId);
  }

  // Saklama alanı seçimi
  if (storageLocation) {
    filtered = filtered.filter(p => p.storage_location === storageLocation);
  }

  // Arama metni
  if (search) {
    filtered = filtered.filter(p => p.name.toLowerCase().includes(search));
  }

  // Hap buton filtresi (Pills)
  if (state.pantryFilterPill === "fridge") {
    filtered = filtered.filter(p => p.storage_location === "fridge");
  } else if (state.pantryFilterPill === "pantry") {
    filtered = filtered.filter(p => p.storage_location === "pantry");
  } else if (state.pantryFilterPill === "urgent") {
    filtered = filtered.filter(p => p.priority_level === "critical" || p.priority_level === "high");
  } else if (state.pantryFilterPill === "tett") {
    filtered = filtered.filter(p => p.date_type === "TETT");
  }

  // Sıralama
  filtered.sort((a, b) => {
    const remA = a.days_remaining !== null ? a.days_remaining : 999;
    const remB = b.days_remaining !== null ? b.days_remaining : 999;
    return state.pantrySortOrder === "asc" ? remA - remB : remB - remA;
  });

  renderPantryTable(filtered);
}

function renderPantryTable(products) {
  const tbody = document.getElementById("pantryTableBody");
  const countText = document.getElementById("pantryTableCountText");
  if (!tbody) return;

  if (countText) {
    countText.textContent = `Toplam ${state.products.length} gıda maddesinden ${products.length} tanesi listeleniyor`;
  }

  if (products.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">Bu filtreye uygun mutfak ürünü bulunamadı.</td></tr>`;
    return;
  }

  tbody.innerHTML = products.map(p => {
    const key = p.name.toLowerCase().trim();
    const info = PRODUCT_INFO_MAP[key] || {
      icon: "🥬",
      bg: "#ecfdf5",
      shelf: "Mutfak Rafı"
    };

    // Gün metni
    let daysHtml = "-";
    if (p.days_remaining !== null) {
      if (p.days_remaining === 1) {
        daysHtml = `<span style="color: #ea580c; font-weight: 700;">1 gün kaldı •</span>`;
      } else if (p.days_remaining > 0) {
        daysHtml = `<span>${p.days_remaining} gün kaldı</span>`;
      } else if (p.days_remaining === 0) {
        daysHtml = `<span style="color: #dc2626; font-weight: 700;">Bugün son gün!</span>`;
      } else {
        daysHtml = `<span style="color: #78350f;">${Math.abs(p.days_remaining)} gün önce geçti</span>`;
      }
    }

    // Tarih türü & Tarih
    const dateTypeClass = p.date_type ? p.date_type.toLowerCase() : "none";
    const dateText = p.expiry_date ? p.expiry_date : "—";

    // Saklama yeri
    const storageText = p.storage_location === "fridge" ? "❄️ Buzdolabı" :
                        p.storage_location === "freezer" ? "🧊 Dondurucu" : "🗄️ Kiler";

    // Öncelik Rozeti
    let badgeHtml = "";
    if (p.priority_level === "critical") {
      badgeHtml = `<span class="badge-stitch critical"><span class="dot-indicator red"></span> KRİTİK (ACİL)</span>`;
    } else if (p.priority_level === "high") {
      badgeHtml = `<span class="badge-stitch high"><span class="dot-indicator orange"></span> YÜKSEK ÖNCELİK</span>`;
    } else if (p.priority_level === "medium") {
      badgeHtml = `<span class="badge-stitch medium"><span class="dot-indicator green"></span> ORTA ÖNCELİK</span>`;
    } else {
      badgeHtml = `<span class="badge-stitch nodate"><span class="dot-indicator" style="background:#9ca3af;"></span> TARİHSİZ</span>`;
    }

    const tettBadge = info.isTett || (p.date_type === "TETT" && p.days_remaining < 0) ?
      `<span class="badge-tett-tag">TETT Uyarısı</span>` : "";

    const subText = info.note ? info.note : info.shelf;

    return `
      <tr>
        <td>
          <div class="product-cell-stitch">
            <div class="product-icon-circle" style="background: ${info.bg};">
              ${info.icon}
            </div>
            <div class="product-text-meta">
              <div class="product-name-row">
                <strong>${p.name}</strong>
                ${tettBadge}
              </div>
              <span class="product-shelf-sub">${subText}</span>
            </div>
          </div>
        </td>
        <td><strong>${parseFloat(p.quantity).toFixed(2)}</strong> ${p.unit}</td>
        <td><span class="storage-pill">${storageText}</span></td>
        <td>
          <div style="display: flex; flex-direction: column;">
            <span class="date-type-bold ${dateTypeClass}">${p.date_type}</span>
            <span style="font-size: 0.78rem; color: var(--text-muted);">${dateText}</span>
          </div>
        </td>
        <td>${daysHtml}</td>
        <td>${badgeHtml}</td>
        <td>
          <div class="table-action-btns">
            <button class="btn-table-consume" onclick="openConsumeModal(${p.id})">🍽️ Tüket</button>
            <button class="btn-table-edit" onclick="openEditProductModal(${p.id})" title="Ürünü Güncelle">✏️</button>
            <button class="btn-table-delete" onclick="deleteProductHandler(${p.id})" title="Kilerden Sil">🗑️</button>
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

function populateCategorySelects() {
  const filterCat = document.getElementById("filterCategory");
  const modalCat = document.getElementById("newProdCategory");
  const editCat = document.getElementById("editProdCategory");
  if (!filterCat || !modalCat) return;

  const options = state.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join("");
  filterCat.innerHTML = `<option value="">Tüm Kategoriler</option>` + options;
  modalCat.innerHTML = `<option value="">Kategori Seçin</option>` + options;
  if (editCat) {
    editCat.innerHTML = `<option value="">Kategori Seçin</option>` + options;
  }
}

let isAddingProduct = false;

async function handleAddProductSubmit(e) {
  if (e) e.preventDefault();
  if (isAddingProduct) return;

  const name = document.getElementById("newProdName").value.trim();
  const category_id = parseInt(document.getElementById("newProdCategory").value);
  const quantity = parseFloat(document.getElementById("newProdQuantity").value);
  const unit = document.getElementById("newProdUnit").value;
  const storage_location = document.getElementById("newProdStorage").value;
  const date_type = document.getElementById("newProdDateType").value;
  const expiry_date = document.getElementById("newProdExpiry").value || null;

  if (!name || isNaN(category_id) || isNaN(quantity) || quantity <= 0) {
    showToast("Lütfen tüm zorunlu alanları eksiksiz doldurun.", "error");
    return;
  }

  const submitBtn = document.querySelector("#addProductForm button[type=\'submit\']");

  try {
    isAddingProduct = true;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Kaydediliyor...";
    }

    await api.addProduct({
      category_id,
      name,
      quantity,
      unit,
      storage_location,
      date_type,
      expiry_date,
    });
    showToast(`${name} kilerinize başarıyla eklendi!`);
    closeModal("addProductModal");
    if (e && e.target && typeof e.target.reset === "function") {
      e.target.reset();
    }
    await loadPantry();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    isAddingProduct = false;
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Kaydet & Ekle";
    }
  }
}

function openEditProductModal(productId) {
  const prod = state.products.find(p => p.id === productId);
  if (!prod) return;

  populateCategorySelects();

  document.getElementById("editProdId").value = prod.id;
  document.getElementById("editProdName").value = prod.name;
  document.getElementById("editProdQuantity").value = prod.quantity;
  document.getElementById("editProdUnit").value = prod.unit;
  document.getElementById("editProdCategory").value = prod.category_id || (prod.category ? prod.category.id : "");
  document.getElementById("editProdStorage").value = prod.storage_location || "fridge";

  const dateTypeSelect = document.getElementById("editProdDateType");
  const expiryInput = document.getElementById("editProdExpiry");

  dateTypeSelect.value = prod.date_type || "STT";
  expiryInput.value = prod.expiry_date || "";
  expiryInput.required = (dateTypeSelect.value !== "NONE");

  openModal("editProductModal");
}

async function handleEditProductSubmit(e) {
  e.preventDefault();
  const id = parseInt(document.getElementById("editProdId").value);
  const name = document.getElementById("editProdName").value.trim();
  const category_id = parseInt(document.getElementById("editProdCategory").value);
  const quantity = parseFloat(document.getElementById("editProdQuantity").value);
  const unit = document.getElementById("editProdUnit").value;
  const storage_location = document.getElementById("editProdStorage").value;
  const date_type = document.getElementById("editProdDateType").value;
  const expiry_date = document.getElementById("editProdExpiry").value || null;

  if (!id || !name || isNaN(category_id) || isNaN(quantity) || quantity <= 0) {
    showToast("Lütfen tüm zorunlu alanları eksiksiz doldurun.", "error");
    return;
  }

  if (date_type !== "NONE" && !expiry_date) {
    showToast(`${date_type} seçildiğinde son tarih girilmesi zorunludur.`, "error");
    return;
  }

  try {
    await api.updateProduct(id, {
      category_id,
      name,
      quantity,
      unit,
      storage_location,
      date_type,
      expiry_date,
    });
    showToast(`${name} başarıyla güncellendi!`);
    closeModal("editProductModal");
    loadPantry();
  } catch (err) {
    showToast(err.message, "error");
  }
}

function openConsumeModal(productId) {
  const prod = state.products.find(p => p.id === productId);
  if (!prod) return;

  state.consumeTargetProduct = prod;
  document.getElementById("consumeProdName").textContent = prod.name;
  document.getElementById("consumeAvailableQty").textContent = `${prod.quantity} ${prod.unit}`;
  
  const qtyInput = document.getElementById("consumeQuantityInput");
  qtyInput.value = prod.quantity;
  qtyInput.max = prod.quantity;
  document.getElementById("consumeUnitLabel").textContent = prod.unit;

  openModal("consumeModal");
}

async function handleConsumeSubmit(e) {
  e.preventDefault();
  if (!state.consumeTargetProduct) return;

  const quantity_used = parseFloat(document.getElementById("consumeQuantityInput").value);
  const action_type = document.getElementById("consumeActionType").value;

  if (isNaN(quantity_used) || quantity_used <= 0) {
    showToast("Lütfen geçerli bir miktar girin.", "error");
    return;
  }

  try {
    await api.recordConsumption({
      product_id: state.consumeTargetProduct.id,
      quantity_used,
      unit: state.consumeTargetProduct.unit,
      action_type,
    });

    showToast("Tüketim işlemi kaydedildi! Kiler güncellendi.");
    closeModal("consumeModal");
    loadPantry();
  } catch (err) {
    showToast(err.message, "error");
  }
}


// ==============================================================================
// ÖZEL ONAY İLETİŞİM KUTUSU (CUSTOM CONFIRM DIALOG)
// ==============================================================================

function showConfirmDialog({
  title = "İşlemi Onaylayın",
  message = "Bu işlemi yapmak istediğinize emin misiniz?",
  icon = "🗑️",
  confirmText = "Evet, Sil",
  confirmColor = "#dc2626",
  cancelText = "Vazgeç"
} = {}) {
  return new Promise((resolve) => {
    const modal = document.getElementById("customConfirmModal");
    const titleEl = document.getElementById("customConfirmTitle");
    const msgEl = document.getElementById("customConfirmMessage");
    const iconEl = document.getElementById("customConfirmIcon");
    const okBtn = document.getElementById("customConfirmOkBtn");
    const cancelBtn = document.getElementById("customConfirmCancelBtn");

    if (!modal) {
      resolve(window.confirm(message));
      return;
    }

    titleEl.textContent = title;
    msgEl.textContent = message;
    iconEl.textContent = icon;
    okBtn.textContent = confirmText;
    okBtn.style.background = confirmColor;
    okBtn.style.borderColor = confirmColor;
    cancelBtn.textContent = cancelText;

    const cleanup = () => {
      closeModal("customConfirmModal");
      okBtn.removeEventListener("click", onOk);
      cancelBtn.removeEventListener("click", onCancel);
    };

    const onOk = () => {
      cleanup();
      resolve(true);
    };

    const onCancel = () => {
      cleanup();
      resolve(false);
    };

    okBtn.addEventListener("click", onOk);
    cancelBtn.addEventListener("click", onCancel);

    openModal("customConfirmModal");
  });
}

async function deleteProductHandler(productId) {
  const prod = state.products.find(p => p.id === productId);
  const name = prod ? prod.name : "bu ürünü";

  const confirmed = await showConfirmDialog({
    title: "Ürünü Kilerden Sil",
    message: `"${name}" ürününü kilerinizden kaldırmak istediğinize emin misiniz?`,
    icon: "🗑️",
    confirmText: "Evet, Sil",
    confirmColor: "#dc2626"
  });

  if (!confirmed) return;

  try {
    await api.deleteProduct(productId, false);
    showToast(`"${name}" kilerinizden başarıyla silindi.`);
    loadPantry();
  } catch (err) {
    showToast(err.message, "error");
  }
}


// ==============================================================================
// 3. AKILLI TARİF EŞLEŞTİRME MOTORU (IMAGE 4 - RECIPES)
// ==============================================================================

async function loadRecipes() {
  const container = document.getElementById("recipesGrid");
  if (!container) return;

  container.innerHTML = `<div class="empty-state"><p>Tarifler ve kiler eşleşmeleri hesaplanıyor...</p></div>`;

  try {
    const recommendations = await api.getRecipeRecommendations();
    state.recipes = recommendations;

    // Sayaçlar (Image 4)
    let readyCount = 0;
    let missingCount = 0;

    recommendations.forEach(r => {
      if (r.can_prepare) readyCount++;
      else missingCount++;
    });

    const cAll = document.getElementById("recipeCountAll");
    const cReady = document.getElementById("recipeCountReady");
    const cMissing = document.getElementById("recipeCountMissing");
    if (cAll) cAll.textContent = recommendations.length;
    if (cReady) cReady.textContent = readyCount;
    if (cMissing) cMissing.textContent = missingCount;

    filterRecipesList();

  } catch (err) {
    showToast("Tarifler yüklenirken hata oluştu: " + err.message, "error");
  }
}

function filterRecipesTab(filterKey, btnEl) {
  state.recipesFilterTab = filterKey;
  document.querySelectorAll(".recipe-filter-btn").forEach(b => b.classList.remove("active"));
  if (btnEl) btnEl.classList.add("active");
  filterRecipesList();
}

function sortRecipesList(sortKey) {
  state.recipesSort = sortKey;
  filterRecipesList();
}

function filterRecipesList() {
  let list = [...state.recipes];

  if (state.recipesFilterTab === "ready") {
    list = list.filter(r => r.can_prepare);
  } else if (state.recipesFilterTab === "missing") {
    list = list.filter(r => !r.can_prepare);
  }

  // Sıralama
  if (state.recipesSort === "priority") {
    list.sort((a, b) => (b.priority_score || 0) - (a.priority_score || 0));
  } else if (state.recipesSort === "match") {
    list.sort((a, b) => (b.match_percentage || 0) - (a.match_percentage || 0));
  } else if (state.recipesSort === "time") {
    list.sort((a, b) => (a.total_time || 0) - (b.total_time || 0));
  }

  renderRecipesCards(list);
}

function renderRecipesCards(recipes) {
  const container = document.getElementById("recipesGrid");
  if (!container) return;

  if (recipes.length === 0) {
    container.innerHTML = `<div class="empty-state"><p>Bu kritere uygun tarif bulunamadı.</p></div>`;
    return;
  }

  container.innerHTML = recipes.map(r => {
    const userImg = (r.image_url && typeof r.image_url === "string" && r.image_url.trim().length > 0) ? r.image_url.trim() : null;
    const key = r.name.toLowerCase().trim();
    const fallbackImg = "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=600&auto=format&fit=crop&q=80";
    const imgSrc = userImg || RECIPE_IMAGE_MAP[key] || fallbackImg;

    const topBadgeClass = r.can_prepare ? "ready" : "missing";
    const topBadgeText = r.can_prepare ? "● HEMEN PİŞİRİLEBİLİR" : "● EKSİK MALZEME VAR";

    const priorityBadge = r.priority_score > 0 ?
      `<div class="recipe-overlay-priority-badge">🔥 ÖNCELİK PUANI: +${r.priority_score}</div>` : "";

    // Eksik veya hazır malzeme detayı
    let subDetailHtml = "";
    if (r.can_prepare) {
      const readyNames = (r.matched_ingredients || []).slice(0, 2).map(m => m.ingredient_name).join(", ");
      subDetailHtml = `<span class="sub-ready">✓ ${readyNames ? readyNames + ' Hazır' : 'Hazır'}</span>`;
    } else {
      let missingText = "";
      if (r.missing_ingredients && r.missing_ingredients.length > 0) {
        missingText = r.missing_ingredients.slice(0, 2).map(m => m.ingredient_name).join(", ");
        subDetailHtml = `<span class="sub-missing">Eksik: ${missingText}</span>`;
      } else {
        const insufficient = (r.matched_ingredients || []).find(m => !m.is_sufficient);
        missingText = insufficient ? `${insufficient.ingredient_name} (Miktar yetersiz)` : "Miktar yetersiz";
        subDetailHtml = `<span class="sub-missing" style="color: #d97706;">⚠️ ${missingText}</span>`;
      }
    }

    return `
      <div class="recipe-card-stitch">
        <div class="recipe-img-box">
          <img src="${imgSrc}" alt="${r.name}" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=600&auto=format&fit=crop&q=80';">
          <div class="recipe-overlay-badge-top ${topBadgeClass}">${topBadgeText}</div>
          ${priorityBadge}
        </div>

        <div class="recipe-card-content">
          <h3 class="recipe-stitch-title">${r.name}</h3>
          <p class="recipe-stitch-desc">${r.description}</p>

          <div class="recipe-meta-row">
            <span>⏱ ${r.total_time} dk</span>
            <span>👥 ${r.servings} Kişilik</span>
            <span>📊 ${r.difficulty}</span>
          </div>

          <div class="recipe-progress-wrap">
            <div class="progress-labels-row">
              <span>Malzeme Uyumu</span>
              <span>%${r.match_percentage}</span>
            </div>
            <div class="recipe-progress-track">
              <div class="recipe-progress-bar" style="width: ${r.match_percentage}%;"></div>
            </div>
            <div class="progress-sub-row">
              <span class="sub-kilerde">✓ ${r.matched_ingredients.length} / ${r.ingredients.length} Malzeme Kilerde</span>
              ${subDetailHtml}
            </div>
          </div>

          <div class="recipe-card-actions-row">
            <button class="btn-stitch-primary btn-grow" onclick="openRecipeDetailModal(${r.id})">
              İncele &amp; Pişir →
            </button>
            <button class="btn-recipe-card-action" onclick="openEditRecipeModal(${r.id})" title="Tarifi Düzenle">✏️</button>
            <button class="btn-recipe-card-action btn-recipe-delete" onclick="deleteRecipeHandler(${r.id})" title="Tarifi Sil">🗑️</button>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function openRecipeDetailModal(recipeId) {
  const recipe = state.recipes.find(r => r.id === recipeId);
  if (!recipe) return;

  state.selectedRecipe = recipe;
  document.getElementById("recipeModalTitle").textContent = recipe.name;
  
  const detailImg = document.getElementById("recipeModalImage");
  if (detailImg) {
    const userImg = (recipe.image_url && typeof recipe.image_url === "string" && recipe.image_url.trim().length > 0) ? recipe.image_url.trim() : null;
    const key = recipe.name.toLowerCase().trim();
    const imgSrc = userImg || RECIPE_IMAGE_MAP[key] || "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=600&auto=format&fit=crop&q=80";
    detailImg.src = imgSrc;
    detailImg.style.display = "block";
  }
  document.getElementById("recipeModalDesc").textContent = recipe.description;
  document.getElementById("recipeModalInstructions").innerHTML = recipe.instructions.replace(/\n/g, "<br>");

  const ingList = document.getElementById("recipeModalIngredients");
  ingList.innerHTML = recipe.ingredients.map(ing => {
    const matched = recipe.matched_ingredients.find(m => m.ingredient_name.toLowerCase() === ing.ingredient_name.toLowerCase());
    if (matched) {
      if (matched.is_sufficient) {
        return `
          <li style="padding: 0.4rem 0; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; font-size: 0.85rem;">
            <span>✅ <strong>${ing.ingredient_name}</strong>: ${ing.quantity} ${ing.unit}</span>
            <span style="color: #166534; font-weight: 600;">Kilerde mevcut (${matched.available_quantity} ${matched.available_unit})</span>
          </li>
        `;
      } else {
        return `
          <li style="padding: 0.4rem 0; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; font-size: 0.85rem;">
            <span>⚠️ <strong>${ing.ingredient_name}</strong>: ${ing.quantity} ${ing.unit}</span>
            <span style="color: #d97706; font-weight: 600;">Yetersiz miktar (Kilerde: ${matched.available_quantity} ${matched.available_unit})</span>
          </li>
        `;
      }
    } else {
      return `
        <li style="padding: 0.4rem 0; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; font-size: 0.85rem;">
          <span>❌ <strong>${ing.ingredient_name}</strong>: ${ing.quantity} ${ing.unit} ${ing.is_optional ? '(Opsiyonel)' : ''}</span>
          <span style="color: #dc2626; font-weight: 600;">Kilerde eksik</span>
        </li>
      `;
    }
  }).join("");

  openModal("recipeDetailModal");
}

async function cookRecipeHandler() {
  if (!state.selectedRecipe) return;

  const matched = state.selectedRecipe.matched_ingredients;
  if (!matched || matched.length === 0) {
    showToast("Bu tarif için kilerinizde eşleşen malzeme bulunamadı.", "error");
    return;
  }

  const confirmed = await showConfirmDialog({
    title: "Tarifi Pişir ve Stoktan Düş",
    message: `"${state.selectedRecipe.name}" tarifini pişirip kilerdeki ${matched.length} malzemeyi tüketim kaydı olarak düşmek istiyor musunuz?`,
    icon: "🍲",
    confirmText: "Evet, Pişir",
    confirmColor: "#16a34a"
  });

  if (!confirmed) return;

  try {
    const payload = {
      recipe_id: state.selectedRecipe.id,
      ingredients: matched.map(m => ({
        product_id: m.product_id,
        name: m.ingredient_name,
        quantity: m.required_quantity,
        unit: m.required_unit,
      }))
    };

    const res = await api.smartDeductRecipe(payload);
    const count = res.deductions ? res.deductions.length : matched.length;

    let consumedMsg = "";
    if (res.consumed_products && res.consumed_products.length > 0) {
      consumedMsg = ` (${res.consumed_products.join(", ")} tamamen bitti ve tüketildi)`;
    }

    showToast(`Harika! "${state.selectedRecipe.name}" pişirildi ve ${count} malzeme kilerden düşüldü!${consumedMsg} 🌿`);
    closeModal("recipeDetailModal");
    loadRecipes();
    if (typeof loadPantry === "function") loadPantry();
    if (typeof loadDashboard === "function") loadDashboard();
  } catch (err) {
    showToast("Tarif tüketimi sırasında hata: " + err.message, "error");
  }
}


// ==============================================================================
// 4. ETKİ PANELİ (IMPACT)
// ==============================================================================

async function loadImpact() {
  try {
    const summary = await api.getConsumptionSummary();

    document.getElementById("impactTotalKg").textContent = `${summary.total_evaluated_kg} kg`;
    document.getElementById("impactWeeklyKg").textContent = `${summary.weekly_evaluated_kg} kg`;
    document.getElementById("impactMonthlyKg").textContent = `${summary.monthly_evaluated_kg} kg`;
    document.getElementById("impactCompletedRecipes").textContent = summary.completed_recipes_count;
    const co2Val = summary.environmental_impact ? summary.environmental_impact.estimated_co2_saved_kg : 0;
    const waterVal = summary.environmental_impact ? Math.round(summary.environmental_impact.estimated_water_saved_liters) : 0;
    document.getElementById("impactCo2Saved").textContent = `${co2Val} kg CO₂`;
    document.getElementById("impactWaterSaved").textContent = `${waterVal} Litre`;

    const catTbody = document.getElementById("impactCategoryTableBody");
    if (catTbody) {
      if (!summary.category_breakdown || summary.category_breakdown.length === 0) {
        catTbody.innerHTML = `<tr><td colspan="3" class="empty-state">Henüz değerlendirilmiş gıda verisi yok.</td></tr>`;
      } else {
        catTbody.innerHTML = summary.category_breakdown.map(c => `
          <tr>
            <td><strong>${c.category_name}</strong></td>
            <td>${c.total_quantity_kg} kg</td>
            <td>${c.log_count} işlem</td>
          </tr>
        `).join("");
      }
    }

  } catch (err) {
    showToast("Etki paneli verileri yüklenirken hata: " + err.message, "error");
  }
}


// ==============================================================================
// 5. BİLDİRİMLER (NOTIFICATIONS)
// ==============================================================================

async function loadNotifications() {
  const container = document.getElementById("notificationsList");
  if (!container) return;

  try {
    const notifs = await api.getNotifications();
    state.notifications = notifs;

    const unreadCount = notifs.filter(n => !n.is_read).length;
    updateNotificationBadge(unreadCount);

    if (notifs.length === 0) {
      container.innerHTML = `<div class="empty-state">
        <p>Her şey yolunda! Bekleyen bir uyarınız yok.</p>
      </div>`;
      return;
    }

    container.innerHTML = notifs.map(n => {
      const isUnread = !n.is_read;
      const dateFormatted = new Date(n.created_at).toLocaleDateString("tr-TR", {
        day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
      });

      return `
        <div class="stitch-card" style="margin-bottom: 0.85rem; border-left: 4px solid ${isUnread ? '#16a34a' : '#e5e7eb'};">
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
              <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.2rem;">${n.title}</h4>
              <p style="font-size: 0.82rem; color: var(--text-muted);">${n.message}</p>
              <span style="font-size: 0.72rem; color: var(--text-light); margin-top: 0.35rem; display: block;">${dateFormatted}</span>
            </div>
            ${isUnread ? `<button class="btn-stitch-outline btn-sm" onclick="markReadHandler(${n.id})">Okundu</button>` : `<span style="font-size: 0.75rem; color: var(--text-light);">Okundu</span>`}
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    showToast("Bildirimler yüklenirken hata: " + err.message, "error");
  }
}

function updateNotificationBadge(count) {
  const badge = document.getElementById("navNotifBadge");
  if (!badge) return;
  if (count > 0) {
    badge.style.display = "block";
  } else {
    badge.style.display = "none";
  }
}

async function markReadHandler(id) {
  try {
    await api.markNotificationRead(id);
    loadNotifications();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function markAllReadHandler() {
  try {
    await api.markAllNotificationsRead();
    showToast("Tüm bildirimler okundu olarak işaretlendi.");
    loadNotifications();
  } catch (err) {
    showToast(err.message, "error");
  }
}


// ==============================================================================
// MODALLAR
// ==============================================================================

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add("active");
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove("active");
}


// ==============================================================================
// BAŞLANGIÇ (DOM READY)
// ==============================================================================

document.addEventListener("DOMContentLoaded", () => {
  // Navigation event listeners
  document.querySelectorAll(".nav-link").forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      switchView(link.dataset.view);
    });
  });

  // Form submit listeners HTML tarafında inline onsubmit ile yönetilmektedir
  // (Çift ekleme ve mükerrer istekleri engellemek için mükerrer addEventListener kaldırıldı)

  // Modal dışı tıklama
  document.querySelectorAll(".modal-overlay").forEach(modal => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("active");
    });
  });

  // Kimlik doğrulama
  initAuth();

  // İlk görünüm olarak Ana Sayfa
  switchView("home");
});


// ==============================================================================
// TARİF CRUD FONKSİYONLARI (EKLE, GÜNCELLE, SİL)
// ==============================================================================

// Güvenli API bağlama (Tarayıcı önbelleği eski api.js dosyasını tutsa dahi CRUD işlemlerini garanti eder)
if (typeof api !== "undefined") {
  if (typeof api.addRecipe !== "function") {
    api.addRecipe = async function (recipeData) {
      return this.request("/recipes", {
        method: "POST",
        body: JSON.stringify(recipeData),
      });
    };
  }
  if (typeof api.updateRecipe !== "function") {
    api.updateRecipe = async function (id, recipeData) {
      return this.request(`/recipes/${id}`, {
        method: "PUT",
        body: JSON.stringify(recipeData),
      });
    };
  }
  if (typeof api.deleteRecipe !== "function") {
    api.deleteRecipe = async function (id) {
      return this.request(`/recipes/${id}`, {
        method: "DELETE",
      });
    };
  }
}

function addIngredientRow(data = {}) {
  const container = document.getElementById("recipeIngredientsContainer");
  if (!container) return;

  const row = document.createElement("div");
  row.className = "recipe-ing-row";

  const nameVal = data.ingredient_name || "";
  const qtyVal = data.quantity !== undefined ? data.quantity : 1;
  const unitVal = (data.unit || "adet").toLowerCase();
  const isOpt = !!data.is_optional;

  const units = ["adet", "kg", "gram", "litre", "ml", "kaşık", "paket", "demet", "porsiyon", "dilim", "bardak", "kutu", "kavanoz"];
  const unitOptions = units.map(u => `<option value="${u}" ${u === unitVal ? "selected" : ""}>${u}</option>`).join("");

  row.innerHTML = `
    <input type="text" class="form-control ing-name" placeholder="Malzeme adı (örn: Domates)" value="${nameVal}" required>
    <input type="number" class="form-control ing-qty" step="0.01" min="0.01" placeholder="Miktar" value="${qtyVal}" required>
    <select class="form-control ing-unit" required>
      ${unitOptions}
    </select>
    <label style="display: flex; align-items: center; gap: 4px; font-size: 0.75rem; color: var(--text-muted); cursor: pointer; white-space: nowrap;">
      <input type="checkbox" class="ing-opt" ${isOpt ? "checked" : ""}> Ops.
    </label>
    <button type="button" class="recipe-ing-remove" onclick="this.closest('.recipe-ing-row').remove()" title="Malzemeyi Kaldır">&times;</button>
  `;

  container.appendChild(row);
}

function openAddRecipeModal() {
  const form = document.getElementById("recipeForm");
  if (form) form.reset();

  document.getElementById("recipeFormId").value = "";
  document.getElementById("recipeFormModalTitle").textContent = "🍲 Yeni Tarif Ekle";
  document.getElementById("recipeFormSubmitBtn").textContent = "Tarifi Kaydet";

  const container = document.getElementById("recipeIngredientsContainer");
  if (container) {
    container.innerHTML = "";
    addIngredientRow({ ingredient_name: "", quantity: 1, unit: "adet" });
    addIngredientRow({ ingredient_name: "", quantity: 1, unit: "adet" });
  }

  openModal("recipeFormModal");
}

async function openEditRecipeModal(recipeId) {
  closeModal("recipeDetailModal");

  let recipe = state.recipes.find(r => r.id === recipeId);
  if (!recipe || !recipe.ingredients) {
    try {
      recipe = await api.getRecipeDetail(recipeId);
    } catch (err) {
      showToast("Tarif bilgileri yüklenemedi: " + err.message, "error");
      return;
    }
  }

  document.getElementById("recipeFormId").value = recipe.id;
  document.getElementById("recipeFormName").value = recipe.name;
  document.getElementById("recipeFormDesc").value = recipe.description;
  document.getElementById("recipeFormPrepTime").value = recipe.preparation_time;
  document.getElementById("recipeFormCookTime").value = recipe.cooking_time;
  document.getElementById("recipeFormServings").value = recipe.servings;
  document.getElementById("recipeFormDifficulty").value = recipe.difficulty;
  document.getElementById("recipeFormImageUrl").value = recipe.image_url || "";
  document.getElementById("recipeFormInstructions").value = recipe.instructions;

  document.getElementById("recipeFormModalTitle").textContent = "✏️ Tarifi Düzenle";
  document.getElementById("recipeFormSubmitBtn").textContent = "Değişiklikleri Güncelle";

  const container = document.getElementById("recipeIngredientsContainer");
  if (container) {
    container.innerHTML = "";
    if (recipe.ingredients && recipe.ingredients.length > 0) {
      recipe.ingredients.forEach(ing => addIngredientRow(ing));
    } else {
      addIngredientRow({ ingredient_name: "", quantity: 1, unit: "adet" });
    }
  }

  openModal("recipeFormModal");
}

async function handleRecipeFormSubmit(event) {
  event.preventDefault();

  const idVal = document.getElementById("recipeFormId").value;
  const name = document.getElementById("recipeFormName").value.trim();
  const description = document.getElementById("recipeFormDesc").value.trim();
  const preparation_time = parseInt(document.getElementById("recipeFormPrepTime").value);
  const cooking_time = parseInt(document.getElementById("recipeFormCookTime").value);
  const servings = parseInt(document.getElementById("recipeFormServings").value);
  const difficulty = document.getElementById("recipeFormDifficulty").value;
  const image_url = document.getElementById("recipeFormImageUrl").value.trim() || null;
  const instructions = document.getElementById("recipeFormInstructions").value.trim();

  // Malzemeleri topla
  const ingRows = document.querySelectorAll("#recipeIngredientsContainer .recipe-ing-row");
  if (ingRows.length === 0) {
    showToast("Lütfen tarif için en az 1 malzeme ekleyin.", "error");
    return;
  }

  const ingredients = [];
  for (const row of ingRows) {
    const ingName = row.querySelector(".ing-name").value.trim();
    const ingQty = parseFloat(row.querySelector(".ing-qty").value);
    const ingUnit = row.querySelector(".ing-unit").value;
    const isOpt = row.querySelector(".ing-opt").checked;

    if (!ingName || isNaN(ingQty) || ingQty <= 0) {
      showToast("Lütfen tüm malzeme satırlarını geçerli bilgilerle doldurun.", "error");
      return;
    }

    ingredients.push({
      ingredient_name: ingName,
      quantity: ingQty,
      unit: ingUnit,
      is_optional: isOpt,
    });
  }

  const payload = {
    name,
    description,
    preparation_time,
    cooking_time,
    servings,
    difficulty,
    image_url,
    instructions,
    ingredients,
  };

  try {
    if (idVal) {
      await api.updateRecipe(parseInt(idVal), payload);
      showToast(`"${name}" tarifi başarıyla güncellendi!`);
    } else {
      await api.addRecipe(payload);
      showToast(`"${name}" tarifi başarıyla oluşturuldu!`);
    }

    closeModal("recipeFormModal");
    await loadRecipes();
  } catch (err) {
    showToast("İşlem sırasında hata oluştu: " + err.message, "error");
  }
}

async function deleteRecipeHandler(recipeId) {
  let recipe = state.recipes.find(r => r.id === recipeId);
  const recipeName = recipe ? recipe.name : "Bu tarifi";

  const confirmed = await showConfirmDialog({
    title: "Tarifi Sil",
    message: `"${recipeName}" tarifini sistemden kalıcı olarak silmek istediğinize emin misiniz?`,
    icon: "🗑️",
    confirmText: "Evet, Sil",
    confirmColor: "#dc2626"
  });

  if (!confirmed) return;

  try {
    await api.deleteRecipe(recipeId);
    showToast(`"${recipeName}" tarifi silindi.`);
    closeModal("recipeDetailModal");
    await loadRecipes();
  } catch (err) {
    showToast("Tarif silinirken hata oluştu: " + err.message, "error");
  }
}
