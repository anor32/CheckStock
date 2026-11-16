import {
  acquireIdempotencyKey,
  apiRequest,
  escapeHtml,
  fmtDate,
  loadReferenceData,
  movementStatusLabel,
  productLabelById,
  state,
  warehouseLabelById,
} from "../core/api.js";
import { $, setStatus, showFbsResult } from "../core/ui.js";

export async function loadFbsReserves() {
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

export async function runFbsReserveAction({
  button,
  movementId,
  qty,
  action,
  successText,
  alreadyDoneText,
  errorText,
  conflictHandled = true,
  notify,
  reloads,
}) {
  const endpoint = `/api/v1/movements/${movementId}/${action}`;
  const confirmText = action === "fbs-ship"
    ? `Отправить резерв #${movementId} на ${qty} шт.?`
    : `Отменить резерв #${movementId} на ${qty} шт.?`;
  if (!window.confirm(confirmText)) return;
  button.disabled = true;
  try {
    await apiRequest(endpoint, {
      method: "POST",
      body: { idempotency_key: acquireIdempotencyKey(button) },
    });
    notify(successText, "success");
    await Promise.all(reloads.map((reload) => reload()));
  } catch (err) {
    if (conflictHandled && err.status === 409) {
      notify(alreadyDoneText, "success");
    } else {
      notify(errorText(err), "error");
    }
  } finally {
    button.disabled = false;
  }
}
