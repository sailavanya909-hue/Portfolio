/* The dashboard displays the published analytic snapshot without replacing it with demo values. */
(() => {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
  const numbers = new Intl.NumberFormat("en-US", { maximumFractionDigits: 3 });
  const dateFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
  const pageSize = 10;
  let snapshot = null;
  let visibleLimit = pageSize;
  let filteredLots = [];
  let expandedRecommendations = false;

  function number(value) {
    return typeof value === "number" && Number.isFinite(value) ? value : null;
  }

  function money(value) {
    return number(value) === null ? "Unavailable" : currency.format(value);
  }

  function quantity(value, unit) {
    return number(value) === null ? "—" : `${numbers.format(value)} ${unit || ""}`.trim();
  }

  function calendarDate(value) {
    if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
    const parsed = new Date(`${value}T00:00:00Z`);
    return Number.isNaN(parsed.valueOf()) ? null : parsed;
  }

  function date(value) {
    const parsed = calendarDate(value);
    return parsed ? dateFormat.format(parsed) : "Unavailable";
  }

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = String(text);
    return node;
  }

  function badge(text) {
    const label = String(text || "Unavailable");
    const lower = label.toLowerCase();
    let tone = "";
    if (/expired|shortage/.test(lower)) tone = "critical";
    else if (/expiry/.test(lower)) tone = "caution";
    else if (/quarantin/.test(lower)) tone = "neutral";
    return element("span", `badge ${tone}`, label);
  }

  function validate(data) {
    if (!data || typeof data !== "object" || !data.meta || !data.kpis) {
      throw new Error("The inventory file is missing its snapshot information.");
    }
    if (!Array.isArray(data.materials) || !Array.isArray(data.lots)) {
      throw new Error("The inventory file is missing its material or lot records.");
    }
    if (data.meta.synthetic !== true) {
      throw new Error("This portfolio dashboard requires the clearly labeled synthetic dataset.");
    }
    if (data.meta.currency && data.meta.currency !== "USD") {
      throw new Error("This dashboard expects values in USD.");
    }
    if (!calendarDate(data.meta.as_of) || !calendarDate(data.meta.horizon_end) || number(data.meta.horizon_days) === null) {
      throw new Error("The inventory file is missing its planning dates.");
    }
    return data;
  }

  async function loadSnapshot() {
    byId("loading-state").hidden = false;
    byId("error-state").hidden = true;
    byId("dashboard-content").hidden = true;
    byId("retry-button").disabled = true;
    try {
      const response = await fetch("./dashboard.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`The inventory file could not be retrieved (${response.status}).`);
      snapshot = validate(await response.json());
      visibleLimit = pageSize;
      expandedRecommendations = false;
      renderSnapshot();
      byId("dashboard-content").hidden = false;
    } catch (error) {
      byId("error-message").textContent = "Please try again. If this continues, the project source contains the published analysis and assumptions.";
      byId("error-state").hidden = false;
      byId("as-of").textContent = "Unavailable";
      byId("horizon").textContent = "Unavailable";
      byId("scope").textContent = "Unavailable";
      byId("methodology-list").replaceChildren(element("li", "", "The calculation assumptions are unavailable until the inventory snapshot loads. See the project documentation for the complete method."));
      console.error("Inventory snapshot error:", error);
    } finally {
      byId("loading-state").hidden = true;
      byId("retry-button").disabled = false;
    }
  }

  function renderSnapshot() {
    const { meta, kpis } = snapshot;
    byId("as-of").textContent = date(meta.as_of);
    byId("horizon").textContent = `${numbers.format(meta.horizon_days)} days · through ${date(meta.horizon_end)}`;
    byId("scope").textContent = `${snapshot.materials.length} materials · ${snapshot.lots.length} lots`;
    const definitions = [
      { label: "Total inventory value", value: money(kpis.total_inventory_value), note: "All lots in the snapshot, including quarantine and already expired inventory." },
      { label: "Expiry exposure", value: money(kpis.expiry_exposed_residual_value), note: number(kpis.expired_released_value) !== null && number(kpis.expiry_exposed_residual_value) !== null ? `Includes ${money(kpis.expired_released_value)} already expired and ${money(kpis.expiry_exposed_residual_value - kpis.expired_released_value)} projected residual at future expiry. Quarantine excluded.` : "Purchase cost of already expired released stock plus projected residual at expiry during the window." },
      { label: "Quarantined inventory", value: money(kpis.quarantined_value), note: "Purchase cost of lots awaiting quality release. Excluded from available supply." },
      { label: "Materials below lead-time coverage", value: number(kpis.materials_below_lead_time_coverage) === null ? "Unavailable" : `${kpis.materials_below_lead_time_coverage} / ${snapshot.materials.length}`, note: "Simulated uninterrupted demand coverage is shorter than the supplier lead time." }
    ];
    byId("kpi-grid").replaceChildren(...definitions.map((item) => {
      const card = element("article", "kpi-card");
      card.append(element("h3", "kpi-label", item.label), element("p", "kpi-value", item.value), element("p", "kpi-note", item.note));
      return card;
    }));
    populateFilter("supplier-filter", snapshot.lots.map((lot) => lot.supplier_name), "All suppliers");
    populateFilter("status-filter", snapshot.lots.map((lot) => lot.quality_status), "All statuses");
    populateFilter("risk-filter", snapshot.lots.map((lot) => lot.risk), "All flags");
    renderMaterials();
    renderLots();
    renderRecommendations();
    const methods = Array.isArray(snapshot.methodology) ? snapshot.methodology : [];
    byId("methodology-list").replaceChildren(...(methods.length ? methods : ["Calculation assumptions were not supplied. Review the project documentation before interpreting results."]).map((item) => element("li", "", item)));
  }

  function populateFilter(id, values, allLabel) {
    const select = byId(id);
    const selected = select.value;
    const distinct = [...new Set(values.filter((value) => typeof value === "string" && value.trim()))].sort((a, b) => a.localeCompare(b));
    const all = element("option", "", allLabel);
    all.value = "";
    const options = distinct.map((value) => {
      const option = element("option", "", value);
      option.value = value;
      return option;
    });
    select.replaceChildren(all, ...options);
    select.value = distinct.includes(selected) ? selected : "";
  }

  function renderMaterials() {
    if (!snapshot) return;
    const ranking = {
      expiry: { field: "expiry_exposed_residual_value", label: "Expiry exposure", description: "Purchase cost of already expired released stock plus projected residual stock at future expiry within the planning window. Quarantined inventory is excluded." },
      gap: { field: "replenishment_gap_value", label: "Replenishment cost", description: "Estimated purchase cost of the material gap to cover supplier lead time under the stated demand assumptions. This is a planning estimate, not lost revenue." },
      quarantine: { field: "quarantined_value", label: "Quarantine value", description: "Purchase cost of quarantined inventory. These lots are excluded from available supply until their quality status changes." }
    }[byId("material-sort").value];
    byId("ranking-description").textContent = ranking.description;
    const materials = [...snapshot.materials].sort((a, b) => (number(b[ranking.field]) || 0) - (number(a[ranking.field]) || 0) || String(a.name).localeCompare(String(b.name)));
    const max = Math.max(0, ...materials.map((item) => number(item[ranking.field]) || 0));
    if (!materials.length) {
      byId("material-ranking").replaceChildren(element("div", "empty-state", "No materials were supplied in this snapshot."));
      return;
    }
    byId("material-ranking").replaceChildren(...materials.map((material) => {
      const row = element("article", "material-row");
      const title = element("div", "material-title");
      title.append(element("h3", "material-name", material.name || material.material_id), element("p", "material-details", `${material.material_id} · ${material.supplier_name || "Supplier unavailable"}`));
      const chart = element("div", "material-bar");
      const meta = element("div", "bar-meta");
      meta.append(element("span", "", ranking.label), element("strong", "", money(material[ranking.field])));
      const track = element("div", "bar-track");
      track.setAttribute("aria-hidden", "true");
      const fill = element("div", "bar-fill");
      fill.style.width = `${max ? Math.max(0, Math.min(100, (number(material[ranking.field]) || 0) / max * 100)) : 0}%`;
      track.append(fill);
      chart.append(meta, track);
      const summary = element("div", "material-summary");
      const coverage = number(material.coverage_days);
      const coverText = coverage === null ? "No demand modeled" : `${material.coverage_is_capped ? "≥ " : ""}${numbers.format(coverage)} days covered`;
      summary.append(element("strong", "", coverText), element("div", "", `${numbers.format(material.lead_time_days)}-day supplier lead time`));
      if (number(material.lead_time_gap_qty) > 0) summary.append(element("div", "", `${quantity(material.lead_time_gap_qty, material.unit)} gap`));
      summary.append(badge(material.status));
      row.append(title, chart, summary);
      return row;
    }));
  }

  function getFilteredLots() {
    const query = byId("lot-search").value.trim().toLowerCase();
    const supplier = byId("supplier-filter").value;
    const status = byId("status-filter").value;
    const risk = byId("risk-filter").value;
    return snapshot.lots.filter((lot) => {
      const searchable = `${lot.material_name || ""} ${lot.material_id || ""} ${lot.lot_id || ""}`.toLowerCase();
      return (!query || searchable.includes(query)) && (!supplier || lot.supplier_name === supplier) && (!status || lot.quality_status === status) && (!risk || lot.risk === risk);
    }).sort((a, b) => (number(b.expiry_exposed_residual_value) || 0) - (number(a.expiry_exposed_residual_value) || 0) || String(a.expiry_date).localeCompare(String(b.expiry_date)) || String(a.lot_id).localeCompare(String(b.lot_id)));
  }

  function renderLots() {
    if (!snapshot) return;
    filteredLots = getFilteredLots();
    const displayed = filteredLots.slice(0, visibleLimit);
    const total = snapshot.lots.length;
    byId("lot-count").textContent = `Showing ${displayed.length} of ${filteredLots.length} matching lots · ${total} in the snapshot`;
    byId("download-lots").disabled = filteredLots.length === 0;
    byId("show-more").hidden = filteredLots.length <= visibleLimit;
    byId("lots-empty").hidden = filteredLots.length !== 0;
    byId("lot-table-body").replaceChildren(...displayed.map((lot) => {
      const row = element("tr");
      const material = element("td");
      material.append(element("strong", "", lot.material_name || lot.material_id), element("span", "lot-id", `${lot.material_id} / ${lot.lot_id}`));
      const supplier = element("td", "", lot.supplier_name || "Unavailable");
      const status = element("td");
      status.append(badge(lot.quality_status));
      const expiry = element("td", "", date(lot.expiry_date));
      const expiryDate = calendarDate(lot.expiry_date);
      const asOf = calendarDate(snapshot.meta.as_of);
      if (expiryDate && asOf) {
        const remainingDays = Math.round((expiryDate - asOf) / 86400000);
        const note = remainingDays < 0 ? `${Math.abs(remainingDays)} days before snapshot` : remainingDays === 0 ? "Expires on snapshot date" : `${remainingDays} days after snapshot`;
        expiry.append(element("span", "expiry-note", note));
      }
      const qty = element("td", "number", quantity(lot.qty, lot.unit));
      const isQuarantined = String(lot.quality_status).toLowerCase() === "quarantine";
      const residual = element("td", "number", isQuarantined ? "Not modeled" : quantity(lot.expiry_residual_qty, lot.unit));
      const exposure = element("td", "number", isQuarantined ? "Excluded" : money(lot.expiry_exposed_residual_value));
      const risk = element("td");
      risk.append(badge(lot.risk));
      row.append(material, supplier, status, expiry, qty, residual, exposure, risk);
      return row;
    }));
  }

  function renderRecommendations() {
    const priorityOrder = { High: 0, Medium: 1, Low: 2 };
    const recommendations = Array.isArray(snapshot.recommendations) ? [...snapshot.recommendations].sort((a, b) => (priorityOrder[a.priority] ?? 3) - (priorityOrder[b.priority] ?? 3)) : [];
    if (!recommendations.length) {
      byId("recommendation-list").replaceChildren(element("div", "empty-state", "No review actions were supplied for this snapshot."));
      return;
    }
    byId("show-recommendations").hidden = recommendations.length <= 3 || expandedRecommendations;
    byId("show-recommendations").textContent = `View all ${recommendations.length} review actions`;
    byId("recommendation-list").replaceChildren(...(expandedRecommendations ? recommendations : recommendations.slice(0, 3)).map((recommendation) => {
      const card = element("article", "recommendation-card");
      const meta = element("div", "recommendation-meta");
      meta.append(element("span", "", `Priority ${recommendation.priority}`), element("span", "", recommendation.material_id || "Portfolio"));
      card.append(meta, element("h3", "", recommendation.action || "Review recommendation"), element("p", "", recommendation.reason || "Review the source analysis for details."));
      return card;
    }));
  }

  function csvCell(value) {
    let text = value === undefined || value === null ? "" : String(value);
    if (/^[=+@\-\t\r]/.test(text)) text = `'${text}`;
    return `"${text.replace(/"/g, '""')}"`;
  }

  function downloadLots() {
    if (!snapshot || !filteredLots.length) return;
    const fields = ["lot_id", "material_id", "material_name", "unit", "supplier_name", "quality_status", "expiry_date", "qty", "unit_cost", "inventory_value", "expiry_residual_qty", "expiry_exposed_residual_value", "risk"];
    const rows = [fields, ...filteredLots.map((lot) => fields.map((key) => lot[key]))];
    const csv = rows.map((row) => row.map(csvCell).join(",")).join("\r\n");
    const url = URL.createObjectURL(new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8;" }));
    const link = element("a");
    link.href = url;
    link.download = `synthetic-inventory-lots-${snapshot.meta.as_of || "snapshot"}.csv`;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  byId("retry-button").addEventListener("click", loadSnapshot);
  byId("material-sort").addEventListener("change", renderMaterials);
  byId("lot-filters").addEventListener("submit", (event) => event.preventDefault());
  byId("lot-search").addEventListener("input", () => { visibleLimit = pageSize; renderLots(); });
  ["supplier-filter", "status-filter", "risk-filter"].forEach((id) => byId(id).addEventListener("change", () => { visibleLimit = pageSize; renderLots(); }));
  byId("reset-filters").addEventListener("click", () => { byId("lot-filters").reset(); visibleLimit = pageSize; renderLots(); });
  byId("show-more").addEventListener("click", () => { visibleLimit += pageSize; renderLots(); });
  byId("download-lots").addEventListener("click", downloadLots);
  byId("show-recommendations").addEventListener("click", () => { expandedRecommendations = true; renderRecommendations(); });
  loadSnapshot();
})();
