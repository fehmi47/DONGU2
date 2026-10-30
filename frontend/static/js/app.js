/**
 * 🌿 DÖNGÜ - Frontend Ana Uygulama Mantığı
 * Sayfa geçişleri, dinamik veri yüklemeleri, modallar, tüketim kayıtları ve arayüz etkileşimleri.
 */

// Uygulama Durumu
const state = {
  activeView: "dashboard",
  categories: [],
  products: [],
  recipes: [],
  notifications: [],
  selectedRecipe: null,
  consumeTargetProduct: null,
};

// Yardımcı Fonksiyon: Toast Bildirimi Göster
function showToast(message, type = "success") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  const icon = type === "success" ? "✅" : type === "error" ? "❌" : "ℹ️";
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Öncelik Rozeti HTML'i Üret
function getPriorityBadge(priority_level) {
  switch (priority_level) {
    case "critical":
      return `<span class="badge badge-critical">🚨 Kritik (Acil)</span>`;
    case "high":
      return `<span class="badge badge-high">⚠️ Yüksek Öncelik</span>`;
    case "medium":
      return `<span class="badge badge-medium">🟡 Orta Öncelik</span>`;
    case "low":
      return `<span class="badge badge-low">🟢 Düşük Öncelik</span>`;
    case "expired_stt":
      return `<span class="badge badge-expired">🛑 STT Geçti (Tüketmeyin)</span>`;
    case "no_date":
    default:
      return `<span class="badge badge-nodate">⚪ Tarihsiz</span>`;
  }
}

// Saklama Yeri İkonu
function getStorageIcon(location) {
  switch (location) {
    case "fridge": return "🧊 Buzdolabı";
    case "freezer": return "❄️ Dondurucu";
    case "pantry": return "🥫 Kiler";
    default: return location;
  }
}

// ==============================================================================
// GÖRÜNÜM YÖNETİMİ (ROUTING)
// ==============================================================================

function switchView(viewName) {
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

  // İlgili görünümün verilerini yükle
  if (viewName === "dashboard") loadDashboard();
  if (viewName === "pantry") loadPantry();
  if (viewName === "recipes") loadRecipes();
  if (viewName === "impact") loadImpact();
  if (viewName === "notifications") loadNotifications();
}

// ==============================================================================
// 1. DASHBOARD YÜKLEME
// ==============================================================================

async function loadDashboard() {
  try {
    const data = await api.getDashboardSummary();

    // Metrik sayaçları
    document.getElementById("dashActiveProducts").textContent = data.active_products_count;
    document.getElementById("dashExpiring").textContent = data.expiring_stt_count + data.expiring_tett_count;
    document.getElementById("dashCritical").textContent = data.critical_priority_count;
    document.getElementById("dashTotalSaved").textContent = `${data.total_evaluated_kg} kg`;
    document.getElementById("dashCompletedRecipes").textContent = data.completed_recipes_count;

    // Bildirim rozeti
    updateNotificationBadge(data.unread_notifications_count);

    // Çevresel kazanımlar
    document.getElementById("dashCo2Saved").textContent = `${data.environmental_impact.estimated_co2_saved_kg} kg`;
    document.getElementById("dashWaterSaved").textContent = `${data.environmental_impact.estimated_water_saved_liters} L`;

    // Haftalık grafik çubukları
    renderWeeklyChart(data.weekly_stats);

    // Son işlemler listesi
    renderRecentLogs(data.recent_consumptions);

  } catch (err) {
    showToast("Dashboard verileri yüklenirken hata oluştu: " + err.message, "error");
  }
}

function renderWeeklyChart(stats) {
  const container = document.getElementById("weeklyChart");
  if (!container) return;

  if (!stats || stats.length === 0) {
    container.innerHTML = `<div class="empty-state">Henüz haftalık tüketim verisi yok.</div>`;
    return;
  }

  const maxVal = Math.max(...stats.map(s => s.amount_kg), 1.0);

  container.innerHTML = stats.map(s => {
    const heightPercent = Math.min(Math.round((s.amount_kg / maxVal) * 100), 100);
    return `
      <div class="chart-bar-col">
        <span class="chart-bar-value">${s.amount_kg > 0 ? s.amount_kg + " kg" : ""}</span>
        <div class="chart-bar-fill" style="height: ${Math.max(heightPercent, 4)}%;"></div>
        <span class="chart-bar-label">${s.day_name.slice(0, 3)}</span>
      </div>
    `;
  }).join("");
}

