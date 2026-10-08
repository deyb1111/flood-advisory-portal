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

  /* -------- Marker factory (colored circle with glyph) -------- */
  const PIN_STYLES = {
    flood:    { cls: 'bd-pin--flood',    glyph: '≈' },
    affected: { cls: 'bd-pin--affected', glyph: '⊟' },
    passable: { cls: 'bd-pin--passable', glyph: '✓' },
    caution:  { cls: 'bd-pin--caution',  glyph: '!' },
    notpass:  { cls: 'bd-pin--notpass',  glyph: '✕' }
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

  /* -------- Placeholder seed data (fallback) -------- */
  const FALLBACK = [
    { id: 'ADV-SJ-2026-1005-031', lat: 14.5764, lng: 121.0851, kind: 'notpass',
      title: 'A. Sandoval Ave near E. Santos St', barangay: 'San Joaquin' },
    { id: 'ADV-KL-2026-1005-024', lat: 14.5780, lng: 121.0830, kind: 'caution',
      title: 'Lopez Jaena Street', barangay: 'Kalawaan' },
    { id: 'ADV-BM-2026-1005-019', lat: 14.5740, lng: 121.0820, kind: 'passable',
      title: 'F. Mariano Ave', barangay: 'Bambang' },
    { id: 'ADV-BM-2026-1005-018', lat: 14.5735, lng: 121.0810, kind: 'flood',
      title: 'M. Concepcion Ave', barangay: 'Bambang' },
    { id: 'ADV-BM-2026-1005-015', lat: 14.5755, lng: 121.0840, kind: 'affected',
      title: 'Road affected near bridge', barangay: 'San Joaquin' }
  ];

  const layerGroup = L.layerGroup().addTo(map);

  function addMarkers(items) {
    layerGroup.clearLayers();
    items.forEach(item => {
      const marker = L.marker([item.lat, item.lng], { icon: makeIcon(item.kind), title: item.title });
      marker.on('click', () => selectAdvisory(item));
      marker.addTo(layerGroup);
    });
  }

  /* -------- Right panel selection -------- */
  const panel = document.querySelector('.bd-map-panel');

  function selectAdvisory(item) {
    if (!panel) return;
    // In a real app, fetch /api/advisories/<id> and hydrate the panel.
    // For the mock interface we simply ensure the panel is visible.
    panel.scrollTop = 0;
    map.panTo([item.lat, item.lng]);
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

  /* -------- Boot: try API, fall back to seed -------- */
  fetch('/api/advisories')
    .then(r => r.ok ? r.json() : Promise.reject())
    .then(data => addMarkers(data && data.length ? data : FALLBACK))
    .catch(() => addMarkers(FALLBACK));
})();