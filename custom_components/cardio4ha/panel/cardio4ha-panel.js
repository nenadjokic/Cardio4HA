/**
 * Cardio4HA v1.0.0 - Sidebar Panel
 * Apple Home style device health monitor.
 * WebSocket-powered, real-time, expandable rows, timeline bars.
 */

const PANEL_VERSION = "1.1.0";

// ════════════════════════════════════════════════════════════
// SECTION 1: Panel Class
// ════════════════════════════════════════════════════════════

class Cardio4HAPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._narrow = false;
    this._panel = {};
    this._data = null;
    this._unsub = null;
    this._view = "overview";
    this._filters = { area: "all", severity: "all", search: "" };
    this._sort = { col: null, dir: "asc" };
    this._scanning = false;
    this._connected = false;
    this._maintenanceDialog = null;
    this._expandedRows = new Set();
    this._timelineCache = {};
    this._flakyKeys = new Set();
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) {
      this._subscribe();
      this._render();
    }
  }

  set narrow(n) {
    this._narrow = n;
    this._render();
  }

  set panel(p) { this._panel = p; }
  set route(r) {}

  connectedCallback() {
    if (this._hass && !this._unsub) {
      this._subscribe();
    }
  }

  disconnectedCallback() {
    this._unsubscribe();
  }

  // ── WebSocket ─────────────────────────────────────────────

  async _subscribe() {
    if (this._unsub || !this._hass) return;
    try {
      this._unsub = await this._hass.connection.subscribeMessage(
        (msg) => this._handleUpdate(msg),
        { type: "cardio4ha/subscribe" }
      );
      this._connected = true;
    } catch (e) {
      console.error("Cardio4HA: subscribe failed", e);
      this._connected = false;
    }
  }

  _unsubscribe() {
    if (this._unsub) {
      this._unsub();
      this._unsub = null;
    }
    this._connected = false;
  }

  _handleUpdate(msg) {
    this._data = msg;
    this._flakyKeys = new Set(msg.flaky_device_keys || []);
    this._updateDOM();
  }

  async _forceScan() {
    if (!this._hass || this._scanning) return;
    this._scanning = true;
    this._updateScanButton();
    try {
      await this._hass.callWS({ type: "cardio4ha/force_scan" });
    } catch (e) {
      console.error("Force scan failed", e);
    }
    setTimeout(() => { this._scanning = false; this._updateScanButton(); }, 2000);
  }

  async _fetchTimeline(deviceKey) {
    if (this._timelineCache[deviceKey]) return this._timelineCache[deviceKey];
    try {
      const result = await this._hass.callWS({
        type: "cardio4ha/get_device_timeline",
        device_key: deviceKey,
      });
      this._timelineCache[deviceKey] = result;
      return result;
    } catch (e) {
      console.error("Timeline fetch failed", e);
      return null;
    }
  }

  // ── View Switching ────────────────────────────────────────

  _switchView(view) {
    this._view = view;
    this._expandedRows.clear();
    this._filters = { area: "all", severity: "all", search: "" };
    this._sort = { col: null, dir: "asc" };
    this._render();
  }

  // ── Sort / Filter ─────────────────────────────────────────

  _toggleSort(col) {
    if (this._sort.col === col) {
      this._sort.dir = this._sort.dir === "asc" ? "desc" : "asc";
    } else {
      this._sort.col = col;
      this._sort.dir = "asc";
    }
    this._updateDOM();
  }

  _applyFilters(list) {
    let result = [...list];
    const f = this._filters;
    if (f.area && f.area !== "all") {
      result = result.filter(d => (d.area || "Unknown") === f.area);
    }
    if (f.severity && f.severity !== "all") {
      result = result.filter(d => d.severity === f.severity);
    }
    if (f.search) {
      const s = f.search.toLowerCase();
      result = result.filter(d =>
        (d.name || "").toLowerCase().includes(s) ||
        (d.entity_id || "").toLowerCase().includes(s) ||
        (d.area || "").toLowerCase().includes(s)
      );
    }
    return result;
  }

  _applySorting(list) {
    if (!this._sort.col) return list;
    const col = this._sort.col;
    const dir = this._sort.dir === "asc" ? 1 : -1;
    return [...list].sort((a, b) => {
      let va = a[col], vb = b[col];
      if (va == null) va = "";
      if (vb == null) vb = "";
      if (typeof va === "number" && typeof vb === "number") return (va - vb) * dir;
      return String(va).localeCompare(String(vb)) * dir;
    });
  }

  // ── Toggle Expand ─────────────────────────────────────────

  async _toggleExpand(deviceKey) {
    if (this._expandedRows.has(deviceKey)) {
      this._expandedRows.delete(deviceKey);
    } else {
      this._expandedRows.add(deviceKey);
      // Lazy load timeline
      if (!this._timelineCache[deviceKey]) {
        await this._fetchTimeline(deviceKey);
      }
    }
    this._updateDOM();
  }

  // ── Maintenance ───────────────────────────────────────────

  async _setMaintenance(entityId, duration = 3600) {
    try {
      await this._hass.callWS({
        type: "cardio4ha/set_maintenance",
        entity_id: entityId,
        duration: duration,
      });
    } catch (e) { console.error("Set maintenance failed", e); }
  }

  async _clearMaintenance(entityId) {
    try {
      await this._hass.callWS({
        type: "cardio4ha/clear_maintenance",
        entity_id: entityId,
      });
    } catch (e) { console.error("Clear maintenance failed", e); }
  }

  // ── Ignore ───────────────────────────────────────────────

  async _setIgnore(deviceKey, name = "", area = "") {
    try {
      await this._hass.callWS({
        type: "cardio4ha/set_ignore",
        device_key: deviceKey,
        name: name,
        area: area,
      });
    } catch (e) { console.error("Set ignore failed", e); }
  }

  async _clearIgnore(deviceKey) {
    try {
      if (deviceKey) {
        await this._hass.callWS({
          type: "cardio4ha/clear_ignore",
          device_key: deviceKey,
        });
      } else {
        await this._hass.callWS({
          type: "cardio4ha/clear_ignore",
        });
      }
    } catch (e) { console.error("Clear ignore failed", e); }
  }

  // ── Export CSV ─────────────────────────────────────────────

  _exportCSV() {
    if (!this._data) return;
    const d = this._data;
    let csv = "Type,Name,Entity ID,Area,Severity,Value\n";
    (d.unavailable || []).forEach(dev => {
      csv += `Unavailable,"${dev.name}","${dev.entity_id}","${dev.area || ""}","${dev.severity}","${dev.duration_human}"\n`;
    });
    (d.low_battery || []).forEach(dev => {
      csv += `Low Battery,"${dev.name}","${dev.entity_id}","${dev.area || ""}","${dev.severity}","${dev.battery_level}%"\n`;
    });
    (d.weak_signal || []).forEach(dev => {
      csv += `Weak Signal,"${dev.name}","${dev.entity_id}","${dev.area || ""}","${dev.severity}","${dev.linkquality || dev.rssi}"\n`;
    });
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cardio4ha_export_${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // ── Update Helpers ────────────────────────────────────────

  _updateScanButton() {
    const btn = this.shadowRoot.querySelector(".scan-btn");
    if (btn) {
      btn.disabled = this._scanning;
      btn.textContent = this._scanning ? "Scanning..." : "Scan Now";
    }
  }

  _updateDOM() {
    const content = this.shadowRoot.querySelector(".content-area");
    if (!content) return;
    content.innerHTML = this._renderContent();
    this._attachContentEvents();
  }

  // ════════════════════════════════════════════════════════════
  // SECTION 2: Main Render
  // ════════════════════════════════════════════════════════════

  _render() {
    const root = this.shadowRoot;
    root.innerHTML = `
      <style>${this._getStyles()}</style>
      <div class="panel">
        ${this._renderHeader()}
        <div class="tabs-bar">${this._renderTabs()}</div>
        <div class="content-area">${this._renderContent()}</div>
      </div>
    `;
    this._attachEvents();
  }

  _renderHeader() {
    return `
      <div class="header">
        <div class="header-left">
          <ha-icon icon="mdi:heart-pulse" class="header-icon"></ha-icon>
          <div>
            <h1>Cardio4HA</h1>
            <span class="header-sub">Device Health Monitor v${PANEL_VERSION}</span>
          </div>
        </div>
        <div class="header-actions">
          <button class="scan-btn" ${this._scanning ? "disabled" : ""}>${this._scanning ? "Scanning..." : "Scan Now"}</button>
          <button class="export-btn" title="Export CSV">Export</button>
        </div>
      </div>`;
  }

  _renderTabs() {
    const tabs = [
      { id: "overview", label: "Overview", icon: "mdi:view-dashboard" },
      { id: "unavailable", label: "Unavailable", icon: "mdi:alert-circle-outline" },
      { id: "battery", label: "Battery", icon: "mdi:battery-alert" },
      { id: "signal", label: "Signal", icon: "mdi:signal" },
      { id: "maintenance", label: "Maintenance", icon: "mdi:wrench" },
    ];
    return tabs.map(t => `
      <button class="tab ${this._view === t.id ? "active" : ""}" data-view="${t.id}">
        <ha-icon icon="${t.icon}"></ha-icon>
        <span>${t.label}</span>
        ${this._getTabBadge(t.id)}
      </button>
    `).join("");
  }

  _getTabBadge(viewId) {
    if (!this._data) return "";
    const s = this._data.summary || {};
    let count = 0;
    if (viewId === "unavailable") count = s.unavailable_count || 0;
    else if (viewId === "battery") count = s.low_battery_count || 0;
    else if (viewId === "signal") count = s.weak_signal_count || 0;
    else if (viewId === "maintenance") count = Object.keys(this._data.maintenance || {}).length + Object.keys(this._data.ignored_devices || {}).length;
    if (count > 0) return `<span class="tab-badge">${count}</span>`;
    return "";
  }

  // ════════════════════════════════════════════════════════════
  // SECTION 3: Content Rendering
  // ════════════════════════════════════════════════════════════

  _renderContent() {
    if (!this._data) return `<div class="loading"><div class="spinner"></div><p>Loading device data...</p></div>`;
    switch (this._view) {
      case "overview": return this._renderOverview();
      case "unavailable": return this._renderUnavailable();
      case "battery": return this._renderBattery();
      case "signal": return this._renderSignal();
      case "maintenance": return this._renderMaintenance();
      default: return "";
    }
  }

  // ── Overview ──────────────────────────────────────────────

  _renderOverview() {
    const d = this._data;
    const s = d.summary || {};
    const score = s.health_score ?? 100;
    const critical = s.critical_count || 0;
    const flaky = s.flaky_count || 0;

    return `
      ${critical > 0 ? this._renderCriticalBanner(critical) : ""}
      <div class="overview-grid">
        <div class="score-card">
          ${this._renderHealthRing(score)}
          <div class="score-label">Health Score</div>
        </div>
        <div class="stats-row">
          ${this._renderStatCard("Unavailable", s.unavailable_count || 0, "mdi:alert-circle-outline", "var(--error-color, #db4437)")}
          ${this._renderStatCard("Low Battery", s.low_battery_count || 0, "mdi:battery-alert", "var(--warning-color, #f4b400)")}
          ${this._renderStatCard("Weak Signal", s.weak_signal_count || 0, "mdi:signal-off", "var(--warning-color, #f4b400)")}
          ${this._renderStatCard("Flaky", flaky, "mdi:swap-horizontal", "#9c27b0")}
        </div>
      </div>
      ${this._renderRecentNotifications()}
      ${flaky > 0 ? this._renderFlakyOverview() : ""}
    `;
  }

  _renderCriticalBanner(count) {
    return `
      <div class="critical-banner">
        <ha-icon icon="mdi:alert"></ha-icon>
        <span>${count} critical issue${count !== 1 ? "s" : ""} require attention</span>
      </div>`;
  }

  _renderHealthRing(score) {
    const size = 180;
    const stroke = 12;
    const r = (size - stroke) / 2;
    const circ = 2 * Math.PI * r;
    const offset = circ * (1 - score / 100);
    let color = "#4caf50";
    if (score < 50) color = "var(--error-color, #db4437)";
    else if (score < 75) color = "var(--warning-color, #f4b400)";
    else if (score < 90) color = "#8bc34a";

    return `
      <svg class="health-ring" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
        <circle cx="${size/2}" cy="${size/2}" r="${r}" fill="none" stroke="var(--divider-color, #e0e0e0)" stroke-width="${stroke}" opacity="0.3"/>
        <circle cx="${size/2}" cy="${size/2}" r="${r}" fill="none" stroke="${color}" stroke-width="${stroke}"
          stroke-dasharray="${circ}" stroke-dashoffset="${offset}" stroke-linecap="round"
          transform="rotate(-90 ${size/2} ${size/2})" class="ring-progress"/>
        <text x="${size/2}" y="${size/2 - 8}" text-anchor="middle" class="ring-score" fill="var(--primary-text-color)">${score}</text>
        <text x="${size/2}" y="${size/2 + 16}" text-anchor="middle" class="ring-label" fill="var(--secondary-text-color)">/ 100</text>
      </svg>`;
  }

  _renderStatCard(label, count, icon, color) {
    return `
      <div class="stat-card">
        <div class="stat-icon" style="background: ${color}20; color: ${color}">
          <ha-icon icon="${icon}"></ha-icon>
        </div>
        <div class="stat-value">${count}</div>
        <div class="stat-label">${label}</div>
      </div>`;
  }

  _renderRecentNotifications() {
    const notifs = this._data.notification_history || [];
    if (notifs.length === 0) return "";
    const recent = notifs.slice(-5).reverse();
    return `
      <div class="section-card">
        <h3>Recent Notifications</h3>
        <div class="notif-list">
          ${recent.map(n => `
            <div class="notif-item notif-${n.type}">
              <ha-icon icon="${this._getNotifIcon(n.type)}"></ha-icon>
              <div class="notif-content">
                <div class="notif-title">${this._escapeHtml(n.title)}</div>
                <div class="notif-time">${this._formatTime(n.ts)}</div>
              </div>
            </div>
          `).join("")}
        </div>
      </div>`;
  }

  _renderFlakyOverview() {
    const flaky = this._data.flaky_devices || [];
    return `
      <div class="section-card">
        <h3>Flaky Devices (Unstable)</h3>
        <div class="flaky-list">
          ${flaky.map(f => `
            <div class="flaky-item">
              <span class="flaky-badge">Unstable</span>
              <span class="flaky-name">${this._escapeHtml(f.name)}</span>
              <span class="flaky-count">${f.offline_count_30d} offline events (30d)</span>
            </div>
          `).join("")}
        </div>
      </div>`;
  }

  // ── Unavailable View ──────────────────────────────────────

  _renderUnavailable() {
    const raw = this._data.unavailable || [];
    const filtered = this._applySorting(this._applyFilters(raw));
    const critical = (this._data.summary || {}).critical_count || 0;

    return `
      ${critical > 0 ? this._renderCriticalBanner(critical) : ""}
      ${this._renderFilterBar(raw)}
      ${filtered.length === 0
        ? `<div class="empty-state"><ha-icon icon="mdi:check-circle"></ha-icon><p>No unavailable devices</p></div>`
        : `<div class="device-list">${filtered.map(d => this._renderUnavailableRow(d)).join("")}</div>`
      }`;
  }

  _renderUnavailableRow(dev) {
    const dk = dev.device_key || dev.entity_id;
    const expanded = this._expandedRows.has(dk);
    const isFlaky = this._flakyKeys.has(dk);

    return `
      <div class="device-row ${expanded ? "expanded" : ""}" data-key="${dk}">
        <div class="device-row-main" data-expand="${dk}">
          <div class="device-info">
            <div class="device-name">
              ${this._escapeHtml(dev.name)}
              ${isFlaky ? '<span class="flaky-badge">Unstable</span>' : ""}
            </div>
            <div class="device-meta">${this._escapeHtml(dev.area || "No area")} &middot; ${this._escapeHtml(dev.integration || "")}</div>
          </div>
          <div class="device-values">
            <span class="duration-badge severity-${dev.severity}">${dev.duration_human}</span>
            <ha-icon icon="mdi:chevron-${expanded ? "up" : "down"}" class="expand-icon"></ha-icon>
          </div>
        </div>
        ${expanded ? this._renderExpandedUnavailable(dev, dk) : ""}
      </div>`;
  }

  _renderExpandedUnavailable(dev, dk) {
    const timeline = this._timelineCache[dk];
    return `
      <div class="expanded-content">
        ${timeline ? this._renderTimelineBar(timeline.timeline) : '<div class="timeline-loading">Loading timeline...</div>'}
        <div class="detail-grid">
          <div class="detail-item"><span class="detail-label">Entity</span><span class="detail-value entity-link" data-entity="${dev.entity_id}">${dev.entity_id}</span></div>
          <div class="detail-item"><span class="detail-label">Area</span><span class="detail-value">${this._escapeHtml(dev.area || "None")}</span></div>
          <div class="detail-item"><span class="detail-label">Since</span><span class="detail-value">${this._formatTime(dev.since)}</span></div>
          <div class="detail-item"><span class="detail-label">Integration</span><span class="detail-value">${this._escapeHtml(dev.integration || "unknown")}</span></div>
          ${dev.device_id ? `<div class="detail-item"><span class="detail-label">Device ID</span><span class="detail-value">${dev.device_id}</span></div>` : ""}
        </div>
        <div class="action-buttons">
          <button class="action-btn maintenance-btn" data-entity="${dev.entity_id}">
            <ha-icon icon="mdi:wrench"></ha-icon> Maintenance
          </button>
          <button class="action-btn ignore-btn" data-key="${dk}" data-name="${this._escapeHtml(dev.name || "")}" data-area="${this._escapeHtml(dev.area || "")}">
            <ha-icon icon="mdi:eye-off"></ha-icon> Ignore
          </button>
          <button class="action-btn info-btn" data-entity="${dev.entity_id}">
            <ha-icon icon="mdi:information"></ha-icon> More Info
          </button>
        </div>
      </div>`;
  }

  // ── Battery View ──────────────────────────────────────────

  _renderBattery() {
    const raw = this._data.low_battery || [];
    const predictions = this._data.battery_predictions || {};
    const filtered = this._applySorting(this._applyFilters(raw));

    return `
      ${this._renderFilterBar(raw)}
      ${filtered.length === 0
        ? `<div class="empty-state"><ha-icon icon="mdi:battery-check"></ha-icon><p>All batteries healthy</p></div>`
        : `<div class="device-list">${filtered.map(d => this._renderBatteryRow(d, predictions)).join("")}</div>`
      }`;
  }

  _renderBatteryRow(dev, predictions) {
    const dk = dev.device_key || dev.entity_id;
    const expanded = this._expandedRows.has(dk);
    const isFlaky = this._flakyKeys.has(dk);
    const level = dev.battery_level;
    const daysRemaining = dev.days_remaining ?? predictions[dk] ?? null;

    return `
      <div class="device-row ${expanded ? "expanded" : ""}" data-key="${dk}">
        <div class="device-row-main" data-expand="${dk}">
          <div class="device-info">
            <div class="device-name">
              ${this._escapeHtml(dev.name)}
              ${isFlaky ? '<span class="flaky-badge">Unstable</span>' : ""}
            </div>
            <div class="device-meta">${this._escapeHtml(dev.area || "No area")}</div>
          </div>
          <div class="device-values">
            <div class="battery-display">
              ${this._renderBatteryBar(level, dev.severity)}
              <span class="battery-pct">${Math.round(level)}%</span>
            </div>
            ${daysRemaining !== null ? `<span class="prediction-badge">${daysRemaining}d left</span>` : ""}
            <ha-icon icon="mdi:chevron-${expanded ? "up" : "down"}" class="expand-icon"></ha-icon>
          </div>
        </div>
        ${expanded ? this._renderExpandedBattery(dev, dk, daysRemaining) : ""}
      </div>`;
  }

  _renderBatteryBar(level, severity) {
    let color = "#4caf50";
    if (severity === "critical") color = "var(--error-color, #db4437)";
    else if (severity === "warning") color = "var(--warning-color, #f4b400)";
    else if (severity === "low") color = "#ff9800";
    return `
      <div class="battery-bar-container">
        <div class="battery-bar" style="width: ${level}%; background: ${color}"></div>
      </div>`;
  }

  _renderExpandedBattery(dev, dk, daysRemaining) {
    const timeline = this._timelineCache[dk];
    const readings = timeline ? timeline.battery_readings || [] : [];
    return `
      <div class="expanded-content">
        ${readings.length > 0 ? this._renderBatteryChart(readings) : ""}
        <div class="detail-grid">
          <div class="detail-item"><span class="detail-label">Entity</span><span class="detail-value entity-link" data-entity="${dev.entity_id}">${dev.entity_id}</span></div>
          <div class="detail-item"><span class="detail-label">Level</span><span class="detail-value">${Math.round(dev.battery_level)}%</span></div>
          <div class="detail-item"><span class="detail-label">Area</span><span class="detail-value">${this._escapeHtml(dev.area || "None")}</span></div>
          ${daysRemaining !== null ? `<div class="detail-item"><span class="detail-label">Predicted Empty</span><span class="detail-value">${daysRemaining} days</span></div>` : ""}
        </div>
        <div class="action-buttons">
          <button class="action-btn ignore-btn" data-key="${dk}" data-name="${this._escapeHtml(dev.name || "")}" data-area="${this._escapeHtml(dev.area || "")}">
            <ha-icon icon="mdi:eye-off"></ha-icon> Ignore
          </button>
          <button class="action-btn info-btn" data-entity="${dev.entity_id}">
            <ha-icon icon="mdi:information"></ha-icon> More Info
          </button>
        </div>
      </div>`;
  }

  _renderBatteryChart(readings) {
    if (readings.length < 2) return "";
    const w = 320, h = 80, pad = 4;
    const minTs = readings[0].ts, maxTs = readings[readings.length - 1].ts;
    const tsRange = maxTs - minTs || 1;
    const points = readings.map(r => {
      const x = pad + ((r.ts - minTs) / tsRange) * (w - 2 * pad);
      const y = pad + (1 - r.level / 100) * (h - 2 * pad);
      return `${x},${y}`;
    }).join(" ");
    return `
      <div class="mini-chart">
        <svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
          <polyline points="${points}" fill="none" stroke="var(--warning-color, #f4b400)" stroke-width="2" stroke-linejoin="round"/>
        </svg>
        <div class="chart-label">Battery trend (30d)</div>
      </div>`;
  }

  // ── Signal View ───────────────────────────────────────────

  _renderSignal() {
    const raw = this._data.weak_signal || [];
    const filtered = this._applySorting(this._applyFilters(raw));

    return `
      ${this._renderFilterBar(raw)}
      ${filtered.length === 0
        ? `<div class="empty-state"><ha-icon icon="mdi:signal-cellular-3"></ha-icon><p>All signals healthy</p></div>`
        : `<div class="device-list">${filtered.map(d => this._renderSignalRow(d)).join("")}</div>`
      }`;
  }

  _renderSignalRow(dev) {
    const dk = dev.device_key || dev.entity_id;
    const expanded = this._expandedRows.has(dk);
    const isFlaky = this._flakyKeys.has(dk);
    const val = dev.signal_type === "zigbee" ? dev.linkquality : dev.rssi;
    const label = dev.signal_type === "zigbee" ? `LQI: ${Math.round(val)}` : `${Math.round(val)} dBm`;

    return `
      <div class="device-row ${expanded ? "expanded" : ""}" data-key="${dk}">
        <div class="device-row-main" data-expand="${dk}">
          <div class="device-info">
            <div class="device-name">
              ${this._escapeHtml(dev.name)}
              ${isFlaky ? '<span class="flaky-badge">Unstable</span>' : ""}
            </div>
            <div class="device-meta">${this._escapeHtml(dev.area || "No area")} &middot; ${dev.signal_type}</div>
          </div>
          <div class="device-values">
            ${this._renderSignalBars(dev)}
            <span class="signal-label severity-${dev.severity}">${label}</span>
            <ha-icon icon="mdi:chevron-${expanded ? "up" : "down"}" class="expand-icon"></ha-icon>
          </div>
        </div>
        ${expanded ? this._renderExpandedSignal(dev, dk) : ""}
      </div>`;
  }

  _renderSignalBars(dev) {
    let strength = 0;
    if (dev.signal_type === "zigbee") {
      strength = Math.min(5, Math.max(0, Math.round(dev.linkquality / 51)));
    } else {
      const rssi = dev.rssi || -100;
      if (rssi >= -50) strength = 5;
      else if (rssi >= -60) strength = 4;
      else if (rssi >= -70) strength = 3;
      else if (rssi >= -80) strength = 2;
      else if (rssi >= -90) strength = 1;
    }
    let bars = "";
    for (let i = 1; i <= 5; i++) {
      const h = 4 + i * 3;
      const active = i <= strength;
      bars += `<div class="signal-bar" style="height:${h}px;${active ? "" : "opacity:0.2"}"></div>`;
    }
    return `<div class="signal-bars">${bars}</div>`;
  }

  _renderExpandedSignal(dev, dk) {
    const timeline = this._timelineCache[dk];
    const readings = timeline ? timeline.signal_readings || [] : [];
    return `
      <div class="expanded-content">
        ${readings.length > 1 ? this._renderSignalChart(readings, dev.signal_type) : ""}
        <div class="detail-grid">
          <div class="detail-item"><span class="detail-label">Entity</span><span class="detail-value entity-link" data-entity="${dev.entity_id}">${dev.entity_id}</span></div>
          <div class="detail-item"><span class="detail-label">Type</span><span class="detail-value">${dev.signal_type}</span></div>
          <div class="detail-item"><span class="detail-label">Value</span><span class="detail-value">${dev.signal_type === "zigbee" ? dev.linkquality : dev.rssi}</span></div>
          <div class="detail-item"><span class="detail-label">Area</span><span class="detail-value">${this._escapeHtml(dev.area || "None")}</span></div>
        </div>
        <div class="action-buttons">
          <button class="action-btn ignore-btn" data-key="${dk}" data-name="${this._escapeHtml(dev.name || "")}" data-area="${this._escapeHtml(dev.area || "")}">
            <ha-icon icon="mdi:eye-off"></ha-icon> Ignore
          </button>
          <button class="action-btn info-btn" data-entity="${dev.entity_id}">
            <ha-icon icon="mdi:information"></ha-icon> More Info
          </button>
        </div>
      </div>`;
  }

  _renderSignalChart(readings, type) {
    if (readings.length < 2) return "";
    const w = 320, h = 80, pad = 4;
    const values = readings.map(r => r.value);
    const minV = Math.min(...values), maxV = Math.max(...values);
    const vRange = maxV - minV || 1;
    const minTs = readings[0].ts, maxTs = readings[readings.length - 1].ts;
    const tsRange = maxTs - minTs || 1;
    const points = readings.map(r => {
      const x = pad + ((r.ts - minTs) / tsRange) * (w - 2 * pad);
      const y = pad + (1 - (r.value - minV) / vRange) * (h - 2 * pad);
      return `${x},${y}`;
    }).join(" ");
    return `
      <div class="mini-chart">
        <svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
          <polyline points="${points}" fill="none" stroke="var(--info-color, #039be5)" stroke-width="2" stroke-linejoin="round"/>
        </svg>
        <div class="chart-label">Signal trend (30d)</div>
      </div>`;
  }

  // ── Timeline Bar ──────────────────────────────────────────

  _renderTimelineBar(timeline) {
    if (!timeline || timeline.length === 0) return '<div class="timeline-empty">No timeline data yet</div>';
    const days = timeline.length;
    return `
      <div class="timeline-section">
        <div class="timeline-label">30-Day Uptime</div>
        <div class="timeline-bar">
          ${timeline.map((day, i) => {
            let color = "#4caf50";
            if (day.uptime_pct < 50) color = "var(--error-color, #db4437)";
            else if (day.uptime_pct < 90) color = "var(--warning-color, #f4b400)";
            else if (day.uptime_pct < 99) color = "#8bc34a";
            return `<div class="timeline-day" style="background:${color}" title="${day.date}: ${day.uptime_pct}% uptime, ${day.events} events"></div>`;
          }).join("")}
        </div>
        <div class="timeline-dates">
          <span>${timeline[0]?.date || ""}</span>
          <span>Today</span>
        </div>
      </div>`;
  }

  // ── Maintenance View ──────────────────────────────────────

  _renderMaintenance() {
    const maint = this._data.maintenance || {};
    const entries = Object.entries(maint);

    return `
      <div class="section-card">
        <h3>Devices Under Maintenance</h3>
        ${entries.length === 0
          ? `<div class="empty-state-inline">No devices under maintenance</div>`
          : `<div class="device-list">${entries.map(([entityId, info]) => `
              <div class="device-row">
                <div class="device-row-main">
                  <div class="device-info">
                    <div class="device-name">${this._escapeHtml(entityId)}</div>
                    <div class="device-meta">Set: ${this._formatTime(info.set_at)} &middot; Expires: ${this._formatTime(info.expires_at)}</div>
                  </div>
                  <div class="device-values">
                    <button class="action-btn clear-maint-btn" data-entity="${entityId}">
                      <ha-icon icon="mdi:close"></ha-icon> Clear
                    </button>
                  </div>
                </div>
              </div>
            `).join("")}</div>`
        }
      </div>
      <div class="section-card">
        <div class="action-buttons">
          <button class="action-btn clear-all-maint-btn">
            <ha-icon icon="mdi:broom"></ha-icon> Clear All Maintenance
          </button>
        </div>
      </div>
      ${this._renderIgnoredDevices()}`;
  }

  _renderIgnoredDevices() {
    const ignored = this._data.ignored_devices || {};
    const entries = Object.entries(ignored);

    return `
      <div class="section-card" style="margin-top: 20px;">
        <h3>Ignored Devices</h3>
        ${entries.length === 0
          ? `<div class="empty-state-inline">No ignored devices</div>`
          : `<div class="device-list">${entries.map(([deviceKey, info]) => `
              <div class="device-row">
                <div class="device-row-main">
                  <div class="device-info">
                    <div class="device-name">${this._escapeHtml(info.name || deviceKey)}</div>
                    <div class="device-meta">${this._escapeHtml(info.area || "No area")} &middot; Since: ${this._formatTime(info.ignored_since)}</div>
                  </div>
                  <div class="device-values">
                    <button class="action-btn clear-ignore-btn" data-key="${deviceKey}">
                      <ha-icon icon="mdi:eye"></ha-icon> Un-ignore
                    </button>
                  </div>
                </div>
              </div>
            `).join("")}</div>`
        }
      </div>
      ${entries.length > 0 ? `
      <div class="section-card">
        <div class="action-buttons">
          <button class="action-btn clear-all-ignore-btn">
            <ha-icon icon="mdi:eye"></ha-icon> Clear All Ignored
          </button>
        </div>
      </div>` : ""}`;
  }

  // ── Filter Bar ────────────────────────────────────────────

  _renderFilterBar(data) {
    const areas = [...new Set(data.map(d => d.area || "Unknown"))].sort();
    return `
      <div class="filter-bar">
        <input type="text" class="search-input" placeholder="Search devices..." value="${this._escapeHtml(this._filters.search)}">
        <select class="filter-select area-filter">
          <option value="all">All Areas</option>
          ${areas.map(a => `<option value="${this._escapeHtml(a)}" ${this._filters.area === a ? "selected" : ""}>${this._escapeHtml(a)}</option>`).join("")}
        </select>
        <select class="filter-select severity-filter">
          <option value="all">All Severity</option>
          <option value="critical" ${this._filters.severity === "critical" ? "selected" : ""}>Critical</option>
          <option value="warning" ${this._filters.severity === "warning" ? "selected" : ""}>Warning</option>
          <option value="low" ${this._filters.severity === "low" ? "selected" : ""}>Low</option>
        </select>
        <span class="result-count">${this._applyFilters(data).length} device${this._applyFilters(data).length !== 1 ? "s" : ""}</span>
      </div>`;
  }

  // ── Helpers ───────────────────────────────────────────────

  _getNotifIcon(type) {
    const icons = {
      device_offline: "mdi:alert-circle",
      battery_critical: "mdi:battery-alert",
      mass_offline: "mdi:alert-octagon",
      device_recovered: "mdi:check-circle",
      daily_digest: "mdi:clipboard-text",
    };
    return icons[type] || "mdi:bell";
  }

  _formatTime(ts) {
    if (!ts) return "Unknown";
    try {
      const d = new Date(ts);
      if (isNaN(d.getTime())) return "Unknown";
      const now = new Date();
      const diff = now - d;
      if (diff < 60000) return "Just now";
      if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
      if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
      return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
    } catch (e) { return "Unknown"; }
  }

  _escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // ════════════════════════════════════════════════════════════
  // SECTION 4: Event Handlers
  // ════════════════════════════════════════════════════════════

  _attachEvents() {
    const root = this.shadowRoot;

    // Tabs
    root.querySelectorAll(".tab").forEach(tab => {
      tab.addEventListener("click", () => this._switchView(tab.dataset.view));
    });

    // Scan button
    const scanBtn = root.querySelector(".scan-btn");
    if (scanBtn) scanBtn.addEventListener("click", () => this._forceScan());

    // Export
    const exportBtn = root.querySelector(".export-btn");
    if (exportBtn) exportBtn.addEventListener("click", () => this._exportCSV());

    this._attachContentEvents();
  }

  _attachContentEvents() {
    const root = this.shadowRoot;

    // Expandable rows
    root.querySelectorAll("[data-expand]").forEach(el => {
      el.addEventListener("click", (e) => {
        if (e.target.closest(".action-btn") || e.target.closest(".entity-link")) return;
        this._toggleExpand(el.dataset.expand);
      });
    });

    // Filters
    const search = root.querySelector(".search-input");
    if (search) {
      search.addEventListener("input", (e) => {
        this._filters.search = e.target.value;
        this._updateDOM();
      });
    }

    const areaFilter = root.querySelector(".area-filter");
    if (areaFilter) {
      areaFilter.addEventListener("change", (e) => {
        this._filters.area = e.target.value;
        this._updateDOM();
      });
    }

    const sevFilter = root.querySelector(".severity-filter");
    if (sevFilter) {
      sevFilter.addEventListener("change", (e) => {
        this._filters.severity = e.target.value;
        this._updateDOM();
      });
    }

    // Entity links
    root.querySelectorAll(".entity-link").forEach(el => {
      el.addEventListener("click", () => {
        const entityId = el.dataset.entity;
        if (entityId && this._hass) {
          const event = new Event("hass-more-info", { bubbles: true, composed: true });
          event.detail = { entityId };
          this.dispatchEvent(event);
        }
      });
    });

    // Maintenance buttons
    root.querySelectorAll(".maintenance-btn").forEach(btn => {
      btn.addEventListener("click", () => this._setMaintenance(btn.dataset.entity));
    });

    root.querySelectorAll(".clear-maint-btn").forEach(btn => {
      btn.addEventListener("click", () => this._clearMaintenance(btn.dataset.entity));
    });

    const clearAllBtn = root.querySelector(".clear-all-maint-btn");
    if (clearAllBtn) {
      clearAllBtn.addEventListener("click", async () => {
        try { await this._hass.callWS({ type: "cardio4ha/clear_maintenance" }); } catch (e) {}
      });
    }

    // Ignore buttons
    root.querySelectorAll(".ignore-btn").forEach(btn => {
      btn.addEventListener("click", () => this._setIgnore(btn.dataset.key, btn.dataset.name || "", btn.dataset.area || ""));
    });

    root.querySelectorAll(".clear-ignore-btn").forEach(btn => {
      btn.addEventListener("click", () => this._clearIgnore(btn.dataset.key));
    });

    const clearAllIgnoreBtn = root.querySelector(".clear-all-ignore-btn");
    if (clearAllIgnoreBtn) {
      clearAllIgnoreBtn.addEventListener("click", () => this._clearIgnore(null));
    }

    // More Info buttons
    root.querySelectorAll(".info-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const entityId = btn.dataset.entity;
        if (entityId && this._hass) {
          const event = new Event("hass-more-info", { bubbles: true, composed: true });
          event.detail = { entityId };
          this.dispatchEvent(event);
        }
      });
    });
  }

  // ════════════════════════════════════════════════════════════
  // SECTION 5: Styles
  // ════════════════════════════════════════════════════════════

  _getStyles() {
    return `
      :host {
        --card-bg: var(--ha-card-background, var(--card-background-color, #fff));
        --text-primary: var(--primary-text-color, #212121);
        --text-secondary: var(--secondary-text-color, #727272);
        --border: var(--divider-color, #e8e8e8);
        --accent: var(--primary-color, #03a9f4);
        --error: var(--error-color, #db4437);
        --warning: var(--warning-color, #f4b400);
        --success: #4caf50;
        --radius: 16px;
        --radius-sm: 12px;
        --shadow: 0 2px 8px rgba(0,0,0,0.06);
        --shadow-hover: 0 4px 16px rgba(0,0,0,0.1);
      }

      * { box-sizing: border-box; margin: 0; padding: 0; }

      .panel {
        min-height: 100vh;
        background: var(--primary-background-color, #fafafa);
        color: var(--text-primary);
        font-family: var(--paper-font-body1_-_font-family, "Roboto", sans-serif);
      }

      /* ── Header ── */
      .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 24px;
        background: var(--card-bg);
        box-shadow: var(--shadow);
        position: sticky;
        top: 0;
        z-index: 10;
      }
      .header-left {
        display: flex;
        align-items: center;
        gap: 14px;
      }
      .header-icon {
        --mdc-icon-size: 32px;
        color: var(--accent);
      }
      .header h1 {
        font-size: 22px;
        font-weight: 600;
        letter-spacing: -0.3px;
      }
      .header-sub {
        font-size: 13px;
        color: var(--text-secondary);
      }
      .header-actions {
        display: flex;
        gap: 10px;
      }
      .scan-btn, .export-btn {
        padding: 8px 18px;
        border-radius: var(--radius-sm);
        border: none;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
      }
      .scan-btn {
        background: var(--accent);
        color: #fff;
      }
      .scan-btn:hover:not(:disabled) { opacity: 0.85; transform: translateY(-1px); }
      .scan-btn:disabled { opacity: 0.5; cursor: default; }
      .export-btn {
        background: var(--card-bg);
        color: var(--text-primary);
        border: 1px solid var(--border);
      }
      .export-btn:hover { background: var(--border); }

      /* ── Tabs ── */
      .tabs-bar {
        display: flex;
        gap: 4px;
        padding: 12px 24px;
        background: var(--card-bg);
        border-bottom: 1px solid var(--border);
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
      }
      .tab {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 18px;
        border: none;
        border-radius: var(--radius-sm);
        background: transparent;
        color: var(--text-secondary);
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        white-space: nowrap;
        position: relative;
      }
      .tab:hover { background: rgba(0,0,0,0.04); }
      .tab.active {
        background: var(--accent);
        color: #fff;
      }
      .tab ha-icon { --mdc-icon-size: 20px; }
      .tab-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 20px;
        height: 20px;
        padding: 0 6px;
        border-radius: 10px;
        background: var(--error);
        color: #fff;
        font-size: 11px;
        font-weight: 700;
      }
      .tab.active .tab-badge {
        background: rgba(255,255,255,0.3);
      }

      /* ── Content Area ── */
      .content-area {
        padding: 20px 24px 40px;
        max-width: 1200px;
        margin: 0 auto;
      }

      /* ── Loading ── */
      .loading {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 80px 20px;
        color: var(--text-secondary);
      }
      .spinner {
        width: 40px;
        height: 40px;
        border: 3px solid var(--border);
        border-top-color: var(--accent);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        margin-bottom: 16px;
      }
      @keyframes spin { to { transform: rotate(360deg); } }

      /* ── Empty State ── */
      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 60px 20px;
        color: var(--text-secondary);
      }
      .empty-state ha-icon {
        --mdc-icon-size: 48px;
        color: var(--success);
        margin-bottom: 16px;
      }
      .empty-state p { font-size: 16px; }
      .empty-state-inline {
        padding: 24px;
        text-align: center;
        color: var(--text-secondary);
      }

      /* ── Critical Banner ── */
      .critical-banner {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 14px 20px;
        background: linear-gradient(135deg, #db443710, #db443720);
        border: 1px solid #db443740;
        border-radius: var(--radius);
        margin-bottom: 20px;
        color: var(--error);
        font-weight: 500;
      }
      .critical-banner ha-icon { --mdc-icon-size: 24px; }

      /* ── Overview ── */
      .overview-grid {
        display: flex;
        flex-direction: column;
        gap: 20px;
        margin-bottom: 24px;
      }
      .score-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 32px 24px 24px;
        background: var(--card-bg);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
      }
      .score-label {
        margin-top: 12px;
        font-size: 16px;
        font-weight: 500;
        color: var(--text-secondary);
      }
      .health-ring .ring-score {
        font-size: 48px;
        font-weight: 700;
      }
      .health-ring .ring-label {
        font-size: 16px;
      }
      .ring-progress {
        transition: stroke-dashoffset 1s ease;
      }

      .stats-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 12px;
      }
      .stat-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 20px 16px;
        background: var(--card-bg);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        text-align: center;
      }
      .stat-icon {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 10px;
      }
      .stat-icon ha-icon { --mdc-icon-size: 22px; }
      .stat-value {
        font-size: 28px;
        font-weight: 700;
        line-height: 1.1;
      }
      .stat-label {
        font-size: 13px;
        color: var(--text-secondary);
        margin-top: 4px;
      }

      /* ── Section Card ── */
      .section-card {
        background: var(--card-bg);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        padding: 20px 24px;
        margin-bottom: 16px;
      }
      .section-card h3 {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 16px;
      }

      /* ── Notifications ── */
      .notif-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .notif-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 14px;
        border-radius: var(--radius-sm);
        background: rgba(0,0,0,0.02);
      }
      .notif-item ha-icon { --mdc-icon-size: 20px; color: var(--text-secondary); }
      .notif-device_offline ha-icon { color: var(--error); }
      .notif-battery_critical ha-icon { color: var(--warning); }
      .notif-device_recovered ha-icon { color: var(--success); }
      .notif-mass_offline ha-icon { color: var(--error); }
      .notif-content { flex: 1; min-width: 0; }
      .notif-title { font-size: 14px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .notif-time { font-size: 12px; color: var(--text-secondary); }

      /* ── Flaky ── */
      .flaky-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .flaky-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        border-radius: var(--radius-sm);
        background: rgba(156, 39, 176, 0.06);
      }
      .flaky-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        background: #9c27b0;
        color: #fff;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: nowrap;
      }
      .flaky-name { font-weight: 500; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .flaky-count { font-size: 13px; color: var(--text-secondary); white-space: nowrap; }

      /* ── Filter Bar ── */
      .filter-bar {
        display: flex;
        gap: 10px;
        align-items: center;
        margin-bottom: 16px;
        flex-wrap: wrap;
      }
      .search-input {
        flex: 1;
        min-width: 180px;
        padding: 10px 14px;
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        background: var(--card-bg);
        color: var(--text-primary);
        font-size: 14px;
        outline: none;
        transition: border-color 0.2s;
      }
      .search-input:focus { border-color: var(--accent); }
      .filter-select {
        padding: 10px 14px;
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        background: var(--card-bg);
        color: var(--text-primary);
        font-size: 14px;
        outline: none;
        cursor: pointer;
      }
      .result-count {
        font-size: 13px;
        color: var(--text-secondary);
        white-space: nowrap;
      }

      /* ── Device List ── */
      .device-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .device-row {
        background: var(--card-bg);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        overflow: hidden;
        transition: box-shadow 0.2s;
      }
      .device-row:hover { box-shadow: var(--shadow-hover); }
      .device-row.expanded { box-shadow: var(--shadow-hover); }

      .device-row-main {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 20px;
        cursor: pointer;
        gap: 16px;
      }
      .device-info { flex: 1; min-width: 0; }
      .device-name {
        font-size: 15px;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
      }
      .device-meta {
        font-size: 13px;
        color: var(--text-secondary);
        margin-top: 2px;
      }
      .device-values {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-shrink: 0;
      }
      .expand-icon {
        --mdc-icon-size: 20px;
        color: var(--text-secondary);
        transition: transform 0.2s;
      }

      /* ── Severity Badges ── */
      .duration-badge, .signal-label {
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        white-space: nowrap;
      }
      .severity-critical { background: #db443715; color: var(--error); }
      .severity-warning { background: #f4b40015; color: #e6a000; }
      .severity-low { background: #ff980015; color: #e68900; }

      /* ── Battery ── */
      .battery-display {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .battery-bar-container {
        width: 60px;
        height: 10px;
        background: var(--border);
        border-radius: 5px;
        overflow: hidden;
      }
      .battery-bar {
        height: 100%;
        border-radius: 5px;
        transition: width 0.5s ease;
      }
      .battery-pct {
        font-size: 14px;
        font-weight: 600;
        min-width: 36px;
        text-align: right;
      }
      .prediction-badge {
        padding: 3px 8px;
        border-radius: 6px;
        background: #ff980015;
        color: #e68900;
        font-size: 12px;
        font-weight: 600;
        white-space: nowrap;
      }

      /* ── Signal Bars ── */
      .signal-bars {
        display: flex;
        align-items: flex-end;
        gap: 2px;
        height: 20px;
      }
      .signal-bar {
        width: 5px;
        border-radius: 2px;
        background: var(--text-secondary);
        transition: opacity 0.3s;
      }

      /* ── Expanded Content ── */
      .expanded-content {
        padding: 0 20px 20px;
        border-top: 1px solid var(--border);
        animation: slideDown 0.2s ease;
      }
      @keyframes slideDown {
        from { opacity: 0; max-height: 0; }
        to { opacity: 1; max-height: 600px; }
      }

      .detail-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        padding: 16px 0;
      }
      .detail-item {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .detail-label {
        font-size: 12px;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .detail-value {
        font-size: 14px;
        font-weight: 500;
        word-break: break-all;
      }
      .entity-link {
        color: var(--accent);
        cursor: pointer;
        text-decoration: none;
      }
      .entity-link:hover { text-decoration: underline; }

      /* ── Timeline ── */
      .timeline-section {
        padding: 16px 0 8px;
      }
      .timeline-label {
        font-size: 12px;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
      }
      .timeline-bar {
        display: flex;
        gap: 2px;
        height: 24px;
        border-radius: 4px;
        overflow: hidden;
      }
      .timeline-day {
        flex: 1;
        border-radius: 2px;
        transition: opacity 0.2s;
        cursor: default;
      }
      .timeline-day:hover { opacity: 0.7; }
      .timeline-dates {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        color: var(--text-secondary);
        margin-top: 4px;
      }
      .timeline-loading, .timeline-empty {
        padding: 16px 0;
        text-align: center;
        color: var(--text-secondary);
        font-size: 13px;
      }

      /* ── Mini Chart ── */
      .mini-chart {
        padding: 12px 0;
      }
      .mini-chart svg {
        width: 100%;
        height: 60px;
        border-radius: 8px;
        background: rgba(0,0,0,0.02);
      }
      .chart-label {
        font-size: 11px;
        color: var(--text-secondary);
        margin-top: 4px;
        text-align: center;
      }

      /* ── Action Buttons ── */
      .action-buttons {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
      .action-btn {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 8px 14px;
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        background: var(--card-bg);
        color: var(--text-primary);
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
      }
      .action-btn:hover { background: var(--border); }
      .action-btn ha-icon { --mdc-icon-size: 18px; }
      .ignore-btn { color: var(--warning-color, #f4b400); border-color: var(--warning-color, #f4b400); }
      .ignore-btn:hover { background: rgba(244, 180, 0, 0.1); }
      .clear-ignore-btn { color: var(--success-color, #4caf50); }
      .clear-all-ignore-btn { color: var(--warning-color, #f4b400); border-color: var(--warning-color, #f4b400); }
      .clear-all-ignore-btn:hover { background: rgba(244, 180, 0, 0.1); }

      /* ── Mobile ── */
      @media (max-width: 600px) {
        .header {
          padding: 14px 16px;
          flex-wrap: wrap;
          gap: 10px;
        }
        .header h1 { font-size: 18px; }
        .header-actions { width: 100%; justify-content: flex-end; }
        .tabs-bar { padding: 8px 12px; gap: 2px; }
        .tab { padding: 8px 12px; font-size: 13px; }
        .tab span { display: none; }
        .content-area { padding: 14px 12px 30px; }
        .stats-row { grid-template-columns: repeat(2, 1fr); }
        .filter-bar { flex-direction: column; }
        .search-input { min-width: 100%; }
        .device-row-main { padding: 12px 14px; flex-wrap: wrap; }
        .detail-grid { grid-template-columns: 1fr; }
        .score-card { padding: 24px 16px 20px; }
        .health-ring .ring-score { font-size: 40px; }
      }

      /* ── Tablet ── */
      @media (min-width: 601px) and (max-width: 1024px) {
        .stats-row { grid-template-columns: repeat(2, 1fr); }
      }
    `;
  }
}

customElements.define("cardio4ha-panel", Cardio4HAPanel);
