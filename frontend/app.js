// Конфигурация API: измените при необходимости (например, "http://localhost:8000")
const API_BASE_URL = window.API_BASE_URL || "";

const state = {
  products: [],
  warehouses: [],
  stocks: { page: 1, pageSize: 20, total: 0 },
  movements: { page: 1, pageSize: 20, total: 0 },
};

const MOVEMENT_TYPE_LABELS = {
  inbound: "Приход",
  transfer: "Перемещение",
  transfer_out: "Перемещение (отправка)",
  transfer_in: "Перемещение (приёмка)",
  fbo_out: "Отправка на маркетплейс",
  fbo_receive: "Приёмка на маркетплейсе",
  fbo_received: "Приёмка на маркетплейсе",
  fbs_reserve: "Резерв FBS",
  fbs_ship: "Отгрузка FBS",
  fbs_cancel: "Отмена FBS",
};

const MOVEMENT_STATUS_LABELS = {
  draft: "Черновик",
  pending: "Ожидает",
  in_transit: "В пути",
  completed: "Завершено",
  cancelled: "Отменено",
};

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

function setGlobalMessage(text, type = "success") {
  const el = $("#global-message");
  if (!text) {
    el.className = "message hidden";
    el.textContent = "";
    return;
  }
  el.className = `message ${type}`;
  el.textContent = text;
}

function setStatus(id, text) {
  const el = $(id);
  if (el) el.textContent = text || "";
}

