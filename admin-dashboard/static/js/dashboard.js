/* FreshMart Admin Dashboard
 * Every page fetches live data from the Flask REST API using the JWT issued
 * at /admin/login. No mock data, no hardcoded JSON — this file is the only
 * client-side logic and it always talks to /api/*.
 */
(function (global) {
  const TOKEN_KEY = "gg_admin_access_token";
  const REFRESH_KEY = "gg_admin_refresh_token";
  const USER_KEY = "gg_admin_user";

  function getToken() { return localStorage.getItem(TOKEN_KEY); }
  function getUser() {
    try { return JSON.parse(localStorage.getItem(USER_KEY) || "null"); } catch (e) { return null; }
  }
  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
  }

  async function api(path, options = {}) {
    const headers = Object.assign({}, options.headers || {});
    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }
    const token = getToken();
    if (token) headers["Authorization"] = "Bearer " + token;

    const res = await fetch(path, Object.assign({}, options, { headers }));

    if (res.status === 401) {
      clearSession();
      window.location.href = "/admin/login";
      throw new Error("Session expired");
    }

    const isJson = (res.headers.get("content-type") || "").includes("application/json");
    const body = isJson ? await res.json().catch(() => ({})) : null;

    if (!res.ok) {
      const message = (body && body.error) || `Request failed (${res.status})`;
      throw new Error(message);
    }
    return isJson ? body : res;
  }

  function showError(message) {
    const el = document.getElementById("errorBanner");
    if (!el) { alert(message); return; }
    el.textContent = message;
    el.style.display = "block";
    setTimeout(() => { el.style.display = "none"; }, 6000);
  }

  function money(v) {
    return "₹" + Number(v || 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function badge(status) {
    return `<span class="badge badge-${status}">${(status || "").replace(/_/g, " ")}</span>`;
  }

  function escapeHtml(str) {
    return String(str == null ? "" : str).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  // ---------- Login page ----------
  function initLogin() {
    if (getToken()) { window.location.href = "/admin/dashboard"; return; }
    const form = document.getElementById("loginForm");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;
      const errEl = document.getElementById("loginError");
      errEl.style.display = "none";
      try {
        const res = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const body = await res.json();
        if (!res.ok) throw new Error(body.error || "Login failed");
        const { access_token, refresh_token, user } = body.data;
        if (!["admin", "manager", "staff"].includes(user.role)) {
          throw new Error("This account does not have admin dashboard access.");
        }
        localStorage.setItem(TOKEN_KEY, access_token);
        localStorage.setItem(REFRESH_KEY, refresh_token);
        localStorage.setItem(USER_KEY, JSON.stringify(user));
        window.location.href = "/admin/dashboard";
      } catch (err) {
        errEl.textContent = err.message;
        errEl.style.display = "block";
      }
    });
  }

  // ---------- Shell (sidebar/topbar) shared by every logged-in page ----------
  function initShell(activePage) {
    if (!getToken()) { window.location.href = "/admin/login"; return; }
    document.querySelectorAll(".sidebar nav a").forEach((a) => {
      if (a.dataset.page === activePage) a.classList.add("active");
    });
    const user = getUser();
    const label = document.getElementById("currentUserLabel");
    if (label && user) label.textContent = `${user.name} (${user.role})`;

    document.getElementById("logoutBtn").addEventListener("click", () => {
      clearSession();
      window.location.href = "/admin/login";
    });

    api("/api/branding").then((res) => {
      const b = res.data;
      document.getElementById("sidebarAppName").textContent = b.app_name || "FreshMart";
      document.title = (b.app_name || "FreshMart") + " Admin";
      if (b.logo_url) {
        const img = document.getElementById("sidebarLogo");
        img.src = b.logo_url;
        img.style.display = "inline-block";
      }
    }).catch(() => {});

    api("/api/themes/active").then((res) => {
      document.documentElement.dataset.theme = res.data.theme_name === "dark" ? "dark" : "light";
    }).catch(() => {});

    const pageInit = PAGES[activePage];
    if (pageInit) pageInit().catch((err) => showError(err.message));
  }

  // ---------- Page renderers ----------
  const PAGES = {};

  PAGES.dashboard = async function () {
    const content = document.querySelector(".content");
    content.insertAdjacentHTML("beforeend", `
      <div class="grid grid-4" id="statCards"></div>
      <div class="section-title">Recent Orders</div>
      <div class="card"><table id="recentOrdersTable"><thead><tr><th>Order</th><th>Customer</th><th>Status</th><th>Total</th><th>Placed</th></tr></thead><tbody></tbody></table></div>
      <div class="section-title">Low Stock Alerts</div>
      <div class="card"><table id="lowStockTable"><thead><tr><th>Product</th><th>Qty</th><th>Reorder Level</th></tr></thead><tbody></tbody></table></div>
    `);

    const [orders, lowStock, sales, revenue] = await Promise.all([
      api("/api/orders?per_page=8&sort_by=placed_at&sort_dir=desc"),
      api("/api/inventory/low-stock"),
      api("/api/reports/sales?period=monthly"),
      api("/api/reports/revenue?period=monthly"),
    ]);

    document.getElementById("statCards").innerHTML = [
      ["Orders (30d)", sales.data.total_orders],
      ["Revenue (30d)", money(sales.data.total_revenue)],
      ["Payments Collected", money(revenue.data.total_revenue)],
      ["Low Stock Items", lowStock.data.length],
    ].map(([label, value]) => `
      <div class="card stat-card"><div class="label">${label}</div><div class="value">${value}</div></div>
    `).join("");

    document.querySelector("#recentOrdersTable tbody").innerHTML = orders.data.map((o) => `
      <tr><td>#${o.id}</td><td>Customer ${o.customer_id}</td><td>${badge(o.status)}</td><td>${money(o.total_amount)}</td><td>${new Date(o.placed_at).toLocaleString()}</td></tr>
    `).join("") || `<tr><td colspan="5" class="empty-state">No orders yet</td></tr>`;

    document.querySelector("#lowStockTable tbody").innerHTML = lowStock.data.map((i) => `
      <tr><td>${escapeHtml(i.product_name)}</td><td>${i.quantity}</td><td>${i.reorder_level}</td></tr>
    `).join("") || `<tr><td colspan="3" class="empty-state">All stock levels healthy</td></tr>`;
  };

  PAGES.inventory = async function () {
    const content = document.querySelector(".content");
    content.insertAdjacentHTML("beforeend", `
      <div class="toolbar">
        <div class="filters"><input id="invSearch" placeholder="Search product..." style="width:240px" /></div>
        <button class="btn" id="viewReorderBtn">View Reorder Suggestions</button>
      </div>
      <div class="card"><table id="invTable">
        <thead><tr><th>Product</th><th>Qty</th><th>Reorder Level</th><th>Status</th><th>Adjust</th></tr></thead>
        <tbody></tbody>
      </table></div>
      <div class="section-title" id="reorderTitle" style="display:none">Reorder Suggestions</div>
      <div class="card" id="reorderCard" style="display:none"><table>
        <thead><tr><th>Product</th><th>Current</th><th>Suggested Reorder Qty</th><th>Supplier</th></tr></thead>
        <tbody id="reorderTbody"></tbody>
      </table></div>
    `);

    async function loadInventory() {
      const res = await api("/api/inventory?per_page=100");
      window.__inv = res.data;
      renderInventory(res.data);
    }

    function renderInventory(items) {
      const q = (document.getElementById("invSearch").value || "").toLowerCase();
      const filtered = items.filter((i) => (i.product_name || "").toLowerCase().includes(q));
      document.querySelector("#invTable tbody").innerHTML = filtered.map((i) => `
        <tr>
          <td>${escapeHtml(i.product_name)}</td>
          <td>${i.quantity}</td>
          <td>${i.reorder_level}</td>
          <td>${i.is_low_stock ? '<span class="badge badge-low">Low stock</span>' : '<span class="badge badge-active">OK</span>'}</td>
          <td>
            <button class="btn btn-sm" data-adjust="${i.product_id}" data-delta="10">+10 (restock)</button>
            <button class="btn btn-sm btn-secondary" data-adjust="${i.product_id}" data-delta="-1">-1 (adj)</button>
          </td>
        </tr>
      `).join("") || `<tr><td colspan="5" class="empty-state">No inventory records</td></tr>`;

      filtered.forEach(() => {});
      document.querySelectorAll("[data-adjust]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const productId = btn.dataset.adjust;
          const delta = parseInt(btn.dataset.delta, 10);
          try {
            await api(`/api/inventory/${productId}/adjust`, {
              method: "POST",
              body: JSON.stringify({ change_qty: delta, reason: delta > 0 ? "restock" : "adjustment" }),
            });
            await loadInventory();
          } catch (err) { showError(err.message); }
        });
      });
    }

    document.getElementById("invSearch").addEventListener("input", () => renderInventory(window.__inv || []));
    document.getElementById("viewReorderBtn").addEventListener("click", async () => {
      const card = document.getElementById("reorderCard");
      const title = document.getElementById("reorderTitle");
      const isHidden = card.style.display === "none";
      if (isHidden) {
        const res = await api("/api/inventory/reorder-suggestions");
        document.getElementById("reorderTbody").innerHTML = res.data.map((r) => `
          <tr><td>${escapeHtml(r.product_name)}</td><td>${r.current_quantity}</td><td>${r.suggested_reorder_quantity}</td><td>${escapeHtml(r.supplier_name || "—")}</td></tr>
        `).join("") || `<tr><td colspan="4" class="empty-state">No reorder suggestions right now</td></tr>`;
      }
      card.style.display = isHidden ? "block" : "none";
      title.style.display = isHidden ? "block" : "none";
    });

    await loadInventory();
  };

  PAGES.customers = async function () {
    const content = document.querySelector(".content");
    content.insertAdjacentHTML("beforeend", `
      <div class="card"><table id="custTable">
        <thead><tr><th>Name</th><th>Email</th><th>City</th><th>Loyalty Pts</th></tr></thead>
        <tbody></tbody>
      </table></div>
    `);
    const res = await api("/api/customers?per_page=100");
    document.querySelector("#custTable tbody").innerHTML = res.data.map((c) => `
      <tr><td>${escapeHtml(c.name)}</td><td>${escapeHtml(c.email)}</td><td>${escapeHtml(c.city || "—")}</td><td>${c.loyalty_points}</td></tr>
    `).join("") || `<tr><td colspan="4" class="empty-state">No customers yet</td></tr>`;
  };

  PAGES.orders = async function () {
    const content = document.querySelector(".content");
    content.insertAdjacentHTML("beforeend", `
      <div class="toolbar">
        <div class="filters">
          <select id="statusFilter">
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="confirmed">Confirmed</option>
            <option value="preparing">Preparing</option>
            <option value="out_for_delivery">Out for delivery</option>
            <option value="delivered">Delivered</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>
      <div class="card"><table id="ordersTable">
        <thead><tr><th>Order</th><th>Customer</th><th>Status</th><th>Total</th><th>Placed</th><th>Actions</th></tr></thead>
        <tbody></tbody>
      </table></div>
    `);

    const NEXT_STATUS = {
      pending: "confirmed", confirmed: "preparing", preparing: "out_for_delivery", out_for_delivery: "delivered",
    };

    async function load() {
      const status = document.getElementById("statusFilter").value;
      const qs = status ? `?status=${status}&per_page=100` : "?per_page=100";
      const res = await api(`/api/orders${qs}`);
      document.querySelector("#ordersTable tbody").innerHTML = res.data.map((o) => {
        const next = NEXT_STATUS[o.status];
        return `
        <tr>
          <td>#${o.id}</td><td>Customer ${o.customer_id}</td><td>${badge(o.status)}</td>
          <td>${money(o.total_amount)}</td><td>${new Date(o.placed_at).toLocaleString()}</td>
          <td>
            ${next ? `<button class="btn btn-sm" data-advance="${o.id}" data-next="${next}">Mark ${next.replace(/_/g, " ")}</button>` : ""}
            ${!["delivered", "cancelled"].includes(o.status) ? `<button class="btn btn-sm btn-danger" data-cancel="${o.id}">Cancel</button>` : ""}
            <a class="btn btn-sm btn-secondary" href="/api/reports/invoice/${o.id}" target="_blank">Invoice</a>
          </td>
        </tr>`;
      }).join("") || `<tr><td colspan="6" class="empty-state">No orders found</td></tr>`;

      document.querySelectorAll("[data-advance]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          try {
            await api(`/api/orders/${btn.dataset.advance}/status`, {
              method: "PUT", body: JSON.stringify({ status: btn.dataset.next }),
            });
            await load();
          } catch (err) { showError(err.message); }
        });
      });
      document.querySelectorAll("[data-cancel]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          try {
            await api(`/api/orders/${btn.dataset.cancel}/cancel`, { method: "POST" });
            await load();
          } catch (err) { showError(err.message); }
        });
      });
    }

    document.getElementById("statusFilter").addEventListener("change", load);
    await load();
  };

  PAGES.payments = async function () {
    const content = document.querySelector(".content");
    content.insertAdjacentHTML("beforeend", `
      <div class="card"><table id="payTable">
        <thead><tr><th>Order</th><th>Method</th><th>Amount</th><th>Status</th><th>Ref</th></tr></thead>
        <tbody></tbody>
      </table></div>
    `);
    const orders = await api("/api/orders?per_page=50");
    const rows = [];
    for (const o of orders.data) {
      const p = await api(`/api/payments/order/${o.id}`);
      p.data.forEach((pay) => rows.push({ order: o.id, ...pay }));
    }
    document.querySelector("#payTable tbody").innerHTML = rows.map((p) => `
      <tr><td>#${p.order}</td><td>${p.method.toUpperCase()}</td><td>${money(p.amount)}</td><td>${badge(p.status)}</td><td>${escapeHtml(p.transaction_ref || p.razorpay_payment_id || "—")}</td></tr>
    `).join("") || `<tr><td colspan="5" class="empty-state">No payments recorded</td></tr>`;
  };

  PAGES.reports = async function () {
    const content = document.querySelector(".content");
    content.insertAdjacentHTML("beforeend", `
      <div class="toolbar">
        <div class="filters">
          <select id="reportType">
            <option value="sales">Sales</option>
            <option value="revenue">Revenue</option>
            <option value="inventory">Inventory</option>
            <option value="customers">Customer</option>
            <option value="top-products">Top Products</option>
          </select>
          <select id="reportPeriod">
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly" selected>Monthly</option>
          </select>
        </div>
        <div>
          <a class="btn btn-secondary" id="exportPdf" href="#">Export PDF</a>
          <a class="btn" id="exportExcel" href="#">Export Excel</a>
        </div>
      </div>
      <div class="card"><pre id="reportOutput" style="white-space:pre-wrap;font-size:0.82rem"></pre></div>
    `);

    function updateExportLinks() {
      const type = document.getElementById("reportType").value;
      const period = document.getElementById("reportPeriod").value;
      document.getElementById("exportPdf").href = `/api/reports/${type}/export?period=${period}&format=pdf`;
      document.getElementById("exportExcel").href = `/api/reports/${type}/export?period=${period}&format=excel`;
    }

    async function load() {
      const type = document.getElementById("reportType").value;
      const period = document.getElementById("reportPeriod").value;
      const res = await api(`/api/reports/${type}?period=${period}`);
      document.getElementById("reportOutput").textContent = JSON.stringify(res.data, null, 2);
      updateExportLinks();
    }

    document.getElementById("reportType").addEventListener("change", load);
    document.getElementById("reportPeriod").addEventListener("change", load);

    // Exports require the JWT; plain <a href> can't send auth headers, so
    // fetch as a blob and trigger the download manually.
    ["exportPdf", "exportExcel"].forEach((id) => {
      document.getElementById(id).addEventListener("click", async (e) => {
        e.preventDefault();
        const url = e.currentTarget.href;
        const res = await fetch(url, { headers: { Authorization: "Bearer " + getToken() } });
        const blob = await res.blob();
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = url.includes("format=excel") ? "report.xlsx" : "report.pdf";
        link.click();
      });
    });

    await load();
  };

  PAGES.branding = async function () {
    const content = document.querySelector(".content");
    content.insertAdjacentHTML("beforeend", `
      <div class="card" style="max-width:480px">
        <div class="field"><label>App Name</label><input id="brandName" /></div>
        <div class="field"><label>Primary Color</label><input id="brandPrimary" type="color" /></div>
        <div class="field"><label>Secondary Color</label><input id="brandSecondary" type="color" /></div>
        <div class="field"><label>Logo</label><input id="brandLogo" type="file" accept="image/*" /></div>
        <button class="btn" id="saveBrandBtn">Save Branding</button>
      </div>
    `);
    const res = await api("/api/branding");
    document.getElementById("brandName").value = res.data.app_name || "";
    document.getElementById("brandPrimary").value = res.data.primary_color || "#2E7D32";
    document.getElementById("brandSecondary").value = res.data.secondary_color || "#FFC107";

    document.getElementById("saveBrandBtn").addEventListener("click", async () => {
      try {
        await api("/api/branding", {
          method: "PUT",
          body: JSON.stringify({
            app_name: document.getElementById("brandName").value,
            primary_color: document.getElementById("brandPrimary").value,
            secondary_color: document.getElementById("brandSecondary").value,
          }),
        });
        const file = document.getElementById("brandLogo").files[0];
        if (file) {
          const fd = new FormData();
          fd.append("logo", file);
          await api("/api/branding/logo", { method: "POST", body: fd });
        }
        showError("Branding saved.");
      } catch (err) { showError(err.message); }
    });
  };

  PAGES.theme = async function () {
    const content = document.querySelector(".content");
    content.insertAdjacentHTML("beforeend", `
      <div class="grid grid-3" id="themeCards"></div>
    `);
    const res = await api("/api/themes");
    function render() {
      document.getElementById("themeCards").innerHTML = res.data.map((t) => `
        <div class="card">
          <div style="font-weight:700;text-transform:capitalize">${t.theme_name}</div>
          <div style="margin:10px 0">${t.is_active ? '<span class="badge badge-active">Active</span>' : ""}</div>
          ${!t.is_active ? `<button class="btn btn-sm" data-activate="${t.id}">Activate</button>` : ""}
        </div>
      `).join("");
      document.querySelectorAll("[data-activate]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          await api(`/api/themes/${btn.dataset.activate}/activate`, { method: "PUT" });
          window.location.reload();
        });
      });
    }
    render();
  };

  PAGES.subscriptions = async function () {
    const content = document.querySelector(".content");
    content.insertAdjacentHTML("beforeend", `
      <div class="card"><table id="subTable">
        <thead><tr><th>Customer</th><th>Plan</th><th>Status</th><th>Start</th><th>End</th><th>Amount</th></tr></thead>
        <tbody></tbody>
      </table></div>
    `);
    const res = await api("/api/subscriptions?per_page=100");
    document.querySelector("#subTable tbody").innerHTML = res.data.map((s) => `
      <tr><td>${s.customer_id}</td><td>${escapeHtml(s.plan_name)}</td><td>${badge(s.status)}</td><td>${s.start_date}</td><td>${s.end_date}</td><td>${money(s.amount)}</td></tr>
    `).join("") || `<tr><td colspan="6" class="empty-state">No subscriptions yet</td></tr>`;
  };

  PAGES.analytics = async function () {
    const content = document.querySelector(".content");
    content.insertAdjacentHTML("beforeend", `<div class="grid grid-2">
        <div class="card"><div class="section-title" style="margin-top:0">Top Products (30d)</div><table id="topProdTable"><thead><tr><th>Product</th><th>Units Sold</th><th>Revenue</th></tr></thead><tbody></tbody></table></div>
        <div class="card"><div class="section-title" style="margin-top:0">Revenue by Payment Method</div><table id="revByMethodTable"><thead><tr><th>Method</th><th>Amount</th></tr></thead><tbody></tbody></table></div>
      </div>`);
    const [top, revenue] = await Promise.all([
      api("/api/reports/top-products?period=monthly"),
      api("/api/reports/revenue?period=monthly"),
    ]);
    document.querySelector("#topProdTable tbody").innerHTML = top.data.top_products.map((p) => `
      <tr><td>${escapeHtml(p.name)}</td><td>${p.units_sold}</td><td>${money(p.revenue)}</td></tr>
    `).join("") || `<tr><td colspan="3" class="empty-state">No sales yet</td></tr>`;
    document.querySelector("#revByMethodTable tbody").innerHTML = Object.entries(revenue.data.by_method).map(([m, v]) => `
      <tr><td>${m.toUpperCase()}</td><td>${money(v)}</td></tr>
    `).join("") || `<tr><td colspan="2" class="empty-state">No payments yet</td></tr>`;
  };

  PAGES.settings = async function () {
    const content = document.querySelector(".content");
    const user = getUser();
    content.insertAdjacentHTML("beforeend", `
      <div class="card" style="max-width:480px">
        <div class="field"><label>Name</label><input value="${escapeHtml(user?.name || "")}" disabled /></div>
        <div class="field"><label>Email</label><input value="${escapeHtml(user?.email || "")}" disabled /></div>
        <div class="field"><label>Role</label><input value="${escapeHtml(user?.role || "")}" disabled /></div>
        <p class="hint">Profile fields are managed by an Admin from the Customers/Users API.</p>
      </div>
      <div class="section-title">Audit Log (latest 20)</div>
      <div class="card"><table id="auditTable"><thead><tr><th>Action</th><th>Entity</th><th>User</th><th>When</th></tr></thead><tbody></tbody></table></div>
    `);
    try {
      const res = await api("/api/audit-logs?per_page=20&sort_by=created_at&sort_dir=desc");
      document.querySelector("#auditTable tbody").innerHTML = res.data.map((a) => `
        <tr><td>${escapeHtml(a.action)}</td><td>${escapeHtml(a.entity_type || "—")}</td><td>${a.user_id ?? "—"}</td><td>${new Date(a.created_at).toLocaleString()}</td></tr>
      `).join("") || `<tr><td colspan="4" class="empty-state">No audit entries yet</td></tr>`;
    } catch (err) {
      document.querySelector("#auditTable tbody").innerHTML = `<tr><td colspan="4" class="empty-state">${escapeHtml(err.message)}</td></tr>`;
    }
  };

  global.GroceryGoAdmin = { initLogin, initShell, api, showError, money, badge, escapeHtml };
})(window);
