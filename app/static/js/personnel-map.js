/* Personnel map: dashboard mini, report detail, and full map page. */
(function () {
  'use strict';
  if (!window.L) return;

  const CENTER = [14.5764, 121.0851];
  const PIN = {
    verified:   { cls: 'bd-pin--verified',   glyph: '✓' },
    unverified: { cls: 'bd-pin--unverified', glyph: '!' },
    rejected:   { cls: 'bd-pin--rejected',   glyph: '✕' },
  };

  function makeIcon(status) {
    const s = PIN[status] || PIN.unverified;
    return L.divIcon({
      className: '',
      html: `<div class="bd-pin ${s.cls}"><span>${s.glyph}</span></div>`,
      iconSize: [30, 30], iconAnchor: [15, 15], popupAnchor: [0, -15],
    });
  }

  function newMap(el, center, zoom) {
    const m = L.map(el, { center, zoom, zoomControl: true, attributionControl: true });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19, attribution: '&copy; OpenStreetMap contributors'
    }).addTo(m);
    return m;
  }

  // --- Full map page ---
  const mapEl = document.getElementById('map');
  if (mapEl) {
    const reports = JSON.parse(mapEl.dataset.reports || '[]');
    const map = newMap(mapEl, CENTER, 15);
    const layer = L.layerGroup().addTo(map);
    const detail = document.getElementById('map-detail');

    function render(filter) {
      layer.clearLayers();
      const list = reports.filter(filter);
      list.forEach(r => {
        const marker = L.marker([r.lat, r.lng], { icon: makeIcon(r.status) }).addTo(layer);
        marker.on('click', () => select(r));
      });
      if (list.length) {
        const bounds = L.latLngBounds(list.map(r => [r.lat, r.lng]));
        map.fitBounds(bounds.pad(0.35), { maxZoom: 16 });
      }
    }

    function select(r) {
      if (!detail) return;
      map.panTo([r.lat, r.lng]);
      detail.innerHTML = `
        <span class="bd-badge bd-badge--${r.status === 'verified' ? 'verified' : r.status === 'rejected' ? 'rejected' : 'pending'}">${r.status === 'verified' ? '✓ Verified' : r.status === 'rejected' ? 'Rejected' : 'Awaiting review'}</span>
        <h3>${r.street || 'Reported location'}</h3>
        <p class="bd-map-detail__loc">Report ${r.reference} · ${r.submitted_at}</p>
        <p class="bd-map-detail__meta">${r.description || ''}</p>
        <a class="bd-btn bd-btn--primary w-100 mt-3 justify-content-center"
           href="/personnel/reports/${r.id}">${r.status === 'unverified' ? 'Review report' : 'View report'}</a>
      `;
    }

    document.getElementById('map-status')?.addEventListener('change', apply);
    document.getElementById('map-type')?.addEventListener('change', apply);
    document.getElementById('map-rejected')?.addEventListener('change', apply);
    document.getElementById('map-q')?.addEventListener('input', apply);

    function apply() {
      const status = document.getElementById('map-status').value;
      const type = document.getElementById('map-type').value;
      const showRej = document.getElementById('map-rejected').value === 'on';
      const q = (document.getElementById('map-q').value || '').toLowerCase();
      render(r => {
        if (!showRej && r.status === 'rejected') return false;
        if (status && r.status !== status) return false;
        if (type && r.report_type !== type) return false;
        if (q && !(`${r.street} ${r.reference}`).toLowerCase().includes(q)) return false;
        return true;
      });
    }
    render(() => true);
  }

  // --- Report detail mini-map ---
  const detailMapEl = document.getElementById('detail-map');
  if (detailMapEl) {
    const lat = parseFloat(detailMapEl.dataset.lat);
    const lng = parseFloat(detailMapEl.dataset.lng);
    const status = detailMapEl.dataset.status || 'unverified';
    if (Number.isFinite(lat) && Number.isFinite(lng)) {
      const m = newMap(detailMapEl, [lat, lng], 16);
      L.marker([lat, lng], { icon: makeIcon(status) }).addTo(m);
    }
  }

  // --- Dashboard mini-map ---
  const miniEl = document.getElementById('mini-map');
  if (miniEl && !miniEl.dataset.initialized) {
    miniEl.dataset.initialized = '1';
    newMap(miniEl, CENTER, 14);
  }
})();