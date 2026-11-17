import {
  acquireIdempotencyKey,
  apiRequest,
  loadReferenceData,
  movementStatusLabel,
  refreshAllSelectors,
  state,
} from "./core/api.js";
import {
  $,
  $$,
  setGlobalMessage,
  setStatus,
  setSubmitting,
  showFbsResult,
  showReceiptResult,
} from "./core/ui.js";
import { loadFbsReserves, runFbsReserveAction } from "./views/fbs.js";
import { loadInTransitItems, loadStocks } from "./views/stocks.js";
import { loadMovements, loadReceiveCandidates, showMovementDetails } from "./views/movements.js";
import { loadWarehouses } from "./views/warehouses.js";

// Navigation
export function switchView(view) {
  $$(".nav-btn").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
  $$(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${view}`));
  setGlobalMessage("");
  if (view === "stocks") { loadStocks(); loadInTransitItems(); }
  if (view === "warehouses") loadWarehouses();
  if (view === "movements") { loadMovements(); loadReferenceData().catch(() => {}); }
  if (view === "receipts") { loadReferenceData().then(loadReceiveCandidates).catch((e) => setStatus("#receipts-status", e.message)); }
  if (view === "fbs") { loadReferenceData().then(loadFbsReserves).catch((e) => setStatus("#fbs-status", e.message)); }
}

export function setupTabs() {
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

    if (action === "fbs-ship" || action === "fbs-cancel") {
      const qty = btn.dataset.qty || "";
      if (action === "fbs-ship") {
        await runFbsReserveAction({
          button: btn,
          movementId: id,
          qty,
          action: "fbs-ship",
          successText: `Резерв #${id} отправлен (${qty} шт.).`,
          alreadyDoneText: `Операция уже выполнена (резерв #${id}).`,
          errorText: (err) => `Ошибка: ${err.message}`,
          notify: (text, type) => setGlobalMessage(text, type),
          reloads: [loadInTransitItems, loadStocks, loadReceiveCandidates, loadMovements, loadFbsReserves],
        });
        return;
      }
      await runFbsReserveAction({
        button: btn,
        movementId: id,
        qty,
        action: "fbs-cancel",
        successText: `Резерв #${id} отменён.`,
        errorText: (err) => `Ошибка: ${err.message}`,
        conflictHandled: false,
        notify: (text, type) => setGlobalMessage(text, type),
        reloads: [loadInTransitItems, loadStocks, loadMovements, loadFbsReserves],
      });
      return;
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
      await runFbsReserveAction({
        button: btn,
        movementId: id,
        qty,
        action: "fbs-ship",
        successText: `Резерв #${id} отправлен (${qty} шт.).`,
        alreadyDoneText: `Операция уже выполнена (резерв #${id}).`,
        errorText: (err) => `Ошибка ${err.status || ""}: ${err.message}`.trim(),
        notify: (text, type) => showFbsResult(text, type),
        reloads: [loadFbsReserves, loadStocks, loadMovements],
      });
      return;
    }
    if (action === "fbs-cancel") {
      await runFbsReserveAction({
        button: btn,
        movementId: id,
        qty,
        action: "fbs-cancel",
        successText: `Резерв #${id} отменён.`,
        errorText: (err) => `Ошибка ${err.status || ""}: ${err.message}`.trim(),
        conflictHandled: false,
        notify: (text, type) => showFbsResult(text, type),
        reloads: [loadFbsReserves, loadStocks, loadMovements],
      });
      return;
    }
  });

  on("#goto-movements", "click", () => switchView("movements"));
  on("#goto-stocks", "click", () => switchView("stocks"));
}

export async function init() {
  setupTabs();
  bindEvents();
  try {
    await loadReferenceData();
  } catch (e) {
    setGlobalMessage(`Не удалось загрузить справочники: ${e.message}. Проверьте API_BASE_URL и доступность API.`, "error");
  }
  await Promise.all([loadStocks(), loadInTransitItems()]);
}