function escapeHtml(v) {
  return String(v ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function fmtDate(v) {
  if (!v) return "—";
  try { return new Date(v).toLocaleString(); } catch { return String(v); }
}

function toIsoOrUndefined(dtLocalValue) {
  if (!dtLocalValue) return undefined;
  const d = new Date(dtLocalValue);
  if (Number.isNaN(d.getTime())) return undefined;
  return d.toISOString();
}

function generateIdempotencyKey() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return `idem-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function acquireIdempotencyKey(scope) {
  const key = scope && scope.dataset ? scope.dataset.idempotencyKey : null;
  if (key) return key;
  const generated = generateIdempotencyKey();
  if (scope && scope.dataset) scope.dataset.idempotencyKey = generated;
  return generated;
}

function movementTypeLabel(type) {
  return MOVEMENT_TYPE_LABELS[type] || (type ? String(type) : "—");
}

function movementStatusLabel(status) {
  return MOVEMENT_STATUS_LABELS[status] || (status ? String(status) : "—");
}

function badgeHtml(text, kind = "active") {
  return `<span class="badge badge-${kind}">${escapeHtml(text)}</span>`;
}

function warehouseStatusBadge(isDeleted) {
  return isDeleted ? badgeHtml("Удалён", "deleted") : badgeHtml("Активен", "active");
}

async function apiRequest(path, { method = "GET", body, query } = {}) {
  const base = API_BASE_URL || window.location.origin;
  const url = new URL(path, base);
  if (query) {
    Object.entries(query).forEach(([k, v]) => {
      if (v === undefined || v === null || v === "") return;
      url.searchParams.set(k, String(v));
    });
  }
  const opts = { method, headers: { Accept: "application/json" } };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(url.toString(), opts);
  } catch (e) {
    throw new Error(`Ошибка сети: ${e.message || e}`);
  }
  const text = await res.text();
  let data = null;
  if (text) {
    try { data = JSON.parse(text); } catch { data = text; }
  }
  if (!res.ok) {
    const detail = data && typeof data === "object" && "detail" in data ? data.detail : (text || res.statusText);
    const err = new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

function productLabelById(id) {
  const p = state.products.find((x) => x.id === id);
  if (!p) return `#${id}`;
  return `${p.sku} — ${p.name}`;
}

function warehouseLabelById(id, { showDeletedBadge = true } = {}) {
  if (id === null || id === undefined || id === "") return "—";
  const w = state.warehouses.find((x) => x.id === id);
  if (!w) return `#${id}`;
  if (!showDeletedBadge || !w.is_deleted) return w.name;
  return `${w.name} (Удалён)`;
}

function fillSelect(select, items, { valueKey = "id", labelFn, includeEmpty = true, emptyLabel = "— выбрать —" } = {}) {
  if (!select) return;
  const prev = select.value;
  const opts = [];
  if (includeEmpty) opts.push(`<option value="">${escapeHtml(emptyLabel)}</option>`);
  for (const item of items) {
    const val = item[valueKey];
    const label = labelFn ? labelFn(item) : String(val);
    opts.push(`<option value="${escapeHtml(val)}">${escapeHtml(label)}</option>`);
  }
  select.innerHTML = opts.join("");
  if (prev && Array.from(select.options).some((o) => o.value === prev)) select.value = prev;
}

async function loadProducts() {
  const products = await apiRequest("/api/v1/products");
  state.products = Array.isArray(products) ? products : [];
  return state.products;
}

async function loadWarehousesForSelectors() {
  const warehouses = await apiRequest("/api/v1/warehouses", { query: { include_deleted: true } });
  state.warehouses = Array.isArray(warehouses) ? warehouses : [];
  return state.warehouses;
}

async function loadReferenceData() {
  await Promise.all([loadProducts(), loadWarehousesForSelectors()]);
  refreshAllSelectors();
}

function refreshAllSelectors() {
  const activeWarehouses = state.warehouses.filter((w) => !w.is_deleted);
  const allWarehouses = state.warehouses;
  fillSelect($("#stocks-warehouse-filter"), allWarehouses, {
    labelFn: (w) => `${w.name} (#${w.id})${w.is_deleted ? " — удалён" : ""}`,
    includeEmpty: true, emptyLabel: "Все",
  });
  fillSelect($("#movements-product-filter"), state.products, {
    labelFn: (p) => `${p.sku} — ${p.name}`, includeEmpty: true, emptyLabel: "Все",
  });
  fillSelect($("#movements-warehouse-filter"), allWarehouses, {
    labelFn: (w) => `${w.name} (#${w.id})${w.is_deleted ? " — удалён" : ""}`,
    includeEmpty: true, emptyLabel: "Все",
  });
  const productLabel = (p) => `${p.sku} — ${p.name}`;
  const whLabel = (w) => `${w.name} (#${w.id})`;
  fillSelect($("#inbound-product"), state.products, { labelFn: productLabel });
  fillSelect($("#inbound-warehouse"), activeWarehouses, { labelFn: whLabel });
  fillSelect($("#transfer-product"), state.products, { labelFn: productLabel });
  fillSelect($("#transfer-from"), activeWarehouses, { labelFn: whLabel });
  fillSelect($("#transfer-to"), activeWarehouses, { labelFn: whLabel });
  fillSelect($("#fbo-product"), state.products, { labelFn: productLabel });
  fillSelect($("#fbo-from-warehouse"), activeWarehouses, { labelFn: whLabel });
  fillSelect($("#fbs-product"), state.products, { labelFn: productLabel });
  fillSelect($("#fbs-warehouse"), activeWarehouses, { labelFn: whLabel });
}

// Navigation
function switchView(view) {
  $$(".nav-btn").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
  $$(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${view}`));
  setGlobalMessage("");
  if (view === "stocks") { loadStocks(); loadInTransitItems(); }
  if (view === "warehouses") loadWarehouses();
  if (view === "movements") { loadMovements(); loadReferenceData().catch(() => {}); }
  if (view === "receipts") { loadReferenceData().then(loadReceiveCandidates).catch((e) => setStatus("#receipts-status", e.message)); }
  if (view === "fbs") { loadReferenceData().then(loadFbsReserves).catch((e) => setStatus("#fbs-status", e.message)); }
}

// Stocks
async function loadStocks() {
  const form = $("#stocks-filters");
  const fd = new FormData(form);
  const sku = (fd.get("sku") || "").toString().trim();
  const warehouse_id = fd.get("warehouse_id") || "";
  const include_deleted_warehouses = fd.get("include_deleted_warehouses") ? "true" : "false";
  setStatus("#stocks-status", "Загрузка…");
  try {
    if (!state.warehouses.length) await loadReferenceData().catch(() => {});
    const data = await apiRequest("/api/v1/stocks", {
      query: {
        page: state.stocks.page,
        page_size: state.stocks.pageSize,
        sku: sku || undefined,
        warehouse_id: warehouse_id || undefined,
        include_deleted_warehouses,
      },
    });
    state.stocks.page = data.page || state.stocks.page;
    state.stocks.pageSize = data.page_size || state.stocks.pageSize;
    renderStocks(data.items || []);
    $("#stocks-page-info").textContent = `Страница ${state.stocks.page}`;
    $("#stocks-prev").disabled = state.stocks.page <= 1;
    $("#stocks-next").disabled = (data.items || []).length < state.stocks.pageSize;
    setStatus("#stocks-status", data.items?.length ? "" : "Нет данных");
  } catch (e) {
    renderStocks([]);
    $("#stocks-page-info").textContent = "";
    setStatus("#stocks-status", `Ошибка: ${e.message}`);
  }
}

function renderStocks(items) {
  const tbody = $("#stocks-table tbody");
  if (!items.length) {
    tbody.innerHTML = `<tr><td colspan="7">Нет данных</td></tr>`;
    return;
  }
  tbody.innerHTML = items.map((i) => `
    <tr>
      <td class="mono">${escapeHtml(i.sku)}</td>
      <td>${escapeHtml(i.product_name)}</td>
      <td>${escapeHtml(i.warehouse_name)}</td>
      <td>${warehouseStatusBadge(i.warehouse_is_deleted)}</td>
      <td>${escapeHtml(i.qty_physical)}</td>
      <td>${escapeHtml(i.qty_reserved_fbs)}</td>
      <td>${escapeHtml(i.qty_available)}</td>
    </tr>`).join("");
}

function inTransitCategory(m) {
  if (m.type === "fbo_out") return "На склад маркетплейса (FBO)";
  if (m.type === "transfer" || m.type === "transfer_out" || m.type === "transfer_in") return "Между ФФ";
  if (m.type === "fbs_reserve" || m.type === "fbs_ship") return "К клиенту (FBS)";
  return "—";
}

function inTransitDirection(m) {
  if (m.type === "fbo_out") return "Маркетплейс";
  if (m.type === "fbs_reserve" || m.type === "fbs_ship") return "Клиент (FBS)";
  return warehouseLabelById(m.to_warehouse_id);
}

function inTransitActionButton(m) {
  if (m.type === "fbo_out") {
    return `<button data-action="in-transit-receive" data-type="fbo_out" data-id="${m.id}">Подтвердить получение</button>`;
  }
  if (m.type === "transfer" || m.type === "transfer_out") {
    return `<button data-action="in-transit-receive" data-type="transfer" data-id="${m.id}">Принять перемещение</button>`;
  }
  if (m.type === "fbs_reserve" && m.status === "pending") {
    return `<div class="row-actions"><button class="btn-sm" data-action="fbs-ship" data-id="${m.id}" data-qty="${escapeHtml(m.qty)}">Отправить клиенту</button><button class="btn-sm btn-danger-soft" data-action="fbs-cancel" data-id="${m.id}" data-qty="${escapeHtml(m.qty)}">Отменить отправку</button></div>`;
  }
  if (m.type === "fbs_ship" && (m.status === "in_transit" || m.status === "pending")) {
    return "—";
  }
  return "—";
}

async function loadInTransitItems() {
  setStatus("#in-transit-status", "Загрузка…");
  try {
    if (!state.products.length || !state.warehouses.length) await loadReferenceData().catch(() => {});
    const [inTransitRes, fbsPendingRes] = await Promise.all([
      apiRequest("/api/v1/movements", { query: { page: 1, page_size: 100, status: "in_transit" } }),
      apiRequest("/api/v1/movements", { query: { page: 1, page_size: 100, type: "fbs_reserve", status: "pending" } }),
    ]);
    const byId = new Map();
    for (const m of (inTransitRes && inTransitRes.items) || []) {
      if (["transfer", "transfer_out", "transfer_in", "fbo_out", "fbs_ship"].includes(m.type)) byId.set(m.id, m);
    }
    for (const m of (fbsPendingRes && fbsPendingRes.items) || []) {
      if (m.type === "fbs_reserve" && m.status === "pending") byId.set(m.id, m);
    }
    const items = Array.from(byId.values()).sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
    const tbody = $("#in-transit-table tbody");
    if (!items.length) {
      tbody.innerHTML = `<tr><td colspan="10">Нет товаров в пути</td></tr>`;
      setStatus("#in-transit-status", "");
      return;
    }
    tbody.innerHTML = items.map((m) => `
      <tr>
        <td>${escapeHtml(inTransitCategory(m))}</td>
        <td class="mono">${escapeHtml(m.id)}</td>
        <td>${escapeHtml(fmtDate(m.created_at))}</td>
        <td>${escapeHtml(productLabelById(m.product_id))}</td>
        <td>${escapeHtml(m.qty)}</td>
        <td>${escapeHtml(warehouseLabelById(m.from_warehouse_id))}</td>
        <td>${escapeHtml(inTransitDirection(m))}</td>
        <td>${escapeHtml(movementTypeLabel(m.type))}</td>
        <td>${escapeHtml(movementStatusLabel(m.status))}</td>
        <td class="table-actions">${inTransitActionButton(m)}</td>
      </tr>`).join("");
    setStatus("#in-transit-status", "");
  } catch (e) {
    $("#in-transit-table tbody").innerHTML = `<tr><td colspan="10">Ошибка загрузки</td></tr>`;
    setStatus("#in-transit-status", `Ошибка: ${e.message}`);
  }
}

// Warehouses
async function loadWarehouses() {
  setStatus("#warehouses-status", "Загрузка…");
  const showDeleted = $("#warehouses-show-deleted")?.checked;
  try {
    const items = await apiRequest("/api/v1/warehouses", {
      query: { include_deleted: showDeleted ? "true" : "false" },
    });
    const warehouses = Array.isArray(items) ? items : [];
    renderWarehouses(warehouses);
    await loadWarehousesForSelectors();
    refreshAllSelectors();
    setStatus("#warehouses-status", warehouses.length ? "" : "Нет данных");
  } catch (e) {
    renderWarehouses([]);
    setStatus("#warehouses-status", `Ошибка: ${e.message}`);
  }
}

function renderWarehouses(items) {
  const tbody = $("#warehouses-table tbody");
  if (!items.length) {
    tbody.innerHTML = `<tr><td colspan="4">Нет данных</td></tr>`;
    return;
  }
  tbody.innerHTML = items.map((w) => `
    <tr data-id="${w.id}">
      <td>${escapeHtml(w.id)}</td>
      <td>${escapeHtml(w.name)}</td>
      <td>${warehouseStatusBadge(w.is_deleted)}</td>
      <td class="row-actions">
        <button data-action="rename" data-id="${w.id}" data-name="${escapeHtml(w.name)}">Переименовать</button>
        <button data-action="delete" data-id="${w.id}" class="danger" ${w.is_deleted ? "disabled" : ""}>Удалить</button>
      </td>
    </tr>`).join("");
}

// Movements
async function loadMovements() {
  const form = $("#movements-filters");
  const fd = new FormData(form);
  const query = {
    page: state.movements.page,
    page_size: state.movements.pageSize,
    product_id: fd.get("product_id") || undefined,
    type: fd.get("type") || undefined,
    status: fd.get("status") || undefined,
    warehouse_id: fd.get("warehouse_id") || undefined,
    date_from: toIsoOrUndefined(fd.get("date_from")),
    date_to: toIsoOrUndefined(fd.get("date_to")),
  };
  setStatus("#movements-status", "Загрузка…");
  try {
    if (!state.products.length || !state.warehouses.length) await loadReferenceData().catch(() => {});
    const data = await apiRequest("/api/v1/movements", { query });
    state.movements.total = data.total || 0;
    state.movements.page = data.page || state.movements.page;
    state.movements.pageSize = data.page_size || state.movements.pageSize;
    renderMovements(data.items || []);
    const maxPage = Math.max(1, Math.ceil(state.movements.total / state.movements.pageSize));
    $("#movements-page-info").textContent = `Страница ${state.movements.page} из ${maxPage}, всего: ${state.movements.total}`;
    $("#movements-prev").disabled = state.movements.page <= 1;
    $("#movements-next").disabled = state.movements.page >= maxPage;
    setStatus("#movements-status", data.items?.length ? "" : "Нет данных");
  } catch (e) {
    renderMovements([]);
    $("#movements-page-info").textContent = "";
    setStatus("#movements-status", `Ошибка: ${e.message}`);
  }
}

function renderMovements(items) {
  const tbody = $("#movements-table tbody");
  if (!items.length) {
    tbody.innerHTML = `<tr><td colspan="9">Нет данных</td></tr>`;
    return;
  }
  tbody.innerHTML = items.map((m) => `
    <tr>
      <td>${escapeHtml(fmtDate(m.created_at))}</td>
      <td>${escapeHtml(productLabelById(m.product_id))}</td>
      <td>${escapeHtml(m.qty)}</td>
      <td>${escapeHtml(warehouseLabelById(m.from_warehouse_id))}</td>
      <td>${escapeHtml(warehouseLabelById(m.to_warehouse_id))}</td>
      <td>${escapeHtml(movementTypeLabel(m.type))}</td>
      <td>${escapeHtml(movementStatusLabel(m.status))}</td>
      <td class="mono">${escapeHtml(m.id)}</td>
      <td><button data-action="details" data-id="${m.id}">Детали</button></td>
    </tr>`).join("");
}

async function showMovementDetails(id) {
  const box = $("#movement-details");
  box.classList.remove("hidden");
  box.innerHTML = "Загрузка деталей…";
  try {
    const m = await apiRequest(`/api/v1/movements/${id}`);
    const details = {
      ...m,
      type_label: movementTypeLabel(m.type),
      status_label: movementStatusLabel(m.status),
      product: productLabelById(m.product_id),
      from: warehouseLabelById(m.from_warehouse_id),
      to: warehouseLabelById(m.to_warehouse_id),
    };
    box.innerHTML = `<h3>Детали движения #${escapeHtml(m.id)}</h3>
      <pre>${escapeHtml(JSON.stringify(details, null, 2))}</pre>`;
  } catch (e) {
    box.innerHTML = `<div class="error">Ошибка: ${escapeHtml(e.message)}</div>`;
  }
}

async function loadReceiveCandidates() {
  try {
    const data = await apiRequest("/api/v1/movements", { query: { page: 1, page_size: 100, status: "in_transit" } });
    const items = ((data && data.items) || []).filter((m) => ["transfer", "transfer_out"].includes(m.type));
    fillSelect($("#receive-movement-select"), items, {
      valueKey: "id",
      labelFn: (m) => `#${m.id} — ${productLabelById(m.product_id)} (${m.qty}) ${warehouseLabelById(m.from_warehouse_id, { showDeletedBadge: false })} → ${warehouseLabelById(m.to_warehouse_id, { showDeletedBadge: false })}`,
      includeEmpty: true, emptyLabel: "— выбрать —",
    });
  } catch {
    // необязательно
  }
}

