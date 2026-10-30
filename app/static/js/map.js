/* ============================================================
   Bantay Daan Pasig — Full map page
   Stack: Leaflet + OpenStreetMap tiles + vanilla JS fetch
   ============================================================ */
(function () {
  'use strict';

  const mapEl = document.getElementById('map');
  if (!mapEl) return;

  const CENTER = [14.5764, 121.0851];
  const BARANGAY_ZOOM = 14;

  const map = L.map('map', {
    center: CENTER,
    zoom: BARANGAY_ZOOM,
    zoomControl: true,
    attributionControl: true
  });

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

    const boundaryReady = window.PasigBoundary
    ? PasigBoundary.init(map, mapEl.dataset.geojson).catch(() => null)
    : Promise.resolve(null);

  /* -------- Marker factory (colored circle with glyph) -------- */
  const PIN_STYLES = {
    flood:    { cls: 'bd-pin--flood',    glyph: '≈' },
    affected: { cls: 'bd-pin--affected', glyph: '⊟' },
    passable: { cls: 'bd-pin--passable', glyph: '✓' },
    caution:  { cls: 'bd-pin--caution',  glyph: '!' },
    notpass:  { cls: 'bd-pin--notpass',  glyph: '✕' },
    not_passable: { cls: 'bd-pin--notpass', glyph: '✕' }
  };

  function makeIcon(kind) {
    const s = PIN_STYLES[kind] || PIN_STYLES.flood;
    return L.divIcon({
      className: '',
      html: `<div class="bd-pin ${s.cls}"><span>${s.glyph}</span></div>`,
      iconSize: [30, 30],
      iconAnchor: [15, 15],
      popupAnchor: [0, -15]
    });
  }

  const layerGroup = L.layerGroup().addTo(map);

  /* -------- Filters (condition / affected-only / barangay) -------- */
  const AFFECTED = ['caution', 'not_passable', 'affected', 'flood'];
  const normKind = k => (k === 'notpass' ? 'not_passable' : k);
  const filters = { condition: 'all', barangay: 'all', affectedOnly: false };
  let allItems = [];
  let boundary = null;

  const elCondition = document.getElementById('map-condition');
  const elBarangay = document.getElementById('map-barangay');
  const elAffected = document.getElementById('map-affected');
  const elCount = document.getElementById('map-count');

  function matches(item) {
    const k = normKind(item.kind);
    if (filters.affectedOnly && !AFFECTED.includes(k)) return false;
    if (filters.condition !== 'all' && k !== filters.condition) return false;
    if (filters.barangay !== 'all' && item.barangay !== filters.barangay) return false;
    return true;
  }

  function addMarkers(items) {
    layerGroup.clearLayers();
    items.forEach(item => {
      const marker = L.marker([item.lat, item.lng], { icon: makeIcon(item.kind), title: item.title });
      marker.on('click', () => selectAdvisory(item));
      marker.addTo(layerGroup);
    });
  }

  function refresh() {
    const visible = allItems.filter(matches);
    addMarkers(visible);
    if (elCount) {
      elCount.textContent = `${visible.length} ${visible.length === 1 ? 'advisory' : 'advisories'} shown`;
    }
  }

  function syncControls() {
    if (elCondition) elCondition.value = filters.condition;
    if (elBarangay) elBarangay.value = filters.barangay;
    if (elAffected) {
      elAffected.classList.toggle('is-active', filters.affectedOnly);
      elAffected.setAttribute('aria-pressed', filters.affectedOnly ? 'true' : 'false');
    }
  }

  elCondition?.addEventListener('change', () => { filters.condition = elCondition.value; refresh(); });
  elBarangay?.addEventListener('change', () => { filters.barangay = elBarangay.value; refresh(); });
  elAffected?.addEventListener('click', () => { filters.affectedOnly = !filters.affectedOnly; syncControls(); refresh(); });

  /* -------- Right panel selection -------- */
  const panel = document.querySelector('.bd-map-panel');

  function selectAdvisory(item) {
    if (!panel) return;
    panel.scrollTop = 0;
    map.panTo([item.lat, item.lng]);
    const title = panel.querySelector('[data-detail="title"]');
    const barangay = panel.querySelector('[data-detail="barangay"]');
    const road = panel.querySelector('[data-detail="road"]');
    const condition = panel.querySelector('[data-detail="condition"]');
    const description = panel.querySelector('[data-detail="description"]');
    const updated = panel.querySelector('[data-detail="updated"]');
    const image = panel.querySelector('[data-detail="image"]');
    const link = panel.querySelector('[data-detail="link"]');
    if (title) title.textContent = item.title || item.road || 'Road advisory';
    if (barangay) barangay.textContent = item.barangay ? `Barangay ${item.barangay}` : 'Barangay unavailable';
    if (road) road.textContent = item.road || 'Road unavailable';
    if (condition) condition.textContent = ({passable:'Passable', caution:'Difficult to pass', not_passable:'Not passable'})[item.kind] || 'Condition unavailable';
    if (description) description.textContent = item.description || 'No description provided.';
    if (updated) updated.textContent = item.published_at ? new Date(item.published_at).toLocaleString() : 'Update time unavailable';
    if (image) {
      if (item.image_url) { image.src = item.image_url; image.hidden = false; }
      else { image.removeAttribute('src'); image.hidden = true; }
    }
    if (link) link.href = item.detail_url || '/advisories';
  }

  /* -------- Search: advisories first, then OSM Nominatim bounded to Pasig -------- */
  const searchInput = document.getElementById('map-search');
  const resultsEl = document.getElementById('map-search-results');
  let searchTimer = null;
  let searchAbort = null;
  let searchPin = null;
  let currentResults = [];

  const esc = str => String(str).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  function hideResults() { if (resultsEl) { resultsEl.hidden = true; resultsEl.innerHTML = ''; } }

  function renderResults(list) {
    currentResults = list;
    if (!resultsEl) return;
    if (!list.length) {
      resultsEl.innerHTML = '<li class="bd-search-results__empty">No matching place found in Pasig City.</li>';
      resultsEl.hidden = false;
      return;
    }
    resultsEl.innerHTML = list.map((r, i) =>
      `<li role="option" tabindex="0" data-i="${i}">
         <span class="bd-search-results__name">${esc(r.label)}</span>
         <span class="bd-search-results__meta">${esc(r.meta)}</span>
       </li>`).join('');
    resultsEl.hidden = false;
  }

  function goTo(r) {
    hideResults();
    if (searchInput) searchInput.value = r.label;
    // Make sure a matched advisory is not hidden by an active filter.
    if (r.item && !matches(r.item)) {
      Object.assign(filters, { condition: 'all', barangay: 'all', affectedOnly: false });
      syncControls();
      refresh();
    }
    map.flyTo([r.lat, r.lng], 17, { duration: 0.8 });
    if (searchPin) map.removeLayer(searchPin);
    searchPin = L.circleMarker([r.lat, r.lng], {
      radius: 9, color: '#0d6efd', weight: 3, fillColor: '#fff', fillOpacity: 0.9
    }).addTo(map).bindTooltip(r.label, { permanent: false });
    if (r.item) selectAdvisory(r.item);
  }

  function searchLocal(q) {
    const needle = q.toLowerCase();
    return allItems
      .filter(i => `${i.title} ${i.barangay}`.toLowerCase().includes(needle))
      .map(i => ({ label: i.title, meta: `Advisory · Barangay ${i.barangay}`, lat: i.lat, lng: i.lng, item: i }));
  }

  async function searchRemote(q, signal) {
    const b = boundary && boundary.bounds;
    if (!b) return [];
    const box = [b.getWest(), b.getNorth(), b.getEast(), b.getSouth()].join(',');
    const url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&limit=6&countrycodes=ph' +
      `&viewbox=${box}&bounded=1&q=${encodeURIComponent(q + ' Pasig')}`;
    const res = await fetch(url, { signal, headers: { 'Accept': 'application/json' } });
    if (!res.ok) return [];
    const rows = await res.json();
    return rows
      .map(r => ({
        label: (r.name || r.display_name.split(',')[0]),
        meta: r.display_name.split(',').slice(1, 3).join(',').trim() || 'Pasig City',
        lat: parseFloat(r.lat), lng: parseFloat(r.lon)
      }))
      .filter(r => !boundary.isInside || boundary.isInside(r.lat, r.lng));
  }

  async function runSearch() {
    const q = (searchInput.value || '').trim();
    if (q.length < 2) { hideResults(); return; }
    if (searchAbort) searchAbort.abort();
    searchAbort = new AbortController();
    const local = searchLocal(q);
    renderResults(local);
    try {
      const remote = await searchRemote(q, searchAbort.signal);
      const seen = new Set(local.map(r => r.label.toLowerCase()));
      renderResults(local.concat(remote.filter(r => !seen.has(r.label.toLowerCase()))));
    } catch (e) { /* aborted or offline: keep local results */ }
  }

  if (searchInput && resultsEl) {
    searchInput.addEventListener('input', () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(runSearch, 350);
    });
    searchInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') { e.preventDefault(); if (currentResults[0]) goTo(currentResults[0]); else runSearch(); }
      if (e.key === 'Escape') hideResults();
    });
    resultsEl.addEventListener('click', e => {
      const li = e.target.closest('li[data-i]');
      if (li) goTo(currentResults[Number(li.dataset.i)]);
    });
    resultsEl.addEventListener('keydown', e => {
      if (e.key === 'Enter') { const li = e.target.closest('li[data-i]'); if (li) goTo(currentResults[Number(li.dataset.i)]); }
    });
    document.addEventListener('click', e => { if (!e.target.closest('.bd-map-search')) hideResults(); });
  }

  /* -------- "My location" -------- */
  const btnLoc = document.getElementById('btn-my-location');
  if (btnLoc && navigator.geolocation) {
    btnLoc.addEventListener('click', () => {
      navigator.geolocation.getCurrentPosition(
        pos => map.setView([pos.coords.latitude, pos.coords.longitude], 16),
        () => { /* show toast in real app */ }
      );
    });
  }

  /* -------- Boot: render only records returned by the API -------- */
  boundaryReady.then(b => {
    boundary = b;
    return fetch('/api/advisories', { credentials: 'same-origin' })
      .then(r => { if (!r.ok) throw new Error('Unable to load advisories'); return r.json(); })
      .then(data => Array.isArray(data) ? data : [])
      .catch(() => [])
      .then(items => {
        allItems = b ? items.filter(i => Number.isFinite(i.lat) && Number.isFinite(i.lng) && b.isInside(i.lat, i.lng))
                     : items.filter(i => Number.isFinite(i.lat) && Number.isFinite(i.lng));
        refresh();
        if (!allItems.length && elCount) elCount.textContent = 'No active verified reports available';
        // Verification/publication may happen while the map remains open.
        window.setInterval(async () => {
          try {
            const response = await fetch('/api/advisories', { credentials: 'same-origin' });
            if (!response.ok) return;
            const latest = await response.json();
            allItems = (Array.isArray(latest) ? latest : [])
              .filter(i => Number.isFinite(i.lat) && Number.isFinite(i.lng))
              .filter(i => !b || b.isInside(i.lat, i.lng));
            refresh();
          } catch (_) { /* retry on next interval */ }
        }, 15000);
      });
  });
})();