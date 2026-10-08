/* ============================================================
   Bantay Daan Pasig — Resident report form
   ============================================================ */
(function () {
  'use strict';

  const pickerEl = document.getElementById('map-picker');
  if (!pickerEl) return;

  const inputLat = document.getElementById('input-lat');
  const inputLng = document.getElementById('input-lng');
  const CENTER = [14.5764, 121.0851];

  const map = L.map('map-picker', {
    center: CENTER, zoom: 15, zoomControl: true, attributionControl: false
  });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

  const marker = L.marker(CENTER, { draggable: true }).addTo(map);
  marker.on('dragend', () => {
    const p = marker.getLatLng();
    inputLat.value = p.lat.toFixed(6);
    inputLng.value = p.lng.toFixed(6);
  });

  map.on('click', e => {
    marker.setLatLng(e.latlng);
    inputLat.value = e.latlng.lat.toFixed(6);
    inputLng.value = e.latlng.lng.toFixed(6);
  });

  const btnLoc = document.getElementById('btn-use-location');
  if (btnLoc && navigator.geolocation) {
    btnLoc.addEventListener('click', () => {
      btnLoc.disabled = true;
      navigator.geolocation.getCurrentPosition(
        pos => {
          const p = { lat: pos.coords.latitude, lng: pos.coords.longitude };
          map.setView([p.lat, p.lng], 16);
          marker.setLatLng([p.lat, p.lng]);
          inputLat.value = p.lat.toFixed(6);
          inputLng.value = p.lng.toFixed(6);
          btnLoc.disabled = false;
        },
        () => { btnLoc.disabled = false; }
      );
    });
  }

  /* -------- Photo preview -------- */
  const photoInput   = document.getElementById('input-photo');
  const photoPreview = document.getElementById('photo-preview');
  const photoImg     = document.getElementById('photo-preview-img');

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