// FBS reserves
function showFbsResult(text, type = "success") {
  const el = $("#fbs-result");
  if (!el) return;
  el.className = `result ${type}`;
  el.textContent = text;
}

async function loadFbsReserves() {
  setStatus("#fbs-status", "Загрузка…");
  try {
    if (!state.products.length || !state.warehouses.length) await loadReferenceData().catch(() => {});
    const data = await apiRequest("/api/v1/movements", {
      query: { page: 1, page_size: 100, type: "fbs_reserve", status: "pending" },
    });
    const items = ((data && data.items) || []).filter((m) => m.type === "fbs_reserve" && m.status === "pending");
    const tbody = $("#fbs-reserves-table tbody");
    if (!tbody) return;
    if (!items.length) {
      tbody.innerHTML = `<tr><td colspan="7">Нет активных резервов</td></tr>`;
      setStatus("#fbs-status", "");
      return;
    }
    tbody.innerHTML = items.map((m) => `
      <tr>
        <td class="mono">${escapeHtml(m.id)}</td>
        <td>${escapeHtml(productLabelById(m.product_id))}</td>
        <td>${escapeHtml(warehouseLabelById(m.from_warehouse_id))}</td>
        <td>${escapeHtml(m.qty)}</td>
        <td>${escapeHtml(fmtDate(m.created_at))}</td>
        <td>${escapeHtml(movementStatusLabel(m.status))}</td>
        <td class="row-actions table-actions">
          <button class="btn-sm" data-action="fbs-ship" data-id="${m.id}" data-qty="${escapeHtml(m.qty)}">Отправить клиенту</button>
          <button class="btn-sm btn-danger-soft" data-action="fbs-cancel" data-id="${m.id}" data-qty="${escapeHtml(m.qty)}">Отменить отправку</button>
        </td>
      </tr>`).join("");
    setStatus("#fbs-status", "");
  } catch (e) {
    const tbody = $("#fbs-reserves-table tbody");
    if (tbody) tbody.innerHTML = `<tr><td colspan="7">Ошибка загрузки</td></tr>`;
    setStatus("#fbs-status", `Ошибка: ${e.message}`);
  }
}