function renderRecentLogs(logs) {
  const tbody = document.getElementById("recentLogsTableBody");
  if (!tbody) return;

  if (!logs || logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-state">Henüz tüketim kaydı oluşturulmadı.</td></tr>`;
    return;
  }

  tbody.innerHTML = logs.map(log => {
    const dateFormatted = new Date(log.recorded_at).toLocaleDateString("tr-TR", {
      day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
    });
    const typeLabel = log.action_type === "consumed" ? "🍽️ Tüketildi" :
                      log.action_type === "recipe_used" ? "🍲 Tarifte Kullanıldı" : "🗑️ İsraf / Atıldı";

    return `
      <tr>
        <td>${dateFormatted}</td>
        <td><strong>${log.product_name || "Silinmiş Ürün"}</strong></td>
        <td>${log.quantity_used} ${log.unit}</td>
        <td>${typeLabel}</td>
        <td>${log.recipe_name ? `<span class="badge badge-low">${log.recipe_name}</span>` : "-"}</td>
      </tr>
    `;
  }).join("");
}

// ==============================================================================
// 2. MUTFAĞIM (PANTRY) YÜKLEME VE İŞLEMLER
// ==============================================================================

async function loadPantry() {
  try {
    // Kategorileri yükle (önceden yüklenmediyse)
    if (state.categories.length === 0) {
      state.categories = await api.getCategories();
      populateCategorySelects();
    }

    const categoryId = document.getElementById("filterCategory").value;
    const storageLocation = document.getElementById("filterStorage").value;
    const search = document.getElementById("searchPantry").value;

    // Öncelik bilgileriyle zenginleştirilmiş ürün listesini getir
    const products = await api.getPriorityProducts();
    state.products = products;

    // Client-side filtreleme (kategori, saklama yeri, arama)
    let filtered = products;
    if (categoryId) filtered = filtered.filter(p => p.category_id == categoryId);
    if (storageLocation) filtered = filtered.filter(p => p.storage_location === storageLocation);
    if (search) filtered = filtered.filter(p => p.name.toLowerCase().includes(search.toLowerCase()));

    renderPantryTable(filtered);
  } catch (err) {
    showToast("Ürünler yüklenirken hata oluştu: " + err.message, "error");
  }
}

