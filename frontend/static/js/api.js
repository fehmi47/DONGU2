/**
 * 🌿 DÖNGÜ - Merkezi API İstemcisi
 * Tüm backend API isteklerini, kimlik başlığını ve hata yönetimini merkezi noktadan koordine eder.
 */

const API_BASE = "/api";

class ApiService {
  constructor() {
    // Aktif kullanıcı ID'si (Varsayılan: 1, localStorage ile saklanır)
    this.userId = localStorage.getItem("dongu_user_id") || "1";
  }

  setUserId(id) {
    this.userId = id.toString();
    localStorage.setItem("dongu_user_id", this.userId);
  }

  getHeaders(customHeaders = {}) {
    return {
      "Content-Type": "application/json",
      "X-User-Id": this.userId,
      ...customHeaders,
    };
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
      ...options,
      headers: this.getHeaders(options.headers),
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        let errorDetail = "Bilinmeyen bir hata oluştu.";
        try {
          const errData = await response.json();
          if (errData.detail) {
            if (Array.isArray(errData.detail)) {
              errorDetail = errData.detail.map(e => e.msg || e).join(", ");
            } else {
              errorDetail = errData.detail;
            }
          }
        } catch {
          errorDetail = `Sunucu hatası: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorDetail);
      }

      // 204 No Content kontrolü
      if (response.status === 204) return null;
      return await response.json();
    } catch (err) {
      console.error(`[API Hatası] ${url}:`, err);
      throw err;
    }
  }

  // --- KİMLİK DOĞRULAMA (AUTH) ---
  async register(userData) {
    return this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify(userData),
    });
  }

  async login(credentials) {
    return this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
  }

  async getMe() {
    return this.request("/auth/me");
  }

  async getDemoUsers() {
    return this.request("/auth/demo-users");
  }

  logout() {
    localStorage.removeItem("dongu_user_id");
    localStorage.removeItem("dongu_user");
    this.userId = "1";
  }

  // --- DASHBOARD ---
  async getDashboardSummary() {
    return this.request("/dashboard/summary");
  }


  // --- ÜRÜNLER (PRODUCTS) ---
  async getProducts(params = {}) {
    const query = new URLSearchParams();
    if (params.category_id) query.append("category_id", params.category_id);
    if (params.status) query.append("status", params.status);
    if (params.storage_location) query.append("storage_location", params.storage_location);
    if (params.search) query.append("search", params.search);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return this.request(`/products${qs}`);
  }

  async getPriorityProducts() {
    return this.request("/products/priority");
  }

  async getExpiringProducts(days = 3) {
    return this.request(`/products/expiring?days=${days}`);
  }

  async addProduct(productData) {
    return this.request("/products", {
      method: "POST",
      body: JSON.stringify(productData),
    });
  }

  async updateProduct(id, productData) {
    return this.request(`/products/${id}`, {
      method: "PUT",
      body: JSON.stringify(productData),
    });
  }

  async deleteProduct(id, soft = false) {
    return this.request(`/products/${id}?soft=${soft}`, {
      method: "DELETE",
    });
  }

  // --- KATEGORİLER ---
  async getCategories() {
    return this.request("/categories");
  }

  // --- TARİFLER ---
  async getRecipes(search = "") {
    const qs = search ? `?search=${encodeURIComponent(search)}` : "";
    return this.request(`/recipes${qs}`);
  }

  async getRecipeDetail(id) {
    return this.request(`/recipes/${id}`);
  }

  async getRecipeRecommendations() {
    return this.request("/recipes/recommendations");
  }

  async smartDeductRecipe(deductionData) {
    return this.request("/recipes/smart-deduction", {
      method: "POST",
      body: JSON.stringify(deductionData),
    });
  }

  // --- TÜKETİM (CONSUMPTION) ---
  async recordConsumption(consumptionData) {
    return this.request("/consumption", {
      method: "POST",
      body: JSON.stringify(consumptionData),
    });
  }

  async getConsumptions(limit = 50, offset = 0) {
    return this.request(`/consumption?limit=${limit}&offset=${offset}`);
  }

  async getConsumptionSummary() {
    return this.request("/consumption/summary");
  }

  // --- BİLDİRİMLER (NOTIFICATIONS) ---
  async getNotifications(unreadOnly = false) {
    return this.request(`/notifications?unread_only=${unreadOnly}`);
  }

  async markNotificationRead(id) {
    return this.request(`/notifications/${id}/read`, {
      method: "PATCH",
    });
  }

  async markAllNotificationsRead() {
    return this.request("/notifications/read-all", {
      method: "PATCH",
    });
  }
}

// Global API nesnesi
const api = new ApiService();
