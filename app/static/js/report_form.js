/* ============================================================
   Bantay Daan Pasig — Resident report form
   Restrict every pin update to Kalawaan, San Joaquin, or Bambang.
   ============================================================ */
(function () {
  'use strict';

  const pickerEl = document.getElementById('map-picker');
  if (!pickerEl) return;

  const inputLat = document.getElementById('input-lat');
  const inputLng = document.getElementById('input-lng');
  const btnLoc = document.getElementById('btn-use-location');
  const form = document.getElementById('report-form');
  const CENTER = [14.5764, 121.0851];
  const ALLOWED_NAMES = new Set(['kalawaan', 'san joaquin', 'bambang']);
  const BOUNDARY_URL =
    'https://services1.arcgis.com/GMAJGrCZkLEPNMcz/ArcGIS/rest/services/PasigBarangay/FeatureServer/1/query' +
    '?where=' + encodeURIComponent("BARANGAY IN ('Kalawaan','San Joaquin','Bambang')") +
    '&outFields=BARANGAY&returnGeometry=true&outSR=4326&f=geojson';

  const map = L.map('map-picker', {
    center: CENTER, zoom: 15, zoomControl: true, attributionControl: false
  });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  const marker = L.marker(CENTER, { draggable: true }).addTo(map);
  let allowedFeatures = [];
  let allowedLayer = null;
  let boundaryReady = false;
  let lastValid = null;
  let messageTimer = null;

  const notice = document.createElement('div');
  notice.className = 'bd-alert bd-alert--warning mt-2';
  notice.setAttribute('role', 'status');
  notice.setAttribute('aria-live', 'polite');
  notice.hidden = true;
  notice.textContent = 'Reporting is restricted to Kalawaan, San Joaquin, and Bambang.';
  pickerEl.insertAdjacentElement('afterend', notice);

  function showRestrictionMessage(message) {
    notice.textContent = message || 'Reporting is restricted to Kalawaan, San Joaquin, and Bambang.';
    notice.hidden = false;
    if (messageTimer) clearTimeout(messageTimer);
    messageTimer = setTimeout(() => { notice.hidden = true; }, 4500);
  }

  // Ray-casting test for one ring; GeoJSON coordinates are [longitude, latitude].
  function pointInRing(lng, lat, ring) {
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const xi = ring[i][0], yi = ring[i][1];
      const xj = ring[j][0], yj = ring[j][1];
      const crosses = ((yi > lat) !== (yj > lat)) &&
        (lng < ((xj - xi) * (lat - yi)) / ((yj - yi) || Number.EPSILON) + xi);
      if (crosses) inside = !inside;
    }
    return inside;
  }

  function pointInPolygonCoordinates(lng, lat, polygon) {
    if (!polygon || !polygon.length || !pointInRing(lng, lat, polygon[0])) return false;
    // GeoJSON interior rings represent holes and are excluded.
    for (let i = 1; i < polygon.length; i++) {
      if (pointInRing(lng, lat, polygon[i])) return false;
    }
    return true;
  }

  function pointInFeature(lng, lat, feature) {
    const geometry = feature && feature.geometry;
    if (!geometry) return false;
    if (geometry.type === 'Polygon') {
      return pointInPolygonCoordinates(lng, lat, geometry.coordinates);
    }
    if (geometry.type === 'MultiPolygon') {
      return geometry.coordinates.some(poly => pointInPolygonCoordinates(lng, lat, poly));
    }
    return false;
  }

  function isAllowed(lat, lng) {
    return boundaryReady && allowedFeatures.some(feature => pointInFeature(lng, lat, feature));
  }

  function setCoordinates(lat, lng) {
    inputLat.value = Number(lat).toFixed(6);
    inputLng.value = Number(lng).toFixed(6);
    lastValid = L.latLng(Number(lat), Number(lng));
  }

  function rejectPlacement() {
    if (lastValid) marker.setLatLng(lastValid);
    else marker.setOpacity(0);
    showRestrictionMessage();
    return false;
  }

  function placePin(lat, lng, options) {
    const settings = options || {};
    lat = Number(lat);
    lng = Number(lng);
    if (!Number.isFinite(lat) || !Number.isFinite(lng) || !isAllowed(lat, lng)) {
      return rejectPlacement();
    }
    const point = L.latLng(lat, lng);
    marker.setLatLng(point);
    marker.setOpacity(1);
    setCoordinates(lat, lng);
    if (settings.flyTo) map.flyTo(point, settings.zoom || 17, { duration: 0.8 });
    if (settings.label) marker.bindTooltip(settings.label, { direction: 'top' }).openTooltip();
    else marker.closeTooltip();
    notice.hidden = true;
    return true;
  }

  function normalizeName(value) {
    return String(value || '').toLowerCase()
      .replace(/\b(barangay|brgy)\b/g, ' ').replace(/[^a-z\s]/g, ' ').replace(/\s+/g, ' ').trim();
  }

  // Match on any string property so a differently named attribute field still resolves.
  function getFeatureName(feature) {
    const props = (feature && feature.properties) || {};
    for (const value of Object.values(props)) {
      const name = normalizeName(value);
      if (ALLOWED_NAMES.has(name)) return name;
    }
    return '';
  }

  async function fetchGeo(url) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 8000);
    try {
      const response = await fetch(url, { signal: ctrl.signal });
      if (!response.ok) throw new Error('Boundary source returned HTTP ' + response.status);
      const geo = await response.json();
      if (geo.error) throw new Error(geo.error.message || 'Boundary service error');
      return geo;
    } finally { clearTimeout(timer); }
  }

  async function resolveBoundaryFeatures() {
    try {
      const geo = await fetchGeo(BOUNDARY_URL);
      const features = (geo.features || []).filter(f => getFeatureName(f));
      if (!features.length) throw new Error('No matching barangay polygons in response');
      if (features.length < 3) {
        const found = new Set(features.map(getFeatureName));
        const missing = [...ALLOWED_NAMES].filter(n => !found.has(n));
        console.warn('Boundary service omitted:', missing.join(', '));
        showRestrictionMessage('Boundary data is missing for: ' + missing.join(', ') + '. Pins there cannot be placed yet.');
      }
      return features;
    } catch (error) {
      // Remote barangay layer unavailable: fall back to the bundled Pasig City boundary so pinning is not blocked.
      console.warn('Barangay boundary service failed; using city boundary fallback:', error);
      const fallbackUrl = pickerEl.dataset.fallbackBoundary;
      if (!fallbackUrl) throw error;
      const geo = await fetchGeo(fallbackUrl);
      if (!(geo.features || []).length) throw error;
      showRestrictionMessage('Barangay boundaries are unavailable; pins are temporarily checked against the Pasig City boundary.');
      return geo.features;
    }
  }

  async function loadAllowedBoundaries() {
    try {
      const features = await resolveBoundaryFeatures();
      allowedFeatures = features;
      allowedLayer = L.geoJSON({ type: 'FeatureCollection', features }, {
        style: { color: '#087f5b', weight: 3, opacity: 1, fillColor: '#20c997', fillOpacity: 0.13 },
        interactive: false
      }).addTo(map);

      // Shade the world except the permitted polygon areas.
      const world = [[-90, -180], [-90, 180], [90, 180], [90, -180]];
      const holes = [];
      features.forEach(feature => {
        const geom = feature.geometry;
        const polygons = geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates;
        polygons.forEach(poly => holes.push(poly[0].map(c => L.latLng(c[1], c[0]))));
      });
      L.polygon([world, ...holes], {
        stroke: false, fillColor: '#17212b', fillOpacity: 0.48, interactive: false
      }).addTo(map);
      allowedLayer.bringToFront();

      boundaryReady = true;
      const bounds = allowedLayer.getBounds();
      map.options.maxBoundsViscosity = 1.0;
      map.fitBounds(bounds.pad(0.08));
      map.setMaxBounds(bounds.pad(0.35));

      if (!placePin(CENTER[0], CENTER[1])) {
        marker.setOpacity(0);
        inputLat.value = '';
        inputLng.value = '';
        showRestrictionMessage('Click the map to choose a location inside Kalawaan, San Joaquin, or Bambang.');
      }
    } catch (error) {
      boundaryReady = false;
      marker.setOpacity(0);
      inputLat.value = '';
      inputLng.value = '';
      if (btnLoc) btnLoc.disabled = true;
      showRestrictionMessage('The barangay boundary data could not be loaded. Pin placement is disabled until the boundary data is available.');
      console.error('Unable to load boundaries:', error);
    }
  }

  marker.on('dragend', () => {
    const p = marker.getLatLng();
    placePin(p.lat, p.lng);
  });

  map.on('click', e => {
    if (!boundaryReady) {
      showRestrictionMessage('The allowed barangay boundaries are still loading. Try again shortly.');
      return;
    }
    placePin(e.latlng.lat, e.latlng.lng);
  });

  // Called by report-form-fields.js when a road is selected or a search result is chosen.
  window.BDReportMap = {
    focus(lat, lng, label) {
      if (!placePin(lat, lng, { flyTo: true, zoom: 17, label })) return false;
      return true;
    },
    isValid() {
      const lat = Number(inputLat.value), lng = Number(inputLng.value);
      return inputLat.value !== '' && inputLng.value !== '' && isAllowed(lat, lng);
    },
    isReady() { return boundaryReady; }
  };

  if (btnLoc && navigator.geolocation) {
    btnLoc.addEventListener('click', () => {
      if (!boundaryReady) {
        showRestrictionMessage('The allowed barangay boundaries are still loading. Try again shortly.');
        return;
      }
      btnLoc.disabled = true;
      navigator.geolocation.getCurrentPosition(
        pos => {
          const p = { lat: pos.coords.latitude, lng: pos.coords.longitude };
          if (placePin(p.lat, p.lng, { flyTo: true, zoom: 16 })) {
            btnLoc.disabled = false;
          } else {
            btnLoc.disabled = false;
          }
        },
        () => {
          btnLoc.disabled = false;
          showRestrictionMessage('Your location could not be retrieved. Choose a point inside the three covered barangays.');
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
      );
    });
  }

  if (form) {
    form.addEventListener('submit', event => {
      if (!boundaryReady || !window.BDReportMap.isValid()) {
        event.preventDefault();
        showRestrictionMessage('Choose a location inside Kalawaan, San Joaquin, or Bambang before submitting.');
        notice.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }, true);
  }

  loadAllowedBoundaries();

  /* -------- Photo preview -------- */
  const photoInput = document.getElementById('input-photo');
  const photoPreview = document.getElementById('photo-preview');
  const photoImg = document.getElementById('photo-preview-img');

  if (photoInput) {
    photoInput.addEventListener('change', () => {
      const file = photoInput.files && photoInput.files[0];
      if (!file) { photoPreview.hidden = true; return; }
      const url = URL.createObjectURL(file);
      photoImg.src = url;
      photoPreview.hidden = false;
    });
  }

  /* -------- Drag & drop -------- */
  const dz = document.getElementById('dropzone');
  if (dz && photoInput) {
    ['dragenter', 'dragover'].forEach(ev =>
      dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.add('is-dragover'); }));
    ['dragleave', 'drop'].forEach(ev =>
      dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.remove('is-dragover'); }));
    dz.addEventListener('drop', e => {
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        photoInput.files = e.dataTransfer.files;
        photoInput.dispatchEvent(new Event('change'));
      }
    });
  }
})();