// Forms helpers
function setSubmitting(form, submitting) {
  $$("button, input, select", form).forEach((el) => { el.disabled = submitting; });
}
function showReceiptResult(text, type = "success") {
  const el = $("#receipts-result");
  el.className = `result ${type}`;
  el.textContent = text;
}

function setupTabs() {
  $$(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.tab;
      $$(".tab-btn").forEach((b) => b.classList.toggle("active", b === btn));
      $$(".tab-panel").forEach((p) => p.classList.toggle("active", p.id === `tab-${tab}`));
      if (tab === "receive") loadReceiveCandidates();
    });
  });
}

function on(sel, event, handler, root = document) {
  const el = $(sel, root);
  if (el) el.addEventListener(event, handler);
}

function bindEvents() {
  $$(".nav-btn").forEach((btn) => btn.addEventListener("click", () => switchView(btn.dataset.view)));

  on("#stocks-filters", "submit", (e) => { e.preventDefault(); state.stocks.page = 1; loadStocks(); });
  on("#stocks-prev", "click", () => { if (state.stocks.page > 1) { state.stocks.page--; loadStocks(); } });
  on("#stocks-next", "click", () => { state.stocks.page++; loadStocks(); });
  on("#in-transit-refresh", "click", loadInTransitItems);
  on("#in-transit-table", "click", async (e) => {
    const btn = e.target.closest("button[data-action]");
    if (!btn) return;
    const id = Number(btn.dataset.id);
    const action = btn.dataset.action;
    const type = btn.dataset.type;
    if (!id) return;

    if (action === "in-transit-receive") {
      const isMarketplace = type === "fbo_out";
      const confirmText = isMarketplace
        ? `Подтвердить получение отправки на маркетплейс (движение #${id})?`
        : `Принять перемещение (движение #${id})?`;
      if (!window.confirm(confirmText)) return;
      btn.disabled = true;
      try {
        const path = isMarketplace
          ? `/api/v1/movements/${id}/fbo-receive`
          : `/api/v1/movements/${id}/receive`;
        await apiRequest(path, {
          method: "POST",
          body: { idempotency_key: acquireIdempotencyKey(btn) },
        });
        setGlobalMessage(
          isMarketplace
            ? `Отправка на маркетплейс подтверждена (движение #${id})`
            : `Перемещение принято (движение #${id})`,
          "success"
        );
        await Promise.all([loadInTransitItems(), loadStocks(), loadReceiveCandidates(), loadMovements(), loadFbsReserves()]);
      } catch (err) {
        setGlobalMessage(`Ошибка: ${err.message}`, "error");
      } finally {
        btn.disabled = false;
      }
      return;
    }

    if (action === "fbs-ship") {
      const qty = btn.dataset.qty || "";
      if (!window.confirm(`Отправить резерв #${id} на ${qty} шт.?`)) return;
      btn.disabled = true;
      try {
        await apiRequest(`/api/v1/movements/${id}/fbs-ship`, {
          method: "POST",
          body: { idempotency_key: acquireIdempotencyKey(btn) },
        });
        setGlobalMessage(`Резерв #${id} отправлен (${qty} шт.).`, "success");
        await Promise.all([loadInTransitItems(), loadStocks(), loadMovements(), loadFbsReserves()]);
      } catch (err) {
        if (err.status === 409) {
          setGlobalMessage(`Операция уже выполнена (резерв #${id}).`, "success");
        } else {
          setGlobalMessage(`Ошибка: ${err.message}`, "error");
        }
      } finally {
        btn.disabled = false;
      }
      return;
    }

    if (action === "fbs-cancel") {
      const qty = btn.dataset.qty || "";
      if (!window.confirm(`Отменить резерв #${id} на ${qty} шт.?`)) return;
      btn.disabled = true;
      try {
        await apiRequest(`/api/v1/movements/${id}/fbs-cancel`, {
          method: "POST",
          body: { idempotency_key: acquireIdempotencyKey(btn) },
        });
        setGlobalMessage(`Резерв #${id} отменён.`, "success");
        await Promise.all([loadInTransitItems(), loadStocks(), loadMovements(), loadFbsReserves()]);
      } catch (err) {
        setGlobalMessage(`Ошибка: ${err.message}`, "error");
      } finally {
        btn.disabled = false;
      }
    }
  });

  on("#warehouses-refresh", "click", loadWarehouses);
  on("#warehouses-show-deleted", "change", loadWarehouses);
  on("#warehouse-create-form", "submit", async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const name = new FormData(form).get("name").toString().trim();
    if (!name) return;
    setSubmitting(form, true);
    try {
      await apiRequest("/api/v1/warehouses", { method: "POST", body: { name } });
      form.reset();
      setGlobalMessage("Склад создан", "success");
      await loadWarehouses();
    } catch (err) {
      setGlobalMessage(`Ошибка: ${err.message}`, "error");
    } finally {
      setSubmitting(form, false);
    }
  });

  on("#warehouses-table", "click", async (e) => {
    const btn = e.target.closest("button[data-action]");
    if (!btn) return;
    const id = Number(btn.dataset.id);
    if (btn.dataset.action === "rename") {
      const next = window.prompt("Новое название склада:", btn.dataset.name || "");
      if (next === null) return;
      const name = next.trim();
      if (!name) return setGlobalMessage("Название не может быть пустым", "error");
      btn.disabled = true;
      try {
        await apiRequest(`/api/v1/warehouses/${id}`, { method: "PATCH", body: { name } });
        setGlobalMessage("Склад переименован", "success");
        await loadWarehouses();
      } catch (err) {
        setGlobalMessage(`Ошибка: ${err.message}`, "error");
      } finally {
        btn.disabled = false;
      }
    }
    if (btn.dataset.action === "delete") {
      if (!window.confirm("Удалить склад (soft-delete)?")) return;
      btn.disabled = true;
      try {
        await apiRequest(`/api/v1/warehouses/${id}`, { method: "DELETE" });
        setGlobalMessage("Склад удалён", "success");
        await loadWarehouses();
      } catch (err) {
        setGlobalMessage(`Ошибка: ${err.message}`, "error");
      } finally {
        btn.disabled = false;
      }
    }
  });

  on("#movements-filters", "submit", (e) => { e.preventDefault(); state.movements.page = 1; loadMovements(); });
  on("#movements-prev", "click", () => { if (state.movements.page > 1) { state.movements.page--; loadMovements(); } });
  on("#movements-next", "click", () => { state.movements.page++; loadMovements(); });
  on("#movements-table", "click", (e) => {
    const btn = e.target.closest("button[data-action='details']");
    if (btn) showMovementDetails(btn.dataset.id);
  });

  on("#receive-movement-select", "change", (e) => {
    if (e.target.value) $("#receive-movement-id").value = e.target.value;
  });

  on("#form-inbound", "submit", async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fd = new FormData(form);
    const body = {
      product_id: Number(fd.get("product_id")),
      warehouse_id: Number(fd.get("warehouse_id")),
      qty: Number(fd.get("qty")),
      idempotency_key: acquireIdempotencyKey(form),
    };
    setSubmitting(form, true);
    showReceiptResult("Отправка…", "success");
    try {
      const res = await apiRequest("/api/v1/movements/inbound", { method: "POST", body });
      showReceiptResult(`Успешно: приход создан (движение #${res.id}, статус: ${movementStatusLabel(res.status)}).`, "success");
      form.reset();
      delete form.dataset.idempotencyKey;
      await Promise.all([loadReferenceData(), loadStocks(), loadInTransitItems()]);
    } catch (err) {
      showReceiptResult(`Ошибка ${err.status || ""}: ${err.message}`.trim(), "error");
    } finally {
      setSubmitting(form, false);
      refreshAllSelectors();
    }
  });

  on("#form-transfer", "submit", async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fd = new FormData(form);
    const fromId = Number(fd.get("from_warehouse_id"));
    const toId = Number(fd.get("to_warehouse_id"));
    if (fromId === toId) {
      showReceiptResult("Ошибка: склад-отправитель и склад-получатель должны отличаться.", "error");
      return;
    }
    const body = {
      product_id: Number(fd.get("product_id")),
      from_warehouse_id: fromId,
      to_warehouse_id: toId,
      qty: Number(fd.get("qty")),
      idempotency_key: acquireIdempotencyKey(form),
    };
    setSubmitting(form, true);
    showReceiptResult("Отправка…", "success");
    try {
      const res = await apiRequest("/api/v1/movements/transfer", { method: "POST", body });
      showReceiptResult(`Успешно: перемещение создано (движение #${res.id}, статус: ${movementStatusLabel(res.status)}).`, "success");
      form.reset();
      delete form.dataset.idempotencyKey;
      await loadReceiveCandidates();
    } catch (err) {
      showReceiptResult(`Ошибка ${err.status || ""}: ${err.message}`.trim(), "error");
    } finally {
      setSubmitting(form, false);
      refreshAllSelectors();
    }
  });

  on("#form-receive", "submit", async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fd = new FormData(form);
    const movementId = Number(fd.get("movement_id"));
    if (!movementId) {
      showReceiptResult("Ошибка: укажите ID движения.", "error");
      return;
    }
    setSubmitting(form, true);
    showReceiptResult("Отправка…", "success");
    try {
      const res = await apiRequest(`/api/v1/movements/${movementId}/receive`, {
        method: "POST",
        body: { idempotency_key: acquireIdempotencyKey(form) },
      });
      showReceiptResult(`Успешно: перемещение принято (движение #${res.id}, статус: ${movementStatusLabel(res.status)}).`, "success");
      form.reset();
      delete form.dataset.idempotencyKey;
      await Promise.all([loadReceiveCandidates(), loadStocks()]);
    } catch (err) {
      showReceiptResult(`Ошибка ${err.status || ""}: ${err.message}`.trim(), "error");
    } finally {
      setSubmitting(form, false);
      refreshAllSelectors();
    }
  });

  on("#form-fbo-out", "submit", async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fd = new FormData(form);
    const body = {
      product_id: Number(fd.get("product_id")),
      from_warehouse_id: Number(fd.get("from_warehouse_id")),
      qty: Number(fd.get("qty")),
      idempotency_key: acquireIdempotencyKey(form),
    };
    setSubmitting(form, true);
    showReceiptResult("Отправка…", "success");
    try {
      const res = await apiRequest("/api/v1/movements/fbo-out", { method: "POST", body });
      showReceiptResult(`Успешно: отправка на маркетплейс создана (движение #${res.id}, статус: ${movementStatusLabel(res.status)}).`, "success");
      form.reset();
      delete form.dataset.idempotencyKey;
      await Promise.all([loadStocks(), loadInTransitItems()]);
    } catch (err) {
      showReceiptResult(`Ошибка ${err.status || ""}: ${err.message}`.trim(), "error");
    } finally {
      setSubmitting(form, false);
      refreshAllSelectors();
    }
  });

  on("#form-product-create", "submit", async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fd = new FormData(form);
    const sku = (fd.get("sku") || "").toString().trim();
    const name = (fd.get("name") || "").toString().trim();
    if (!sku || !name) {
      showReceiptResult("Ошибка: укажите SKU и название товара.", "error");
      return;
    }
    setSubmitting(form, true);
    showReceiptResult("Отправка…", "success");
    try {
      const product = await apiRequest("/api/v1/products", { method: "POST", body: { sku, name } });
      form.reset();
      await loadReferenceData();
      if (product && product.id) {
        const inboundSelect = $("#inbound-product");
        if (inboundSelect && Array.from(inboundSelect.options).some((o) => o.value === String(product.id))) {
          inboundSelect.value = String(product.id);
        }
      }
      showReceiptResult(`Успешно: товар создан (${product?.sku || sku} — ${product?.name || name}).`, "success");
    } catch (err) {
      showReceiptResult(`Ошибка ${err.status || ""}: ${err.message}`.trim(), "error");
    } finally {
      setSubmitting(form, false);
    }
  });

  on("#form-fbs-reserve", "submit", async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fd = new FormData(form);
    const body = {
      product_id: Number(fd.get("product_id")),
      warehouse_id: Number(fd.get("warehouse_id")),
      qty: Number(fd.get("qty")),
      idempotency_key: acquireIdempotencyKey(form),
    };
    setSubmitting(form, true);
    showFbsResult("Отправка…", "success");
    try {
      const res = await apiRequest("/api/v1/movements/fbs-reserve", { method: "POST", body });
      showFbsResult(`Успешно: резерв создан (движение #${res.id}, кол-во: ${res.qty}, статус: ${movementStatusLabel(res.status)}).`, "success");
      form.reset();
      delete form.dataset.idempotencyKey;
      await Promise.all([loadFbsReserves(), loadStocks()]);
    } catch (err) {
      showFbsResult(`Ошибка ${err.status || ""}: ${err.message}`.trim(), "error");
    } finally {
      setSubmitting(form, false);
      refreshAllSelectors();
    }
  });

  on("#fbs-reserves-refresh", "click", loadFbsReserves);
  on("#fbs-reserves-table", "click", async (e) => {
    const btn = e.target.closest("button[data-action]");
    if (!btn) return;
    const id = Number(btn.dataset.id);
    const qty = btn.dataset.qty || "";
    const action = btn.dataset.action;
    if (!id) return;
    if (action === "fbs-ship") {
      if (!window.confirm(`Отправить резерв #${id} на ${qty} шт.?`)) return;
      btn.disabled = true;
      try {
        await apiRequest(`/api/v1/movements/${id}/fbs-ship`, {
          method: "POST",
          body: { idempotency_key: acquireIdempotencyKey(btn) },
        });
        showFbsResult(`Резерв #${id} отправлен (${qty} шт.).`, "success");
        await Promise.all([loadFbsReserves(), loadStocks(), loadMovements()]);
      } catch (err) {
        if (err.status === 409) {
          showFbsResult(`Операция уже выполнена (резерв #${id}).`, "success");
        } else {
          showFbsResult(`Ошибка ${err.status || ""}: ${err.message}`.trim(), "error");
        }
      } finally {
        btn.disabled = false;
      }
    }
    if (action === "fbs-cancel") {
      if (!window.confirm(`Отменить резерв #${id} на ${qty} шт.?`)) return;
      btn.disabled = true;
      try {
        await apiRequest(`/api/v1/movements/${id}/fbs-cancel`, {
          method: "POST",
          body: { idempotency_key: acquireIdempotencyKey(btn) },
        });
        showFbsResult(`Резерв #${id} отменён.`, "success");
        await Promise.all([loadFbsReserves(), loadStocks(), loadMovements()]);
      } catch (err) {
        showFbsResult(`Ошибка ${err.status || ""}: ${err.message}`.trim(), "error");
      } finally {
        btn.disabled = false;
      }
    }
  });

  on("#goto-movements", "click", () => switchView("movements"));
  on("#goto-stocks", "click", () => switchView("stocks"));
}

async function init() {
  setupTabs();
  bindEvents();
  try {
    await loadReferenceData();
  } catch (e) {
    setGlobalMessage(`Не удалось загрузить справочники: ${e.message}. Проверьте API_BASE_URL и доступность API.`, "error");
  }
  await Promise.all([loadStocks(), loadInTransitItems()]);
}

init();