function renderPantryTable(products) {
  const tbody = document.getElementById("pantryTableBody");
  if (!tbody) return;

  if (products.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">
      <div class="empty-icon">🥬</div>
      <p>Kilerinizde bu kriterlere uygun ürün bulunmuyor.</p>
    </td></tr>`;
    return;
  }

  tbody.innerHTML = products.map(p => {
    const daysText = p.days_remaining !== null ? 
      (p.days_remaining < 0 ? `${Math.abs(p.days_remaining)} gün önce geçti` : `${p.days_remaining} gün kaldı`) : "-";

    return `
      <tr>
        <td><strong>${p.name}</strong></td>
        <td>${p.quantity} ${p.unit}</td>
        <td>${getStorageIcon(p.storage_location)}</td>
        <td>${p.date_type} (${p.expiry_date || "Yok"})</td>
        <td>${daysText}</td>
        <td>${getPriorityBadge(p.priority_level)}</td>
        <td>
          <div style="display: flex; gap: 0.35rem;">
            <button class="btn btn-sm btn-outline-primary" onclick="openConsumeModal(${p.id})">🍽️ Tüket</button>
            <button class="btn btn-sm btn-danger" onclick="deleteProductHandler(${p.id})">Sil</button>
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

function populateCategorySelects() {
  const filterCat = document.getElementById("filterCategory");
  const modalCat = document.getElementById("newProdCategory");
  if (!filterCat || !modalCat) return;

  const options = state.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join("");
  filterCat.innerHTML = `<option value="">Tüm Kategoriler</option>` + options;
  modalCat.innerHTML = `<option value="">Kategori Seçin</option>` + options;
}

// Yeni Ürün Ekle Form Submit
async function handleAddProductSubmit(e) {
  e.preventDefault();
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

  if (date_type !== "NONE" && !expiry_date) {
    showToast(`${date_type} seçildiğinde son tarih girilmesi zorunludur!`, "error");
    return;
  }

  try {
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
    e.target.reset();
    loadPantry();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Ürün Tüketim Modalı Açma
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

// Tüketim Form Submit
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

    showToast("Tüketim işlemi başarıyla kaydedildi! Kileriniz güncellendi.");
    closeModal("consumeModal");
    loadPantry();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Ürün Silme
async function deleteProductHandler(productId) {
  if (!confirm("Bu ürünü kilerinizden kaldırmak istediğinize emin misiniz?")) return;

  try {
    await api.deleteProduct(productId, false);
    showToast("Ürün başarıyla silindi.");
    loadPantry();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ==============================================================================
// 3. TARİFLER VE AKILLI ÖNERİ YÜKLEME
// ==============================================================================

async function loadRecipes() {
  const container = document.getElementById("recipesGrid");
  if (!container) return;

  container.innerHTML = `<div class="empty-state"><p>Tarifler ve kiler eşleşmeleri hesaplanıyor...</p></div>`;

  try {
    const recommendations = await api.getRecipeRecommendations();
    state.recipes = recommendations;
    renderRecipesList(recommendations);
  } catch (err) {
    showToast("Tarifler yüklenirken hata oluştu: " + err.message, "error");
  }
}

function renderRecipesList(recipes) {
  const container = document.getElementById("recipesGrid");
  if (!container) return;

  if (recipes.length === 0) {
    container.innerHTML = `<div class="empty-state"><p>Kayıtlı tarif bulunamadı.</p></div>`;
    return;
  }

  container.innerHTML = recipes.map(r => {
    const readyBadge = r.can_prepare ? 
      `<span class="badge badge-low" style="font-size: 0.8rem;">✨ Hemen Pişirilebilir</span>` : 
      `<span class="badge badge-high" style="font-size: 0.8rem;">Eksik Malzeme Var</span>`;

    const priorityBadge = r.priority_score > 0 ? 
      `<span class="badge badge-critical" title="Tarihi yaklaşan malzemeleri değerlendirir">🔥 Öncelik Puanı: +${r.priority_score}</span>` : "";

    return `
      <div class="recipe-card">
        <img src="${r.image_url || 'https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=600'}" alt="${r.name}" class="recipe-img">
        <div class="recipe-body">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.3rem;">
            <h4 class="recipe-title">${r.name}</h4>
            ${readyBadge}
          </div>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;">${r.description}</p>
          
          <div class="recipe-meta">
            <span>⏱️ ${r.total_time} dk</span>
            <span>👥 ${r.servings} Kişilik</span>
            <span>📊 ${r.difficulty}</span>
          </div>

          <div style="margin-top: 0.5rem;">
            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 600;">
              <span>Malzeme Uyumu</span>
              <span>%${r.match_percentage}</span>
            </div>
            <div class="progress-bar-container">
              <div class="progress-bar" style="width: ${r.match_percentage}%;"></div>
            </div>
          </div>

          <div style="margin: 0.4rem 0;">${priorityBadge}</div>

          <div class="recipe-footer">
            <span style="font-size: 0.8rem; color: var(--text-muted);">${r.matched_ingredients.length} / ${r.ingredients.length} Malzeme Kilerde</span>
            <button class="btn btn-sm btn-primary" onclick="openRecipeDetailModal(${r.id})">İncele & Pişir</button>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

// Tarif Detay Modalı
function openRecipeDetailModal(recipeId) {
  const recipe = state.recipes.find(r => r.id === recipeId);
  if (!recipe) return;

  state.selectedRecipe = recipe;
  document.getElementById("recipeModalTitle").textContent = recipe.name;
  document.getElementById("recipeModalDesc").textContent = recipe.description;
  document.getElementById("recipeModalInstructions").innerHTML = recipe.instructions.replace(/\n/g, "<br>");

  // Malzemeler listesi
  const ingList = document.getElementById("recipeModalIngredients");
  ingList.innerHTML = recipe.ingredients.map(ing => {
    const matched = recipe.matched_ingredients.find(m => m.ingredient_name.toLowerCase() === ing.ingredient_name.toLowerCase());
    if (matched) {
      return `
        <li style="padding: 0.4rem 0; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between;">
          <span>✅ <strong>${ing.ingredient_name}</strong>: ${ing.quantity} ${ing.unit}</span>
          <span style="font-size: 0.8rem; color: var(--primary);">Kilerde mevcut (${matched.available_quantity} ${matched.available_unit})</span>
        </li>
      `;
    } else {
      return `
        <li style="padding: 0.4rem 0; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between;">
          <span>❌ <strong>${ing.ingredient_name}</strong>: ${ing.quantity} ${ing.unit} ${ing.is_optional ? '(Opsiyonel)' : ''}</span>
          <span style="font-size: 0.8rem; color: var(--danger);">Kilerde eksik</span>
        </li>
      `;
    }
  }).join("");

  openModal("recipeDetailModal");
}

// Tarifi Pişir ve Kilerden Düş
async function cookRecipeHandler() {
  if (!state.selectedRecipe) return;

  const matched = state.selectedRecipe.matched_ingredients;
  if (!matched || matched.length === 0) {
    showToast("Bu tarif için kilerinizde eşleşen malzeme bulunamadı.", "error");
    return;
  }

  if (!confirm(`"${state.selectedRecipe.name}" tarifini pişirip kilerdeki ${matched.length} malzemeyi tüketim kaydı olarak düşmek istiyor musunuz?`)) {
    return;
  }

  try {
    let successCount = 0;
    for (const m of matched) {
      await api.recordConsumption({
        product_id: m.product_id,
        quantity_used: m.required_quantity,
        unit: m.required_unit,
        action_type: "recipe_used",
        recipe_id: state.selectedRecipe.id,
      });
      successCount++;
    }

    showToast(`Harika! ${state.selectedRecipe.name} başarıyla pişirildi ve ${successCount} malzeme kilerden düşüldü! 🌿`);
    closeModal("recipeDetailModal");
    loadRecipes();
  } catch (err) {
    showToast("Tarif tüketimi sırasında hata: " + err.message, "error");
  }
}

// ==============================================================================
// 4. ETKİ PANELİ (IMPACT) YÜKLEME
// ==============================================================================

async function loadImpact() {
  try {
    const summary = await api.getConsumptionSummary();

    document.getElementById("impactTotalKg").textContent = `${summary.total_evaluated_kg} kg`;
    document.getElementById("impactWeeklyKg").textContent = `${summary.weekly_evaluated_kg} kg`;
    document.getElementById("impactMonthlyKg").textContent = `${summary.monthly_evaluated_kg} kg`;
    document.getElementById("impactCompletedRecipes").textContent = summary.completed_recipes_count;
    document.getElementById("impactCo2Saved").textContent = `${summary.environmental_impact.estimated_co2_saved_kg} kg`;
    document.getElementById("impactWaterSaved").textContent = `${summary.environmental_impact.estimated_water_saved_liters} L`;

    // Kategori Dağılımı Tablosu
    const catTbody = document.getElementById("impactCategoryTableBody");
    if (catTbody) {
      if (summary.category_breakdown.length === 0) {
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

    // Tüketim Geçmişi
    const historyLogs = await api.getConsumptions(50);
    renderRecentLogs(historyLogs);

  } catch (err) {
    showToast("Etki paneli verileri yüklenirken hata oluştu: " + err.message, "error");
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
        <div class="empty-icon">🔔</div>
        <p>Her şey yolunda! Şu anda bekleyen bir uyarınız yok.</p>
      </div>`;
      return;
    }

    container.innerHTML = notifs.map(n => {
      const isUnread = !n.is_read;
      const dateFormatted = new Date(n.created_at).toLocaleDateString("tr-TR", {
        day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
      });

      return `
        <div class="card" style="margin-bottom: 0.85rem; border-left: 4px solid ${isUnread ? 'var(--primary)' : 'var(--border-color)'};">
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
              <h4 style="font-size: 1rem; color: var(--text-main); margin-bottom: 0.25rem;">${n.title}</h4>
              <p style="font-size: 0.88rem; color: var(--text-muted);">${n.message}</p>
              <span style="font-size: 0.75rem; color: var(--text-light); margin-top: 0.4rem; display: block;">${dateFormatted}</span>
            </div>
            ${isUnread ? `<button class="btn btn-sm btn-outline-primary" onclick="markReadHandler(${n.id})">Okundu</button>` : `<span style="font-size: 0.75rem; color: var(--text-light);">Okundu</span>`}
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
    badge.textContent = count;
    badge.style.display = "inline-block";
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
// MODAL YARDIMCILARI
// ==============================================================================

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add("active");
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove("active");
}

// Kullanıcı Değiştirici (İzolasyonu Canlı Test Etmek İçin)
function switchUser(userId) {
  api.setUserId(userId);
  showToast(`Kullanıcı değiştirildi: ID ${userId}`);
  document.getElementById("currentUserName").textContent = `Kullanıcı ${userId}`;
  switchView(state.activeView);
}

// ==============================================================================
// BAŞLANGIÇ YÜKLEMESİ (DOM READY)
// ==============================================================================

document.addEventListener("DOMContentLoaded", () => {
  // Navigation event listeners
  document.querySelectorAll(".nav-link").forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      switchView(link.dataset.view);
    });
  });

  // Filtre listener'ları
  const filterCat = document.getElementById("filterCategory");
  const filterStorage = document.getElementById("filterStorage");
  const searchPantry = document.getElementById("searchPantry");
  if (filterCat) filterCat.addEventListener("change", loadPantry);
  if (filterStorage) filterStorage.addEventListener("change", loadPantry);
  if (searchPantry) searchPantry.addEventListener("input", debounce(loadPantry, 300));

  // Form submit listeners
  const addProdForm = document.getElementById("addProductForm");
  if (addProdForm) addProdForm.addEventListener("submit", handleAddProductSubmit);

  const consumeForm = document.getElementById("consumeProductForm");
  if (consumeForm) consumeForm.addEventListener("submit", handleConsumeSubmit);

  // Modal dışı tıklama ile kapatma
  document.querySelectorAll(".modal-overlay").forEach(modal => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("active");
    });
  });

  // İlk görünüm olarak Dashboard'u aç
  switchView("dashboard");
});

function debounce(func, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => func.apply(this, args), delay);
  };
}
