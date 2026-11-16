import { apiRequest, escapeHtml, loadWarehousesForSelectors, refreshAllSelectors, warehouseStatusBadge } from "../core/api.js";
import { $, setStatus } from "../core/ui.js";

export async function loadWarehouses() {
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
