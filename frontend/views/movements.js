import {
  apiRequest,
  escapeHtml,
  fillSelect,
  fmtDate,
  loadReferenceData,
  movementStatusLabel,
  movementTypeLabel,
  productLabelById,
  state,
  toIsoOrUndefined,
  warehouseLabelById,
} from "../core/api.js";
import { $, setStatus } from "../core/ui.js";

export async function loadMovements() {
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

export async function showMovementDetails(id) {
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

export async function loadReceiveCandidates() {
  try {
    const data = await apiRequest("/api/v1/movements", { query: { page: 1, page_size: 100, status: "in_transit" } });
    const items = ((data && data.items) || []).filter((m) => ["transfer", "transfer_out"].includes(m.type));
    fillSelect("#receive-movement-select", items, {
      valueKey: "id",
      labelFn: (m) => `#${m.id} — ${productLabelById(m.product_id)} (${m.qty}) ${warehouseLabelById(m.from_warehouse_id, { showDeletedBadge: false })} → ${warehouseLabelById(m.to_warehouse_id, { showDeletedBadge: false })}`,
      includeEmpty: true, emptyLabel: "— выбрать —",
    });
  } catch {
    // необязательно
  }
}
