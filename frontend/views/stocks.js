import {
  apiRequest,
  escapeHtml,
  fmtDate,
  loadReferenceData,
  movementStatusLabel,
  movementTypeLabel,
  productLabelById,
  state,
  warehouseLabelById,
  warehouseStatusBadge,
} from "../core/api.js";
import { $, setStatus } from "../core/ui.js";

export async function loadStocks() {
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

export async function loadInTransitItems() {
  setStatus("#in-transit-status", "Загрузка…");
  try {
    if (!state.products.length || !state.warehouses.length) await loadReferenceData().catch(() => {});
    const inTransitRes = await apiRequest("/api/v1/movements", {
      query: { page: 1, page_size: 100, status: "in_transit" },
    });
    const items = ((inTransitRes && inTransitRes.items) || [])
      .filter((m) => ["transfer", "transfer_out", "transfer_in", "fbo_out"].includes(m.type))
      .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
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

function inTransitCategory(m) {
  if (m.type === "fbo_out") return "На склад маркетплейса (FBO)";
  if (m.type === "transfer" || m.type === "transfer_out" || m.type === "transfer_in") return "Между ФФ";
  return "—";
}

function inTransitDirection(m) {
  if (m.type === "fbo_out") return "Маркетплейс";
  return warehouseLabelById(m.to_warehouse_id);
}

function inTransitActionButton(m) {
  if (m.type === "fbo_out") {
    return `<button data-action="in-transit-receive" data-type="fbo_out" data-id="${m.id}">Подтвердить получение</button>`;
  }
  if (m.type === "transfer" || m.type === "transfer_out") {
    return `<button data-action="in-transit-receive" data-type="transfer" data-id="${m.id}">Принять перемещение</button>`;
  }
  return "—";
}
