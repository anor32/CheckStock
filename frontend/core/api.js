import { $ } from "./ui.js";

export const API_BASE_URL = window.API_BASE_URL || "";

export const state = {
  products: [],
  warehouses: [],
  stocks: { page: 1, pageSize: 20, total: 0 },
  movements: { page: 1, pageSize: 20, total: 0 },
};

export const MOVEMENT_TYPE_LABELS = {
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

export const MOVEMENT_STATUS_LABELS = {
  draft: "Черновик",
  pending: "Ожидает",
  in_transit: "В пути",
  completed: "Завершено",
  cancelled: "Отменено",
};

export function movementTypeLabel(type) {
  return MOVEMENT_TYPE_LABELS[type] || (type ? String(type) : "—");
}

export function movementStatusLabel(status) {
  return MOVEMENT_STATUS_LABELS[status] || (status ? String(status) : "—");
}

export function productLabelById(id) {
  const p = state.products.find((x) => x.id === id);
  if (!p) return `#${id}`;
  return `${p.sku} — ${p.name}`;
}

export function warehouseLabelById(id, { showDeletedBadge = true } = {}) {
  if (id === null || id === undefined || id === "") return "—";
  const w = state.warehouses.find((x) => x.id === id);
  if (!w) return `#${id}`;
  if (!showDeletedBadge || !w.is_deleted) return w.name;
  return `${w.name} (Удалён)`;
}

export function escapeHtml(v) {
  return String(v ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function fmtDate(v) {
  if (!v) return "—";
  try { return new Date(v).toLocaleString(); } catch { return String(v); }
}

export function toIsoOrUndefined(dtLocalValue) {
  if (!dtLocalValue) return undefined;
  const d = new Date(dtLocalValue);
  if (Number.isNaN(d.getTime())) return undefined;
  return d.toISOString();
}

export function badgeHtml(text, kind = "active") {
  return `<span class="badge badge-${kind}">${escapeHtml(text)}</span>`;
}

export function warehouseStatusBadge(isDeleted) {
  return isDeleted ? badgeHtml("Удалён", "deleted") : badgeHtml("Активен", "active");
}

export function generateIdempotencyKey() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return `idem-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function acquireIdempotencyKey(scope) {
  const key = scope && scope.dataset ? scope.dataset.idempotencyKey : null;
  if (key) return key;
  const generated = generateIdempotencyKey();
  if (scope && scope.dataset) scope.dataset.idempotencyKey = generated;
  return generated;
}

export async function apiRequest(path, { method = "GET", body, query } = {}) {
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

export function fillSelect(select, items, { valueKey = "id", labelFn, includeEmpty = true, emptyLabel = "— выбрать —" } = {}) {
  const el = typeof select === "string" ? $(select.startsWith("#") ? select : `#${select}`) : select;
  if (!el) return;
  const prev = el.value;
  const opts = [];
  if (includeEmpty) opts.push(`<option value="">${escapeHtml(emptyLabel)}</option>`);
  for (const item of items) {
    const val = item[valueKey];
    const label = labelFn ? labelFn(item) : String(val);
    opts.push(`<option value="${escapeHtml(val)}">${escapeHtml(label)}</option>`);
  }
  el.innerHTML = opts.join("");
  if (prev && Array.from(el.options).some((o) => o.value === prev)) el.value = prev;
}

export async function loadProducts() {
  const products = await apiRequest("/api/v1/products");
  state.products = Array.isArray(products) ? products : [];
  return state.products;
}

export async function loadWarehousesForSelectors() {
  const warehouses = await apiRequest("/api/v1/warehouses", { query: { include_deleted: true } });
  state.warehouses = Array.isArray(warehouses) ? warehouses : [];
  return state.warehouses;
}

export async function loadReferenceData() {
  await Promise.all([loadProducts(), loadWarehousesForSelectors()]);
  refreshAllSelectors();
}

export function refreshAllSelectors() {
  const activeWarehouses = state.warehouses.filter((w) => !w.is_deleted);
  const allWarehouses = state.warehouses;
  const productLabel = (p) => `${p.sku} — ${p.name}`;
  const warehouseWithDeletedLabel = (w) => `${w.name} (#${w.id})${w.is_deleted ? " — удалён" : ""}`;

  const productSelects = [
    { id: "movements-product-filter", emptyLabel: "Все" },
    { id: "inbound-product" },
    { id: "transfer-product" },
    { id: "fbo-product" },
    { id: "fbs-product" },
  ];
  for (const { id, emptyLabel } of productSelects) {
    fillSelect(`#${id}`, state.products, {
      labelFn: productLabel,
      includeEmpty: true,
      emptyLabel: emptyLabel || "— выбрать —",
    });
  }

  const warehouseSelects = [
    { id: "stocks-warehouse-filter", warehouses: allWarehouses, emptyLabel: "Все" },
    { id: "movements-warehouse-filter", warehouses: allWarehouses, emptyLabel: "Все" },
    { id: "inbound-warehouse", warehouses: activeWarehouses },
    { id: "transfer-from", warehouses: activeWarehouses },
    { id: "transfer-to", warehouses: activeWarehouses },
    { id: "fbo-from-warehouse", warehouses: activeWarehouses },
    { id: "fbs-warehouse", warehouses: activeWarehouses },
  ];
  for (const { id, warehouses, emptyLabel } of warehouseSelects) {
    fillSelect(`#${id}`, warehouses, {
      labelFn: warehouseWithDeletedLabel,
      includeEmpty: true,
      emptyLabel: emptyLabel || "— выбрать —",
    });
  }
}
