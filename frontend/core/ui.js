export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

export function setGlobalMessage(text, type = "success") {
  const el = $("#global-message");
  if (!text) {
    el.className = "message hidden";
    el.textContent = "";
    return;
  }
  el.className = `message ${type}`;
  el.textContent = text;
}

export function setStatus(id, text) {
  const el = $(id);
  if (el) el.textContent = text || "";
}

export function setSubmitting(form, submitting) {
  $$("button, input, select", form).forEach((el) => { el.disabled = submitting; });
}

export function showReceiptResult(text, type = "success") {
  const el = $("#receipts-result");
  el.className = `result ${type}`;
  el.textContent = text;
}

export function showFbsResult(text, type = "success") {
  const el = $("#fbs-result");
  if (!el) return;
  el.className = `result ${type}`;
  el.textContent = text;
}
